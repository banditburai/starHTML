"""Integration tests for live reload functionality.

This module tests:
- LiveReloadJs generation and injection
- WebSocket live reload endpoint
- StarHTMLWithLiveReload class behavior
- Live reload configuration options
- Browser-server communication patterns
"""

from unittest.mock import AsyncMock, Mock

import pytest
from starlette.testclient import TestClient

# Use anyio for async tests
from starhtml import H1, Div, P, star_app
from starhtml.realtime import LiveReloadJs, StarHTMLWithLiveReload, live_reload_ws
from starhtml.xtend import Script


class TestLiveReloadJs:
    """Test LiveReloadJs script generation."""

    def test_live_reload_js_basic(self):
        """Test basic LiveReloadJs generation."""
        script = LiveReloadJs()

        # Should return a Script element
        assert script.tag == "script"
        assert hasattr(script, "children")

        # Check script content
        script_content = str(script.children[0])
        assert "WebSocket" in script_content
        assert "/live-reload" in script_content
        assert "window.location.reload()" in script_content
        assert "onclose" in script_content
        assert "onopen" in script_content

    def test_live_reload_js_custom_config(self):
        """Test LiveReloadJs with custom configuration."""
        script = LiveReloadJs(reload_attempts=10, reload_interval=500)

        script_content = str(script.children[0])

        # Check that custom values are injected
        assert "500" in script_content  # reload_interval
        assert "10" in script_content  # reload_attempts

    def test_live_reload_js_content_structure(self):
        """Test the structure and logic of the generated JavaScript."""
        script = LiveReloadJs(reload_attempts=5, reload_interval=1000)

        script_content = str(script.children[0])

        # Check key components
        assert "let attempts = 0" in script_content
        assert "const connect = () =>" in script_content
        assert "new WebSocket" in script_content
        assert "socket.onopen" in script_content
        assert "socket.onclose" in script_content
        assert "fetch(window.location.href)" in script_content
        assert "setTimeout" in script_content

        # Check the retry logic
        assert "attempts++" in script_content
        assert "attempts > 5" in script_content  # Custom reload_attempts

    def test_live_reload_js_websocket_url(self):
        """Test WebSocket URL generation in the script."""
        script = LiveReloadJs()
        script_content = str(script.children[0])

        # Should use current host for WebSocket connection
        assert "ws://${window.location.host}/live-reload" in script_content

    def test_live_reload_js_different_configs(self):
        """Test various configuration combinations."""
        configs = [
            {"reload_attempts": 1, "reload_interval": 100},
            {"reload_attempts": 50, "reload_interval": 5000},
            {"reload_attempts": 0, "reload_interval": 0},
        ]

        for config in configs:
            script = LiveReloadJs(**config)
            script_content = str(script.children[0])

            assert str(config["reload_interval"]) in script_content
            assert str(config["reload_attempts"]) in script_content


class TestLiveReloadWebSocket:
    """Test live reload WebSocket functionality."""

    @pytest.mark.asyncio
    async def test_live_reload_ws_accept(self):
        """Test that live_reload_ws accepts WebSocket connections."""
        mock_websocket = AsyncMock()

        # Mock the accept method
        mock_websocket.accept = AsyncMock()

        await live_reload_ws(mock_websocket)

        # Verify that accept was called
        mock_websocket.accept.assert_called_once()

    @pytest.mark.asyncio
    async def test_live_reload_ws_simple_connection(self):
        """Test basic WebSocket connection behavior."""
        mock_websocket = Mock()
        mock_websocket.accept = AsyncMock()

        # Call the handler
        await live_reload_ws(mock_websocket)

        # Verify connection was accepted
        mock_websocket.accept.assert_called_once()

        # The function should complete without error
        # (it's a simple keep-alive connection)


class TestStarHTMLWithLiveReload:
    """Test StarHTMLWithLiveReload class."""

    def test_star_html_with_live_reload_creation(self):
        """Test StarHTMLWithLiveReload instantiation."""
        app = StarHTMLWithLiveReload()

        # Should be a StarHTML instance
        from starhtml.core import StarHTML

        assert isinstance(app, StarHTML)

        # Should have the live reload script in headers
        headers = getattr(app, "hdrs", [])

        # Find the LiveReload script in headers
        live_reload_script = None
        for header in headers:
            if hasattr(header, "tag") and header.tag == "script":
                script_content = str(header.children[0]) if header.children else ""
                if "/live-reload" in script_content:
                    live_reload_script = header
                    break

        assert live_reload_script is not None

    def test_star_html_with_live_reload_routes(self):
        """Test that live reload routes are added."""
        app = StarHTMLWithLiveReload()

        # Check that the WebSocket route was added
        routes = app.routes

        # Find the live reload route
        live_reload_route = None
        for route in routes:
            if hasattr(route, "path") and route.path == "/live-reload":
                live_reload_route = route
                break

        assert live_reload_route is not None
        # Should be a WebSocket route
        from starlette.routing import WebSocketRoute

        assert isinstance(live_reload_route, WebSocketRoute)

    def test_star_html_with_live_reload_custom_config(self):
        """Test StarHTMLWithLiveReload with custom configuration."""
        app = StarHTMLWithLiveReload(reload_attempts=15, reload_interval=2000)

        # Find the LiveReload script
        live_reload_script = None
        for header in app.hdrs:
            if hasattr(header, "tag") and header.tag == "script":
                script_content = str(header.children[0]) if header.children else ""
                if "/live-reload" in script_content:
                    live_reload_script = header
                    break

        assert live_reload_script is not None
        script_content = str(live_reload_script.children[0])

        # Check custom configuration is applied
        assert "2000" in script_content  # reload_interval
        assert "15" in script_content  # reload_attempts

    def test_star_html_with_live_reload_existing_headers(self):
        """Test that existing headers are preserved."""

        existing_script = Script("console.log('existing');")
        app = StarHTMLWithLiveReload(hdrs=[existing_script])

        # Should have both existing and live reload scripts
        assert len(app.hdrs) >= 2

        # Check that existing script is preserved
        script_contents = []
        for header in app.hdrs:
            if hasattr(header, "tag") and header.tag == "script":
                content = str(header.children[0]) if header.children else ""
                script_contents.append(content)

        # Should have both the existing script and live reload script
        existing_found = any("existing" in content for content in script_contents)
        live_reload_found = any("/live-reload" in content for content in script_contents)

        assert existing_found
        assert live_reload_found

    def test_star_html_with_live_reload_existing_routes(self):
        """Test that existing routes are preserved."""
        from starlette.responses import PlainTextResponse
        from starlette.routing import Route

        def existing_endpoint():
            return PlainTextResponse("existing")

        existing_route = Route("/existing", endpoint=existing_endpoint)
        app = StarHTMLWithLiveReload(routes=[existing_route])

        # Should have both existing and live reload routes
        route_paths = [getattr(route, "path", None) for route in app.routes]

        assert "/existing" in route_paths
        assert "/live-reload" in route_paths


class TestLiveReloadIntegration:
    """Test live reload integration with StarHTML apps."""

    def test_live_reload_in_star_app(self):
        """Test live reload integration via star_app factory."""
        app, rt = star_app(live=True)

        # Should be a StarHTMLWithLiveReload instance
        assert type(app).__name__ == "_StarHTMLWithLiveReload"

        # Should have live reload script
        headers = getattr(app, "hdrs", [])
        live_reload_found = False

        for header in headers:
            if hasattr(header, "tag") and header.tag == "script":
                content = str(header.children[0]) if header.children else ""
                if "/live-reload" in content:
                    live_reload_found = True
                    break

        assert live_reload_found

    def test_live_reload_websocket_endpoint(self):
        """Test live reload WebSocket endpoint functionality."""
        app = StarHTMLWithLiveReload()
        client = TestClient(app)

        # Test WebSocket connection
        with client.websocket_connect("/live-reload"):
            # Connection should be accepted (no immediate close)
            # The WebSocket should stay open for live reload functionality
            pass  # If we get here without exception, the connection worked

    def test_live_reload_script_injection(self):
        """Test that live reload script is injected into pages."""
        app = StarHTMLWithLiveReload()

        @app.route("/")
        def home():
            return Div(H1("Home Page"), P("Welcome to the site"))

        client = TestClient(app)
        response = client.get("/")

        assert response.status_code == 200
        html_content = response.text

        # Should contain the live reload script
        assert "WebSocket" in html_content
        assert "/live-reload" in html_content
        assert "window.location.reload()" in html_content

    def test_live_reload_without_live_flag(self):
        """Test that regular star_app doesn't include live reload."""
        app, rt = star_app(live=False)  # Explicitly disable

        # Should be regular StarHTML, not the live reload version
        assert type(app).__name__ == "StarHTML"

        @rt("/")
        def home():
            return Div(H1("Home Page"))

        client = TestClient(app)
        response = client.get("/")

        assert response.status_code == 200
        html_content = response.text

        # Should NOT contain live reload script
        assert "/live-reload" not in html_content
        assert "WebSocket" not in html_content or "datastar" in html_content.lower()  # datastar might have WebSocket


class TestLiveReloadErrorHandling:
    """Test error handling in live reload functionality."""

    def test_live_reload_websocket_disconnect(self):
        """Test WebSocket disconnect handling."""
        app = StarHTMLWithLiveReload()
        client = TestClient(app)

        # Connect and then disconnect
        with client.websocket_connect("/live-reload"):
            # The connection should work initially
            pass

        # Reconnection should also work
        with client.websocket_connect("/live-reload"):
            pass

    def test_live_reload_with_invalid_config(self):
        """Test live reload with edge case configurations."""
        # Test with zero values
        app1 = StarHTMLWithLiveReload(reload_attempts=0, reload_interval=0)
        assert app1 is not None

        # Test with very large values
        app2 = StarHTMLWithLiveReload(reload_attempts=1000, reload_interval=60000)
        assert app2 is not None

        # Test with negative values (should be handled gracefully)
        app3 = StarHTMLWithLiveReload(reload_attempts=-1, reload_interval=-100)
        assert app3 is not None

    def test_live_reload_route_conflict(self):
        """Test behavior when /live-reload route already exists."""
        from starlette.responses import PlainTextResponse
        from starlette.routing import Route

        def conflicting_endpoint():
            return PlainTextResponse("conflict")

        existing_route = Route("/live-reload", endpoint=conflicting_endpoint)

        # Should handle route conflicts gracefully
        app = StarHTMLWithLiveReload(routes=[existing_route])

        # App should still be created
        assert app is not None

        # Check route behavior - last one should win or they should coexist
        route_paths = [getattr(route, "path", None) for route in app.routes]
        live_reload_count = route_paths.count("/live-reload")
        assert live_reload_count >= 1  # At least one /live-reload route


class TestLiveReloadRealWorldScenarios:
    """Test realistic live reload usage scenarios."""

    def test_development_workflow_simulation(self):
        """Simulate a typical development workflow."""
        app = StarHTMLWithLiveReload(reload_attempts=3, reload_interval=500)

        @app.route("/")
        def home():
            return Div(H1("Development Server"), P("This page will reload automatically when files change."))

        @app.route("/api/data")
        def api():
            return {"status": "ok", "data": ["item1", "item2"]}

        client = TestClient(app)

        # Test normal page request
        response = client.get("/")
        assert response.status_code == 200
        assert "Development Server" in response.text
        assert "/live-reload" in response.text

        # Test API endpoint (should work normally)
        response = client.get("/api/data")
        assert response.status_code == 200
        assert response.json()["status"] == "ok"

        # Test WebSocket connection for live reload
        with client.websocket_connect("/live-reload"):
            # Should connect successfully
            pass

    def test_production_like_setup(self):
        """Test that live reload can be disabled for production-like setup."""
        # Simulate production by not using live=True
        app, rt = star_app()  # No live reload

        @rt("/")
        def home():
            return Div(H1("Production Site"))

        client = TestClient(app)
        response = client.get("/")

        assert response.status_code == 200
        assert "Production Site" in response.text
        # Should not have live reload scripts
        assert "/live-reload" not in response.text

    def test_multiple_pages_live_reload(self):
        """Test live reload across multiple pages."""
        app = StarHTMLWithLiveReload()

        @app.route("/")
        def home():
            return Div(H1("Home"), P("Home page content"))

        @app.route("/about")
        def about():
            return Div(H1("About"), P("About page content"))

        @app.route("/contact")
        def contact():
            return Div(H1("Contact"), P("Contact page content"))

        client = TestClient(app)

        # All pages should have live reload
        pages = ["/", "/about", "/contact"]
        for page in pages:
            response = client.get(page)
            assert response.status_code == 200
            assert "/live-reload" in response.text

    def test_live_reload_with_complex_app(self):
        """Test live reload with a more complex application structure."""
        app = StarHTMLWithLiveReload(reload_attempts=5, reload_interval=1000)

        # Add some middleware-like behavior
        @app.middleware("http")
        async def add_process_time_header(request, call_next):
            response = await call_next(request)
            response.headers["X-Process-Time"] = "0.001"
            return response

        @app.route("/")
        def home():
            return Div(H1("Complex App"), P("This app has middleware and live reload"))

        @app.route("/slow")
        def slow_endpoint():
            import time

            time.sleep(0.01)  # Simulate slow processing
            return {"message": "slow response"}

        client = TestClient(app)

        # Test that everything works together
        response = client.get("/")
        assert response.status_code == 200
        assert "X-Process-Time" in response.headers
        assert "/live-reload" in response.text

        # Test slow endpoint
        response = client.get("/slow")
        assert response.status_code == 200
        assert response.json()["message"] == "slow response"

        # Test WebSocket still works
        with client.websocket_connect("/live-reload"):
            pass

    def test_live_reload_configuration_effects(self):
        """Test how different configurations affect the generated script."""
        configs = [
            {"reload_attempts": 1, "reload_interval": 100},  # Fast, few retries
            {"reload_attempts": 20, "reload_interval": 5000},  # Slow, many retries
            {"reload_attempts": 5, "reload_interval": 1000},  # Balanced
        ]

        for config in configs:
            app = StarHTMLWithLiveReload(**config)

            def make_test_page(config_data):
                def test_page():
                    return Div(H1(f"Config Test: {config_data}"))

                return test_page

            app.route("/test")(make_test_page(config))

            client = TestClient(app)
            response = client.get("/test")

            assert response.status_code == 200

            # Check that configuration values are in the generated script
            html_content = response.text
            assert str(config["reload_interval"]) in html_content
            assert str(config["reload_attempts"]) in html_content
