"""The `StarHTML` subclass of `Starlette`"""

import asyncio
import logging
import os
import re

logger = logging.getLogger(__name__)
from copy import deepcopy
from functools import partialmethod
from pathlib import Path as PathlibPath
from typing import Protocol, runtime_checkable

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
from starlette.routing import Mount, Route, WebSocketRoute

from .realtime import _ws_endp, set_debug_context, setup_ws
from .server import _mk_locfunc, _wrap_call, _wrap_ex, _wrap_req, all_meths, cookie, render_response, serve
from .starapp import Beforeware, _datastar_cdn_url, def_hdrs
from .utils import _list, _params, get_key, noop_body, reg_re_param


@runtime_checkable
class Registrable(Protocol):
    """Protocol for items registrable with app.register()."""

    def get_package_name(self) -> str: ...
    def get_static_path(self) -> Path | PathlibPath | None: ...
    def get_headers(self, pkg_prefix: str) -> tuple: ...


DEFAULT_PKG_PREFIX = "/_pkg"

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
    "register",
    "register_package",
    "register_package_static",
    "Registrable",
]


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
        static_path=None,
        datastar: str = "patched",
        **bodykw,
    ):
        middleware, before, after = map(_list, (middleware, before, after))
        self.title, self.canonical = title, canonical
        hdrs, ftrs = map(listify, (hdrs, ftrs))

        if datastar == "cdn":
            self._datastar_url = _datastar_cdn_url()
        elif datastar == "patched" or not datastar:
            self._datastar_url = "/_pkg/starhtml/datastar.js"
        else:
            self._datastar_url = datastar

        htmlkw = htmlkw or {}
        if default_hdrs:
            hdrs = def_hdrs(datastar_url=self._datastar_url) + hdrs
        on_startup, on_shutdown = listify(on_startup) or None, listify(on_shutdown) or None
        self.lifespan, self.hdrs, self.ftrs = lifespan, hdrs, ftrs
        self.body_wrap, self.before, self.after, self.htmlkw, self.bodykw = body_wrap, before, after, htmlkw, bodykw
        self._registered_plugins: list = []
        self._plugin_hdrs: tuple = ()
        self._lifecycle_wired: set[int] = set()
        self._registered_packages: set[str] = set()
        self._registered_items: set[int] = set()
        self._import_map: dict[str, str] = {}
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
        env_debug = os.environ.get("STARHTML_DEBUG")
        if env_debug is not None:
            debug = env_debug.lower() in ("1", "true", "yes")

        super().__init__(
            debug,
            routes,
            middleware=middleware,
            exception_handlers=excs,
            on_startup=on_startup,
            on_shutdown=on_shutdown,
            lifespan=lifespan,
        )

        if self.debug:
            logger.warning("StarHTML debug mode is ON. Do not use in production.")
            from .debugger import setup_debugger

            setup_debugger(self)

        if datastar == "patched" or not datastar:
            datastar_path = PathlibPath(__file__).parent / "static" / "datastar.js"

            @self.route("/_pkg/starhtml/datastar.js")
            async def serve_datastar():
                return FileResponse(datastar_path, media_type="application/javascript")

        self.register_package_static(
            name="starhtml",
            static_path=PathlibPath(__file__).parent / "static" / "js",
        )

        if static_path:
            self.static_route_exts(static_path=static_path)

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

    async def handle_request(
        self,
        method: str,
        path: str,
        body: str = "",
        headers: dict | None = None,
    ) -> Response:
        """Async request handler for WASM runtimes (no threading required)."""
        import httpx

        transport = httpx.ASGITransport(app=self)
        async with httpx.AsyncClient(transport=transport, base_url="http://app") as client:
            kwargs = {"method": method.upper(), "url": path, "headers": headers or {}}

            if method.upper() in ("POST", "PUT", "PATCH") and body:
                kwargs["content"] = body

            response = await client.request(**kwargs)

        return Response(
            content=response.content,
            status_code=response.status_code,
            headers=dict(response.headers),
        )


@patch
def _endp(self: StarHTML, f, body_wrap):
    """Create a Starlette-compatible endpoint from a StarHTML route function"""
    sig = signature_ex(f, True)
    _is_debug = self.debug

    async def _f(req):
        resp = None
        req.injects = []
        req.hdrs, req.ftrs, req.htmlkw, req.bodykw = map(deepcopy, (self.hdrs, self.ftrs, self.htmlkw, self.bodykw))
        req.hdrs, req.ftrs = listify(req.hdrs), listify(req.ftrs)
        # No reset needed — each ASGI request gets its own contextvars copy
        if _is_debug:
            set_debug_context(handler=f.__qualname__, route=req.url.path)
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

# Starlette doesn't have the '?', so it chomps the whole remaining URL
reg_re_param("path", ".*?")
_static_exts = "ico gif jpg jpeg webm css js woff png svg mp4 webp ttf otf eot woff2 txt html map pdf zip tgz gz csv mp3 wav ogg flac aac doc docx xls xlsx ppt pptx epub mobi bmp tiff avi mov wmv mkv xml yaml yml rar 7z tar bz2 htm xhtml apk dmg exe msi swf iso".split()
reg_re_param("static", "|".join(_static_exts))


@patch
def register_package_static(self: StarHTML, name: str, static_path, prefix: str = None):
    """Serve a package's static directory under /_pkg/{name}/."""
    if name in self._registered_packages:
        return
    self._registered_packages.add(name)
    static_path = PathlibPath(static_path)
    prefix = prefix or f"/_pkg/{name}"

    async def serve_package_static(request):
        filename = request.path_params.get("filename", "")
        file_path = static_path / filename

        # Prevent path traversal attacks
        try:
            file_path = file_path.resolve()
            if not str(file_path).startswith(str(static_path.resolve())):
                return Response("Forbidden", status_code=403)
        except (ValueError, OSError):
            return Response("Bad Request", status_code=400)

        if file_path.exists() and file_path.is_file():
            return FileResponse(file_path)

        return Response("Not Found", status_code=404)

    route = Route(f"{prefix}/{{filename:path}}", serve_package_static, name=f"pkg_{name}_static")
    self.routes.insert(0, route)


@patch
def mount(self: StarHTML, path: str, app):
    """Mount a child ASGI app, inserting before the catch-all static route."""
    # The catch-all /{ext:static} route would intercept .js/.css requests meant for mounted apps
    routes = self.router.routes
    for i, r in enumerate(routes):
        if ".{ext:" in getattr(r, "path", ""):
            routes.insert(i, Mount(path, app))
            return
    routes.append(Mount(path, app))


@patch
def register_package(self: StarHTML, name: str, static_path=None, hdrs=None, prefix: str = None):
    """Register a package: serve static files and/or add headers."""
    if static_path:
        self.register_package_static(name, static_path, prefix)
    if hdrs:
        self.hdrs = list(self.hdrs) + listify(hdrs)


def _is_import_map(h):
    return getattr(h, "attrs", {}).get("type") == "importmap"


def _register_item(app: StarHTML, item, pkg_prefix: str | None = None):
    """Register a Registrable item (plugin, component, or custom type)."""
    if not isinstance(item, Registrable):
        raise TypeError(
            f"Cannot register {type(item).__name__}. "
            f"Item must implement: get_package_name(), get_static_path(), get_headers()"
        )

    if id(item) in app._registered_items:
        return item
    app._registered_items.add(id(item))

    pkg_prefix = pkg_prefix or DEFAULT_PKG_PREFIX

    # Dependencies like starelements runtime must be served before the component
    if deps := getattr(item, "get_dependencies", None):
        for dep_name, dep_path in deps():
            app.register_package_static(dep_name, dep_path, f"{pkg_prefix}/{dep_name}")

    name, static_path = item.get_package_name(), item.get_static_path()
    full_prefix = f"{pkg_prefix}/{name}" if static_path else ""

    app.register_package(
        name=name,
        static_path=static_path,
        hdrs=item.get_headers(pkg_prefix),
        prefix=full_prefix or None,
    )
    return item


@patch
def register(self: StarHTML, *items, prefix: str | None = None):
    """Register plugins and/or components with the app.

    Works with any object implementing the Registrable protocol:
    - Plugin (from plugins: canvas, persist, scroll, etc.)
    - Component class (decorated with @element from starelements)
    - Custom types implementing get_package_name(), get_static_path(), get_headers()

    Items with on_startup/on_shutdown methods are automatically wired up.
    Multiple register() calls accumulate and regenerate a single unified import map.
    """
    import json

    from .plugins import Plugin, PluginInstance, plugins_hdrs
    from .xtend import Script

    prefix = prefix or DEFAULT_PKG_PREFIX
    plugins, others = [], []
    for item in items:
        (plugins if isinstance(item, Plugin | PluginInstance) else others).append(item)

    for item in others:
        _register_item(self, item, prefix)

    if plugins:
        registered = {p._base_name for p in self._registered_plugins}
        for p in plugins:
            if p._base_name in registered:
                continue
            if p.get_static_path():
                self.register_package_static(
                    p.get_package_name(), p.get_static_path(), f"{prefix}/{p.get_package_name()}"
                )
            self._registered_plugins.append(p)

        old_ids = {id(h) for h in self._plugin_hdrs}
        self.hdrs = [h for h in self.hdrs if id(h) not in old_ids]
        self._plugin_hdrs = tuple(plugins_hdrs(*self._registered_plugins))
        self.hdrs.extend(self._plugin_hdrs)

    for item in items:
        if get_map := getattr(item, "get_import_map", None):
            self._import_map.update(get_map(prefix))

    # Browser requires one import map before any module scripts
    self.hdrs = [
        h for h in self.hdrs if not _is_import_map(h) and not (getattr(h, "src", None) or "").endswith("datastar.js")
    ]
    merged = {"imports": {"datastar": self._datastar_url, **self._import_map}}
    self.hdrs.insert(0, Script(json.dumps(merged), type="importmap"))

    # Wire lifecycle handlers
    for item in items:
        if id(item) in self._lifecycle_wired:
            continue
        self._lifecycle_wired.add(id(item))
        for event in ("startup", "shutdown"):
            method = getattr(item, f"on_{event}", None)
            if method is None:
                continue
            if asyncio.iscoroutinefunction(method):

                async def _async(app=self, m=method):
                    await m(app)

                self.add_event_handler(event, _async)
            else:

                def _sync(app=self, m=method):
                    m(app)

                self.add_event_handler(event, _sync)

    return items[0] if len(items) == 1 else (tuple(items) or None)


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
