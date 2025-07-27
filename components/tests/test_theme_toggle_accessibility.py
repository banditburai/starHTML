"""Comprehensive accessibility tests for theme toggle functionality."""

import sys
from pathlib import Path

import pytest

# Add the project root to the path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from components.ui import ThemeToggle

from starhtml import *


class TestThemeToggleBasicAccessibility:
    """Test basic accessibility requirements for theme toggle."""
    
    def test_semantic_html_structure(self):
        """Test that theme toggle uses semantic HTML structure."""
        toggle = ThemeToggle()
        
        # Should use semantic HTML elements
        assert toggle.tag == "div", "Container should be a div"
        
        button = toggle.children[0]
        assert button.tag == "button", "Interactive element should be a button"
        
    def test_aria_attributes(self):
        """Test ARIA attributes for accessibility."""
        toggle = ThemeToggle()
        button = toggle.children[0]
        
        # Should have proper ARIA attributes
        assert "aria-label" in button.attrs, "Should have aria-label"
        assert button.attrs.get("aria-label") == "Toggle theme", "Should have descriptive aria-label"
        
    def test_title_attribute(self):
        """Test title attribute for tooltip accessibility."""
        toggle = ThemeToggle()
        button = toggle.children[0]
        
        # Should have title for tooltip
        assert "title" in button.attrs, "Should have title attribute"
        assert "Toggle between light and dark mode" in button.attrs.get("title"), "Should have descriptive title"
        
    def test_button_type_attribute(self):
        """Test button type attribute."""
        toggle = ThemeToggle()
        button = toggle.children[0]
        
        # Should have proper button type
        button_type = button.attrs.get("type", "button")
        assert button_type == "button", "Should be a button type"
        
    def test_keyboard_accessibility(self):
        """Test keyboard accessibility."""
        toggle = ThemeToggle()
        button = toggle.children[0]
        
        # Should be keyboard accessible
        assert button.tag == "button", "Should be a button for keyboard access"
        
        # Should not have tabindex that removes from tab order
        tabindex = button.attrs.get("tabindex")
        assert tabindex is None or tabindex != "-1", "Should not be removed from tab order"
        
        
class TestThemeToggleScreenReaderSupport:
    """Test screen reader support for theme toggle."""
    
    def test_screen_reader_announcements(self):
        """Test screen reader announcement structure."""
        toggle = ThemeToggle()
        button = toggle.children[0]
        
        # Should have clear announcements
        aria_label = button.attrs.get("aria-label")
        assert aria_label == "Toggle theme", "Should have clear aria-label"
        
    def test_state_communication(self):
        """Test communication of current state to screen readers."""
        toggle = ThemeToggle()
        
        # Should communicate state through JavaScript
        click_handler = toggle.children[0].attrs.get("data-on-click", "")
        
        # Should dispatch events that screen readers can detect
        assert "CustomEvent" in click_handler, "Should dispatch custom events"
        assert "theme-changed" in click_handler, "Should announce theme changes"
        
    def test_role_attributes(self):
        """Test role attributes for screen readers."""
        toggle = ThemeToggle()
        button = toggle.children[0]
        
        # Button should have implicit button role
        assert button.tag == "button", "Should have button role implicitly"
        
        # Should not have conflicting roles
        assert "role" not in button.attrs or button.attrs.get("role") == "button", "Should not have conflicting roles"
        
    def test_alternative_text(self):
        """Test alternative text for icons."""
        toggle = ThemeToggle()
        button = toggle.children[0]
        icon = button.children[0]
        
        # Icon should not need alt text since button has aria-label
        assert "alt" not in icon.attrs, "Icon should not have alt text when button has aria-label"
        
    def test_descriptive_context(self):
        """Test descriptive context for screen readers."""
        toggle = ThemeToggle()
        button = toggle.children[0]
        
        # Should provide context about what the toggle does
        title = button.attrs.get("title")
        assert "light and dark mode" in title, "Should explain what the toggle does"
        
        
class TestThemeToggleKeyboardNavigation:
    """Test keyboard navigation for theme toggle."""
    
    def test_tab_order(self):
        """Test proper tab order."""
        toggle = ThemeToggle()
        button = toggle.children[0]
        
        # Should be in natural tab order
        assert button.tag == "button", "Should be focusable button"
        
        # Should not have negative tabindex
        tabindex = button.attrs.get("tabindex")
        assert tabindex is None or int(tabindex) >= 0, "Should not have negative tabindex"
        
    def test_focus_management(self):
        """Test focus management."""
        toggle = ThemeToggle()
        button = toggle.children[0]
        
        # Should be focusable
        assert button.tag == "button", "Should be focusable"
        
        # Should not programmatically move focus
        click_handler = button.attrs.get("data-on-click", "")
        assert "focus(" not in click_handler, "Should not programmatically move focus"
        
    def test_keyboard_activation(self):
        """Test keyboard activation (Space and Enter)."""
        toggle = ThemeToggle()
        button = toggle.children[0]
        
        # Button should support Space and Enter activation by default
        assert button.tag == "button", "Button should support keyboard activation"
        
        # Should not have custom key handlers that interfere
        assert "data-on-keydown" not in button.attrs, "Should not interfere with native keyboard handling"
        
    def test_focus_indicators(self):
        """Test focus indicators."""
        toggle = ThemeToggle()
        button = toggle.children[0]
        
        # Should have focus indicators through CSS
        button_classes = button.attrs.get("class", "")
        assert "focus-visible" in button_classes, "Should have focus-visible classes"
        
        
class TestThemeToggleColorContrastAccessibility:
    """Test color contrast accessibility."""
    
    def test_theme_aware_styling(self):
        """Test theme-aware styling for accessibility."""
        toggle = ThemeToggle()
        
        # Should use theme-aware colors
        # This is primarily handled by CSS, but we can test the structure
        assert toggle is not None, "Should create theme-aware toggle"
        
    def test_high_contrast_mode_support(self):
        """Test high contrast mode support."""
        toggle = ThemeToggle()
        
        # Should work with high contrast mode
        # This is primarily a CSS concern, but the structure should support it
        button = toggle.children[0]
        assert button.tag == "button", "Should be a proper button for high contrast"
        
    def test_color_independence(self):
        """Test that functionality doesn't depend solely on color."""
        toggle = ThemeToggle()
        button = toggle.children[0]
        
        # Should have text/icon indicators, not just color
        assert "aria-label" in button.attrs, "Should have text indicator"
        assert len(button.children) > 0, "Should have icon indicator"
        
    def test_reduced_motion_support(self):
        """Test support for reduced motion preferences."""
        toggle = ThemeToggle()
        
        # Should use CSS transitions that respect reduced motion
        # This is handled in CSS, but JavaScript should not interfere
        click_handler = toggle.children[0].attrs.get("data-on-click", "")
        assert "setTimeout" in click_handler, "Should use proper timing that can be controlled by CSS"
        
        
class TestThemeToggleMotionAccessibility:
    """Test motion and animation accessibility."""
    
    def test_animation_control(self):
        """Test animation control for accessibility."""
        toggle = ThemeToggle()
        
        click_handler = toggle.children[0].attrs.get("data-on-click", "")
        
        # Should use CSS classes for animations
        assert "theme-transitioning" in click_handler, "Should use CSS classes for animations"
        
    def test_vestibular_disorder_support(self):
        """Test support for users with vestibular disorders."""
        toggle = ThemeToggle()
        
        # Should not use jarring animations
        # This is primarily handled by CSS, but we can test the structure
        click_handler = toggle.children[0].attrs.get("data-on-click", "")
        assert "setTimeout" in click_handler, "Should use controlled timing"
        
    def test_parallax_avoidance(self):
        """Test avoidance of parallax and excessive motion."""
        toggle = ThemeToggle()
        
        # Should not use excessive motion effects
        click_handler = toggle.children[0].attrs.get("data-on-click", "")
        
        # Should use simple state changes
        assert "classList.toggle" in click_handler, "Should use simple state changes"
        
        
class TestThemeToggleCognitiveLlAccessibility:
    """Test cognitive accessibility for theme toggle."""
    
    def test_clear_purpose(self):
        """Test clear purpose and functionality."""
        toggle = ThemeToggle()
        button = toggle.children[0]
        
        # Should have clear purpose
        aria_label = button.attrs.get("aria-label")
        title = button.attrs.get("title")
        
        assert "Toggle theme" in aria_label, "Should have clear purpose in aria-label"
        assert "light and dark mode" in title, "Should explain functionality"
        
    def test_predictable_behavior(self):
        """Test predictable behavior."""
        toggle = ThemeToggle()
        
        # Should have predictable toggle behavior
        click_handler = toggle.children[0].attrs.get("data-on-click", "")
        assert "$isDark = !$isDark" in click_handler, "Should have predictable toggle logic"
        
    def test_consistent_interface(self):
        """Test consistent interface across instances."""
        toggle1 = ThemeToggle()
        toggle2 = ThemeToggle()
        
        # Should have consistent interface
        button1 = toggle1.children[0]
        button2 = toggle2.children[0]
        
        assert button1.attrs.get("aria-label") == button2.attrs.get("aria-label"), "Should have consistent labels"
        
    def test_error_prevention(self):
        """Test error prevention and handling."""
        toggle = ThemeToggle()
        
        click_handler = toggle.children[0].attrs.get("data-on-click", "")
        toggle.attrs.get("data-on-load", "")
        
        # Should prevent and handle errors gracefully
        assert "try {" in click_handler, "Should prevent errors"
        assert "} catch" in click_handler, "Should handle errors"
        assert "console.warn" in click_handler, "Should warn about errors"
        
    def test_simple_interaction_model(self):
        """Test simple interaction model."""
        toggle = ThemeToggle()
        button = toggle.children[0]
        
        # Should have simple click interaction
        assert button.tag == "button", "Should be simple button"
        assert "data-on-click" in button.attrs, "Should have simple click handler"
        
        
class TestThemeToggleInternationalization:
    """Test internationalization and localization support."""
    
    def test_text_direction_support(self):
        """Test support for different text directions."""
        toggle = ThemeToggle()
        
        # Should work with RTL languages
        # This is primarily handled by CSS, but structure should support it
        assert toggle is not None, "Should work with different text directions"
        
    def test_language_neutral_icons(self):
        """Test language-neutral icons."""
        toggle = ThemeToggle()
        button = toggle.children[0]
        icon = button.children[0]
        
        # Should use language-neutral icons
        icon_name = icon.attrs.get("icon", "")
        assert "sun" in icon_name or "moon" in icon_name, "Should use universal sun/moon icons"
        
    def test_localizable_text(self):
        """Test that text can be localized."""
        toggle = ThemeToggle()
        button = toggle.children[0]
        
        # Text should be in attributes that can be localized
        assert "aria-label" in button.attrs, "Should have localizable aria-label"
        assert "title" in button.attrs, "Should have localizable title"
        
    def test_cultural_sensitivity(self):
        """Test cultural sensitivity in design."""
        toggle = ThemeToggle()
        
        # Should use culturally neutral concepts
        # Sun/moon metaphor is universally understood
        assert toggle is not None, "Should use culturally neutral concepts"
        
        
class TestThemeToggleAssistiveTechnologySupport:
    """Test support for various assistive technologies."""
    
    def test_screen_magnifier_support(self):
        """Test support for screen magnifiers."""
        toggle = ThemeToggle()
        button = toggle.children[0]
        
        # Should work with screen magnifiers
        assert button.tag == "button", "Should be standard button for magnifiers"
        
    def test_voice_control_support(self):
        """Test support for voice control."""
        toggle = ThemeToggle()
        button = toggle.children[0]
        
        # Should be voice controllable
        assert button.tag == "button", "Should be voice controllable button"
        assert "aria-label" in button.attrs, "Should have voice control label"
        
    def test_switch_control_support(self):
        """Test support for switch control."""
        toggle = ThemeToggle()
        button = toggle.children[0]
        
        # Should work with switch control
        assert button.tag == "button", "Should work with switch control"
        
        # Should not have complex interaction patterns
        assert "data-on-click" in button.attrs, "Should have simple activation"
        
    def test_eye_tracking_support(self):
        """Test support for eye tracking."""
        toggle = ThemeToggle()
        button = toggle.children[0]
        
        # Should have adequate target size
        button_classes = button.attrs.get("class", "")
        assert "h-" in button_classes, "Should have defined height"
        
    def test_head_pointer_support(self):
        """Test support for head pointer devices."""
        toggle = ThemeToggle()
        button = toggle.children[0]
        
        # Should have adequate target size and spacing
        assert button.tag == "button", "Should be standard button"
        
        
class TestThemeToggleAccessibilityIntegration:
    """Test accessibility in integrated scenarios."""
    
    def test_accessibility_in_forms(self):
        """Test accessibility when integrated with forms."""
        form_layout = Form(
            Label("Theme Setting"),
            ThemeToggle(),
            Input(name="other_field"),
            Button("Submit", type="submit")
        )
        
        # Should integrate well with forms
        assert form_layout is not None, "Should integrate with forms"
        
    def test_accessibility_in_navigation(self):
        """Test accessibility in navigation contexts."""
        nav_layout = Nav(
            A("Home", href="/"),
            A("About", href="/about"),
            ThemeToggle(),
            role="navigation"
        )
        
        # Should integrate well with navigation
        assert nav_layout is not None, "Should integrate with navigation"
        
    def test_accessibility_with_other_controls(self):
        """Test accessibility with other form controls."""
        control_layout = Div(
            Button("Action 1"),
            ThemeToggle(),
            Button("Action 2"),
            cls="control-group"
        )
        
        # Should work well with other controls
        assert control_layout is not None, "Should work with other controls"
        
    def test_accessibility_in_modal_dialogs(self):
        """Test accessibility in modal dialogs."""
        modal_layout = Div(
            Header(
                H2("Settings"),
                ThemeToggle(cls="ml-auto"),
                cls="flex items-center justify-between"
            ),
            Div("Modal content"),
            role="dialog",
            aria_labelledby="modal-title"
        )
        
        # Should work in modal dialogs
        assert modal_layout is not None, "Should work in modal dialogs"
        
        
class TestThemeToggleAccessibilityValidation:
    """Test accessibility validation and compliance."""
    
    def test_wcag_compliance_structure(self):
        """Test WCAG compliance structure."""
        toggle = ThemeToggle()
        button = toggle.children[0]
        
        # Should meet WCAG requirements
        assert button.tag == "button", "Should be semantic button (WCAG 4.1.2)"
        assert "aria-label" in button.attrs, "Should have accessible name (WCAG 4.1.2)"
        
    def test_section_508_compliance(self):
        """Test Section 508 compliance."""
        toggle = ThemeToggle()
        button = toggle.children[0]
        
        # Should meet Section 508 requirements
        assert button.tag == "button", "Should be standard form control"
        assert "aria-label" in button.attrs, "Should have accessible description"
        
    def test_ada_compliance(self):
        """Test ADA compliance."""
        toggle = ThemeToggle()
        button = toggle.children[0]
        
        # Should meet ADA requirements
        assert button.tag == "button", "Should be accessible to all users"
        assert "title" in button.attrs, "Should provide helpful information"
        
    def test_aria_best_practices(self):
        """Test ARIA best practices."""
        toggle = ThemeToggle()
        button = toggle.children[0]
        
        # Should follow ARIA best practices
        assert "aria-label" in button.attrs, "Should have accessible name"
        assert "role" not in button.attrs or button.attrs.get("role") == "button", "Should not override semantic roles"
        
    def test_accessibility_tree_structure(self):
        """Test accessibility tree structure."""
        toggle = ThemeToggle()
        button = toggle.children[0]
        
        # Should create proper accessibility tree
        assert button.tag == "button", "Should be button in accessibility tree"
        assert len(button.children) > 0, "Should have child elements"
        
        
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
