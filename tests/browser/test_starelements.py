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
        return Div((count := Local("count", 5)), Span(data_text=count + 1, id="static"))  # no SSR fallback text

    app, rt = star_app()
    app.register(EarlyHost)

    @rt("/")
    def index():
        x = Signal("x", 0)
        return Div(EarlyHost(), x, Button("bump", id="bump", data_on_click=x.set(x + 1)), Span(data_text=x, id="xs"))

    root = "document.querySelector('early-host').shadowRoot" if shadow else "document"
    await page.add_init_script("document.addEventListener('datastar-ready', () => { window.__ready = (window.__ready || 0) + 1 })")
    async with served(page, app) as errors:
        await page.goto(f"{ORIGIN}/", wait_until="load")
        await text_of(page, "#xs", "0")  # page-level scan happened
        await page.wait_for_function(f"{root}.querySelector('#static')?.textContent === '6'")  # host content reactive
        await page.locator("#bump").click()
        await text_of(page, "#xs", "1")
        assert await page.evaluate("window.__ready") == 1  # document scan ran exactly once
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
        # `__root` stays in the markup (Datastar ignores unknown modifiers), so a later rescope cannot re-capture it
        assert "data-ref__root=page_box" in attrs["#ref_page"], attrs
        assert "data-computed:shout__root=$page_name + '!'" in attrs["#shout"], attrs
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


# ---------------------------------------------------------------------------------------------------------------------
# 2c (not applicable) / 2e / 2f: a host patched in after the first scan upgrades and renders (hosts are bare, `$$` only
# lives in inert templates); bad attribute values fall back to the codec default with a named warning; emit() warns on
# events not declared with @element(events=[...]).
# ---------------------------------------------------------------------------------------------------------------------


async def test_late_host_codec_fallback_and_declared_events(page):
    from starhtml import Button, Div, Span, elements, sse, star_app
    from starhtml.xtend import Script

    from starelements import Local, element

    @element("late-host", events=["ping"])
    def LateHost():
        count = Local("count", 7)
        return Div(count, Span(data_text=count + 1, cls="n"), Script("el.emit('ping'); el.emit('pong');"))

    app, rt = star_app()
    app.register(LateHost)

    @rt("/")
    def index():
        return Div(Button("add", id="add", data_on_click="@get('/add')"), Div(id="out"))

    @rt("/add")
    @sse
    def add():
        yield elements(Div(LateHost(count="abc", id="late")), selector="#out", mode="inner")

    warnings: list[str] = []
    page.on("console", lambda m: warnings.append(m.text) if m.type == "warning" else None)
    async with served(page, app) as errors:
        await page.goto(f"{ORIGIN}/", wait_until="load")
        await page.locator("#add").click()
        await page.wait_for_function("document.querySelector('#late .n')?.textContent === '8'")  # default 7, not NaN
        assert await page.evaluate("document.querySelector('#late').hasAttribute('data-star-ready')")
        assert any("CodecParseError" in w and "count" in w for w in warnings), warnings
        assert any("UndeclaredEvent" in w and "pong" in w for w in warnings), warnings
        assert not any('emit("ping")' in w for w in warnings), warnings  # declared: no warning
        assert not errors, errors


# ---------------------------------------------------------------------------------------------------------------------
# Review follow-ups: __root stays idempotent across later patches; nested hosts are not re-prefixed by the outer
# host's rescope; a patch that re-sends the host's outer markup re-renders it; an empty int default registers.
# ---------------------------------------------------------------------------------------------------------------------


async def test_root_escape_survives_later_patches_and_nested_hosts_keep_their_scope(page):
    from starhtml import Button, Div, Signal, Span, elements, sse, star_app

    from starelements import Local, element

    @element("inner-host")
    def InnerHost():
        n = Local("n", 2)
        return Div(n, Span(data_text="$$dbl", id="inner_dbl", **{"data-computed:dbl": "$$n * 2"}), Div(data_ref="box", id="inner_ref"))

    @element("outer-host")
    def OuterHost():
        text = Local("text", "hi")
        return Div(
            text,
            Div(**{"data-ref__root": "page_box"}, id="ref_page"),
            Span(data_text="$shout", id="shout", **{"data-computed:shout__root": "$page_name + '!'"}),
            Div(id="slot"),
            InnerHost(),
        )

    app, rt = star_app()
    app.register(OuterHost, InnerHost)

    @rt("/")
    def index():
        return Div(Signal("page_name", "ada"), OuterHost(), Button("go", id="go", data_on_click="@get('/patch')"))

    @rt("/patch")
    @sse
    def patch():
        yield elements(Span(data_text="$$text", id="patched"), selector="#slot", mode="inner")

    async with served(page, app) as errors:
        await page.goto(f"{ORIGIN}/", wait_until="load")
        await text_of(page, "#shout", "ada!")
        await text_of(page, "#inner_dbl", "4")
        inner_ref = await page.evaluate("document.querySelector('#inner_ref').getAttribute('data-ref')")
        assert inner_ref.startswith("_star_inner_host_id") and inner_ref.endswith("_box"), inner_ref
        for _ in range(2):  # every patch into the outer host rescopes its children again
            await page.locator("#go").click()
            await text_of(page, "#patched", "hi")
        names = await page.evaluate("[...document.querySelector('#ref_page').attributes].map(a => a.name + '=' + a.value)")
        assert "data-ref__root=page_box" in names, names  # modifier kept, name never namespaced
        assert await page.evaluate("document.querySelector('#shout').hasAttribute('data-computed:shout__root')")
        await text_of(page, "#shout", "ada!")
        assert await page.evaluate("document.querySelector('#inner_ref').getAttribute('data-ref')") == inner_ref
        await text_of(page, "#inner_dbl", "4")  # inner computed key not re-prefixed by the outer rescope
        assert not errors, errors


async def test_repatching_outer_markup_rerenders_host(page):
    from starhtml import Button, Div, Span, elements, sse, star_app

    from starelements import Local, element

    @element("wrap-host")
    def WrapHost():
        n = Local("n", 1)
        return Div(n, Span(data_text=n + 1, cls="n"), Button("+", cls="inc", data_on_click=n.set(n + 1)))

    app, rt = star_app()
    app.register(WrapHost)

    @rt("/")
    def index():
        return Div(Div(WrapHost(id="h"), id="wrap"), Button("re", id="re", data_on_click="@get('/re')"))

    @rt("/re")
    @sse
    def re_send():
        yield elements(Div(WrapHost(id="h"), id="wrap"), selector="#wrap", mode="outer")  # server markup is bare

    async with served(page, app) as errors:
        await page.goto(f"{ORIGIN}/", wait_until="load")
        await page.wait_for_function("document.querySelector('#h .n')?.textContent === '2'")
        await page.locator("#h .inc").click()
        await page.wait_for_function("document.querySelector('#h .n')?.textContent === '3'")
        await page.locator("#re").click()
        await page.wait_for_function("document.querySelector('#h .n')?.textContent === '3'")  # re-rendered, state kept
        assert await page.evaluate("getComputedStyle(document.querySelector('#h')).visibility") == "visible"
        assert await page.evaluate("document.querySelector('#h').hasAttribute('data-star-ready')")
        await page.locator("#h .inc").click()
        await page.wait_for_function("document.querySelector('#h .n')?.textContent === '4'")
        assert not errors, errors


async def test_empty_int_default_does_not_abort_registration(page):
    from starhtml import Div, Span, star_app

    from starelements import Local, element

    @element("nullable-host")
    def NullableHost():
        return Div(Local("n", None, type_=int), Span("x", data_text="$$n + 1", id="n"))  # empty default -> 0, not NaN

    @element("after-host")
    def AfterHost():
        return Div(Local("k", 3), Span(data_text="$$k + 1", id="k"))

    app, rt = star_app()
    app.register(NullableHost, AfterHost)

    @rt("/")
    def index():
        return Div(NullableHost(), AfterHost())

    async with served(page, app) as errors:
        await page.goto(f"{ORIGIN}/", wait_until="load")
        await text_of(page, "#n", "1")
        await text_of(page, "#k", "4")  # the template after it still registered
        assert not errors, errors


# ---------------------------------------------------------------------------------------------------------------------
# Patch modes without an upstream scope-children hook (append/prepend/before/after/replace, selectorless outer):
# fragments are pre-scoped in a capture-phase datastar-fetch listener before Datastar parses them.
# ---------------------------------------------------------------------------------------------------------------------


@pytest.mark.parametrize("mode", ["append", "prepend", "before", "after", "replace", "inner", "outer-by-id"])
async def test_patch_modes_into_host_are_prescoped(page, mode):
    from starhtml import Button, Div, Span, elements, sse, star_app

    from starelements import Local, element

    @element("mode-host")
    def ModeHost():
        count = Local("count", 5)
        return Div(count, Div(Span("old", id="anchor"), id="slot"), Div(**{"data-computed:dbl": "$$count * 2"}, id="decl"))

    app, rt = star_app()
    app.register(ModeHost)

    @rt("/")
    def index():
        return Div(ModeHost(), Button("go", id="go", data_on_click="@get('/patch')"))

    @rt("/patch")
    @sse
    def patch():
        frag = Span(data_text="$$count + 1", id="patched", **{"data-computed:tripled": "$$count * 3"})
        if mode == "outer-by-id":
            yield elements(Div(frag, id="slot"))  # no selector: matched by id, outer mode
        else:
            selector = "#slot" if mode in ("append", "prepend", "inner") else "#anchor"
            yield elements(frag, selector=selector, mode=mode)

    async with served(page, app) as errors:
        await page.goto(f"{ORIGIN}/", wait_until="load")
        await page.locator("#go").click()
        await text_of(page, "#patched", "6")
        attrs = await page.evaluate("[...document.querySelector('#patched').attributes].map(a => a.name + '=' + a.value)")
        assert any(a.startswith("data-computed:_star_mode_host_id") and a.endswith("_tripled=$_star_mode_host_id0_count * 3") for a in attrs), attrs
        assert await page.evaluate("document.querySelector('#patched').closest('mode-host') !== null")
        assert not errors, errors
