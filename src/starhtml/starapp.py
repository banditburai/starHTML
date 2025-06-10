"""The `star_app` convenience wrapper for creating StarHTML applications"""

from collections.abc import Callable
from typing import Any

from fastcore.utils import first
from fastlite import database

from .core import Beforeware, StarHTML, noop_body
from .live_reload import StarHTMLWithLiveReload

__all__ = ["star_app"]


def _get_tbl(dt: Any, nm: str, schema: dict[str, Any]) -> tuple[Any, Any]:
    render = schema.pop("render", None)
    tbl = dt[nm]
    if tbl not in dt:
        tbl.create(**schema)
    else:
        tbl.create(**schema, transform=True)
    dc = tbl.dataclass()
    if render:
        dc.__ft__ = render
    return tbl, dc


def _app_factory(*args, **kwargs) -> StarHTML | StarHTMLWithLiveReload:
    "Creates a StarHTML or StarHTMLWithLiveReload app instance"
    if kwargs.pop("live", False):
        return StarHTMLWithLiveReload(*args, **kwargs)
    kwargs.pop("reload_attempts", None)
    kwargs.pop("reload_interval", None)
    return StarHTML(*args, **kwargs)


def star_app(
    db_file: str | None = None,  # Database file name, if needed
    render: Callable | None = None,  # Function used to render default database class
    hdrs: tuple | None = None,  # Additional FT elements to add to <HEAD>
    ftrs: tuple | None = None,  # Additional FT elements to add to end of <BODY>
    tbls: dict[str, Any] | None = None,  # Experimental mapping from DB table names to dict table definitions
    before: tuple | Beforeware | None = None,  # Functions to call prior to calling handler
    middleware: tuple | None = None,  # Standard Starlette middleware
    live: bool = False,  # Enable live reloading
    debug: bool = False,  # Passed to Starlette, indicating if debug tracebacks should be returned on errors
    routes: tuple | None = None,  # Passed to Starlette
    exception_handlers: dict | None = None,  # Passed to Starlette
    on_startup: Callable | None = None,  # Passed to Starlette
    on_shutdown: Callable | None = None,  # Passed to Starlette
    lifespan: Callable | None = None,  # Passed to Starlette
    default_hdrs: bool = True,  # Include default StarHTML headers?
    exts: list | str | None = None,  # Extensions (deprecated, not used with Datastar)
    canonical: bool = True,  # Automatically include canonical link?
    secret_key: str | None = None,  # Signing key for sessions
    key_fname: str = ".sesskey",  # Session cookie signing key file name
    session_cookie: str = "session_",  # Session cookie name
    max_age: int = 365 * 24 * 3600,  # Session cookie expiry time
    sess_path: str = "/",  # Session cookie path
    same_site: str = "lax",  # Session cookie same site policy
    sess_https_only: bool = False,  # Session cookie HTTPS only?
    sess_domain: str | None = None,  # Session cookie domain
    htmlkw: dict | None = None,  # Attrs to add to the HTML tag
    bodykw: dict | None = None,  # Attrs to add to the Body tag
    reload_attempts: int | None = 1,  # Number of reload attempts when live reloading
    reload_interval: int | None = 1000,  # Time between reload attempts in ms
    static_path: str = ".",  # Where the static file route points to, defaults to root dir
    body_wrap: Callable = noop_body,  # FT wrapper for body contents
    **kwargs: Any,
) -> Any:
    "Create a StarHTML app with optional live reloading."
    h = tuple(hdrs) if hdrs else ()

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
