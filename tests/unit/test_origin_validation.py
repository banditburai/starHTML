"OriginValidation middleware: CSRF defense-in-depth via Origin/Referer match."

import asyncio

import pytest
from starlette.applications import Starlette
from starlette.responses import PlainTextResponse
from starlette.routing import Route
from starlette.testclient import TestClient

from starhtml.middleware import OriginValidation


async def _ok(_):
    return PlainTextResponse("ok")


def _client(*, expected={"https://example.com"}, bypass=frozenset(), rejects=None):
    routes = [
        Route("/", _ok, methods=["GET", "POST", "PUT", "PATCH", "DELETE"]),
        Route("/auth/login", _ok, methods=["POST"]),
    ]
    on_reject = (lambda scope, info: rejects.append(info)) if rejects is not None else None
    app = OriginValidation(
        Starlette(routes=routes),
        expected_origins=frozenset(expected),
        bypass_paths=bypass,
        on_reject=on_reject,
    )
    return TestClient(app)


def test_get_with_no_origin_passes():
    assert _client().get("/").status_code == 200


def test_head_skips_check():
    assert _client().head("/").status_code == 200


def test_post_with_matching_origin_passes():
    res = _client().post("/", headers={"Origin": "https://example.com"})
    assert res.status_code == 200


def test_post_with_mismatched_origin_rejected():
    rejects = []
    res = _client(rejects=rejects).post("/", headers={"Origin": "https://attacker.example"})
    assert res.status_code == 403
    assert rejects == [{"method": "POST", "path": "/", "origin": "https://attacker.example", "referer": ""}]


def test_referer_fallback_passes_when_origin_missing():
    res = _client().post("/", headers={"Referer": "https://example.com/x"})
    assert res.status_code == 200


def test_no_origin_no_referer_rejected():
    assert _client().post("/").status_code == 403


def test_mismatched_referer_rejected():
    res = _client().post("/", headers={"Referer": "https://attacker.example/x"})
    assert res.status_code == 403


def test_bypass_path_skips_check():
    rejects = []
    res = _client(bypass=frozenset({"/auth/login"}), rejects=rejects).post(
        "/auth/login", headers={"Origin": "https://accounts.google.com"}
    )
    assert res.status_code == 200
    assert rejects == []


def test_multiple_expected_origins():
    c = _client(expected={"https://a.example", "https://b.example"})
    assert c.post("/", headers={"Origin": "https://a.example"}).status_code == 200
    assert c.post("/", headers={"Origin": "https://b.example"}).status_code == 200
    assert c.post("/", headers={"Origin": "https://c.example"}).status_code == 403


@pytest.mark.parametrize("method", ["PUT", "PATCH", "DELETE"])
def test_unsafe_methods_rejected_on_mismatch(method):
    res = _client().request(method, "/", headers={"Origin": "https://attacker.example"})
    assert res.status_code == 403


def test_origin_null_is_rejected():
    rejects = []
    res = _client(rejects=rejects).post("/", headers={"Origin": "null"})
    assert res.status_code == 403
    assert rejects[0]["origin"] == "null"


def test_empty_origin_falls_back_to_referer():
    res = _client().post("/", headers={"Origin": "", "Referer": "https://example.com/x"})
    assert res.status_code == 200


def test_duplicate_origin_headers_rejected():
    # TestClient can't send duplicate headers via dict; drive ASGI directly.
    rejects = []
    app = OriginValidation(
        Starlette(routes=[Route("/", _ok, methods=["POST"])]),
        expected_origins=frozenset({"https://example.com"}),
        on_reject=lambda scope, info: rejects.append(info),
    )
    received = []
    scope = {
        "type": "http",
        "method": "POST",
        "path": "/",
        "headers": [
            (b"origin", b"https://example.com"),
            (b"origin", b"https://attacker.example"),
        ],
    }

    async def receive():
        return {"type": "http.request", "body": b"", "more_body": False}

    async def send(msg):
        received.append(msg)

    asyncio.run(app(scope, receive, send))
    start = next(m for m in received if m["type"] == "http.response.start")
    assert start["status"] == 403
    assert rejects[0]["origin"] == "<multiple>"


def test_on_reject_optional():
    # No on_reject callback — still rejects, just doesn't notify.
    res = _client().post("/", headers={"Origin": "https://attacker.example"})
    assert res.status_code == 403
