"""StarHTML application factory and configuration utilities"""

import os
from collections.abc import Callable
from typing import TYPE_CHECKING, Any

from fastcore.utils import first
from starlette.middleware.sessions import SessionMiddleware
from starlette.requests import HTTPConnection

from .realtime import StarHTMLWithLiveReload

if TYPE_CHECKING:
    from .core import StarHTML

RouteDecorator = Callable[[Callable[..., Any]], Callable[..., Any]]

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
    "RouteDecorator",
]


class Beforeware:
    def __init__(self, f: Callable[..., Any], skip: list[str] | None = None) -> None:
        self.f, self.skip = f, skip or []


class MiddlewareBase:
    async def __call__(self, scope, receive, send) -> None:
        if scope["type"] not in ["http", "websocket"]:
            await self._app(scope, receive, send)
            return
        return HTTPConnection(scope)


def star_app(
    db_file: str = None,
    render: Callable = None,
    hdrs: tuple = None,
    ftrs: tuple = None,
    tbls: dict = None,
    before: Beforeware | tuple[Any, ...] | None = None,
    after: tuple = None,
    middleware: tuple = None,
    live: bool = False,
    debug: bool = False,
    devtools: bool = False,
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
    sess_cls=SessionMiddleware,
    htmlkw: dict = None,
    bodykw: dict = None,
    reload_attempts: int = 1,
    reload_interval: int = 1000,
    static_path: str = ".",
    body_wrap: Callable = None,
    datastar: str = "patched",
    inline_icons: bool = False,
    **kwargs: Any,
) -> tuple["StarHTML", Callable[..., RouteDecorator]]:
    from .core import noop_body
    from .icons import resolver

    if body_wrap is None:
        body_wrap = noop_body

    # Env var overrides parameter so deployment config wins
    env_val = os.environ.get("STARHTML_INLINE_ICONS")
    resolver.inline = env_val.lower() in ("1", "true", "yes") if env_val is not None else inline_icons
    if resolver.inline:
        resolver.preload_from_disk()

    h = tuple(hdrs or ())
    if not resolver.inline:
        h = (
            iconify_script(),
            _iconify_fill_setup(),
        ) + h

    app = _app_factory(
        hdrs=h,
        ftrs=ftrs,
        before=before,
        after=after,
        middleware=middleware,
        live=live,
        debug=debug,
        devtools=devtools,
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
        sess_cls=sess_cls,
        sess_domain=sess_domain,
        key_fname=key_fname,
        htmlkw=htmlkw,
        bodykw=bodykw,
        reload_attempts=reload_attempts,
        reload_interval=reload_interval,
        body_wrap=body_wrap,
        datastar=datastar,
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


DATASTAR_VERSION = "1.0.0-RC.7+starhtml"
_DATASTAR_CDN_TEMPLATE = "https://cdn.jsdelivr.net/gh/starfederation/datastar@{version}/bundles/datastar.js"
ICONIFY_VERSION = "2.3.0"


def _datastar_cdn_url() -> str:
    # Strip +starhtml build metadata; CDN uses upstream version only
    return _DATASTAR_CDN_TEMPLATE.format(version=DATASTAR_VERSION.split("+")[0])


def def_hdrs(datastar_url="/_pkg/starhtml/datastar.js"):
    from .tags import Meta, Style
    from .xtend import Script

    return [
        # FOUC prevention: hide custom elements until registered; size icon wrappers
        Style(
            ":not(:defined){visibility:hidden} [data-icon-sh]{display:inline-block}"
            " [data-icon-sh].icon-fill :is(path,circle,rect,polygon,ellipse,line,polyline,g){fill:currentColor}"
        ),
        Meta(charset="utf-8"),
        Meta(name="viewport", content="width=device-width, initial-scale=1, viewport-fit=cover"),
        Script(src=datastar_url, type="module"),
    ]


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
    """Iconify CDN web component (auto-included by star_app in CDN mode)."""
    from .xtend import Script

    return Script(
        src=f"https://cdn.jsdelivr.net/npm/iconify-icon@{version or ICONIFY_VERSION}/dist/iconify-icon.min.js",
        type="module",
    )


_ICON_FILL_SHADOW_CSS = ":host(.icon-fill) :is(path,circle,rect,polygon,ellipse,line,polyline,g){fill:currentColor}"


def _iconify_fill_setup():
    """Inject icon-fill CSS into iconify-icon open shadow DOMs via adoptedStyleSheets."""
    from .xtend import Script

    return Script(
        "{"
        f'const s=new CSSStyleSheet();s.replaceSync("{_ICON_FILL_SHADOW_CSS}");'
        "const a=e=>{const r=e.shadowRoot;"
        "if(r&&!r.adoptedStyleSheets.includes(s))r.adoptedStyleSheets=[...r.adoptedStyleSheets,s]};"
        "customElements.whenDefined('iconify-icon').then(()=>{"
        "document.querySelectorAll('iconify-icon').forEach(a);"
        "new MutationObserver(ms=>{for(const m of ms)for(const n of m.addedNodes)"
        "if(n.nodeType===1){if(n.localName==='iconify-icon')a(n);"
        "n.querySelectorAll&&n.querySelectorAll('iconify-icon').forEach(a)}"
        "}).observe(document.documentElement,{childList:true,subtree:true})"
        "})}"
    )


def compression(minimum_size=500, gzip=True, brotli=True, zstd=True, **kwargs):
    """Compression middleware with sensible defaults."""
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
    devtools = kwargs.pop("devtools", False)

    if live:
        kwargs["devtools"] = devtools
        return StarHTMLWithLiveReload(*args, **kwargs)

    kwargs.pop("reload_attempts", None)
    kwargs.pop("reload_interval", None)
    kwargs["devtools"] = devtools

    if bodykw := kwargs.pop("bodykw", None):
        kwargs.update(bodykw)

    return StarHTML(*args, **kwargs)
