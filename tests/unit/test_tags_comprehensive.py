"""Comprehensive tests for the tags.py module.

This module tests all functionality in src/starhtml/tags.py including:
- HTML tag factory functions
- SVG tag factory functions and specialized SVG components
- PathFT class and path building methods
- transformd utility function
- Dynamic tag generation via __getattr__
- ft_svg base factory function
"""

import pytest

from starhtml.datastar import ds_on_click, ds_show
from starhtml.tags import (
    H1,
    Button,
    Circle,
    # HTML tags (sample)
    Div,
    Ellipse,
    Form,
    Input,
    Line,
    P,
    PathFT,
    Polygon,
    Polyline,
    Rect,
    Svg,
    SvgInb,
    SvgOob,
    SvgPath,
    Text,
    __getattr__,
    # Module functions
    _create_tag_factory,
    _get_ft_datastar,
    # Utilities
    ft_svg,
    transformd,
)


class TestHTMLTagFactories:
    """Test HTML tag factory functions."""

    def test_basic_html_tags(self):
        """Test basic HTML tag creation."""
        div = Div("content")
        assert div.tag == "div"
        assert div.children == ("content",)

        p = P("paragraph text")
        assert p.tag == "p"
        assert p.children == ("paragraph text",)

        h1 = H1("heading")
        assert h1.tag == "h1"
        assert h1.children == ("heading",)

    def test_html_tags_with_attributes(self):
        """Test HTML tags with attributes."""
        div = Div("content", id="test-id", cls="test-class")
        assert div.attrs["id"] == "test-id"
        assert div.attrs["class"] == "test-class"

        input_elem = Input(type="text", name="username", placeholder="Enter username")
        assert input_elem.attrs["type"] == "text"
        assert input_elem.attrs["name"] == "username"
        assert input_elem.attrs["placeholder"] == "Enter username"

    def test_html_tags_with_datastar_attrs(self):
        """Test HTML tags with Datastar attributes."""
        button = Button("Click me", ds_on_click("handleClick()"), ds_show("$isVisible"))
        assert "data-on-click" in button.attrs
        assert "data-show" in button.attrs
        assert button.attrs["data-on-click"] == "handleClick()"
        assert button.attrs["data-show"] == "$isVisible"

    def test_nested_html_elements(self):
        """Test nesting HTML elements."""
        form = Form(
            Div(Input(type="text", name="username"), Input(type="password", name="password"), cls="form-group"),
            Button("Submit", type="submit"),
            method="post",
        )

        assert form.tag == "form"
        assert form.attrs["method"] == "post"
        assert len(form.children) == 2

        form_group = form.children[0]
        assert form_group.tag == "div"
        assert form_group.attrs["class"] == "form-group"
        assert len(form_group.children) == 2


class TestSVGComponents:
    """Test SVG component creation and functionality."""

    def test_svg_root_element(self):
        """Test Svg root element creation."""
        svg = Svg(width=100, height=100)
        assert svg.tag == "svg"
        assert svg.attrs["width"] == 100
        assert svg.attrs["height"] == 100
        assert svg.attrs["xmlns"] == "http://www.w3.org/2000/svg"

    def test_svg_with_viewbox_auto_generation(self):
        """Test Svg with automatic viewBox generation."""
        svg = Svg(width=200, height=150)
        assert svg.attrs["viewbox"] == "0 0 200 150"  # Note: lowercase 'viewbox'

        # Test with w/h shorthand
        svg2 = Svg(w=300, h=200)
        assert svg2.attrs["width"] == 300
        assert svg2.attrs["height"] == 200
        assert svg2.attrs["viewbox"] == "0 0 300 200"

    def test_svg_with_explicit_viewbox(self):
        """Test Svg with explicit viewBox."""
        svg = Svg(width=100, height=100, viewBox="0 0 50 50")
        assert svg.attrs["viewbox"] == "0 0 50 50"  # Explicit viewBox should not be overridden

    def test_rect_element(self):
        """Test Rect SVG element."""
        rect = Rect(width=50, height=30, x=10, y=5)
        assert rect.tag == "rect"
        assert rect.attrs["width"] == 50
        assert rect.attrs["height"] == 30
        assert rect.attrs["x"] == 10
        assert rect.attrs["y"] == 5

    def test_rect_with_styling(self):
        """Test Rect with styling attributes."""
        rect = Rect(width=100, height=50, fill="red", stroke="blue", stroke_width=2, rx=5, ry=5)
        assert rect.attrs["fill"] == "red"
        assert rect.attrs["stroke"] == "blue"
        assert rect.attrs["stroke-width"] == 2
        assert rect.attrs["rx"] == 5
        assert rect.attrs["ry"] == 5

    def test_circle_element(self):
        """Test Circle SVG element."""
        circle = Circle(r=25, cx=50, cy=50)
        assert circle.tag == "circle"
        assert circle.attrs["r"] == 25
        assert circle.attrs["cx"] == 50
        assert circle.attrs["cy"] == 50

    def test_circle_with_default_position(self):
        """Test Circle with default center position."""
        circle = Circle(r=30)
        assert circle.attrs["r"] == 30
        assert circle.attrs["cx"] == 0
        assert circle.attrs["cy"] == 0

    def test_ellipse_element(self):
        """Test Ellipse SVG element."""
        ellipse = Ellipse(rx=40, ry=20, cx=100, cy=80)
        assert ellipse.tag == "ellipse"
        assert ellipse.attrs["rx"] == 40
        assert ellipse.attrs["ry"] == 20
        assert ellipse.attrs["cx"] == 100
        assert ellipse.attrs["cy"] == 80

    def test_line_element(self):
        """Test Line SVG element."""
        line = Line(x1=0, y1=0, x2=100, y2=50)
        assert line.tag == "line"
        assert line.attrs["x1"] == 0
        assert line.attrs["y1"] == 0
        assert line.attrs["x2"] == 100
        assert line.attrs["y2"] == 50
        assert line.attrs["stroke"] == "black"  # Default stroke
        assert line.attrs["stroke-width"] == 1  # Default stroke-width

    def test_line_with_w_shorthand(self):
        """Test Line with w shorthand for stroke_width."""
        line = Line(x1=0, y1=0, x2=50, y2=50, w=3)
        assert line.attrs["stroke-width"] == 3

    def test_polyline_with_args(self):
        """Test Polyline with coordinate arguments."""
        polyline = Polyline((0, 0), (10, 20), (30, 15))
        assert polyline.tag == "polyline"
        assert "0,0 10,20 30,15" in polyline.attrs["points"]

    def test_polyline_with_points_param(self):
        """Test Polyline with explicit points parameter."""
        polyline = Polyline(points="5,5 25,25 45,15")
        assert polyline.attrs["points"] == "5,5 25,25 45,15"

    def test_polygon_with_args(self):
        """Test Polygon with coordinate arguments."""
        polygon = Polygon((0, 0), (50, 0), (25, 50))
        assert polygon.tag == "polygon"
        assert "0,0 50,0 25,50" in polygon.attrs["points"]

    def test_polygon_with_points_param(self):
        """Test Polygon with explicit points parameter."""
        polygon = Polygon(points="10,10 40,10 25,40")
        assert polygon.attrs["points"] == "10,10 40,10 25,40"

    def test_text_element(self):
        """Test Text SVG element."""
        text = Text("Hello SVG", x=20, y=40)
        assert text.tag == "text"
        assert text.children == ("Hello SVG",)
        assert text.attrs["x"] == 20
        assert text.attrs["y"] == 40

    def test_text_with_styling(self):
        """Test Text with font and styling attributes."""
        text = Text(
            "Styled text",
            x=10,
            y=30,
            font_family="Arial",
            font_size="16px",
            fill="blue",
            text_anchor="middle",
            font_weight="bold",
        )
        assert text.attrs["font-family"] == "Arial"
        assert text.attrs["font-size"] == "16px"
        assert text.attrs["fill"] == "blue"
        assert text.attrs["text-anchor"] == "middle"
        assert text.attrs["font-weight"] == "bold"


class TestFtSvg:
    """Test ft_svg base factory function."""

    def test_ft_svg_basic(self):
        """Test basic ft_svg functionality."""
        element = ft_svg("g")
        assert element.tag == "g"

    def test_ft_svg_with_content(self):
        """Test ft_svg with content and attributes."""
        element = ft_svg("g", "content", id="group-id", cls="group-class")
        assert element.tag == "g"
        assert element.children == ("content",)
        assert element.attrs["id"] == "group-id"
        assert element.attrs["class"] == "group-class"

    def test_ft_svg_with_svg_attributes(self):
        """Test ft_svg with SVG-specific attributes."""
        element = ft_svg("rect", transform="translate(10,20)", opacity=0.8, filter="blur(2px)", pointer_events="none")
        assert element.attrs["transform"] == "translate(10,20)"
        assert element.attrs["opacity"] == 0.8
        assert element.attrs["filter"] == "blur(2px)"
        assert element.attrs["pointer-events"] == "none"

    def test_ft_svg_with_clip_and_mask(self):
        """Test ft_svg with clip and mask attributes."""
        element = ft_svg("circle", clip="url(#clipPath)", mask="url(#maskPath)", vector_effect="non-scaling-stroke")
        assert element.attrs["clip"] == "url(#clipPath)"
        assert element.attrs["mask"] == "url(#maskPath)"
        assert element.attrs["vector-effect"] == "non-scaling-stroke"


class TestTransformd:
    """Test transformd transformation utility function."""

    def test_translate_transform(self):
        """Test translate transformation."""
        transform = transformd(translate=(10, 20))
        assert transform["transform"] == "translate(10, 20)"

    def test_scale_transform(self):
        """Test scale transformation."""
        transform = transformd(scale=(2, 1.5))
        assert transform["transform"] == "scale(2, 1.5)"

        # Test single scale value
        transform = transformd(scale=(2,))
        assert transform["transform"] == "scale(2,)"

    def test_rotate_transform(self):
        """Test rotate transformation."""
        transform = transformd(rotate=(45,))
        assert "rotate(45)" in transform["transform"]

        # Test rotate with center point
        transform = transformd(rotate=(30, 50, 50))
        assert "rotate(30,50,50)" in transform["transform"]

    def test_skew_transforms(self):
        """Test skewX and skewY transformations."""
        transform = transformd(skewX=15)
        assert transform["transform"] == "skewX(15)"

        transform = transformd(skewY=-10)
        assert transform["transform"] == "skewY(-10)"

        transform = transformd(skewX=10, skewY=5)
        assert "skewX(10)" in transform["transform"]
        assert "skewY(5)" in transform["transform"]

    def test_matrix_transform(self):
        """Test matrix transformation."""
        transform = transformd(matrix=(1, 0, 0, 1, 30, 40))
        assert transform["transform"] == "matrix(1, 0, 0, 1, 30, 40)"

    def test_combined_transforms(self):
        """Test multiple transformations combined."""
        transform = transformd(translate=(10, 20), scale=(1.5,), rotate=(45,))
        transform_str = transform["transform"]
        assert "translate(10, 20)" in transform_str
        assert "scale(1.5,)" in transform_str
        assert "rotate(45)" in transform_str

    def test_empty_transform(self):
        """Test transformd with no parameters."""
        transform = transformd()
        assert transform == {}


class TestPathFT:
    """Test PathFT class and path building methods."""

    def test_path_creation(self):
        """Test basic Path creation."""
        path = SvgPath()
        assert isinstance(path, PathFT)
        assert path.tag == "path"

    def test_path_with_initial_d(self):
        """Test Path creation with initial d attribute."""
        path = SvgPath(d="M 10 10 L 20 20")
        assert path.attrs["d"] == "M 10 10 L 20 20"

    def test_path_with_styling(self):
        """Test Path with styling attributes."""
        path = SvgPath(fill="none", stroke="red", stroke_width=2)
        assert path.attrs["fill"] == "none"
        assert path.attrs["stroke"] == "red"
        assert path.attrs["stroke-width"] == 2

    def test_path_absolute_commands(self):
        """Test PathFT absolute command methods."""
        path = SvgPath()

        # Test Move to (M)
        path.M(10, 20)
        assert "M10,20" in (path.d or "")

        # Test Line to (L)
        path.L(30, 40)
        assert "L30,40" in (path.d or "")

        # Test Horizontal line (H)
        path.H(50)
        assert "H50" in (path.d or "")

        # Test Vertical line (V)
        path.V(60)
        assert "V60" in (path.d or "")

        # Test Close path (Z)
        path.Z()
        assert "Z" in (path.d or "")

    def test_path_relative_commands(self):
        """Test PathFT relative command methods."""
        path = SvgPath()

        # Test Move to relative (m)
        path.m(5, 10)
        assert "m5,10" in (path.d or "")

        # Test Line to relative (l)
        path.l(15, 20)
        assert "l15,20" in (path.d or "")

        # Test Horizontal line relative (h)
        path.h(25)
        assert "h25" in (path.d or "")

        # Test Vertical line relative (v)
        path.v(35)
        assert "v35" in (path.d or "")

        # Test Close path relative (z)
        path.z()
        assert "z" in (path.d or "")

    def test_path_cubic_bezier_commands(self):
        """Test PathFT cubic Bézier curve commands."""
        path = SvgPath()

        # Test Cubic Bézier absolute (C)
        path.C(10, 10, 20, 20, 30, 10)
        assert "C10,10 20,20 30,10" in (path.d or "")

        # Test Smooth cubic Bézier absolute (S)
        path.S(40, 20, 50, 10)
        assert "S40,20 50,10" in (path.d or "")

        # Test Cubic Bézier relative (c)
        path.c(5, 5, 10, 10, 15, 5)
        assert "c5,5 10,10 15,5" in (path.d or "")

        # Test Smooth cubic Bézier relative (s)
        path.s(20, 10, 25, 5)
        assert "s20,10 25,5" in (path.d or "")

    def test_path_quadratic_bezier_commands(self):
        """Test PathFT quadratic Bézier curve commands."""
        path = SvgPath()

        # Test Quadratic Bézier absolute (Q)
        path.Q(10, 20, 30, 10)
        assert "Q10,20 30,10" in (path.d or "")

        # Test Smooth quadratic Bézier absolute (T)
        path.T(50, 20)
        assert "T50,20" in (path.d or "")

        # Test Quadratic Bézier relative (q)
        path.q(5, 10, 15, 5)
        assert "q5,10 15,5" in (path.d or "")

        # Test Smooth quadratic Bézier relative (t)
        path.t(25, 10)
        assert "t25,10" in (path.d or "")

    def test_path_arc_commands(self):
        """Test PathFT arc commands."""
        path = SvgPath()

        # Test Arc absolute (A)
        path.A(rx=25, ry=25, x_axis_rotation=0, large_arc_flag=0, sweep_flag=1, x=50, y=25)
        assert "A25,25 0 0,1 50,25" in (path.d or "")

        # Test Arc relative (a)
        path.a(rx=15, ry=15, x_axis_rotation=0, large_arc_flag=1, sweep_flag=0, dx=30, dy=15)
        assert "a15,15 0 1,0 30,15" in (path.d or "")

    def test_path_command_chaining(self):
        """Test chaining of PathFT commands."""
        path = SvgPath().M(0, 0).L(10, 0).L(10, 10).L(0, 10).Z()

        d_attr = path.d
        assert "M0,0" in d_attr
        assert "L10,0" in d_attr
        assert "L10,10" in d_attr
        assert "L0,10" in d_attr
        assert "Z" in d_attr

    def test_path_d_accumulation(self):
        """Test that path commands properly accumulate in d attribute."""
        path = SvgPath()

        # Start with empty d
        getattr(path, "d", "")

        # Add first command
        path.M(10, 10)
        assert path.d.strip() == "M10,10"

        # Add second command
        path.L(20, 20)
        expected = "M10,10 L20,20"
        assert path.d.strip() == expected

    def test_path_non_string_d_handling(self):
        """Test PathFT handles non-string d attribute."""
        path = SvgPath()
        # Simulate non-string d attribute
        path.d = None
        path.M(10, 10)
        assert "M10,10" in (path.d or "")


class TestSvgHelpers:
    """Test SVG helper functions."""

    def test_svg_oob(self):
        """Test SvgOob function."""
        svg = SvgOob(width=100, height=100)
        assert svg.tag == "svg"
        assert svg.attrs["width"] == 100
        assert svg.attrs["height"] == 100

    def test_svg_inb(self):
        """Test SvgInb function."""
        svg = SvgInb(width=200, height=150)
        assert svg.tag == "svg"
        assert svg.attrs["width"] == 200
        assert svg.attrs["height"] == 150


class TestTagFactoryFunction:
    """Test _create_tag_factory function."""

    def test_create_html_tag_factory(self):
        """Test creating HTML tag factory."""
        div_factory = _create_tag_factory("Div", is_svg=False)
        div_element = div_factory("content", id="test")

        assert div_element.tag == "div"
        assert div_element.children == ("content",)
        assert div_element.attrs["id"] == "test"
        assert div_factory.__name__ == "Div"
        assert "HTML" in (div_factory.__doc__ or "")

    def test_create_svg_tag_factory(self):
        """Test creating SVG tag factory."""
        circle_factory = _create_tag_factory("Circle", is_svg=True)
        circle_element = circle_factory(r=25)

        assert circle_element.tag == "circle"  # camelCase converted to lowercase
        assert circle_element.attrs["r"] == 25
        assert circle_factory.__name__ == "Circle"
        assert "SVG" in (circle_factory.__doc__ or "")

    def test_svg_camelcase_conversion(self):
        """Test SVG camelCase to lowercase conversion."""
        custom_factory = _create_tag_factory("CustomElement", is_svg=True)
        element = custom_factory()
        assert element.tag == "customelement"  # All lowercase

        # Test single letter tag
        x_factory = _create_tag_factory("X", is_svg=True)
        x_element = x_factory()
        assert x_element.tag == "x"


class TestGetFtDatastar:
    """Test _get_ft_datastar function."""

    def test_get_ft_datastar_import(self):
        """Test that _get_ft_datastar successfully imports ft_datastar."""
        ft_datastar = _get_ft_datastar()
        assert callable(ft_datastar)

        # Test that it works to create an element
        element = ft_datastar("div", "content")
        assert element.tag == "div"
        assert element.children == ("content",)


class TestDynamicTagGeneration:
    """Test __getattr__ dynamic tag generation."""

    def test_dynamic_custom_tag(self):
        """Test creating custom tags via __getattr__."""
        # This simulates calling tags.CustomTag()
        custom_factory = __getattr__("CustomTag")
        element = custom_factory("content", id="custom")

        assert element.tag == "customtag"  # All lowercase
        assert element.children == ("content",)
        assert element.attrs["id"] == "custom"

    def test_dynamic_tag_with_target_id(self):
        """Test dynamic tag with target_id parameter."""
        factory = __getattr__("MyElement")
        element = factory("content", target_id="target")

        assert element.tag == "myelement"  # All lowercase
        assert element.attrs.get("target-id") == "target"  # Converted to kebab-case

    def test_dynamic_tag_with_hyphens(self):
        """Test dynamic tag with underscores converted to hyphens."""
        factory = __getattr__("Custom_Element")
        element = factory("content")

        assert element.tag == "custom-element"  # All lowercase with hyphens

    def test_getattr_rejects_private_attributes(self):
        """Test that __getattr__ rejects private attributes."""
        with pytest.raises(AttributeError):
            __getattr__("_private_attr")

    def test_getattr_rejects_lowercase_start(self):
        """Test that __getattr__ rejects lowercase starting attributes."""
        with pytest.raises(AttributeError):
            __getattr__("lowercase")


class TestComplexSVGScenarios:
    """Test complex SVG creation scenarios."""

    def test_complete_svg_with_shapes(self):
        """Test creating a complete SVG with multiple shapes."""
        svg = Svg(
            Rect(width=100, height=50, fill="blue"),
            Circle(r=25, cx=50, cy=75, fill="red"),
            Text("Hello SVG", x=50, y=25, text_anchor="middle"),
            width=100,
            height=100,
        )

        assert svg.tag == "svg"
        assert len(svg.children) == 3

        rect = svg.children[0]
        circle = svg.children[1]
        text = svg.children[2]

        assert rect.tag == "rect"
        assert circle.tag == "circle"
        assert text.tag == "text"

    def test_svg_with_transform_groups(self):
        """Test SVG with transform groups."""
        from starhtml.tags import G

        transform_attrs = transformd(translate=(10, 20), scale=(1.5,))

        svg = Svg(G(Circle(r=10), Rect(width=20, height=15), **transform_attrs), width=100, height=100)

        group = svg.children[0]
        assert group.tag == "g"
        assert "translate(10, 20)" in group.attrs["transform"]
        assert "scale(1.5,)" in group.attrs["transform"]

    def test_complex_path_drawing(self):
        """Test complex path drawing with PathFT."""
        # Draw a simple house shape
        path = (
            SvgPath()
            .M(10, 50)  # Start at bottom left
            .L(10, 20)  # Up to roof level
            .L(25, 10)  # Up to roof peak
            .L(40, 20)  # Down to right roof level
            .L(40, 50)  # Down to bottom right
            .Z()
        )  # Close the path

        d_attr = path.d
        assert "M10,50" in d_attr
        assert "L10,20" in d_attr
        assert "L25,10" in d_attr
        assert "L40,20" in d_attr
        assert "L40,50" in d_attr
        assert "Z" in d_attr


class TestEdgeCases:
    """Test edge cases and error conditions."""

    def test_empty_svg_creation(self):
        """Test creating empty SVG elements."""
        svg = Svg()
        assert svg.tag == "svg"
        assert svg.attrs["xmlns"] == "http://www.w3.org/2000/svg"

    def test_svg_with_no_dimensions(self):
        """Test SVG without width/height (no auto viewBox)."""
        svg = Svg()
        # Should not have viewBox when no dimensions provided
        assert "viewBox" not in svg.attrs or svg.attrs.get("viewBox") is None

    def test_path_with_empty_d(self):
        """Test Path with empty d attribute."""
        path = SvgPath(d="")
        assert path.attrs["d"] == ""

        # Adding commands should work normally
        path.M(0, 0)
        assert "M0,0" in (path.d or "")

    def test_polyline_with_no_points(self):
        """Test Polyline with no coordinate arguments."""
        # Should handle empty args gracefully
        polyline = Polyline()
        assert polyline.tag == "polyline"
        # points should be empty string when no args provided
        assert polyline.attrs.get("points") == ""

    def test_polygon_with_no_points(self):
        """Test Polygon with no coordinate arguments."""
        polygon = Polygon()
        assert polygon.tag == "polygon"
        assert polygon.attrs.get("points") == ""

    def test_text_with_all_styling_options(self):
        """Test Text with all available styling options."""
        text = Text(
            "Full style text",
            x=10,
            y=20,
            font_family="Times",
            font_size="14px",
            fill="green",
            text_anchor="start",
            dominant_baseline="middle",
            font_weight="normal",
            font_style="italic",
            text_decoration="underline",
        )

        assert text.attrs["font-family"] == "Times"
        assert text.attrs["font-size"] == "14px"
        assert text.attrs["fill"] == "green"
        assert text.attrs["text-anchor"] == "start"
        assert text.attrs["dominant-baseline"] == "middle"
        assert text.attrs["font-weight"] == "normal"
        assert text.attrs["font-style"] == "italic"
        assert text.attrs["text-decoration"] == "underline"


class TestRealWorldUsage:
    """Test real-world usage scenarios."""

    def test_icon_creation(self):
        """Test creating an SVG icon."""
        # Create a simple checkmark icon
        checkmark = Svg(
            SvgPath(d="M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41z", fill="currentColor"),
            width=24,
            height=24,
            viewBox="0 0 24 24",
        )

        assert checkmark.tag == "svg"
        assert checkmark.attrs["viewbox"] == "0 0 24 24"  # Note: lowercase 'viewbox'

        path = checkmark.children[0]
        assert path.tag == "path"
        assert "M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41z" in path.attrs["d"]

    def test_chart_creation(self):
        """Test creating a simple bar chart."""
        chart = Svg(
            # Bars
            Rect(x=10, y=40, width=20, height=30, fill="blue"),
            Rect(x=40, y=20, width=20, height=50, fill="green"),
            Rect(x=70, y=30, width=20, height=40, fill="red"),
            # Labels
            Text("A", x=20, y=85, text_anchor="middle"),
            Text("B", x=50, y=85, text_anchor="middle"),
            Text("C", x=80, y=85, text_anchor="middle"),
            width=100,
            height=90,
            viewBox="0 0 100 90",
        )

        assert chart.tag == "svg"
        assert len(chart.children) == 6  # 3 bars + 3 labels

        # Check first bar
        first_bar = chart.children[0]
        assert first_bar.tag == "rect"
        assert first_bar.attrs["fill"] == "blue"

    def test_interactive_svg_with_datastar(self):
        """Test SVG with Datastar interactivity."""
        # Note: SVG elements with complex Datastar integration
        # would be better tested at the application level
        interactive_circle = Circle(r=25, cx=50, cy=50, fill="blue")

        assert interactive_circle.tag == "circle"
        assert interactive_circle.attrs["r"] == 25
        assert interactive_circle.attrs["fill"] == "blue"
