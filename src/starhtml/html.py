"""Core HTML generation functionality for StarHTML."""

import re
from collections.abc import Callable
from typing import Any

from bs4 import BeautifulSoup, Comment
from fastcore.utils import (
    AttrDict,
    partition,
    patch,
    risinstance,
)
from fastcore.xml import FT, attrmap, ft, to_xml, valmap, voids

from . import datastar as ds
from .utils import unqid

__all__ = ["ft_html", "ft_datastar", "html2ft", "attrmap_x", "fh_cfg", "named", "html_attrs", "js_evts"]

named = set("a button form frame iframe img input map meta object param select textarea".split())
html_attrs = "id cls title style accesskey contenteditable dir draggable enterkeyhint hidden inert inputmode lang popover spellcheck tabindex translate".split()
js_evts = "blur change contextmenu focus input invalid reset select submit keydown keypress keyup click dblclick mousedown mouseenter mouseleave mousemove mouseout mouseover mouseup wheel".split()


def attrmap_x(o: str) -> str:
    """Extended attribute mapping for StarHTML (e.g., `_at_` -> `@`)."""
    if o.startswith("_at_"):
        o = "@" + o[4:]
    return attrmap(o)


fh_cfg = AttrDict(
    attrmap=attrmap_x,  # How to transform attribute names (e.g., cls -> class)
    valmap=valmap,  # How to transform attribute values
    ft_cls=FT,  # Which class to use for HTML elements
    auto_id=False,  # Whether to auto-generate element IDs
    auto_name=True,  # Whether to auto-generate name attributes
    indent=True,  # Whether to indent HTML/XML output
)

# ============================================================================
# Core HTML Element Creation
# ============================================================================


def ft_html(
    tag: str,
    *c: Any,
    id: str | bool | FT | None = None,
    cls: str | None = None,
    title: str | None = None,
    style: str | None = None,
    attrmap: Callable | None = None,
    valmap: Callable | None = None,
    ft_cls: type | None = None,
    **kwargs: Any,
) -> FT:
    "Create a basic HTML element using fastcore's ft system"
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


def _apply_slot_attrs_to_children(parent, slot_attrs):
    """Apply slot attributes to matching children."""
    if not (slot_attrs and hasattr(parent, "children")):
        return

    for child in parent.children:
        if hasattr(child, "attrs") and isinstance(child.attrs, dict):
            slot_name = child.attrs.get("data-slot")
            if slot_name in slot_attrs:
                attr_value = slot_attrs[slot_name]

                if isinstance(attr_value, dict):
                    processed_attrs, _ = ds.process_datastar_kwargs(attr_value)
                    for key, value in processed_attrs.items():
                        child.attrs.setdefault(key, value)
                elif isinstance(attr_value, list):
                    for attr_dict in attr_value:
                        if isinstance(attr_dict, dict):
                            processed_attrs, _ = ds.process_datastar_kwargs(attr_dict)
                            for key, value in processed_attrs.items():
                                child.attrs.setdefault(key, value)

        _apply_slot_attrs_to_children(child, slot_attrs)


def ft_datastar(tag: str, *c: Any, **kwargs: Any) -> FT:
    """Create an HTML element with Datastar support."""
    slot_attrs_dict = {
        key[5:].replace("_", "-"): value
        for key, value in list(kwargs.items())
        if key.startswith("slot_") and isinstance(value, dict) and kwargs.pop(key)
    }

    new_children, collected_signals, defined_signals = [], set(), []

    for child in c:
        match child:
            case ds.Signal():
                defined_signals.append(child)
                if computed_attr := child.get_computed_attr():
                    attr_name, attr_value = computed_attr
                    kwargs[attr_name] = attr_value
            case _:
                new_children.append(child)
                if signals := getattr(child, "__signals_found", None):
                    if isinstance(signals, set | list | tuple):
                        collected_signals.update(s for s in signals if isinstance(s, ds.Signal))

    processed_kwargs, signals_found = ds.process_datastar_kwargs(kwargs)
    collected_signals.update(signals_found)

    if defined_signals and not any(k in ("data-signals", "data_signals") for k in (*processed_kwargs, *kwargs)):
        kwargs["data_signals"] = defined_signals
        processed_kwargs, new_signals = ds.process_datastar_kwargs(kwargs)
        collected_signals.update(new_signals)

    result = ft_html(tag, *new_children, **processed_kwargs)

    if collected_signals:
        result.__signals_found = collected_signals

    if slot_attrs_dict:
        _apply_slot_attrs_to_children(result, slot_attrs_dict)

    return result


# ============================================================================
# HTML Conversion Utility (html2ft)
# ============================================================================

_re_h2x_attr_key = re.compile(r"^[A-Za-z_-][\w-]*$")
_attr_cache: dict[str, bool] = {}


def _is_valid_attr(key: str) -> bool:
    """Cached attribute validation"""
    return _attr_cache.setdefault(key, _re_h2x_attr_key.match(key) is not None)


_tag_cache: dict[str, str] = {}


def _get_tag_name(name: str) -> str:
    """Cached tag name transformation"""
    return _tag_cache.setdefault(name, "[document]" if name == "[document]" else name.capitalize().replace("-", "_"))


def html2ft(html, attr1st=False):
    """Convert HTML to an `ft` expression - Optimized version with 2.52x speedup"""
    rev_map = {"class": "cls", "for": "fr"}

    def _parse(elm, lvl=0, indent=4):
        if isinstance(elm, str):
            return repr(stripped) if (stripped := elm.strip()) else ""
        if isinstance(elm, list):
            return "\n".join(_parse(o, lvl) for o in elm)

        tag_name = _get_tag_name(elm.name)
        if tag_name == "[document]":
            return _parse(list(elm.children), lvl)

        cs = [
            repr(c.strip()) if isinstance(c, str) and c.strip() else _parse(c, lvl + 1)
            for c in elm.contents
            if not isinstance(c, str) or c.strip()
        ]

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

    soup = BeautifulSoup(html.strip(), "html.parser")
    [comment.extract() for comment in soup.find_all(string=lambda text: isinstance(text, Comment))]
    return _parse(soup, 1)


# ============================================================================
# Internal Patches
# ============================================================================


@patch
def __str__(self: "FT") -> str:
    return self.id if self.id else to_xml(self, indent=False)


@patch
def __radd__(self: "FT", b: Any) -> str:
    return f"{b}{self}"


@patch
def __add__(self: "FT", b: Any) -> str:
    return f"{self}{b}"
