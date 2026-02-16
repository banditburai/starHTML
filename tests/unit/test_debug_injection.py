"""Tests for debugger auto-injection when debug=True."""

from starhtml.core import StarHTML


class TestDebugInjection:
    def test_debug_injects_script(self):
        """When debug=True, the debugger script is in headers."""
        app = StarHTML(debug=True)
        hdrs_html = "".join(str(h) for h in app.hdrs)
        assert "debugger.js" in hdrs_html

    def test_debug_injects_panel_element(self):
        """When debug=True, the debugger custom element is in footers."""
        app = StarHTML(debug=True)
        ftrs_html = "".join(str(h) for h in app.ftrs)
        assert "starhtml-debugger" in ftrs_html

    def test_no_debug_no_script(self):
        """When debug=False, no debugger script."""
        app = StarHTML(debug=False)
        hdrs_html = "".join(str(h) for h in app.hdrs)
        assert "debugger.js" not in hdrs_html

    def test_no_debug_no_panel(self):
        """When debug=False, no debugger panel."""
        app = StarHTML(debug=False)
        ftrs_html = "".join(str(h) for h in app.ftrs)
        assert "starhtml-debugger" not in ftrs_html

    def test_debug_script_is_module(self):
        """Debugger script should be loaded as ES module."""
        app = StarHTML(debug=True)
        hdrs_html = "".join(str(h) for h in app.hdrs)
        assert 'type="module"' in hdrs_html or "type='module'" in hdrs_html
