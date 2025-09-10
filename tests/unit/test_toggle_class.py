"""Tests for the toggle_class helper function."""

from starhtml.datastar import ds_attr, if_, toggle_class
from starhtml.tags import Button, Div


class TestToggleClass:
    """Test suite for toggle_class helper."""

    def test_simple_toggle(self):
        """Test basic toggle between two class sets."""
        result = toggle_class("$active", "bg-blue-500 text-white", "bg-gray-300 text-black")

        assert "data-attr-class" in result.attrs
        expected = '$active ? "bg-blue-500 text-white" : "bg-gray-300 text-black"'
        assert result.attrs["data-attr-class"] == expected

    def test_with_base_classes(self):
        """Test toggle with base classes that always apply."""
        result = toggle_class("$expanded", "scale-105 shadow-lg", "scale-100", base="transition-all duration-200 p-4")

        expected = '$expanded ? "transition-all duration-200 p-4 scale-105 shadow-lg" : "transition-all duration-200 p-4 scale-100"'
        assert result.attrs["data-attr-class"] == expected

    def test_complex_condition(self):
        """Test with complex condition expression."""
        result = toggle_class("$currentStep >= 2", "bg-green-500 text-white", "bg-gray-300 text-gray-600")

        expected = '$currentStep >= 2 ? "bg-green-500 text-white" : "bg-gray-300 text-gray-600"'
        assert result.attrs["data-attr-class"] == expected

    def test_empty_truthy(self):
        """Test with empty truthy classes."""
        result = toggle_class("$hidden", "", "block", base="p-4")

        expected = '$hidden ? "p-4" : "p-4 block"'
        assert result.attrs["data-attr-class"] == expected

    def test_empty_falsy(self):
        """Test with empty falsy classes."""
        result = toggle_class("$visible", "block", "", base="p-4")

        expected = '$visible ? "p-4 block" : "p-4"'
        assert result.attrs["data-attr-class"] == expected

    def test_only_base_classes(self):
        """Test with only base classes, no conditional."""
        result = toggle_class("$any", "", "", base="always-present")

        expected = '$any ? "always-present" : "always-present"'
        assert result.attrs["data-attr-class"] == expected

    def test_integration_with_element(self):
        """Test that toggle_class integrates properly with elements."""
        button = Button("Click me", **toggle_class("$active", "bg-blue-500 text-white", "bg-gray-300 text-black"))

        html = str(button)
        assert "data-attr-class=" in html
        assert "bg-blue-500 text-white" in html
        assert "bg-gray-300 text-black" in html

    def test_html_output(self):
        """Test the actual HTML output."""
        div = Div(
            "Content",
            **toggle_class(
                "$isOpen", "max-h-96 overflow-visible", "max-h-0 overflow-hidden", base="transition-all duration-300"
            ),
        )

        html = str(div)
        expected_attr = 'data-attr-class=\'$isOpen ? "transition-all duration-300 max-h-96 overflow-visible" : "transition-all duration-300 max-h-0 overflow-hidden"\''
        assert expected_attr in html

    def test_with_tailwind_modifiers(self):
        """Test with Tailwind modifier classes."""
        result = toggle_class(
            "$darkMode", "dark:bg-gray-900 dark:text-white hover:bg-gray-800", "bg-white text-gray-900 hover:bg-gray-50"
        )

        assert "dark:bg-gray-900" in result.attrs["data-attr-class"]
        assert "hover:bg-gray-50" in result.attrs["data-attr-class"]

    def test_comparison_with_ds_attr(self):
        """Test that toggle_class produces similar result as ds_attr with if_()."""
        # Using toggle_class
        toggle_result = toggle_class("$active", "bg-blue-500", "bg-gray-300")

        # Using ds_attr with if_
        attr_result = ds_attr(class_=if_("$active", "bg-blue-500", "bg-gray-300"))

        # They create different attribute names due to HTML underscore conversion issue
        # toggle_class uses data-attr-class (no trailing dash) to avoid HTML conversion issues
        # ds_attr creates data-attr-class- (with trailing dash)
        assert "data-attr-class" in toggle_result.attrs
        assert "data-attr-class-" in attr_result.attrs
        # But the expression values should be the same
        assert toggle_result.attrs["data-attr-class"] == attr_result.attrs["data-attr-class-"]

    def test_multiple_conditions(self):
        """Test with equality and comparison conditions."""
        result = toggle_class("$status === 'success'", "border-green-500 bg-green-50", "border-gray-300 bg-white")

        assert "$status === 'success'" in result.attrs["data-attr-class"]
        assert "border-green-500 bg-green-50" in result.attrs["data-attr-class"]

    def test_whitespace_handling(self):
        """Test that whitespace is preserved as provided."""
        result = toggle_class("$active", "  bg-blue-500   text-white  ", "   bg-gray-300   ", base="  p-4  rounded  ")

        # Whitespace is preserved as given (with one space between base and additional)
        expected = '$active ? "p-4  rounded     bg-blue-500   text-white" : "p-4  rounded      bg-gray-300"'
        assert result.attrs["data-attr-class"] == expected

    def test_real_world_step_component(self):
        """Test a real-world step component example."""
        result = toggle_class(
            "$currentStep >= 1",
            "bg-blue-500 text-white border-blue-600 shadow-lg",
            "bg-gray-300 text-gray-600 border-gray-300",
            base="flex items-center gap-3 p-4 rounded-lg border-2 transition-colors",
        )

        # Check it includes all the classes
        attr_value = result.attrs["data-attr-class"]
        assert "flex items-center gap-3 p-4 rounded-lg border-2 transition-colors" in attr_value
        assert "bg-blue-500 text-white border-blue-600 shadow-lg" in attr_value
        assert "bg-gray-300 text-gray-600 border-gray-300" in attr_value

    def test_real_world_dark_mode(self):
        """Test a real-world dark mode toggle."""
        result = toggle_class(
            "$darkMode",
            "bg-gray-900 text-gray-100 border-gray-700",
            "bg-white text-gray-900 border-gray-200",
            base="min-h-screen p-8 transition-colors duration-200",
        )

        attr_value = result.attrs["data-attr-class"]
        assert "min-h-screen p-8 transition-colors duration-200" in attr_value
        assert "$darkMode ?" in attr_value

    def test_multi_state_without_base(self):
        """Test multi-state pattern without base classes."""
        result = toggle_class(
            "$status",
            success="bg-green-500 text-white",
            error="bg-red-500 text-white",
            warning="bg-yellow-500 text-black",
            _="bg-gray-300",
        )
        expected = '$status === "success" ? "bg-green-500 text-white" : $status === "error" ? "bg-red-500 text-white" : $status === "warning" ? "bg-yellow-500 text-black" : "bg-gray-300"'
        assert result.attrs["data-attr-class"] == expected

    def test_multi_state_with_base(self):
        """Test multi-state pattern with base classes always applied."""
        result = toggle_class(
            "$status",
            success="bg-green-500 text-white",
            error="bg-red-500 text-white",
            _="bg-gray-300",
            base="px-3 py-1 rounded",
        )
        expected = '$status === "success" ? "px-3 py-1 rounded bg-green-500 text-white" : $status === "error" ? "px-3 py-1 rounded bg-red-500 text-white" : "px-3 py-1 rounded bg-gray-300"'
        assert result.attrs["data-attr-class"] == expected

    def test_multi_state_no_default(self):
        """Test multi-state pattern without default (_) case."""
        result = toggle_class(
            "$theme",
            dark="bg-gray-900 text-white",
            light="bg-white text-gray-900",
            base="transition-colors duration-200",
        )
        expected = '$theme === "dark" ? "transition-colors duration-200 bg-gray-900 text-white" : $theme === "light" ? "transition-colors duration-200 bg-white text-gray-900" : "transition-colors duration-200"'
        assert result.attrs["data-attr-class"] == expected

    def test_multi_state_single_option(self):
        """Test multi-state with just one named state and default."""
        result = toggle_class("$isSpecial", special="bg-gold-500 animate-pulse", _="bg-gray-100")
        expected = '$isSpecial === "special" ? "bg-gold-500 animate-pulse" : "bg-gray-100"'
        assert result.attrs["data-attr-class"] == expected

    def test_api_patterns(self):
        """Test that both API patterns work correctly."""
        # Binary pattern with positional args
        binary_result = toggle_class(
            "$active",
            "bg-blue-500",  # truthy (first positional)
            "bg-gray-300",  # falsy (second positional)
            base="p-4",
        )

        # Multi-state pattern with keyword args
        multi_result = toggle_class("$status", success="bg-green-500", error="bg-red-500", _="bg-gray-300", base="p-4")

        # Binary should generate simple ternary
        assert binary_result.attrs["data-attr-class"] == '$active ? "p-4 bg-blue-500" : "p-4 bg-gray-300"'

        # Multi-state should generate chained ternaries
        assert '$status === "success"' in multi_result.attrs["data-attr-class"]
        assert '$status === "error"' in multi_result.attrs["data-attr-class"]

    def test_full_equivalence_simple(self):
        """Test that toggle_class generates equivalent expressions to ds_attr."""
        # Test 1: Simple binary
        toggle_result = toggle_class("$active", "on", "off")
        manual_result = ds_attr(class_=if_("$active", "on", "off"))
        # Compare expression values (different attribute names)
        assert toggle_result.attrs["data-attr-class"] == manual_result.attrs["data-attr-class-"]

        # Test 2: With base classes
        toggle_result = toggle_class("$expanded", "h-auto", "h-0", base="overflow-hidden transition-height")
        manual_result = ds_attr(
            class_=if_("$expanded", "overflow-hidden transition-height h-auto", "overflow-hidden transition-height h-0")
        )
        assert toggle_result.attrs["data-attr-class"] == manual_result.attrs["data-attr-class-"]

        # Test 3: Complex condition
        toggle_result = toggle_class("$count > 10 && $enabled", "text-green-500", "text-gray-400")
        manual_result = ds_attr(class_=if_("$count > 10 && $enabled", "text-green-500", "text-gray-400"))
        assert toggle_result.attrs["data-attr-class"] == manual_result.attrs["data-attr-class-"]

    def test_full_equivalence_multi_state(self):
        """Test that toggle_class generates equivalent expressions for multi-state cases."""
        # Multi-state without base
        toggle_result = toggle_class("$theme", dark="bg-gray-900", light="bg-white", _="bg-gray-100")
        manual_result = ds_attr(class_=if_("$theme", dark="bg-gray-900", light="bg-white", _="bg-gray-100"))
        # Compare expression values (different attribute names)
        assert toggle_result.attrs["data-attr-class"] == manual_result.attrs["data-attr-class-"]

        # Multi-state with base - manual version is more complex
        toggle_result = toggle_class(
            "$status", success="text-green-500", error="text-red-500", _="text-gray-500", base="font-semibold"
        )
        # Manual equivalent would need to repeat base in each branch
        manual_expression = '$status === "success" ? "font-semibold text-green-500" : $status === "error" ? "font-semibold text-red-500" : "font-semibold text-gray-500"'
        assert toggle_result.attrs["data-attr-class"] == manual_expression
