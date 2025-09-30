"""Tests for drag_handler behavior and functionality."""

from starhtml.handlers import drag_handler


class TestDragHandler:
    """Test drag_handler behavior and configuration."""

    def test_drag_handler_creates_javascript_output(self):
        """Test that drag_handler creates JavaScript output for the browser."""
        result = drag_handler()

        # Test that result is a HandlerBundle with scripts and signals
        assert hasattr(result, "scripts"), "Result should have scripts attribute"
        assert hasattr(result, "signals"), "Result should have signals attribute"

        # Test that scripts contain the expected drag handler content
        script_content = str(result)
        assert "/static/js/handlers/drag.js" in script_content
        assert "import handlerPlugin" in script_content
        assert "load(handlerPlugin)" in script_content
        assert "apply()" in script_content

    def test_drag_handler_configuration_passed_through(self):
        """Test that drag_handler configuration is properly embedded."""
        result = drag_handler(
            signal="custom_drag", mode="sortable", throttle_ms=32, constrain_to_parent=True, touch_enabled=False
        )

        # Configuration should be embedded in the output
        output_str = str(result)
        assert "custom_drag" in output_str
        assert "sortable" in output_str
        assert "32" in output_str
        assert "constrainToParent" in output_str or "constrain_to_parent" in output_str
        assert "touchEnabled" in output_str and "false" in output_str

    def test_drag_handler_signal_naming(self):
        """Test that custom signal names are properly handled."""
        custom_signal = "my_drag_system"
        result = drag_handler(signal=custom_signal)

        output_str = str(result)
        assert custom_signal in output_str

    def test_drag_handler_mode_configuration(self):
        """Test that different drag modes are properly configured."""
        # Test freeform mode
        result_freeform = drag_handler(mode="freeform")
        output_str = str(result_freeform)
        assert "freeform" in output_str

        # Test sortable mode
        result_sortable = drag_handler(mode="sortable")
        output_str = str(result_sortable)
        assert "sortable" in output_str

    def test_drag_handler_throttle_configuration(self):
        """Test that throttle values are properly configured."""
        # Test custom throttle value
        result = drag_handler(throttle_ms=8)  # 125fps
        output_str = str(result)
        assert "8" in output_str

    def test_drag_handler_constraint_configuration(self):
        """Test that constraint options are properly configured."""
        result = drag_handler(constrain_to_parent=True)
        output_str = str(result)
        assert "constrainToParent" in output_str or "constrain_to_parent" in output_str
        assert "true" in output_str

    def test_drag_handler_touch_configuration(self):
        """Test that touch enable/disable configuration works."""
        result = drag_handler(touch_enabled=False)
        output_str = str(result)
        assert "touchEnabled" in output_str and "false" in output_str

    def test_drag_handler_comprehensive_configuration(self):
        """Test drag_handler with comprehensive parameter set."""
        result = drag_handler(
            signal="test_drag", mode="sortable", throttle_ms=20, constrain_to_parent=True, touch_enabled=True
        )

        output_str = str(result)
        # All configuration should be present
        assert "test_drag" in output_str
        assert "sortable" in output_str
        assert "20" in output_str
        assert "constrainToParent" in output_str or "constrain_to_parent" in output_str

    def test_drag_handler_loads_correct_javascript_module(self):
        """Test that drag_handler references the correct JavaScript module."""
        result = drag_handler()
        output_str = str(result)

        # Should load the drag handler module
        assert "drag.js" in output_str
        assert "handlerPlugin" in output_str

    def test_drag_handler_datastar_integration(self):
        """Test that drag_handler integrates with Datastar framework."""
        result = drag_handler()
        output_str = str(result)

        # Should integrate with Datastar
        assert "datastar" in output_str.lower()
        assert "load" in output_str and "apply" in output_str

    def test_drag_handler_documentation_and_api(self):
        """Test that drag_handler has proper documentation and API."""
        # Should have documentation
        assert drag_handler.__doc__ is not None
        assert len(drag_handler.__doc__) > 10

        # Should mention key concepts
        doc = drag_handler.__doc__
        if doc is None:
            raise AssertionError("drag_handler should have documentation")
        doc_lower = doc.lower()
        assert "drag" in doc_lower
        assert "reactive" in doc_lower or "state" in doc_lower

        # Should be callable with various parameter combinations
        try:
            drag_handler()  # Default
            drag_handler(signal="test")  # Custom signal
            drag_handler(mode="freeform")  # Freeform mode
            drag_handler(mode="sortable")  # Sortable mode
            drag_handler(throttle_ms=16)  # Custom throttle
            drag_handler(constrain_to_parent=True)  # With constraints
        except Exception as e:
            raise AssertionError(f"drag_handler should accept various parameter combinations: {e}") from e

    def test_drag_handler_signal_creation_behavior(self):
        """Test that drag_handler creates the expected signals."""
        bundle = drag_handler()

        # Should create standard drag signals
        expected_signals = ["is_dragging", "element_id", "x", "y", "drop_zone"]
        for signal_name in expected_signals:
            assert signal_name in bundle.signals, f"Missing signal: {signal_name}"

        # Signals should be accessible via attribute access
        assert hasattr(bundle, "is_dragging")
        assert hasattr(bundle, "element_id")
        assert hasattr(bundle, "x")
        assert hasattr(bundle, "y")
        assert hasattr(bundle, "drop_zone")

    def test_drag_handler_zone_mode_behavior(self):
        """Test that drag_handler in zone modes creates zone_items helper."""
        # Sortable mode should include zone_items
        sortable_bundle = drag_handler(mode="sortable")
        assert "zone_items" in sortable_bundle.signals
        assert callable(sortable_bundle.signals["zone_items"])

        # Freeform mode should include zone_items
        freeform_bundle = drag_handler(mode="freeform")
        assert "zone_items" in freeform_bundle.signals
        assert callable(freeform_bundle.signals["zone_items"])

        # Non-zone mode should not include zone_items
        basic_bundle = drag_handler(mode="basic")
        assert "zone_items" not in basic_bundle.signals
