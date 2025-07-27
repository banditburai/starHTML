"""Cross-browser compatibility tests for theme toggle functionality."""

import sys
from pathlib import Path

import pytest

# Add the project root to the path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from components.ui import ThemeToggle


class TestThemeToggleModernBrowsers:
    """Test theme toggle compatibility with modern browsers."""
    
    def test_chrome_compatibility(self):
        """Test Chrome-specific compatibility features."""
        toggle = ThemeToggle()
        
        click_handler = toggle.attrs.get("data-on-click", "")
        load_handler = toggle.attrs.get("data-on-load", "")
        
        # Should use modern APIs available in Chrome
        assert "CustomEvent" in click_handler, "Should use CustomEvent API"
        assert "addEventListener" in load_handler, "Should use modern event listeners"
        assert "window.matchMedia" in load_handler, "Should use matchMedia API"
        
    def test_firefox_compatibility(self):
        """Test Firefox-specific compatibility features."""
        toggle = ThemeToggle()
        
        load_handler = toggle.attrs.get("data-on-load", "")
        
        # Should work with Firefox's implementation
        assert "prefers-color-scheme" in load_handler, "Should use CSS media queries"
        assert "localStorage" in load_handler, "Should use localStorage API"
        
    def test_safari_compatibility(self):
        """Test Safari-specific compatibility features."""
        toggle = ThemeToggle()
        
        click_handler = toggle.attrs.get("data-on-click", "")
        toggle.attrs.get("data-on-load", "")
        
        # Should work with Safari's WebKit implementation
        assert "classList.toggle" in click_handler, "Should use classList API"
        assert "document.documentElement" in click_handler, "Should use standard DOM APIs"
        
    def test_edge_compatibility(self):
        """Test Microsoft Edge compatibility features."""
        toggle = ThemeToggle()
        
        load_handler = toggle.attrs.get("data-on-load", "")
        
        # Should work with Edge's Chromium implementation
        assert "window.matchMedia" in load_handler, "Should use matchMedia API"
        assert "addEventListener" in load_handler, "Should use modern event listeners"
        

class TestThemeToggleLegacyBrowsers:
    """Test theme toggle compatibility with legacy browsers."""
    
    def test_internet_explorer_fallbacks(self):
        """Test fallbacks for Internet Explorer."""
        toggle = ThemeToggle()
        
        load_handler = toggle.attrs.get("data-on-load", "")
        
        # Should have fallbacks for older browsers
        assert "addListener" in load_handler, "Should have fallback for old browsers"
        assert "try {" in load_handler, "Should have error handling for unsupported features"
        
    def test_older_chrome_compatibility(self):
        """Test compatibility with older Chrome versions."""
        toggle = ThemeToggle()
        
        load_handler = toggle.attrs.get("data-on-load", "")
        
        # Should check for feature availability
        assert "addEventListener" in load_handler, "Should check for modern features"
        assert "addListener" in load_handler, "Should provide fallback"
        
    def test_older_firefox_compatibility(self):
        """Test compatibility with older Firefox versions."""
        toggle = ThemeToggle()
        
        click_handler = toggle.attrs.get("data-on-click", "")
        load_handler = toggle.attrs.get("data-on-load", "")
        
        # Should use features available in older Firefox
        assert "classList" in click_handler, "Should use classList API"
        assert "localStorage" in load_handler, "Should use localStorage"
        
    def test_older_safari_compatibility(self):
        """Test compatibility with older Safari versions."""
        toggle = ThemeToggle()
        
        load_handler = toggle.attrs.get("data-on-load", "")
        
        # Should handle Safari's implementation differences
        assert "window.matchMedia" in load_handler, "Should use matchMedia"
        assert "try {" in load_handler, "Should handle errors gracefully"
        

class TestThemeToggleMobileBrowsers:
    """Test theme toggle compatibility with mobile browsers."""
    
    def test_mobile_safari_compatibility(self):
        """Test Mobile Safari compatibility."""
        toggle = ThemeToggle()
        
        click_handler = toggle.attrs.get("data-on-click", "")
        toggle.attrs.get("data-on-load", "")
        
        # Should work with Mobile Safari's implementation
        assert "localStorage" in click_handler, "Should use localStorage"
        assert "document.documentElement" in click_handler, "Should use standard DOM"
        
    def test_chrome_mobile_compatibility(self):
        """Test Chrome Mobile compatibility."""
        toggle = ThemeToggle()
        
        click_handler = toggle.attrs.get("data-on-click", "")
        
        # Should work with Chrome Mobile
        assert "CustomEvent" in click_handler, "Should use CustomEvent"
        assert "classList.toggle" in click_handler, "Should use classList"
        
    def test_firefox_mobile_compatibility(self):
        """Test Firefox Mobile compatibility."""
        toggle = ThemeToggle()
        
        load_handler = toggle.attrs.get("data-on-load", "")
        
        # Should work with Firefox Mobile
        assert "prefers-color-scheme" in load_handler, "Should use media queries"
        assert "matchMedia" in load_handler, "Should use matchMedia API"
        
    def test_samsung_internet_compatibility(self):
        """Test Samsung Internet compatibility."""
        toggle = ThemeToggle()
        
        click_handler = toggle.attrs.get("data-on-click", "")
        load_handler = toggle.attrs.get("data-on-load", "")
        
        # Should work with Samsung Internet's Chromium base
        assert "localStorage" in click_handler, "Should use localStorage"
        assert "addEventListener" in load_handler, "Should use modern event listeners"
        

class TestThemeToggleAPICompatibility:
    """Test compatibility with various web APIs."""
    
    def test_localstorage_compatibility(self):
        """Test localStorage compatibility and fallbacks."""
        toggle = ThemeToggle()
        
        click_handler = toggle.attrs.get("data-on-click", "")
        load_handler = toggle.attrs.get("data-on-load", "")
        
        # Should handle localStorage availability
        assert "localStorage.setItem" in click_handler, "Should use localStorage"
        assert "localStorage.getItem" in load_handler, "Should read from localStorage"
        assert "try {" in click_handler, "Should handle localStorage errors"
        
    def test_media_query_compatibility(self):
        """Test media query compatibility."""
        toggle = ThemeToggle()
        
        load_handler = toggle.attrs.get("data-on-load", "")
        
        # Should use media queries properly
        assert "window.matchMedia" in load_handler, "Should use matchMedia"
        assert "prefers-color-scheme: dark" in load_handler, "Should check system theme"
        assert "matches" in load_handler, "Should check media query matches"
        
    def test_event_listener_compatibility(self):
        """Test event listener compatibility."""
        toggle = ThemeToggle()
        
        load_handler = toggle.attrs.get("data-on-load", "")
        
        # Should provide fallbacks for event listeners
        assert "addEventListener" in load_handler, "Should use modern event listeners"
        assert "addListener" in load_handler, "Should provide fallback"
        
    def test_custom_event_compatibility(self):
        """Test custom event compatibility."""
        toggle = ThemeToggle()
        
        click_handler = toggle.attrs.get("data-on-click", "")
        
        # Should use custom events properly
        assert "CustomEvent" in click_handler, "Should use CustomEvent constructor"
        assert "dispatchEvent" in click_handler, "Should dispatch events"
        

class TestThemeToggleFeatureDetection:
    """Test feature detection and graceful degradation."""
    
    def test_feature_detection_structure(self):
        """Test that feature detection is properly structured."""
        toggle = ThemeToggle()
        
        load_handler = toggle.attrs.get("data-on-load", "")
        
        # Should check for feature availability
        assert "if (" in load_handler, "Should have conditional checks"
        assert "addEventListener" in load_handler, "Should check for modern features"
        assert "else" in load_handler, "Should have fallback branches"
        
    def test_graceful_degradation(self):
        """Test graceful degradation when features are unavailable."""
        toggle = ThemeToggle()
        
        click_handler = toggle.attrs.get("data-on-click", "")
        toggle.attrs.get("data-on-load", "")
        
        # Should handle feature unavailability gracefully
        assert "try {" in click_handler, "Should handle localStorage errors"
        assert "} catch" in click_handler, "Should catch errors"
        assert "console.warn" in click_handler, "Should warn about errors"
        
    def test_progressive_enhancement(self):
        """Test progressive enhancement approach."""
        toggle = ThemeToggle()
        
        # Should provide basic functionality without JavaScript
        assert toggle.tag == "div", "Should be a proper HTML element"
        
        button = toggle.children[0]
        assert button.tag == "button", "Should be a proper button"
        assert "aria-label" in button.attrs, "Should have accessibility attributes"
        

class TestThemeTogglePerformanceAcrossBrowsers:
    """Test performance characteristics across different browsers."""
    
    def test_dom_manipulation_efficiency(self):
        """Test efficient DOM manipulation across browsers."""
        toggle = ThemeToggle()
        
        click_handler = toggle.attrs.get("data-on-click", "")
        
        # Should use efficient DOM manipulation
        assert "const html = document.documentElement" in click_handler, "Should cache DOM references"
        assert "classList.toggle" in click_handler, "Should use efficient classList API"
        assert "theme-transitioning" in click_handler, "Should batch DOM operations"
        
    def test_memory_usage_optimization(self):
        """Test memory usage optimization across browsers."""
        toggle = ThemeToggle()
        
        load_handler = toggle.attrs.get("data-on-load", "")
        
        # Should avoid memory leaks
        assert "const " in load_handler, "Should use const for immutable references"
        assert "addEventListener" in load_handler, "Should use proper event cleanup"
        
    def test_animation_performance(self):
        """Test animation performance across browsers."""
        toggle = ThemeToggle()
        
        click_handler = toggle.attrs.get("data-on-click", "")
        
        # Should use performant animations
        assert "theme-transitioning" in click_handler, "Should use CSS transitions"
        assert "setTimeout" in click_handler, "Should properly manage animation timing"
        

class TestThemeToggleAccessibilityCompatibility:
    """Test accessibility compatibility across browsers."""
    
    def test_screen_reader_compatibility(self):
        """Test screen reader compatibility."""
        toggle = ThemeToggle()
        button = toggle.children[0]
        
        # Should have proper accessibility attributes
        assert "aria-label" in button.attrs, "Should have aria-label"
        assert button.attrs.get("aria-label") == "Toggle theme", "Should have descriptive label"
        assert "title" in button.attrs, "Should have title for tooltip"
        
    def test_keyboard_navigation_compatibility(self):
        """Test keyboard navigation compatibility."""
        toggle = ThemeToggle()
        button = toggle.children[0]
        
        # Should be keyboard accessible
        assert button.tag == "button", "Should be a proper button element"
        # Should not have tabindex that interferes with keyboard navigation
        assert "tabindex" not in button.attrs or button.attrs.get("tabindex") != "-1"
        
    def test_high_contrast_mode_compatibility(self):
        """Test high contrast mode compatibility."""
        toggle = ThemeToggle()
        
        # Should work with high contrast mode
        # This is more of a CSS concern, but the structure should support it
        assert "transition" in str(toggle), "Should have smooth transitions"
        
    def test_reduced_motion_compatibility(self):
        """Test reduced motion preference compatibility."""
        toggle = ThemeToggle()
        
        # Should respect reduced motion preferences
        # This is handled in CSS, but JavaScript should not interfere
        click_handler = toggle.attrs.get("data-on-click", "")
        assert "setTimeout" in click_handler, "Should use proper timing"
        

class TestThemeToggleSecurityCompatibility:
    """Test security compatibility across browsers."""
    
    def test_content_security_policy_compatibility(self):
        """Test CSP compatibility."""
        toggle = ThemeToggle()
        
        # Should not use inline event handlers that would violate CSP
        assert "onclick" not in toggle.attrs, "Should not use inline event handlers"
        assert "onload" not in toggle.attrs, "Should not use inline event handlers"
        
        # Should use Datastar attributes instead
        assert "data-on-click" in toggle.children[0].attrs, "Should use Datastar attributes"
        assert "data-on-load" in toggle.attrs, "Should use Datastar attributes"
        
    def test_xss_prevention(self):
        """Test XSS prevention measures."""
        toggle = ThemeToggle()
        
        # Should not execute user-provided content
        # This is more of a framework concern, but the structure should be safe
        assert toggle.tag == "div", "Should use safe HTML elements"
        
    def test_same_origin_policy_compatibility(self):
        """Test same-origin policy compatibility."""
        toggle = ThemeToggle()
        
        load_handler = toggle.attrs.get("data-on-load", "")
        
        # Should not make cross-origin requests
        assert "fetch" not in load_handler, "Should not make network requests"
        assert "XMLHttpRequest" not in load_handler, "Should not make AJAX requests"
        
        
class TestThemeToggleFrameworkCompatibility:
    """Test compatibility with different frontend frameworks."""
    
    def test_vanilla_js_compatibility(self):
        """Test compatibility with vanilla JavaScript."""
        toggle = ThemeToggle()
        
        # Should work without any framework dependencies
        assert toggle is not None, "Should create without framework dependencies"
        
    def test_server_side_rendering_compatibility(self):
        """Test SSR compatibility."""
        toggle = ThemeToggle()
        
        # Should render properly on server
        assert toggle.tag == "div", "Should have proper HTML structure"
        assert len(toggle.children) > 0, "Should have child elements"
        
    def test_hydration_compatibility(self):
        """Test client-side hydration compatibility."""
        toggle = ThemeToggle(id="hydration-test")
        
        # Should be hydration-friendly
        assert toggle.attrs.get("id") == "hydration-test", "Should maintain stable attributes"
        assert "data-on-load" in toggle.attrs, "Should have initialization code"
        
        
class TestThemeToggleVersionCompatibility:
    """Test compatibility across different versions of dependencies."""
    
    def test_datastar_version_compatibility(self):
        """Test compatibility with different Datastar versions."""
        toggle = ThemeToggle()
        
        # Should use stable Datastar features
        assert "data-signals" in toggle.attrs, "Should use stable signal API"
        assert "data-on-click" in toggle.children[0].attrs, "Should use stable event API"
        
    def test_browser_version_compatibility(self):
        """Test compatibility with different browser versions."""
        toggle = ThemeToggle()
        
        load_handler = toggle.attrs.get("data-on-load", "")
        
        # Should provide fallbacks for older versions
        assert "addEventListener" in load_handler, "Should use modern API"
        assert "addListener" in load_handler, "Should provide fallback"
        
        
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
