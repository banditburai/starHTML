"""Tests for the new plugin system with PluginDef and plugins_hdrs()."""

import pytest

from starhtml.plugins import (
    PluginDef,
    canvas,
    get_registered_plugins,
    persist,
    plugin,
    plugins_hdrs,
    resize,
    scroll,
)


class TestPluginDefCreation:
    """Test PluginDef instantiation and behavior."""

    def test_plugin_decorator_creates_plugindef(self):
        """Test that @plugin decorator returns PluginDef instances."""
        result = persist()

        assert isinstance(result, PluginDef)
        assert result.name == "persist"
        assert isinstance(result.config, dict)
        assert isinstance(result.signals, dict)

    def test_plugin_captures_config_automatically(self):
        """Test that @plugin decorator captures function parameters as config."""
        result = scroll(debug=True)

        assert result.config["debug"] is True

    def test_plugin_converts_snake_case_to_camel_case(self):
        """Test that parameter names are converted to camelCase for JavaScript."""
        result = resize(throttle_ms=100, track_element=True)

        # Should convert throttle_ms -> throttleMs, track_element -> trackElement
        assert "throttleMs" in result.config
        assert result.config["throttleMs"] == 100
        assert "trackElement" in result.config
        assert result.config["trackElement"] is True

    def test_plugin_includes_signal_definitions(self):
        """Test that plugins include their signal definitions."""
        result = scroll()

        # scroll plugin should have signal definitions
        assert "x" in result.signals
        assert "y" in result.signals
        assert "direction" in result.signals

    def test_plugin_signal_access_via_attribute(self):
        """Test that signals can be accessed as attributes."""
        result = scroll()

        # Should be able to access signals as attributes
        x_signal = result.x
        y_signal = result.y

        # These should be JS expressions
        assert str(x_signal) == "$scroll_x"
        assert str(y_signal) == "$scroll_y"

    def test_plugin_signal_access_invalid_raises_attributeerror(self):
        """Test that accessing non-existent signals raises AttributeError."""
        result = persist()

        with pytest.raises(AttributeError, match="has no signal 'nonexistent'"):
            _ = result.nonexistent


class TestBuiltinPlugins:
    """Test built-in plugin functions."""

    def test_persist_plugin(self):
        """Test persist plugin creation."""
        p = persist(debug=True)

        assert p.name == "persist"
        assert p.config["debug"] is True
        assert p.signals == {}  # persist has no signals

    def test_scroll_plugin(self):
        """Test scroll plugin creation."""
        s = scroll(debug=False)

        assert s.name == "scroll"
        assert s.config["debug"] is False
        assert len(s.signals) == 13  # scroll has many signals

    def test_resize_plugin(self):
        """Test resize plugin with custom config."""
        r = resize(signal="myResize", throttle_ms=50, track_element=True)

        assert r.name == "resize"
        assert r.config["signal"] == "myResize"
        assert r.config["throttleMs"] == 50
        assert r.config["trackElement"] is True

    def test_canvas_plugin(self):
        """Test canvas plugin with custom config."""
        c = canvas(signal="canvas", enable_pan=True, min_zoom=0.5, max_zoom=5.0)

        assert c.name == "canvas"
        assert c.config["signal"] == "canvas"
        assert c.config["enablePan"] is True
        assert c.config["minZoom"] == 0.5
        assert c.config["maxZoom"] == 5.0

        # Check action signals
        assert "reset_view" in c.signals
        assert "zoom_in" in c.signals
        assert "zoom_out" in c.signals


class TestPluginRegistry:
    """Test plugin registry functionality."""

    def test_get_registered_plugins_includes_builtins(self):
        """Test that get_registered_plugins returns all registered plugin functions."""
        plugins = get_registered_plugins()

        # Should return list of callable functions
        assert len(plugins) >= 7
        assert all(callable(p) for p in plugins)

        # Should include built-in plugins (check function names)
        plugin_names = [p.__name__ for p in plugins]
        assert "persist" in plugin_names
        assert "scroll" in plugin_names
        assert "resize" in plugin_names
        assert "canvas" in plugin_names
        assert "drag" in plugin_names
        assert "position" in plugin_names
        assert "split" in plugin_names

    def test_custom_plugin_registration(self):
        """Test that custom plugins can be registered."""

        @plugin("testplugin")
        def testplugin(custom_param: str = "test"):
            return {"test_signal": f"${custom_param}_test"}

        result = testplugin(custom_param="foo")

        assert result.name == "testplugin"
        assert result.config["customParam"] == "foo"
        assert "test_signal" in result.signals


class TestPluginsHdrs:
    """Test plugins_hdrs() batch generation."""

    def test_plugins_hdrs_generates_single_script(self):
        """Test that plugins_hdrs batches multiple plugins into single script."""
        p = persist()
        s = scroll()

        hdrs = plugins_hdrs(p, s)

        # Should return tuple of scripts
        assert isinstance(hdrs, tuple)
        assert len(hdrs) == 1  # Single batched script

        # Check script content
        script = hdrs[0]
        script_content = str(script)

        # Should contain Datastar import
        assert "import('" in script_content
        assert "datastar.js" in script_content

        # Should load both plugins
        assert "persist.js" in script_content
        assert "scroll.js" in script_content

    def test_plugins_hdrs_with_no_plugins_returns_empty(self):
        """Test that plugins_hdrs with no plugins returns empty tuple."""
        hdrs = plugins_hdrs()

        assert hdrs == tuple()

    def test_plugins_hdrs_deduplicates_plugins(self):
        """Test that plugins_hdrs removes duplicate plugins."""
        p1 = persist()
        p2 = persist()

        hdrs = plugins_hdrs(p1, p2)

        # Should only load persist once
        script_content = str(hdrs[0])
        # Count occurrences of "persist.js"
        count = script_content.count("persist.js")
        assert count == 1

    def test_plugins_hdrs_with_debug_mode(self):
        """Test that plugins_hdrs respects debug mode."""
        p = persist(debug=True)

        hdrs = plugins_hdrs(p, debug=True)

        script_content = str(hdrs[0])

        # Should include debug logging and cache busting
        assert "console.log" in script_content
        assert "?v=" in script_content

    def test_plugins_hdrs_validates_input_types(self):
        """Test that plugins_hdrs validates input types."""
        with pytest.raises(TypeError, match="Expected PluginDef"):
            plugins_hdrs("not a plugin")

    def test_plugins_hdrs_requires_plugin_name(self):
        """Test that plugins_hdrs requires plugins to have names."""
        from pathlib import Path

        # Create invalid PluginDef without name
        invalid_plugin = PluginDef(name="", config={}, signals={}, static_path=Path())

        with pytest.raises(ValueError, match="missing required 'name' field"):
            plugins_hdrs(invalid_plugin)


class TestPluginIntegration:
    """Test plugin integration patterns."""

    def test_multiple_plugins_batch_correctly(self):
        """Test that multiple different plugins batch into single script."""
        p = persist()
        s = scroll()
        r = resize(throttle_ms=50)
        c = canvas(enable_pan=True)

        hdrs = plugins_hdrs(p, s, r, c)

        # Single script
        assert len(hdrs) == 1

        script_content = str(hdrs[0])

        # All plugins loaded
        assert "persist.js" in script_content
        assert "scroll.js" in script_content
        assert "resize.js" in script_content
        assert "canvas.js" in script_content

        # Configs applied (JSON may not have spaces)
        assert '"throttleMs":50' in script_content
        assert '"enablePan":true' in script_content

    def test_custom_base_url(self):
        """Test that plugins_hdrs accepts custom base_url."""
        p = persist()

        hdrs = plugins_hdrs(p, base_url="/custom/path")

        script_content = str(hdrs[0])
        assert "/custom/path/persist.js" in script_content

    def test_custom_datastar_path(self):
        """Test that plugins_hdrs accepts custom datastar_path."""
        p = persist()

        hdrs = plugins_hdrs(p, datastar_path="/custom/datastar.js")

        script_content = str(hdrs[0])
        assert "/custom/datastar.js" in script_content
