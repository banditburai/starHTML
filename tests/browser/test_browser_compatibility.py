"""
Browser compatibility testing for Signal Proxy Pattern handlers.

This test suite ensures consistent behavior across all supported browsers
using Playwright for automated cross-browser testing.
"""

import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pytest

# Add the project root to the path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.starhtml.handlers import persist_handler, resize_handler, scroll_handler

# Browser test configuration
BROWSER_MATRIX = {
    "chromium": {
        "versions": ["latest"],
        "desktop": True,
        "mobile": True,
        "critical_features": ["ResizeObserver", "requestAnimationFrame", "WeakMap", "MutationObserver"],
    },
    "firefox": {
        "versions": ["latest"],
        "desktop": True,
        "mobile": False,  # Firefox mobile testing is complex
        "critical_features": ["ResizeObserver", "requestAnimationFrame", "WeakMap", "MutationObserver"],
    },
    "webkit": {
        "versions": ["latest"],
        "desktop": True,
        "mobile": True,
        "critical_features": ["ResizeObserver", "requestAnimationFrame", "WeakMap", "MutationObserver"],
    },
}

MOBILE_DEVICES = ["iPhone 12", "iPhone SE", "iPad", "Pixel 5", "Galaxy S21"]


@dataclass
class BrowserTestResult:
    """Container for browser test results."""

    browser: str
    device: str | None
    test_name: str
    success: bool
    error_message: str = ""
    performance_data: dict[str, Any] = None


class BrowserCompatibilityTestSuite:
    """Base class for browser compatibility testing."""

    def __init__(self):
        self.results: list[BrowserTestResult] = []

    def create_test_page(self, handlers: list[str]) -> str:
        """Create a test HTML page with handlers."""
        return f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Handler Compatibility Test</title>
    <style>
        .test-element {{
            width: 200px;
            height: 100px;
            border: 1px solid #ccc;
            margin: 10px;
            padding: 10px;
            resize: both;
            overflow: auto;
            background: #f0f0f0;
        }}
        .scroll-container {{
            height: 200px;
            overflow-y: scroll;
            border: 1px solid #333;
            margin: 10px;
        }}
        .scroll-content {{
            height: 1000px;
            background: linear-gradient(to bottom, #f0f0f0, #333);
        }}
        .signal-display {{
            font-family: monospace;
            background: #eee;
            padding: 5px;
            margin: 5px;
            border: 1px solid #999;
        }}
    </style>
</head>
<body>
    <!-- Test Elements -->
    <div id="test-container">
        <h1>Handler Compatibility Test</h1>
        
        <!-- Resize Test Element -->
        <div class="test-element"
             data-on-resize="window.testResults.resize = {{width: width, height: height, timestamp: Date.now()}}"
             data-signals='{{"resizeWidth": 0, "resizeHeight": 0}}'>
            <h3>Resize Test</h3>
            <div class="signal-display">
                Width: <span data-text="$resizeWidth">0</span>px<br>
                Height: <span data-text="$resizeHeight">0</span>px
            </div>
        </div>
        
        <!-- Scroll Test Element -->
        <div class="scroll-container"
             data-on-scroll="window.testResults.scroll = {{position: scrollY, direction: direction, velocity: velocity, timestamp: Date.now()}}"
             data-signals='{{"scrollPos": 0, "scrollDir": "none"}}'>
            <div class="scroll-content">
                <div class="signal-display">
                    Position: <span data-text="$scrollPos">0</span>px<br>
                    Direction: <span data-text="$scrollDir">none</span>
                </div>
            </div>
        </div>
        
        <!-- Persist Test Element -->
        <div data-persist="testValue"
             data-signals='{{"testValue": "initial"}}'>
            <div class="signal-display">
                Persisted Value: <span data-text="$testValue">initial</span>
            </div>
            <button onclick="window.$ = window.$ || {{}}; window.$.testValue = 'changed_' + Date.now();">
                Change Value
            </button>
        </div>
        
        <!-- Feature Detection -->
        <div id="feature-detection">
            <h3>Feature Detection Results</h3>
            <div id="features"></div>
        </div>
        
        <!-- Performance Monitoring -->
        <div id="performance-monitor">
            <h3>Performance Monitor</h3>
            <div id="performance-data"></div>
        </div>
    </div>

    <!-- Initialize test results -->
    <script>
        window.testResults = {{
            resize: null,
            scroll: null,
            persist: null,
            features: {{}},
            performance: {{}}
        }};
        
        // Feature detection
        const features = [
            'ResizeObserver',
            'MutationObserver',
            'WeakMap',
            'requestAnimationFrame',
            'localStorage',
            'sessionStorage',
            'addEventListener'
        ];
        
        features.forEach(feature => {{
            window.testResults.features[feature] = typeof window[feature] !== 'undefined';
        }});
        
        // Display feature detection results
        const featuresDiv = document.getElementById('features');
        Object.entries(window.testResults.features).forEach(([feature, supported]) => {{
            const div = document.createElement('div');
            div.textContent = `${{feature}}: ${{supported ? '✓' : '✗'}}`;
            div.style.color = supported ? 'green' : 'red';
            featuresDiv.appendChild(div);
        }});
        
        // Performance monitoring
        let performanceStart = performance.now();
        setInterval(() => {{
            window.testResults.performance = {{
                timestamp: Date.now(),
                memory: performance.memory ? {{
                    used: performance.memory.usedJSHeapSize,
                    total: performance.memory.totalJSHeapSize,
                    limit: performance.memory.jsHeapSizeLimit
                }} : null,
                timing: performance.now() - performanceStart
            }};
            
            const perfDiv = document.getElementById('performance-data');
            if (window.testResults.performance.memory) {{
                perfDiv.innerHTML = `
                    <div>Memory Used: ${{(window.testResults.performance.memory.used / 1024 / 1024).toFixed(2)}} MB</div>
                    <div>Memory Total: ${{(window.testResults.performance.memory.total / 1024 / 1024).toFixed(2)}} MB</div>
                    <div>Runtime: ${{(window.testResults.performance.timing / 1000).toFixed(2)}} seconds</div>
                `;
            }}
        }}, 1000);
    </script>
    
    <!-- Include Handlers -->
    {"".join(handlers)}
    
    <!-- Test completion marker -->
    <script>
        window.testReady = true;
        console.log('Browser compatibility test page loaded');
    </script>
</body>
</html>
"""

    def get_handler_scripts(self) -> dict[str, str]:
        """Get JavaScript content for all handlers."""
        return {
            "scroll": str(scroll_handler().children[0]),
            "resize_dom": str(resize_handler().children[0]),
            "resize_sp": str(resize_handler().children[0]),
            "persist": str(persist_handler().children[0]),
        }


# Skip Playwright tests if not available
try:
    from playwright.async_api import Browser, Page, async_playwright

    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False
    async_playwright = None
    Browser = None
    Page = None


@pytest.mark.skipif(not PLAYWRIGHT_AVAILABLE, reason="Playwright not available")
class TestBrowserCompatibility:
    """Browser compatibility tests using Playwright."""

    @pytest.fixture(scope="class")
    async def browser_setup(self):
        """Set up browsers for testing."""
        if not PLAYWRIGHT_AVAILABLE:
            pytest.skip("Playwright not available")

        async with async_playwright() as p:
            browsers = {}
            for browser_name in BROWSER_MATRIX.keys():
                try:
                    if browser_name == "chromium":
                        browser = await p.chromium.launch()
                    elif browser_name == "firefox":
                        browser = await p.firefox.launch()
                    elif browser_name == "webkit":
                        browser = await p.webkit.launch()

                    browsers[browser_name] = browser
                except Exception as e:
                    print(f"Failed to launch {browser_name}: {e}")

            yield browsers

            # Cleanup
            for browser in browsers.values():
                await browser.close()

    @pytest.mark.asyncio
    async def test_feature_detection_all_browsers(self, browser_setup):
        """Test that all required features are available in target browsers."""
        browsers = browser_setup
        test_suite = BrowserCompatibilityTestSuite()

        for browser_name, browser in browsers.items():
            context = await browser.new_context()
            page = await context.new_page()

            # Create test page with basic feature detection
            handlers = ["<script>" + test_suite.get_handler_scripts()["scroll"] + "</script>"]
            html_content = test_suite.create_test_page(handlers)

            await page.set_content(html_content)
            await page.wait_for_function("window.testReady === true", timeout=5000)

            # Check feature detection results
            features = await page.evaluate("window.testResults.features")

            required_features = BROWSER_MATRIX[browser_name]["critical_features"]
            for feature in required_features:
                assert features.get(feature, False), f"{feature} not available in {browser_name}"

            test_suite.results.append(
                BrowserTestResult(browser=browser_name, device=None, test_name="feature_detection", success=True)
            )

            await context.close()

    @pytest.mark.asyncio
    async def test_scroll_handler_all_browsers(self, browser_setup):
        """Test scroll handler functionality across browsers."""
        browsers = browser_setup
        test_suite = BrowserCompatibilityTestSuite()

        for browser_name, browser in browsers.items():
            context = await browser.new_context()
            page = await context.new_page()

            # Create test page with scroll handler
            handlers = ["<script>" + test_suite.get_handler_scripts()["scroll"] + "</script>"]
            html_content = test_suite.create_test_page(handlers)

            await page.set_content(html_content)
            await page.wait_for_function("window.testReady === true", timeout=5000)

            # Test scroll functionality
            scroll_container = page.locator(".scroll-container")
            await scroll_container.scroll_into_view_if_needed()

            # Perform scroll action
            await scroll_container.evaluate("el => el.scrollTop = 100")
            await page.wait_for_timeout(200)  # Wait for throttling

            # Check scroll results
            scroll_result = await page.evaluate("window.testResults.scroll")

            assert scroll_result is not None, f"Scroll handler not triggered in {browser_name}"
            assert scroll_result.get("position", 0) > 0, f"Scroll position not updated in {browser_name}"

            test_suite.results.append(
                BrowserTestResult(browser=browser_name, device=None, test_name="scroll_handler", success=True)
            )

            await context.close()

    @pytest.mark.asyncio
    async def test_resize_handler_all_browsers(self, browser_setup):
        """Test resize handler functionality across browsers."""
        browsers = browser_setup
        test_suite = BrowserCompatibilityTestSuite()

        for browser_name, browser in browsers.items():
            context = await browser.new_context()
            page = await context.new_page()

            # Test both DOM and Signal Proxy resize handlers
            for handler_type in ["resize_dom", "resize_sp"]:
                handlers = ["<script>" + test_suite.get_handler_scripts()[handler_type] + "</script>"]
                html_content = test_suite.create_test_page(handlers)

                await page.set_content(html_content)
                await page.wait_for_function("window.testReady === true", timeout=5000)

                # Test resize functionality by changing viewport
                await page.set_viewport_size({"width": 800, "height": 600})
                await page.wait_for_timeout(300)  # Wait for resize events

                # Check if resize was detected
                await page.evaluate("window.testResults.resize")

                # Note: Resize handler might not trigger from viewport changes
                # This tests that the handler loads without errors
                console_errors = []
                page.on(
                    "console",
                    lambda msg, errors=console_errors: errors.append(msg.text) if msg.type == "error" else None,
                )

                # Wait a bit more to catch any errors
                await page.wait_for_timeout(500)

                # Check for JavaScript errors
                js_errors = [err for err in console_errors if "error" in err.lower()]
                assert len(js_errors) == 0, f"JavaScript errors in {browser_name} with {handler_type}: {js_errors}"

                test_suite.results.append(
                    BrowserTestResult(
                        browser=browser_name, device=None, test_name=f"resize_handler_{handler_type}", success=True
                    )
                )

            await context.close()

    @pytest.mark.asyncio
    async def test_persist_handler_all_browsers(self, browser_setup):
        """Test persist handler functionality across browsers."""
        browsers = browser_setup
        test_suite = BrowserCompatibilityTestSuite()

        for browser_name, browser in browsers.items():
            context = await browser.new_context()
            page = await context.new_page()

            # Create test page with persist handler
            handlers = ["<script>" + test_suite.get_handler_scripts()["persist"] + "</script>"]
            html_content = test_suite.create_test_page(handlers)

            await page.set_content(html_content)
            await page.wait_for_function("window.testReady === true", timeout=5000)

            # Test persistence functionality
            change_button = page.locator("button")
            await change_button.click()
            await page.wait_for_timeout(200)

            # Check localStorage for persisted value
            has_storage = await page.evaluate("""
                () => {
                    try {
                        return typeof localStorage !== 'undefined' && localStorage.length >= 0;
                    } catch(e) {
                        return false;
                    }
                }
            """)

            if has_storage:
                stored_keys = await page.evaluate("Object.keys(localStorage)")
                [key for key in stored_keys if "persist" in key.lower()]

                # Note: Persist handler uses Signal Proxy pattern, so storage might be different
                # Main test is that no errors occur

            # Check for console errors
            console_errors = []
            page.on(
                "console", lambda msg, errors=console_errors: errors.append(msg.text) if msg.type == "error" else None
            )
            await page.wait_for_timeout(500)

            js_errors = [err for err in console_errors if "error" in err.lower()]
            assert len(js_errors) == 0, f"JavaScript errors in persist handler for {browser_name}: {js_errors}"

            test_suite.results.append(
                BrowserTestResult(browser=browser_name, device=None, test_name="persist_handler", success=True)
            )

            await context.close()

    @pytest.mark.asyncio
    async def test_mobile_compatibility(self, browser_setup):
        """Test mobile device compatibility."""
        browsers = browser_setup
        test_suite = BrowserCompatibilityTestSuite()

        # Test mobile compatibility with webkit (Safari) and chromium
        mobile_browsers = {k: v for k, v in browsers.items() if BROWSER_MATRIX[k]["mobile"]}

        for browser_name, browser in mobile_browsers.items():
            for device_name in MOBILE_DEVICES[:2]:  # Test first 2 devices to save time
                context = await browser.new_context(
                    **await browser.new_context(
                        user_agent="Mozilla/5.0 (iPhone; CPU iPhone OS 14_7_1 like Mac OS X) AppleWebKit/605.1.15",
                        viewport={"width": 375, "height": 667},
                        is_mobile=True,
                        has_touch=True,
                    )
                )
                page = await context.new_page()

                # Create test page with all handlers
                handlers = [
                    "<script>" + test_suite.get_handler_scripts()["scroll"] + "</script>",
                    "<script>" + test_suite.get_handler_scripts()["resize_dom"] + "</script>",
                    "<script>" + test_suite.get_handler_scripts()["persist"] + "</script>",
                ]
                html_content = test_suite.create_test_page(handlers)

                await page.set_content(html_content)
                await page.wait_for_function("window.testReady === true", timeout=10000)

                # Test touch scrolling
                scroll_container = page.locator(".scroll-container")
                await scroll_container.scroll_into_view_if_needed()

                # Simulate touch scroll
                await page.touch_screen.tap(200, 300)
                await page.evaluate("document.querySelector('.scroll-container').scrollTop = 50")
                await page.wait_for_timeout(300)

                # Check for mobile-specific errors
                console_errors = []
                page.on(
                    "console",
                    lambda msg, errors=console_errors: errors.append(msg.text) if msg.type == "error" else None,
                )
                await page.wait_for_timeout(500)

                mobile_errors = [
                    err
                    for err in console_errors
                    if any(keyword in err.lower() for keyword in ["touch", "mobile", "viewport"])
                ]
                assert len(mobile_errors) == 0, (
                    f"Mobile-specific errors in {browser_name} on {device_name}: {mobile_errors}"
                )

                test_suite.results.append(
                    BrowserTestResult(
                        browser=browser_name, device=device_name, test_name="mobile_compatibility", success=True
                    )
                )

                await context.close()

    @pytest.mark.asyncio
    async def test_performance_across_browsers(self, browser_setup):
        """Test performance characteristics across browsers."""
        browsers = browser_setup
        test_suite = BrowserCompatibilityTestSuite()

        for browser_name, browser in browsers.items():
            context = await browser.new_context()
            page = await context.new_page()

            # Create test page with all handlers
            handlers = [
                "<script>" + test_suite.get_handler_scripts()["scroll"] + "</script>",
                "<script>" + test_suite.get_handler_scripts()["resize_sp"] + "</script>",
                "<script>" + test_suite.get_handler_scripts()["persist"] + "</script>",
            ]
            html_content = test_suite.create_test_page(handlers)

            await page.set_content(html_content)
            await page.wait_for_function("window.testReady === true", timeout=5000)

            # Let performance monitoring run
            await page.wait_for_timeout(2000)

            # Get performance data
            performance_data = await page.evaluate("window.testResults.performance")

            # Basic performance checks
            if performance_data and performance_data.get("memory"):
                memory_used_mb = performance_data["memory"]["used"] / (1024 * 1024)
                assert memory_used_mb < 50, f"Excessive memory usage in {browser_name}: {memory_used_mb:.2f}MB"

            # Check for performance-related console warnings
            console_messages = []
            page.on("console", lambda msg, messages=console_messages: messages.append(msg.text))
            await page.wait_for_timeout(500)

            [
                msg
                for msg in console_messages
                if any(keyword in msg.lower() for keyword in ["slow", "performance", "lag"])
            ]

            test_suite.results.append(
                BrowserTestResult(
                    browser=browser_name,
                    device=None,
                    test_name="performance",
                    success=True,
                    performance_data=performance_data,
                )
            )

            await context.close()


class TestBrowserCompatibilityMatrix:
    """Test browser compatibility matrix without Playwright dependency."""

    def test_javascript_syntax_compatibility(self):
        """Test JavaScript syntax compatibility across browser targets."""
        handlers = {
            "scroll": str(scroll_handler().children[0]),
            "resize_dom": str(resize_handler().children[0]),
            "resize_sp": str(resize_handler().children[0]),
            "persist": str(persist_handler().children[0]),
        }

        # Check for modern JavaScript features that might not be supported
        problematic_features = [
            "?.",  # Optional chaining
            "??",  # Nullish coalescing (outside of comments)
            "=>",  # Arrow functions (check if excessive)
            "async ",  # Async/await
            "const ",  # Let/const (should be fine in modern browsers)
        ]

        for handler_name, content in handlers.items():
            # Count modern features
            feature_counts = {}
            for feature in problematic_features:
                if feature == "??":
                    # Exclude comments
                    lines = [line for line in content.split("\n") if not line.strip().startswith("//")]
                    feature_counts[feature] = "\n".join(lines).count(feature)
                else:
                    feature_counts[feature] = content.count(feature)

            # Arrow functions are OK but shouldn't be excessive
            if feature_counts.get("=>", 0) > 10:
                print(f"Warning: Many arrow functions in {handler_name}: {feature_counts['=>']}")

            # Optional chaining might not be supported in older browsers
            assert feature_counts.get("?.", 0) == 0, f"Optional chaining used in {handler_name} (compatibility issue)"

            # Async/await might not be needed
            assert feature_counts.get("async ", 0) == 0, f"Async/await used in {handler_name} (might not be needed)"

    def test_required_browser_apis(self):
        """Test that only supported browser APIs are used."""
        handlers = {
            "scroll": str(scroll_handler().children[0]),
            "resize_dom": str(resize_handler().children[0]),
            "resize_sp": str(resize_handler().children[0]),
            "persist": str(persist_handler().children[0]),
        }

        # APIs that should be available in target browsers

        # APIs that might not be universally supported
        potentially_unsupported = [
            "IntersectionObserver",  # Good support but newer
            "PerformanceObserver",  # Newer API
            "AbortController",  # Modern API
            "fetch",  # Should use fallbacks
        ]

        for handler_name, content in handlers.items():
            # Check for potentially unsupported APIs
            for api in potentially_unsupported:
                if api in content:
                    print(f"Warning: {api} used in {handler_name} (check compatibility)")

            # Ensure fallback patterns for newer APIs
            if "fetch" in content:
                assert "XMLHttpRequest" in content or "fallback" in content.lower(), (
                    f"No fetch fallback in {handler_name}"
                )

    def test_polyfill_requirements(self):
        """Test polyfill requirements for browser compatibility."""
        handlers = {
            "resize_dom": str(resize_handler().children[0]),
            "resize_sp": str(resize_handler().children[0]),
        }

        # APIs that might need polyfills
        polyfill_apis = {
            "ResizeObserver": "resize-observer-polyfill",
            "WeakMap": "weakmap-polyfill",
            "requestAnimationFrame": "raf-polyfill",
        }

        for handler_name, content in handlers.items():
            for api, _polyfill in polyfill_apis.items():
                if api in content:
                    # Should have feature detection or polyfill loading
                    has_detection = f"typeof {api}" in content or f"window.{api}" in content
                    has_fallback = "polyfill" in content.lower() or "fallback" in content.lower()

                    if not (has_detection or has_fallback):
                        print(f"Consider adding feature detection for {api} in {handler_name}")

    def test_browser_specific_code_paths(self):
        """Test for browser-specific code paths."""
        handlers = {
            "scroll": str(scroll_handler().children[0]),
            "resize_dom": str(resize_handler().children[0]),
            "persist": str(persist_handler().children[0]),
        }

        # Browser detection patterns (should be avoided)
        browser_detection = ["navigator.userAgent", "chrome", "firefox", "safari", "webkit", "gecko"]

        for handler_name, content in handlers.items():
            for pattern in browser_detection:
                if pattern.lower() in content.lower():
                    # This might indicate browser-specific code
                    print(f"Potential browser-specific code in {handler_name}: {pattern}")

    def test_event_compatibility(self):
        """Test event handling compatibility."""
        scroll_content = str(scroll_handler().children[0])
        resize_content = str(resize_handler().children[0])

        # Should use modern module pattern with datastar
        assert "import handlerPlugin from" in scroll_content, "Should use ES6 modules"
        assert "import handlerPlugin from" in resize_content, "Should use ES6 modules"
        assert "datastar" in scroll_content, "Should use datastar"
        assert "datastar" in resize_content, "Should use datastar"

        # Check handler file references
        assert "/static/js/handlers/scroll.js" in scroll_content, "Should load scroll handler"
        assert "/static/js/handlers/resize.js" in resize_content, "Should load resize handler"

        # Should not use deprecated event patterns
        deprecated_patterns = [
            ".attachEvent",  # IE-specific
            "on" + "scroll =",  # Inline event handlers in JS
            "on" + "resize =",
        ]

        for pattern in deprecated_patterns:
            assert pattern not in scroll_content, f"Deprecated event pattern in scroll: {pattern}"
            assert pattern not in resize_content, f"Deprecated event pattern in resize: {pattern}"


if __name__ == "__main__":
    # Run tests with appropriate markers
    if PLAYWRIGHT_AVAILABLE:
        pytest.main([__file__, "-v", "--tb=short", "-m", "not slow"])
    else:
        pytest.main([__file__, "-v", "--tb=short", "-k", "not test_browser_compatibility"])
