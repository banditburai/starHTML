# StarHTML UI Components
"""
A collection of accessible, customizable UI components built with StarHTML and Datastar.
Inspired by shadcn/ui, these components maintain visual parity while using Python and Datastar for reactivity.
"""

from .button import Button, ButtonSize, ButtonVariant, button
from .iconify import Icon
from .theme_toggle import ThemeToggle

__all__ = [
    "Button",
    "button",
    "ButtonVariant",
    "ButtonSize",
    "Icon",
    "ThemeToggle"
]
