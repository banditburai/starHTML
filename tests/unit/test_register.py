"""Tests for app.register() unified registration method."""

import pytest

from starhtml import StarHTML
from starhtml.plugins import PluginDef, canvas, persist, scroll


class TestAppRegister:
    """Test app.register() method."""

    def test_register_single_plugin(self):
        """Test registering a single plugin."""
        app = StarHTML()
        p = persist()

        result = app.register(p)

        # Should return the plugin
        assert result is p
        assert isinstance(result, PluginDef)

        # Should add headers to app
        assert len(app.hdrs) > 0

    def test_register_multiple_plugins(self):
        """Test registering multiple plugins."""
        app = StarHTML()
        p = persist()
        s = scroll()

        result = app.register(p, s)

        # Should return tuple of plugins
        assert isinstance(result, tuple)
        assert len(result) == 2
        assert result[0] is p
        assert result[1] is s

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
        app.register(persist())

        # Should have more headers now
        assert len(app.hdrs) > initial_hdr_count

    def test_register_with_custom_prefix(self):
        """Test that register accepts custom prefix."""
        app = StarHTML()
        p = persist()

        # Should not raise an error
        app.register(p, prefix="/custom")

        # Headers should be added
        assert len(app.hdrs) > 0

    def test_register_plugin_creates_route(self):
        """Test that registering plugin creates static file route."""
        app = StarHTML()
        p = persist()

        initial_route_count = len(app.routes)

        app.register(p)

        # Should have added a route for serving static files
        assert len(app.routes) > initial_route_count


class TestRegisterBatchBehavior:
    """Test batching behavior when registering plugins."""

    def test_multiple_register_calls_accumulate_headers(self):
        """Test that multiple register() calls accumulate headers."""
        app = StarHTML()

        # Register plugins separately
        app.register(persist())
        first_count = len(app.hdrs)

        app.register(scroll())
        second_count = len(app.hdrs)

        # Should have more headers after second registration
        assert second_count > first_count

    def test_batch_registration_creates_single_script(self):
        """Test that batch registration creates efficient single script."""
        app = StarHTML()

        # Register multiple plugins at once
        app.register(persist(), scroll(), canvas())

        # Check that headers were added
        assert len(app.hdrs) > 0

        # The plugins_hdrs() function should batch into single script
        # (we can't easily test the exact script count here without examining internals)


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

        # Register multiple plugins
        persist_plugin = persist()
        scroll_plugin = scroll()
        canvas_plugin = canvas(enable_pan=True)

        result = app.register(persist_plugin, scroll_plugin, canvas_plugin)

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
        p = persist()

        # Single registration returns the plugin
        result = app.register(p)
        assert result is p

        # Could potentially use for further configuration
        assert isinstance(result, PluginDef)
