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
