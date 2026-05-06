"""Host validation for the app's bound interface.

Unlike Starlette's TrustedHostMiddleware, this accepts loopback aliases
for loopback binds and parses bracketed IPv6 hosts correctly.
"""

import logging

from starlette.responses import JSONResponse
from starlette.types import ASGIApp, Receive, Scope, Send

log = logging.getLogger(__name__)

_LOOPBACK = frozenset({"localhost", "127.0.0.1", "::1"})
_ALL_INTERFACES = frozenset({"0.0.0.0", "::"})


def is_accepted_host(host_header: str, bound_host: str) -> bool:
    if not host_header:
        return False
    h = host_header.strip()
    if h.startswith("["):
        close = h.find("]")
        host_only = h[1:close] if close != -1 else ""
    else:
        host_only = h.rsplit(":", 1)[0] if ":" in h else h
    host_only = host_only.lower()

    bound = bound_host.lower()
    if bound in _ALL_INTERFACES:
        return True
    if bound in _LOOPBACK:
        return host_only in _LOOPBACK
    return host_only == bound


def _host_from_scope(scope: Scope) -> str:
    return next((v.decode("latin-1") for k, v in scope.get("headers", []) if k == b"host"), "")


class HostHeaderMiddleware:
    def __init__(self, app: ASGIApp, bound_host: str) -> None:
        self._app = app
        self._bound_host = bound_host

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            return await self._app(scope, receive, send)
        if not is_accepted_host(_host_from_scope(scope), self._bound_host):
            log.warning("rejecting request with bad Host header: bound=%s", self._bound_host)
            await JSONResponse({"detail": "Invalid Host header"}, status_code=400)(scope, receive, send)
            return
        await self._app(scope, receive, send)
