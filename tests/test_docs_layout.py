"""Tests for documentation layout components."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
from starhtml import *
from components.docs import DocsLayout, DocsHeader, DocsSidebar, DocsBreadcrumb, DocsFooter


def test_docs_header_renders():
    """Test that DocsHeader renders correctly."""
    header = DocsHeader()
    html = str(header)
    
    assert "<header" in html
    assert "shadcn/ui" in html
    assert "Search documentation" in html
    assert "data-signals" in html


def test_docs_sidebar_renders():
    """Test that DocsSidebar renders correctly."""
    sidebar = DocsSidebar()
    html = str(sidebar)
    
    assert "<aside" in html
    assert "Getting Started" in html
    assert "Components" in html
    assert "Introduction" in html
    assert "Button" in html


def test_docs_breadcrumb_renders():
    """Test that DocsBreadcrumb renders correctly."""
    items = [
        {"label": "Docs", "href": "/docs"},
        {"label": "Components", "href": "/docs/components"},
        {"label": "Button", "active": True}
    ]
    breadcrumb = DocsBreadcrumb(items)
    html = str(breadcrumb)
    
    assert "<nav" in html
    assert "aria-label=\"Breadcrumb\"" in html
    assert "Docs" in html
    assert "Components" in html
    assert "Button" in html


def test_docs_footer_renders():
    """Test that DocsFooter renders correctly."""
    footer = DocsFooter()
    html = str(footer)
    
    assert "<footer" in html
    assert "Built by shadcn" in html
    assert "Hosted on Vercel" in html
    assert "GitHub" in html


def test_docs_layout_renders():
    """Test that complete DocsLayout renders correctly."""
    layout = DocsLayout(
        H1("Test Page"),
        P("Test content"),
        title="Test",
        description="Test description",
        breadcrumb_items=[
            {"label": "Docs", "href": "/docs"},
            {"label": "Test", "active": True}
        ]
    )
    html = str(layout)
    
    # Check for main structural elements
    assert "<header" in html
    assert "<aside" in html  # sidebar
    assert "<main" in html
    assert "<footer" in html
    
    # Check for content
    assert "Test Page" in html
    assert "Test content" in html
    assert "Test description" in html
    assert "shadcn/ui" in html
    
    # Check for responsive classes
    assert "md:hidden" in html  # mobile menu
    assert "md:w-64" in html    # sidebar width


def test_docs_layout_without_sidebar():
    """Test DocsLayout without sidebar."""
    layout = DocsLayout(
        H1("No Sidebar"),
        show_sidebar=False
    )
    html = str(layout)
    
    assert "<header" in html
    assert "<main" in html
    assert "<footer" in html
    # Should not have sidebar
    assert "<aside" not in html


def test_docs_layout_with_custom_nav():
    """Test DocsLayout with custom navigation items."""
    custom_nav = [
        {"href": "/custom", "label": "Custom", "active": True},
        {"href": "/other", "label": "Other"}
    ]
    
    layout = DocsLayout(
        H1("Custom Nav"),
        nav_items=custom_nav
    )
    html = str(layout)
    
    assert "Custom" in html
    assert "Other" in html


def test_lowercase_aliases():
    """Test that lowercase aliases work."""
    from components.docs import docs_header, docs_sidebar, docs_breadcrumb, docs_footer, docs_layout
    
    # These should work without errors
    header = docs_header()
    sidebar = docs_sidebar()
    breadcrumb = docs_breadcrumb([{"label": "Test", "active": True}])
    footer = docs_footer()
    layout = docs_layout(H1("Test"))
    
    assert all(str(component) for component in [header, sidebar, breadcrumb, footer, layout])


def test_component_customization():
    """Test component customization options."""
    # Custom header
    header = DocsHeader(
        logo_text="Custom Logo",
        github_stars="100k",
        show_search=False
    )
    html = str(header)
    assert "Custom Logo" in html
    assert "100k" in html
    assert "Search documentation" not in html
    
    # Custom footer
    footer = DocsFooter(
        attribution="Built by Custom Team",
        hosting_info="Hosted on Custom Platform"
    )
    html = str(footer)
    assert "Custom Team" in html
    assert "Custom Platform" in html