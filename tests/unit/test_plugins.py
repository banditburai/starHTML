"""Tests for the minimal plugin system."""

import pytest

from starhtml.plugins import (
    Plugin,
    canvas,
    clipboard,
    drag,
    persist,
    plugins_hdrs,
    position,
    resize,
    scroll,
    split,
)


class TestPluginClass:
    """Test Plugin class instantiation and behavior."""

    def test_plugin_basic_creation(self):
        """Test that Plugin factory is created correctly."""
        p = Plugin("test", signals=("x", "y"))

        assert p.name == "test"
        assert p.inline is None
        assert p.is_action is False

    def test_plugin_signal_access(self):
        """Test that signals can be accessed as attributes."""
        p = Plugin("test", signals=("x", "y", "is_active"))

        assert str(p.x) == "$test_x"
        assert str(p.y) == "$test_y"
        assert str(p.is_active) == "$test_is_active"

    def test_plugin_method_access(self):
        """Test that methods can be accessed as attributes."""
        p = Plugin("test", methods=("reset", "doSomething"))

        assert str(p.reset) == "window.__test.reset"
        assert str(p.doSomething) == "window.__test.doSomething"

    def test_plugin_mixed_signals_and_methods(self):
        """Test plugin with both signals and methods."""
        p = Plugin("test", signals=("x", "y"), methods=("reset",))

        assert str(p.x) == "$test_x"
        assert str(p.reset) == "window.__test.reset"

    def test_plugin_invalid_attribute_raises(self):
        """Test that accessing non-existent attributes raises AttributeError."""
        p = Plugin("test", signals=("x",))

        with pytest.raises(AttributeError, match="has no signal or method 'nonexistent'"):
            _ = p.nonexistent

    def test_plugin_inline_js(self):
        """Test plugin with inline JavaScript."""
        p = Plugin("test", inline="{ name: 'test' }", is_action=True)

        assert p.inline == "{ name: 'test' }"
        assert p.is_action is True


class TestPluginFactory:
    """Test Plugin factory pattern."""

    def test_plugin_is_callable(self):
        """Test that Plugin is callable."""
        p = Plugin("test", signals=("x",))
        assert callable(p)

    def test_call_creates_named_instance(self):
        """Test that calling plugin creates a named instance."""
        from starhtml.plugins import PluginInstance

        p = Plugin("test", signals=("x", "y"))
        instance = p(name="custom")

        assert isinstance(instance, PluginInstance)
        assert instance.name == "custom"
        assert str(instance.x) == "$custom_x"
        assert str(instance.y) == "$custom_y"

    def test_call_without_name_uses_base_name(self):
        """Test that calling without name uses base name."""
        p = Plugin("test", signals=("x",))
        instance = p()

        assert instance.name == "test"
        assert str(instance.x) == "$test_x"

    def test_call_with_config_kwargs(self):
        """Test that config kwargs are stored on instance."""
        p = Plugin("test", signals=("x",))
        instance = p(name="custom", responsive=True, min_size=100)

        assert instance.config == {"responsive": True, "min_size": 100}

    def test_factory_delegates_to_default_singleton(self):
        """Test that attribute access on factory delegates to default instance."""
        p = Plugin("test", signals=("x", "y"))

        # First access creates and caches default singleton
        x_ref = p.x
        assert str(x_ref) == "$test_x"

        # Verify same singleton is used
        assert p._default is not None
        assert str(p.y) == "$test_y"

    def test_instance_str_returns_name(self):
        """Test that PluginInstance __str__ returns name."""
        p = Plugin("test", signals=("x",))
        instance = p(name="main")

        assert str(instance) == "main"

    def test_named_instances_are_independent(self):
        """Test that multiple named instances have separate signal namespaces."""
        main = split(name="main")
        sidebar = split(name="sidebar")

        assert str(main.position) == "$main_position"
        assert str(sidebar.position) == "$sidebar_position"

    def test_builtin_plugin_is_callable(self):
        """Test that built-in plugins are callable factories."""
        main = split(name="main")
        assert main.name == "main"
        assert str(main.sizes) == "$main_sizes"


class TestBuiltinPlugins:
    """Test built-in plugin instances."""

    def test_persist_plugin(self):
        """Test persist plugin."""
        assert persist.name == "persist"
        assert persist.inline is None
        assert persist.is_action is False

    def test_scroll_plugin(self):
        """Test scroll plugin has expected signals."""
        assert scroll.name == "scroll"

        # Test signal access (delegates to default singleton)
        assert str(scroll.x) == "$scroll_x"
        assert str(scroll.y) == "$scroll_y"
        assert str(scroll.direction) == "$scroll_direction"
        assert str(scroll.is_bottom) == "$scroll_is_bottom"

    def test_resize_plugin(self):
        """Test resize plugin has expected signals."""
        assert resize.name == "resize"

        assert str(resize.width) == "$resize_width"
        assert str(resize.is_mobile) == "$resize_is_mobile"
        assert str(resize.current_breakpoint) == "$resize_current_breakpoint"

    def test_canvas_plugin(self):
        """Test canvas plugin has signals and methods."""
        assert canvas.name == "canvas"

        # Signals
        assert str(canvas.pan_x) == "$canvas_pan_x"
        assert str(canvas.zoom) == "$canvas_zoom"

        # Methods (Python snake_case -> JS camelCase)
        assert str(canvas.reset_view) == "window.__canvas.resetView"
        assert str(canvas.zoom_in) == "window.__canvas.zoomIn"
        assert str(canvas.zoom_out) == "window.__canvas.zoomOut"

    def test_drag_plugin(self):
        """Test drag plugin."""
        assert drag.name == "drag"
        assert str(drag.is_dragging) == "$drag_is_dragging"
        assert str(drag.x) == "$drag_x"

    def test_position_plugin(self):
        """Test position plugin."""
        assert position.name == "position"
        assert str(position.x) == "$position_x"
        assert str(position.visible) == "$position_visible"

    def test_split_plugin(self):
        """Test split plugin."""
        assert split.name == "split"
        assert str(split.position) == "$split_position"
        assert str(split.sizes) == "$split_sizes"
        assert str(split.is_dragging) == "$split_is_dragging"

    def test_clipboard_plugin(self):
        """Test clipboard plugin is inline action."""
        assert clipboard.name == "clipboard"
        assert clipboard.is_action is True
        assert clipboard.inline is not None
        assert "clipboard" in clipboard.inline


def _find_by_type(hdrs, type_attr):
    """Find header element by type attribute."""
    return next((h for h in hdrs if f'type="{type_attr}"' in str(h)), None)


class TestPluginsHdrs:
    """Test plugins_hdrs() import map generation."""

    def test_plugins_hdrs_generates_import_map_and_loader(self):
        """Test that plugins_hdrs returns import map and loader script."""
        hdrs = plugins_hdrs(persist, scroll)

        assert isinstance(hdrs, tuple)
        # persist has critical_css, so we get Style + 2 Scripts
        assert len(hdrs) == 3

        import_map = _find_by_type(hdrs, "importmap")
        assert import_map is not None

        import_map_content = str(import_map)
        assert "datastar" in import_map_content
        assert "@starhtml/plugins/persist" in import_map_content
        assert "@starhtml/plugins/scroll" in import_map_content

        loader = _find_by_type(hdrs, "module")
        assert loader is not None

        loader_content = str(loader)
        assert "@starhtml/plugins/persist" in loader_content
        assert "@starhtml/plugins/scroll" in loader_content
        assert "from'datastar'" in loader_content

    def test_plugins_hdrs_with_no_plugins_returns_empty(self):
        """Test that plugins_hdrs with no plugins returns empty tuple."""
        hdrs = plugins_hdrs()
        assert hdrs == ()

    def test_plugins_hdrs_with_debug_mode(self):
        """Test that plugins_hdrs respects debug mode."""
        hdrs = plugins_hdrs(persist, debug=True)

        import_map = _find_by_type(hdrs, "importmap")
        assert "?v=" in str(import_map)

    def test_custom_base_url(self):
        """Test that plugins_hdrs accepts custom base_url."""
        hdrs = plugins_hdrs(persist, base_url="/custom/path")

        import_map = _find_by_type(hdrs, "importmap")
        assert "/custom/path/persist.js" in str(import_map)

    def test_custom_datastar_path(self):
        """Test that plugins_hdrs accepts custom datastar_path."""
        hdrs = plugins_hdrs(persist, datastar_path="/custom/datastar.js")

        import_map = _find_by_type(hdrs, "importmap")
        assert "/custom/datastar.js" in str(import_map)


class TestPluginIntegration:
    """Test plugin integration patterns."""

    def test_multiple_plugins(self):
        """Test that multiple plugins generate correct output."""
        hdrs = plugins_hdrs(persist, scroll, resize, canvas)

        import_map = _find_by_type(hdrs, "importmap")
        import_map_content = str(import_map)
        assert "@starhtml/plugins/persist" in import_map_content
        assert "@starhtml/plugins/scroll" in import_map_content
        assert "@starhtml/plugins/resize" in import_map_content
        assert "@starhtml/plugins/canvas" in import_map_content

    def test_mixed_inline_and_file_plugins(self):
        """Test combining inline (clipboard) and file-based (persist) plugins."""
        hdrs = plugins_hdrs(clipboard, persist)

        # Import map should NOT include inline plugins
        import_map = _find_by_type(hdrs, "importmap")
        import_map_content = str(import_map)
        assert "@starhtml/plugins/clipboard" not in import_map_content
        assert "@starhtml/plugins/persist" in import_map_content

        # Loader should inline clipboard
        loader = _find_by_type(hdrs, "module")
        loader_content = str(loader)
        assert "const plugin_0" in loader_content
        assert "clipboard" in loader_content

    def test_action_and_attribute_plugins(self):
        """Test that action and attribute plugins import correct Datastar functions."""
        hdrs = plugins_hdrs(clipboard, persist)

        loader = _find_by_type(hdrs, "module")
        loader_content = str(loader)
        # Should have both attribute (for persist) and action (for clipboard)
        assert "attribute" in loader_content
        assert "action" in loader_content


class TestPluginProtocol:
    """Test that Plugin implements the Registrable protocol."""

    def test_get_package_name(self):
        """Test get_package_name returns expected value."""
        assert persist.get_package_name() == "starhtml/plugins"

    def test_get_static_path(self):
        """Test get_static_path returns a Path."""
        path = persist.get_static_path()
        assert path is not None
        assert "plugins" in str(path)

    def test_get_headers(self):
        """Test get_headers returns tuple of headers."""
        hdrs = persist.get_headers(base_url="/_pkg/starhtml/plugins")
        assert isinstance(hdrs, tuple)
        # persist has critical_css, so: Style + Script[importmap] + Script[module]
        assert len(hdrs) == 3


class TestCustomPlugins:
    """Test custom plugin creation with custom paths."""

    def test_custom_plugin_with_static_path(self):
        """Test creating a plugin with custom static_path."""
        from pathlib import Path

        custom_path = Path("./my_app/static/plugins")

        myplugin = Plugin("myplugin", signals=("x", "y"), static_path=custom_path)

        assert myplugin.get_static_path() == custom_path
        assert str(myplugin.x) == "$myplugin_x"

    def test_custom_plugin_with_package_name(self):
        """Test creating a plugin with custom package_name."""
        myplugin = Plugin("myplugin", signals=("x",), package_name="myapp/plugins")

        assert myplugin.get_package_name() == "myapp/plugins"

    def test_custom_plugin_instance_inherits_paths(self):
        """Test that named instances inherit custom paths."""
        from pathlib import Path

        custom_path = Path("./custom/plugins")

        myplugin = Plugin("myplugin", signals=("x",), static_path=custom_path, package_name="myapp/plugins")
        instance = myplugin(name="main")

        assert instance.get_static_path() == custom_path
        assert instance.get_package_name() == "myapp/plugins"
        assert str(instance.x) == "$main_x"

    def test_plugin_instance_inherits_critical_css(self):
        """Test that named instances inherit critical_css from parent Plugin."""
        myplugin = Plugin("myplugin", signals=("x",), critical_css=".test{display:none}")
        instance = myplugin(name="main")

        assert instance._critical_css == ".test{display:none}"

        # Verify it works in plugins_hdrs
        hdrs = plugins_hdrs(instance)
        css_found = any("display:none" in str(h) for h in hdrs)
        assert css_found, "Critical CSS should be included in headers"

    def test_builtin_plugins_use_defaults(self):
        """Test that built-in plugins still use framework defaults."""
        assert "starhtml/plugins" in persist.get_package_name()
        assert "plugins" in str(persist.get_static_path())

    def test_plugin_config_passed_to_js(self):
        """Test that plugin config kwargs are passed to JS via setConfig."""
        splitter = split(name="main", responsive=True, responsive_breakpoint=768)
        hdrs = plugins_hdrs(splitter)

        loader = _find_by_type(hdrs, "module")
        loader_content = str(loader)
        # Should call setConfig with the config
        assert "setConfig" in loader_content
        # Config should include signal name and converted camelCase keys (compact JSON)
        assert '"signal":"main"' in loader_content or '"signal": "main"' in loader_content
        assert '"responsive":true' in loader_content or '"responsive": true' in loader_content
        assert '"responsiveBreakpoint":768' in loader_content or '"responsiveBreakpoint": 768' in loader_content

    def test_plugin_without_config_no_setconfig(self):
        """Test that plugins without config don't call setConfig."""
        hdrs = plugins_hdrs(persist)

        loader = _find_by_type(hdrs, "module")
        loader_content = str(loader)
        # Should NOT call setConfig for plugins without config
        assert "setConfig" not in loader_content
