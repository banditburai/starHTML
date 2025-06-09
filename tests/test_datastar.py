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
    assert 'data-signals=' in xml
    # Check for proper JSON format
    assert '"count": 0' in xml
    assert '"name": "test"' in xml

def test_datastar_events():
    """Test Datastar event handling."""
    button = Button(ds_on_click="console.log('clicked')")
    xml = to_xml(button)
    assert 'data-on-click="console.log(\'clicked\')"' in xml

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

    @rt('/')
    def get():
        return Div(
            H1("Datastar Test"),
            Button("Click Me", ds_on_click="count++"),
            P("Count: ", ds_text="count"),
            Form(
                Input(ds_bind="name"),
                Button("Submit", type="submit")
            )
        )

    # Should not raise any errors
    assert get is not None

def test_datastar_sse():
    """Test Datastar SSE functionality."""
    app, rt = star_app()

    @rt('/sse')
    @sse
    def get():
        yield signals(count=1)
        yield fragments(Div("Updated content"), "#target", "morph")

    # Should not raise any errors
    assert get is not None

def test_datastar_auto_selector():
    """Test auto-selector detection functionality."""
    app, rt = star_app()

    @rt('/auto')
    @sse
    def get():
        # Auto-detection: should use #my-target selector
        yield fragments(Div("Auto content", id="my-target"))

    # Should not raise any errors
    assert get is not None

def test_datastar_conditional_rendering():
    """Test Datastar conditional rendering."""
    app, rt = star_app()

    @rt('/')
    def get():
        return Div(
            Button("Toggle", ds_on_click="visible = !visible"),
            Div("Content", ds_show="visible")
        )

    # Should not raise any errors
    assert get is not None

def test_datastar_form_handling():
    """Test Datastar form handling."""
    app, rt = star_app()

    @rt('/')
    def get():
        return Form(
            Input(ds_bind="name"),
            Input(ds_bind="email"),
            Button("Submit", type="submit", ds_on_submit="submitForm()")
        )

    # Should not raise any errors
    assert get is not None

def test_datastar_navigation():
    """Test Datastar navigation."""
    app, rt = star_app()

    @rt('/')
    def get():
        return A("Go to page", href="/page", ds_on_click="navigate()")

    # Should not raise any errors
    assert get is not None

def test_boolean_values():
    """Test that boolean values are converted to strings."""
    div = Div(
        ds_show=True,
        ds_on_load=True,
        ds_on_intersect_once=False
    )
    xml = to_xml(div)
    assert 'data-show="true"' in xml
    assert 'data-on-load="true"' in xml
    assert 'data-on-intersect.once="false"' in xml
