"CSRF defense-in-depth for unsafe-method requests."

from collections.abc import Callable, Container
from urllib.parse import urlparse

from starlette.datastructures import Headers
from starlette.responses import PlainTextResponse
from starlette.types import ASGIApp, Receive, Scope, Send

_SAFE_METHODS = frozenset({"GET", "HEAD", "OPTIONS"})


def _origin_from_referer(referer: str) -> str:
    p = urlparse(referer)
    return f"{p.scheme}://{p.netloc}" if p.scheme and p.netloc else ""


class OriginValidation:
    def __init__(
        self,
        app: ASGIApp,
        *,
        expected_origins: Container[str],
        bypass_paths: Container[str] = frozenset(),
        on_reject: Callable[[Scope, dict[str, str]], object] | None = None,
    ) -> None:
        self._app = app
        self._expected = expected_origins
        self._bypass = bypass_paths
        self._on_reject = on_reject

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            return await self._app(scope, receive, send)

        method = scope.get("method", "").upper()
        if method in _SAFE_METHODS:
            return await self._app(scope, receive, send)

        path = scope.get("path", "")
        if path in self._bypass:
            return await self._app(scope, receive, send)

        headers = Headers(scope=scope)
        origins = headers.getlist("origin")
        # RFC 6454 allows exactly one Origin; duplicates are safer to reject than reconcile.
        if len(origins) > 1:
            origin, referer, candidate = "<multiple>", "", ""
        else:
            origin = origins[0] if origins else ""
            referer = headers.get("referer", "")
            # Origin: null comes from sandboxed/file contexts; let Referer prove same-origin if present.
            usable = origin if origin and origin != "null" else ""
            candidate = usable or _origin_from_referer(referer)

        if candidate and candidate in self._expected:
            return await self._app(scope, receive, send)

        if self._on_reject:
            self._on_reject(scope, {"method": method, "path": path, "origin": origin, "referer": referer})

        await PlainTextResponse("forbidden: origin mismatch\n", status_code=403)(scope, receive, send)
