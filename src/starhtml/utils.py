"""Utility functions for StarHTML framework."""

import re
import secrets
import types
from base64 import b64encode
from dataclasses import dataclass
from datetime import date
from inspect import Parameter, get_annotations
from types import UnionType
from typing import Union, get_args, get_origin
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
from starlette.datastructures import UploadFile

from .forms import form2dict, parse_form

__all__ = [
    "qp",
    "decode_uri",
    "uri",
    "reg_re_param",
    "File",
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


def File(fname: str):
    "Use the unescaped text in file `fname` directly"
    from fastcore.utils import Path
    from fastcore.xml import NotStr

    return NotStr(Path(fname).read_text())


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


def get_key(key=None, fname=".sesskey", *, secret_env=None, strict_mode=True):
    "Get or create a session key (atomic 0o600 on create, mode-checked on read)."
    import os
    import stat
    import warnings
    from pathlib import Path

    env = (secret_env and os.environ.get(secret_env)) or os.environ.get("STARHTML_SECRET_KEY")
    if key := key or env:
        return key

    fpath = Path(fname)
    if fpath.exists():
        mode = stat.S_IMODE(fpath.stat().st_mode)
        if mode != 0o600:
            msg = f"{fpath} mode is {mode:04o}; expected 0600. Run: chmod 600 {fpath}"
            if strict_mode:
                raise PermissionError(msg)
            warnings.warn(msg, stacklevel=2)
        return fpath.read_text().strip()

    new_key = secrets.token_urlsafe(32)
    try:
        fd = os.open(fpath, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    except FileExistsError:
        # Concurrent boot won the race; read what they wrote.
        return get_key(key, fname, secret_env=secret_env, strict_mode=strict_mode)
    try:
        os.write(fd, new_key.encode())
    finally:
        os.close(fd)
    return new_key


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
