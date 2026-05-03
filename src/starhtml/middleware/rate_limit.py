"""Per-IP token-bucket rate limiter scoped to a single path.

State is in-process (``dict`` keyed by client IP) and resets on restart —
deliberate: this is a brute-force speed bump, not a durable record.

Source IP comes from ``scope["client"][0]``. If you're behind a reverse
proxy, mount ``uvicorn.middleware.proxy_headers.ProxyHeadersMiddleware``
*outside* this middleware so ``X-Forwarded-For`` is un-wrapped first; if
you're NOT behind a trusted proxy, don't mount ProxyHeaders at all (it
would let any remote attacker forge a bucket key).

Multi-worker uvicorn (``--workers N``) gives each worker its own bucket
dict — effective limit becomes ``N × capacity`` per IP. Production
deployments needing a shared limit should swap in a Redis-backed limiter.
"""

import time

_DEFAULT_REFILL = 10 / 60  # 10 tokens per minute


class PathRateLimit:
    """ASGI middleware: 429 + Retry-After when a bucket is exhausted.

    ``on_throttle(scope, client_ip)`` fires on every 429 — wire it to your
    audit/log/metrics."""

    def __init__(
        self,
        app,
        *,
        path,
        method="POST",
        capacity=10,
        refill_per_second=_DEFAULT_REFILL,
        retry_after_seconds=60,
        on_throttle=None,
        time_fn=None,
    ):
        self._app = app
        self._path = path
        self._method = method.upper()
        self._capacity = float(capacity)
        self._refill = float(refill_per_second)
        self._retry_after = retry_after_seconds
        self._on_throttle = on_throttle
        self._time = time_fn or time.monotonic
        self._buckets = {}

    def _take_token(self, ip):
        now = self._time()
        last, tokens = self._buckets.get(ip, (now, self._capacity))
        tokens = min(self._capacity, tokens + max(0.0, now - last) * self._refill)
        if tokens >= 1.0:
            self._buckets[ip] = (now, tokens - 1.0)
            return True
        self._buckets[ip] = (now, tokens)
        return False

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            return await self._app(scope, receive, send)
        if scope.get("method", "").upper() != self._method or scope.get("path", "") != self._path:
            return await self._app(scope, receive, send)

        client = scope.get("client") or ("unknown", 0)
        ip = client[0] if client else "unknown"
        if self._take_token(ip):
            return await self._app(scope, receive, send)

        if self._on_throttle:
            self._on_throttle(scope, ip)

        body = b"too many requests\n"
        await send({
            "type": "http.response.start",
            "status": 429,
            "headers": [
                (b"content-type", b"text/plain; charset=utf-8"),
                (b"content-length", str(len(body)).encode("ascii")),
                (b"retry-after", str(self._retry_after).encode("ascii")),
            ],
        })
        await send({"type": "http.response.body", "body": body})
