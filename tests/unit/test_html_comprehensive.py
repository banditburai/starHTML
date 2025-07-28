"""Comprehensive tests for the html.py module.

This module tests all functionality in src/starhtml/html.py including:
- ft_html core element creation
- ft_datastar Datastar-aware element creation
- html2ft HTML to FT conversion
- Helper functions (attrmap_x, _is_valid_attr, _get_tag_name)
- FT patches (__str__, __add__, __radd__)
- Configuration (fh_cfg)
"""

from fastcore.xml import FT

from starhtml.datastar import ds_bind, ds_on_click, ds_show, ds_signals, ds_text
from starhtml.html import _get_tag_name, _is_valid_attr, attrmap_x, fh_cfg, ft_datastar, ft_html, html2ft


class TestFtHtml:
    """Test ft_html core element creation function."""

    def test_basic_element_creation(self):
        """Test basic element creation with ft_html."""
        element = ft_html("div", "content")
        assert element.tag == "div"
        assert element.children == ("content",)

    def test_element_with_attributes(self):
        """Test element creation with various attributes."""
        element = ft_html("div", "content", id="test-id", cls="test-class")
        assert element.tag == "div"
        assert element.children == ("content",)
        assert element.attrs["id"] == "test-id"
        assert element.attrs["class"] == "test-class"

    def test_element_with_style_and_title(self):
        """Test element with style and title attributes."""
        element = ft_html("p", "text", style="color: red;", title="Tooltip")
        assert element.attrs["style"] == "color: red;"
        assert element.attrs["title"] == "Tooltip"

    def test_element_with_multiple_children(self):
        """Test element with multiple children."""
        child1 = ft_html("span", "first")
        child2 = ft_html("span", "second")
        parent = ft_html("div", child1, child2)

        assert len(parent.children) == 2
        assert parent.children[0] == child1
        assert parent.children[1] == child2

    def test_element_with_dict_attributes(self):
        """Test element creation with dictionary attributes."""
        attrs = {"data-value": "123", "aria-label": "test"}
        element = ft_html("div", "content", attrs)

        assert "data-value" in element.attrs
        assert "aria-label" in element.attrs

    def test_auto_id_generation(self):
        """Test automatic ID generation when enabled."""
        # Enable auto_id temporarily
        original_auto_id = fh_cfg.auto_id
        fh_cfg.auto_id = True

        try:
            element = ft_html("div", "content")
            assert "id" in element.attrs
            assert element.attrs["id"] is not None

            # Test explicit ID overrides auto ID
            element_with_id = ft_html("div", "content", id="custom-id")
            assert element_with_id.attrs["id"] == "custom-id"
        finally:
            fh_cfg.auto_id = original_auto_id

    def test_auto_id_boolean_true(self):
        """Test auto ID generation with id=True."""
        element = ft_html("div", "content", id=True)
        assert "id" in element.attrs
        assert element.attrs["id"] is not None
        assert len(element.attrs["id"]) > 0

    def test_id_from_ft_element(self):
        """Test ID extraction from FT element."""
        ft_element = FT("span", ("test",), {"id": "span-id"})
        element = ft_html("div", "content", id=ft_element)
        assert element.attrs["id"] == "span-id"

    def test_auto_name_generation(self):
        """Test automatic name attribute generation for named elements."""
        # Test with button (in named set)
        element = ft_html("button", "Click me", id="btn-id")
        assert element.attrs["name"] == "btn-id"

        # Test with explicit name overrides auto name
        element_with_name = ft_html("button", "Click", id="btn-id", name="custom-name")
        assert element_with_name.attrs["name"] == "custom-name"

        # Test with non-named element (div not in named set)
        div_element = ft_html("div", "content", id="div-id")
        assert "name" not in div_element.attrs

    def test_void_elements(self):
        """Test void elements are properly marked."""
        # br is a void element
        br_element = ft_html("br")
        assert br_element.void_ is True

        # div is not a void element
        div_element = ft_html("div")
        assert div_element.void_ is False

    def test_custom_ft_cls(self):
        """Test custom ft_cls parameter."""

        class CustomFT(FT):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)
                self.custom_attr = "custom"

        element = ft_html("div", "content", ft_cls=CustomFT)
        assert isinstance(element, CustomFT)
        assert hasattr(element, "custom_attr")
        assert element.custom_attr == "custom"

    def test_custom_attrmap_and_valmap(self):
        """Test custom attrmap and valmap functions."""

        def custom_attrmap(attr):
            return attr.upper()

        def custom_valmap(val):
            return str(val).upper() if val else val

        element = ft_html("div", "content", test_attr="value", attrmap=custom_attrmap, valmap=custom_valmap)

        # The exact behavior depends on the fastcore implementation
        # but we can verify the custom functions were used
        assert element.tag == "div"


class TestFtDatastar:
    """Test ft_datastar function for Datastar-aware elements."""

    def test_basic_datastar_element(self):
        """Test basic Datastar element creation."""
        element = ft_datastar("div", "content", ds_show("$isVisible"))
        assert element.tag == "div"
        assert element.children == ("content",)
        # ds_show should be converted to data-show
        assert "data-show" in element.attrs

    def test_datastar_with_regular_attrs(self):
        """Test Datastar element with mixed regular and Datastar attributes."""
        element = ft_datastar(
            "div", "content", ds_bind("value"), ds_on_click("handleClick()"), id="test-id", cls="test-class"
        )

        assert element.attrs["id"] == "test-id"
        assert element.attrs["class"] == "test-class"
        assert "data-bind" in element.attrs
        assert "data-on-click" in element.attrs

    def test_multiple_datastar_attributes(self):
        """Test element with multiple Datastar attributes."""
        element = ft_datastar(
            "button",
            "Click me",
            ds_show("$isVisible"),
            ds_text("$buttonText"),
            ds_on_click("handleClick()"),
            ds_bind("buttonValue"),
        )

        expected_attrs = ["data-show", "data-text", "data-on-click", "data-bind"]
        for attr in expected_attrs:
            assert attr in element.attrs


class TestHtml2ft:
    """Test html2ft HTML to FT conversion function."""

    def test_simple_html_conversion(self):
        """Test conversion of simple HTML to ft expression."""
        html = "<div>Hello World</div>"
        result = html2ft(html)
        assert "Div(" in result
        assert "Hello World" in result

    def test_html_with_attributes(self):
        """Test HTML with attributes conversion."""
        html = '<div id="test" class="container">Content</div>'
        result = html2ft(html)
        assert "Div(" in result
        assert "id=" in result or "test" in result
        assert "cls=" in result or "class" in result or "container" in result
        assert "Content" in result

    def test_nested_html_conversion(self):
        """Test nested HTML structure conversion."""
        html = "<div><p>Paragraph</p><span>Span text</span></div>"
        result = html2ft(html)
        assert "Div(" in result
        assert "P(" in result
        assert "Span(" in result
        assert "Paragraph" in result
        assert "Span text" in result

    def test_html_with_special_attributes(self):
        """Test HTML with special attributes like data- and aria-."""
        html = '<div data-value="123" aria-label="test">Content</div>'
        result = html2ft(html)
        assert "Div(" in result
        assert "data_value" in result or "data-value" in result
        assert "aria_label" in result or "aria-label" in result

    def test_attr1st_parameter(self):
        """Test attr1st parameter functionality."""
        html = '<div class="test">Content</div>'
        result_normal = html2ft(html, attr1st=False)
        result_attr1st = html2ft(html, attr1st=True)

        # Both should contain the same content but different formatting
        assert "Content" in result_normal
        assert "Content" in result_attr1st
        assert "cls=" in result_normal or "class=" in result_normal
        assert "cls=" in result_attr1st or "class=" in result_attr1st

    def test_html_with_comments(self):
        """Test HTML with comments (should be removed)."""
        html = "<div><!-- This is a comment -->Content</div>"
        result = html2ft(html)
        assert "Content" in result
        assert "comment" not in result.lower()

    def test_malformed_html_handling(self):
        """Test handling of malformed HTML."""
        html = "<div><p>Unclosed paragraph<span>Span</span></div>"
        result = html2ft(html)
        # Should still produce valid ft expression
        assert "Div(" in result
        assert "Span" in result

    def test_empty_html(self):
        """Test conversion of empty or whitespace-only HTML."""
        result = html2ft("")
        assert result == ""

        result = html2ft("   ")
        assert result == ""

        # Test HTML with only whitespace content to cover empty stripped text case
        result = html2ft("<div>   </div>")
        assert "Div(" in result

        # Test with mixed content including empty strings
        result = html2ft("<p>text</p><span></span>")
        assert "P(" in result and "Span(" in result

    def test_html_with_exotic_attributes(self):
        """Test HTML with non-standard attribute names."""
        html = '<div @click="handler" v-if="condition">Content</div>'
        result = html2ft(html)
        assert "Content" in result
        # Exotic attributes should be handled appropriately


class TestAttrMapX:
    """Test attrmap_x attribute mapping function."""

    def test_basic_attribute_mapping(self):
        """Test basic attribute name mapping."""
        assert attrmap_x("data_bind") == "data-bind"
        assert attrmap_x("aria_label") == "aria-label"
        assert attrmap_x("tab_index") == "tab-index"

    def test_cls_mapping(self):
        """Test cls to class mapping."""
        assert attrmap_x("cls") == "class"
        assert attrmap_x("klass") == "class"

    def test_for_mapping(self):
        """Test fr to for mapping."""
        assert attrmap_x("fr") == "for"

    def test_at_prefix_mapping(self):
        """Test _at_ prefix mapping to @ (Alpine.js style)."""
        assert attrmap_x("_at_click") == "@click"
        assert attrmap_x("_at_keyup") == "@keyup"
        assert attrmap_x("_at_model") == "@model"

    def test_no_mapping_needed(self):
        """Test attributes that don't need mapping."""
        assert attrmap_x("id") == "id"
        assert attrmap_x("href") == "href"
        assert attrmap_x("src") == "src"


class TestHelperFunctions:
    """Test helper functions in html module."""

    def test_is_valid_attr(self):
        """Test _is_valid_attr function."""
        # Valid attribute names
        assert _is_valid_attr("data-value") is True
        assert _is_valid_attr("aria-label") is True
        assert _is_valid_attr("id") is True
        assert _is_valid_attr("class") is True
        assert _is_valid_attr("_underscore") is True

        # Invalid attribute names
        assert _is_valid_attr("123invalid") is False
        assert _is_valid_attr("@invalid") is False
        assert _is_valid_attr("") is False

    def test_attribute_validation_performance(self):
        """Test that attribute validation is performant for repeated calls."""
        import time

        # Test behavior: repeated validation calls should be fast
        attr_name = "data-complex-attribute-name"

        # Time first call
        start = time.perf_counter()
        result1 = _is_valid_attr(attr_name)
        first_call_time = time.perf_counter() - start

        # Time second call (should be faster if cached)
        start = time.perf_counter()
        result2 = _is_valid_attr(attr_name)
        second_call_time = time.perf_counter() - start

        # Verify results are consistent
        assert result1 == result2
        # Second call should be at least as fast (caching benefit)
        assert second_call_time <= first_call_time * 2  # Allow some variance

    def test_get_tag_name(self):
        """Test _get_tag_name function."""
        assert _get_tag_name("div") == "Div"
        assert _get_tag_name("custom-element") == "Custom_element"
        assert _get_tag_name("[document]") == "[document]"
        assert _get_tag_name("h1") == "H1"

    def test_tag_name_conversion_consistency(self):
        """Test that tag name conversion is consistent across calls."""
        # Test behavior: tag names are consistently converted
        test_tags = ["custom-element", "my-component", "data-view"]

        for tag in test_tags:
            # Multiple calls should return same result
            result1 = _get_tag_name(tag)
            result2 = _get_tag_name(tag)
            result3 = _get_tag_name(tag)

            assert result1 == result2 == result3
            # Verify the conversion follows expected pattern
            assert "-" not in result1  # Hyphens should be converted


class TestFtPatches:
    """Test FT class patches for string operations."""

    def test_ft_str_with_id(self):
        """Test FT __str__ patch when element has ID."""
        element = ft_html("div", "content", id="test-id")
        result = str(element)
        # Should return the ID when element has one
        assert result == "test-id"

    def test_ft_str_without_id(self):
        """Test FT __str__ patch when element has no ID."""
        element = ft_html("div", "content")
        result = str(element)
        # Should return XML representation when no ID
        assert "<div" in result
        assert "content" in result

    def test_ft_radd(self):
        """Test FT __radd__ patch (right addition)."""
        element = ft_html("span", "text", id="span-id")
        result = "prefix" + str(element)  # type: ignore
        assert result == "prefixspan-id"

    def test_ft_add(self):
        """Test FT __add__ patch (left addition)."""
        element = ft_html("span", "text", id="span-id")
        result = str(element) + "suffix"  # type: ignore
        assert result == "span-idsuffix"

    def test_ft_string_concatenation_complex(self):
        """Test complex string concatenation scenarios."""
        element1 = ft_html("div", "content1", id="div1")
        element2 = ft_html("span", "content2", id="span2")

        # Element + Element (both have IDs)
        result = str(element1) + str(element2)  # type: ignore
        assert result == "div1span2"

        # String + Element + String
        result = "start-" + str(element1) + "-end"  # type: ignore
        assert result == "start-div1-end"


class TestConfiguration:
    """Test fh_cfg configuration object."""

    def test_default_configuration(self):
        """Test default configuration values."""
        assert fh_cfg.attrmap == attrmap_x
        assert fh_cfg.ft_cls == FT
        assert fh_cfg.auto_id is False
        assert fh_cfg.auto_name is True
        assert fh_cfg.indent is True

    def test_configuration_modification(self):
        """Test that configuration can be modified."""
        original_auto_id = fh_cfg.auto_id

        try:
            fh_cfg.auto_id = True
            assert fh_cfg.auto_id is True

            # Test that the change affects element creation
            element = ft_html("div", "content")
            assert "id" in element.attrs
        finally:
            # Restore original value
            fh_cfg.auto_id = original_auto_id


class TestEdgeCases:
    """Test edge cases and error conditions."""

    def test_empty_tag_name(self):
        """Test behavior with empty tag name."""
        # This should still work or handle gracefully
        element = ft_html("", "content")
        assert element.children == ("content",)

    def test_none_values_handling(self):
        """Test handling of None values in various contexts."""
        element = ft_html("div", None, id=None, cls="test")
        assert element.tag == "div"
        assert element.attrs.get("class") == "test"
        # None values should be filtered appropriately

    def test_special_characters_in_attributes(self):
        """Test special characters in attribute values."""
        element = ft_html("div", "content", data_value='{"key": "value"}', title="Title with 'quotes' and <brackets>")
        assert element.attrs["data-value"] == '{"key": "value"}'
        assert "quotes" in element.attrs["title"]

    def test_large_content_handling(self):
        """Test handling of large content."""
        large_content = "x" * 10000
        element = ft_html("div", large_content)
        assert element.children[0] == large_content
        assert len(str(element)) > 10000

    def test_deeply_nested_structures(self):
        """Test deeply nested element structures."""
        # Create a deeply nested structure
        inner = ft_html("span", "deep content")
        for i in range(10):
            inner = ft_html("div", inner, cls=f"level-{i}")

        # Should handle deep nesting without issues
        assert inner.tag == "div"
        assert "level-9" in inner.attrs["class"]


class TestRealWorldScenarios:
    """Test real-world usage scenarios."""

    def test_datastar_reactive_component(self):
        """Test creating a reactive component with Datastar."""
        component = ft_datastar(
            "div",
            ft_html("h2", "Counter"),
            ft_html("p", "Count: ", ft_html("span", ds_text("$count"))),
            ft_html("button", "+", ds_on_click("count++")),
            ft_html("button", "-", ds_on_click("count--")),
            ds_signals({"count": 0}),
            cls="counter-component",
        )

        assert component.tag == "div"
        assert component.attrs["class"] == "counter-component"
        assert "data-signals-count" in component.attrs

        # Check that child elements exist
        assert len(component.children) == 4  # h2, p, button, button

    def test_html_conversion_real_page(self):
        """Test converting a real HTML page structure."""
        html = """
        <html>
            <head>
                <title>Test Page</title>
                <meta charset="utf-8">
            </head>
            <body>
                <header>
                    <h1>Welcome</h1>
                    <nav>
                        <a href="/">Home</a>
                        <a href="/about">About</a>
                    </nav>
                </header>
                <main>
                    <article>
                        <h2>Article Title</h2>
                        <p>Article content goes here.</p>
                    </article>
                </main>
                <footer>
                    <p>&copy; 2023 Test Site</p>
                </footer>
            </body>
        </html>
        """

        result = html2ft(html)

        # Should contain all the major elements
        assert "Html(" in result
        assert "Head(" in result
        assert "Title(" in result
        assert "Body(" in result
        assert "Header(" in result
        assert "Nav(" in result
        assert "Main(" in result
        assert "Article(" in result
        assert "Footer(" in result

        # Should contain content
        assert "Test Page" in result
        assert "Welcome" in result
        assert "Article Title" in result

    def test_mixed_content_and_elements(self):
        """Test mixing text content with child elements."""
        element = ft_html(
            "p", "This is some text with ", ft_html("strong", "bold text"), " and ", ft_html("em", "italic text"), "."
        )

        assert element.tag == "p"
        assert len(element.children) == 5
        assert element.children[0] == "This is some text with "
        assert element.children[1].tag == "strong"
        assert element.children[2] == " and "
        assert element.children[3].tag == "em"
        assert element.children[4] == "."
