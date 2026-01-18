"""Tests for async handle_request interface.

This interface enables WASM runtimes (like Pyodide) to handle HTTP requests
asynchronously without requiring threads, which is necessary since WASM
environments don't support threading.
"""

import pytest

from starhtml.core import StarHTML


class TestHandleRequestBasic:
    """Test basic handle_request functionality."""

    @pytest.mark.asyncio
    async def test_handle_request_returns_response(self):
        """handle_request returns a Response object."""
        app = StarHTML()

        @app.get("/")
        def home():
            return "<h1>Hello</h1>"

        response = await app.handle_request("GET", "/")

        assert response.status_code == 200
        assert b"<h1>Hello</h1>" in response.body

    @pytest.mark.asyncio
    async def test_handle_request_with_path_params(self):
        """handle_request extracts path parameters."""
        app = StarHTML()

        @app.get("/users/{user_id}")
        def get_user(user_id: int):
            return f"<div>User {user_id}</div>"

        response = await app.handle_request("GET", "/users/42")

        assert response.status_code == 200
        assert b"User 42" in response.body

    @pytest.mark.asyncio
    async def test_handle_request_404(self):
        """handle_request returns 404 for unknown routes."""
        app = StarHTML()

        @app.get("/")
        def home():
            return "Home"

        response = await app.handle_request("GET", "/unknown")

        assert response.status_code == 404


class TestHandleRequestMethods:
    """Test different HTTP methods."""

    @pytest.mark.asyncio
    async def test_handle_request_post(self):
        """handle_request handles POST requests."""
        app = StarHTML()

        @app.post("/submit")
        def submit():
            return "<div>Submitted</div>"

        response = await app.handle_request("POST", "/submit")

        assert response.status_code == 200
        assert b"Submitted" in response.body

    @pytest.mark.asyncio
    async def test_handle_request_post_with_json_body(self):
        """handle_request handles POST with JSON body."""
        app = StarHTML()

        @app.post("/api/data")
        def receive_data(data: dict):
            return f"<div>Received: {data.get('name', 'unknown')}</div>"

        response = await app.handle_request(
            "POST",
            "/api/data",
            body='{"name": "test"}',
            headers={"content-type": "application/json"},
        )

        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_handle_request_put(self):
        """handle_request handles PUT requests."""
        app = StarHTML()

        @app.put("/update/{item_id}")
        def update_item(item_id: int):
            return f"<div>Updated item {item_id}</div>"

        response = await app.handle_request("PUT", "/update/123")

        assert response.status_code == 200
        assert b"Updated item 123" in response.body

    @pytest.mark.asyncio
    async def test_handle_request_delete(self):
        """handle_request handles DELETE requests."""
        app = StarHTML()

        @app.delete("/delete/{item_id}")
        def delete_item(item_id: int):
            return f"<div>Deleted item {item_id}</div>"

        response = await app.handle_request("DELETE", "/delete/456")

        assert response.status_code == 200
        assert b"Deleted item 456" in response.body


class TestHandleRequestHeaders:
    """Test header handling."""

    @pytest.mark.asyncio
    async def test_handle_request_html_content_type(self):
        """HTML responses have correct content-type header."""
        app = StarHTML()

        @app.get("/")
        def home():
            return "<h1>Hello</h1>"

        response = await app.handle_request("GET", "/")

        content_type = response.headers.get("content-type", "")
        assert "text/html" in content_type

    @pytest.mark.asyncio
    async def test_handle_request_with_custom_headers(self):
        """handle_request passes custom headers to the request."""
        app = StarHTML()

        @app.get("/check-header")
        def check_header(request):
            custom_value = request.headers.get("x-custom-header", "not-found")
            return f"<div>Header: {custom_value}</div>"

        response = await app.handle_request("GET", "/check-header", headers={"x-custom-header": "my-value"})

        assert response.status_code == 200
        assert b"my-value" in response.body


class TestHandleRequestQueryParams:
    """Test query parameter handling."""

    @pytest.mark.asyncio
    async def test_handle_request_with_query_params(self):
        """handle_request handles query parameters."""
        app = StarHTML()

        @app.get("/search")
        def search(q: str = "default"):
            return f"<div>Searching for: {q}</div>"

        response = await app.handle_request("GET", "/search?q=hello")

        assert response.status_code == 200
        assert b"hello" in response.body


class TestHandleRequestCaseInsensitive:
    """Test that method matching is case-insensitive."""

    @pytest.mark.asyncio
    async def test_handle_request_lowercase_method(self):
        """handle_request works with lowercase method."""
        app = StarHTML()

        @app.get("/")
        def home():
            return "<h1>Hello</h1>"

        response = await app.handle_request("get", "/")

        assert response.status_code == 200
        assert b"<h1>Hello</h1>" in response.body

    @pytest.mark.asyncio
    async def test_handle_request_uppercase_method(self):
        """handle_request works with uppercase method."""
        app = StarHTML()

        @app.post("/submit")
        def submit():
            return "<div>Done</div>"

        response = await app.handle_request("POST", "/submit")

        assert response.status_code == 200
