"""devtools='capture' loads the data layer (capture.js) without registering
the visible UI panel — used by wasm-app-rig and similar diagnostic tools."""

import os
from unittest.mock import patch

import pytest

from starhtml import star_app
from starhtml.core import StarHTML
from starhtml.devtools import setup_devtools


class TestDevtoolsCaptureMode:
    def test_capture_mode_loads_capture_script(self):
        """capture mode must include the capture.js script tag."""
        app = StarHTML(devtools="capture")
        hdrs_html = "".join(str(h) for h in app.hdrs)
        assert "capture.js" in hdrs_html

    def test_capture_mode_skips_panel_element(self):
        """capture mode must NOT register the <starhtml-devtools> panel."""
        app = StarHTML(devtools="capture")
        ftrs_html = "".join(str(f) for f in app.ftrs)
        assert "starhtml-devtools" not in ftrs_html

    def test_capture_mode_script_is_module(self):
        app = StarHTML(devtools="capture")
        hdrs_html = "".join(str(h) for h in app.hdrs)
        assert 'type="module"' in hdrs_html or "type='module'" in hdrs_html

    def test_capture_mode_records_mode_attr(self):
        """app._devtools should preserve the 'capture' string for downstream checks."""
        app = StarHTML(devtools="capture")
        assert app._devtools == "capture"

    def test_star_app_passes_capture_mode(self):
        app, _ = star_app(devtools="capture")
        assert "capture.js" in "".join(str(h) for h in app.hdrs)
        assert "starhtml-devtools" not in "".join(str(f) for f in app.ftrs)

    def test_devtools_true_still_loads_full_panel(self):
        """devtools=True (existing behavior) must keep working."""
        app = StarHTML(devtools=True)
        ftrs_html = "".join(str(f) for f in app.ftrs)
        hdrs_html = "".join(str(h) for h in app.hdrs)
        assert "starhtml-devtools" in ftrs_html
        assert "capture.js" in hdrs_html

    def test_devtools_false_loads_nothing(self):
        app = StarHTML(devtools=False)
        ftrs_html = "".join(str(f) for f in app.ftrs)
        hdrs_html = "".join(str(h) for h in app.hdrs)
        assert "starhtml-devtools" not in ftrs_html
        assert "capture.js" not in hdrs_html

    def test_setup_devtools_false_noops(self):
        app = StarHTML(devtools=False)
        setup_devtools(app, mode=False)
        assert "capture.js" not in "".join(str(h) for h in app.hdrs)
        assert "starhtml-devtools" not in "".join(str(f) for f in app.ftrs)

    def test_unknown_string_mode_raises(self):
        """Typo guard: unknown string modes must fail loud at construction."""
        with pytest.raises(ValueError, match="Unknown devtools mode"):
            StarHTML(devtools="capturee")

    def test_env_override_capture(self):
        """STARHTML_DEVTOOLS=capture sets capture mode even when devtools=False."""
        with patch.dict(os.environ, {"STARHTML_DEVTOOLS": "capture"}):
            app = StarHTML(devtools=False)
            hdrs_html = "".join(str(h) for h in app.hdrs)
            ftrs_html = "".join(str(f) for f in app.ftrs)
            assert "capture.js" in hdrs_html
            assert "starhtml-devtools" not in ftrs_html
