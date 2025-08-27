"""Tests for the enhanced scroll handler with anchored positioning."""

import pytest
from starhtml import *


def test_scroll_handler_basic():
    """Test basic scroll handler without anchored positioning."""
    result = ds_on_scroll("$scrollY = window.scrollY", throttle="50")
    assert result.attrs["data-on-scroll__throttle.50ms"] == "$scrollY = window.scrollY"


def test_scroll_handler_anchored_minimal():
    """Test anchored positioning with minimal configuration."""
    result = ds_on_scroll("", anchor_to="popoverTrigger")
    assert "data-on-scroll__anchor_to.popoverTrigger" in result.attrs
    assert result.attrs["data-on-scroll__anchor_to.popoverTrigger"] == True


def test_scroll_handler_anchored_with_throttle():
    """Test anchored positioning with custom throttle."""
    result = ds_on_scroll("", anchor_to="selectTrigger", throttle="16")
    assert "data-on-scroll__anchor_to.selectTrigger.throttle.16ms" in result.attrs


def test_scroll_handler_anchored_with_hide_action():
    """Test anchored positioning with custom hide action."""
    result = ds_on_scroll(
        "",
        anchor_to="tooltipTrigger",
        hide_action="tooltipContent.hidePopover()",
        hide_when_offscreen=True
    )
    assert "anchor_to.tooltipTrigger" in str(result.attrs)
    assert "hide_action.tooltipContent.hidePopover()" in str(result.attrs)
    assert "hide_when_offscreen" in str(result.attrs)


def test_scroll_handler_anchored_with_signal_prefix():
    """Test anchored positioning with explicit signal prefix."""
    result = ds_on_scroll(
        "",
        anchor_to="complexElement",
        signal_prefix="modal",
        hide_when_offscreen=False
    )
    assert "anchor_to.complexElement" in str(result.attrs)
    assert "signal_prefix.modal" in str(result.attrs)


def test_scroll_handler_combined_expression_and_anchored():
    """Test combining custom expression with anchored positioning."""
    result = ds_on_scroll(
        "$customCounter++",
        anchor_to="trigger",
        throttle="50"
    )
    assert "$customCounter++" in str(result.attrs.values())


def test_scroll_handler_multiple_modifiers():
    """Test multiple modifiers with anchored positioning."""
    result = ds_on_scroll(
        "",
        "smooth",
        anchor_to="smoothTrigger",
        throttle="16",
        hide_when_offscreen=True,
        hide_action="$smooth_open = false"
    )
    assert "smooth" in str(result.attrs)
    assert "anchor_to.smoothTrigger" in str(result.attrs)
    assert "throttle.16ms" in str(result.attrs)


def test_scroll_handler_backwards_compatibility():
    """Test that traditional scroll handlers still work."""
    # Traditional usage should still work
    result = ds_on_scroll("$scrollPos = window.scrollY")
    assert "data-on-scroll" in result.attrs
    assert result.attrs["data-on-scroll"] == "$scrollPos = window.scrollY"
    
    # With throttle
    result = ds_on_scroll("$pos++", throttle="100")
    assert "data-on-scroll__throttle.100ms" in result.attrs
    assert result.attrs["data-on-scroll__throttle.100ms"] == "$pos++"


def test_scroll_handler_empty_expression_without_anchor_returns_valid():
    """Test that empty expression with anchor_to still creates valid attribute."""
    result = ds_on_scroll("", anchor_to="emptyTrigger")
    assert len(result.attrs) > 0
    assert "anchor_to.emptyTrigger" in str(result.attrs)


def test_scroll_handler_integration_with_elements():
    """Test integration with actual HTML elements."""
    div = Div(
        Button("Click me", id="testButton"),
        Div(
            "Popover content",
            ds_show("$test_open"),
            ds_style(
                position="'fixed'",
                top="$test_top + 'px'",
                left="$test_left + 'px'"
            ),
            id="testPopover",
        ),
        ds_on_scroll("", anchor_to="testButton", signal_prefix="test"),
        ds_signals(test_open=False, test_top=0, test_left=0),
    )
    
    # Verify the element has scroll handler attached
    html = str(div)
    assert "data-on-scroll" in html
    assert "anchor_to.testbutton" in html.lower()
    assert "signal_prefix.test" in html


def test_scroll_handler_all_parameters():
    """Test scroll handler with all possible parameters."""
    result = ds_on_scroll(
        "$myExpression()",
        "smooth",
        "passive",
        anchor_to="fullTrigger",
        signal_prefix="full",
        hide_when_offscreen=True,
        hide_action="fullContent.close()",
        throttle="32"
    )
    
    # Check that all parameters are included
    attrs_str = str(result.attrs)
    assert "smooth" in attrs_str
    assert "passive" in attrs_str
    assert "anchor_to.fullTrigger" in attrs_str
    assert "signal_prefix.full" in attrs_str
    assert "hide_when_offscreen" in attrs_str
    assert "hide_action.fullContent.close()" in attrs_str
    assert "throttle.32ms" in attrs_str
    assert "$myExpression()" in str(result.attrs.values())


if __name__ == "__main__":
    pytest.main([__file__, "-v"])