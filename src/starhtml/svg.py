"""Simple SVG FT elements"""

from fastcore.utils import *
from fastcore.meta import delegates
from fastcore.xml import FT
from .common import *
from .components import *
from .xtend import *

__all__ = ['g', 'svg_inb', 'Svg', 'ft_svg', 'Rect', 'Circle', 'Ellipse', 'transformd', 'Line', 'Polyline', 'Polygon', 'Text',
           'PathFT', 'Path', 'SvgOob', 'SvgInb', 'AltGlyph', 'AltGlyphDef', 'AltGlyphItem', 'Animate', 'AnimateColor',
           'AnimateMotion', 'AnimateTransform', 'ClipPath', 'Color_profile', 'Cursor', 'Defs', 'Desc', 'FeBlend',
           'FeColorMatrix', 'FeComponentTransfer', 'FeComposite', 'FeConvolveMatrix', 'FeDiffuseLighting',
           'FeDisplacementMap', 'FeDistantLight', 'FeFlood', 'FeFuncA', 'FeFuncB', 'FeFuncG', 'FeFuncR',
           'FeGaussianBlur', 'FeImage', 'FeMerge', 'FeMergeNode', 'FeMorphology', 'FeOffset', 'FePointLight',
           'FeSpecularLighting', 'FeSpotLight', 'FeTile', 'FeTurbulence', 'Filter', 'Font', 'Font_face',
           'Font_face_format', 'Font_face_name', 'Font_face_src', 'Font_face_uri', 'ForeignObject', 'G', 'Glyph',
           'GlyphRef', 'Hkern', 'Image', 'LinearGradient', 'Marker', 'Mask', 'Metadata', 'Missing_glyph', 'Mpath',
           'Pattern', 'RadialGradient', 'Set', 'Stop', 'Switch', 'Symbol', 'TextPath', 'Tref', 'Tspan', 'Use', 'View',
           'Vkern', 'Template']

_all_ = ['AltGlyph', 'AltGlyphDef', 'AltGlyphItem', 'Animate', 'AnimateColor', 'AnimateMotion', 'AnimateTransform', 'ClipPath', 'Color_profile', 'Cursor', 'Defs', 'Desc', 'FeBlend', 'FeColorMatrix', 'FeComponentTransfer', 'FeComposite', 'FeConvolveMatrix', 'FeDiffuseLighting', 'FeDisplacementMap', 'FeDistantLight', 'FeFlood', 'FeFuncA', 'FeFuncB', 'FeFuncG', 'FeFuncR', 'FeGaussianBlur', 'FeImage', 'FeMerge', 'FeMergeNode', 'FeMorphology', 'FeOffset', 'FePointLight', 'FeSpecularLighting', 'FeSpotLight', 'FeTile', 'FeTurbulence', 'Filter', 'Font', 'Font_face', 'Font_face_format', 'Font_face_name', 'Font_face_src', 'Font_face_uri', 'ForeignObject', 'G', 'Glyph', 'GlyphRef', 'Hkern', 'Image', 'LinearGradient', 'Marker', 'Mask', 'Metadata', 'Missing_glyph', 'Mpath', 'Pattern', 'RadialGradient', 'Set', 'Stop', 'Switch', 'Symbol', 'TextPath', 'Tref', 'Tspan', 'Use', 'View', 'Vkern', 'Template']

g = globals()
for o in _all_: g[o] = partial(ft_datastar, o[0].lower() + o[1:])

def Svg(*args, viewBox=None, h=None, w=None, height=None, width=None, xmlns="http://www.w3.org/2000/svg", **kwargs):
    "An SVG tag; xmlns is added automatically, and viewBox defaults to height and width if not provided"
    if h: height=h
    if w: width=w
    if not viewBox and height and width: viewBox=f'0 0 {width} {height}'
    return ft_svg('svg', *args, xmlns=xmlns, viewBox=viewBox, height=height, width=width, **kwargs)

@delegates(ft_datastar)
def ft_svg(tag: str, *c, transform=None, opacity=None, clip=None, mask=None, filter=None,
           vector_effect=None, pointer_events=None, **kwargs):
    "Create a standard `FT` element with some SVG-specific attrs"
    return ft_datastar(tag, *c, transform=transform, opacity=opacity, clip=clip, mask=mask, filter=filter,
           vector_effect=vector_effect, pointer_events=pointer_events, **kwargs)

@delegates(ft_svg)
def Rect(width, height, x=0, y=0, fill=None, stroke=None, stroke_width=None, rx=None, ry=None, **kwargs):
    "A standard SVG `rect` element"
    return ft_svg('rect', width=width, height=height, x=x, y=y, fill=fill,
                 stroke=stroke, stroke_width=stroke_width, rx=rx, ry=ry, **kwargs)

@delegates(ft_svg)
def Circle(r, cx=0, cy=0, fill=None, stroke=None, stroke_width=None, **kwargs):
    "A standard SVG `circle` element"
    return ft_svg('circle', r=r, cx=cx, cy=cy, fill=fill, stroke=stroke, stroke_width=stroke_width, **kwargs)

@delegates(ft_svg)
def Ellipse(rx, ry, cx=0, cy=0, fill=None, stroke=None, stroke_width=None, **kwargs):
    "A standard SVG `ellipse` element"
    return ft_svg('ellipse', rx=rx, ry=ry, cx=cx, cy=cy, fill=fill, stroke=stroke, stroke_width=stroke_width, **kwargs)

def transformd(translate=None, scale=None, rotate=None, skewX=None, skewY=None, matrix=None):
    "Create an SVG `transform` kwarg dict"
    funcs = []
    if translate is not None: funcs.append(f"translate{translate}")
    if scale is not None: funcs.append(f"scale{scale}")
    if rotate is not None: funcs.append(f"rotate({','.join(map(str,rotate))})")
    if skewX is not None: funcs.append(f"skewX({skewX})")
    if skewY is not None: funcs.append(f"skewY({skewY})")
    if matrix is not None: funcs.append(f"matrix{matrix}")
    return dict(transform=' '.join(funcs)) if funcs else {}

@delegates(ft_svg)
def Line(x1, y1, x2=0, y2=0, stroke='black', w=None, stroke_width=1, **kwargs):
    "A standard SVG `line` element"
    if w: stroke_width=w
    return ft_svg('line', x1=x1, y1=y1, x2=x2, y2=y2, stroke=stroke, stroke_width=stroke_width, **kwargs)

@delegates(ft_svg)
def Polyline(*args, points=None, fill=None, stroke=None, stroke_width=None, **kwargs):
    "A standard SVG `polyline` element"
    if points is None: points = ' '.join(f"{x},{y}" for x, y in args)
    return ft_svg('polyline', points=points, fill=fill, stroke=stroke, stroke_width=stroke_width, **kwargs)

@delegates(ft_svg)
def Polygon(*args, points=None, fill=None, stroke=None, stroke_width=None, **kwargs):
    "A standard SVG `polygon` element"
    if points is None: points = ' '.join(f"{x},{y}" for x, y in args)
    return ft_svg('polygon', points=points, fill=fill, stroke=stroke, stroke_width=stroke_width, **kwargs)

@delegates(ft_svg)
def Text(*args, x=0, y=0, font_family=None, font_size=None, fill=None, text_anchor=None,
         dominant_baseline=None, font_weight=None, font_style=None, text_decoration=None, **kwargs):
    "A standard SVG `text` element"
    return ft_svg('text', *args, x=x, y=y, font_family=font_family, font_size=font_size, fill=fill,
                 text_anchor=text_anchor, dominant_baseline=dominant_baseline, font_weight=font_weight,
                 font_style=font_style, text_decoration=text_decoration, **kwargs)

class PathFT(FT):
    def _append_cmd(self, cmd):
        if not isinstance(getattr(self, 'd'), str): self.d = cmd
        else: self.d += f' {cmd}'
        return self
    
    def M(self, x, y):
        "Move to."
        return self._append_cmd(f'M{x} {y}')

    def L(self, x, y):
        "Line to."
        return self._append_cmd(f'L{x} {y}')

    def H(self, x):
        "Horizontal line to."
        return self._append_cmd(f'H{x}')

    def V(self, y):
        "Vertical line to."
        return self._append_cmd(f'V{y}')

    def Z(self):
        "Close path."
        return self._append_cmd('Z')

    def C(self, x1, y1, x2, y2, x, y):
        "Cubic Bézier curve."
        return self._append_cmd(f'C{x1} {y1} {x2} {y2} {x} {y}')

    def S(self, x2, y2, x, y):
        "Smooth cubic Bézier curve."
        return self._append_cmd(f'S{x2} {y2} {x} {y}')

    def Q(self, x1, y1, x, y):
        "Quadratic Bézier curve."
        return self._append_cmd(f'Q{x1} {y1} {x} {y}')

    def T(self, x, y):
        "Smooth quadratic Bézier curve."
        return self._append_cmd(f'T{x} {y}')

    def A(self, rx, ry, x_axis_rotation, large_arc_flag, sweep_flag, x, y):
        "Elliptical Arc."
        return self._append_cmd(f'A{rx} {ry} {x_axis_rotation} {large_arc_flag} {sweep_flag} {x} {y}')

@delegates(ft_svg)
def Path(d='', fill=None, stroke=None, stroke_width=None, **kwargs):
    "Create a standard `path` SVG element. This is a special object"
    return ft_svg('path', d=d, fill=fill, stroke=stroke, stroke_width=stroke_width, ft_cls=PathFT, **kwargs)


def SvgOob(*args, **kwargs):
    "Wraps an SVG shape (simplified for Datastar)"
    return Svg(*args, **kwargs)

def SvgInb(*args, **kwargs):
    "Wraps an SVG shape (simplified for Datastar)"
    return Svg(*args, **kwargs)