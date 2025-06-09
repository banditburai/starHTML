"""Breadcrumb navigation component for shadcn-ui documentation."""
from typing import List, Dict, Any, Optional
from starhtml import *
from ..ui.iconify import IconifyIcon
from ..utils import cn


def BreadcrumbItem(
    label: str,
    href: Optional[str] = None,
    active: bool = False,
    **attrs
) -> FT:
    """Individual breadcrumb item."""
    if active or href is None:
        return Span(
            label,
            cls="font-medium text-foreground",
            **attrs
        )
    
    return A(
        label,
        href=href,
        cls="text-muted-foreground transition-colors hover:text-foreground",
        **attrs
    )


def BreadcrumbSeparator(**attrs) -> FT:
    """Breadcrumb separator icon."""
    return IconifyIcon(
        "ph:caret-right-bold",
        cls="h-4 w-4 text-muted-foreground",
        **attrs
    )


def DocsBreadcrumb(
    items: List[Dict[str, Any]],
    separator: Optional[FT] = None,
    class_name: str = "",
    **attrs
) -> FT:
    """
    Breadcrumb navigation component.
    
    Args:
        items: List of breadcrumb items with 'label', optional 'href', 'active'
        separator: Custom separator element (defaults to caret-right icon)
        class_name: Additional CSS classes
        **attrs: Additional HTML attributes
        
    Returns:
        Breadcrumb navigation element
        
    Examples:
        # Basic breadcrumb
        Breadcrumb([
            {"label": "Docs", "href": "/docs"},
            {"label": "Components", "href": "/docs/components"},
            {"label": "Button", "active": True}
        ])
        
        # With custom separator
        Breadcrumb(
            items=[...],
            separator=Span("/", cls="text-muted-foreground")
        )
    """
    if not items:
        return Div()
    
    if separator is None:
        separator = BreadcrumbSeparator()
    
    # Build breadcrumb elements with separators
    breadcrumb_elements = []
    
    for i, item in enumerate(items):
        # Add separator before item (except first)
        if i > 0:
            breadcrumb_elements.append(
                Li(separator, cls="flex items-center")
            )
        
        # Add breadcrumb item
        breadcrumb_elements.append(
            Li(
                BreadcrumbItem(
                    label=item["label"],
                    href=item.get("href"),
                    active=item.get("active", False)
                ),
                cls="flex items-center"
            )
        )
    
    return Nav(
        Ol(
            *breadcrumb_elements,
            cls="flex flex-wrap items-center gap-1.5 break-words text-sm text-muted-foreground sm:gap-2.5"
        ),
        aria_label="Breadcrumb",
        cls=cn("mb-4", class_name),
        **attrs
    )


def docs_breadcrumb(
    items: List[Dict[str, Any]],
    separator: Optional[FT] = None,
    class_name: str = "",
    **attrs
) -> FT:
    """Alias for DocsBreadcrumb() using lowercase convention."""
    return DocsBreadcrumb(
        items=items,
        separator=separator,
        class_name=class_name,
        **attrs
    )