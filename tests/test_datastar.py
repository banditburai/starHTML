"""Tests for StarHTML with Datastar functionality - new direct attribute syntax only."""

from starhtml import H1, A, Button, Div, Form, Input, P, star_app
from starhtml.components import to_xml
from starhtml.datastar import fragments, signals, sse


def test_datastar_imports():
    """Test that Datastar SSE components can be imported."""
    assert sse is not None
    assert signals is not None
    assert fragments is not None


def test_datastar_direct_attributes():
    """Test Datastar direct attribute syntax."""
    div = Div(ds_attr_visible="true", ds_attr_disabled="false")
    xml = to_xml(div)
    assert 'data-attr-visible="true"' in xml
    assert 'data-attr-disabled="false"' in xml


def test_datastar_signals():
    """Test Datastar signal initialization."""
    div = Div(ds_signals={"count": 0, "name": "test"})
    xml = to_xml(div)
    assert "data-signals=" in xml
    # Check for proper JSON format
    assert '"count": 0' in xml
    assert '"name": "test"' in xml


def test_datastar_events():
    """Test Datastar event handling."""
    button = Button(ds_on_click="console.log('clicked')")
    xml = to_xml(button)
    assert "data-on-click=\"console.log('clicked')\"" in xml


def test_datastar_visibility():
    """Test Datastar visibility control."""
    div = Div(ds_show="count > 0")
    xml = to_xml(div)
    # Note: > will be escaped in XML
    assert 'data-show="count &gt; 0"' in xml


def test_datastar_binding():
    """Test Datastar value binding."""
    input_elem = Input(ds_bind="name")
    xml = to_xml(input_elem)
    assert 'data-bind="name"' in xml


def test_datastar_text():
    """Test Datastar text binding."""
    p = P(ds_text="name")
    xml = to_xml(p)
    assert 'data-text="name"' in xml


def test_datastar_indicator():
    """Test Datastar loading indicator."""
    button = Button(ds_indicator="loading")
    xml = to_xml(button)
    assert 'data-indicator="loading"' in xml


def test_datastar_component_integration():
    """Test Datastar with StarHTML components."""
    app, rt = star_app()

    @rt("/")
    def get():
        return Div(
            H1("Datastar Test"),
            Button("Click Me", ds_on_click="count++"),
            P("Count: ", ds_text="count"),
            Form(Input(ds_bind="name"), Button("Submit", type="submit")),
        )

    # Should not raise any errors
    assert get is not None


def test_datastar_sse():
    """Test Datastar SSE functionality."""
    app, rt = star_app()

    @rt("/sse")
    @sse
    def get():
        yield signals(count=1)
        yield fragments(Div("Updated content"), "#target", "morph")

    # Should not raise any errors
    assert get is not None


def test_datastar_auto_selector():
    """Test auto-selector detection functionality."""
    app, rt = star_app()

    @rt("/auto")
    @sse
    def get():
        # Auto-detection: should use #my-target selector
        yield fragments(Div("Auto content", id="my-target"))

    # Should not raise any errors
    assert get is not None


def test_datastar_conditional_rendering():
    """Test Datastar conditional rendering."""
    app, rt = star_app()

    @rt("/")
    def get():
        return Div(Button("Toggle", ds_on_click="visible = !visible"), Div("Content", ds_show="visible"))

    # Should not raise any errors
    assert get is not None


def test_datastar_form_handling():
    """Test Datastar form handling."""
    app, rt = star_app()

    @rt("/")
    def get():
        return Form(
            Input(ds_bind="name"), Input(ds_bind="email"), Button("Submit", type="submit", ds_on_submit="submitForm()")
        )

    # Should not raise any errors
    assert get is not None


def test_datastar_navigation():
    """Test Datastar navigation."""
    app, rt = star_app()

    @rt("/")
    def get():
        return A("Go to page", href="/page", ds_on_click="navigate()")

    # Should not raise any errors
    assert get is not None


def test_boolean_values():
    """Test that boolean values are converted to strings."""
    div = Div(ds_show=True, ds_on_load=True, ds_on_intersect_once=False)
    xml = to_xml(div)
    assert 'data-show="true"' in xml
    assert 'data-on-load="true"' in xml
    assert 'data-on-intersect.once="false"' in xml


def test_json_dumps_function():
    """Test json_dumps functionality"""
    from starhtml.datastar import json_dumps
    
    # Test basic serialization
    result = json_dumps({"key": "value"})
    assert isinstance(result, str)
    assert '"key"' in result
    assert '"value"' in result
    
    # Test with various types
    result = json_dumps({"num": 123, "bool": True, "null": None})
    assert "123" in result
    assert "true" in result
    assert "null" in result


def test_escape_newlines():
    """Test escape_newlines function"""
    from starhtml.datastar import escape_newlines
    
    # Test various newline formats
    result = escape_newlines("line1\nline2")
    assert result == "line1&#10;line2"
    
    result = escape_newlines("line1\r\nline2")
    assert result == "line1&#10;line2"
    
    result = escape_newlines("line1\rline2")
    assert result == "line1&#10;line2"
    
    # Test no newlines
    result = escape_newlines("no newlines here")
    assert result == "no newlines here"


def test_format_sse_event_with_id():
    """Test format_sse_event with event ID"""
    from starhtml.datastar import format_sse_event
    
    result = format_sse_event("test-event", ["data line 1", "data line 2"], event_id="test-123", retry=5000)
    assert "id: test-123" in result
    assert "event: test-event" in result
    assert "retry: 5000" in result
    assert "data: data line 1" in result
    assert "data: data line 2" in result
    assert result.endswith("\n\n")


def test_format_signal_event_error():
    """Test format_signal_event error handling"""
    import pytest

    from starhtml.datastar import format_signal_event
    
    # Test with non-serializable object
    class NonSerializable:
        pass
    
    with pytest.raises(ValueError, match="Failed to serialize signals"):
        format_signal_event({"obj": NonSerializable()})


def test_format_fragment_event_errors():
    """Test format_fragment_event error handling"""
    import pytest

    from starhtml.datastar import format_fragment_event
    
    # Test with invalid selector
    with pytest.raises(ValueError, match="Invalid selector"):
        format_fragment_event("content", "invalid selector with spaces")
        
    # Test with invalid merge mode
    with pytest.raises(ValueError, match="Invalid merge mode"):
        format_fragment_event("content", "#target", "invalid_mode")
        
    # Test with empty selector that gets stripped to None
    result = format_fragment_event("content", "   ", "morph")
    assert "selector" not in result


def test_process_sse_item_unknown_type():
    """Test process_sse_item with unknown type"""
    import pytest

    from starhtml.datastar import process_sse_item
    
    with pytest.raises(ValueError, match="Unknown SSE item type"):
        process_sse_item("unknown_type", {})
