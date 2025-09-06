"""Test Tailwind opacity handling with dictionary syntax for StarHTML/Datastar."""

import json

from starhtml import Div
from starhtml.datastar import ds_class


class TestTailwindOpacityHandling:
    """Test dictionary syntax for Tailwind opacity classes with forward slashes."""

    def test_ds_class_with_slash_uses_dictionary(self):
        """Test that ds_class uses dictionary syntax when slashes are present."""
        result = ds_class(**{"border-primary/60": "$isPrimary", "bg-accent/30": "$isActive"})

        # Should use dictionary syntax to preserve slashes
        expected_dict = {"border-primary/60": "$isPrimary", "bg-accent/30": "$isActive"}

        assert "data-class" in result.attrs
        assert json.loads(str(result.attrs["data-class"])) == expected_dict

    def test_ds_class_without_slash_uses_attributes(self):
        """Test that ds_class uses regular attributes when no slashes."""
        result = ds_class(**{"text_blue_500": "$isBlue", "hover_bg_gray_100": "$isHover"})

        # Should use regular attribute syntax
        expected = {"data-class-text-blue-500": "$isBlue", "data-class-hover-bg-gray-100": "$isHover"}

        assert result.attrs == expected

    def test_mixed_classes_with_and_without_slashes(self):
        """Test mixed classes triggers dictionary mode."""
        result = ds_class(**{"border-primary/60": "$isPrimary", "text_blue_500": "$isBlue", "bg-white/90": "$isLight"})

        # Should use dictionary for all when any have slashes
        expected_dict = {"border-primary/60": "$isPrimary", "text-blue-500": "$isBlue", "bg-white/90": "$isLight"}

        assert "data-class" in result.attrs
        assert json.loads(str(result.attrs["data-class"])) == expected_dict

    def test_other_ds_functions_with_slashes(self):
        """Test that other ds_* functions created with _make_attr_func handle slashes."""
        from starhtml.datastar import ds_attr, ds_style

        # Test ds_style with slash-containing keys
        style_result = ds_style(**{"width/special": "$widthValue"})
        assert "data-style" in style_result.attrs
        assert json.loads(str(style_result.attrs["data-style"])) == {"width/special": "$widthValue"}

        # Test ds_attr with slash-containing keys
        attr_result = ds_attr(**{"href/special": "$linkValue"})
        assert "data-attr" in attr_result.attrs
        assert json.loads(str(attr_result.attrs["data-attr"])) == {"href/special": "$linkValue"}

    def test_html_generation_with_opacity_classes(self):
        """Test HTML generation with Tailwind opacity classes."""
        element = Div(
            "Opacity example",
            **ds_class(
                **{"border-primary/60": "$isPrimary", "bg-accent/30": "$isActive", "p_4": True, "rounded_lg": True}
            ),
        )

        html_str = str(element)

        # Check that dictionary syntax is in HTML
        assert "data-class=" in html_str
        assert "border-primary/60" in html_str
        assert "bg-accent/30" in html_str

    def test_boolean_values_with_slashes(self):
        """Test boolean values work with slash-containing keys."""
        result = ds_class(**{"bg-black/50": True, "hover:bg-white/10": False})

        expected_dict = {
            "bg-black/50": "true",  # Booleans are normalized to strings
            "hover:bg-white/10": "false",
        }

        assert "data-class" in result.attrs
        assert json.loads(str(result.attrs["data-class"])) == expected_dict

    def test_single_quotes_converted_to_double_quotes(self):
        """Test that single quotes in JS expressions are converted to double quotes to avoid HTML escaping."""
        result = ds_class(**{"border-primary/60": "$plan === 'free'", "text-red/50": "$status !== 'active'"})

        # Extract the JSON
        json_str = str(result.attrs["data-class"])
        parsed = json.loads(json_str)

        # Single quotes should be converted to double quotes
        assert parsed["border-primary/60"] == '$plan === "free"'
        assert parsed["text-red/50"] == '$status !== "active"'

    def test_html_output_has_parseable_json(self):
        """Test that the JSON in HTML output is parseable by JavaScript."""
        result = ds_class(**{"border-primary/60": "$plan === 'premium'", "bg-accent/30": "$user.role === 'admin'"})

        # Generate HTML
        element = Div("Test", **result.attrs)
        html_str = str(element)

        # Extract JSON from HTML (simulating browser behavior)
        import re

        match = re.search(r"data-class=(['\"])(.*?)\1", html_str)
        assert match is not None

        extracted_json = match.group(2)

        # Should parse without HTML entity issues
        parsed = json.loads(extracted_json)
        assert "border-primary/60" in parsed
        assert "bg-accent/30" in parsed

        # Should not contain HTML entities
        assert "&#39;" not in extracted_json
        assert "&quot;" not in extracted_json


if __name__ == "__main__":
    import pytest

    pytest.main([__file__, "-v"])
