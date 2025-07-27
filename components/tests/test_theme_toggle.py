"""Comprehensive tests for theme toggle functionality."""

import sys
from pathlib import Path

import pytest

# Add the project root to the path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from components.ui import ThemeToggle, ThemeToggleCompact


class TestThemeToggleStructure:
    """Test the component structure and HTML output."""
    
    def test_theme_toggle_basic_structure(self):
        """Test basic theme toggle structure."""
        toggle = ThemeToggle()
        
        # Should return a Div element
        assert toggle.tag == "div"
        
        # Should have a button child
        assert len(toggle.children) == 1
        button = toggle.children[0]
        assert button.tag == "button"
        
        # Should have Datastar attributes
        assert "data-signals" in toggle.attrs
        assert "data-on-load" in toggle.attrs
        
    def test_theme_toggle_with_custom_attrs(self):
        """Test theme toggle with custom attributes."""
        toggle = ThemeToggle(cls="custom-class", id="theme-toggle")
        
        assert toggle.attrs.get("class") == "custom-class"
        assert toggle.attrs.get("id") == "theme-toggle"
        
    def test_theme_toggle_compact_structure(self):
        """Test compact theme toggle structure."""
        toggle = ThemeToggleCompact()
        
        # Should return a Div element
        assert toggle.tag == "div"
        
        # Should have a button child
        assert len(toggle.children) == 1
        button = toggle.children[0]
        assert button.tag == "button"
        
        # Should have icon size variant
        assert "icon" in str(button.attrs)
        
    def test_theme_toggle_accessibility(self):
        """Test theme toggle accessibility features."""
        toggle = ThemeToggle()
        button = toggle.children[0]
        
        # Should have aria-label
        assert button.attrs.get("aria-label") == "Toggle theme"
        
        # Should have title for tooltip
        assert button.attrs.get("title") == "Toggle between light and dark mode"
        
    def test_theme_toggle_signals_structure(self):
        """Test Datastar signals structure."""
        toggle = ThemeToggle()
        
        # Should have isDark signal
        signals = toggle.attrs.get("data-signals")
        assert signals is not None
        assert "isDark" in signals
        

class TestThemeToggleJavaScript:
    """Test the JavaScript functionality."""
    
    def test_click_handler_structure(self):
        """Test the click handler JavaScript structure."""
        toggle = ThemeToggle()
        button = toggle.children[0]
        
        click_handler = button.attrs.get("data-on-click")
        assert click_handler is not None
        
        # Should contain key functionality
        assert "$isDark = !$isDark" in click_handler
        assert "document.documentElement" in click_handler
        assert "classList.toggle" in click_handler
        assert "localStorage.setItem" in click_handler
        assert "theme-transitioning" in click_handler
        
    def test_load_handler_structure(self):
        """Test the load handler JavaScript structure."""
        toggle = ThemeToggle()
        
        load_handler = toggle.attrs.get("data-on-load")
        assert load_handler is not None
        
        # Should contain initialization logic
        assert "localStorage.getItem" in load_handler
        assert "window.matchMedia" in load_handler
        assert "prefers-color-scheme" in load_handler
        assert "addEventListener" in load_handler
        
    def test_error_handling_in_javascript(self):
        """Test error handling in JavaScript code."""
        toggle = ThemeToggle()
        button = toggle.children[0]
        
        click_handler = button.attrs.get("data-on-click")
        load_handler = toggle.attrs.get("data-on-load")
        
        # Should have try-catch blocks
        assert "try {" in click_handler
        assert "} catch" in click_handler
        assert "try {" in load_handler
        assert "} catch" in load_handler
        
    def test_custom_event_dispatch(self):
        """Test custom event dispatching."""
        toggle = ThemeToggle()
        button = toggle.children[0]
        
        click_handler = button.attrs.get("data-on-click")
        
        # Should dispatch custom event
        assert "CustomEvent" in click_handler
        assert "theme-changed" in click_handler
        assert "dispatchEvent" in click_handler
        

class TestThemeTogglePerformance:
    """Test performance optimizations."""
    
    def test_batched_dom_operations(self):
        """Test that DOM operations are batched."""
        toggle = ThemeToggle()
        button = toggle.children[0]
        
        click_handler = button.attrs.get("data-on-click")
        
        # Should batch DOM operations
        assert "const html = document.documentElement" in click_handler
        assert "theme-transitioning" in click_handler
        
    def test_transition_classes(self):
        """Test transition class usage."""
        toggle = ThemeToggle()
        button = toggle.children[0]
        
        click_handler = button.attrs.get("data-on-click")
        
        # Should add and remove transition classes
        assert "classList.add('theme-transitioning')" in click_handler
        assert "classList.remove('theme-transitioning')" in click_handler
        assert "setTimeout" in click_handler
        
    def test_optimized_icon_binding(self):
        """Test optimized icon binding."""
        toggle = ThemeToggle()
        button = toggle.children[0]
        icon = button.children[0]
        
        # Should use single icon with binding
        assert "data-bind-icon" in icon.attrs
        assert "ph:sun-bold" in icon.attrs.get("data-bind-icon", "")
        assert "ph:moon-bold" in icon.attrs.get("data-bind-icon", "")
        
    def test_css_transitions(self):
        """Test CSS transition classes."""
        toggle = ThemeToggle()
        button = toggle.children[0]
        icon = button.children[0]
        
        # Should have transition classes
        assert "transition-all duration-200" in icon.attrs.get("class", "")
        assert "transition-colors duration-200" in button.attrs.get("class", "")
        

class TestThemeToggleEdgeCases:
    """Test edge cases and error conditions."""
    
    def test_empty_attributes(self):
        """Test with empty attributes."""
        toggle = ThemeToggle()
        assert toggle is not None
        
    def test_conflicting_attributes(self):
        """Test with conflicting attributes."""
        toggle = ThemeToggle(cls="test", class_="override")
        # Should handle attribute conflicts gracefully
        assert toggle is not None
        
    def test_invalid_attribute_types(self):
        """Test with invalid attribute types."""
        # Should not crash with unusual attribute values
        toggle = ThemeToggle(data_test=123, aria_custom=True)
        assert toggle is not None
        
    def test_compact_vs_regular_differences(self):
        """Test differences between compact and regular variants."""
        regular = ThemeToggle()
        compact = ThemeToggleCompact()
        
        # Should have different button sizes
        regular_button = regular.children[0]
        compact_button = compact.children[0]
        
        # Regular should have padding
        assert "px-4 py-2" in regular_button.attrs.get("class", "")
        
        # Compact should have icon size
        assert "w-8" in compact_button.attrs.get("class", "")
        

class TestThemeToggleIntegration:
    """Test integration with other components."""
    
    def test_theme_toggle_in_layout(self):
        """Test theme toggle within layout components."""
        from starhtml import Div, Header
        
        layout = Div(
            Header(
                ThemeToggle(cls="ml-auto"),
                cls="flex items-center justify-between"
            )
        )
        
        assert layout is not None
        assert len(layout.children) == 1
        
    def test_multiple_theme_toggles(self):
        """Test multiple theme toggle instances."""
        toggle1 = ThemeToggle(id="toggle1")
        toggle2 = ThemeToggle(id="toggle2")
        
        # Should be separate instances
        assert toggle1.attrs.get("id") != toggle2.attrs.get("id")
        
    def test_theme_toggle_with_custom_icons(self):
        """Test theme toggle with custom icon setup."""
        # The optimized version uses icon binding, test that structure
        toggle = ThemeToggle()
        button = toggle.children[0]
        icon = button.children[0]
        
        # Should have icon binding for dynamic switching
        assert "data-bind-icon" in icon.attrs
        
        
class TestThemeToggleSystemIntegration:
    """Test system-level integration features."""
    
    def test_system_theme_detection(self):
        """Test system theme detection logic."""
        toggle = ThemeToggle()
        
        load_handler = toggle.attrs.get("data-on-load")
        
        # Should detect system theme
        assert "prefers-color-scheme: dark" in load_handler
        assert "matchMedia" in load_handler
        
    def test_media_query_listener(self):
        """Test media query change listener."""
        toggle = ThemeToggle()
        
        load_handler = toggle.attrs.get("data-on-load")
        
        # Should listen for system theme changes
        assert "addEventListener" in load_handler
        assert "addListener" in load_handler  # Fallback
        assert "handleSystemThemeChange" in load_handler
        
    def test_localstorage_integration(self):
        """Test localStorage integration."""
        toggle = ThemeToggle()
        button = toggle.children[0]
        
        click_handler = button.attrs.get("data-on-click")
        load_handler = toggle.attrs.get("data-on-load")
        
        # Should save and load from localStorage
        assert "localStorage.setItem" in click_handler
        assert "localStorage.getItem" in load_handler
        
    def test_dom_ready_state_handling(self):
        """Test DOM ready state handling."""
        toggle = ThemeToggle()
        
        load_handler = toggle.attrs.get("data-on-load")
        
        # Should handle different DOM ready states
        assert "document.readyState" in load_handler
        assert "DOMContentLoaded" in load_handler
        

class TestThemeToggleAccessibility:
    """Test accessibility features."""
    
    def test_aria_attributes(self):
        """Test ARIA attributes."""
        toggle = ThemeToggle()
        button = toggle.children[0]
        
        # Should have proper ARIA attributes
        assert "aria-label" in button.attrs
        assert button.attrs.get("aria-label") == "Toggle theme"
        
    def test_title_attribute(self):
        """Test title attribute for tooltip."""
        toggle = ThemeToggle()
        button = toggle.children[0]
        
        # Should have title for tooltip
        assert "title" in button.attrs
        assert "Toggle between light and dark mode" in button.attrs.get("title")
        
    def test_keyboard_navigation(self):
        """Test keyboard navigation support."""
        toggle = ThemeToggle()
        button = toggle.children[0]
        
        # Should be a proper button element
        assert button.tag == "button"
        
        # Should not have tabindex that would interfere with keyboard navigation
        assert "tabindex" not in button.attrs or button.attrs.get("tabindex") != "-1"
        
    def test_reduced_motion_support(self):
        """Test reduced motion support in CSS."""
        # This would be tested in the CSS test suite
        # Here we just verify the structure supports it
        toggle = ThemeToggle()
        
        # Should have transition classes that can be overridden
        assert "transition" in str(toggle).lower()
        

class TestThemeToggleRobustness:
    """Test robustness and error handling."""
    
    def test_malformed_attributes(self):
        """Test with malformed attributes."""
        # Should not crash with malformed attributes
        toggle = ThemeToggle(**{"data-invalid-attr": "value"})
        assert toggle is not None
        
    def test_missing_dependencies(self):
        """Test graceful handling of missing dependencies."""
        # The component should still render even if some dependencies are missing
        toggle = ThemeToggle()
        assert toggle is not None
        assert toggle.tag == "div"
        
    def test_javascript_error_handling(self):
        """Test JavaScript error handling."""
        toggle = ThemeToggle()
        button = toggle.children[0]
        
        click_handler = button.attrs.get("data-on-click")
        load_handler = toggle.attrs.get("data-on-load")
        
        # Should have console.warn for errors
        assert "console.warn" in click_handler
        assert "console.warn" in load_handler
        
    def test_fallback_behavior(self):
        """Test fallback behavior when features are unavailable."""
        toggle = ThemeToggle()
        
        load_handler = toggle.attrs.get("data-on-load")
        
        # Should have fallback for older browsers
        assert "addListener" in load_handler
        
        
class TestThemeToggleDatastarCompliance:
    """Test compliance with Datastar patterns."""
    
    def test_datastar_signal_format(self):
        """Test Datastar signal format."""
        toggle = ThemeToggle()
        
        # Should have proper signal format
        signals = toggle.attrs.get("data-signals")
        assert signals is not None
        assert isinstance(signals, (str, dict))
        
    def test_datastar_event_handlers(self):
        """Test Datastar event handler format."""
        toggle = ThemeToggle()
        button = toggle.children[0]
        
        # Should have data-on-click handler
        assert "data-on-click" in button.attrs
        
        # Should have data-on-load handler
        assert "data-on-load" in toggle.attrs
        
    def test_datastar_binding_format(self):
        """Test Datastar binding format."""
        toggle = ThemeToggle()
        button = toggle.children[0]
        icon = button.children[0]
        
        # Should have proper binding format
        assert "data-bind-icon" in icon.attrs
        
        icon_binding = icon.attrs.get("data-bind-icon")
        assert "$isDark" in icon_binding
        assert "?" in icon_binding  # Ternary operator
        
        
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
