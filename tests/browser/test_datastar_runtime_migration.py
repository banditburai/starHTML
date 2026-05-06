"""Browser-level Datastar runtime migration tests.

These tests intentionally load StarHTML's patched local Datastar bundle instead
of a CDN copy so migration coverage follows the vendored runtime.
"""

import json
import re
import sys
from pathlib import Path

import pytest
import pytest_asyncio

try:
    from playwright.async_api import Page, async_playwright

    PLAYWRIGHT_AVAILABLE = True
except ImportError:  # pragma: no cover - exercised only when the optional dep is absent
    Page = None
    async_playwright = None
    PLAYWRIGHT_AVAILABLE = False


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATASTAR_RUNTIME = PROJECT_ROOT / "src" / "starhtml" / "static" / "js" / "datastar.js"
DATASTAR_UPSTREAM = PROJECT_ROOT / "patches" / "datastar-upstream.js"
STARAPP_PATH = PROJECT_ROOT / "src" / "starhtml" / "starapp.py"
sys.path.insert(0, str(PROJECT_ROOT / "patches"))
from patch_definitions import apply_all  # noqa: E402


@pytest.fixture(scope="session")
def datastar_runtime_source() -> str:
    """Return the built StarHTML Datastar runtime used by normal app pages."""
    if DATASTAR_RUNTIME.exists():
        return DATASTAR_RUNTIME.read_text()

    version_match = re.search(r'DATASTAR_VERSION\s*=\s*["\']([^"\']+)["\']', STARAPP_PATH.read_text())
    if not version_match:
        pytest.fail("DATASTAR_VERSION not found in src/starhtml/starapp.py")
    return apply_all(DATASTAR_UPSTREAM.read_text(), version_match.group(1).split("+")[0])


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


async def load_datastar_page(page: Page, body: str, datastar_source: str) -> None:
    """Load a page with StarHTML's local Datastar runtime and wait for scans."""
    await page.set_content(datastar_test_page(body, datastar_source), wait_until="domcontentloaded")


async def wait_for_dom_text(page: Page, selector: str, expected: str) -> None:
    """Wait until a selector has the expected text content."""
    await page.wait_for_function(
        """([selector, expected]) => document.querySelector(selector)?.textContent === expected""",
        arg=[selector, expected],
    )


async def dispatch_signal_patch(page: Page, signals: dict[str, object]) -> None:
    """Patch Datastar signals through the public runtime API."""
    await page.evaluate(
        """signals => window.__datastar.mergePatch(signals)""",
        signals,
    )


async def read_signals(page: Page, selector: str = "#signals") -> dict[str, object]:
    """Read a JSON signal snapshot rendered by ``data-json-signals``."""
    text = await page.locator(selector).text_content()
    return json.loads(text or "{}")


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
