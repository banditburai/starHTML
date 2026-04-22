"""Tests for StarRoute — Route subclass with StarHTML's _endp processing."""

from starlette.responses import PlainTextResponse
from starlette.routing import Route

from starhtml import Div, Mount, StarHTML, StarRoute, TestClient


class TestStarRouteBasic:
    def test_with_app_immediate_binding(self):
        app = StarHTML()

        def handler():
            return "hello"

        route = StarRoute("/test", handler, app=app)
        assert route._bound is True
        assert isinstance(route, Route)

    def test_without_app_deferred(self):
        def handler():
            return "hello"

        route = StarRoute("/test", handler)
        assert route._bound is False
        assert route.path == "/test"
        assert route.methods is not None
        assert "GET" in route.methods
        assert "POST" in route.methods

    def test_default_methods(self):
        route = StarRoute("/test", lambda: None)
        assert route.methods is not None
        assert "GET" in route.methods
        assert "POST" in route.methods

    def test_explicit_methods(self):
        route = StarRoute("/test", lambda: None, methods=["DELETE"])
        assert route.methods is not None
        assert "DELETE" in route.methods

    def test_isinstance_route(self):
        route = StarRoute("/test", lambda: None)
        assert isinstance(route, Route)


class TestStarRouteServing:
    def test_serves_string_response(self):
        app = StarHTML()
        route = StarRoute("/hello", lambda: "world", app=app)
        app.add_route(route)

        client = TestClient(app)
        resp = client.get("/hello")
        assert resp.status_code == 200
        assert "world" in resp.text

    def test_ft_rendering(self):
        """Handler returning FT objects renders to HTML."""
        app = StarHTML()

        def handler():
            return Div("content", cls="test")

        route = StarRoute("/ft", handler, app=app)
        app.add_route(route)

        client = TestClient(app)
        resp = client.get("/ft")
        assert resp.status_code == 200
        assert '<div class="test">content</div>' in resp.text

    def test_param_extraction(self):
        """Path and query params are extracted correctly."""
        app = StarHTML()

        def handler(name: str):
            return f"hello {name}"

        route = StarRoute("/greet/{name}", handler, app=app)
        app.add_route(route)

        client = TestClient(app)
        resp = client.get("/greet/world")
        assert resp.status_code == 200
        assert "hello world" in resp.text

    def test_beforeware_runs(self):
        """Beforeware executes on StarRoute handlers."""
        called = []

        def before(req):
            called.append("before")

        app = StarHTML(before=[before])

        route = StarRoute("/test", lambda: "ok", app=app)
        app.add_route(route)

        client = TestClient(app)
        resp = client.get("/test")
        assert resp.status_code == 200
        assert called == ["before"]


class TestStarRouteInMount:
    def test_in_mount_with_app(self):
        """StarRoute inside Mount serves correctly when pre-bound."""
        app = StarHTML(
            routes=[
                Mount(
                    "/api",
                    routes=[
                        StarRoute("/users", lambda: "user list", app=None),
                    ],
                ),
            ]
        )
        # Auto-binding happens in __init__
        client = TestClient(app)
        resp = client.get("/api/users")
        assert resp.status_code == 200
        assert "user list" in resp.text

    def test_mixed_with_plain_route(self):
        """StarRoute and plain Starlette Route coexist in same Mount."""

        async def plain_handler(request):
            return PlainTextResponse("plain")

        app = StarHTML(
            routes=[
                Mount(
                    "/api",
                    routes=[
                        StarRoute("/star", lambda: "star response", app=None),
                        Route("/plain", plain_handler),
                    ],
                ),
            ]
        )

        client = TestClient(app)

        resp_star = client.get("/api/star")
        assert resp_star.status_code == 200
        assert "star response" in resp_star.text

        resp_plain = client.get("/api/plain")
        assert resp_plain.status_code == 200
        assert resp_plain.text == "plain"


class TestStarRouteDeferredBinding:
    def test_deferred_in_routes_list(self):
        """StarRoute without app is auto-bound when passed in routes=[]."""

        def handler():
            return "deferred"

        app = StarHTML(routes=[StarRoute("/deferred", handler)])

        client = TestClient(app)
        resp = client.get("/deferred")
        assert resp.status_code == 200
        assert "deferred" in resp.text

    def test_deferred_in_mount(self):
        """StarRoute without app inside Mount is auto-bound by StarHTML."""

        def handler():
            return "nested deferred"

        app = StarHTML(
            routes=[
                Mount("/sub", routes=[StarRoute("/item", handler)]),
            ]
        )

        client = TestClient(app)
        resp = client.get("/sub/item")
        assert resp.status_code == 200
        assert "nested deferred" in resp.text

    def test_via_add_route(self):
        """app.add_route(StarRoute(...)) auto-binds."""
        app = StarHTML()

        route = StarRoute("/dynamic", lambda: "added")
        assert route._bound is False

        app.add_route(route)
        assert route._bound is True

        client = TestClient(app)
        resp = client.get("/dynamic")
        assert resp.status_code == 200
        assert "added" in resp.text


class TestStarRouteGuards:
    """Fail-fast errors when StarRoute is misused (wrong app type / unbound)."""

    def test_bind_rejects_non_starhtml_app(self):
        """StarRoute(..., app=plain_starlette) raises TypeError with actionable guidance."""
        import pytest
        from starlette.applications import Starlette

        plain_app = Starlette()

        with pytest.raises(TypeError) as excinfo:
            StarRoute("/oops", lambda: "x", app=plain_app)

        msg = str(excinfo.value)
        assert "StarRoute" in msg
        assert "StarHTML" in msg
        assert "StarHTML(routes=" in msg

    def test_unbound_starroute_raises_clear_error_at_request_time(self):
        """A StarRoute that ends up in a plain Starlette app (never bound) raises a clear RuntimeError."""
        import pytest
        from starlette.applications import Starlette

        def handler():
            return "unreachable"

        unbound = StarRoute("/fragment", handler)
        assert unbound._bound is False

        plain_app = Starlette(routes=[unbound])
        client = TestClient(plain_app)

        with pytest.raises(RuntimeError) as excinfo:
            client.get("/fragment")

        msg = str(excinfo.value)
        assert "StarRoute" in msg
        assert "never bound" in msg
        assert "StarHTML(routes=" in msg
        assert "add_route" in msg


class TestRuntimeBodyWrap:
    """Beforeware can override body_wrap per request (htmx fragments, embed views, etc.)."""

    def test_beforeware_body_wrap_override_is_respected(self):
        """A beforeware that sets ``req.body_wrap`` wins over the app-level default."""

        def app_wrap(content):
            return Div(content, cls="app-shell")

        def fragment_wrap(content):
            # Bare passthrough for htmx/iframe/embed fragment requests
            return content

        def maybe_fragment(req):
            if req.headers.get("x-fragment") == "1":
                req.body_wrap = fragment_wrap

        app = StarHTML(body_wrap=app_wrap, before=[maybe_fragment])

        @app.route("/page")
        def page():
            return Div("hello", id="content")

        client = TestClient(app)

        # No header → app-level shell kicks in
        full = client.get("/page")
        assert full.status_code == 200
        assert 'class="app-shell"' in full.text

        # With header → beforeware override wins
        frag = client.get("/page", headers={"x-fragment": "1"})
        assert frag.status_code == 200
        assert 'class="app-shell"' not in frag.text
        assert 'id="content"' in frag.text

    def test_app_body_wrap_still_applies_when_no_override(self):
        """Default path unchanged: app-level body_wrap applies when beforeware doesn't touch it."""

        def shell(content):
            return Div(content, cls="outer-shell")

        app = StarHTML(body_wrap=shell)

        @app.route("/default")
        def default_page():
            return Div("hi", id="inner")

        client = TestClient(app)
        resp = client.get("/default")
        assert resp.status_code == 200
        assert 'class="outer-shell"' in resp.text
        assert 'id="inner"' in resp.text
