"""Main layout wrapper for shadcn-ui documentation."""
from typing import Optional, List, Dict, Any
from starhtml import *
from .header import DocsHeader
from .sidebar import DocsSidebar
from .breadcrumb import DocsBreadcrumb
from .footer import DocsFooter
from ..utils import cn


def DocsLayout(
    *content,
    title: str = "",
    description: str = "",
    breadcrumb_items: Optional[List[Dict[str, Any]]] = None,
    
    # Header configuration
    logo_text: str = "shadcn/ui",
    logo_href: str = "/",
    nav_items: Optional[List[Dict[str, Any]]] = None,
    github_stars: str = "88.0k",
    show_search: bool = True,
    show_github: bool = True,
    show_theme_toggle: bool = True,
    
    # Sidebar configuration  
    sidebar_sections: Optional[List[Dict[str, Any]]] = None,
    show_sidebar: bool = True,
    
    # Footer configuration
    footer_attribution: str = "Built by shadcn",
    footer_hosting: str = "Hosted on Vercel",
    footer_source_text: str = "The source code is available on GitHub",
    footer_source_href: str = "https://github.com/shadcn-ui/ui",
    footer_links: Optional[List[Dict[str, Any]]] = None,
    show_footer: bool = True,
    
    # Layout options
    max_width: str = "screen-2xl",
    container_class: str = "",
    content_class: str = "",
    class_name: str = "",
    **attrs
) -> FT:
    """
    Main documentation layout wrapper that combines header, sidebar, content, and footer.
    
    Args:
        *content: Main content elements
        title: Page title for the content area
        description: Page description
        breadcrumb_items: Breadcrumb navigation items
        
        # Header options
        logo_text: Logo text
        logo_href: Logo link destination  
        nav_items: Main navigation items
        github_stars: GitHub star count
        show_search: Whether to show search
        show_github: Whether to show GitHub link
        show_theme_toggle: Whether to show theme toggle
        
        # Sidebar options
        sidebar_sections: Navigation sections for sidebar
        show_sidebar: Whether to show sidebar
        
        # Footer options
        footer_attribution: Footer attribution text
        footer_hosting: Footer hosting info
        footer_source_text: Source code link text
        footer_source_href: Source code URL
        footer_links: Additional footer links
        show_footer: Whether to show footer
        
        # Layout options
        max_width: Maximum container width
        container_class: Additional container classes
        content_class: Additional content area classes
        class_name: Additional root classes
        **attrs: Additional HTML attributes
        
    Returns:
        Complete documentation layout
        
    Examples:
        # Basic layout
        DocsLayout(
            H1("Button"),
            P("A clickable button component.")
        )
        
        # With breadcrumbs and custom title
        DocsLayout(
            H1("Button Component"),
            P("Documentation for the button component."),
            title="Button",
            breadcrumb_items=[
                {"label": "Docs", "href": "/docs"},
                {"label": "Components", "href": "/docs/components"},
                {"label": "Button", "active": True}
            ]
        )
        
        # Custom sidebar sections
        DocsLayout(
            content,
            sidebar_sections=[
                {
                    "title": "Getting Started",
                    "items": [...]
                }
            ]
        )
    """
    
    return Div(
        # Header
        DocsHeader(
            logo_text=logo_text,
            logo_href=logo_href,
            nav_items=nav_items,
            github_stars=github_stars,
            show_search=show_search,
            show_github=show_github,
            show_theme_toggle=show_theme_toggle
        ),
        
        # Main content area
        Div(
            # Sidebar (if enabled)
            (
                DocsSidebar(
                    sections=sidebar_sections,
                    mobile_overlay=True
                ) if show_sidebar else ""
            ),
            
            # Main content
            Main(
                Div(
                    # Breadcrumb navigation
                    (
                        DocsBreadcrumb(items=breadcrumb_items) 
                        if breadcrumb_items else ""
                    ),
                    
                    # Page header (if title provided)
                    (
                        Div(
                            H1(title, cls="scroll-m-20 text-4xl font-bold tracking-tight"),
                            (
                                P(description, cls="text-xl text-muted-foreground")
                                if description else ""
                            ),
                            cls="space-y-2 pb-8 pt-6 md:pb-10 md:pt-10 lg:py-10"
                        ) if title else ""
                    ),
                    
                    # Main content
                    Div(
                        *content,
                        cls=cn("prose prose-slate max-w-none dark:prose-invert", content_class)
                    ),
                    
                    cls=cn(f"container mx-auto max-w-{max_width} px-4 py-6 lg:py-8", container_class)
                ),
                
                cls="flex-1"
            ),
            
            cls="flex min-h-[calc(100vh-3.5rem)]"
        ),
        
        # Footer (if enabled)
        (
            DocsFooter(
                attribution=footer_attribution,
                hosting_info=footer_hosting,
                source_text=footer_source_text,
                source_href=footer_source_href,
                links=footer_links
            ) if show_footer else ""
        ),
        
        cls=cn("flex min-h-screen flex-col", class_name),
        **attrs
    )


def docs_layout(
    *content,
    title: str = "",
    description: str = "",
    breadcrumb_items: Optional[List[Dict[str, Any]]] = None,
    
    # Header configuration
    logo_text: str = "shadcn/ui",
    logo_href: str = "/",
    nav_items: Optional[List[Dict[str, Any]]] = None,
    github_stars: str = "88.0k",
    show_search: bool = True,
    show_github: bool = True,
    show_theme_toggle: bool = True,
    
    # Sidebar configuration  
    sidebar_sections: Optional[List[Dict[str, Any]]] = None,
    show_sidebar: bool = True,
    
    # Footer configuration
    footer_attribution: str = "Built by shadcn",
    footer_hosting: str = "Hosted on Vercel",
    footer_source_text: str = "The source code is available on GitHub",
    footer_source_href: str = "https://github.com/shadcn-ui/ui",
    footer_links: Optional[List[Dict[str, Any]]] = None,
    show_footer: bool = True,
    
    # Layout options
    max_width: str = "screen-2xl",
    container_class: str = "",
    content_class: str = "",
    class_name: str = "",
    **attrs
) -> FT:
    """Alias for DocsLayout() using lowercase convention."""
    return DocsLayout(
        *content,
        title=title,
        description=description,
        breadcrumb_items=breadcrumb_items,
        logo_text=logo_text,
        logo_href=logo_href,
        nav_items=nav_items,
        github_stars=github_stars,
        show_search=show_search,
        show_github=show_github,
        show_theme_toggle=show_theme_toggle,
        sidebar_sections=sidebar_sections,
        show_sidebar=show_sidebar,
        footer_attribution=footer_attribution,
        footer_hosting=footer_hosting,
        footer_source_text=footer_source_text,
        footer_source_href=footer_source_href,
        footer_links=footer_links,
        show_footer=show_footer,
        max_width=max_width,
        container_class=container_class,
        content_class=content_class,
        class_name=class_name,
        **attrs
    )