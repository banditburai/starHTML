"""Theme toggle component using Datastar for reactivity."""
from starhtml import *

from .button import Button


def ThemeToggle(**attrs) -> Div:
    """Theme toggle using Datastar signals for reactive dark mode."""
    return Div(
        Button(
            # Sun icon (visible in light mode)
            Icon(
                "ph:sun-bold",
                ds_show="!$isDark",
                cls="h-4 w-4"
            ),
            # Moon icon (visible in dark mode)
            Icon(
                "ph:moon-bold",
                ds_show="$isDark",
                cls="h-4 w-4"
            ),
            variant="ghost",
            ds_on_click="$isDark = !$isDark; document.documentElement.classList.toggle('dark', $isDark); localStorage.setItem('theme', $isDark ? 'dark' : 'light')",
            aria_label="Toggle theme",
            cls="h-9 px-4 py-2 flex-shrink-0"
        ),
        ds_signals={"isDark": False},
        ds_on_load="""
            // Initialize theme from localStorage or system preference
            const saved = localStorage.getItem('theme');
            const systemDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
            const shouldBeDark = saved === 'dark' || (!saved && systemDark);
            
            // Set both the DOM class and the Datastar signal
            $isDark = shouldBeDark;
            document.documentElement.classList.toggle('dark', shouldBeDark);
        """,
        **attrs
    )
