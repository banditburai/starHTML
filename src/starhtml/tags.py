"""All HTML and SVG tag definitions for StarHTML framework."""

from typing import Any

from fastcore.xml import FT

_HTML_TAG_NAMES = [
    "A",
    "Abbr",
    "Address",
    "Area",
    "Article",
    "Aside",
    "Audio",
    "B",
    "Base",
    "Bdi",
    "Bdo",
    "Blockquote",
    "Body",
    "Br",
    "Button",
    "Canvas",
    "Caption",
    "Cite",
    "Code",
    "Col",
    "Colgroup",
    "Data",
    "Datalist",
    "Dd",
    "Del",
    "Details",
    "Dfn",
    "Dialog",
    "Div",
    "Dl",
    "Dt",
    "Em",
    "Embed",
    "Fencedframe",
    "Fieldset",
    "Figcaption",
    "Figure",
    "Footer",
    "Form",
    "H1",
    "H2",
    "H3",
    "H4",
    "H5",
    "H6",
    "Head",
    "Header",
    "Hgroup",
    "Hr",
    "Html",
    "I",
    "Iframe",
    "Img",
    "Input",
    "Ins",
    "Kbd",
    "Label",
    "Legend",
    "Li",
    "Link",
    "Main",
    "Map",
    "Mark",
    "Menu",
    "Meta",
    "Meter",
    "Nav",
    "Noscript",
    "Object",
    "Ol",
    "Optgroup",
    "Option",
    "Output",
    "P",
    "Picture",
    "PortalExperimental",
    "Pre",
    "Progress",
    "Q",
    "Rp",
    "Rt",
    "Ruby",
    "S",
    "Samp",
    "Script",
    "Search",
    "Section",
    "Select",
    "Slot",
    "Small",
    "Source",
    "Span",
    "Strong",
    "Style",
    "Sub",
    "Summary",
    "Sup",
    "Table",
    "Tbody",
    "Td",
    "Template",
    "Textarea",
    "Tfoot",
    "Th",
    "Thead",
    "Time",
    "Title",
    "Tr",
    "Track",
    "U",
    "Ul",
    "Var",
    "Video",
    "Wbr",
]

_SVG_TAG_NAMES = [
    # Note: Custom-defined tags like Svg, Rect, Path, etc., are listed here
    # to be included in __all__, but their functions will be defined manually below.
    "Svg",
    "G",
    "Rect",
    "Circle",
    "Ellipse",
    "Line",
    "Polyline",
    "Polygon",
    "Text",
    "SvgPath",
    "AltGlyph",
    "AltGlyphDef",
    "AltGlyphItem",
    "Animate",
    "AnimateColor",
    "AnimateMotion",
    "AnimateTransform",
    "ClipPath",
    "Color_profile",
    "Cursor",
    "Defs",
    "Desc",
    "FeBlend",
    "FeColorMatrix",
    "FeComponentTransfer",
    "FeComposite",
    "FeConvolveMatrix",
    "FeDiffuseLighting",
    "FeDisplacementMap",
    "FeDistantLight",
    "FeFlood",
    "FeFuncA",
    "FeFuncB",
    "FeFuncG",
    "FeFuncR",
    "FeGaussianBlur",
    "FeImage",
    "FeMerge",
    "FeMergeNode",
    "FeMorphology",
    "FeOffset",
    "FePointLight",
    "FeSpecularLighting",
    "FeSpotLight",
    "FeTile",
    "FeTurbulence",
    "Filter",
    "Font",
    "Font_face",
    "Font_face_format",
    "Font_face_name",
    "Font_face_src",
    "Font_face_uri",
    "ForeignObject",
    "Glyph",
    "GlyphRef",
    "Hkern",
    "Image",
    "LinearGradient",
    "Marker",
    "Mask",
    "Metadata",
    "Missing_glyph",
    "Mpath",
    "Pattern",
    "RadialGradient",
    "Set",
    "Stop",
    "Switch",
    "Symbol",
    "TextPath",
    "Tref",
    "Tspan",
    "Use",
    "View",
    "Vkern",
    "Template",
]

__all__ = [
    *_HTML_TAG_NAMES,
    *_SVG_TAG_NAMES,
    "ft_svg",
    "transformd",
    "SvgOob",
    "SvgInb",
    "PathFT",
]


def _get_ft_datastar():
    """Lazy import ft_datastar to avoid circular dependencies"""
    from .html import ft_datastar

    return ft_datastar


def _create_tag_factory(tag_name: str, is_svg: bool = False):
    # SVG tags are camelCase, HTML tags are lowercase
    processed_tag = (tag_name[0].lower() + tag_name[1:]) if is_svg and len(tag_name) > 1 else tag_name.lower()

    def _tag_func(*c: Any, **kwargs: Any) -> FT:
        ft_datastar = _get_ft_datastar()
        return ft_datastar(processed_tag, *c, **kwargs)

    _tag_func.__name__ = tag_name
    _tag_func.__qualname__ = tag_name
    _tag_func.__doc__ = f"Create a <{processed_tag}> {'SVG' if is_svg else 'HTML'} element."

    return _tag_func


_g: dict[str, Any] = globals()

for tag_name in _HTML_TAG_NAMES:
    _g[tag_name] = _create_tag_factory(tag_name, is_svg=False)

for tag_name in _SVG_TAG_NAMES:
    if tag_name not in _g:  # Avoid overriding custom functions like Svg, Rect, etc.
        _g[tag_name] = _create_tag_factory(tag_name, is_svg=True)

# ============================================================================
# Enhanced SVG Components & Helpers
# ============================================================================


def ft_svg(
    tag: str,
    *c: Any,
    transform: str | None = None,
    opacity: int | float | str | None = None,
    clip: str | None = None,
    mask: str | None = None,
    filter: str | None = None,
    vector_effect: str | None = None,
    pointer_events: str | None = None,
    **kwargs: Any,
) -> FT:
    """Base factory for creating SVG elements with common SVG-specific attributes."""
    ft_datastar = _get_ft_datastar()
    return ft_datastar(
        tag,
        *c,
        transform=transform,
        opacity=opacity,
        clip=clip,
        mask=mask,
        filter=filter,
        vector_effect=vector_effect,
        pointer_events=pointer_events,
        **kwargs,
    )


def Svg(
    *args: Any,
    viewBox: str | None = None,
    h: int | str | None = None,
    w: int | str | None = None,
    height: int | str | None = None,
    width: int | str | None = None,
    xmlns: str = "http://www.w3.org/2000/svg",
    **kwargs: Any,
) -> FT:
    """Creates an <svg> element with automatic xmlns and viewBox handling."""
    if h:
        height = h
    if w:
        width = w
    if not viewBox and height and width:
        viewBox = f"0 0 {width} {height}"
    return ft_svg("svg", *args, xmlns=xmlns, viewBox=viewBox, height=height, width=width, **kwargs)


def Rect(width, height, x=0, y=0, fill=None, stroke=None, stroke_width=None, rx=None, ry=None, **kwargs):
    """A standard SVG `rect` element."""
    return ft_svg(
        "rect",
        width=width,
        height=height,
        x=x,
        y=y,
        fill=fill,
        stroke=stroke,
        stroke_width=stroke_width,
        rx=rx,
        ry=ry,
        **kwargs,
    )


def Circle(r, cx=0, cy=0, fill=None, stroke=None, stroke_width=None, **kwargs):
    """A standard SVG `circle` element."""
    return ft_svg("circle", r=r, cx=cx, cy=cy, fill=fill, stroke=stroke, stroke_width=stroke_width, **kwargs)


def Ellipse(rx, ry, cx=0, cy=0, fill=None, stroke=None, stroke_width=None, **kwargs):
    """A standard SVG `ellipse` element."""
    return ft_svg("ellipse", rx=rx, ry=ry, cx=cx, cy=cy, fill=fill, stroke=stroke, stroke_width=stroke_width, **kwargs)


def Line(x1, y1, x2=0, y2=0, stroke="black", w=None, stroke_width=1, **kwargs):
    """A standard SVG `line` element."""
    if w:
        stroke_width = w
    return ft_svg("line", x1=x1, y1=y1, x2=x2, y2=y2, stroke=stroke, stroke_width=stroke_width, **kwargs)


def Polyline(*args, points=None, fill=None, stroke=None, stroke_width=None, **kwargs):
    """A standard SVG `polyline` element."""
    if points is None:
        points = " ".join(f"{x},{y}" for x, y in args)
    return ft_svg("polyline", points=points, fill=fill, stroke=stroke, stroke_width=stroke_width, **kwargs)


def Polygon(*args, points=None, fill=None, stroke=None, stroke_width=None, **kwargs):
    """A standard SVG `polygon` element."""
    if points is None:
        points = " ".join(f"{x},{y}" for x, y in args)
    return ft_svg("polygon", points=points, fill=fill, stroke=stroke, stroke_width=stroke_width, **kwargs)


def Text(
    *args,
    x=0,
    y=0,
    font_family=None,
    font_size=None,
    fill=None,
    text_anchor=None,
    dominant_baseline=None,
    font_weight=None,
    font_style=None,
    text_decoration=None,
    **kwargs,
):
    """A standard SVG `text` element."""
    return ft_svg(
        "text",
        *args,
        x=x,
        y=y,
        font_family=font_family,
        font_size=font_size,
        fill=fill,
        text_anchor=text_anchor,
        dominant_baseline=dominant_baseline,
        font_weight=font_weight,
        font_style=font_style,
        text_decoration=text_decoration,
        **kwargs,
    )


def transformd(
    translate: tuple | None = None,
    scale: tuple | None = None,
    rotate: tuple | None = None,
    skewX: int | float | None = None,
    skewY: int | float | None = None,
    matrix: tuple | None = None,
) -> dict[str, str]:
    """Create a dictionary for use with the `transform` SVG attribute."""
    funcs = []
    if translate is not None:
        funcs.append(f"translate{translate}")
    if scale is not None:
        funcs.append(f"scale{scale}")
    if rotate is not None:
        funcs.append(f"rotate({','.join(map(str, rotate))})")
    if skewX is not None:
        funcs.append(f"skewX({skewX})")
    if skewY is not None:
        funcs.append(f"skewY({skewY})")
    if matrix is not None:
        funcs.append(f"matrix{matrix}")
    return dict(transform=" ".join(funcs)) if funcs else {}


class PathFT(FT):
    """A special FT class for SVG path elements with builder methods for both absolute and relative commands."""

    def _append_cmd(self, cmd: str) -> "PathFT":
        current_d = getattr(self, "d", "")
        if not isinstance(current_d, str):
            current_d = ""

        self.d = f"{current_d} {cmd}".strip()
        return self

    # --- Absolute Commands (Uppercase) ---
    def M(self, x: int | float, y: int | float) -> "PathFT":
        "Move to (absolute)."
        return self._append_cmd(f"M{x},{y}")

    def L(self, x: int | float, y: int | float) -> "PathFT":
        "Line to (absolute)."
        return self._append_cmd(f"L{x},{y}")

    def H(self, x: int | float) -> "PathFT":
        "Horizontal line to (absolute)."
        return self._append_cmd(f"H{x}")

    def V(self, y: int | float) -> "PathFT":
        "Vertical line to (absolute)."
        return self._append_cmd(f"V{y}")

    def C(
        self, x1: int | float, y1: int | float, x2: int | float, y2: int | float, x: int | float, y: int | float
    ) -> "PathFT":
        "Cubic Bézier curve (absolute)."
        return self._append_cmd(f"C{x1},{y1} {x2},{y2} {x},{y}")

    def S(self, x2: int | float, y2: int | float, x: int | float, y: int | float) -> "PathFT":
        "Smooth cubic Bézier curve (absolute)."
        return self._append_cmd(f"S{x2},{y2} {x},{y}")

    def Q(self, x1: int | float, y1: int | float, x: int | float, y: int | float) -> "PathFT":
        "Quadratic Bézier curve (absolute)."
        return self._append_cmd(f"Q{x1},{y1} {x},{y}")

    def T(self, x: int | float, y: int | float) -> "PathFT":
        "Smooth quadratic Bézier curve (absolute)."
        return self._append_cmd(f"T{x},{y}")

    def A(
        self,
        rx: int | float,
        ry: int | float,
        x_axis_rotation: int | float,
        large_arc_flag: int,
        sweep_flag: int,
        x: int | float,
        y: int | float,
    ) -> "PathFT":
        "Elliptical Arc (absolute)."
        return self._append_cmd(f"A{rx},{ry} {x_axis_rotation} {large_arc_flag},{sweep_flag} {x},{y}")

    def Z(self) -> "PathFT":
        "Close path."
        return self._append_cmd("Z")

    # --- Relative Commands (Lowercase) ---
    def m(self, dx: int | float, dy: int | float) -> "PathFT":
        "Move to (relative)."
        return self._append_cmd(f"m{dx},{dy}")

    def l(self, dx: int | float, dy: int | float) -> "PathFT":
        "Line to (relative)."
        return self._append_cmd(f"l{dx},{dy}")

    def h(self, dx: int | float) -> "PathFT":
        "Horizontal line to (relative)."
        return self._append_cmd(f"h{dx}")

    def v(self, dy: int | float) -> "PathFT":
        "Vertical line to (relative)."
        return self._append_cmd(f"v{dy}")

    def c(
        self, dx1: int | float, dy1: int | float, dx2: int | float, dy2: int | float, dx: int | float, dy: int | float
    ) -> "PathFT":
        "Cubic Bézier curve (relative)."
        return self._append_cmd(f"c{dx1},{dy1} {dx2},{dy2} {dx},{dy}")

    def s(self, dx2: int | float, dy2: int | float, dx: int | float, dy: int | float) -> "PathFT":
        "Smooth cubic Bézier curve (relative)."
        return self._append_cmd(f"s{dx2},{dy2} {dx},{dy}")

    def q(self, dx1: int | float, dy1: int | float, dx: int | float, dy: int | float) -> "PathFT":
        "Quadratic Bézier curve (relative)."
        return self._append_cmd(f"q{dx1},{dy1} {dx},{dy}")

    def t(self, dx: int | float, dy: int | float) -> "PathFT":
        "Smooth quadratic Bézier curve (relative)."
        return self._append_cmd(f"t{dx},{dy}")

    def a(
        self,
        rx: int | float,
        ry: int | float,
        x_axis_rotation: int | float,
        large_arc_flag: int,
        sweep_flag: int,
        dx: int | float,
        dy: int | float,
    ) -> "PathFT":
        "Elliptical Arc (relative)."
        return self._append_cmd(f"a{rx},{ry} {x_axis_rotation} {large_arc_flag},{sweep_flag} {dx},{dy}")

    def z(self) -> "PathFT":
        "Close path (relative, equivalent to Z)."
        return self._append_cmd("z")


def SvgPath(d="", fill=None, stroke=None, stroke_width=None, **kwargs):
    """Creates a <path> SVG element, returning a powerful PathFT builder object."""
    return ft_svg("path", d=d, fill=fill, stroke=stroke, stroke_width=stroke_width, ft_cls=PathFT, **kwargs)


def SvgOob(*args, **kwargs):
    """Wraps an SVG shape (simplified for Datastar)."""
    return Svg(*args, **kwargs)


def SvgInb(*args, **kwargs):
    """Wraps an SVG shape (simplified for Datastar)."""
    return Svg(*args, **kwargs)


# ============================================================================
# Dynamic Fallback Tag Generation
# ============================================================================


def __getattr__(tag: str) -> Any:
    """
    Module-level fallback to dynamically create any PascalCase tag.
    This allows for using non-standard or future tags without explicit definition.
    Example: `tags.MyCustomElement()` will create a `<mycustomelement>` tag.
    """
    if tag.startswith("_") or tag[0].islower():
        # This is required to allow Python to find internal names.
        raise AttributeError(f"'{__name__}' object has no attribute '{tag}'")

    tag = tag.replace("_", "-")

    def _f(*c: Any, target_id: str | None = None, **kwargs: Any) -> Any:
        ft_datastar = _get_ft_datastar()
        return ft_datastar(tag, *c, target_id=target_id, **kwargs)

    return _f
