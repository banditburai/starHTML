"""``__Host-`` cookie prefix support in ``star_app()``.

RFC 6265bis §4.1.3.2: cookies named ``__Host-*`` are accepted by browsers
*only* when ``Secure`` is set, ``Path=/``, and there is no ``Domain``
attribute. When all three preconditions hold, ``star_app(...)``
auto-prefixes the configured ``session_cookie`` with ``__Host-`` so apps
inherit the protection without having to think about the prefix.

Apps that explicitly opt out (rare — e.g. apps deliberately scoping the
cookie to a subpath) pass ``host_cookie_prefix=False``.
"""

from __future__ import annotations

from starlette.routing import Route
from starlette.testclient import TestClient

from starhtml import star_app


def _ok(_):
    from starlette.responses import PlainTextResponse

    return PlainTextResponse("ok")


def _build(**kwargs):
    app, _rt = star_app(secret_key="x" * 32, routes=[Route("/", _ok)], **kwargs)
    return TestClient(app, base_url="https://example.com")


def _set_cookie_lower(client: TestClient) -> str:
    # Force a session write so SessionMiddleware emits Set-Cookie.
    @client.app.route("/setsess")
    async def _set(req):
        from starlette.responses import PlainTextResponse

        req.session["k"] = "v"
        return PlainTextResponse("ok")

    res = client.get("/setsess")
    return res.headers.get("set-cookie", "").lower()


def test_host_prefix_added_when_https_only_and_root_path() -> None:
    client = _build(sess_https_only=True, sess_path="/", session_cookie="myapp")
    cookie = _set_cookie_lower(client)
    assert "__host-myapp=" in cookie
    assert "secure" in cookie


def test_no_prefix_when_not_https_only() -> None:
    client = _build(sess_https_only=False, sess_path="/", session_cookie="myapp")
    cookie = _set_cookie_lower(client)
    assert "myapp=" in cookie
    assert "__host-" not in cookie


def test_no_prefix_when_path_is_subpath() -> None:
    client = _build(sess_https_only=True, sess_path="/app", session_cookie="myapp")
    cookie = _set_cookie_lower(client)
    assert "myapp=" in cookie
    assert "__host-" not in cookie


def test_no_prefix_when_domain_is_set() -> None:
    client = _build(
        sess_https_only=True,
        sess_path="/",
        sess_domain=".example.com",
        session_cookie="myapp",
    )
    cookie = _set_cookie_lower(client)
    assert "myapp=" in cookie
    assert "__host-" not in cookie


def test_explicit_opt_out() -> None:
    client = _build(
        sess_https_only=True,
        sess_path="/",
        session_cookie="myapp",
        host_cookie_prefix=False,
    )
    cookie = _set_cookie_lower(client)
    assert "myapp=" in cookie
    assert "__host-" not in cookie


def test_idempotent_when_caller_already_prefixed() -> None:
    """Don't double-prefix if the caller already passed ``__Host-name``."""
    client = _build(
        sess_https_only=True,
        sess_path="/",
        session_cookie="__Host-myapp",
    )
    cookie = _set_cookie_lower(client)
    assert "__host-myapp=" in cookie
    assert "__host-__host-" not in cookie
