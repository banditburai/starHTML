"""The `StarHTML` subclass of `Starlette`"""

import logging
import os
import re

logger = logging.getLogger(__name__)
from collections.abc import Callable, Collection, Sequence
from contextlib import asynccontextmanager, nullcontext
from functools import partialmethod
from pathlib import Path as PathlibPath
from typing import TYPE_CHECKING, Any, Literal, Protocol, runtime_checkable

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

from .realtime import _ws_endp, set_devtools_context, setup_ws
from .server import _handle, _mk_locfunc, _wrap_call, _wrap_ex, _wrap_req, all_meths, cookie, render_response, serve
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
    "StarRoute",
    "Lifespan",
    "Request",
    "Response",
    "Route",
    "Mount",
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


async def _run_handler(handler, app):
    # Use inspect.signature directly (no eval_str) — lifespan dispatch only
    # needs param count. Resolving annotations would crash on forward-refs
    # whose target isn't importable from the handler's module (e.g. starimo's
    # `on_startup(self, app: "Starlette")` where Starlette isn't imported).
    import inspect

    takes_arg = bool(inspect.signature(handler).parameters)
    await _handle(handler, [app] if takes_arg else [])


class Lifespan:
    """Handlers run INSIDE the user lifespan so they can access resources it initializes."""

    def __init__(self, startup=None, shutdown=None, lifespan=None):
        self.startup = listify(startup)
        self.shutdown = listify(shutdown)
        self.lifespan = lifespan

    @asynccontextmanager
    async def __call__(self, app):
        ctx = self.lifespan(app) if self.lifespan else nullcontext()
        # Forward lifespan state (Starlette 1.0 removed the fallback that
        # swallowed it; without this req.state.X raises AttributeError).
        async with ctx as state:
            for f in self.startup:
                await _run_handler(f, app)
            yield state
            for f in self.shutdown:
                await _run_handler(f, app)


class StarRoute(Route):
    """Route that runs endpoints through StarHTML's request pipeline.

    Must be bound to a StarHTML app — auto-bound when passed via
    ``StarHTML(routes=[...])``, ``app.add_route(...)``, or ``app=`` on
    the constructor.
    """

    def __init__(
        self,
        path: str,
        endpoint: Callable[..., Any],
        *,
        app: "StarHTML | None" = None,
        methods: Collection[str] | None = None,
        name: str | None = None,
        include_in_schema: bool = True,
        middleware: Sequence[Middleware] | None = None,
        body_wrap: Callable[..., Any] | None = None,
    ) -> None:
        self._original_endpoint = endpoint
        self._body_wrap = body_wrap
        self._bound = False
        methods = methods or ["GET", "POST"]
        super().__init__(
            path, endpoint, methods=methods, name=name, include_in_schema=include_in_schema, middleware=middleware
        )
        if app:
            self._bind(app)

    def _bind(self, app):
        if self._bound:
            return
        if not isinstance(app, StarHTML):
            raise TypeError(
                f"StarRoute({self.path!r}) requires a StarHTML app, got {type(app).__name__}. "
                "Use StarHTML(routes=[...]) or pass app= to StarRoute."
            )
        wrapped = app._endp(self._original_endpoint, self._body_wrap or app.body_wrap)
        super().__init__(
            self.path,
            wrapped,
            methods=self.methods,
            name=self.name,
            include_in_schema=self.include_in_schema,
        )
        self._bound = True

    async def handle(self, scope, receive, send):
        if not self._bound:
            raise RuntimeError(
                f"StarRoute({self.path!r}) was never bound to a StarHTML app. "
                "Pass it via StarHTML(routes=[...]) or app.add_route(...)."
            )
        await super().handle(scope, receive, send)


class StarHTML(Starlette):
    def __init__(
        self,
        debug=False,
        devtools=False,
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
        self._lifespan = Lifespan(on_startup, on_shutdown, lifespan)
        self.hdrs, self.ftrs = hdrs, ftrs
        self.body_wrap, self.before, self.after, self.htmlkw, self.bodykw = body_wrap, before, after, htmlkw, bodykw
        self._registered_plugins: list = []
        self._plugin_hdrs: tuple = ()
        self._lifecycle_wired: set[int] = set()
        self._registered_packages: dict[str, PathlibPath] = {}
        self._registered_items: set[int] = set()
        self._import_map: dict[str, str] = {}
        if sess_cls:
            secret_key = get_key(secret_key, key_fname)
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

        env_devtools = os.environ.get("STARHTML_DEVTOOLS")
        if env_devtools is not None:
            env_lower = env_devtools.lower()
            if env_lower == "capture":
                devtools = "capture"
            else:
                devtools = env_lower in ("1", "true", "yes")
        self._devtools = devtools

        super().__init__(
            debug,
            routes,
            middleware=middleware,
            exception_handlers=excs,
            lifespan=self._lifespan,
        )

        self._bind_star_routes(self.router.routes)

        # One route for all framework JS avoids chunk 404s when plugins share bundled dependencies
        self.register_package_static(
            name="starhtml",
            static_path=PathlibPath(__file__).parent / "static" / "js",
        )

        if self.debug:
            logger.warning("StarHTML debug mode is ON. Do not use in production.")

        if self._devtools:
            from .devtools import setup_devtools

            setup_devtools(self, mode=self._devtools)

        if static_path:
            self.static_route_exts(static_path=static_path)

    def _bind_star_routes(self, routes):
        for route in routes:
            if isinstance(route, StarRoute):
                route._bind(self)
            elif isinstance(route, Mount) and route.routes:
                self._bind_star_routes(route.routes)

    def add_route(self, route):
        if isinstance(route, StarRoute):
            route._bind(self)
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

    if TYPE_CHECKING:

        def register(self, *items: Any, prefix: str | None = None) -> None: ...
        def register_package(
            self, name: str, static_path: Any = None, hdrs: Any = None, prefix: str | None = None
        ) -> None: ...
        def register_package_static(self, name: str, static_path: Any, prefix: str | None = None) -> None: ...
        def static_route_exts(self, prefix: str = "/", static_path: str = ".", exts: str = "static") -> None: ...
        def static_route(self, ext: str = "", prefix: str = "/", static_path: str = ".") -> None: ...

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

    def add_lifecycle_handler(self, event: Literal["startup", "shutdown"], handler: Callable) -> None:
        """Register a startup or shutdown handler."""
        getattr(self._lifespan, event).append(handler)

    def on_event(self, event: Literal["startup", "shutdown"]) -> Callable:
        """Decorator to register a startup or shutdown handler."""

        def _decorator(func: Callable) -> Callable:
            self.add_lifecycle_handler(event, func)
            return func

        return _decorator

    def add_exception_handler(self, exc_class_or_status_code: int | type[Exception], handler: Callable) -> None:
        wrapped = _wrap_ex(
            handler,
            exc_class_or_status_code,
            self.hdrs,
            self.ftrs,
            self.htmlkw,
            self.bodykw,
            body_wrap=self.body_wrap,
        )
        super().add_exception_handler(exc_class_or_status_code, wrapped)

    def exception_handler(self, exc_class_or_status_code: int | type[Exception]) -> Callable:
        """Decorator to register an exception handler."""

        def _decorator(func: Callable) -> Callable:
            self.add_exception_handler(exc_class_or_status_code, func)
            return func

        return _decorator


@patch
def _endp(self: StarHTML, f, body_wrap):
    sig = signature_ex(f, True)
    _has_devtools = self._devtools

    async def _f(req):
        resp = None
        req.injects = []
        req.hdrs, req.ftrs = list(self.hdrs), list(self.ftrs)
        req.htmlkw, req.bodykw = dict(self.htmlkw), dict(self.bodykw)
        # No reset needed — each ASGI request gets its own contextvars copy
        if _has_devtools:
            set_devtools_context(handler=f.__qualname__, route=req.url.path)
        for b in self.before:
            if not resp:
                if isinstance(b, Beforeware):
                    bf, skip = b.f, b.skip
                else:
                    bf, skip = b, []
                if not any(re.fullmatch(r, req.url.path) for r in skip):
                    resp = await _wrap_call(bf, req, _params(bf))
        # Beforeware may set req.body_wrap to override the shell for this
        # request; only fall back to the route/app default if it didn't.
        if getattr(req, "body_wrap", None) is None:
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
    endp = _ws_endp(func, conn, disconn)
    route = WebSocketRoute(path, endpoint=endp, name=name, middleware=middleware)
    route.methods = ["ws"]
    self.add_route(route)
    return func


@patch
def ws(self: StarHTML, path: str, conn=None, disconn=None, name=None, middleware=None):
    def f(func=noop):
        return self._add_ws(func, path, conn, disconn, name=name, middleware=middleware)  # type: ignore[attr-defined]

    return f


def nested_name(f):
    """Get name of function `f` using '_' to join nested function names"""
    return f.__qualname__.replace(".<locals>.", "_")


@patch
def _add_route(self: StarHTML, func, path, methods, name, include_in_schema, body_wrap):
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
    route = StarRoute(
        p,
        func,
        app=self,
        methods=m,
        name=n,
        include_in_schema=include_in_schema,
        body_wrap=body_wrap,
    )
    self.add_route(route)
    lf = _mk_locfunc(func, p)
    lf.__routename__ = n
    return lf


@patch
def route(
    self: StarHTML,
    path: str | Callable[..., Any] | None = None,
    methods: list[str] | str | None = None,
    name: str | None = None,
    include_in_schema: bool = True,
    body_wrap: Callable[..., Any] | None = None,
) -> Callable[..., Any]:
    def f(func: Callable[..., Any]) -> Callable[..., Any]:
        return self._add_route(func, path, methods, name=name, include_in_schema=include_in_schema, body_wrap=body_wrap)  # type: ignore[attr-defined]

    return f(path) if callable(path) else f


for o in all_meths:
    setattr(StarHTML, o, partialmethod(StarHTML.route, methods=o))

# Starlette doesn't have the '?', so it chomps the whole remaining URL
reg_re_param("path", ".*?")
_static_exts = "ico gif jpg jpeg webm css js woff png svg mp4 webp ttf otf eot woff2 txt html map pdf zip tgz gz csv mp3 wav ogg flac aac doc docx xls xlsx ppt pptx epub mobi bmp tiff avi mov wmv mkv xml yaml yml rar 7z tar bz2 htm xhtml apk dmg exe msi swf iso".split()
reg_re_param("static", "|".join(_static_exts))


@patch
def register_package_static(self: StarHTML, name: str, static_path, prefix: str = None):
    """Serve a package's static directory under /_pkg/{name}/.

    Skips route creation when the path is already covered by a parent registration
    (e.g. ``static/js/plugins/`` is a no-op when ``static/js/`` already serves
    subdirectories via its ``{filename:path}`` pattern).
    """
    if name in self._registered_packages:
        return
    static_path = PathlibPath(static_path)
    resolved = static_path.resolve()
    covered = any(resolved.is_relative_to(r) for r in self._registered_packages.values())
    self._registered_packages[name] = resolved
    if covered:
        return

    prefix = prefix or f"/_pkg/{name}"

    async def serve_package_static(request):
        filename = request.path_params.get("filename", "")
        file_path = static_path / filename

        try:
            file_path = file_path.resolve()
            if not file_path.is_relative_to(resolved):
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

    for item in items:
        if id(item) in self._lifecycle_wired:
            continue
        self._lifecycle_wired.add(id(item))
        for event in ("startup", "shutdown"):
            if (method := getattr(item, f"on_{event}", None)) is not None:
                self.add_lifecycle_handler(event, method)

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
