"""Tests for StarHTML SVG module functionality"""

from starhtml.svg import (
    Circle,
    Defs,
    Ellipse,
    G,  # Test some generated SVG elements
    Line,
    Path,
    PathFT,
    Polygon,
    Polyline,
    Rect,
    Svg,
    SvgInb,
    SvgOob,
    Text,
    Use,
    ft_svg,
    transformd,
)


class TestSvgBasics:
    def test_ft_svg_basic(self):
        """Test basic ft_svg function"""
        result = ft_svg("rect", width=100, height=50)
        assert result.tag == "rect"
        assert result.attrs["width"] == 100
        assert result.attrs["height"] == 50

    def test_ft_svg_with_svg_attrs(self):
        """Test ft_svg with SVG-specific attributes"""
        result = ft_svg("rect", transform="translate(10,20)", opacity=0.5)
        assert result.attrs["transform"] == "translate(10,20)"
        assert result.attrs["opacity"] == 0.5

    def test_svg_basic(self):
        """Test basic Svg creation"""
        result = Svg()
        assert result.tag == "svg"
        assert result.attrs["xmlns"] == "http://www.w3.org/2000/svg"

    def test_svg_with_dimensions(self):
        """Test Svg with width and height"""
        result = Svg(width=100, height=200)
        assert result.attrs["width"] == 100
        assert result.attrs["height"] == 200
        # Should auto-generate viewBox if provided (could be viewBox or viewbox)
        assert result.attrs.get("viewBox") is not None or result.attrs.get("viewbox") is not None

    def test_svg_with_h_w_shortcuts(self):
        """Test Svg with h and w shortcuts"""
        result = Svg(h=150, w=300)
        assert result.attrs["height"] == 150
        assert result.attrs["width"] == 300

    def test_svg_with_custom_viewbox(self):
        """Test Svg with custom viewBox"""
        result = Svg(width=100, height=200, viewBox="0 0 50 100")
        # Check for viewBox in both possible forms
        assert result.attrs.get("viewBox") == "0 0 50 100" or result.attrs.get("viewbox") == "0 0 50 100"


class TestBasicShapes:
    def test_rect_basic(self):
        """Test basic rectangle creation"""
        result = Rect(100, 50)
        assert result.tag == "rect"
        assert result.attrs["width"] == 100
        assert result.attrs["height"] == 50
        assert result.attrs["x"] == 0
        assert result.attrs["y"] == 0

    def test_rect_with_position(self):
        """Test rectangle with position"""
        result = Rect(100, 50, x=10, y=20)
        assert result.attrs["x"] == 10
        assert result.attrs["y"] == 20

    def test_rect_with_styling(self):
        """Test rectangle with fill and stroke"""
        result = Rect(100, 50, fill="red", stroke="blue", stroke_width=2)
        assert result.attrs.get("fill") == "red"
        assert result.attrs.get("stroke") == "blue"
        # Check that stroke_width is set somehow (could be stroke_width or stroke-width)
        assert result.attrs.get("stroke_width") == 2 or result.attrs.get("stroke-width") == 2

    def test_rect_with_rounded_corners(self):
        """Test rectangle with rounded corners"""
        result = Rect(100, 50, rx=5, ry=10)
        assert result.attrs["rx"] == 5
        assert result.attrs["ry"] == 10

    def test_circle_basic(self):
        """Test basic circle creation"""
        result = Circle(25)
        assert result.tag == "circle"
        assert result.attrs["r"] == 25
        assert result.attrs["cx"] == 0
        assert result.attrs["cy"] == 0

    def test_circle_with_position(self):
        """Test circle with position"""
        result = Circle(25, cx=50, cy=100)
        assert result.attrs["cx"] == 50
        assert result.attrs["cy"] == 100

    def test_ellipse_basic(self):
        """Test basic ellipse creation"""
        result = Ellipse(30, 20)
        assert result.tag == "ellipse"
        assert result.attrs["rx"] == 30
        assert result.attrs["ry"] == 20
        assert result.attrs["cx"] == 0
        assert result.attrs["cy"] == 0

    def test_ellipse_with_position(self):
        """Test ellipse with position"""
        result = Ellipse(30, 20, cx=40, cy=60)
        assert result.attrs["cx"] == 40
        assert result.attrs["cy"] == 60


class TestTransforms:
    def test_transformd_translate(self):
        """Test transformd with translate"""
        result = transformd(translate=(10, 20))
        assert result["transform"] == "translate(10, 20)"

    def test_transformd_scale(self):
        """Test transformd with scale"""
        result = transformd(scale=(2, 3))
        assert result["transform"] == "scale(2, 3)"

    def test_transformd_rotate(self):
        """Test transformd with rotate"""
        result = transformd(rotate=(45, 50, 50))
        assert result["transform"] == "rotate(45,50,50)"

    def test_transformd_skew(self):
        """Test transformd with skew"""
        result = transformd(skewX=15, skewY=25)
        assert result["transform"] == "skewX(15) skewY(25)"

    def test_transformd_matrix(self):
        """Test transformd with matrix"""
        result = transformd(matrix=(1, 0, 0, 1, 10, 20))
        assert result["transform"] == "matrix(1, 0, 0, 1, 10, 20)"

    def test_transformd_multiple(self):
        """Test transformd with multiple transforms"""
        result = transformd(translate=(10, 20), scale=(2, 2))
        assert "translate(10, 20)" in result["transform"]
        assert "scale(2, 2)" in result["transform"]

    def test_transformd_empty(self):
        """Test transformd with no parameters"""
        result = transformd()
        assert result == {}


class TestLinesAndPaths:
    def test_line_basic(self):
        """Test basic line creation"""
        result = Line(0, 0, 100, 50)
        assert result.tag == "line"
        assert result.attrs["x1"] == 0
        assert result.attrs["y1"] == 0
        assert result.attrs["x2"] == 100
        assert result.attrs["y2"] == 50
        assert result.attrs.get("stroke") == "black"
        # Check stroke_width is set (could be stroke_width or stroke-width)
        assert result.attrs.get("stroke_width") == 1 or result.attrs.get("stroke-width") == 1

    def test_line_with_w_shortcut(self):
        """Test line with w shortcut for stroke_width"""
        result = Line(0, 0, 100, 50, w=3)
        # Check that stroke_width is set somehow
        assert result.attrs.get("stroke_width") == 3 or result.attrs.get("stroke-width") == 3

    def test_polyline_with_args(self):
        """Test polyline with coordinate arguments"""
        result = Polyline((0, 0), (10, 20), (30, 15))
        assert result.tag == "polyline"
        assert result.attrs["points"] == "0,0 10,20 30,15"

    def test_polyline_with_points(self):
        """Test polyline with points parameter"""
        result = Polyline(points="0,0 10,20 30,15")
        assert result.attrs["points"] == "0,0 10,20 30,15"

    def test_polygon_with_args(self):
        """Test polygon with coordinate arguments"""
        result = Polygon((0, 0), (10, 20), (30, 15))
        assert result.tag == "polygon"
        assert result.attrs["points"] == "0,0 10,20 30,15"

    def test_polygon_with_points(self):
        """Test polygon with points parameter"""
        result = Polygon(points="0,0 10,20 30,15")
        assert result.attrs["points"] == "0,0 10,20 30,15"


class TestText:
    def test_text_basic(self):
        """Test basic text creation"""
        result = Text("Hello World")
        assert result.tag == "text"
        assert "Hello World" in result.children
        assert result.attrs["x"] == 0
        assert result.attrs["y"] == 0

    def test_text_with_position(self):
        """Test text with position"""
        result = Text("Hello", x=10, y=20)
        assert result.attrs["x"] == 10
        assert result.attrs["y"] == 20

    def test_text_with_styling(self):
        """Test text with font styling"""
        result = Text("Hello", font_family="Arial", font_size=16, fill="red")
        # Check font attributes (could be font_family or font-family, etc.)
        assert result.attrs.get("font_family") == "Arial" or result.attrs.get("font-family") == "Arial"
        assert result.attrs.get("font_size") == 16 or result.attrs.get("font-size") == 16
        assert result.attrs.get("fill") == "red"

    def test_text_with_alignment(self):
        """Test text with text alignment"""
        result = Text("Hello", text_anchor="middle", dominant_baseline="central")
        # Check alignment attributes (could use underscores or hyphens)
        assert result.attrs.get("text_anchor") == "middle" or result.attrs.get("text-anchor") == "middle"
        assert result.attrs.get("dominant_baseline") == "central" or result.attrs.get("dominant-baseline") == "central"


class TestPathFT:
    def test_path_basic(self):
        """Test basic path creation"""
        result = Path()
        assert result.tag == "path"
        assert isinstance(result, PathFT)

    def test_path_with_d(self):
        """Test path with d attribute"""
        result = Path(d="M10,10 L20,20")
        assert result.attrs["d"] == "M10,10 L20,20"

    def test_path_ft_move_to(self):
        """Test PathFT M command"""
        path = Path()
        result = path.M(10, 20)
        assert "M10 20" in result.d  # type: ignore[attr-defined]
        assert result is path  # Should return self

    def test_path_ft_line_to(self):
        """Test PathFT L command"""
        path = Path()
        result = path.M(10, 20).L(30, 40)
        d_str = result.d  # type: ignore[attr-defined]
        assert "M10 20" in d_str and "L30 40" in d_str

    def test_path_ft_horizontal_line(self):
        """Test PathFT H command"""
        path = Path()
        result = path.M(10, 20).H(50)
        d_str = result.d  # type: ignore[attr-defined]
        assert "M10 20" in d_str and "H50" in d_str

    def test_path_ft_vertical_line(self):
        """Test PathFT V command"""
        path = Path()
        result = path.M(10, 20).V(60)
        d_str = result.d  # type: ignore[attr-defined]
        assert "M10 20" in d_str and "V60" in d_str

    def test_path_ft_close_path(self):
        """Test PathFT Z command"""
        path = Path()
        result = path.M(10, 20).L(30, 40).Z()
        d_str = result.d  # type: ignore[attr-defined]
        assert "M10 20" in d_str and "L30 40" in d_str and "Z" in d_str

    def test_path_ft_cubic_bezier(self):
        """Test PathFT C command"""
        path = Path()
        result = path.M(10, 20).C(15, 25, 25, 35, 30, 40)
        d_str = result.d  # type: ignore[attr-defined]
        assert "M10 20" in d_str and "C15 25 25 35 30 40" in d_str

    def test_path_ft_smooth_cubic(self):
        """Test PathFT S command"""
        path = Path()
        result = path.M(10, 20).S(25, 35, 30, 40)
        d_str = result.d  # type: ignore[attr-defined]
        assert "M10 20" in d_str and "S25 35 30 40" in d_str

    def test_path_ft_quadratic_bezier(self):
        """Test PathFT Q command"""
        path = Path()
        result = path.M(10, 20).Q(20, 30, 30, 40)
        d_str = result.d  # type: ignore[attr-defined]
        assert "M10 20" in d_str and "Q20 30 30 40" in d_str

    def test_path_ft_smooth_quadratic(self):
        """Test PathFT T command"""
        path = Path()
        result = path.M(10, 20).T(30, 40)
        d_str = result.d  # type: ignore[attr-defined]
        assert "M10 20" in d_str and "T30 40" in d_str

    def test_path_ft_arc(self):
        """Test PathFT A command"""
        path = Path()
        result = path.M(10, 20).A(5, 10, 0, 1, 0, 30, 40)
        d_str = result.d  # type: ignore[attr-defined]
        assert "M10 20" in d_str and "A5 10 0 1 0 30 40" in d_str

    def test_path_ft_initial_command(self):
        """Test PathFT with no initial d attribute"""
        path = Path()
        # Initial command should work when d is not a string
        result = path.M(10, 20)
        assert "M10 20" in result.d  # type: ignore[attr-defined]


class TestGeneratedElements:
    def test_g_element(self):
        """Test generated G element"""
        result = G("content")
        assert result.tag == "g"
        assert "content" in result.children

    def test_defs_element(self):
        """Test generated Defs element"""
        result = Defs("content")
        assert result.tag == "defs"

    def test_use_element(self):
        """Test generated Use element"""
        result = Use(href="#myshape")
        assert result.tag == "use"
        assert result.attrs["href"] == "#myshape"


class TestSvgWrappers:
    def test_svg_oob(self):
        """Test SvgOob wrapper"""
        result = SvgOob(width=100, height=200)
        assert result.tag == "svg"
        assert result.attrs["width"] == 100
        assert result.attrs["height"] == 200

    def test_svg_inb(self):
        """Test SvgInb wrapper"""
        result = SvgInb(width=150, height=250)
        assert result.tag == "svg"
        assert result.attrs["width"] == 150
        assert result.attrs["height"] == 250
