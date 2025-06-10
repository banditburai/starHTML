"""Theme toggle component using Datastar for reactivity."""
from starhtml import *
from starhtml.xtend import Script  # Use the Script that auto-wraps with NotStr
from .button import Button
from .iconify import IconifyIcon


def ThemeToggle(**attrs) -> Div:
    """Theme toggle using Datastar signals for reactive dark mode."""
    return Div(
        Button(
            # Sun icon (visible in light mode)
            IconifyIcon(
                "ph:sun-bold",
                ds_show="!$isDark",
                cls="h-[1.2rem] w-[1.2rem]"
            ),
            # Moon icon (visible in dark mode)
            IconifyIcon(
                "ph:moon-bold",
                ds_show="$isDark",
                cls="h-[1.2rem] w-[1.2rem]"
            ),
            size="icon",
            variant="outline",
            ds_on_click="$isDark = !$isDark; document.documentElement.classList.toggle('dark', $isDark); localStorage.setItem('theme', $isDark ? 'dark' : 'light')",
            aria_label="Toggle theme"
        ),
        ds_signals={"isDark": False},
        ds_init="""
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