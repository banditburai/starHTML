"""CSP mode (Datastar 1.0.3+): per-response nonces on <html>, every script/style, and the CSP header."""

import re

import pytest
from starlette.testclient import TestClient

from starhtml import *
from starhtml.server import DEFAULT_CSP_POLICY, csp_nonce
from starhtml.xtend import Script

NONCE_RE = re.compile(r'<html[^>]* data-nonce="([^"]+)"')


def _nonces(html: str) -> tuple[str, list[str]]:
    root = NONCE_RE.search(html)
    assert root, html[:300]
    return root.group(1), re.findall(r'<(?:script|style)\b[^>]*\bnonce="([^"]+)"', html)


def _tags(html: str) -> int:
    return len(re.findall(r"<(?:script|style)\b", html))


def test_csp_off_by_default():
    app, rt = star_app()

    @rt("/")
    def index():
        return Div("hi", Script("console.log(1)"))

    r = TestClient(app).get("/")
    assert "nonce" not in r.text
    assert "content-security-policy" not in r.headers


def test_csp_true_stamps_every_script_and_style_and_sets_header():
    from starhtml.plugins import persist

    app, rt = star_app(csp=True, hdrs=(theme_script(), Style("body{margin:0}")))
    app.register(persist)  # adds the <script type="importmap"> and plugin module scripts

    @rt("/")
    def index():
        return Div("hi", Script("console.log(1)"), Style(".x{}"))

    r = TestClient(app).get("/")
    root, tag_nonces = _nonces(r.text)
    assert len(tag_nonces) == _tags(r.text), "every <script>/<style> carries the nonce"
    assert set(tag_nonces) == {root}
    assert len(root) >= 22  # 16 random bytes, base64url
    assert 'type="importmap"' in r.text
    assert r.headers["content-security-policy"] == DEFAULT_CSP_POLICY.format(nonce=root)
    assert "'strict-dynamic'" in r.headers["content-security-policy"]


def test_nonce_is_fresh_per_response():
    app, rt = star_app(csp=True)

    @rt("/")
    def index():
        return Div("hi")

    c = TestClient(app)
    a, _ = _nonces(c.get("/").text)
    b, _ = _nonces(c.get("/").text)
    assert a != b


def test_handler_can_read_nonce_and_explicit_nonce_is_preserved():
    app, rt = star_app(csp=True)

    @rt("/")
    def index(req):
        n = csp_nonce(req)
        return Div(Script("console.log(1)", nonce="user-supplied"), P(n, id="n"))

    r = TestClient(app).get("/")
    root, tag_nonces = _nonces(r.text)
    assert f'<p id="n">{root}</p>' in r.text
    assert "user-supplied" in tag_nonces and root in tag_nonces


def test_full_page_response_is_stamped_too():
    app, rt = star_app(csp=True)

    @rt("/")
    def index():
        return Html(Head(Script("console.log(1)")), Body(P("x")))

    r = TestClient(app).get("/")
    root, tag_nonces = _nonces(r.text)
    assert tag_nonces == [root]
    assert r.headers["content-security-policy"].startswith("script-src 'nonce-")


def test_custom_policy_template():
    policy = "default-src 'self'; script-src 'self' 'nonce-{nonce}'"
    app, rt = star_app(csp=policy)

    @rt("/")
    def index():
        return Div("hi")

    r = TestClient(app).get("/")
    root, _ = _nonces(r.text)
    assert r.headers["content-security-policy"] == policy.format(nonce=root)


def test_policy_template_requires_nonce_slot():
    with pytest.raises(ValueError, match="{nonce}"):
        star_app(csp="script-src 'self'")


def test_exception_pages_are_stamped():
    app, rt = star_app(csp=True, exception_handlers={404: lambda req, exc: Div("missing", Script("1"))})

    r = TestClient(app).get("/nope")
    assert r.status_code == 404
    root, tag_nonces = _nonces(r.text)
    assert set(tag_nonces) == {root}
    assert "content-security-policy" in r.headers


def test_json_and_plain_responses_untouched():
    app, rt = star_app(csp=True)

    @rt("/j")
    def j():
        return {"a": 1}

    r = TestClient(app).get("/j")
    assert r.json() == {"a": 1}
    assert "content-security-policy" not in r.headers
