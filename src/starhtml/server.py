"""HTTP server functionality: requests, responses, routing for StarHTML."""

import asyncio
import inspect
import json
import os
import types
from collections.abc import Mapping
from copy import deepcopy
from datetime import datetime
from functools import partialmethod, update_wrapper
from http import cookies
from inspect import iscoroutinefunction
from pathlib import Path
from types import GenericAlias
from typing import Any
from warnings import warn

from anyio import from_thread
from fastcore.utils import dict2obj, noop, partition, patch, risinstance, tuplify
from fastcore.xml import FT, to_xml
from httpx import ASGITransport, AsyncClient
from starlette.applications import Starlette
from starlette.background import BackgroundTask, BackgroundTasks
from starlette.concurrency import run_in_threadpool
from starlette.convertors import StringConvertor, register_url_convertor
from starlette.datastructures import URLPath
from starlette.exceptions import HTTPException
from starlette.requests import HTTPConnection, Request
from starlette.responses import (
    FileResponse,
    HTMLResponse,
    RedirectResponse,
    Response,
)
from starlette.responses import (
    JSONResponse as JSONResponseOrig,
)

from .utils import (
    HttpHeader,
    _fix_anno,
    _from_body,
    _is_body,
    _url_for,
    empty,
    flat_tuple,
    flat_xt,
    form2dict,
    noop_body,
    parse_form,
    snake2hyphens,
)

__all__ = [
    "all_meths",
    "JSONResponse",
    "Redirect",
    "FtResponse",
    "Client",
    "RouteFuncs",
    "APIRouter",
    "serve",
    "cookie",
    "signal_shutdown",
    "ResponseRenderer",
    "render_response",
    "to_string",
    "url_path_for",
]

all_meths = "get post put delete patch head trace options".split()
_iter_typs = (tuple, list, map, filter, range, types.GeneratorType)
_verbs = dict(
    get="data-on-click",
    post="data-on-submit",
    put="data-on-submit",
    delete="data-on-click",
    patch="data-on-submit",
    link="href",
)

# ============================================================================
# Public API: Routing & Server Utilities
# ============================================================================


class APIRouter:
    "Add routes to an app"

    def __init__(self, prefix: str | None = None, body_wrap=None):
        from .utils import noop_body

        self.routes, self.wss = [], []
        self.rt_funcs = RouteFuncs()  # Store wrapped route function for discoverability
        self.prefix = prefix if prefix else ""
        self.body_wrap = body_wrap or noop_body

    def _wrap_func(self, func, path=None):
        name = func.__name__
        wrapped = _mk_locfunc(func, path)
        wrapped.__routename__ = name  # type: ignore[attr-defined]
        # If you are using the def get or def post method names, this approach is not supported
        if name not in all_meths:
            setattr(self.rt_funcs, name, wrapped)
        return wrapped

    def __call__(self, path: str = None, methods=None, name=None, include_in_schema=True, body_wrap=None):
        "Add a route at `path`"

        def f(func):
            p = self.prefix + (
                "/" + ("" if getattr(path, "__name__", None) == "index" else func.__name__) if callable(path) else path
            )
            wrapped = self._wrap_func(func, p)
            self.routes.append((func, p, methods, name, include_in_schema, body_wrap or self.body_wrap))
            return wrapped

        return f(path) if callable(path) else f

    def __getattr__(self, name):
        try:
            return getattr(self.rt_funcs, name)
        except AttributeError:
            return super().__getattribute__(name)  # type: ignore[misc]

    def to_app(self, app):
        "Add routes to `app`"
        for args in self.routes:
            app._add_route(*args)
        for args in self.wss:
            app._add_ws(*args)

    def ws(self, path: str, conn=None, disconn=None, name=None, middleware=None):
        "Add a websocket route at `path`"

        def f(func=noop):
            return self.wss.append((func, f"{self.prefix}{path}", conn, disconn, name, middleware))

        return f


# Add HTTP method shortcuts to APIRouter
for o in all_meths:
    setattr(APIRouter, o, partialmethod(APIRouter.__call__, methods=o))


class RouteFuncs:
    "Container for route functions"

    def __init__(self):
        super().__setattr__("_funcs", {})

    def __setattr__(self, name, value):
        self._funcs[name] = value

    def __getattr__(self, name):
        if name in all_meths:
            raise AttributeError("Route functions with HTTP Names are not accessible here")
        try:
            return self._funcs[name]
        except KeyError as e:
            raise AttributeError(f"No route named {name} found in route functions") from e

    def __dir__(self):
        return list(self._funcs.keys())


def serve(
    appname=None,  # Name of the module
    app="app",  # App instance to be served
    host="0.0.0.0",  # If host is 0.0.0.0 will convert to localhost
    port=None,  # If port is None it will default to 5001 or the PORT environment variable
    reload=True,  # Default is to reload the app upon code changes
    reload_includes: list[str] | str | None = None,  # Additional files to watch for changes
    reload_excludes: list[str] | str | None = None,  # Files to ignore for changes
):
    "Run the app in an async server, with live reload set as the default."
    bk = inspect.currentframe().f_back
    glb = bk.f_globals
    code = bk.f_code
    if not appname:
        if glb.get("__name__") == "__main__":
            appname = Path(glb.get("__file__", "")).stem
        elif code.co_name == "main" and bk.f_back.f_globals.get("__name__") == "__main__":
            appname = inspect.getmodule(bk).__name__
    import uvicorn

    if appname:
        if not port:
            port = int(os.getenv("PORT", default=5001))
        print(f"Link: http://{'localhost' if host == '0.0.0.0' else host}:{port}")
        uvicorn.run(
            f"{appname}:{app}",
            host=host,
            port=port,
            reload=reload,
            reload_includes=reload_includes,
            reload_excludes=reload_excludes,
        )


def cookie(
    key: str,
    value="",
    max_age=None,
    expires=None,
    path="/",
    domain=None,
    secure=False,
    httponly=False,
    samesite="lax",
):
    "Create a 'set-cookie' `HttpHeader`"
    from .utils import HttpHeader

    cookie = cookies.SimpleCookie()
    cookie[key] = value
    if max_age is not None:
        cookie[key]["max-age"] = max_age
    if expires is not None:
        if isinstance(expires, datetime):
            # Format datetime as HTTP date string (RFC 7231)
            cookie[key]["expires"] = expires.strftime("%a, %d %b %Y %H:%M:%S GMT")
        else:
            cookie[key]["expires"] = expires
    if path is not None:
        cookie[key]["path"] = path
    if domain is not None:
        cookie[key]["domain"] = domain
    if secure:
        cookie[key]["secure"] = True
    if httponly:
        cookie[key]["httponly"] = True
    if samesite is not None:
        assert samesite.lower() in [
            "strict",
            "lax",
            "none",
        ], "must be 'strict', 'lax' or 'none'"
        cookie[key]["samesite"] = samesite
    cookie_val = cookie.output(header="").strip()
    return HttpHeader("set-cookie", cookie_val)


def signal_shutdown():
    "Create shutdown signal handler"
    from uvicorn.main import Server

    event = asyncio.Event()

    @patch
    def handle_exit(self: Server, *args, **kwargs):
        event.set()
        self.force_exit = True
        self._orig_handle_exit(*args, **kwargs)

    return event


class Client:
    "A simple httpx ASGI client that doesn't require `async`"

    def __init__(self, app, url="http://testserver"):
        self.cli = AsyncClient(transport=ASGITransport(app), base_url=url)

    def _sync(self, method, url, **kwargs):
        async def _request():
            return await self.cli.request(method, url, **kwargs)

        with from_thread.start_blocking_portal() as portal:
            return portal.call(_request)


# Add HTTP method shortcuts to Client
for o in ("get", "post", "delete", "put", "patch", "options"):
    setattr(Client, o, partialmethod(Client._sync, o))

# ============================================================================
# Public API: Custom Response Classes
# ============================================================================


class JSONResponse(JSONResponseOrig):
    "Same as starlette's version, but auto-stringifies non serializable types"

    def render(self, content: Any) -> bytes:
        res = json.dumps(content, ensure_ascii=False, allow_nan=False, indent=None, separators=(",", ":"), default=str)
        return res.encode("utf-8")


class Redirect:
    "Redirect to `loc` using standard HTTP redirect"

    def __init__(self, loc):
        self.loc = loc

    def __response__(self, req):
        return RedirectResponse(self.loc, status_code=303)


class FtResponse:
    "Wrap an FT response with any Starlette `Response`"

    def __init__(
        self,
        content,
        status_code: int = 200,
        headers=None,
        cls=HTMLResponse,
        media_type: str | None = None,
        background: BackgroundTask | None = None,
    ):
        self.content, self.status_code, self.headers = content, status_code, headers
        self.cls, self.media_type, self.background = cls, media_type, background

    def __response__(self, req):
        """Delegates rendering to the main ResponseRenderer."""
        return render_response(req, self.content, cls=self.cls, status_code=self.status_code)


# ============================================================================
# Internal: Request-to-Response Pipeline
# ============================================================================


class ResponseRenderer:
    def __init__(self, request):
        self.request = request
        self.headers = {}
        self.tasks = None

    def process(self, user_response: Any, cls: type = None, status_code: int = 200) -> Response:
        """Main method that orchestrates the entire response processing pipeline."""
        if not user_response:
            user_response = ""
        if hasattr(user_response, "__response__"):
            response_method = user_response.__response__
            if callable(response_method):
                return response_method(self.request)
        if isinstance(user_response, FileResponse):
            if not os.path.exists(user_response.path):
                raise HTTPException(404, user_response.path)
        if isinstance(user_response, Response):
            return user_response

        body_content, kw = self._partition_response(user_response)
        self.headers.update(kw.get("headers", {}))
        self.tasks = kw.get("background")
        final_content, content_type = self._render_body(body_content)

        return self._build_final_response(final_content, content_type, cls, status_code)

    def _partition_response(self, resp):
        """Separates HttpHeader and BackgroundTask objects from the response body."""
        resp = flat_tuple(resp)
        resp = resp + tuple(getattr(self.request, "injects", ()))
        http_hdrs, resp = partition(resp, risinstance(HttpHeader))
        tasks, resp = partition(resp, risinstance(BackgroundTask))

        kw = {"headers": {}}
        if http_hdrs:
            kw["headers"] |= {o.k: str(o.v) for o in http_hdrs}
        if tasks:
            ts = BackgroundTasks()
            for t in tasks:
                ts.tasks.append(t)
            kw["background"] = ts

        return resp[0] if len(resp) == 1 else resp, kw

    def _render_body(self, body: Any) -> tuple[Any, str]:
        """Determines content type and renders body to final form."""
        if self._is_ft_response(body):
            processed_body = self._process_ft_objects(body)
            html_content = self._wrap_in_full_page(processed_body)
            return html_content, "html"

        if isinstance(body, Mapping):
            return body, "json"
        if isinstance(body, str):
            return body, "html"
        return str(body), "html"  # Default to HTML

    def _build_final_response(self, content: Any, content_type: str, cls: type, status_code: int) -> Response:
        """Selects the correct Response class and instantiates it."""
        if cls in (Any, FT, empty):
            cls = None
        if cls:
            return cls(content, status_code=status_code, headers=self.headers, background=self.tasks)

        if content_type == "json":
            return JSONResponse(content, status_code=status_code, headers=self.headers, background=self.tasks)
        else:  # Default to HTML
            return HTMLResponse(content, status_code=status_code, headers=self.headers, background=self.tasks)

    def _process_ft_objects(self, resp: Any) -> Any:
        """Recursively processes FT objects by applying __ft__ methods and transforming target attributes in a single pass."""
        if isinstance(resp, tuple):
            return tuple(self._process_ft_objects(o) for o in resp)

        if hasattr(resp, "__ft__"):
            ft_method = resp.__ft__
            if callable(ft_method):
                resp = ft_method()

        if isinstance(resp, FT):
            # Process children first
            resp.children = tuple(self._process_ft_objects(c) for c in resp.children)

            # Then process target attributes on this element
            for k, v in _verbs.items():
                target_path = resp.attrs.pop(k, None)
                if target_path:
                    url = _url_for(self.request, target_path)
                    if k == "link":
                        resp.attrs[v] = url
                    else:
                        resp.attrs[v] = f"@{k}('{url}')"

        return resp

    def _wrap_in_full_page(self, resp: Any) -> str:
        """Wraps response fragment in full HTML page if needed, returns HTML string."""
        from .html import fh_cfg

        resp = tuplify(resp)
        if self._is_full_page(resp):
            return to_xml(resp, indent=fh_cfg.indent)

        hdr_tags = "title", "meta", "link", "style", "base"
        heads, bdy = partition(resp, lambda o: getattr(o, "tag", "") in hdr_tags)

        from .tags import Body, Head, Html, Link, Title

        title = [] if any(getattr(o, "tag", "") == "title" for o in heads) else [Title(self.request.app.title)]
        canonical = (
            [Link(rel="canonical", href=getattr(self.request, "canonical", self.request.url))]
            if self.request.app.canonical
            else []
        )

        body_wrap = getattr(self.request, "body_wrap", noop_body)
        params = inspect.signature(body_wrap).parameters
        bw_args = (bdy, self.request) if len(params) > 1 else (bdy,)
        body = Body(body_wrap(*bw_args), *flat_xt(self.request.ftrs), **self.request.bodykw)

        html_page = Html(Head(*heads, *title, *canonical, *flat_xt(self.request.hdrs)), body, **self.request.htmlkw)

        return to_xml(html_page, indent=fh_cfg.indent)

    def _is_ft_response(self, resp):
        """Check if response needs FT processing."""
        return isinstance(resp, _iter_typs + (HttpHeader, FT)) or hasattr(resp, "__ft__")

    def _is_full_page(self, resp):
        """Check if response is already a full HTML page."""
        if not resp:
            return False
        return any(getattr(o, "tag", "") == "html" for o in resp)


def render_response(request, user_response: Any, cls: type = None, status_code: int = 200) -> Response:
    """Main entry point for rendering a user's route return value into an HTTP response.

    This is the clean, modern API for response processing.
    """
    renderer = ResponseRenderer(request)
    return renderer.process(user_response, cls, status_code)


def _should_extract_datastar_signals(req):
    """Check if datastar signal extraction is enabled for this request."""
    if not (hasattr(req, "scope") and req.scope):
        return False
    app = req.scope.get("app")
    return app and hasattr(app, "state") and getattr(app.state, "auto_unpack", True)


def _extract_from_datastar_query(req, arg):
    """Extract parameter from datastar query parameter."""
    datastar_query = req.query_params.get("datastar")
    if not datastar_query:
        return empty  # Use empty sentinel to indicate not found
    try:
        data = json.loads(datastar_query)
        if arg in data:
            return data[arg]  # Return the value even if it's None
        return empty  # Key not found
    except (json.JSONDecodeError, AttributeError):
        return empty  # Invalid JSON


async def _extract_from_datastar_body(req, arg):
    """Extract parameter from datastar signals in request body."""
    if req.method not in {"POST", "PUT", "PATCH", "DELETE"}:
        return empty  # Use empty sentinel to indicate not found

    form_data = form2dict(await parse_form(req))
    if not (isinstance(form_data, dict) and all(k.startswith("$") or k == "datastar" for k in form_data.keys())):
        return empty  # Not a datastar request

    # Check with $ prefix first, then without
    if f"${arg}" in form_data:
        return form_data[f"${arg}"]  # Return the value even if it's None
    elif arg in form_data:
        return form_data[arg]  # Return the value even if it's None
    return empty  # Key not found


async def _find_p(req, arg: str, p):
    "In `req` find param named `arg` of type in `p` (`arg` is ignored for body types)"

    anno = p.annotation
    # If there's an annotation of special types, return object of that type
    # GenericAlias is a type of typing for iterators like list[int] that is not a class
    if isinstance(anno, type) and not isinstance(anno, GenericAlias):
        if issubclass(anno, Request):
            return req
        if issubclass(anno, Starlette):
            return req.scope["app"]
        if _is_body(anno) and "session".startswith(arg.lower()):
            return req.scope.get("session", {})
        if _is_body(anno):
            return await _from_body(req, p)
    # If there's no annotation, check for special names
    if anno is empty:
        if "request".startswith(arg.lower()):
            return req
        if "session".startswith(arg.lower()):
            return req.scope.get("session", {})
        if arg.lower() == "scope":
            return dict2obj(req.scope)
        if arg.lower() == "auth":
            return req.scope.get("auth", None)
        if arg.lower() == "app":
            return req.scope["app"]
        if arg.lower() == "body":
            return (await req.body()).decode()
        if arg.lower() in ("hdrs", "ftrs", "bodykw", "htmlkw"):
            return getattr(req, arg.lower())
        if arg != "resp":
            warn(f"`{arg} has no type annotation and is not a recognised special name, so is ignored.", stacklevel=2)
        return None
    # Look through path, cookies, headers, query, and body in that order
    res = req.path_params.get(arg, None)
    if res in (empty, None):
        res = req.cookies.get(arg, None)
    if res in (empty, None):
        res = req.headers.get(snake2hyphens(arg), None)
    if res in (empty, None):
        res = req.query_params.getlist(arg)
    if res == []:
        res = None
    if res in (empty, None) and req.method in {"POST", "PUT", "PATCH", "DELETE"}:
        res = form2dict(await parse_form(req)).get(arg, None)
    # Track if we found a value in datastar (even if it's None)
    found_in_datastar = False

    if res in (empty, None) and _should_extract_datastar_signals(req):
        # Try query first
        query_res = _extract_from_datastar_query(req, arg)
        if query_res is not empty:
            res = query_res
            found_in_datastar = True
        else:
            # Try body if query didn't find it
            body_res = await _extract_from_datastar_body(req, arg)
            if body_res is not empty:
                res = body_res
                found_in_datastar = True

    if (res in (empty, None)) and p.default is empty and not found_in_datastar:
        from starlette.exceptions import HTTPException

        raise HTTPException(400, f"Missing required field: {arg}")

    # Only use default if we didn't find the parameter anywhere (including datastar)
    if res in (empty, None) and not found_in_datastar:
        res = p.default
    if anno is empty:
        return res
    try:
        return _fix_anno(anno, res)
    except ValueError:
        from starlette.exceptions import HTTPException

        raise HTTPException(404, req.url.path) from None


async def _wrap_req(req, params):
    "Wrap request with parameters"
    return [await _find_p(req, arg, p) for arg, p in params.items()]


async def _handle(f, args, **kwargs):
    "Handle function call (async or sync)"
    return (await f(*args, **kwargs)) if iscoroutinefunction(f) else await run_in_threadpool(f, *args, **kwargs)


async def _wrap_call(f, req, params):
    "Wrap function call with request"
    wreq = await _wrap_req(req, params)
    return await _handle(f, wreq)


def _wrap_ex(f, status_code, hdrs, ftrs, htmlkw, bodykw, body_wrap):
    "Wrap exception handler"

    async def _f(req, exc):
        req.hdrs, req.ftrs, req.htmlkw, req.bodykw = map(deepcopy, (hdrs, ftrs, htmlkw, bodykw))
        req.body_wrap = body_wrap
        res = await _handle(f, (req, exc))
        return render_response(req, res, status_code=status_code)

    return _f


def _mk_locfunc(f, p):
    "Create a location function for a route"
    from .utils import qp

    class _lf:
        def __init__(self):
            update_wrapper(self, f)

        def __call__(self, *args, **kw):
            return f(*args, **kw)

        def to(self, **kw):
            return qp(p, **kw)

        def __str__(self):
            return p

    return _lf()


# ============================================================================
# Internal: Patches & URL Convertors
# ============================================================================

StringConvertor.regex = "[^/]*"  # `+` replaced with `*`


@patch
def to_string(self: StringConvertor, value: str) -> str:
    "Convert value to string for URL routing"
    value = str(value)
    assert "/" not in value, "May not contain path separators"
    return value


@patch
def url_path_for(self: HTTPConnection, name: str, **path_params):
    "Generate URL path for named route"
    lp = self.scope["app"].url_path_for(name, **path_params)
    return URLPath(f"{self.scope['root_path']}{lp}", lp.protocol, lp.host)


_static_exts = "ico gif jpg jpeg webm css js woff png svg mp4 webp ttf otf eot woff2 txt html map pdf zip tgz gz csv mp3 wav ogg flac aac doc docx xls xlsx ppt pptx epub mobi bmp tiff avi mov wmv mkv xml yaml yml rar 7z tar bz2 htm xhtml apk dmg exe msi swf iso".split()
register_url_convertor("static", "|".join(_static_exts))
