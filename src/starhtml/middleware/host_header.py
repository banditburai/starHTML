"""Host-header validation: reject DNS-rebinding / cross-host attacks.

Stricter than Starlette's ``TrustedHostMiddleware`` in two ways:

* Case-insensitive matching (browsers may capitalize ``Host``).
* Correct IPv6 bracket parsing — ``[::1]:8282`` is unwrapped to ``::1``,
  not to ``[`` like ``host.split(":")[0]`` would yield.
"""

import logging

log = logging.getLogger(__name__)

_LOOPBACK = frozenset({"localhost", "127.0.0.1", "::1"})
_ALL_INTERFACES = frozenset({"0.0.0.0", "::"})


def is_accepted_host(host_header, bound_host):
    """True if ``host_header`` targets the interface we bound to.

    * Empty Host header → rejected.
    * Loopback bind: any of {localhost, 127.0.0.1, ::1} accepted.
    * Non-loopback bind: exact match required (port stripped, case-insensitive).
    * 0.0.0.0 / :: bind: always accepted (no Host-layer gate possible).
    """
    if not host_header:
        return False
    h = host_header.strip()
    if h.startswith("["):
        close = h.find("]")
        # Malformed bracket form: fail closed rather than guess.
        host_only = h[1:close] if close != -1 else h.strip("[]")
    else:
        host_only = h.rsplit(":", 1)[0] if ":" in h else h
    host_only = host_only.lower()

    if bound_host in _ALL_INTERFACES:
        return True
    bound = bound_host.lower()
    if bound in _LOOPBACK:
        return host_only in _LOOPBACK
    return host_only == bound


def _host_from_scope(scope):
    for k, v in scope.get("headers", []):
        if k == b"host":
            try:
                return v.decode("latin-1")
            except UnicodeDecodeError:
                return ""
    return ""


class HostHeaderMiddleware:
    "ASGI middleware: 400 when the Host header doesn't match the bound interface."

    def __init__(self, app, bound_host):
        self._app = app
        self._bound_host = bound_host

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            return await self._app(scope, receive, send)
        if not is_accepted_host(_host_from_scope(scope), self._bound_host):
            log.warning("rejecting request with bad Host header: bound=%s", self._bound_host)
            body = b'{"detail":"Invalid Host header"}'
            await send({
                "type": "http.response.start",
                "status": 400,
                "headers": [
                    (b"content-type", b"application/json"),
                    (b"content-length", str(len(body)).encode()),
                ],
            })
            await send({"type": "http.response.body", "body": body})
            return
        await self._app(scope, receive, send)
