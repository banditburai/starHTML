"""Tests for Button component."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
from starhtml import *
from components.ui import Button, button


def test_button_renders_basic():
    """Test basic button rendering."""
    btn = button("Click me")
    html = str(btn)

    assert "<button" in html
    assert "Click me" in html
    assert 'type="button"' in html
    assert "inline-flex items-center" in html
    assert "gap-2" in html


def test_button_variants():
    """Test all button variants."""
    variants = ["default", "destructive", "outline", "secondary", "ghost", "link"]

    for variant in variants:
        btn = button("Test", variant=variant)
        html = str(btn)

        assert "<button" in html

        # Check variant-specific classes
        if variant == "default":
            assert "bg-primary" in html
            assert "text-primary-foreground" in html
        elif variant == "destructive":
            assert "bg-destructive" in html
            assert "text-destructive-foreground" in html
        elif variant == "outline":
            assert "border" in html and "bg-background" in html
        elif variant == "secondary":
            assert "bg-secondary" in html
            assert "text-secondary-foreground" in html
        elif variant == "ghost":
            assert "hover:bg-accent" in html
        elif variant == "link":
            assert "underline-offset-4" in html


def test_button_sizes():
    """Test all button sizes."""
    sizes = ["default", "sm", "lg", "icon"]

    for size in sizes:
        btn = button("Test", size=size)
        html = str(btn)

        assert "<button" in html

        # Check size-specific classes
        if size == "default":
            assert "h-9 px-4" in html
        elif size == "sm":
            assert "h-8" in html and "px-3" in html
        elif size == "lg":
            assert "h-10" in html and "px-8" in html
        elif size == "icon":
            assert "h-9 w-9" in html


def test_button_disabled():
    """Test disabled state."""
    btn = button("Disabled", disabled=True)
    html = str(btn)

    assert "disabled" in html
    assert "disabled:pointer-events-none" in html
    assert "disabled:opacity-50" in html


def test_button_custom_class():
    """Test custom class names."""
    btn = button("Custom", class_name="custom-class")
    html = str(btn)

    assert "custom-class" in html
    # Should still have base classes
    assert "inline-flex" in html


def test_button_type_attribute():
    """Test button type attribute."""
    btn_submit = button("Submit", type="submit")
    btn_reset = button("Reset", type="reset")

    assert 'type="submit"' in str(btn_submit)
    assert 'type="reset"' in str(btn_reset)


def test_button_with_datastar():
    """Test button with Datastar attributes."""
    btn = button("Click", data_on_click="$count++", data_signals={"count": 0})
    html = str(btn)

    assert 'data-on-click="$count++"' in html
    assert "data-signals=" in html


def test_button_with_children():
    """Test button with multiple children."""
    btn = button(Span("Icon", class_="icon"), "Text", variant="outline")
    html = str(btn)

    assert "<span" in html
    assert "icon" in html
    assert "Text" in html


def test_button_pascal_case_alias():
    """Test that Button (PascalCase) works the same as button."""
    btn1 = button("Test", variant="secondary")
    btn2 = Button("Test", variant="secondary")

    assert str(btn1) == str(btn2)
