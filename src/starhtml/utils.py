"""Utility functions for StarHTML framework."""

import re
import types
from base64 import b64encode
from dataclasses import dataclass
from datetime import date
from inspect import Parameter, get_annotations
from types import UnionType
from typing import Any, Union, get_args, get_origin
from urllib.parse import parse_qs, quote, unquote, urlencode
from uuid import uuid4

from dateutil import parser as dtparse
from fastcore.utils import (
    camel2words,
    first,
    is_namedtuple,
    listify,
    signature_ex,
    snake2camel,
    str2bool,
    str2date,
    str2int,
)
from fastcore.xml import FT
from starlette.datastructures import FormData, UploadFile
from starlette.exceptions import HTTPException
from starlette.requests import Request

__all__ = [
    "qp",
    "decode_uri",
    "uri",
    "reg_re_param",
    "File",
    "fill_form",
    "fill_dataclass",
    "find_inputs",
    "form2dict",
    "parse_form",
    "clear_form_signals",
    "to_js",
    "unqid",
    "parsed_date",
    "snake2hyphens",
    "get_key",
    "flat_xt",
    "flat_tuple",
    "noop_body",
    "HttpHeader",
    "empty",
]

empty = Parameter.empty
_iter_typs = (tuple, list, map, filter, range, types.GeneratorType)


@dataclass
class HttpHeader:
    k: str
    v: str


# ============================================================================
# URL and URI Utilities
# ============================================================================


def qp(p: str, **kw) -> str:
    "Add parameters kw to path p"

    def _sub(m):
        pre, post = m.groups()
        if pre not in kw:
            return f"{{{pre}{post or ''}}}"
        pre = kw.pop(pre)
        return "" if pre in (False, None) else str(pre)

    p = re.sub(r"\{([^:}]+)(:.+?)?}", _sub, p)
    return p + ("?" + urlencode({k: "" if v in (False, None) else v for k, v in kw.items()}, doseq=True) if kw else "")


def decode_uri(s):
    "Decode URI into path and query parameters"
    arg, _, kw = s.partition("/")
    return unquote(arg), {k: v[0] for k, v in parse_qs(kw).items()}


def uri(_arg, **kwargs):
    "Create URI with quoted argument and URL-encoded kwargs"
    return f"{quote(_arg)}/{urlencode(kwargs, doseq=True)}"


def reg_re_param(m, s):
    "Register a regex parameter converter"
    from starlette.convertors import StringConvertor, register_url_convertor

    class RegexConvertor(StringConvertor):
        regex = s

    register_url_convertor(m, RegexConvertor())


def _url_for(req, t):
    "Generate URL for route target"
    if callable(t):
        t = getattr(t, "__routename__", str(t))
    kw = {}
    if t.find("/") > -1 and (t.find("?") < 0 or t.find("/") < t.find("?")):
        t, kw = decode_uri(t)
    t, m, q = t.partition("?")
    return f"{req.url_path_for(t, **kw)}{m}{q}"


# ============================================================================
# Form and Request Processing
# ============================================================================


async def parse_form(req: Request) -> FormData:
    "Starlette errors on empty multipart forms, so this checks for that situation"
    ctype = req.headers.get("Content-Type", "")
    if ctype == "application/json":
        return await req.json()
    if not ctype.startswith("multipart/form-data"):
        return await req.form()
    try:
        boundary = ctype.split("boundary=")[1].strip()
    except IndexError as e:
        raise HTTPException(400, "Invalid form-data: no boundary") from e
    min_len = len(boundary) + 6
    clen = int(req.headers.get("Content-Length", "0"))
    if clen <= min_len:
        return FormData()
    return await req.form()


def form2dict(form: FormData) -> dict:
    "Convert starlette form data to a dict"
    if isinstance(form, dict):
        return form
    return {k: _formitem(form, k) for k in form}


def fill_form(form, obj):
    "Fills named items in `form` using attributes in `obj`"
    from dataclasses import asdict, is_dataclass

    if is_dataclass(obj):
        obj = asdict(obj)
    elif not isinstance(obj, dict):
        obj = obj.__dict__
    return _fill_item(form, obj)


def fill_dataclass(src, dest):
    "Modifies dataclass in-place and returns it"
    from dataclasses import asdict

    for nm, val in asdict(src).items():
        setattr(dest, nm, val)
    return dest


def find_inputs(e, tags="input", **kw):
    "Recursively find all elements in `e` with `tags` and attrs matching `kw`"
    from fastcore.xml import FT

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


def to_js(value):
    """Convert Python value to safe JavaScript literal."""
    import json

    match value:
        case bool():
            return "true" if value else "false"
        case str():
            return json.dumps(value)
        case int() | float():
            return str(value)
        case None:
            return "null"
        case dict() | list() | tuple():
            return json.dumps(value)
        case _:
            return json.dumps(str(value))


def clear_form_signals(*signals, **kwargs):
    """Generate JavaScript to clear form signals to empty strings or specified values."""

    # Auto-detect dict passed as first argument (no ** required)
    if len(signals) == 1 and isinstance(signals[0], dict) and not kwargs:
        kwargs = signals[0]
        signals = ()

    assignments = [f"${s} = ''" for s in signals]
    assignments.extend(f"${k} = {to_js(v)}" for k, v in kwargs.items())

    return "; ".join(assignments)


def File(fname: str):
    "Use the unescaped text in file `fname` directly"
    from fastcore.utils import Path
    from fastcore.xml import NotStr

    return NotStr(Path(fname).read_text())


def _formitem(form, k):
    "Return single item `k` from `form` if len 1, otherwise return list"
    if isinstance(form, dict):
        return form.get(k)
    o = form.getlist(k)
    return o[0] if len(o) == 1 else o if o else None


async def _from_body(req, p):
    "Extract and convert body parameters based on annotation"
    anno = p.annotation
    # Get the fields and types of type `anno`, if available
    d = _annotations(anno)
    data = form2dict(await parse_form(req))
    if req.query_params:
        data = {**data, **dict(req.query_params)}
    cargs = {k: _form_arg(k, v, d) for k, v in data.items() if not d or k in d}
    return anno(**cargs)


def _fill_item(item, obj: dict[str, Any]):
    "Fill a single form item with data from obj"

    from fastcore.xml import FT

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


# ============================================================================
# Type Processing and Introspection
# ============================================================================


def _params(f):
    "Get function parameters using signature_ex"
    return signature_ex(f, True).parameters


def _annotations(anno):
    "Same as `get_annotations`, but also works on namedtuples"
    if is_namedtuple(anno):
        return {o: str for o in anno._fields}
    return get_annotations(anno)


def _is_body(anno):
    "Check if annotation represents a body type"
    from types import SimpleNamespace as ns

    return issubclass(anno, dict | ns) or _annotations(anno)


def _fix_anno(t, o):
    "Create appropriate callable type for casting a `str` to type `t` (or first type in `t` if union)"
    from fastcore.utils import noop

    origin = get_origin(t)
    if origin is Union or origin is UnionType or origin in (list, list):
        t = first(o for o in get_args(t) if o != type(None))
    d = {bool: str2bool, int: str2int, date: str2date, UploadFile: noop}
    res = d.get(t, t)
    if origin in (list, list):
        return _mk_list(res, o)
    if not isinstance(o, str | list | tuple):
        return o
    return res(o[-1]) if isinstance(o, list | tuple) else res(o)


def _mk_list(t, v):
    "Create a typed list from value v using type t"
    return [t(o) for o in listify(v)]


def _form_arg(k, v, d):
    "Get type by accessing key `k` from `d`, and use to cast `v`"
    if v is None:
        return
    if not isinstance(v, str | list | tuple):
        return v
    # This is the type we want to cast `v` to
    anno = d.get(k, None)
    if not anno:
        return v
    return _fix_anno(anno, v)


# ============================================================================
# General Python Utilities
# ============================================================================


def unqid():
    "Generate a unique URL-safe ID for HTML elements"
    res = b64encode(uuid4().bytes)
    return "_" + res.decode().rstrip("=").translate(str.maketrans("+/", "_-"))


def parsed_date(s: str):
    "Convert `s` to a datetime"
    return dtparse.parse(s)


def snake2hyphens(s: str):
    "Convert `s` from snake case to hyphenated and capitalised"
    s = snake2camel(s)
    return camel2words(s, "-")


def get_key(key=None, fname=".sesskey"):
    "Get or create a session key"
    from pathlib import Path

    fpath = Path(fname)
    if key:
        fpath.write_text(key)
    elif fpath.exists():
        key = fpath.read_text().strip()
    else:
        import secrets

        key = secrets.token_urlsafe(32)
        fpath.write_text(key)
    return key


def flat_xt(lst):
    "Flatten lists for XML elements"
    result = []
    if isinstance(lst, FT | str):
        lst = [lst]
    for item in lst:
        if isinstance(item, list | tuple):
            result.extend(item)
        else:
            result.append(item)
    return tuple(result)


def flat_tuple(o):
    "Flatten lists into a tuple"
    result = []
    if not isinstance(o, _iter_typs):
        o = [o]
    o = list(o)
    for item in o:
        if isinstance(item, _iter_typs):
            result.extend(list(item))
        else:
            result.append(item)
    return tuple(result)


def noop_body(c, req):
    "Default Body wrap function which just returns the content"
    return c


def _list(o):
    "Ensure input is a list"
    return [] if not o else list(o) if isinstance(o, tuple | list) else [o]


def _add_ids(s):
    "Add IDs to FT elements that don't have them"
    from fastcore.xml import FT

    if not isinstance(s, FT):
        return
    if not getattr(s, "id", None):
        s.id = unqid()
    for c in s.children:
        _add_ids(c)


def _camel_to_kebab(name: str) -> str:
    """Convert camelCase or PascalCase to kebab-case."""
    # Insert hyphens before uppercase letters (except at start)
    s1 = re.sub("(.)([A-Z][a-z]+)", r"\1-\2", name)
    # Insert hyphens before uppercase letters following lowercase
    return re.sub("([a-z0-9])([A-Z])", r"\1-\2", s1).lower()
