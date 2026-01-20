"""StarHTML application factory and configuration utilities"""

from collections.abc import Callable
from typing import Any

from fastcore.utils import first
from starlette.requests import HTTPConnection

from .realtime import StarHTMLWithLiveReload

__all__ = [
    "star_app",
    "DATASTAR_VERSION",
    "ICONIFY_VERSION",
    "def_hdrs",
    "theme_script",
    "iconify_script",
    "compression",
    "Beforeware",
    "MiddlewareBase",
]


def star_app(
    db_file: str = None,
    render: Callable = None,
    hdrs: tuple = None,
    ftrs: tuple = None,
    tbls: dict = None,
    before: tuple = None,
    middleware: tuple = None,
    live: bool = False,
    debug: bool = False,
    routes: tuple = None,
    exception_handlers: dict = None,
    on_startup: Callable = None,
    on_shutdown: Callable = None,
    lifespan: Callable = None,
    default_hdrs: bool = True,
    title: str = "StarHTML page",
    canonical: bool = True,
    secret_key: str = None,
    key_fname: str = ".sesskey",
    session_cookie: str = "session_",
    max_age: int = 365 * 24 * 3600,
    sess_path: str = "/",
    same_site: str = "lax",
    sess_https_only: bool = False,
    sess_domain: str = None,
    htmlkw: dict = None,
    bodykw: dict = None,
    reload_attempts: int = 1,
    reload_interval: int = 1000,
    static_path: str = ".",
    body_wrap: Callable = None,
    **kwargs: Any,
):
    from .core import noop_body

    if body_wrap is None:
        body_wrap = noop_body
    h = tuple(hdrs or ())

    app = _app_factory(
        hdrs=h,
        ftrs=ftrs,
        before=before,
        middleware=middleware,
        live=live,
        debug=debug,
        routes=routes,
        exception_handlers=exception_handlers,
        on_startup=on_startup,
        on_shutdown=on_shutdown,
        lifespan=lifespan,
        default_hdrs=default_hdrs,
        title=title,
        secret_key=secret_key,
        canonical=canonical,
        session_cookie=session_cookie,
        max_age=max_age,
        sess_path=sess_path,
        same_site=same_site,
        sess_https_only=sess_https_only,
        sess_domain=sess_domain,
        key_fname=key_fname,
        htmlkw=htmlkw,
        bodykw=bodykw,
        reload_attempts=reload_attempts,
        reload_interval=reload_interval,
        body_wrap=body_wrap,
    )
    app.static_route_exts(static_path=static_path)

    if not db_file:
        return app, app.route

    from fastlite import database

    db = database(db_file)

    tables = tbls or {}
    if kwargs:
        if isinstance(first(kwargs.values()), dict):
            tables = kwargs
        else:
            table_schema = kwargs.copy()
            if render:
                table_schema["render"] = render
            tables = {"items": table_schema}

    db_tables = [_get_tbl(db.t, name, schema) for name, schema in tables.items()]
    if len(db_tables) == 1:
        return app, app.route, *db_tables[0]
    return app, app.route, *db_tables


DATASTAR_VERSION = "1.0.0-RC.7"
ICONIFY_VERSION = "2.3.0"


def def_hdrs(fallback_path="/static/datastar.js"):
    """Generate default headers for StarHTML apps."""
    from .tags import Meta, Style
    from .xtend import Script

    headers = [
        Style(":not(:defined){visibility:hidden}"),  # Prevent FOUC for custom elements
        Meta(charset="utf-8"),
        Meta(name="viewport", content="width=device-width, initial-scale=1, viewport-fit=cover"),
        Script(src=fallback_path, type="module"),
    ]

    return headers


def theme_script(
    storage_key="theme",
    cls="dark",
    system_match="(prefers-color-scheme: dark)",
    use_data_theme=False,
    default_theme="light",
):
    """Inline script to prevent theme flash. MUST be first in headers to execute before rendering."""
    from .xtend import Script

    if use_data_theme:
        return Script(
            f"const useAlt=localStorage.{storage_key}==='{cls}'||"
            f"(!('{storage_key}' in localStorage)&&window.matchMedia('{system_match}').matches);"
            f"document.documentElement.setAttribute('data-theme',useAlt?'{cls}':'{default_theme}');"
        )
    else:
        return Script(
            f"document.documentElement.classList.toggle('{cls}',"
            f"localStorage.{storage_key}==='{cls}'||"
            f"(!('{storage_key}' in localStorage)&&window.matchMedia('{system_match}').matches));"
        )


def iconify_script(version=None):
    """Iconify web component script. Required if using Icon() component."""
    from .xtend import Script

    ver = version or ICONIFY_VERSION
    return Script(
        src=f"https://cdn.jsdelivr.net/npm/iconify-icon@{ver}/dist/iconify-icon.min.js",
        type="module",
    )


def compression(minimum_size=500, gzip=True, brotli=True, zstd=True, **kwargs):
    """Compression middleware helper. Wraps starlette-compress for response compression."""
    from starlette.middleware import Middleware
    from starlette_compress import CompressMiddleware

    return Middleware(
        CompressMiddleware,
        minimum_size=minimum_size,
        gzip=gzip,
        brotli=brotli,
        zstd=zstd,
        **kwargs,
    )


class Beforeware:
    def __init__(self, f, skip=None):
        self.f, self.skip = f, skip or []


class MiddlewareBase:
    async def __call__(self, scope, receive, send) -> None:
        if scope["type"] not in ["http", "websocket"]:
            await self._app(scope, receive, send)
            return
        return HTTPConnection(scope)


def _get_tbl(dt: Any, nm: str, schema: dict):
    schema_copy = schema.copy()
    render = schema_copy.pop("render", None)
    tbl = dt[nm]
    if tbl not in dt:
        tbl.create(**schema_copy)
    else:
        tbl.create(**schema_copy, transform=True)
    dc = tbl.dataclass()
    if render:
        dc.__ft__ = render
    return tbl, dc


def _app_factory(*args, **kwargs):
    from .core import StarHTML

    live = kwargs.pop("live", False)

    if live:
        kwargs.setdefault("debug", True)  # Live reload needs debug for proper error display
        return StarHTMLWithLiveReload(*args, **kwargs)

    kwargs.pop("reload_attempts", None)
    kwargs.pop("reload_interval", None)

    # Unpack bodykw for StarHTML's **bodykw signature
    if bodykw := kwargs.pop("bodykw", None):
        kwargs.update(bodykw)

    return StarHTML(*args, **kwargs)
