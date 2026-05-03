"HostHeaderMiddleware: reject DNS-rebinding via Host-header check."

import asyncio

import pytest
from starlette.applications import Starlette
from starlette.responses import PlainTextResponse
from starlette.routing import Route
from starlette.testclient import TestClient

from starhtml.middleware import HostHeaderMiddleware, is_accepted_host


@pytest.mark.parametrize(
    "host_header,bound,expected",
    [
        # Loopback bind accepts loopback names + IPv6 ::1.
        ("localhost:8282", "127.0.0.1", True),
        ("127.0.0.1:8282", "127.0.0.1", True),
        ("[::1]:8282", "127.0.0.1", True),
        ("LOCALHOST:8282", "127.0.0.1", True),  # case-insensitive
        ("localhost", "127.0.0.1", True),
        ("evil.example.com:8282", "127.0.0.1", False),
        ("attacker:8282", "localhost", False),
        # Non-loopback bind requires exact host match.
        ("hermes.example:443", "hermes.example", True),
        ("HERMES.EXAMPLE:443", "hermes.example", True),
        ("evil.example:443", "hermes.example", False),
        # 0.0.0.0 / :: bind accepts everything.
        ("anything.example:443", "0.0.0.0", True),
        ("evil:443", "::", True),
        # Empty / malformed.
        ("", "127.0.0.1", False),
        ("[invalid", "127.0.0.1", False),
        ("localhost.:8282", "127.0.0.1", False),  # trailing dot — fail closed
        ("[fe80::1%eth0]:9119", "127.0.0.1", False),  # IPv6 zone-id — fail closed
    ],
)
def test_is_accepted_host(host_header, bound, expected):
    assert is_accepted_host(host_header, bound) is expected


async def _ok(_):
    return PlainTextResponse("ok")


def _client(bound):
    return TestClient(
        HostHeaderMiddleware(Starlette(routes=[Route("/hello", _ok)]), bound),
        headers={"host": "localhost:8282"},
    )


def test_good_host_passes():
    assert _client("127.0.0.1").get("/hello").status_code == 200


def test_bad_host_returns_400():
    res = TestClient(
        HostHeaderMiddleware(Starlette(routes=[Route("/hello", _ok)]), "127.0.0.1"),
        headers={"host": "evil.example:8282"},
    ).get("/hello")
    assert res.status_code == 400
    assert res.json() == {"detail": "Invalid Host header"}


def test_missing_host_returns_400():
    res = _client("127.0.0.1").get("/hello", headers={"host": ""})
    assert res.status_code == 400


def test_lifespan_passes_through():
    with _client("127.0.0.1") as c:
        assert c.get("/hello").status_code == 200


def test_zero_zero_zero_zero_bind_accepts_anything():
    res = TestClient(
        HostHeaderMiddleware(Starlette(routes=[Route("/hello", _ok)]), "0.0.0.0"),
        headers={"host": "any-public-host:443"},
    ).get("/hello")
    assert res.status_code == 200


def test_undecodable_host_bytes_rejected():
    app = HostHeaderMiddleware(Starlette(routes=[Route("/hello", _ok)]), "127.0.0.1")
    received = []

    async def receive():
        return {"type": "http.request", "body": b"", "more_body": False}

    async def send(msg):
        received.append(msg)

    scope = {
        "type": "http",
        "method": "GET",
        "path": "/hello",
        "headers": [(b"host", b"\xff\xfe\x00")],
    }
    asyncio.run(app(scope, receive, send))
    start = next(m for m in received if m["type"] == "http.response.start")
    # \xff\xfe\x00 IS decodable as latin-1; what's NOT decodable is essentially nothing.
    # Test instead that any garbled value falls into the host-mismatch path:
    assert start["status"] == 400
