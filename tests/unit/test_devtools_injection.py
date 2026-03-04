"""Tests for devtools auto-injection when devtools=True."""

import os
import sys
from unittest.mock import patch

from starhtml.core import StarHTML


class TestDevtoolsInjection:
    def test_devtools_injects_script(self):
        app = StarHTML(devtools=True)
        hdrs_html = "".join(str(h) for h in app.hdrs)
        assert "capture.js" in hdrs_html

    def test_devtools_injects_panel_element(self):
        app = StarHTML(devtools=True)
        ftrs_html = "".join(str(h) for h in app.ftrs)
        assert "starhtml-devtools" in ftrs_html

    def test_no_devtools_no_script(self):
        app = StarHTML(devtools=False)
        hdrs_html = "".join(str(h) for h in app.hdrs)
        assert "devtools-capture.js" not in hdrs_html

    def test_no_devtools_no_panel(self):
        app = StarHTML(devtools=False)
        ftrs_html = "".join(str(h) for h in app.ftrs)
        assert "starhtml-devtools" not in ftrs_html

    def test_devtools_script_is_module(self):
        app = StarHTML(devtools=True)
        hdrs_html = "".join(str(h) for h in app.hdrs)
        assert 'type="module"' in hdrs_html or "type='module'" in hdrs_html

    def test_devtools_preserves_custom_hdrs(self):
        """Devtools elements are appended, not replacing user hdrs."""
        from starhtml.xtend import Script

        custom = Script("console.log('custom')")
        app = StarHTML(devtools=True, hdrs=[custom])
        hdrs_html = "".join(str(h) for h in app.hdrs)
        assert "custom" in hdrs_html
        assert "capture.js" in hdrs_html

    def test_devtools_preserves_custom_ftrs(self):
        """Devtools footer appended after user ftrs."""
        from fastcore.xml import NotStr

        custom = NotStr('<div id="my-footer">hi</div>')
        app = StarHTML(devtools=True, ftrs=[custom])
        ftrs_html = "".join(str(h) for h in app.ftrs)
        assert "my-footer" in ftrs_html
        assert "starhtml-devtools" in ftrs_html

    def test_env_override_triggers_injection(self):
        """STARHTML_DEVTOOLS=1 injects devtools even when devtools=False."""
        with patch.dict(os.environ, {"STARHTML_DEVTOOLS": "1"}):
            app = StarHTML(devtools=False)
            hdrs_html = "".join(str(h) for h in app.hdrs)
            assert "capture.js" in hdrs_html

    def test_devtools_true_debug_false(self):
        """devtools=True enables panel without Starlette debug tracebacks."""
        app = StarHTML(devtools=True, debug=False)
        assert app.debug is False
        assert app._devtools is True
        ftrs_html = "".join(str(h) for h in app.ftrs)
        assert "starhtml-devtools" in ftrs_html

    def test_debug_true_alone_no_panel(self):
        """debug=True alone does NOT inject devtools panel (clean break)."""
        app = StarHTML(debug=True, devtools=False)
        assert app.debug is True
        assert app._devtools is False
        ftrs_html = "".join(str(h) for h in app.ftrs)
        assert "starhtml-devtools" not in ftrs_html

    def test_graceful_fallback_without_starelements(self):
        """When starelements is missing, devtools prints warning and skips."""
        import importlib

        import starhtml.devtools as dt_mod

        # Evict cached starelements so the import is re-attempted on reload
        cached = {k: sys.modules.pop(k) for k in list(sys.modules) if k.startswith("starelements")}
        try:
            real_import = importlib.__import__

            def mock_import(name, *args, **kwargs):
                if name == "starelements" or name.startswith("starelements."):
                    raise ModuleNotFoundError(f"No module named '{name}'")
                return real_import(name, *args, **kwargs)

            with patch("builtins.__import__", side_effect=mock_import):
                # Reload devtools module to clear any cached import
                importlib.reload(dt_mod)
                app = StarHTML(devtools=True)
                hdrs_html = "".join(str(h) for h in app.hdrs)
                ftrs_html = "".join(str(h) for h in app.ftrs)
                assert "capture.js" not in hdrs_html
                assert "starhtml-devtools" not in ftrs_html
        finally:
            sys.modules.update(cached)
            importlib.reload(dt_mod)
