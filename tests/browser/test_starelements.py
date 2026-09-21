"""Browser coverage for StarElements (optional dep) running on StarHTML's Datastar bundle.

Run with BOTH editable checkouts (StarElements depends on starhtml, so a bare ``--with-editable ../starelements``
resolves a cached starhtml wheel with stale static JS); rebuild the runtimes first (``bun run build`` here,
``python scripts/build.py`` in starelements):

    uv run --with playwright --with-editable ../starelements --with-editable . \
        pytest tests/browser/test_starelements.py -q

Pages are served by a real ``star_app`` proxied through ``page.route`` (same shape as the CSP end-to-end test), so
the StarElements runtime, templates, import map and SSE responses are exactly what production serves.
"""

from __future__ import annotations

import contextlib
import os

import pytest

try:
    import starelements  # noqa: F401

    STARELEMENTS_AVAILABLE = True
except ImportError:
    STARELEMENTS_AVAILABLE = False

try:
    from playwright.async_api import async_playwright

    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False

import pytest_asyncio

pytestmark = [
    pytest.mark.asyncio,
    pytest.mark.skipif(not STARELEMENTS_AVAILABLE, reason="starelements not installed"),
    pytest.mark.skipif(not PLAYWRIGHT_AVAILABLE, reason="playwright not installed"),
]

ORIGIN = "https://starhtml.test"


@pytest_asyncio.fixture
async def page():
    browser_name = os.environ.get("STARHTML_BROWSER", "chromium")
    async with async_playwright() as playwright:
        browser = await getattr(playwright, browser_name).launch()
        context = await browser.new_context()
        test_page = await context.new_page()
        try:
            yield test_page
        finally:
            await context.close()
            await browser.close()


@contextlib.asynccontextmanager
async def served(page, app):
    """Proxy ``app`` (ASGI) at ORIGIN through page.route; yields the list of console error texts."""
    import httpx

    client = httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url=ORIGIN)

    async def proxy(route):
        req = route.request
        resp = await client.request(req.method, req.url.replace(ORIGIN, ""), headers=req.headers)
        headers = {k: v for k, v in resp.headers.items() if k.lower() in ("content-type", "content-security-policy")}
        await route.fulfill(status=resp.status_code, headers=headers, body=resp.content)

    errors: list[str] = []
    page.on("console", lambda m: errors.append(m.text) if m.type == "error" else None)
    page.on("pageerror", lambda e: errors.append(str(e)))
    await page.route(f"{ORIGIN}/**", proxy)
    try:
        yield errors
    finally:
        await page.unroute(f"{ORIGIN}/**", proxy)
        await client.aclose()


async def text_of(page, selector: str, expected: str, timeout: int = 5000) -> None:
    await page.wait_for_function(
        "([s, e]) => document.querySelector(s)?.textContent === e", arg=[selector, expected], timeout=timeout
    )


# ---------------------------------------------------------------------------------------------------------------------
# Datastar defers its first scan to a timeout and then scans `roots.size ? [...roots] : [documentElement]`. A host
# that connects before that timeout (StarElements defines elements as soon as its module runs) dispatches
# `datastar:scan`; the patched listener must not register the host as a root or the document is never scanned.
# ---------------------------------------------------------------------------------------------------------------------


@pytest.mark.parametrize("shadow", [False, True], ids=["light", "shadow"])
async def test_host_connecting_before_first_scan_does_not_starve_document_scan(page, shadow):
    from starhtml import Button, Div, Signal, Span, star_app

    from starelements import Local, element

    @element("early-host", shadow=shadow)
    def EarlyHost():
        return Div((count := Local("count", 5)), Span(data_text=count, id="static"))

    app, rt = star_app()
    app.register(EarlyHost)

    @rt("/")
    def index():
        x = Signal("x", 0)
        return Div(EarlyHost(), x, Button("bump", id="bump", data_on_click=x.set(x + 1)), Span(data_text=x, id="xs"))

    root = "document.querySelector('early-host').shadowRoot" if shadow else "document"
    async with served(page, app) as errors:
        await page.goto(f"{ORIGIN}/", wait_until="load")
        await text_of(page, "#xs", "0")  # page-level scan happened
        await page.wait_for_function(f"{root}.querySelector('#static')?.textContent === '5'")  # host scanned too
        await page.locator("#bump").click()
        await text_of(page, "#xs", "1")
        assert not errors, errors


# ---------------------------------------------------------------------------------------------------------------------
# 2a: data-scope-children — SSE fragments patched into a host may carry raw `$$` and get namespaced before evaluation
# ---------------------------------------------------------------------------------------------------------------------


async def test_sse_fragment_patched_into_host_is_rescoped(page):
    from starhtml import Button, Div, Span, elements, sse, star_app

    from starelements import Local, element

    @element("scope-host")
    def ScopeHost():
        return Div((count := Local("count", 5)), Span(data_text=count, id="static"), Div(id="slot"))

    app, rt = star_app()
    app.register(ScopeHost)

    @rt("/")
    def index():
        return Div(ScopeHost(), Button("go", id="go", data_on_click="@get('/patch')"))

    @rt("/patch")
    @sse
    def patch():
        # `data-computed:` keys and `data-ref` values are namespaced too; the second patch morphs onto the nodes the
        # first one left behind, so the rescope must be idempotent (no `ns_ns_` doubling).
        yield elements(
            Div(Span(data_text="$$count", id="patched"), Span(data_text="$$doubled", id="dbl"), **{"data-computed:doubled": "$$count * 2", "data-ref": "box"}),
            selector="#slot", mode="inner",
        )

    async with served(page, app) as errors:
        await page.goto(f"{ORIGIN}/", wait_until="load")
        await text_of(page, "#static", "5")
        for _ in range(2):
            await page.locator("#go").click()
            await text_of(page, "#patched", "5")
            await text_of(page, "#dbl", "10")
        ns = await page.evaluate("document.querySelector('#static').getAttribute('data-text')")
        assert await page.evaluate("document.querySelector('#patched').getAttribute('data-text')") == ns
        names = await page.evaluate("[...document.querySelector('#slot > div').attributes].map(a => a.name + '=' + a.value)")
        prefix = ns[1:-len("count")]  # `$_star_scope_host_id0_`
        assert f"data-computed:{prefix}doubled=${prefix}count * 2" in names, names
        assert f"data-ref={prefix}box" in names, names
        assert await page.evaluate("document.querySelector('scope-host').hasAttribute('data-scope-children')")
        assert not errors, errors


# ---------------------------------------------------------------------------------------------------------------------
# 2b: attribute-aware rewrite — Local emits `$$name` for data-bind/data-indicator/data-ref; `__root` escapes to page scope
# ---------------------------------------------------------------------------------------------------------------------


async def test_local_bind_ref_and_root_escape(page):
    from starhtml import Div, Input, Signal, Span, star_app

    from starelements import Local, element

    @element("bind-host")
    def BindHost():
        text = Local("text", "hi")
        return Div(
            text,
            Input(data_bind=text, id="inp"),
            Span(data_text=text, id="echo"),
            Div(data_ref="box", id="ref_local"),  # refs inside a component are local by contract
            Div(**{"data-ref__root": "page_box"}, id="ref_page"),
            Span(data_text="$shout", id="shout", **{"data-computed:shout__root": "$page_name + '!'"}),
        )

    app, rt = star_app()
    app.register(BindHost)

    @rt("/")
    def index():
        text, page_name = Signal("text", "page"), Signal("page_name", "ada")
        return Div(text, page_name, BindHost(), Input(data_bind=text, id="page_inp"), Span(data_text=text, id="page_echo"))

    async with served(page, app) as errors:
        await page.goto(f"{ORIGIN}/", wait_until="load")
        await text_of(page, "#echo", "hi")
        await text_of(page, "#page_echo", "page")
        await text_of(page, "#shout", "ada!")
        await page.locator("#inp").fill("yo")
        await text_of(page, "#echo", "yo")
        assert await page.evaluate("document.querySelector('#page_echo').textContent") == "page"  # still page scope
        attrs = await page.evaluate(
            "Object.fromEntries(['#inp','#ref_local','#ref_page','#shout'].map(s => [s, [...document.querySelector(s).attributes].map(a => a.name + '=' + a.value)]))"
        )
        ns = attrs["#inp"][[a.startswith("data-bind=") for a in attrs["#inp"]].index(True)].split("=")[1].removesuffix("text")
        assert ns.startswith("_star_bind_host_id"), attrs
        assert f"data-ref={ns}box" in attrs["#ref_local"]
        assert "data-ref=page_box" in attrs["#ref_page"] and not any(a.startswith("data-ref__root") for a in attrs["#ref_page"])
        assert "data-computed:shout=$page_name + '!'" in attrs["#shout"], attrs
        assert not errors, errors


# ---------------------------------------------------------------------------------------------------------------------
# 2d: CSP — under star_app(csp=True) component setup/static scripts compile through nonced <script>s (no unsafe-eval)
# ---------------------------------------------------------------------------------------------------------------------


async def test_component_scripts_run_under_csp_without_unsafe_eval(page):
    from starhtml import Button, Div, Span, star_app
    from starhtml.xtend import Script

    from starelements import Local, element

    @element("csp-host")
    def CspHost():
        count = Local("count", 1)
        return Div(
            count,
            Span(data_text=count, id="count"),
            Button("bump", id="bump", data_on_click=count.set(count + 1)),
            Script("window.__static_ran = (window.__static_ran || 0) + 1", data_static=True),
            Script("$$count = $$count + 40; effect(() => { el.dataset.seen = String($$count); });"),
        )

    app, rt = star_app(csp=True)
    app.register(CspHost)

    @rt("/")
    def index():
        return Div(CspHost())

    async with served(page, app) as errors:
        response = await page.goto(f"{ORIGIN}/", wait_until="load")
        csp = response.headers.get("content-security-policy", "")
        assert "'nonce-" in csp and "unsafe-eval" not in csp, csp
        await text_of(page, "#count", "41")  # setup script ran (with `$$` scoping through the `with` proxy)
        await page.locator("#bump").click()
        await text_of(page, "#count", "42")
        assert await page.evaluate("document.querySelector('csp-host').dataset.seen") == "42"  # setup effect tracked
        assert await page.evaluate("window.__static_ran") == 1
        assert not errors, errors
