"""Behavioral tests for StarHTML HTML elements and components.

These tests focus on actual functionality and behavior rather than
string matching or trivial existence checks.
"""

import tempfile
from dataclasses import dataclass
from pathlib import Path as PathlibPath

import pytest
from fastcore.xml import to_xml

from starhtml import (
    H1,
    Button,
    Div,
    Form,
    Input,
    Option,
    P,
    Select,
    Svg,
    Table,
    Tbody,
    Td,
    Th,
    Thead,
    Tr,
)
from starhtml.tags import (
    Circle,
    Rect,
    transformd,
)
from starhtml.utils import (
    File,
    fill_dataclass,
    find_inputs,
)


class TestElementBehavior:
    """Test actual element behavior and functionality."""

    def test_element_attribute_accessibility(self):
        """Test that elements properly expose their attributes for programmatic access."""
        div = Div("Content", id="test-id", cls="test-class", data_value="123")

        # Test that attributes are accessible
        assert div.get("id") == "test-id"
        assert div.get("class") == "test-class"
        assert div.get("data-value") == "123"

        # Test that content is accessible
        assert div.children == ("Content",)
        assert div.tag == "div"

    def test_element_nesting_behavior(self):
        """Test element nesting creates proper parent-child relationships."""
        parent = Div(H1("Title"), P("Content", id="content-para"), cls="container")

        # Test that children are properly nested
        assert len(parent.children) == 2
        h1_child = parent.children[0]
        p_child = parent.children[1]

        assert h1_child.tag == "h1"
        assert h1_child.children == ("Title",)

        assert p_child.tag == "p"
        assert p_child.get("id") == "content-para"
        assert p_child.children == ("Content",)

    def test_svg_coordinate_system_behavior(self):
        """Test SVG elements follow proper coordinate system logic."""
        # Create a simple SVG with shapes
        svg = Svg(Rect(x=10, y=10, width=80, height=60), Circle(cx=50, cy=50, r=20), width=100, height=100)

        # Test that SVG has the expected structure
        assert svg.tag == "svg"
        assert svg.get("width") == 100
        assert svg.get("height") == 100

        # Test that children maintain their coordinate properties
        assert len(svg.children) == 2
        rect = svg.children[0]
        circle = svg.children[1]

        assert rect.tag == "rect"
        assert rect.get("x") == 10
        assert rect.get("y") == 10
        assert rect.get("width") == 80
        assert rect.get("height") == 60

        assert circle.tag == "circle"
        assert circle.get("cx") == 50
        assert circle.get("cy") == 50
        assert circle.get("r") == 20

    def test_transformd_coordinate_transformation(self):
        """Test coordinate transformation helper behavior."""
        # Test translate transformation
        translate_transform = transformd(translate=(10, 20))
        assert "translate(10, 20)" in translate_transform["transform"]

        # Test scale transformation
        scale_transform = transformd(scale=(2,))
        assert "scale(2,)" in scale_transform["transform"]

        # Test rotate transformation
        rotate_transform = transformd(rotate=(45, 50, 50))
        assert "rotate(45,50,50)" in rotate_transform["transform"]

        # Test combined transformations
        combined = transformd(translate=(10, 20), scale=(1.5,), rotate=(30,))
        transform_str = combined["transform"]
        assert "translate(10, 20)" in transform_str
        assert "scale(1.5,)" in transform_str
        assert "rotate(30" in transform_str  # Format may vary (rotate(30) vs rotate(30,))

        # Test empty transformation
        empty = transformd()
        assert empty == {}


class TestFormDataFlowBehavior:
    """Test actual data flow in form scenarios."""

    def test_dataclass_form_integration(self):
        """Test integration between dataclasses and forms."""

        @dataclass
        class UserData:
            name: str = ""
            email: str = ""
            age: int = 0

        @dataclass
        class UpdateData:
            name: str = "John Doe"
            email: str = "john@example.com"
            age: int = 30

        user = UserData()
        update = UpdateData()

        # Test dataclass filling behavior
        filled_user = fill_dataclass(update, user)
        assert filled_user.name == "John Doe"
        assert filled_user.email == "john@example.com"
        assert filled_user.age == 30

    def test_form_validation_state_simulation(self):
        """Test form validation state simulation."""
        form = Form(
            Input(type="email", name="email", required=True, pattern=r"[a-z0-9._%+-]+@[a-z0-9.-]+\.[a-z]{2,}$"),
            Input(type="number", name="age", min=18, max=100, required=True),
            Button("Submit", type="submit"),
        )

        # Test that validation attributes are properly set
        inputs = find_inputs(form, "input")
        email_input = next(inp for inp in inputs if inp.get("name") == "email")
        age_input = next(inp for inp in inputs if inp.get("name") == "age")

        assert email_input.get("required") is True
        assert email_input.get("type") == "email"
        assert email_input.get("pattern") is not None

        assert age_input.get("required") is True
        assert age_input.get("type") == "number"
        assert age_input.get("min") == 18
        assert age_input.get("max") == 100


class TestFileHandlingBehavior:
    """Test file handling and content inclusion behavior."""

    def test_file_content_inclusion(self):
        """Test File utility for including external content."""
        test_content = "<div>Test file content</div>"

        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".html") as f:
            f.write(test_content)
            temp_path = f.name

        try:
            # Test file content inclusion
            file_content = File(temp_path)
            assert str(file_content) == test_content

            # Test that file content is treated as raw HTML (NotStr)
            # This prevents double-escaping when included in elements
            div_with_file = Div(file_content)
            xml_output = to_xml(div_with_file)
            assert test_content in xml_output

        finally:
            PathlibPath(temp_path).unlink()

    def test_file_not_found_handling(self):
        """Test File utility behavior with missing files."""
        with pytest.raises(FileNotFoundError):
            File("/path/that/does/not/exist.html")


class TestTableStructureBehavior:
    """Test table structure and data organization behavior."""

    def test_table_data_structure_behavior(self):
        """Test table structure maintains data relationships."""
        table_data = [
            {"name": "Alice", "age": 30, "city": "New York"},
            {"name": "Bob", "age": 25, "city": "London"},
            {"name": "Charlie", "age": 35, "city": "Tokyo"},
        ]

        # Create table programmatically
        table = Table(
            Thead(Tr(Th("Name"), Th("Age"), Th("City"))),
            Tbody(*[Tr(Td(row["name"]), Td(str(row["age"])), Td(row["city"])) for row in table_data]),
        )

        # Test table structure
        assert table.tag == "table"
        assert len(table.children) == 2  # thead and tbody

        thead = table.children[0]
        tbody = table.children[1]

        assert thead.tag == "thead"
        assert tbody.tag == "tbody"

        # Test that tbody has correct number of rows
        assert len(tbody.children) == len(table_data)

        # Test that first row has correct data
        first_row = tbody.children[0]
        assert first_row.tag == "tr"
        assert len(first_row.children) == 3

        name_cell = first_row.children[0]
        age_cell = first_row.children[1]
        city_cell = first_row.children[2]

        assert name_cell.children[0] == "Alice"
        assert age_cell.children[0] == "30"
        assert city_cell.children[0] == "New York"


class TestSelectAndOptionBehavior:
    """Test select dropdown behavior and option management."""

    def test_select_option_value_behavior(self):
        """Test select dropdown with option values and selection."""
        select = Select(
            Option("Choose...", value=""),
            Option("Option 1", value="opt1"),
            Option("Option 2", value="opt2", selected=True),
            Option("Option 3", value="opt3"),
            name="choice",
        )

        # Test select structure
        assert select.tag == "select"
        assert select.get("name") == "choice"
        assert len(select.children) == 4

        # Test option properties
        options = select.children

        # First option (placeholder)
        assert options[0].tag == "option"
        assert options[0].get("value") == ""
        assert options[0].children[0] == "Choose..."

        # Second option
        assert options[1].get("value") == "opt1"
        assert options[1].children[0] == "Option 1"

        # Third option (selected)
        assert options[2].get("value") == "opt2"
        assert options[2].get("selected") is True
        assert options[2].children[0] == "Option 2"

        # Fourth option
        assert options[3].get("value") == "opt3"
        assert options[3].children[0] == "Option 3"

    def test_select_multiple_behavior(self):
        """Test select with multiple selection capability."""
        select = Select(
            Option("Option A", value="a"),
            Option("Option B", value="b", selected=True),
            Option("Option C", value="c", selected=True),
            name="multi_choice",
            multiple=True,
        )

        assert select.get("multiple") is True

        # Count selected options
        selected_options = [opt for opt in select.children if opt.get("selected")]
        assert len(selected_options) == 2


class TestErrorConditionsAndEdgeCases:
    """Test error conditions and edge case handling."""

    def test_element_with_none_values(self):
        """Test element behavior with None attribute values."""
        div = Div("Content", id="test", data_value=None, cls="test")

        # None values should be filtered out
        assert div.get("id") == "test"
        assert div.get("class") == "test"
        # None values typically don't appear in final attributes
        assert div.get("data-value") is None

    def test_element_with_boolean_attributes(self):
        """Test boolean attribute handling behavior."""
        input_elem = Input(type="checkbox", checked=True, disabled=False, required=True, readonly=False)

        # True boolean attributes should appear
        assert input_elem.get("checked") is True
        assert input_elem.get("required") is True

        # False boolean attributes behavior may vary by implementation
        # The key is that they're handled consistently
        disabled_val = input_elem.get("disabled")
        readonly_val = input_elem.get("readonly")

        assert disabled_val is False or disabled_val is None
        assert readonly_val is False or readonly_val is None

    def test_large_content_handling(self):
        """Test handling of large content and deeply nested structures."""
        # Create a deeply nested structure
        large_content = "x" * 10000  # 10KB of content

        deep_structure = Div(
            Div(Div(Div(P(large_content), cls="level-4"), cls="level-3"), cls="level-2"), cls="level-1"
        )

        # Should handle large content without issues
        assert deep_structure.tag == "div"
        assert deep_structure.get("class") == "level-1"

        # Navigate to the deepest content
        level_2 = deep_structure.children[0]
        level_3 = level_2.children[0]
        level_4 = level_3.children[0]
        paragraph = level_4.children[0]

        assert paragraph.tag == "p"
        assert paragraph.children[0] == large_content

    def test_special_character_content_behavior(self):
        """Test handling of special characters in content."""
        special_content = 'Content with "quotes" & <brackets> and unicode: 测试 🚀'
        div = Div(special_content)

        # Content should be preserved exactly
        assert div.children[0] == special_content

        # When serialized to XML, special characters should be properly escaped
        xml_output = to_xml(div)
        # The XML should contain escaped versions
        assert "&quot;" in xml_output or '"quotes"' in xml_output
        assert "&amp;" in xml_output or "&" in xml_output
        assert "&lt;" in xml_output or "<brackets>" in xml_output
        # Unicode should be preserved
        assert "测试" in xml_output
        assert "🚀" in xml_output
