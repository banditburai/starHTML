"""``__Host-`` cookie prefix in star_app() — RFC 6265bis §4.1.3.2."""

from starlette.responses import PlainTextResponse
from starlette.routing import Route
from starlette.testclient import TestClient

from starhtml import star_app


async def _set_session(req):
    req.session["k"] = "v"
    return PlainTextResponse("ok")


def _set_cookie_lower(**kwargs):
    app, _ = star_app(
        secret_key="x" * 32,
        routes=[Route("/setsess", _set_session)],
        **kwargs,
    )
    res = TestClient(app, base_url="https://example.com").get("/setsess")
    return res.headers.get("set-cookie", "").lower()


def test_prefix_added_when_https_only_and_root_path():
    cookie = _set_cookie_lower(sess_https_only=True, sess_path="/", session_cookie="myapp")
    assert "__host-myapp=" in cookie
    assert "secure" in cookie


def test_no_prefix_when_not_https_only():
    cookie = _set_cookie_lower(sess_https_only=False, session_cookie="myapp")
    assert "myapp=" in cookie
    assert "__host-" not in cookie


def test_no_prefix_when_subpath():
    cookie = _set_cookie_lower(sess_https_only=True, sess_path="/app", session_cookie="myapp")
    assert "__host-" not in cookie


def test_no_prefix_when_domain_set():
    cookie = _set_cookie_lower(
        sess_https_only=True,
        sess_path="/",
        sess_domain=".example.com",
        session_cookie="myapp",
    )
    assert "__host-" not in cookie


def test_explicit_opt_out():
    cookie = _set_cookie_lower(
        sess_https_only=True,
        sess_path="/",
        session_cookie="myapp",
        host_cookie_prefix=False,
    )
    assert "__host-" not in cookie


def test_idempotent_when_already_prefixed():
    cookie = _set_cookie_lower(
        sess_https_only=True,
        sess_path="/",
        session_cookie="__Host-myapp",
    )
    assert "__host-myapp=" in cookie
    assert "__host-__host-" not in cookie
