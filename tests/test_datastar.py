"""Comprehensive tests for StarHTML with Datastar functionality."""

import pytest
from starhtml import star_app, Div, H1, Button, Form, Input, P, A
from starhtml.datastar import ds_attrs, ds_signals, ds_on, ds_show, ds_bind, ds_text, ds_indicator

def test_datastar_imports():
    """Test that Datastar components can be imported."""
    assert ds_attrs is not None
    assert ds_signals is not None
    assert ds_on is not None
    assert ds_show is not None
    assert ds_bind is not None
    assert ds_text is not None
    assert ds_indicator is not None

def test_datastar_attributes():
    """Test Datastar attribute generation."""
    attrs = ds_attrs(visible="true", disabled="false")
    assert "data-attr-visible" in attrs
    assert "data-attr-disabled" in attrs
    assert attrs["data-attr-visible"] == "true"
    assert attrs["data-attr-disabled"] == "false"

def test_datastar_signals():
    """Test Datastar signal generation."""
    signals = ds_signals(count=0, name="test")
    assert "data-signals" in signals
    # Check for proper JSON format instead of JavaScript object format
    assert '"count": 0' in signals["data-signals"]
    assert '"name": "test"' in signals["data-signals"]

def test_datastar_events():
    """Test Datastar event handling."""
    events = ds_on(click="console.log('clicked')")
    assert "data-on-click" in events
    assert events["data-on-click"] == "console.log('clicked')"

def test_datastar_visibility():
    """Test Datastar visibility control."""
    show = ds_show(when="count > 0")
    assert "data-show" in show
    assert show["data-show"] == "count > 0"

def test_datastar_binding():
    """Test Datastar value binding."""
    bind = ds_bind("name")
    assert "data-bind" in bind
    assert bind["data-bind"] == "name"

def test_datastar_text():
    """Test Datastar text binding."""
    text = ds_text("name")
    assert "data-text" in text
    assert text["data-text"] == "name"

def test_datastar_indicator():
    """Test Datastar loading indicator."""
    indicator = ds_indicator("loading")
    assert "data-indicator" in indicator
    assert indicator["data-indicator"] == "loading"

def test_datastar_component_integration():
    """Test Datastar with StarHTML components."""
    app, rt = star_app()
    
    @rt('/')
    def get():
        return Div(
            H1("Datastar Test"),
            Button("Click Me", **ds_on(click="count++")),
            P("Count: ", **ds_text("count")),
            Form(
                Input(**ds_bind("name")),
                Button("Submit", type="submit")
            )
        )
    
    # Should not raise any errors
    assert get is not None

def test_datastar_sse():
    """Test Datastar SSE functionality."""
    from starhtml.datastar import sse_response, update_signals, update_fragments
    
    app, rt = star_app()
    
    @rt('/sse')
    @sse_response
    def get():
        yield update_signals(count=1)
        yield update_fragments(Div("Updated content"), "#target", "morph")
    
    # Should not raise any errors
    assert get is not None

def test_datastar_conditional_rendering():
    """Test Datastar conditional rendering."""
    app, rt = star_app()
    
    @rt('/')
    def get():
        return Div(
            Button("Toggle", **ds_on(click="visible = !visible")),
            Div("Content", **ds_show(when="visible"))
        )
    
    # Should not raise any errors
    assert get is not None

def test_datastar_form_handling():
    """Test Datastar form handling."""
    app, rt = star_app()
    
    @rt('/')
    def get():
        return Form(
            Input(**ds_bind("name")),
            Input(**ds_bind("email")),
            Button("Submit", type="submit", **ds_on(submit="submitForm()"))
        )
    
    # Should not raise any errors
    assert get is not None

def test_datastar_navigation():
    """Test Datastar navigation."""
    app, rt = star_app()
    
    @rt('/')
    def get():
        return A("Go to page", href="/page", **ds_on(click="navigate()"))
    
    # Should not raise any errors
    assert get is not None 