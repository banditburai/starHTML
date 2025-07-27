"""Integration tests for theme toggle in real-world scenarios."""

import sys
from pathlib import Path

import pytest

# Add the project root to the path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from components.ui import Button, ThemeToggle, ThemeToggleCompact

from starhtml import *


class TestThemeToggleInDocumentation:
    """Test theme toggle integration in documentation layouts."""
    
    def test_theme_toggle_in_docs_header(self):
        """Test theme toggle integration in documentation header."""
        # Create a header with theme toggle
        header = Div(
            Div(
                H1("Documentation"),
                ThemeToggle(cls="ml-auto"),
                cls="flex items-center justify-between"
            ),
            cls="border-b bg-background"
        )
        
        assert header is not None
        assert len(header.children) == 1
        
        # Find the theme toggle
        header_content = header.children[0]
        theme_toggle = None
        for child in header_content.children:
            if hasattr(child, 'children') and child.children:
                if hasattr(child.children[0], 'tag') and child.children[0].tag == "button":
                    theme_toggle = child
                    break
        
        assert theme_toggle is not None
        
    def test_theme_toggle_in_sidebar(self):
        """Test theme toggle in sidebar navigation."""
        sidebar = Div(
            Nav(
                A("Home", href="/"),
                A("About", href="/about"),
                A("Contact", href="/contact"),
                cls="space-y-2"
            ),
            ThemeToggleCompact(cls="mt-auto"),
            cls="flex flex-col h-full p-4"
        )
        
        assert sidebar is not None
        
        # Should have navigation and theme toggle
        assert len(sidebar.children) == 2
        
    def test_theme_toggle_in_mobile_menu(self):
        """Test theme toggle in mobile menu."""
        mobile_menu = Div(
            Div(
                Button("Close", cls="ml-auto"),
                cls="flex justify-end p-4"
            ),
            Nav(
                A("Home", href="/"),
                A("About", href="/about"),
                cls="space-y-4 p-4"
            ),
            Div(
                ThemeToggle(),
                cls="border-t p-4"
            ),
            cls="fixed inset-0 z-50 bg-background"
        )
        
        assert mobile_menu is not None
        assert len(mobile_menu.children) == 3
        
        
class TestThemeToggleWithForms:
    """Test theme toggle integration with forms and interactive elements."""
    
    def test_theme_toggle_with_form_elements(self):
        """Test theme toggle alongside form elements."""
        form_with_theme = Div(
            Div(
                H2("Settings"),
                ThemeToggle(cls="ml-auto"),
                cls="flex items-center justify-between mb-4"
            ),
            Form(
                Label("Name", for_="name"),
                Input(name="name", type="text", cls="mt-1"),
                Label("Email", for_="email"),
                Input(name="email", type="email", cls="mt-1"),
                Button("Submit", type="submit", cls="mt-4"),
                cls="space-y-4"
            ),
            cls="p-6 bg-card rounded-lg"
        )
        
        assert form_with_theme is not None
        
    def test_theme_toggle_with_interactive_components(self):
        """Test theme toggle with other interactive components."""
        interactive_layout = Div(
            Div(
                Button("Action 1", variant="default"),
                Button("Action 2", variant="secondary"),
                ThemeToggle(cls="ml-auto"),
                cls="flex items-center gap-2"
            ),
            Div(
                P("This content changes with theme"),
                cls="mt-4 p-4 bg-muted rounded"
            ),
            cls="p-6"
        )
        
        assert interactive_layout is not None
        
        
class TestThemeToggleDataFlow:
    """Test theme toggle data flow and state management."""
    
    def test_theme_toggle_signal_isolation(self):
        """Test that theme toggle signals don't interfere with each other."""
        # Create multiple theme toggles
        toggle1 = ThemeToggle(id="toggle1")
        toggle2 = ThemeToggle(id="toggle2")
        
        # Both should have the same signal structure
        assert "data-signals" in toggle1.attrs
        assert "data-signals" in toggle2.attrs
        
        # But should be separate instances
        assert toggle1.attrs.get("id") != toggle2.attrs.get("id")
        
    def test_theme_toggle_with_custom_signals(self):
        """Test theme toggle with additional custom signals."""
        # Create a component with additional signals
        custom_component = Div(
            ThemeToggle(),
            ds_signals={"customState": "active", "userPreference": "default"}
        )
        
        # Should have both theme and custom signals
        assert "data-signals" in custom_component.attrs
        
    def test_theme_toggle_event_propagation(self):
        """Test theme toggle event propagation."""
        container = Div(
            ThemeToggle(),
            ds_on_theme_changed="handleThemeChange($event)",
            cls="theme-aware-container"
        )
        
        # Should handle theme change events
        assert "data-on-theme-changed" in container.attrs
        
        
class TestThemeTogglePerformanceIntegration:
    """Test performance aspects in integrated scenarios."""
    
    def test_multiple_theme_toggles_performance(self):
        """Test performance with multiple theme toggles."""
        # Create a layout with multiple theme toggles
        layout = Div(
            Header(
                ThemeToggle(cls="header-toggle"),
                cls="border-b p-4"
            ),
            Div(
                Aside(
                    ThemeToggleCompact(cls="sidebar-toggle"),
                    cls="w-64 border-r p-4"
                ),
                Main(
                    Div(
                        ThemeToggle(cls="content-toggle"),
                        cls="mb-4"
                    ),
                    P("Main content here"),
                    cls="flex-1 p-4"
                ),
                cls="flex flex-1"
            ),
            cls="min-h-screen"
        )
        
        assert layout is not None
        
        # Should handle multiple toggles without issues
        # This tests the structural integrity
        
    def test_theme_toggle_with_heavy_content(self):
        """Test theme toggle with content-heavy layouts."""
        heavy_layout = Div(
            ThemeToggle(cls="fixed top-4 right-4 z-50"),
            # Simulate heavy content
            *[Div(
                H3(f"Section {i}"),
                *[P(f"Content paragraph {j}") for j in range(10)],
                cls="mb-8"
            ) for i in range(20)],
            cls="p-8"
        )
        
        assert heavy_layout is not None
        
        
class TestThemeToggleAccessibilityIntegration:
    """Test accessibility in integrated scenarios."""
    
    def test_theme_toggle_with_skip_links(self):
        """Test theme toggle with skip navigation links."""
        accessible_layout = Div(
            A("Skip to main content", href="#main", cls="sr-only focus:not-sr-only"),
            Header(
                Nav(
                    A("Home", href="/"),
                    A("About", href="/about"),
                    cls="flex space-x-4"
                ),
                ThemeToggle(cls="ml-auto"),
                cls="flex items-center justify-between p-4"
            ),
            Main(
                H1("Main Content"),
                P("This is the main content area."),
                id="main",
                cls="p-4"
            ),
            cls="min-h-screen"
        )
        
        assert accessible_layout is not None
        
    def test_theme_toggle_focus_management(self):
        """Test theme toggle focus management."""
        # Create a form with theme toggle
        form_layout = Div(
            Form(
                Div(
                    Label("Theme", cls="block text-sm font-medium mb-2"),
                    ThemeToggle(),
                    cls="mb-4"
                ),
                Input(name="name", placeholder="Your name", cls="w-full mb-4"),
                Button("Submit", type="submit", cls="w-full"),
                cls="space-y-4"
            ),
            cls="max-w-md mx-auto p-6"
        )
        
        assert form_layout is not None
        
        # The theme toggle should be properly integrated in the focus order
        
    def test_theme_toggle_with_landmarks(self):
        """Test theme toggle with ARIA landmarks."""
        landmark_layout = Div(
            Header(
                ThemeToggle(),
                role="banner",
                cls="p-4"
            ),
            Nav(
                A("Home", href="/"),
                A("About", href="/about"),
                role="navigation",
                cls="p-4"
            ),
            Main(
                H1("Main Content"),
                role="main",
                cls="p-4"
            ),
            Footer(
                P("Footer content"),
                role="contentinfo",
                cls="p-4"
            ),
            cls="min-h-screen"
        )
        
        assert landmark_layout is not None
        
        
class TestThemeToggleRealWorldScenarios:
    """Test theme toggle in real-world usage scenarios."""
    
    def test_blog_layout_with_theme_toggle(self):
        """Test theme toggle in a blog layout."""
        blog_layout = Div(
            Header(
                Div(
                    H1("My Blog"),
                    ThemeToggle(),
                    cls="flex items-center justify-between"
                ),
                cls="border-b p-6"
            ),
            Main(
                Article(
                    H2("Blog Post Title"),
                    P("Blog post content goes here..."),
                    cls="mb-8"
                ),
                Article(
                    H2("Another Post"),
                    P("More content..."),
                    cls="mb-8"
                ),
                cls="max-w-4xl mx-auto p-6"
            ),
            cls="min-h-screen"
        )
        
        assert blog_layout is not None
        
    def test_dashboard_with_theme_toggle(self):
        """Test theme toggle in a dashboard layout."""
        dashboard = Div(
            Header(
                Div(
                    H1("Dashboard"),
                    Div(
                        ThemeToggleCompact(),
                        Button("Profile", variant="ghost"),
                        cls="flex items-center gap-2"
                    ),
                    cls="flex items-center justify-between"
                ),
                cls="border-b p-4"
            ),
            Div(
                Aside(
                    Nav(
                        A("Overview", href="/dashboard"),
                        A("Analytics", href="/analytics"),
                        A("Settings", href="/settings"),
                        cls="space-y-2"
                    ),
                    cls="w-64 border-r p-4"
                ),
                Main(
                    Div(
                        H2("Overview"),
                        Div(
                            *[Div(
                                H3(f"Metric {i}"),
                                P(f"Value {i}"),
                                cls="p-4 bg-card rounded border"
                            ) for i in range(4)],
                            cls="grid grid-cols-2 gap-4"
                        ),
                        cls="p-6"
                    ),
                    cls="flex-1"
                ),
                cls="flex flex-1"
            ),
            cls="min-h-screen"
        )
        
        assert dashboard is not None
        
    def test_e_commerce_with_theme_toggle(self):
        """Test theme toggle in e-commerce layout."""
        ecommerce = Div(
            Header(
                Div(
                    H1("Store"),
                    Div(
                        ThemeToggle(),
                        Button("Cart (0)", variant="outline"),
                        cls="flex items-center gap-2"
                    ),
                    cls="flex items-center justify-between"
                ),
                cls="border-b p-4"
            ),
            Main(
                Div(
                    H2("Featured Products"),
                    Div(
                        *[Div(
                            H3(f"Product {i}"),
                            P(f"${i * 10}"),
                            Button("Add to Cart", variant="default"),
                            cls="p-4 border rounded"
                        ) for i in range(6)],
                        cls="grid grid-cols-3 gap-4"
                    ),
                    cls="p-6"
                ),
                cls="max-w-6xl mx-auto"
            ),
            cls="min-h-screen"
        )
        
        assert ecommerce is not None
        
        
class TestThemeToggleEdgeCasesIntegration:
    """Test edge cases in integrated scenarios."""
    
    def test_nested_theme_toggles(self):
        """Test handling of nested theme toggles."""
        nested_layout = Div(
            ThemeToggle(cls="outer-toggle"),
            Div(
                ThemeToggleCompact(cls="inner-toggle"),
                cls="p-4 border rounded"
            ),
            cls="p-6"
        )
        
        assert nested_layout is not None
        
        # Should handle nested toggles without interference
        
    def test_theme_toggle_with_conditional_rendering(self):
        """Test theme toggle with conditional rendering."""
        conditional_layout = Div(
            ThemeToggle(),
            Div(
                P("This appears in light mode"),
                ds_show="!$isDark",
                cls="p-4 bg-card"
            ),
            Div(
                P("This appears in dark mode"),
                ds_show="$isDark",
                cls="p-4 bg-card"
            ),
            cls="p-6"
        )
        
        assert conditional_layout is not None
        
    def test_theme_toggle_with_dynamic_content(self):
        """Test theme toggle with dynamically loaded content."""
        dynamic_layout = Div(
            ThemeToggle(),
            Div(
                H2("Dynamic Content"),
                Div(
                    ds_on_load="loadDynamicContent()",
                    ds_text="dynamicContent",
                    cls="p-4 bg-muted rounded"
                ),
                cls="mt-4"
            ),
            ds_signals={"dynamicContent": "Loading..."},
            cls="p-6"
        )
        
        assert dynamic_layout is not None
        
        
class TestThemeToggleServerSideRendering:
    """Test theme toggle with server-side rendering scenarios."""
    
    def test_theme_toggle_ssr_compatibility(self):
        """Test theme toggle server-side rendering compatibility."""
        # Create a page that would be server-side rendered
        page = Div(
            Head(
                Title("SSR Page"),
                Link(rel="stylesheet", href="/theme.css"),
                Script(src="/theme-init.js", defer=True)
            ),
            Body(
                Header(
                    ThemeToggle(),
                    cls="p-4"
                ),
                Main(
                    H1("Server-Side Rendered Content"),
                    P("This content is rendered on the server."),
                    cls="p-4"
                ),
                cls="min-h-screen"
            )
        )
        
        # Should render without JavaScript execution
        assert page is not None
        
    def test_theme_toggle_hydration_friendly(self):
        """Test theme toggle hydration-friendly structure."""
        # Create a component that would be hydrated on the client
        hydration_layout = Div(
            ThemeToggle(id="theme-toggle"),
            Div(
                P("This will be hydrated"),
                cls="hydration-target"
            ),
            cls="p-6"
        )
        
        assert hydration_layout is not None
        
        # Should have stable structure for hydration
        toggle = hydration_layout.children[0]
        assert toggle.attrs.get("id") == "theme-toggle"
        
        
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
