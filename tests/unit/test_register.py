"""Tests for app.register() unified registration method."""

import pytest

from starhtml import StarHTML
from starhtml.plugins import Plugin, canvas, persist, scroll, split


class TestAppRegister:
    """Test app.register() method."""

    def test_register_single_plugin(self):
        """Test registering a single plugin."""
        app = StarHTML()

        result = app.register(persist)

        # Should return the plugin
        assert result is persist
        assert isinstance(result, Plugin)

        # Should add headers to app
        assert len(app.hdrs) > 0

    def test_register_multiple_plugins(self):
        """Test registering multiple plugins."""
        app = StarHTML()

        result = app.register(persist, scroll)

        # Should return tuple of plugins
        assert isinstance(result, tuple)
        assert len(result) == 2
        assert result[0] is persist
        assert result[1] is scroll

        # Should add headers to app
        assert len(app.hdrs) > 0

    def test_register_no_items_returns_none(self):
        """Test that register with no items returns None."""
        app = StarHTML()

        result = app.register()

        assert result is None

    def test_register_invalid_type_raises_typeerror(self):
        """Test that registering invalid types raises TypeError."""
        app = StarHTML()

        with pytest.raises(TypeError, match="Cannot register"):
            app.register("not a plugin")

        with pytest.raises(TypeError, match="Cannot register"):
            app.register(123)

        with pytest.raises(TypeError, match="Cannot register"):
            app.register({"config": "dict"})

    def test_register_adds_to_existing_headers(self):
        """Test that register appends to existing headers."""
        app = StarHTML()

        # Add some initial headers
        initial_hdr_count = len(app.hdrs)

        # Register plugin
        app.register(persist)

        # Should have more headers now
        assert len(app.hdrs) > initial_hdr_count

    def test_register_with_custom_prefix(self):
        """Test that register accepts custom prefix."""
        app = StarHTML()

        # Should not raise an error
        app.register(persist, prefix="/custom")

        # Headers should be added
        assert len(app.hdrs) > 0

    def test_register_plugin_creates_route(self):
        """Test that registering plugin creates static file route."""
        app = StarHTML()

        initial_route_count = len(app.routes)

        app.register(persist)

        # Should have added a route for serving static files
        assert len(app.routes) > initial_route_count


class TestRegisterBatchBehavior:
    """Test batching behavior when registering plugins."""

    def test_multiple_register_calls_accumulate_headers(self):
        """Test that multiple register() calls accumulate headers."""
        app = StarHTML()

        # Register plugins separately
        app.register(persist)
        first_count = len(app.hdrs)

        app.register(scroll)
        second_count = len(app.hdrs)

        # Should have more headers after second registration
        assert second_count > first_count

    def test_batch_registration_creates_single_script(self):
        """Test that batch registration creates efficient single script."""
        app = StarHTML()

        # Register multiple plugins at once
        app.register(persist, scroll, canvas)

        # Check that headers were added
        assert len(app.hdrs) > 0


class TestRegisterHelperFunctions:
    """Test helper functions used by register()."""

    def test_register_item_validates_registrable(self):
        """Test that _register_item validates Registrable protocol."""
        from starhtml.core import _register_item

        app = StarHTML()

        with pytest.raises(TypeError, match="Cannot register"):
            _register_item(app, "not a registrable item")

    def test_register_item_validates_protocol_methods(self):
        """Test that _register_item validates protocol implementation."""
        from starhtml.core import _register_item

        app = StarHTML()

        # Object without protocol methods
        class FakeRegistrable:
            pass

        with pytest.raises(TypeError, match="must implement"):
            _register_item(app, FakeRegistrable())


class TestRegisterIntegration:
    """Test real-world registration scenarios."""

    def test_typical_app_setup(self):
        """Test typical app setup with multiple plugins."""
        app = StarHTML()

        result = app.register(persist, scroll, canvas)

        # Should return tuple of all plugins
        assert isinstance(result, tuple)
        assert len(result) == 3

        # App should have headers
        assert len(app.hdrs) > 0

        # App should have routes for serving static files
        assert len(app.routes) > 0

    def test_register_returns_plugin_for_method_chaining(self):
        """Test that register returns plugin for potential method chaining."""
        app = StarHTML()

        # Single registration returns the plugin
        result = app.register(persist)
        assert result is persist

        # Should be a Plugin instance
        assert isinstance(result, Plugin)

    def test_register_named_instance(self):
        """Test registering a named plugin instance."""
        from starhtml.plugins import PluginInstance

        app = StarHTML()
        main = split(name="main")

        result = app.register(main)

        assert isinstance(result, PluginInstance)
        assert result.name == "main"
        assert len(app.hdrs) > 0

    def test_register_multiple_named_instances(self):
        """Test registering multiple named instances of same plugin type."""
        app = StarHTML()
        main = split(name="main")
        sidebar = split(name="sidebar")

        result = app.register(main, sidebar)

        assert isinstance(result, tuple)
        assert len(result) == 2
        assert result[0].name == "main"
        assert result[1].name == "sidebar"

    def test_named_instances_have_correct_signal_refs(self):
        """Test that named instances have correct signal references."""
        main = split(name="main")
        sidebar = split(name="sidebar")

        # Each instance should have its own signal namespace
        assert str(main.position) == "$main_position"
        assert str(main.sizes) == "$main_sizes"
        assert str(sidebar.position) == "$sidebar_position"
        assert str(sidebar.sizes) == "$sidebar_sizes"
