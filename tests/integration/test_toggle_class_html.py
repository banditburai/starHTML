"""Integration tests to verify toggle_class generates valid Datastar HTML."""

from starhtml.datastar import ds_computed, ds_on_click, ds_signals, toggle_class, toggle_signal
from starhtml.tags import Button, Div, Section


def test_toggle_class_html_output():
    """Verify the actual HTML output is valid Datastar syntax."""
    button = Button(
        "Toggle", **toggle_class("$active", "bg-blue-500", "bg-gray-300"), **ds_on_click(toggle_signal("active"))
    )

    html = str(button)
    assert 'data-attr-class=\'$active ? "bg-blue-500" : "bg-gray-300"\'' in html
    assert 'data-on-click="$active = !$active"' in html


def test_multi_state_html_output():
    """Verify multi-state generates valid Datastar HTML."""
    status_div = Div(
        "Status",
        **toggle_class(
            "$status",
            loading="bg-yellow-500 animate-pulse",
            success="bg-green-500",
            error="bg-red-500",
            _="bg-gray-300",
            base="p-4 rounded",
        ),
    )

    html = str(status_div)
    # Check for the chained ternary structure
    assert "data-attr-class=" in html
    assert '$status === "loading"' in html
    assert '$status === "success"' in html
    assert '$status === "error"' in html
    assert "p-4 rounded" in html


def test_complex_interactive_component():
    """Test a complete interactive component with toggle_class."""
    component = Section(
        Button(
            "Step 1",
            **toggle_class(
                "$currentStep >= 1",
                "bg-blue-500 text-white",
                "bg-gray-300 text-gray-600",
                base="px-4 py-2 rounded mr-2",
            ),
            **ds_on_click("$currentStep = 1"),
        ),
        Button(
            "Step 2",
            **toggle_class(
                "$currentStep >= 2",
                "bg-blue-500 text-white",
                "bg-gray-300 text-gray-600",
                base="px-4 py-2 rounded mr-2",
            ),
            **ds_on_click("$currentStep = 2"),
        ),
        Div(
            "Content for step",
            **toggle_class(
                "$currentStep", one="block", two="block animate-fade-in", _="hidden", base="mt-4 p-4 border"
            ),
        ),
        **ds_signals(currentStep=1),
    )

    html = str(component)

    # Verify signals are set
    assert 'data-signals-currentstep="1"' in html

    # Verify click handlers
    assert 'data-on-click="$currentStep = 1"' in html
    assert 'data-on-click="$currentStep = 2"' in html

    # Verify conditional classes (>= is HTML-encoded as &gt;=)
    assert "$currentStep &gt;= 1" in html
    assert "$currentStep &gt;= 2" in html
    assert '$currentStep === "one"' in html
    assert '$currentStep === "two"' in html


def test_with_computed_signals():
    """Test toggle_class with computed signals."""
    container = Div(
        Div(
            "Price Display",
            **toggle_class(
                "$priceCategory",
                cheap="text-green-600 font-bold",
                moderate="text-yellow-600",
                expensive="text-red-600 font-bold",
                _="text-gray-600",
            ),
        ),
        **ds_signals(price=25),
        **ds_computed("priceCategory", "$price < 20 ? 'cheap' : $price < 50 ? 'moderate' : 'expensive'"),
    )

    html = str(container)

    # Check computed signal is defined (HTML attributes are lowercase)
    assert "data-computed-pricecategory=" in html
    assert "cheap" in html
    assert "moderate" in html
    assert "expensive" in html

    # Check toggle_class uses the computed signal
    assert '$priceCategory === "cheap"' in html
    assert '$priceCategory === "moderate"' in html
    assert '$priceCategory === "expensive"' in html


def test_no_unnecessary_attributes():
    """Ensure toggle_class doesn't add extra attributes."""
    simple = Div("Test", **toggle_class("$show", "block", "hidden"))

    html = str(simple)

    # Should only have the data-attr-class attribute
    assert html.count("data-") == 1
    assert "data-attr-class=" in html

    # Should not have any other Datastar attributes
    assert "data-class-" not in html
    assert "data-style-" not in html
