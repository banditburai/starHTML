"""Header navigation component for shadcn-ui documentation."""
from typing import Optional, List, Dict, Any
from starhtml import *
from ..ui.button import Button
from ..ui.theme_toggle import ThemeToggle
from ..ui.iconify import IconifyIcon
from ..utils import cn


def SearchTrigger(**attrs) -> FT:
    """Search trigger button that opens command palette."""
    return Button(
        Div(
            Span("Search documentation...", cls="hidden lg:inline-flex"),
            Span("Search...", cls="lg:hidden"),
            cls="flex-1 text-left text-muted-foreground"
        ),
        Div(
            Kbd("⌘", cls="pointer-events-none inline-flex h-5 select-none items-center gap-1 rounded border bg-muted px-1.5 font-mono text-[10px] font-medium text-muted-foreground"),
            Kbd("K", cls="pointer-events-none inline-flex h-5 select-none items-center gap-1 rounded border bg-muted px-1.5 font-mono text-[10px] font-medium text-muted-foreground"),
            cls="hidden sm:flex gap-1"
        ),
        variant="outline",
        cls="relative h-8 w-full justify-between rounded-[0.5rem] bg-muted/50 text-sm font-normal text-muted-foreground shadow-none sm:pr-12 md:w-40 lg:w-64",
        ds_on_click="$showSearch = true",
        **attrs
    )


def SearchModal(**attrs) -> FT:
    """Command palette search modal."""
    return Div(
        # Backdrop
        Div(
            cls="fixed inset-0 bg-black/80 z-50",
            ds_show="$showSearch",
            ds_on_click="$showSearch = false"
        ),
        # Modal
        Div(
            Div(
                # Search input
                Div(
                    IconifyIcon("ph:magnifying-glass-bold", cls="h-4 w-4 shrink-0 opacity-50"),
                    Input(
                        placeholder="Type a command or search...",
                        cls="flex h-10 w-full rounded-md bg-transparent py-3 text-sm outline-none placeholder:text-muted-foreground disabled:cursor-not-allowed disabled:opacity-50",
                        autofocus=True,
                        ds_model="$searchQuery"
                    ),
                    cls="flex items-center border-b px-3"
                ),
                # Search results area
                Div(
                    Div("No results found.", cls="px-6 py-6 text-center text-sm text-muted-foreground"),
                    cls="max-h-[300px] overflow-y-auto overflow-x-hidden"
                ),
                cls="fixed left-[50%] top-[50%] z-50 grid w-full max-w-lg translate-x-[-50%] translate-y-[-50%] gap-4 border bg-background p-0 shadow-lg duration-200 sm:rounded-lg"
            ),
            ds_show="$showSearch",
            ds_on_keydown="if(event.key === 'Escape') $showSearch = false"
        ),
        **attrs
    )


def NavItem(href: str, label: str, active: bool = False, **attrs) -> FT:
    """Navigation item for main nav."""
    return A(
        label,
        href=href,
        cls=cn(
            "inline-flex items-center justify-center rounded-md text-sm font-medium transition-colors",
            "hover:bg-accent hover:text-accent-foreground focus-visible:outline-none",
            "focus-visible:ring-2 focus-visible:ring-ring h-9 px-4 py-2",
            "text-foreground/60 hover:text-foreground/80" if not active else "text-foreground"
        ),
        **attrs
    )


def GitHubLink(stars: str = "88.0k", **attrs) -> FT:
    """GitHub repository link with star count."""
    return A(
        Div(
            IconifyIcon("ph:star-bold", cls="h-4 w-4"),
            Span(stars, cls="hidden sm:inline-block"),
            cls="flex items-center gap-1"
        ),
        href="https://github.com/shadcn-ui/ui",
        target="_blank",
        rel="noopener noreferrer",
        cls=cn(
            "inline-flex items-center justify-center rounded-md text-sm font-medium transition-colors",
            "hover:bg-accent hover:text-accent-foreground focus-visible:outline-none",
            "focus-visible:ring-2 focus-visible:ring-ring h-9 px-4 py-2"
        ),
        **attrs
    )


def MobileMenuButton(**attrs) -> FT:
    """Mobile hamburger menu button."""
    return Button(
        IconifyIcon("ph:list-bold", cls="h-5 w-5"),
        variant="ghost",
        size="icon",
        cls="md:hidden",
        ds_on_click="$showMobileMenu = !$showMobileMenu",
        aria_label="Toggle mobile menu",
        **attrs
    )


def DocsHeader(
    logo_text: str = "shadcn/ui",
    logo_href: str = "/",
    nav_items: Optional[List[Dict[str, Any]]] = None,
    github_stars: str = "88.0k",
    show_search: bool = True,
    show_github: bool = True,
    show_theme_toggle: bool = True,
    class_name: str = "",
    **attrs
) -> FT:
    """
    Main header navigation component.
    
    Args:
        logo_text: Logo text to display
        logo_href: Logo link destination
        nav_items: List of navigation items with 'href', 'label', and optional 'active'
        github_stars: Star count display for GitHub link
        show_search: Whether to show search trigger
        show_github: Whether to show GitHub link
        show_theme_toggle: Whether to show theme toggle
        class_name: Additional CSS classes
        **attrs: Additional HTML attributes
        
    Returns:
        Header element with navigation
    """
    if nav_items is None:
        nav_items = [
            {"href": "/docs", "label": "Docs"},
            {"href": "/docs/components", "label": "Components"},
            {"href": "/blocks", "label": "Blocks"},
            {"href": "/charts", "label": "Charts"},
            {"href": "/themes", "label": "Themes"},
            {"href": "/colors", "label": "Colors"},
        ]
    
    return Header(
        # Search modal (rendered once at top level)
        SearchModal() if show_search else "",
        
        Div(
            # Left section: Logo and main nav
            Div(
                # Mobile menu button
                MobileMenuButton(),
                
                # Logo
                A(
                    logo_text,
                    href=logo_href,
                    cls="mr-4 flex items-center space-x-2 lg:mr-6"
                ),
                
                # Main navigation (hidden on mobile)
                Nav(
                    *[
                        NavItem(
                            href=item["href"],
                            label=item["label"],
                            active=item.get("active", False)
                        )
                        for item in nav_items
                    ],
                    cls="hidden md:flex items-center gap-4 text-sm lg:gap-6"
                ),
                
                cls="flex items-center"
            ),
            
            # Right section: Search, GitHub, Theme Toggle
            Div(
                # Search trigger
                SearchTrigger() if show_search else "",
                
                # GitHub link
                GitHubLink(stars=github_stars) if show_github else "",
                
                # Theme toggle
                ThemeToggle() if show_theme_toggle else "",
                
                cls="flex items-center gap-2"
            ),
            
            cls="container mx-auto flex h-14 max-w-screen-2xl items-center justify-between px-4"
        ),
        
        cls=cn(
            "sticky top-0 z-50 w-full border-b border-border/40 bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60",
            class_name
        ),
        ds_signals={
            "showSearch": False,
            "showMobileMenu": False,
            "searchQuery": ""
        },
        **attrs
    )


def docs_header(
    logo_text: str = "shadcn/ui",
    logo_href: str = "/",
    nav_items: Optional[List[Dict[str, Any]]] = None,
    github_stars: str = "88.0k",
    show_search: bool = True,
    show_github: bool = True,
    show_theme_toggle: bool = True,
    class_name: str = "",
    **attrs
) -> FT:
    """Alias for DocsHeader() using lowercase convention."""
    return DocsHeader(
        logo_text=logo_text,
        logo_href=logo_href,
        nav_items=nav_items,
        github_stars=github_stars,
        show_search=show_search,
        show_github=show_github,
        show_theme_toggle=show_theme_toggle,
        class_name=class_name,
        **attrs
    )