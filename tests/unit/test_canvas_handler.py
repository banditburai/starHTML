"""Tests for canvas_handler behavior and functionality."""

from fastcore.xml import FT

from starhtml.handlers import canvas_handler


class TestCanvasHandler:
    """Test canvas_handler behavior and configuration."""

    def test_canvas_handler_creates_javascript_output(self):
        """Test that canvas_handler creates JavaScript output for the browser."""
        result = canvas_handler()
        # Should create some form of JavaScript output (Script or list containing Script)
        if isinstance(result, list):
            assert any(isinstance(item, FT) for item in result)
        else:
            assert isinstance(result, FT)

    def test_canvas_handler_configuration_passed_through(self):
        """Test that canvas_handler configuration is properly embedded."""
        result = canvas_handler(signal="custom_canvas", enable_pan=False, min_zoom=0.5, max_zoom=5.0)

        # Configuration should be embedded as JSON in the output
        output_str = str(result)
        assert "custom_canvas" in output_str
        assert "enablePan" in output_str or "enable_pan" in output_str
        assert "0.5" in output_str
        assert "5.0" in output_str

    def test_canvas_handler_signal_naming(self):
        """Test that custom signal names are properly handled."""
        custom_signal = "my_viewport"
        result = canvas_handler(signal=custom_signal)

        output_str = str(result)
        assert custom_signal in output_str

    def test_canvas_handler_pan_zoom_configuration(self):
        """Test that pan/zoom settings are properly configured."""
        # Test pan disabled
        result_no_pan = canvas_handler(enable_pan=False)
        output_str = str(result_no_pan)
        assert "enablePan" in output_str and "false" in output_str

        # Test zoom disabled
        result_no_zoom = canvas_handler(enable_zoom=False)
        output_str = str(result_no_zoom)
        assert "enableZoom" in output_str and "false" in output_str

    def test_canvas_handler_zoom_limits(self):
        """Test that zoom limit configuration works correctly."""
        result = canvas_handler(min_zoom=0.1, max_zoom=10.0)
        output_str = str(result)

        # Should contain the zoom limits in the configuration
        assert "0.1" in output_str
        assert "10.0" in output_str or "10" in output_str

    def test_canvas_handler_touch_configuration(self):
        """Test touch enable/disable configuration."""
        # Test touch disabled
        result = canvas_handler(touch_enabled=False)
        output_str = str(result)
        assert "touchEnabled" in output_str and "false" in output_str

    def test_canvas_handler_grid_feature(self):
        """Test that grid feature adds visual styling when enabled."""
        # With grid enabled (default)
        result_with_grid = canvas_handler(enable_grid=True)
        output_str = str(result_with_grid)

        # Should contain grid-related styling
        assert "linear-gradient" in output_str or "grid" in output_str.lower()

        # With grid disabled
        result_no_grid = canvas_handler(enable_grid=False)
        output_str_no_grid = str(result_no_grid)

        # Grid styling should be different/absent
        grid_content_with = output_str.count("linear-gradient")
        grid_content_without = output_str_no_grid.count("linear-gradient")
        assert grid_content_with != grid_content_without

    def test_canvas_handler_comprehensive_configuration(self):
        """Test canvas_handler with comprehensive parameter set."""
        result = canvas_handler(
            signal="test_canvas",
            enable_pan=True,
            enable_zoom=True,
            min_zoom=0.1,
            max_zoom=15.0,
            touch_enabled=True,
            grid_color="#ff0000",
            grid_size=50,
        )

        output_str = str(result)
        # All configuration should be present
        assert "test_canvas" in output_str
        assert "0.1" in output_str
        assert "15" in output_str
        assert "#ff0000" in output_str or "ff0000" in output_str
        assert "50" in output_str

    def test_canvas_handler_loads_correct_javascript_module(self):
        """Test that canvas_handler references the correct JavaScript module."""
        result = canvas_handler()
        output_str = str(result)

        # Should load the canvas handler module
        assert "canvas.js" in output_str
        assert "handlerPlugin" in output_str

    def test_canvas_handler_datastar_integration(self):
        """Test that canvas_handler integrates with Datastar framework."""
        result = canvas_handler()
        output_str = str(result)

        # Should integrate with Datastar
        assert "datastar" in output_str.lower()
        assert "load" in output_str and "apply" in output_str

    def test_canvas_handler_documentation_and_api(self):
        """Test that canvas_handler has proper documentation and API."""
        # Should have documentation
        assert canvas_handler.__doc__ is not None
        assert len(canvas_handler.__doc__) > 10

        # Should mention key concepts
        doc_lower = canvas_handler.__doc__.lower()
        assert "canvas" in doc_lower
        assert "pan" in doc_lower or "zoom" in doc_lower

        # Should be callable with various parameter combinations
        try:
            canvas_handler()  # Default
            canvas_handler(signal="test")  # Custom signal
            canvas_handler(enable_grid=False)  # Grid disabled
            canvas_handler(min_zoom=0.5, max_zoom=2.0)  # Custom zoom
        except Exception as e:
            raise AssertionError(f"canvas_handler should accept various parameter combinations: {e}") from e
