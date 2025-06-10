"""Sidebar navigation component for shadcn-ui documentation."""
from typing import Optional, List, Dict, Any, Union
from starhtml import *
from ..ui.iconify import IconifyIcon
from ..utils import cn


def SidebarItem(
    href: str,
    label: str,
    active: bool = False,
    disabled: bool = False,
    **attrs
) -> FT:
    """Individual sidebar navigation item."""
    if disabled:
        return Span(
            label,
            cls="flex w-full items-center rounded-md p-2 text-sm text-muted-foreground cursor-not-allowed opacity-60",
            **attrs
        )
    
    return A(
        label,
        href=href,
        cls=cn(
            "flex w-full items-center rounded-md p-2 text-sm transition-colors",
            "hover:bg-accent hover:text-accent-foreground",
            "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring",
            "text-muted-foreground" if not active else "bg-accent text-accent-foreground font-medium"
        ),
        **attrs
    )


def SidebarSection(
    title: str,
    items: List[Dict[str, Any]],
    collapsible: bool = True,
    default_open: bool = True,
    **attrs
) -> FT:
    """
    Sidebar section with optional collapsible behavior.
    
    Args:
        title: Section title
        items: List of items with 'href', 'label', optional 'active', 'disabled'
        collapsible: Whether section can be collapsed
        default_open: Whether section is open by default
        **attrs: Additional HTML attributes
    """
    section_id = title.lower().replace(" ", "-")
    
    if not collapsible:
        return Div(
            H4(title, cls="mb-1 rounded-md px-2 py-1 text-sm font-semibold"),
            Div(
                *[
                    SidebarItem(
                        href=item["href"],
                        label=item["label"],
                        active=item.get("active", False),
                        disabled=item.get("disabled", False)
                    )
                    for item in items
                ],
                cls="grid grid-flow-row auto-rows-max text-sm"
            ),
            cls="pb-4",
            **attrs
        )
    
    return Div(
        # Section header (clickable if collapsible)
        Button(
            Div(
                H4(title, cls="text-sm font-semibold"),
                IconifyIcon(
                    "ph:caret-down-bold",
                    cls="h-4 w-4 transition-transform",
                    ds_class_transform_rotate_180=f"${section_id}Open"
                ),
                cls="flex items-center justify-between"
            ),
            variant="ghost",
            cls="w-full justify-start p-2 font-normal hover:bg-transparent",
            ds_on_click=f"${section_id}Open = !${section_id}Open"
        ),
        
        # Section content
        Div(
            *[
                SidebarItem(
                    href=item["href"],
                    label=item["label"],
                    active=item.get("active", False),
                    disabled=item.get("disabled", False)
                )
                for item in items
            ],
            cls="grid grid-flow-row auto-rows-max text-sm",
            ds_show=f"${section_id}Open"
        ),
        
        cls="pb-4",
        ds_signals={f"{section_id}Open": default_open},
        **attrs
    )


def DocsSidebar(
    sections: Optional[List[Dict[str, Any]]] = None,
    class_name: str = "",
    mobile_overlay: bool = True,
    **attrs
) -> FT:
    """
    Main sidebar navigation component.
    
    Args:
        sections: List of navigation sections with 'title', 'items', optional 'collapsible', 'default_open'
        class_name: Additional CSS classes
        mobile_overlay: Whether to show as overlay on mobile
        **attrs: Additional HTML attributes
        
    Returns:
        Sidebar navigation element
    """
    if sections is None:
        sections = [
            {
                "title": "Getting Started",
                "collapsible": True,
                "default_open": True,
                "items": [
                    {"href": "/docs", "label": "Introduction"},
                    {"href": "/docs/installation", "label": "Installation"},
                    {"href": "/docs/components-json", "label": "components.json"},
                    {"href": "/docs/theming", "label": "Theming"},
                    {"href": "/docs/dark-mode", "label": "Dark mode"},
                    {"href": "/docs/cli", "label": "CLI"},
                    {"href": "/docs/typography", "label": "Typography"},
                    {"href": "/docs/figma", "label": "Figma"},
                    {"href": "/docs/changelog", "label": "Changelog"}
                ]
            },
            {
                "title": "Components",
                "collapsible": True,
                "default_open": True,
                "items": [
                    {"href": "/docs/components/accordion", "label": "Accordion"},
                    {"href": "/docs/components/alert", "label": "Alert"},
                    {"href": "/docs/components/alert-dialog", "label": "Alert Dialog"},
                    {"href": "/docs/components/avatar", "label": "Avatar"},
                    {"href": "/docs/components/badge", "label": "Badge"},
                    {"href": "/docs/components/breadcrumb", "label": "Breadcrumb"},
                    {"href": "/docs/components/button", "label": "Button", "active": True},
                    {"href": "/docs/components/calendar", "label": "Calendar"},
                    {"href": "/docs/components/card", "label": "Card"},
                    {"href": "/docs/components/carousel", "label": "Carousel"},
                    {"href": "/docs/components/checkbox", "label": "Checkbox"},
                    {"href": "/docs/components/collapsible", "label": "Collapsible"},
                    {"href": "/docs/components/combobox", "label": "Combobox"},
                    {"href": "/docs/components/command", "label": "Command"},
                    {"href": "/docs/components/dialog", "label": "Dialog"},
                    {"href": "/docs/components/drawer", "label": "Drawer"},
                    {"href": "/docs/components/dropdown-menu", "label": "Dropdown Menu"},
                    {"href": "/docs/components/form", "label": "Form"},
                    {"href": "/docs/components/input", "label": "Input"},
                    {"href": "/docs/components/label", "label": "Label"},
                    {"href": "/docs/components/popover", "label": "Popover"},
                    {"href": "/docs/components/select", "label": "Select"},
                    {"href": "/docs/components/sidebar", "label": "Sidebar"},
                    {"href": "/docs/components/table", "label": "Table"},
                    {"href": "/docs/components/tabs", "label": "Tabs"},
                    {"href": "/docs/components/textarea", "label": "Textarea"},
                    {"href": "/docs/components/toast", "label": "Toast"},
                    {"href": "/docs/components/tooltip", "label": "Tooltip"}
                ]
            }
        ]
    
    # Mobile overlay backdrop
    mobile_backdrop = Div(
        cls="fixed inset-0 z-30 bg-black/80 md:hidden",
        ds_show="$showMobileMenu",
        ds_on_click="$showMobileMenu = false"
    ) if mobile_overlay else ""
    
    return Div(
        mobile_backdrop,
        
        # Sidebar content
        Aside(
            Div(
                # Mobile close button
                Div(
                    Button(
                        IconifyIcon("ph:x-bold", cls="h-4 w-4"),
                        variant="ghost",
                        size="icon",
                        ds_on_click="$showMobileMenu = false",
                        aria_label="Close menu"
                    ),
                    cls="flex items-center justify-end p-2 md:hidden"
                ),
                
                # Navigation sections
                Nav(
                    *[
                        SidebarSection(
                            title=section["title"],
                            items=section["items"],
                            collapsible=section.get("collapsible", True),
                            default_open=section.get("default_open", True)
                        )
                        for section in sections
                    ],
                    cls="grid items-start px-2 text-sm font-medium lg:px-4"
                ),
                
                cls="relative overflow-hidden h-full py-2"
            ),
            
            cls=cn(
                # Base styles
                "fixed left-0 top-14 z-40 h-[calc(100vh-3.5rem)] w-full shrink-0 bg-background",
                # Mobile: hidden by default, slide in when open
                "translate-x-[-100%] transition-transform duration-300 md:translate-x-0",
                # Desktop: always visible, fixed width
                "md:sticky md:block md:w-64 md:border-r",
                # Show on mobile when menu is open
                "data-[show=true]:translate-x-0",
                class_name
            ),
            ds_class_data_show="$showMobileMenu",
            **attrs
        ),
        
        # Spacer for desktop layout
        Div(cls="hidden md:block md:w-64 md:shrink-0"),
        
        cls="relative"
    )


def docs_sidebar(
    sections: Optional[List[Dict[str, Any]]] = None,
    class_name: str = "",
    mobile_overlay: bool = True,
    **attrs
) -> FT:
    """Alias for DocsSidebar() using lowercase convention."""
    return DocsSidebar(
        sections=sections,
        class_name=class_name,
        mobile_overlay=mobile_overlay,
        **attrs
    )