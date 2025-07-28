"""StarHTML application factory and configuration utilities"""

from collections.abc import Callable
from typing import Any

from fastcore.utils import first
from fastlite import database
from starlette.requests import HTTPConnection

from .realtime import StarHTMLWithLiveReload

__all__ = ["star_app", "DATASTAR_VERSION", "ICONIFY_VERSION", "def_hdrs", "Beforeware", "MiddlewareBase"]

# ============================================================================
# Main Application Factory
# ============================================================================


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
    exts: list = None,
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
    auto_unpack: bool = True,
    **kwargs: Any,
):
    from .core import noop_body

    if body_wrap is None:
        body_wrap = noop_body
    h = list(hdrs) if hdrs else []

    h = tuple(h)

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
        secret_key=secret_key,
        canonical=canonical,
        session_cookie=session_cookie,
        max_age=max_age,
        sess_path=sess_path,
        same_site=same_site,
        sess_https_only=sess_https_only,
        sess_domain=sess_domain,
        key_fname=key_fname,
        exts=exts,
        htmlkw=htmlkw,
        reload_attempts=reload_attempts,
        reload_interval=reload_interval,
        body_wrap=body_wrap,
        auto_unpack=auto_unpack,
        **(bodykw or {}),
    )
    app.static_route_exts(static_path=static_path)

    if not db_file:
        return app, app.route

    db = database(db_file)
    if not tbls:
        tbls = {}
    if kwargs:
        if isinstance(first(kwargs.values()), dict):
            tbls = kwargs
        else:
            kwargs["render"] = render
            tbls["items"] = kwargs
    dbtbls = [_get_tbl(db.t, k, v) for k, v in tbls.items()]
    if len(dbtbls) == 1:
        dbtbls = dbtbls[0]
    return app, app.route, *dbtbls


# ============================================================================
# Public Helpers & Constants
# ============================================================================

DATASTAR_VERSION = "release-candidate"
ICONIFY_VERSION = "2.3.0"


def def_hdrs(datastar_version=None, include_iconify=True, iconify_version=None, fallback_path="/static/datastar.js"):
    from .tags import Meta, Script

    version = datastar_version or DATASTAR_VERSION
    iconify_ver = iconify_version or ICONIFY_VERSION

    datastarsrc = Script(
        src=f"https://cdn.jsdelivr.net/gh/starfederation/datastar@{version}/bundles/datastar.js",
        type="module",
        onerror=f"this.onerror=null;this.src='{fallback_path}'",
    )

    iconify = (
        Script(src=f"https://cdn.jsdelivr.net/npm/iconify-icon@{iconify_ver}/dist/iconify-icon.min.js", type="module")
        if include_iconify
        else None
    )

    viewport = Meta(name="viewport", content="width=device-width, initial-scale=1, viewport-fit=cover")
    charset = Meta(charset="utf-8")

    base_headers = [charset, viewport, datastarsrc]
    if iconify:
        base_headers.append(iconify)

    return base_headers


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

    if kwargs.pop("live", False):
        return StarHTMLWithLiveReload(*args, **kwargs)
    kwargs.pop("reload_attempts", None)
    kwargs.pop("reload_interval", None)
    return StarHTML(*args, **kwargs)
