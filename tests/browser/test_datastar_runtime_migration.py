"""Browser-level Datastar runtime migration tests.

These tests intentionally load StarHTML's patched local Datastar bundle instead
of a CDN copy so migration coverage follows the vendored runtime.
"""

import json
import re
import sys
from pathlib import Path
from typing import TYPE_CHECKING, TypedDict, cast
from urllib.parse import parse_qs, urlparse

import pytest
import pytest_asyncio

if TYPE_CHECKING:
    from playwright.async_api import Page

try:
    from playwright.async_api import async_playwright

    PLAYWRIGHT_AVAILABLE = True
except ImportError:  # pragma: no cover - exercised only when the optional dep is absent
    async_playwright = None
    PLAYWRIGHT_AVAILABLE = False


class FetchCall(TypedDict):
    url: str
    method: str
    headers: dict[str, str]
    body: str | None


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATASTAR_RUNTIME = PROJECT_ROOT / "src" / "starhtml" / "static" / "js" / "datastar.js"
DATASTAR_UPSTREAM = PROJECT_ROOT / "patches" / "datastar-upstream.js"
STARAPP_PATH = PROJECT_ROOT / "src" / "starhtml" / "starapp.py"
sys.path.insert(0, str(PROJECT_ROOT / "patches"))
from patch_definitions import apply_all, verify  # noqa: E402


@pytest.fixture(scope="session")
def datastar_runtime_source() -> str:
    """Return the built StarHTML Datastar runtime used by normal app pages."""
    if DATASTAR_RUNTIME.exists():
        return DATASTAR_RUNTIME.read_text()

    version_match = re.search(r'DATASTAR_VERSION\s*=\s*["\']([^"\']+)["\']', STARAPP_PATH.read_text())
    if not version_match:
        pytest.fail("DATASTAR_VERSION not found in src/starhtml/starapp.py")
    return apply_all(DATASTAR_UPSTREAM.read_text(), version_match.group(1).split("+")[0])


@pytest.fixture(scope="session")
def datastar_upstream_source() -> str:
    """Return vanilla Datastar 1.0.1 for upstream behavior comparisons."""
    return DATASTAR_UPSTREAM.read_text()


@pytest_asyncio.fixture
async def page():
    """Create a Chromium page for focused Datastar migration tests."""
    if not PLAYWRIGHT_AVAILABLE:
        pytest.skip("Playwright not available")

    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch()
        context = await browser.new_context()
        test_page = await context.new_page()
        try:
            yield test_page
        finally:
            await context.close()
            await browser.close()


def datastar_test_page(body: str, datastar_source: str) -> str:
    """Build a minimal HTML document that loads the local Datastar runtime."""
    source_json = json.dumps(datastar_source)
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>Datastar Runtime Migration Test</title>
</head>
<body>
{body}
  <script type="module">
    const datastarSource = {source_json};
    const datastarUrl = URL.createObjectURL(new Blob([datastarSource], {{ type: "text/javascript" }}));
    window.__datastar = await import(datastarUrl);
    URL.revokeObjectURL(datastarUrl);
  </script>
</body>
</html>"""


async def load_datastar_page(page: "Page", body: str, datastar_source: str) -> None:
    """Load a page with StarHTML's local Datastar runtime and wait for scans."""
    await page.set_content(datastar_test_page(body, datastar_source), wait_until="domcontentloaded")
    await page.wait_for_function("window.__datastar !== undefined")


async def load_datastar_page_at_origin(page: "Page", body: str, datastar_source: str) -> None:
    """Load a Datastar test document at a real origin for storage-sensitive tests."""
    url = "https://starhtml.test/datastar-runtime-test"
    html = datastar_test_page(body, datastar_source)

    async def route_handler(route):
        await route.fulfill(status=200, content_type="text/html", body=html)

    await page.route(url, route_handler)
    try:
        await page.goto(url, wait_until="domcontentloaded")
        await page.wait_for_function("window.__datastar !== undefined")
    finally:
        await page.unroute(url, route_handler)


async def wait_for_dom_text(page: "Page", selector: str, expected: str, timeout: int = 5000) -> None:
    """Wait until a selector has the expected text content."""
    await page.wait_for_function(
        """([selector, expected]) => document.querySelector(selector)?.textContent === expected""",
        arg=[selector, expected],
        timeout=timeout,
    )


async def wait_for_shadow_text(page: "Page", host_selector: str, selector: str, expected: str) -> None:
    """Wait until a selector inside an open shadow root has the expected text."""
    await page.wait_for_function(
        """([hostSelector, selector, expected]) =>
            document.querySelector(hostSelector)?.shadowRoot?.querySelector(selector)?.textContent === expected""",
        arg=[host_selector, selector, expected],
    )


async def dispatch_signal_patch(page: "Page", signals: dict[str, object]) -> None:
    """Patch Datastar signals through the public runtime API."""
    await page.evaluate(
        """signals => window.__datastar.mergePatch(signals)""",
        signals,
    )


async def dispatch_element_patch(page: "Page", elements: str, selector: str = "", mode: str = "outer") -> None:
    """Patch elements through Datastar's registered patch-elements watcher."""
    await page.evaluate(
        """args => {
            document.dispatchEvent(new CustomEvent("datastar-fetch", {
                detail: {
                    type: "datastar-patch-elements",
                    argsRaw: args,
                },
            }));
        }""",
        {"elements": elements, "selector": selector, "mode": mode},
    )
    await page.wait_for_timeout(50)


async def read_signals(page: "Page", selector: str = "#signals") -> dict[str, object]:
    """Read a JSON signal snapshot rendered by ``data-json-signals``."""
    text = await page.locator(selector).text_content()
    return json.loads(text or "{}")


def fetch_capture_script(response_statuses: list[int] | None = None) -> str:
    """Install a fetch mock that records request shape for assertions."""
    statuses_json = json.dumps(response_statuses or [204])
    return f"""
<script>
  window.__fetchCalls = [];
  window.__fetchStatuses = {statuses_json};
  window.fetch = async (url, init = {{}}) => {{
    const headers = Object.fromEntries(new Headers(init.headers || {{}}).entries());
    let body = null;
    if (init.body instanceof URLSearchParams) {{
      body = init.body.toString();
    }} else if (init.body instanceof FormData) {{
      body = Array.from(init.body.entries());
    }} else if (init.body !== undefined && init.body !== null) {{
      body = String(init.body);
    }}
    window.__fetchCalls.push({{
      url: String(url),
      method: init.method || "GET",
      headers,
      body
    }});
    const status = window.__fetchStatuses.shift() || 204;
    return new Response(null, {{ status }});
  }};
</script>
"""


def fetch_visibility_reconnect_script() -> str:
    """Install a fetch mock whose first request stays open until visibility reconnect."""
    return """
<script>
  window.__fetchCalls = [];
  window.fetch = async (url, init = {}) => {
    const headers = Object.fromEntries(new Headers(init.headers || {}).entries());
    let body = null;
    if (init.body instanceof URLSearchParams) {
      body = init.body.toString();
    } else if (init.body instanceof FormData) {
      body = Array.from(init.body.entries());
    } else if (init.body !== undefined && init.body !== null) {
      body = String(init.body);
    }
    window.__fetchCalls.push({
      url: String(url),
      method: init.method || "GET",
      headers,
      body
    });
    if (window.__fetchCalls.length === 1) {
      return new Promise((resolve, reject) => {
        init.signal?.addEventListener("abort", () => {
          reject(new DOMException("Aborted", "AbortError"));
        }, { once: true });
      });
    }
    return new Response(null, { status: 204 });
  };
</script>
"""


async def read_fetch_calls(page: "Page", expected_count: int = 1) -> list[FetchCall]:
    """Return captured calls from the fetch mock."""
    await page.wait_for_function("expected => window.__fetchCalls?.length >= expected", arg=expected_count)
    return cast("list[FetchCall]", await page.evaluate("window.__fetchCalls"))


def datastar_query_payload(url: str) -> dict[str, object]:
    """Decode the Datastar JSON query parameter from a captured URL."""
    parsed = urlparse(url)
    values = parse_qs(parsed.query).get("datastar")
    assert values, f"Missing datastar query parameter in {url}"
    return json.loads(values[0])


@pytest.mark.skipif(not PLAYWRIGHT_AVAILABLE, reason="Playwright not available")
@pytest.mark.asyncio
async def test_local_runtime_binds_signals_text_and_click(page, datastar_runtime_source):
    """Smoke-test the harness against the currently vendored StarHTML runtime."""
    await load_datastar_page(
        page,
        """
<main data-signals='{"count": 0, "label": "ready"}'>
  <button id="increment" data-on:click="$count++">Increment</button>
  <output id="count" data-text="$count"></output>
  <output id="label" data-text="$label"></output>
  <pre id="signals" data-json-signals></pre>
</main>
""",
        datastar_runtime_source,
    )

    await wait_for_dom_text(page, "#count", "0")
    await wait_for_dom_text(page, "#label", "ready")

    await page.locator("#increment").click()
    await wait_for_dom_text(page, "#count", "1")

    await dispatch_signal_patch(page, {"count": 7, "label": "patched"})
    await wait_for_dom_text(page, "#count", "7")
    await wait_for_dom_text(page, "#label", "patched")

    signals = await read_signals(page)
    assert signals["count"] == 7
    assert signals["label"] == "patched"


@pytest.mark.skipif(not PLAYWRIGHT_AVAILABLE, reason="Playwright not available")
@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("method", "action"),
    [("GET", "@get('https://example.test/capture')"), ("DELETE", "@delete('https://example.test/capture')")],
)
async def test_get_and_delete_send_signals_in_query_without_body(page, datastar_runtime_source, method, action):
    """Datastar 1.0.1 sends GET/DELETE signal payloads as query params only."""
    await load_datastar_page(
        page,
        f"""
{fetch_capture_script()}
<main data-signals='{{"name": "Ada", "count": 2}}'>
  <button id="send" data-on:click="{action}">Send</button>
  <output id="ready" data-text="$name"></output>
</main>
""",
        datastar_runtime_source,
    )

    await wait_for_dom_text(page, "#ready", "Ada")
    await page.locator("#send").click()

    [call] = await read_fetch_calls(page)
    assert call["method"] == method
    assert call["body"] is None
    assert "content-type" not in call["headers"]
    assert datastar_query_payload(call["url"]) == {"name": "Ada", "count": 2}


@pytest.mark.skipif(not PLAYWRIGHT_AVAILABLE, reason="Playwright not available")
@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("method", "action"),
    [
        ("POST", "@post('https://example.test/capture')"),
        ("PUT", "@put('https://example.test/capture')"),
        ("PATCH", "@patch('https://example.test/capture')"),
    ],
)
async def test_mutation_fetch_actions_send_json_body(page, datastar_runtime_source, method, action):
    """POST/PUT/PATCH keep the Datastar signal payload in a JSON body."""
    await load_datastar_page(
        page,
        f"""
{fetch_capture_script()}
<main data-signals='{{"name": "Ada", "count": 2}}'>
  <button id="send" data-on:click="{action}">Send</button>
  <output id="ready" data-text="$name"></output>
</main>
""",
        datastar_runtime_source,
    )

    await wait_for_dom_text(page, "#ready", "Ada")
    await page.locator("#send").click()

    [call] = await read_fetch_calls(page)
    assert call["method"] == method
    assert urlparse(call["url"]).query == ""
    assert call["headers"]["content-type"] == "application/json"
    assert json.loads(call["body"]) == {"name": "Ada", "count": 2}


@pytest.mark.skipif(not PLAYWRIGHT_AVAILABLE, reason="Playwright not available")
@pytest.mark.asyncio
async def test_form_submit_input_value_is_included(page, datastar_runtime_source):
    """Datastar 1.0.1 includes input[type=submit] name/value in form submissions."""
    await load_datastar_page(
        page,
        f"""
{fetch_capture_script()}
<form id="form" data-on:submit__prevent="@post('https://example.test/capture', {{contentType: 'form'}})">
  <input name="item" value="book">
  <input id="submit" type="submit" name="intent" value="save">
  <output id="ready" data-text="'ready'"></output>
</form>
""",
        datastar_runtime_source,
    )

    await wait_for_dom_text(page, "#ready", "ready")
    await page.locator("#submit").click()

    [call] = await read_fetch_calls(page)
    assert call["method"] == "POST"
    assert call["headers"]["content-type"] == "application/x-www-form-urlencoded"
    assert parse_qs(call["body"]) == {"item": ["book"], "intent": ["save"]}


@pytest.mark.skipif(not PLAYWRIGHT_AVAILABLE, reason="Playwright not available")
@pytest.mark.asyncio
@pytest.mark.parametrize("runtime_fixture", ["datastar_upstream_source", "datastar_runtime_source"])
async def test_http_retry_reuses_original_signal_payload(page, request, runtime_fixture):
    """Vanilla and StarHTML Datastar 1.0.1 ordinary HTTP retries reuse the original payload."""
    datastar_source = request.getfixturevalue(runtime_fixture)
    await load_datastar_page(
        page,
        f"""
{fetch_capture_script([500, 204])}
<main data-signals='{{"name": "Ada"}}'>
  <button
    id="send"
    data-on:click="@post('https://example.test/capture', {{retry: 'error', retryInterval: 50, retryMaxCount: 3}})"
  >Send</button>
  <output id="ready" data-text="$name"></output>
</main>
""",
        datastar_source,
    )

    await wait_for_dom_text(page, "#ready", "Ada")
    await page.locator("#send").click()
    await read_fetch_calls(page)
    await dispatch_signal_patch(page, {"name": "Grace"})

    calls = await read_fetch_calls(page, expected_count=2)
    assert json.loads(calls[0]["body"]) == {"name": "Ada"}
    assert json.loads(calls[1]["body"]) == {"name": "Ada"}


@pytest.mark.skipif(not PLAYWRIGHT_AVAILABLE, reason="Playwright not available")
@pytest.mark.asyncio
@pytest.mark.parametrize("runtime_fixture", ["datastar_upstream_source", "datastar_runtime_source"])
async def test_visibility_reconnect_rebuilds_payload_from_current_signals(page, request, runtime_fixture):
    """Vanilla and StarHTML Datastar 1.0.1 rebuild payloads on visibility reconnect."""
    datastar_source = request.getfixturevalue(runtime_fixture)
    await load_datastar_page(
        page,
        f"""
{fetch_visibility_reconnect_script()}
<main data-signals='{{"name": "Ada"}}'>
  <button
    id="send"
    data-on:click="@post('https://example.test/capture', {{openWhenHidden: false}})"
  >Send</button>
  <output id="ready" data-text="$name"></output>
</main>
""",
        datastar_source,
    )

    await wait_for_dom_text(page, "#ready", "Ada")
    await page.locator("#send").click()
    await read_fetch_calls(page)
    await dispatch_signal_patch(page, {"name": "Grace"})
    await page.evaluate("document.dispatchEvent(new Event('visibilitychange'))")

    calls = await read_fetch_calls(page, expected_count=2)
    assert json.loads(calls[0]["body"]) == {"name": "Ada"}
    assert json.loads(calls[1]["body"]) == {"name": "Grace"}


@pytest.mark.skipif(not PLAYWRIGHT_AVAILABLE, reason="Playwright not available")
@pytest.mark.asyncio
async def test_data_on_document_receives_document_events(page, datastar_runtime_source):
    """data-on:*__document attaches the listener to document."""
    await load_datastar_page(
        page,
        """
<main data-signals='{"count": 0}'>
  <div id="listener" data-on:custom__document="$count++"></div>
  <output id="count" data-text="$count"></output>
</main>
""",
        datastar_runtime_source,
    )

    await wait_for_dom_text(page, "#count", "0")
    await page.evaluate("document.dispatchEvent(new CustomEvent('custom'))")

    await wait_for_dom_text(page, "#count", "1")


@pytest.mark.skipif(not PLAYWRIGHT_AVAILABLE, reason="Playwright not available")
@pytest.mark.asyncio
async def test_data_on_document_capture_cleanup_removes_listener(page, datastar_runtime_source):
    """Capture listener cleanup must use matching listener options."""
    await load_datastar_page(
        page,
        """
<main data-signals='{"count": 0}'>
  <div id="listener" data-on:click__document__capture="$count++"></div>
  <output id="count" data-text="$count"></output>
</main>
""",
        datastar_runtime_source,
    )

    await wait_for_dom_text(page, "#count", "0")
    await page.locator("body").click()
    await wait_for_dom_text(page, "#count", "1")

    await page.locator("#listener").evaluate("el => el.remove()")
    await page.locator("body").click()
    await page.wait_for_timeout(50)

    assert await page.locator("#count").text_content() == "1"


@pytest.mark.skipif(not PLAYWRIGHT_AVAILABLE, reason="Playwright not available")
@pytest.mark.asyncio
async def test_submit_viewtransition_prevent_stops_native_submission(page, datastar_runtime_source):
    """Submit prevent should run even when wrapped by viewtransition timing."""
    await load_datastar_page(
        page,
        """
<form
  id="form"
  action="https://example.test/native-submit"
  data-signals='{"submitted": false}'
  data-on:submit__viewtransition__prevent="$submitted = true"
>
  <button id="submit" type="submit">Submit</button>
  <output id="submitted" data-text="$submitted"></output>
</form>
""",
        datastar_runtime_source,
    )

    await wait_for_dom_text(page, "#submitted", "false")
    await page.locator("#submit").click()

    await wait_for_dom_text(page, "#submitted", "true")
    assert page.url == "about:blank"


@pytest.mark.skipif(not PLAYWRIGHT_AVAILABLE, reason="Playwright not available")
@pytest.mark.asyncio
async def test_outside_click_does_not_close_just_opened_popover(page, datastar_runtime_source):
    """StarHTML's outside-race patch keeps a just-opened data-show popover open."""
    await load_datastar_page(
        page,
        """
<main data-signals='{"open": false}'>
  <button id="open" data-on:click="$open = true">Open</button>
  <div id="popover" data-show="$open" data-on:click__outside="$open = false">Popover</div>
  <output id="state" data-text="$open"></output>
</main>
""",
        datastar_runtime_source,
    )

    await wait_for_dom_text(page, "#state", "false")
    await page.locator("#open").click()

    await wait_for_dom_text(page, "#state", "true")
    assert await page.locator("#popover").evaluate("el => getComputedStyle(el).display") != "none"


@pytest.mark.skipif(not PLAYWRIGHT_AVAILABLE, reason="Playwright not available")
@pytest.mark.asyncio
async def test_on_intersect_threshold_modifier_uses_numeric_fraction(page, datastar_runtime_source):
    """data-on-intersect__threshold.25 should configure threshold 0.25."""
    await load_datastar_page(
        page,
        """
<script>
  window.__intersectionOptions = [];
  window.IntersectionObserver = class {
    constructor(callback, options) {
      this.callback = callback;
      window.__intersectionOptions.push(options);
    }
    observe() {}
    disconnect() {}
  };
</script>
<main data-signals='{"ready": "yes"}'>
  <div id="target" data-on-intersect__threshold.25="$seen = true"></div>
  <output id="ready" data-text="$ready"></output>
</main>
""",
        datastar_runtime_source,
    )

    await wait_for_dom_text(page, "#ready", "yes")

    thresholds = await page.evaluate("window.__intersectionOptions.map(options => options.threshold)")
    assert thresholds == [0.25]


@pytest.mark.skipif(not PLAYWRIGHT_AVAILABLE, reason="Playwright not available")
@pytest.mark.asyncio
async def test_data_bind_prop_modifier_binds_without_event_modifier(page, datastar_runtime_source):
    """data-bind__prop can target an element property while using default events."""
    await load_datastar_page(
        page,
        """
<main data-signals='{"hidden": true}'>
  <section id="panel" data-bind__prop.hidden="hidden"></section>
  <output id="hidden" data-text="$hidden"></output>
</main>
""",
        datastar_runtime_source,
    )

    await wait_for_dom_text(page, "#hidden", "true")
    assert await page.locator("#panel").evaluate("el => el.hidden") is True

    await page.locator("#panel").evaluate(
        """el => {
            el.hidden = false;
            el.dispatchEvent(new Event("change", { bubbles: true }));
        }"""
    )

    await wait_for_dom_text(page, "#hidden", "false")


@pytest.mark.skipif(not PLAYWRIGHT_AVAILABLE, reason="Playwright not available")
@pytest.mark.asyncio
async def test_data_bind_event_modifier_binds_without_prop_modifier(page, datastar_runtime_source):
    """data-bind__event can override events while preserving default input binding."""
    await load_datastar_page(
        page,
        """
<main data-signals='{"name": "Ada"}'>
  <input id="name" data-bind__event.change="name">
  <output id="name-output" data-text="$name"></output>
</main>
""",
        datastar_runtime_source,
    )

    await wait_for_dom_text(page, "#name-output", "Ada")
    assert await page.locator("#name").input_value() == "Ada"

    await page.locator("#name").evaluate(
        """el => {
            el.value = "Grace";
            el.dispatchEvent(new Event("input", { bubbles: true }));
        }"""
    )
    await page.wait_for_timeout(50)
    assert await page.locator("#name-output").text_content() == "Ada"

    await page.locator("#name").dispatch_event("change")
    await wait_for_dom_text(page, "#name-output", "Grace")


@pytest.mark.skipif(not PLAYWRIGHT_AVAILABLE, reason="Playwright not available")
@pytest.mark.asyncio
async def test_data_bind_prop_and_event_modifiers_combine(page, datastar_runtime_source):
    """Combined prop/event modifiers bind the property and listen only to the requested event."""
    await load_datastar_page(
        page,
        """
<main data-signals='{"label": "Ada"}'>
  <div id="target" data-bind__prop.title__event.datastar-prop-change="label"></div>
  <output id="label" data-text="$label"></output>
</main>
""",
        datastar_runtime_source,
    )

    await wait_for_dom_text(page, "#label", "Ada")
    assert await page.locator("#target").evaluate("el => el.title") == "Ada"

    await page.locator("#target").evaluate(
        """el => {
            el.title = "Grace";
            el.dispatchEvent(new Event("input", { bubbles: true }));
        }"""
    )
    await page.wait_for_timeout(50)
    assert await page.locator("#label").text_content() == "Ada"

    await page.locator("#target").dispatch_event("datastar-prop-change")
    await wait_for_dom_text(page, "#label", "Grace")


@pytest.mark.skipif(not PLAYWRIGHT_AVAILABLE, reason="Playwright not available")
@pytest.mark.asyncio
async def test_data_bind_prop_selected_index_uses_camel_cased_property(page, datastar_runtime_source):
    """Hyphenated prop modifiers bind through the camel-cased DOM property."""
    await load_datastar_page(
        page,
        """
<main data-signals='{"choice_index": 1}'>
  <select id="choice" data-bind__prop.selected-index="choice_index">
    <option value="a">A</option>
    <option value="b">B</option>
    <option value="c">C</option>
  </select>
  <output id="choice-index" data-text="$choice_index"></output>
</main>
""",
        datastar_runtime_source,
    )

    await wait_for_dom_text(page, "#choice-index", "1")
    assert await page.locator("#choice").evaluate("el => el.selectedIndex") == 1

    await page.locator("#choice").evaluate(
        """el => {
            el.selectedIndex = 2;
            el.dispatchEvent(new Event("change", { bubbles: true }));
        }"""
    )

    await wait_for_dom_text(page, "#choice-index", "2")


@pytest.mark.skipif(not PLAYWRIGHT_AVAILABLE, reason="Playwright not available")
@pytest.mark.asyncio
async def test_radio_bind_initializes_missing_signal_from_checked_radio(page, datastar_runtime_source):
    """Missing radio signals adopt the initially checked radio value."""
    await load_datastar_page(
        page,
        """
<main>
  <label><input type="radio" name="choice" value="alpha" data-bind="choice">Alpha</label>
  <label><input type="radio" name="choice" value="beta" data-bind="choice" checked>Beta</label>
  <output id="choice" data-text="$choice"></output>
  <pre id="signals" data-json-signals></pre>
</main>
""",
        datastar_runtime_source,
    )

    await wait_for_dom_text(page, "#choice", "beta")
    assert await page.locator("input[value='beta']").is_checked()

    signals = await read_signals(page)
    assert signals["choice"] == "beta"


@pytest.mark.skipif(not PLAYWRIGHT_AVAILABLE, reason="Playwright not available")
@pytest.mark.asyncio
async def test_single_select_initializes_missing_signal_as_string_value(page, datastar_runtime_source):
    """Missing select signals keep selected string values instead of coercing numbers."""
    await load_datastar_page(
        page,
        """
<main>
  <select id="quantity" data-bind="quantity">
    <option value="1" selected>One</option>
    <option value="2">Two</option>
  </select>
  <output id="quantity-output" data-text="$quantity"></output>
  <pre id="signals" data-json-signals></pre>
</main>
""",
        datastar_runtime_source,
    )

    await wait_for_dom_text(page, "#quantity-output", "1")

    signals = await read_signals(page)
    assert signals["quantity"] == "1"


@pytest.mark.skipif(not PLAYWRIGHT_AVAILABLE, reason="Playwright not available")
@pytest.mark.asyncio
async def test_morphing_bound_text_input_updates_value_and_signal(page, datastar_runtime_source):
    """Morphing an input value dispatches property-change sync for data-bind."""
    await load_datastar_page(
        page,
        """
<main data-signals='{"name": "Ada"}'>
  <input id="name" data-bind="name" value="Ada">
  <output id="name-output" data-text="$name"></output>
</main>
""",
        datastar_runtime_source,
    )

    await wait_for_dom_text(page, "#name-output", "Ada")

    await dispatch_element_patch(page, '<input id="name" data-bind="name" value="Grace">')

    assert await page.locator("#name").input_value() == "Grace"
    await wait_for_dom_text(page, "#name-output", "Grace")


@pytest.mark.skipif(not PLAYWRIGHT_AVAILABLE, reason="Playwright not available")
@pytest.mark.asyncio
async def test_morphing_checked_inputs_update_checked_state_and_signals(page, datastar_runtime_source):
    """Morphing checkbox/radio checked state dispatches property-change sync."""
    await load_datastar_page(
        page,
        """
<main id="controls" data-signals='{"enabled": false, "choice": "alpha"}'>
  <input id="enabled" type="checkbox" data-bind="enabled">
  <input id="alpha" type="radio" name="choice" value="alpha" data-bind="choice" checked>
  <input id="beta" type="radio" name="choice" value="beta" data-bind="choice">
  <output id="enabled-output" data-text="$enabled"></output>
  <output id="choice-output" data-text="$choice"></output>
</main>
""",
        datastar_runtime_source,
    )

    await wait_for_dom_text(page, "#enabled-output", "false")
    await wait_for_dom_text(page, "#choice-output", "alpha")

    await dispatch_element_patch(
        page,
        """
<main id="controls" data-signals='{"enabled": false, "choice": "alpha"}'>
  <input id="enabled" type="checkbox" data-bind="enabled" checked>
  <input id="alpha" type="radio" name="choice" value="alpha" data-bind="choice">
  <input id="beta" type="radio" name="choice" value="beta" data-bind="choice" checked>
  <output id="enabled-output" data-text="$enabled"></output>
  <output id="choice-output" data-text="$choice"></output>
</main>
""",
    )

    assert await page.locator("#enabled").is_checked()
    assert await page.locator("#beta").is_checked()
    await wait_for_dom_text(page, "#enabled-output", "true")
    await wait_for_dom_text(page, "#choice-output", "beta")


@pytest.mark.skipif(not PLAYWRIGHT_AVAILABLE, reason="Playwright not available")
@pytest.mark.asyncio
async def test_morphing_select_selected_option_updates_value_and_signal(page, datastar_runtime_source):
    """Morphing selected options updates select value and bound signal."""
    await load_datastar_page(
        page,
        """
<main data-signals='{"choice": "a"}'>
  <select id="choice" data-bind="choice">
    <option value="a" selected>A</option>
    <option value="b">B</option>
  </select>
  <output id="choice-output" data-text="$choice"></output>
</main>
""",
        datastar_runtime_source,
    )

    await wait_for_dom_text(page, "#choice-output", "a")

    await dispatch_element_patch(
        page,
        """
<select id="choice" data-bind="choice">
  <option value="a">A</option>
  <option value="b" selected>B</option>
</select>
""",
    )

    assert await page.locator("#choice").input_value() == "b"
    await wait_for_dom_text(page, "#choice-output", "b")


@pytest.mark.skipif(not PLAYWRIGHT_AVAILABLE, reason="Playwright not available")
@pytest.mark.asyncio
async def test_morphing_textarea_updates_value_default_and_signal(page, datastar_runtime_source):
    """Morphing textarea content updates value/default text and bound signal."""
    await load_datastar_page(
        page,
        """
<main data-signals='{"bio": "Old"}'>
  <textarea id="bio" data-bind="bio">Old</textarea>
  <output id="bio-output" data-text="$bio"></output>
</main>
""",
        datastar_runtime_source,
    )

    await wait_for_dom_text(page, "#bio-output", "Old")

    await dispatch_element_patch(page, '<textarea id="bio" data-bind="bio">New</textarea>')

    assert await page.locator("#bio").input_value() == "New"
    assert await page.locator("#bio").evaluate("el => el.textContent") == "New"
    await wait_for_dom_text(page, "#bio-output", "New")


@pytest.mark.skipif(not PLAYWRIGHT_AVAILABLE, reason="Playwright not available")
@pytest.mark.asyncio
async def test_morphing_preserve_attr_keeps_protected_attrs(page, datastar_runtime_source):
    """data-preserve-attr keeps protected attrs while other attrs and children morph."""
    await load_datastar_page(
        page,
        """
<main>
  <div id="box" class="keep" data-state="old" data-preserve-attr="class">Old</div>
</main>
""",
        datastar_runtime_source,
    )

    await dispatch_element_patch(
        page,
        '<div id="box" class="replace" data-state="new" data-preserve-attr="class">New</div>',
    )

    box = page.locator("#box")
    assert await box.get_attribute("class") == "keep"
    assert await box.get_attribute("data-state") == "new"
    assert await box.text_content() == "New"


def test_local_runtime_contains_starhtml_patch_markers(datastar_runtime_source):
    """The loaded runtime includes every expected StarHTML patch marker."""
    missing = [f"{name}: {marker}" for name, marker, ok in verify(datastar_runtime_source) if not ok]

    assert not missing


@pytest.mark.skipif(not PLAYWRIGHT_AVAILABLE, reason="Playwright not available")
@pytest.mark.asyncio
async def test_datastar_scan_binds_shadow_root(page, datastar_runtime_source):
    """StarHTML's datastar:scan patch binds attributes inside shadow roots."""
    await load_datastar_page(
        page,
        """
<div id="host"></div>
<script>
  const host = document.querySelector("#host");
  host.attachShadow({ mode: "open" }).innerHTML = `
    <main data-signals='{"count": 0}'>
      <button id="increment" data-on:click="$count++">Increment</button>
      <output id="count" data-text="$count"></output>
    </main>
  `;
</script>
""",
        datastar_runtime_source,
    )

    await page.evaluate(
        """() => {
            const host = document.querySelector("#host");
            document.dispatchEvent(new CustomEvent("datastar:scan", { detail: { root: host } }));
        }"""
    )
    await wait_for_shadow_text(page, "#host", "#count", "0")

    await page.evaluate("""() => document.querySelector("#host").shadowRoot.querySelector("#increment").click()""")

    await wait_for_shadow_text(page, "#host", "#count", "1")


@pytest.mark.skipif(not PLAYWRIGHT_AVAILABLE, reason="Playwright not available")
@pytest.mark.asyncio
async def test_late_plugin_registration_does_not_refire_data_init(page, datastar_runtime_source):
    """Registering a late plugin should not re-run existing data-init handlers."""
    await load_datastar_page(
        page,
        """
<main data-signals='{"count": 0}' data-init="$count++">
  <div id="late" data-late-test></div>
  <output id="count" data-text="$count"></output>
</main>
""",
        datastar_runtime_source,
    )

    await wait_for_dom_text(page, "#count", "1")
    await page.evaluate(
        """() => {
            window.__latePluginRuns = 0;
            window.__datastar.attribute({
                name: "late-test",
                apply() {
                    window.__latePluginRuns++;
                },
            });
        }"""
    )

    await page.wait_for_function("window.__latePluginRuns === 1")
    await page.wait_for_timeout(50)

    assert await page.locator("#count").text_content() == "1"


@pytest.mark.skipif(not PLAYWRIGHT_AVAILABLE, reason="Playwright not available")
@pytest.mark.asyncio
async def test_persist_prehydrates_ifmissing_defaults_and_emits_starhtml_source_event(
    page, datastar_runtime_source
):
    """Persisted values win, Datastar patches stay vanilla, and StarHTML emits source metadata."""
    await load_datastar_page_at_origin(
        page,
        """
<script>
  localStorage.clear();
  sessionStorage.clear();
  localStorage.setItem("starhtml-persist:settings", JSON.stringify({ theme: "persisted" }));
  window.__signalPatches = [];
  window.__signalSources = [];
  document.addEventListener("starhtml:signal-source", event => {
    window.__signalSources.push(event.detail);
  });
  document.addEventListener("datastar-signal-patch", event => {
    window.__signalPatches.push(event.detail);
  });
</script>
<main data-signals:theme__ifmissing="'default'">
  <output id="theme" data-text="$theme"></output>
</main>
""",
        datastar_runtime_source,
    )

    await wait_for_dom_text(page, "#theme", "persisted")

    assert await page.evaluate(
        """() => window.__signalPatches.some(detail =>
            detail?.theme === "persisted" &&
            !("signals" in detail) &&
            !("source" in detail)
        )"""
    )
    assert await page.evaluate(
        """() => window.__signalSources.some(detail =>
            detail?.source === "persist" &&
            detail?.signals?.theme === "persisted" &&
            detail?.paths?.includes("theme") &&
            detail?.phase === "before"
        )"""
    )
