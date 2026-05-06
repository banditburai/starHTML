"PathRateLimit: per-IP token bucket on a configurable path."

import asyncio

from starlette.applications import Starlette
from starlette.responses import PlainTextResponse
from starlette.routing import Route
from starlette.testclient import TestClient

from starhtml.middleware import PathRateLimit


async def _ok(_):
    return PlainTextResponse("ok")


def _client(*, capacity=10, refill_per_second=10 / 60, now=None, throttles=None, path="/auth/login"):
    routes = [Route(path, _ok, methods=["GET", "POST"]), Route("/", _ok, methods=["POST"])]
    time_iter = iter(now) if now is not None else None
    time_fn = (lambda: next(time_iter)) if time_iter is not None else None
    on_throttle = (lambda scope, ip: throttles.append(ip)) if throttles is not None else None
    app = PathRateLimit(
        Starlette(routes=routes),
        path=path,
        capacity=capacity,
        refill_per_second=refill_per_second,
        on_throttle=on_throttle,
        time_fn=time_fn,
    )
    return TestClient(app)


def test_under_capacity_passes():
    c = _client(now=[0.0] * 100)
    for _ in range(10):
        assert c.post("/auth/login").status_code == 200


def test_eleventh_attempt_429_with_retry_after():
    throttles = []
    c = _client(now=[0.0] * 100, throttles=throttles)
    for _ in range(10):
        c.post("/auth/login")
    res = c.post("/auth/login")
    assert res.status_code == 429
    assert res.headers["Retry-After"] == "60"
    assert len(throttles) == 1


def test_get_to_target_path_bypasses():
    c = _client(capacity=1, now=[0.0] * 100)
    for _ in range(50):
        assert c.get("/auth/login").status_code == 200


def test_other_paths_bypass():
    c = _client(capacity=1, now=[0.0] * 100)
    for _ in range(50):
        assert c.post("/").status_code == 200


def test_tokens_refill_over_time():
    # capacity=2, 1 token/sec. now=[0,0,0,1,1] -> drain twice at t=0; one refill by t=1.
    c = _client(capacity=2, refill_per_second=1.0, now=[0.0, 0.0, 0.0, 1.0, 1.0])
    assert c.post("/auth/login").status_code == 200  # t=0: 1 left
    assert c.post("/auth/login").status_code == 200  # t=0: 0 left
    assert c.post("/auth/login").status_code == 429  # t=0: still 0
    assert c.post("/auth/login").status_code == 200  # t=1: refill to 1
    assert c.post("/auth/login").status_code == 429  # t=1: 0


def test_burst_full_refill_burst_recovers_capacity():
    c = _client(capacity=2, refill_per_second=1.0, now=[0.0, 0.0, 10.0, 10.0, 10.0])
    assert c.post("/auth/login").status_code == 200
    assert c.post("/auth/login").status_code == 200
    assert c.post("/auth/login").status_code == 200  # refilled to capacity
    assert c.post("/auth/login").status_code == 200
    assert c.post("/auth/login").status_code == 429


def _drive(app, client_ip):
    received = []
    scope = {
        "type": "http",
        "method": "POST",
        "path": "/auth/login",
        "headers": [],
        "client": (client_ip, 12345) if client_ip is not None else None,
    }
    if client_ip is None:
        scope.pop("client")

    async def receive():
        return {"type": "http.request", "body": b"", "more_body": False}

    async def send(msg):
        received.append(msg)

    asyncio.run(app(scope, receive, send))
    start = next(m for m in received if m["type"] == "http.response.start")
    return start["status"]


def _bare_limiter(**kwargs):
    kwargs.setdefault("capacity", 2)
    kwargs.setdefault("refill_per_second", 0.0)
    kwargs.setdefault("time_fn", lambda: 0.0)
    return PathRateLimit(
        Starlette(routes=[Route("/auth/login", _ok, methods=["POST"])]),
        path="/auth/login",
        **kwargs,
    )


def test_separate_ips_independent_buckets():
    app = _bare_limiter()
    assert _drive(app, "10.0.0.1") == 200
    assert _drive(app, "10.0.0.1") == 200
    assert _drive(app, "10.0.0.1") == 429
    assert _drive(app, "10.0.0.2") == 200


def test_ipv6_bucket_keyed_by_address():
    app = PathRateLimit(
        Starlette(routes=[Route("/auth/login", _ok, methods=["POST"])]),
        path="/auth/login",
        capacity=1,
        refill_per_second=0.0,
        time_fn=lambda: 0.0,
    )
    assert _drive(app, "2001:db8::1") == 200
    assert _drive(app, "2001:db8::1") == 429
    assert _drive(app, "2001:db8::2") == 200


def _drive_with_headers(app, client_ip, headers):
    received = []
    scope = {
        "type": "http",
        "method": "POST",
        "path": "/auth/login",
        "headers": [(k.lower().encode("latin-1"), v.encode("latin-1")) for k, v in headers],
        "client": (client_ip, 12345),
    }

    async def receive():
        return {"type": "http.request", "body": b"", "more_body": False}

    async def send(msg):
        received.append(msg)

    asyncio.run(app(scope, receive, send))
    return next(m for m in received if m["type"] == "http.response.start")["status"]


def test_forwarded_headers_cannot_reset_bucket():
    """Without a trusted proxy upstream, X-Forwarded-For/X-Real-IP must not key the bucket.

    Threat: if forwarded headers were honored, an attacker on a single IP
    could brute-force /auth/login by rotating XFF values.
    """
    app = _bare_limiter()
    # Drain the same client IP twice → third call should 429 regardless of headers.
    assert _drive(app, "10.0.0.1") == 200
    assert _drive(app, "10.0.0.1") == 200
    assert _drive_with_headers(app, "10.0.0.1", [("X-Forwarded-For", "203.0.113.99")]) == 429
    assert _drive_with_headers(app, "10.0.0.1", [("X-Real-IP", "203.0.113.42")]) == 429
    assert _drive_with_headers(app, "10.0.0.1", [("Forwarded", "for=198.51.100.7")]) == 429


def test_concurrent_requests_share_one_bucket_per_ip():
    """N concurrent requests from one IP at capacity=1 yield exactly one 200."""
    app = _bare_limiter(capacity=1)

    async def _one():
        received = []
        scope = {
            "type": "http",
            "method": "POST",
            "path": "/auth/login",
            "headers": [],
            "client": ("10.0.0.99", 0),
        }

        async def receive():
            return {"type": "http.request", "body": b"", "more_body": False}

        async def send(msg):
            received.append(msg)

        await app(scope, receive, send)
        return next(m for m in received if m["type"] == "http.response.start")["status"]

    async def _gather():
        return await asyncio.gather(*[_one() for _ in range(20)])

    statuses = asyncio.run(_gather())
    assert statuses.count(200) == 1
    assert statuses.count(429) == 19


def test_missing_client_falls_back_to_unknown():
    app = PathRateLimit(
        Starlette(routes=[Route("/auth/login", _ok, methods=["POST"])]),
        path="/auth/login",
        capacity=1,
        refill_per_second=0.0,
        time_fn=lambda: 0.0,
    )
    assert _drive(app, None) == 200
    assert _drive(app, None) == 429
