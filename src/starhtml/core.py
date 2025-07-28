"""The `StarHTML` subclass of `Starlette`"""

import re
from copy import deepcopy
from functools import partialmethod
from inspect import Parameter

from fastcore.utils import (
    Path,
    ifnone,
    listify,
    noop,
    patch,
    signature_ex,
)
from starlette.applications import Starlette
from starlette.exceptions import HTTPException
from starlette.middleware import Middleware
from starlette.middleware.sessions import SessionMiddleware
from starlette.requests import Request
from starlette.responses import FileResponse, RedirectResponse, Response
from starlette.routing import Route, WebSocketRoute

from .realtime import _ws_endp, setup_ws
from .server import _mk_locfunc, _wrap_call, _wrap_ex, _wrap_req, all_meths, cookie, render_response, serve
from .starapp import DATASTAR_VERSION, Beforeware, def_hdrs
from .utils import _list, _params, empty, get_key, noop_body, reg_re_param
from .xtend import Script

empty = Parameter.empty

__all__ = [
    "StarHTML",
    "Request",
    "Response",
    "Route",
    "WebSocketRoute",
    "HTTPException",
    "RedirectResponse",
    "serve",
    "setup_ws",
    "cookie",
    "nested_name",
]

# ============================================================================
# Main StarHTML Application Class
# ============================================================================


class StarHTML(Starlette):
    def __init__(
        self,
        debug=False,
        routes=None,
        middleware=None,
        title: str = "StarHTML page",
        exception_handlers=None,
        on_startup=None,
        on_shutdown=None,
        lifespan=None,
        hdrs=None,
        ftrs=None,
        exts=None,
        before=None,
        after=None,
        default_hdrs=True,
        sess_cls=SessionMiddleware,
        secret_key=None,
        session_cookie="session_",
        max_age=365 * 24 * 3600,
        sess_path="/",
        same_site="lax",
        sess_https_only=False,
        sess_domain=None,
        key_fname=".sesskey",
        body_wrap=noop_body,
        htmlkw=None,
        canonical=True,
        datastar_version=None,
        include_iconify=True,
        iconify_version=None,
        auto_unpack=True,
        **bodykw,
    ):
        middleware, before, after = map(_list, (middleware, before, after))
        self.title, self.canonical = title, canonical
        hdrs, ftrs, exts = map(listify, (hdrs, ftrs, exts))
        # Extensions are currently not used with Datastar
        if exts:
            exts = {}
        htmlkw = htmlkw or {}
        if default_hdrs:
            hdrs = def_hdrs(datastar_version, include_iconify, iconify_version) + hdrs
        if exts:
            # Script is now imported at top of file
            hdrs += [Script(src=ext) for ext in exts]
        on_startup, on_shutdown = listify(on_startup) or None, listify(on_shutdown) or None
        self.lifespan, self.hdrs, self.ftrs = lifespan, hdrs, ftrs
        self.body_wrap, self.before, self.after, self.htmlkw, self.bodykw = body_wrap, before, after, htmlkw, bodykw
        secret_key = get_key(secret_key, key_fname)
        if sess_cls:
            sess = Middleware(
                sess_cls,
                secret_key=secret_key,
                session_cookie=session_cookie,
                max_age=max_age,
                path=sess_path,
                same_site=same_site,
                https_only=sess_https_only,
                domain=sess_domain,
            )
            middleware.append(sess)
        exception_handlers = ifnone(exception_handlers, {})
        if 404 not in exception_handlers:

            def _not_found(req, exc):
                return Response("404 Not Found", status_code=404)

            exception_handlers[404] = _not_found
        excs = {
            k: _wrap_ex(v, k, hdrs, ftrs, htmlkw, bodykw, body_wrap=body_wrap) for k, v in exception_handlers.items()
        }
        super().__init__(
            debug,
            routes,
            middleware=middleware,
            exception_handlers=excs,
            on_startup=on_startup,
            on_shutdown=on_shutdown,
            lifespan=lifespan,
        )
        self.state.auto_unpack = auto_unpack

        # Serve datastar.js fallback (CDN-first approach in headers)
        from pathlib import Path

        import httpx
        from starlette.responses import FileResponse, Response

        datastar_path = Path(__file__).parent / "static" / "datastar.js"
        datastar_cdn = f"https://cdn.jsdelivr.net/gh/starfederation/datastar@{DATASTAR_VERSION}/bundles/datastar.js"

        async def serve_datastar_fallback():
            # Serve cached version if exists
            if datastar_path.exists():
                return FileResponse(datastar_path, media_type="application/javascript")

            # Download from CDN and cache
            try:
                async with httpx.AsyncClient() as client:
                    response = await client.get(datastar_cdn)
                    response.raise_for_status()
                    datastar_path.parent.mkdir(parents=True, exist_ok=True)
                    datastar_path.write_text(response.text)
                    return Response(response.text, media_type="application/javascript")
            except Exception as e:
                raise FileNotFoundError(f"datastar.js unavailable: {e}")

        self.route("/static/datastar.js")(serve_datastar_fallback)

        static_js_dir = Path(__file__).parent / "static" / "js"

        @self.route("/static/js/{filename:path}")
        async def serve_starhtml_js(filename: str):
            """Serve StarHTML's built-in JavaScript files (including subdirectories)."""
            js_file = static_js_dir / filename
            if js_file.exists() and js_file.is_file():
                return FileResponse(js_file, media_type="application/javascript")
            return Response("Not Found", status_code=404)

        static_css_dir = Path(__file__).parent / "static" / "css"

        @self.route("/static/css/{filename}")
        async def serve_starhtml_css(filename: str):
            """Serve StarHTML's built-in CSS files."""
            css_file = static_css_dir / filename
            if css_file.exists() and css_file.is_file():
                return FileResponse(css_file, media_type="text/css")
            return Response("Not Found", status_code=404)

    def add_route(self, route) -> None:
        route.methods = [m.upper() if isinstance(m, str) else m for m in listify(route.methods)]
        self.router.routes = [
            r
            for r in self.router.routes
            if not (
                getattr(r, "path", None) == route.path
                and getattr(r, "name", None) == route.name
                and ((route.methods is None) or (set(getattr(r, "methods", [])) == set(route.methods)))
            )
        ]
        self.router.routes.append(route)


@patch
def _endp(self: StarHTML, f, body_wrap):
    """Create a Starlette-compatible endpoint from a StarHTML route function"""
    sig = signature_ex(f, True)

    async def _f(req):
        resp = None
        req.injects = []
        req.hdrs, req.ftrs, req.htmlkw, req.bodykw = map(deepcopy, (self.hdrs, self.ftrs, self.htmlkw, self.bodykw))
        req.hdrs, req.ftrs = listify(req.hdrs), listify(req.ftrs)
        for b in self.before:
            if not resp:
                if isinstance(b, Beforeware):
                    bf, skip = b.f, b.skip
                else:
                    bf, skip = b, []
                if not any(re.fullmatch(r, req.url.path) for r in skip):
                    resp = await _wrap_call(bf, req, _params(bf))
        req.body_wrap = body_wrap
        if not resp:
            resp = await _wrap_call(f, req, sig.parameters)
        for a in self.after:
            _, *wreq = await _wrap_req(req, _params(a))
            nr = a(resp, *wreq)
            if nr:
                resp = nr
        return render_response(req, resp, sig.return_annotation)

    return _f


@patch
def _add_ws(self: StarHTML, func, path, conn, disconn, name, middleware):
    """Add a WebSocket route to the application"""
    endp = _ws_endp(func, conn, disconn)
    route = WebSocketRoute(path, endpoint=endp, name=name, middleware=middleware)
    route.methods = ["ws"]
    self.add_route(route)
    return func


@patch
def ws(self: StarHTML, path: str, conn=None, disconn=None, name=None, middleware=None):
    """Add a websocket route at `path`"""

    def f(func=noop):
        return self._add_ws(func, path, conn, disconn, name=name, middleware=middleware)  # type: ignore[attr-defined]

    return f


def nested_name(f):
    """Get name of function `f` using '_' to join nested function names"""
    return f.__qualname__.replace(".<locals>.", "_")


@patch
def _add_route(self: StarHTML, func, path, methods, name, include_in_schema, body_wrap):
    """Add an HTTP route to the application"""
    n, fn, p = name, nested_name(func), None if callable(path) else path
    if methods:
        m = [methods] if isinstance(methods, str) else methods
    elif fn in all_meths and p is not None:
        m = [fn]
    else:
        m = ["get", "post"]
    if not n:
        n = fn
    if not p:
        p = "/" + ("" if fn == "index" else fn)
    route = Route(
        p,
        endpoint=self._endp(func, body_wrap or self.body_wrap),
        methods=m,
        name=n,
        include_in_schema=include_in_schema,
    )
    self.add_route(route)
    lf = _mk_locfunc(func, p)
    lf.__routename__ = n
    return lf


@patch
def route(self: StarHTML, path: str = None, methods=None, name=None, include_in_schema=True, body_wrap=None):
    """Add a route at `path`"""

    def f(func):
        return self._add_route(func, path, methods, name=name, include_in_schema=include_in_schema, body_wrap=body_wrap)  # type: ignore[attr-defined]

    return f(path) if callable(path) else f


# Add HTTP method decorators (@app.get, @app.post, etc.) via @patch
for o in all_meths:
    setattr(StarHTML, o, partialmethod(StarHTML.route, methods=o))

# ============================================================================
# URL Parameter Registration & Static File Serving
# ============================================================================

# Starlette doesn't have the '?', so it chomps the whole remaining URL
reg_re_param("path", ".*?")
_static_exts = "ico gif jpg jpeg webm css js woff png svg mp4 webp ttf otf eot woff2 txt html map pdf zip tgz gz csv mp3 wav ogg flac aac doc docx xls xlsx ppt pptx epub mobi bmp tiff avi mov wmv mkv xml yaml yml rar 7z tar bz2 htm xhtml apk dmg exe msi swf iso".split()
reg_re_param("static", "|".join(_static_exts))


@patch
def static_route_exts(self: StarHTML, prefix="/", static_path=".", exts="static"):
    """Add a static route at URL path `prefix` with files from `static_path` and `exts` defined by `reg_re_param()`"""

    @self.route(f"{prefix}{{fname:path}}.{{ext:{exts}}}")
    async def get(fname: str, ext: str):
        return FileResponse(f"{static_path}/{fname}.{ext}")


@patch
def static_route(self: StarHTML, ext="", prefix="/", static_path="."):
    """Add a static route at URL path `prefix` with files from `static_path` and single `ext` (including the '.')"""

    @self.route(f"{prefix}{{fname:path}}{ext}")
    async def get(fname: str):
        return FileResponse(f"{static_path}/{fname}{ext}")


# ============================================================================
# Development Tools Support
# ============================================================================

devtools_loc = "/.well-known/appspecific/com.chrome.devtools.json"


@patch
def devtools_json(self: StarHTML, path=None, uuid=None):
    """Add a devtools JSON endpoint for Chrome DevTools integration"""
    if not path:
        path = Path().absolute()
    if not uuid:
        uuid = get_key()

    @self.route(devtools_loc)
    def devtools():
        return dict(workspace=dict(root=path, uuid=uuid))
