"""Tests for StarHTML server functionality and real behavior.

Tests real server behavior including:
- HTTP request/response handling
- Routing functionality
- JSON responses
- Cookie handling
- Real client interactions
"""

import json
from unittest.mock import Mock

from starlette.requests import Request
from starlette.testclient import TestClient

from starhtml import H1, Div, P, star_app
from starhtml.server import Client, FtResponse, JSONResponse, Redirect, all_meths, cookie


class TestServerHTTPFunctionality:
    """Test basic HTTP server functionality."""

    def test_star_app_creation(self):
        """Test that star_app creates functional server app."""
        app, rt = star_app()

        assert app is not None
        assert rt is not None
        assert hasattr(app, "router")
        assert hasattr(app, "middleware_stack")

    def test_basic_route_creation(self):
        """Test creating basic routes."""
        app, rt = star_app()

        @rt("/")
        def home():
            return Div(H1("Hello StarHTML"))

        @rt("/api/data")
        def api_data():
            return {"message": "success"}

        client = TestClient(app)

        # Test HTML response
        response = client.get("/")
        assert response.status_code == 200
        assert "Hello StarHTML" in response.text

        # Test JSON response
        response = client.get("/api/data")
        assert response.status_code == 200
        assert response.json() == {"message": "success"}

    def test_http_methods(self):
        """Test different HTTP methods work correctly."""
        app, rt = star_app()

        @rt("/", methods=["GET"])
        def get_home():
            return {"method": "GET"}

        @rt("/", methods=["POST"])
        def post_home():
            return {"method": "POST"}

        @rt("/", methods=["PUT"])
        def put_home():
            return {"method": "PUT"}

        @rt("/", methods=["DELETE"])
        def delete_home():
            return {"method": "DELETE"}

        client = TestClient(app)

        # Test all HTTP methods
        for method in ["GET", "POST", "PUT", "DELETE"]:
            response = getattr(client, method.lower())("/")
            assert response.status_code == 200
            assert response.json() == {"method": method}

    def test_route_parameters(self):
        """Test route parameters are handled correctly."""
        app, rt = star_app()

        @rt("/users/{user_id}")
        def get_user(user_id: int):
            return {"user_id": user_id, "type": type(user_id).__name__}

        @rt("/posts/{slug}")
        def get_post(slug: str):
            return {"slug": slug, "type": type(slug).__name__}

        client = TestClient(app)

        # Test integer parameter
        response = client.get("/users/123")
        assert response.status_code == 200
        data = response.json()
        assert data["user_id"] == 123
        assert data["type"] == "int"

        # Test string parameter
        response = client.get("/posts/hello-world")
        assert response.status_code == 200
        data = response.json()
        assert data["slug"] == "hello-world"
        assert data["type"] == "str"


class TestJSONResponseFunctionality:
    """Test JSONResponse class functionality."""

    def test_json_response_creation(self):
        """Test JSONResponse creates proper JSON responses."""
        data = {"message": "hello", "count": 42}
        response = JSONResponse(data)

        assert response.status_code == 200
        assert response.media_type == "application/json"

        # Test actual JSON content
        content = json.loads(response.body.decode())
        assert content == data

    def test_json_response_with_status(self):
        """Test JSONResponse with custom status code."""
        response = JSONResponse({"error": "not found"}, status_code=404)
        assert response.status_code == 404

        content = json.loads(response.body.decode())
        assert content == {"error": "not found"}

    def test_json_response_with_headers(self):
        """Test JSONResponse with custom headers."""
        headers = {"X-Custom": "value", "X-Request-ID": "123"}
        response = JSONResponse({"data": "test"}, headers=headers)

        assert response.headers["X-Custom"] == "value"
        assert response.headers["X-Request-ID"] == "123"


class TestRedirectFunctionality:
    """Test redirect functionality."""

    def test_redirect_creation(self):
        """Test Redirect creates proper redirect responses."""
        redirect = Redirect("/new-location")

        # Redirect class stores location
        assert redirect.loc == "/new-location"

        # Test the actual response creation
        mock_request = Mock()
        response = redirect.__response__(mock_request)
        assert response.status_code == 303  # StarHTML uses 303 by default
        assert response.headers["location"] == "/new-location"

    def test_redirect_with_status(self):
        """Test Redirect response creation."""
        redirect = Redirect("/moved")

        # Test response
        mock_request = Mock()
        response = redirect.__response__(mock_request)
        assert response.status_code == 303
        assert response.headers["location"] == "/moved"

    def test_redirect_in_route(self):
        """Test redirect functionality in actual routes."""
        app, rt = star_app()

        @rt("/old-page")
        def old_page():
            return Redirect("/new-page")

        @rt("/new-page")
        def new_page():
            return {"message": "You've been redirected!"}

        client = TestClient(app)

        # Test redirect (follow_redirects=False to check redirect response)
        response = client.get("/old-page", follow_redirects=False)
        assert response.status_code == 303  # StarHTML uses 303 by default
        assert response.headers["location"] == "/new-page"

        # Test following redirect
        response = client.get("/old-page", follow_redirects=True)
        assert response.status_code == 200
        assert response.json() == {"message": "You've been redirected!"}


class TestCookieHandling:
    """Test cookie handling functionality."""

    def test_cookie_creation(self):
        """Test cookie creation utility."""
        cookie_header = cookie("session", "abc123", max_age=3600)

        # Cookie function returns HttpHeader object
        assert hasattr(cookie_header, "k")  # HttpHeader has key and value
        assert hasattr(cookie_header, "v")
        cookie_str = str(cookie_header)
        assert "session=abc123" in cookie_str
        assert "Max-Age=3600" in cookie_str

    def test_cookie_with_options(self):
        """Test cookie with various options."""
        cookie_header = cookie(
            "secure_session", "value123", max_age=7200, httponly=True, secure=True, samesite="strict"
        )

        cookie_str = str(cookie_header)
        assert "secure_session=value123" in cookie_str
        assert "Max-Age=7200" in cookie_str
        assert "HttpOnly" in cookie_str
        assert "Secure" in cookie_str
        assert "SameSite=strict" in cookie_str

    def test_cookie_in_response(self):
        """Test setting cookies in actual responses."""
        app, rt = star_app()

        @rt("/set-cookie")
        def set_cookie():
            response = JSONResponse({"message": "Cookie set"})
            response.set_cookie("test_cookie", "test_value", max_age=3600)
            return response

        @rt("/read-cookie")
        def read_cookie(request: Request):
            cookie_value = request.cookies.get("test_cookie", "not found")
            return {"cookie_value": cookie_value}

        client = TestClient(app)

        # Set cookie
        response = client.get("/set-cookie")
        assert response.status_code == 200
        assert "test_cookie" in response.cookies

        # Read cookie (TestClient automatically handles cookies)
        response = client.get("/read-cookie")
        assert response.status_code == 200
        assert response.json()["cookie_value"] == "test_value"


class TestFtResponseRendering:
    """Test FT element response rendering."""

    def test_ft_response_creation(self):
        """Test FtResponse stores content properly."""
        element = Div(H1("Title"), P("Content"))
        response = FtResponse(element)

        assert response.status_code == 200
        assert response.content == element

    def test_ft_response_with_headers(self):
        """Test FtResponse with custom headers."""
        element = Div("Test content")
        headers = {"X-Frame-Options": "DENY"}
        response = FtResponse(element, headers=headers)

        assert response.headers is not None and response.headers["X-Frame-Options"] == "DENY"
        assert response.content == element


class TestClientFunctionality:
    """Test HTTP client functionality."""

    def test_client_creation(self):
        """Test Client creation and basic functionality."""
        app, rt = star_app()

        @rt("/api/test")
        def api_test():
            return {"message": "client test"}

        # Create client with the app
        client = Client(app)

        # Test client request
        response = client.get("/api/test")
        assert response.status_code == 200
        assert response.json() == {"message": "client test"}

    def test_client_with_real_server(self):
        """Test client with TestClient (simulating real server)."""
        app, rt = star_app()

        @rt("/health")
        def health_check():
            return {"status": "healthy", "service": "starhtml"}

        client = TestClient(app)
        response = client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "starhtml"


class TestServerUtilities:
    """Test server utility functions."""

    def test_all_meths_constant(self):
        """Test all_meths contains expected HTTP methods."""
        expected_methods = ["get", "post", "put", "delete", "patch", "head", "options"]

        for method in expected_methods:
            assert method in all_meths

        # Should be a list or tuple
        assert isinstance(all_meths, list | tuple)
        assert len(all_meths) >= len(expected_methods)


class TestRealServerBehavior:
    """Test real server behavior scenarios."""

    def test_form_handling(self):
        """Test form data handling."""
        app, rt = star_app()

        @rt("/form", methods=["GET"])
        def show_form():
            return Div(
                """<form method="post" action="/form">
                    <input name="username" type="text">
                    <input name="email" type="email">
                    <button type="submit">Submit</button>
                </form>"""
            )

        @rt("/form", methods=["POST"])
        def handle_form(request: Request):
            # This will test real form parsing
            return {"message": "Form received", "method": "POST"}

        client = TestClient(app)

        # Test GET form
        response = client.get("/form")
        assert response.status_code == 200
        assert "form" in response.text

        # Test POST form
        form_data = {"username": "testuser", "email": "test@example.com"}
        response = client.post("/form", data=form_data)
        assert response.status_code == 200
        assert response.json()["message"] == "Form received"

    def test_query_parameters(self):
        """Test query parameter handling."""
        app, rt = star_app()

        @rt("/search")
        def search(request: Request):
            query = request.query_params.get("q", "")
            page = int(request.query_params.get("page", "1"))
            return {"query": query, "page": page, "results": f"Results for '{query}' on page {page}"}

        client = TestClient(app)

        response = client.get("/search?q=starhtml&page=2")
        assert response.status_code == 200
        data = response.json()
        assert data["query"] == "starhtml"
        assert data["page"] == 2
        assert "Results for 'starhtml' on page 2" in data["results"]

    def test_error_handling(self):
        """Test error handling in server."""
        app, rt = star_app()

        @rt("/error")
        def trigger_error():
            raise ValueError("Intentional error for testing")

        @rt("/not-found")
        def not_found():
            # This should trigger a 404 when accessed via wrong route
            return {"found": True}

        client = TestClient(app)

        # Test 404 for non-existent route
        response = client.get("/does-not-exist")
        assert response.status_code == 404

        # Test that existing route works
        response = client.get("/not-found")
        assert response.status_code == 200
        assert response.json()["found"] is True

    def test_middleware_integration(self):
        """Test that server works with middleware."""
        app, rt = star_app()

        # Add custom middleware
        @app.middleware("http")
        async def add_custom_header(request, call_next):
            response = await call_next(request)
            response.headers["X-Custom-Middleware"] = "active"
            return response

        @rt("/middleware-test")
        def middleware_test():
            return {"middleware": "test"}

        client = TestClient(app)
        response = client.get("/middleware-test")

        assert response.status_code == 200
        assert response.headers["X-Custom-Middleware"] == "active"
        assert response.json()["middleware"] == "test"
