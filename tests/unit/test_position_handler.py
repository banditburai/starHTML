"""Tests for the Floating UI position handler."""

import pytest

from starhtml import *


def test_position_handler_basic():
    """Test basic position handler with default settings."""
    result = ds_position(anchor="triggerButton")
    assert "data-position-anchor" in result.attrs
    assert result.attrs["data-position-anchor"] == "triggerButton"


def test_position_handler_with_placement():
    """Test position handler with custom placement."""
    result = ds_position(anchor="menuButton", placement="top-start")
    assert "placement.top-start" in str(result.attrs)


def test_position_handler_with_offset():
    """Test position handler with custom offset."""
    result = ds_position(anchor="tooltipTrigger", offset=12)
    assert "offset.12" in str(result.attrs)


def test_position_handler_with_strategy():
    """Test position handler with fixed strategy."""
    result = ds_position(anchor="popover", strategy="fixed")
    assert "strategy.fixed" in str(result.attrs)


def test_position_handler_flip_disabled():
    """Test position handler with flip disabled."""
    result = ds_position(anchor="dropdown", flip=False)
    assert "flip.false" in str(result.attrs)


def test_position_handler_shift_disabled():
    """Test position handler with shift disabled."""
    result = ds_position(anchor="menu", shift=False)
    assert "shift.false" in str(result.attrs)


def test_position_handler_with_hide():
    """Test position handler with hide enabled."""
    result = ds_position(anchor="tooltip", hide=True)
    assert "hide" in str(result.attrs)


def test_position_handler_with_auto_size():
    """Test position handler with auto-size enabled."""
    result = ds_position(anchor="select", auto_size=True)
    assert "auto_size" in str(result.attrs)


def test_position_handler_with_signal_prefix():
    """Test position handler with explicit signal prefix."""
    result = ds_position(anchor="trigger", signal_prefix="modal")
    assert "signal_prefix.modal" in str(result.attrs)


def test_position_handler_all_options():
    """Test position handler with all options."""
    result = ds_position(
        anchor="complexElement",
        placement="bottom-end",
        strategy="fixed",
        offset=16,
        flip=False,
        shift=False,
        hide=True,
        auto_size=True,
        signal_prefix="custom",
    )

    attrs_str = str(result.attrs)
    assert "complexElement" in attrs_str
    assert "placement.bottom-end" in attrs_str
    assert "strategy.fixed" in attrs_str
    assert "offset.16" in attrs_str
    assert "flip.false" in attrs_str
    assert "shift.false" in attrs_str
    assert "hide" in attrs_str
    assert "auto_size" in attrs_str
    assert "signal_prefix.custom" in attrs_str


def test_position_handler_defaults():
    """Test that defaults are not included in attributes."""
    result = ds_position(
        anchor="test",
        placement="bottom",  # default
        strategy="absolute",  # default
        offset=8,  # default
        flip=True,  # default
        shift=True,  # default
    )

    # Only anchor should be present, no modifiers for defaults
    assert result.attrs == {"data-position-anchor": "test"}


def test_position_handler_integration():
    """Test integration with HTML elements."""
    div = Div(
        Button("Click me", id="testButton"),
        Div(
            "Popover content",
            ds_position(anchor="testButton", placement="top"),
            ds_show("$test_open"),
            id="testPopover",
        ),
        ds_signals(test_open=False),
    )

    html = str(div)
    assert "data-position-anchor" in html
    assert "testButton" in html
    assert "placement.top" in html


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
