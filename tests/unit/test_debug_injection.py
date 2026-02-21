"""Tests for debugger auto-injection when debug=True."""

import os
import sys
from unittest.mock import patch

from starhtml.core import StarHTML


class TestDebugInjection:
    def test_debug_injects_script(self):
        app = StarHTML(debug=True)
        hdrs_html = "".join(str(h) for h in app.hdrs)
        assert "capture.js" in hdrs_html

    def test_debug_injects_panel_element(self):
        app = StarHTML(debug=True)
        ftrs_html = "".join(str(h) for h in app.ftrs)
        assert "starhtml-debugger" in ftrs_html

    def test_no_debug_no_script(self):
        app = StarHTML(debug=False)
        hdrs_html = "".join(str(h) for h in app.hdrs)
        assert "debugger-capture.js" not in hdrs_html

    def test_no_debug_no_panel(self):
        app = StarHTML(debug=False)
        ftrs_html = "".join(str(h) for h in app.ftrs)
        assert "starhtml-debugger" not in ftrs_html

    def test_debug_script_is_module(self):
        app = StarHTML(debug=True)
        hdrs_html = "".join(str(h) for h in app.hdrs)
        assert 'type="module"' in hdrs_html or "type='module'" in hdrs_html

    def test_debug_preserves_custom_hdrs(self):
        """Debugger elements are appended, not replacing user hdrs."""
        from starhtml.xtend import Script

        custom = Script("console.log('custom')")
        app = StarHTML(debug=True, hdrs=[custom])
        hdrs_html = "".join(str(h) for h in app.hdrs)
        assert "custom" in hdrs_html
        assert "capture.js" in hdrs_html

    def test_debug_preserves_custom_ftrs(self):
        """Debugger footer appended after user ftrs."""
        from fastcore.xml import NotStr

        custom = NotStr('<div id="my-footer">hi</div>')
        app = StarHTML(debug=True, ftrs=[custom])
        ftrs_html = "".join(str(h) for h in app.ftrs)
        assert "my-footer" in ftrs_html
        assert "starhtml-debugger" in ftrs_html

    def test_env_override_triggers_injection(self):
        """STARHTML_DEBUG=1 injects debugger even when debug=False."""
        with patch.dict(os.environ, {"STARHTML_DEBUG": "1"}):
            app = StarHTML(debug=False)
            hdrs_html = "".join(str(h) for h in app.hdrs)
            assert "capture.js" in hdrs_html

    def test_graceful_fallback_without_starelements(self):
        """When starelements is missing, debugger prints warning and skips."""
        import importlib

        import starhtml.debugger as dbg_mod

        # Evict cached starelements so the import is re-attempted on reload
        cached = {k: sys.modules.pop(k) for k in list(sys.modules) if k.startswith("starelements")}
        try:
            real_import = importlib.__import__

            def mock_import(name, *args, **kwargs):
                if name == "starelements" or name.startswith("starelements."):
                    raise ModuleNotFoundError(f"No module named '{name}'")
                return real_import(name, *args, **kwargs)

            with patch("builtins.__import__", side_effect=mock_import):
                # Reload debugger module to clear any cached import
                importlib.reload(dbg_mod)
                app = StarHTML(debug=True)
                hdrs_html = "".join(str(h) for h in app.hdrs)
                ftrs_html = "".join(str(h) for h in app.ftrs)
                assert "capture.js" not in hdrs_html
                assert "starhtml-debugger" not in ftrs_html
        finally:
            sys.modules.update(cached)
            importlib.reload(dbg_mod)
