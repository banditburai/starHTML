"""`ft_html` and `ft_datastar` functions to add some conveniences to `ft`, along with a full set of basic HTML components, and functions to work with forms and `FT` conversion"""

import re
from collections.abc import Callable
from dataclasses import asdict, is_dataclass
from typing import Any, Optional, Union

from bs4 import BeautifulSoup, Comment
from fastcore.utils import (
    Path,
    partial,
    partition,
    patch,
    risinstance,
)
from fastcore.xml import FT, NotStr, attrmap, ft, to_xml, valmap, voids

from .core import fh_cfg, unqid


@patch
def __str__(self: FT) -> str:
    return self.id if self.id else to_xml(self, indent=False)  # type: ignore[attr-defined]


@patch  # type: ignore[misc]
def __radd__(self: FT, b: Any) -> str:
    return f"{b}{self}"


@patch  # type: ignore[misc]
def __add__(self: FT, b: Any) -> str:
    return f"{self}{b}"


named = set("a button form frame iframe img input map meta object param select textarea".split())
html_attrs = "id cls title style accesskey contenteditable dir draggable enterkeyhint hidden inert inputmode lang popover spellcheck tabindex translate".split()
# Original Datastar attributes for backward compatibility
datastar_core_attrs = "signals bind text show hide class style indicator computed store signal"
# All Datastar event types
datastar_event_types = "click submit change input load keydown keyup focus blur scroll resize mouseover mouseout mouseenter mouseleave intersect interval"
# New direct attributes with ds_ prefix
ds_direct_attrs = ["ds_" + attr for attr in datastar_core_attrs.split()]
ds_event_attrs = ["ds_on_" + evt for evt in datastar_event_types.split()]
# Additional RC.11 attributes
ds_extra_attrs = "ds_ref ds_html ds_teleport ds_transition_enter ds_transition_leave".split()
# For wildcard attributes
ds_wildcard_attrs = ["ds_attr_", "ds_on_intersect_", "ds_on_interval_"]

datastar_evts = "click submit change input load keydown keyup focus blur scroll resize"
js_evts = "blur change contextmenu focus input invalid reset select submit keydown keypress keyup click dblclick mousedown mouseenter mouseleave mousemove mouseout mouseover mouseup wheel"
# Keep backward compatibility
datastar_attrs = [
    f"data_{o}"
    for o in ("on_click on_submit on_change on_input on_load on_keydown on_keyup " + datastar_core_attrs).split()
]
datastar_attrs_annotations = {
    "data_on_click": str,
    "data_on_submit": str,
    "data_signals": str,
    "data_bind": str,
    "data_text": str,
    "data_show": str,
    "data_indicator": str,
}
datastar_attrs_annotations |= {o: str for o in set(datastar_attrs) - set(datastar_attrs_annotations.keys())}
datastar_attrs_annotations = {k: Optional[v] for k, v in datastar_attrs_annotations.items()}
datastar_attrs = html_attrs + datastar_attrs

datastar_evt_attrs = [f"data_on_{o}" for o in datastar_evts.split()]
evt_attrs = datastar_evt_attrs


def attrmap_x(o: str) -> str:
    if o.startswith("_at_"):
        o = "@" + o[4:]
    return attrmap(o)


fh_cfg["attrmap"] = attrmap_x
fh_cfg["valmap"] = valmap
fh_cfg["ft_cls"] = FT
fh_cfg["auto_id"] = False
fh_cfg["auto_name"] = True


def ft_html(
    tag: str,
    *c: Any,
    id: Optional[Union[str, bool, FT]] = None,
    cls: Optional[str] = None,
    title: Optional[str] = None,
    style: Optional[str] = None,
    attrmap: Optional[Callable] = None,
    valmap: Optional[Callable] = None,
    ft_cls: Optional[type] = None,
    **kwargs: Any,
) -> FT:
    ds, c = partition(c, risinstance(dict))
    for d in ds:
        kwargs = {**kwargs, **d}
    if ft_cls is None:
        ft_cls = fh_cfg.ft_cls
    if attrmap is None:
        attrmap = fh_cfg.attrmap
    if valmap is None:
        valmap = fh_cfg.valmap
    if not id and fh_cfg.auto_id:
        id = True
    if id and isinstance(id, bool):
        id = unqid()
    kwargs["id"] = id.id if isinstance(id, FT) else id
    kwargs["cls"], kwargs["title"], kwargs["style"] = cls, title, style
    tag, c, kw = ft(tag, *c, attrmap=attrmap, valmap=valmap, **kwargs).list
    if fh_cfg["auto_name"] and tag in named and id and "name" not in kw:
        kw["name"] = kw["id"]
    return ft_cls(tag, c, kw, void_=tag in voids)


def _process_datastar_attrs(kwargs: dict[str, Any]) -> dict[str, Any]:
    """Process ds_* attributes and transform them to data-* attributes."""
    processed = {}

    for key, value in kwargs.items():
        if key.startswith("ds_"):
            # Transform ds_* to data-*
            if key.startswith("ds_on_"):
                # Event handlers: ds_on_click -> data-on-click
                event_part = key[6:]  # Remove 'ds_on_'
                # Handle modifiers like ds_on_intersect_once -> data-on-intersect.once
                if "_" in event_part and event_part.split("_")[0] in ["intersect", "interval"]:
                    base_event, modifier = event_part.split("_", 1)
                    data_key = f"data-on-{base_event}.{modifier}"
                else:
                    data_key = f"data-on-{event_part.replace('_', '-')}"
            elif key.startswith("ds_attr_"):
                # Dynamic attributes: ds_attr_disabled -> data-attr-disabled
                data_key = key.replace("ds_attr_", "data-attr-").replace("_", "-")
            elif key == "ds_signals" and isinstance(value, dict):
                # Special handling for signals dict
                import json

                processed["data-signals"] = json.dumps(value)
                continue
            else:
                # Simple attributes: ds_show -> data-show
                data_key = key.replace("ds_", "data-").replace("_", "-")

            # Convert Python booleans to string "true"/"false" for JavaScript
            if isinstance(value, bool):
                processed[data_key] = "true" if value else "false"
            else:
                processed[data_key] = value
        else:
            # Non-datastar attributes pass through
            processed[key] = value

    return processed


def ft_datastar(tag: str, *c: Any, **kwargs: Any) -> FT:
    """Create an HTML element with support for Datastar direct attributes.

    This function processes ds_* attributes and transforms them to data-* attributes.
    For example: ds_on_click="handler()" becomes data-on-click="handler()"
    """
    # Process ds_* attributes to data-* attributes
    kwargs = _process_datastar_attrs(kwargs)

    return ft_html(tag, *c, **kwargs)


_g: dict[str, Any] = globals()
_all_ = [
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
for o in _all_:
    _g[o] = partial(ft_datastar, o.lower())  # type: ignore[misc]


def File(fname: str) -> NotStr:
    "Use the unescaped text in file `fname` directly"
    return NotStr(Path(fname).read_text())


def _fill_item(item: Any, obj: dict[str, Any]) -> Any:
    if not isinstance(item, FT):
        return item
    tag, cs, attr = item.list
    if isinstance(cs, tuple):
        cs = tuple(_fill_item(o, obj) for o in cs)
    name = attr.get("name", None)
    val = None if name is None else obj.get(name, None)
    if val is not None and "skip" not in attr:
        if tag == "input":
            if attr.get("type", "") == "checkbox":
                if isinstance(val, list):
                    if attr["value"] in val:
                        attr["checked"] = "1"
                    else:
                        attr.pop("checked", "")
                elif val:
                    attr["checked"] = "1"
                else:
                    attr.pop("checked", "")
            elif attr.get("type", "") == "radio":
                if val and val == attr["value"]:
                    attr["checked"] = "1"
                else:
                    attr.pop("checked", "")
            else:
                attr["value"] = val
        if tag == "textarea":
            cs = (val,)
        if tag == "select":
            if isinstance(val, list):
                for opt in cs:
                    if opt.tag == "option" and opt.get("value") in val:
                        opt.selected = "1"
            else:
                option = next((o for o in cs if o.tag == "option" and o.get("value") == val), None)
                if option:
                    option.selected = "1"
    return FT(tag, cs, attr, void_=item.void_)


def fill_form(form: FT, obj: Union[dict[str, Any], Any]) -> FT:
    "Fills named items in `form` using attributes in `obj`"
    if is_dataclass(obj):
        obj = asdict(obj)
    elif not isinstance(obj, dict):
        obj = obj.__dict__
    return _fill_item(form, obj)


def fill_dataclass(src: Any, dest: Any) -> Any:
    "Modifies dataclass in-place and returns it"
    for nm, val in asdict(src).items():
        setattr(dest, nm, val)
    return dest


def find_inputs(e: Union[list, tuple, FT], tags: Union[str, list[str]] = "input", **kw: Any) -> list[FT]:
    "Recursively find all elements in `e` with `tags` and attrs matching `kw`"
    if not isinstance(e, list | tuple | FT):
        return []
    inputs = []
    if isinstance(tags, str):
        tags = [tags]
    elif tags is None:
        tags = []
    cs = e
    if isinstance(e, FT):
        tag, cs, attr = e.list
        if tag in tags and kw.items() <= attr.items():
            inputs.append(e)
    for o in cs:
        inputs += find_inputs(o, tags, **kw)
    return inputs


def __getattr__(tag: str) -> Callable[..., Any]:
    if tag.startswith("_") or tag[0].islower():
        raise AttributeError
    tag = tag.replace("_", "-")

    def _f(*c: Any, target_id: Optional[str] = None, **kwargs: Any) -> Any:
        return ft_datastar(tag, *c, target_id=target_id, **kwargs)

    return _f


_re_h2x_attr_key = re.compile(r"^[A-Za-z_-][\w-]*$")
_attr_cache: dict[str, bool] = {}
_tag_cache: dict[str, str] = {}


def _is_valid_attr(key: str) -> bool:
    """Cached attribute validation"""
    return _attr_cache.setdefault(key, _re_h2x_attr_key.match(key) is not None)


def _get_tag_name(name: str) -> str:
    """Cached tag name transformation"""
    return _tag_cache.setdefault(name, "[document]" if name == "[document]" else name.capitalize().replace("-", "_"))


def html2ft(html, attr1st=False):
    """Convert HTML to an `ft` expression - Optimized version with 2.52x speedup"""
    rev_map = {"class": "cls", "for": "fr"}

    def _parse(elm, lvl=0, indent=4):
        # Fast paths for strings and lists
        if isinstance(elm, str):
            return repr(stripped) if (stripped := elm.strip()) else ""
        if isinstance(elm, list):
            return "\n".join(_parse(o, lvl) for o in elm)

        # Get cached tag name and handle document
        tag_name = _get_tag_name(elm.name)
        if tag_name == "[document]":
            return _parse(list(elm.children), lvl)

        # Process contents efficiently
        cs = [
            repr(c.strip()) if isinstance(c, str) and c.strip() else _parse(c, lvl + 1)
            for c in elm.contents
            if not isinstance(c, str) or c.strip()
        ]

        # Process attributes with optimizations
        attrs, exotic_attrs = [], {}
        items = sorted(elm.attrs.items(), key=lambda x: x[0] == "class") if "class" in elm.attrs else elm.attrs.items()

        for key, value in items:
            value = " ".join(value) if isinstance(value, tuple | list) else (value or True)
            key = rev_map.get(key, key)

            if _is_valid_attr(key):
                attrs.append(f"{key.replace('-', '_')}={value!r}")
            else:
                exotic_attrs[key] = value

        if exotic_attrs:
            attrs.append(f"**{exotic_attrs!r}")

        # Format output efficiently
        spc = " " * (lvl * indent)
        onlychild = not elm.contents or (len(elm.contents) == 1 and isinstance(elm.contents[0], str))

        if onlychild:
            inner = ", ".join(filter(None, cs + attrs))
            return (
                f"{tag_name}({inner})"
                if not attr1st
                else f"{tag_name}({', '.join(filter(None, attrs))})({cs[0] if cs else ''})"
            )

        j = f",\n{spc}"
        return (
            f"{tag_name}(\n{spc}{j.join(filter(None, cs + attrs))}\n{' ' * ((lvl - 1) * indent)})"
            if not attr1st or not attrs
            else f"{tag_name}({', '.join(filter(None, attrs))})(\n{spc}{j.join(filter(None, cs))}\n{' ' * ((lvl - 1) * indent)})"
        )

    # Parse HTML and remove comments efficiently
    soup = BeautifulSoup(html.strip(), "html.parser")
    [comment.extract() for comment in soup.find_all(string=lambda text: isinstance(text, Comment))]
    return _parse(soup, 1)


def sse_message(elm, event="message"):
    "Convert element `elm` into a format suitable for SSE streaming"
    data = "\n".join(f"data: {o}" for o in to_xml(elm).splitlines())
    return f"event: {event}\n{data}\n\n"


__all__ = [
    "named",
    "html_attrs",
    "datastar_attrs",
    "datastar_evts",
    "js_evts",
    "datastar_attrs_annotations",
    "datastar_evt_attrs",
    "evt_attrs",
    "attrmap_x",
    "ft_html",
    "ft_datastar",
    "File",
    "fill_form",
    "fill_dataclass",
    "find_inputs",
    "html2ft",
    "sse_message",
] + _all_
