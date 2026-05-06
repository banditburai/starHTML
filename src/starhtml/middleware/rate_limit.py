"""In-process per-IP token bucket for one path.

This is a brute-force speed bump, not a durable global limit. Behind a
trusted reverse proxy, mount ProxyHeadersMiddleware outside this layer;
without a trusted proxy, doing so lets attackers forge the bucket key.
Multi-worker servers get one bucket table per worker.
"""

import time
from collections.abc import Callable

from starlette.responses import PlainTextResponse
from starlette.types import ASGIApp, Receive, Scope, Send

_DEFAULT_REFILL = 10 / 60


class PathRateLimit:
    def __init__(
        self,
        app: ASGIApp,
        *,
        path: str,
        method: str = "POST",
        capacity: float = 10,
        refill_per_second: float = _DEFAULT_REFILL,
        retry_after_seconds: int = 60,
        on_throttle: Callable[[Scope, str], object] | None = None,
        time_fn: Callable[[], float] | None = None,
    ) -> None:
        self._app = app
        self._path = path
        self._method = method.upper()
        self._capacity = float(capacity)
        self._refill = float(refill_per_second)
        self._retry_after = retry_after_seconds
        self._on_throttle = on_throttle
        self._time = time_fn or time.monotonic
        self._buckets: dict[str, tuple[float, float]] = {}

    def _take_token(self, ip: str) -> bool:
        now = self._time()
        last, tokens = self._buckets.get(ip, (now, self._capacity))
        tokens = min(self._capacity, tokens + max(0.0, now - last) * self._refill)
        if tokens >= 1.0:
            self._buckets[ip] = (now, tokens - 1.0)
            return True
        self._buckets[ip] = (now, tokens)
        return False

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            return await self._app(scope, receive, send)
        if scope.get("method", "").upper() != self._method or scope.get("path", "") != self._path:
            return await self._app(scope, receive, send)

        client = scope.get("client") or ("unknown", 0)
        ip = client[0]
        if self._take_token(ip):
            return await self._app(scope, receive, send)

        if self._on_throttle:
            self._on_throttle(scope, ip)

        await PlainTextResponse(
            "too many requests\n",
            status_code=429,
            headers={"Retry-After": str(self._retry_after)},
        )(scope, receive, send)
