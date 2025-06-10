"""Iconify icon component for StarHTML."""
from starhtml import ft_datastar

def IconifyIcon(icon: str, **attrs):
    """Iconify icon wrapper. Usage: IconifyIcon("mdi:home", cls="text-2xl")"""
    return ft_datastar('iconify-icon', icon=icon, **attrs)

def Icon(icon: str, **attrs):
    """Simple alias for IconifyIcon. Usage: Icon("lucide:home", cls="h-4 w-4")"""
    return IconifyIcon(icon, **attrs)