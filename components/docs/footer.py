"""Footer component for shadcn-ui documentation."""
from typing import Optional, List, Dict, Any
from starhtml import *
from ..utils import cn


def DocsFooter(
    attribution: str = "Built by shadcn",
    hosting_info: str = "Hosted on Vercel",
    source_text: str = "The source code is available on GitHub",
    source_href: str = "https://github.com/shadcn-ui/ui",
    links: Optional[List[Dict[str, Any]]] = None,
    class_name: str = "",
    **attrs
) -> FT:
    """
    Footer component for documentation pages.
    
    Args:
        attribution: Credit text for the creator
        hosting_info: Information about hosting platform
        source_text: Text for source code link
        source_href: URL for source code repository
        links: Optional list of additional footer links with 'href', 'label'
        class_name: Additional CSS classes
        **attrs: Additional HTML attributes
        
    Returns:
        Footer element
        
    Examples:
        # Basic footer
        Footer()
        
        # With custom content
        Footer(
            attribution="Built by Your Team",
            hosting_info="Hosted on Netlify",
            source_text="View source on GitHub",
            source_href="https://github.com/yourorg/repo"
        )
        
        # With additional links
        Footer(
            links=[
                {"href": "/privacy", "label": "Privacy Policy"},
                {"href": "/terms", "label": "Terms of Service"}
            ]
        )
    """
    return Footer(
        Div(
            # Main footer content
            Div(
                # Attribution and hosting info
                P(
                    attribution,
                    ". ",
                    hosting_info,
                    ".",
                    cls="text-sm text-muted-foreground"
                ),
                
                # Source code link
                P(
                    A(
                        source_text,
                        href=source_href,
                        target="_blank",
                        rel="noopener noreferrer",
                        cls="font-medium underline underline-offset-4 hover:text-foreground transition-colors"
                    ),
                    ".",
                    cls="text-sm text-muted-foreground"
                ),
                
                # Additional links if provided
                (
                    Div(
                        *[
                            A(
                                link["label"],
                                href=link["href"],
                                cls="text-sm text-muted-foreground hover:text-foreground transition-colors underline-offset-4 hover:underline"
                            )
                            for link in links
                        ],
                        cls="flex flex-wrap gap-4 mt-2"
                    ) if links else ""
                ),
                
                cls="space-y-1"
            ),
            
            cls="container mx-auto max-w-screen-2xl px-4 py-6 md:py-8"
        ),
        
        cls=cn(
            "border-t border-border/40 bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60",
            class_name
        ),
        **attrs
    )


def docs_footer(
    attribution: str = "Built by shadcn",
    hosting_info: str = "Hosted on Vercel",
    source_text: str = "The source code is available on GitHub",
    source_href: str = "https://github.com/shadcn-ui/ui",
    links: Optional[List[Dict[str, Any]]] = None,
    class_name: str = "",
    **attrs
) -> FT:
    """Alias for DocsFooter() using lowercase convention."""
    return DocsFooter(
        attribution=attribution,
        hosting_info=hosting_info,
        source_text=source_text,
        source_href=source_href,
        links=links,
        class_name=class_name,
        **attrs
    )