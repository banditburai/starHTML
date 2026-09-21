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
        yield elements(Span(data_text="$$count", id="patched"), selector="#slot", mode="inner")

    async with served(page, app) as errors:
        await page.goto(f"{ORIGIN}/", wait_until="load")
        await text_of(page, "#static", "5")
        await page.locator("#go").click()
        await text_of(page, "#patched", "5")
        ns = await page.evaluate("document.querySelector('#static').getAttribute('data-text')")
        assert await page.evaluate("document.querySelector('#patched').getAttribute('data-text')") == ns
        assert await page.evaluate("document.querySelector('scope-host').hasAttribute('data-scope-children')")
        assert not errors, errors
