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


def _client(*, expected=None, bypass=frozenset(), rejects=None):
    expected = {"https://example.com"} if expected is None else expected
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


# ---------------------------------------------------------------------------
# Realistic CSRF bypass attempts — must all reject. These are the spoof
# vectors a real attacker reaches for, so they are the ones we explicitly
# pin (and re-pin if origin parsing ever changes).
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "spoof_origin",
    [
        "https://example.com/",  # trailing slash (malformed Origin)
        "http://example.com",  # scheme downgrade
        "https://example.com:8443",  # port mismatch
        "https://example.com.attacker.example",  # suffix spoof
        "https://attacker.example/example.com",  # path-as-host trick
        "https://EXAMPLE.COM",  # case differs (Origin must match byte-for-byte)
    ],
)
def test_realistic_csrf_spoof_origins_rejected(spoof_origin):
    res = _client().post("/", headers={"Origin": spoof_origin})
    assert res.status_code == 403


@pytest.mark.parametrize(
    "spoof_referer",
    [
        "http://example.com/safe",  # scheme downgrade
        "https://example.com:8443/safe",  # port mismatch
        "https://attacker.example/?next=https://example.com",  # path-bait
        "https://example.com.attacker.example/",  # suffix spoof
    ],
)
def test_realistic_csrf_spoof_referer_rejected(spoof_referer):
    res = _client().post("/", headers={"Referer": spoof_referer})
    assert res.status_code == 403


def test_referer_with_userinfo_rejected():
    """Userinfo (`user@host`) splits the netloc; we must not treat it as the trusted host."""
    res = _client().post("/", headers={"Referer": "https://attacker.example@example.com/"})
    # urlparse netloc keeps the userinfo, so the candidate is not "https://example.com".
    assert res.status_code == 403
