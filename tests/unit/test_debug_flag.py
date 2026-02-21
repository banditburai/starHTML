"""Tests for the debug flag infrastructure."""

import os
from unittest.mock import patch

from starhtml.core import StarHTML


class TestDebugFlag:
    def test_debug_default_false(self):
        app = StarHTML()
        assert app.debug is False

    def test_debug_explicit_true(self):
        app = StarHTML(debug=True)
        assert app.debug is True

    def test_debug_env_override_off(self):
        """STARHTML_DEBUG=0 forces debug off even if code says True."""
        with patch.dict(os.environ, {"STARHTML_DEBUG": "0"}):
            app = StarHTML(debug=True)
            assert app.debug is False

    def test_debug_env_override_on(self):
        with patch.dict(os.environ, {"STARHTML_DEBUG": "1"}):
            app = StarHTML(debug=False)
            assert app.debug is True

    def test_debug_env_true_string(self):
        with patch.dict(os.environ, {"STARHTML_DEBUG": "true"}):
            app = StarHTML(debug=False)
            assert app.debug is True

    def test_debug_env_yes_string(self):
        with patch.dict(os.environ, {"STARHTML_DEBUG": "yes"}):
            app = StarHTML(debug=False)
            assert app.debug is True

    def test_debug_stderr_warning(self, caplog):
        import logging

        with caplog.at_level(logging.WARNING, logger="starhtml.core"):
            StarHTML(debug=True)
        assert any("debug mode is ON" in msg for msg in caplog.messages)

    def test_no_debug_no_warning(self, caplog):
        import logging

        with caplog.at_level(logging.WARNING, logger="starhtml.core"):
            StarHTML(debug=False)
        assert not any("debug mode" in msg for msg in caplog.messages)

    def test_debug_env_case_insensitive(self):
        """STARHTML_DEBUG=TRUE (uppercase) should work."""
        for val in ("TRUE", "True", "YES", "Yes"):
            with patch.dict(os.environ, {"STARHTML_DEBUG": val}):
                app = StarHTML(debug=False)
                assert app.debug is True, f"Failed for STARHTML_DEBUG={val}"

    def test_debug_no_env_var_passthrough(self):
        """Without env var, debug param passes through as-is."""
        with patch.dict(os.environ, {}, clear=False):
            os.environ.pop("STARHTML_DEBUG", None)
            app = StarHTML(debug=True)
            assert app.debug is True
            app2 = StarHTML(debug=False)
            assert app2.debug is False
