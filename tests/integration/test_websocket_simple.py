"""Simple WebSocket tests to verify basic functionality."""

from starlette.testclient import TestClient

from starhtml import H1, Div, P, star_app
from starhtml.realtime import setup_ws


class TestWebSocketSimple:
    """Test basic WebSocket functionality with simple examples."""

    def test_websocket_text_echo(self):
        """Test simple text echo over WebSocket."""
        app, rt = star_app()

        @app.ws("/echo")
        def echo_handler(message: str = ""):
            # Simple echo - return what was sent
            return f"Echo: {message}"

        client = TestClient(app)

        with client.websocket_connect("/echo") as websocket:
            # Send and receive text
            websocket.send_json({"message": "Hello"})
            response = websocket.receive_text()
            assert response == "Echo: Hello"

    def test_websocket_html_response(self):
        """Test WebSocket returning HTML elements."""
        app, rt = star_app()

        @app.ws("/html")
        def html_handler(element_type: str = "div"):
            # Return HTML based on request
            if element_type == "heading":
                return H1("WebSocket Heading")
            elif element_type == "paragraph":
                return P("WebSocket paragraph")
            else:
                return Div("Default div")

        client = TestClient(app)

        with client.websocket_connect("/html") as websocket:
            # Request heading
            websocket.send_json({"element_type": "heading"})
            response = websocket.receive_text()
            assert "<h1>WebSocket Heading</h1>" in response

            # Request paragraph
            websocket.send_json({"element_type": "paragraph"})
            response = websocket.receive_text()
            assert "<p>WebSocket paragraph</p>" in response

    def test_websocket_lifecycle(self):
        """Test WebSocket connection lifecycle."""
        app, rt = star_app()

        connections = []

        async def on_connect(ws):
            connections.append("connected")

        async def on_disconnect(ws):
            connections.append("disconnected")

        @app.ws("/lifecycle", conn=on_connect, disconn=on_disconnect)
        def handler(msg: str = ""):
            connections.append(f"message: {msg}")
            return "OK"

        client = TestClient(app)

        # Connect and disconnect
        with client.websocket_connect("/lifecycle") as websocket:
            assert "connected" in connections

            websocket.send_json({"msg": "test"})
            response = websocket.receive_text()
            assert response == "OK"
            assert any("message:" in c for c in connections)

        # Should be disconnected after context exit
        assert "disconnected" in connections

    def test_websocket_parameter_types(self):
        """Test parameter type conversion in WebSocket handlers."""
        app, rt = star_app()

        received_params = {}

        @app.ws("/params")
        def param_handler(count: int = 0, active: bool = False, name: str = "", score: float = 0.0):
            received_params.update({"count": count, "active": active, "name": name, "score": score})
            return f"Received: count={count}, active={active}, name={name}, score={score}"

        client = TestClient(app)

        with client.websocket_connect("/params") as websocket:
            # Send parameters that need conversion
            websocket.send_json({"count": "42", "active": "true", "name": "test", "score": "3.14"})
            websocket.receive_text()

            # Verify conversions
            assert received_params["count"] == 42
            assert received_params["active"] is True
            assert received_params["name"] == "test"
            assert abs(received_params["score"] - 3.14) < 0.001

    def test_websocket_error_handling(self):
        """Test WebSocket error handling behavior."""
        app, rt = star_app()

        @app.ws("/error_test")
        def error_handler(safe: bool = True):
            if not safe:
                # Handlers should handle errors gracefully
                return None  # Return nothing on error condition
            return "Safe response"

        client = TestClient(app)

        with client.websocket_connect("/error_test") as websocket:
            # Normal operation
            websocket.send_json({"safe": True})
            response = websocket.receive_text()
            assert response == "Safe response"

            # Error condition - returns None which shouldn't send
            websocket.send_json({"safe": False})
            # Immediately send another to check connection
            websocket.send_json({"safe": True})
            response = websocket.receive_text()
            assert response == "Safe response"

    def test_setup_ws_functionality(self):
        """Test the setup_ws helper for broadcasting."""
        app, rt = star_app()

        # Set up WebSocket management
        send_func = setup_ws(app)

        # Verify the app has the expected attributes
        assert hasattr(app, "_send")
        assert callable(send_func)

        # The actual broadcast test would require real WebSocket connections
        # Here we just verify the structure is set up correctly
        client = TestClient(app)

        # The /ws route should be available
        with client.websocket_connect("/ws"):
            # Connection should work
            pass

    def test_websocket_special_params(self):
        """Test special parameter injection like ws, scope, etc."""
        app, rt = star_app()

        param_info = {}

        @app.ws("/special")
        def special_handler(ws, scope):
            # These special params should be injected
            param_info["has_ws"] = ws is not None
            param_info["has_scope"] = scope is not None
            param_info["scope_type"] = type(scope).__name__
            return "OK"

        client = TestClient(app)

        with client.websocket_connect("/special") as websocket:
            websocket.send_json({})
            response = websocket.receive_text()
            assert response == "OK"

            # Verify special params were injected
            assert param_info["has_ws"] is True
            assert param_info["has_scope"] is True

    def test_websocket_falsy_responses(self):
        """Test WebSocket behavior with falsy responses.

        FIXED: Changed from 'if not resp:' to 'if resp is None:' to allow
        empty strings to be sent. This aligns with standard web API behavior
        where empty string is a valid response, and only None means "no response".

        Previous behavior treated "" as falsy (Python), but web APIs typically
        expect empty strings to be sent (like JavaScript/DOM). This change makes
        the behavior more intuitive for web developers.
        """
        app, rt = star_app()

        message_log = []

        @app.ws("/falsy")
        def falsy_handler(value: str = "default"):
            message_log.append(f"Handler called with: {value}")

            if value == "none":
                return None  # Won't send (only None prevents sending)
            elif value == "empty":
                return ""  # WILL send (empty string is valid response)
            elif value == "zero":
                return "0"  # This WILL send (string "0" is truthy)
            elif value == "space":
                return " "  # This WILL send (non-empty string)
            else:
                return f"Value: {value}"

        client = TestClient(app)

        with client.websocket_connect("/falsy") as websocket:
            # Test truthy responses that work normally
            websocket.send_json({"value": "test"})
            response = websocket.receive_text()
            assert response == "Value: test"

            # Test empty string (should now work after fix)
            websocket.send_json({"value": "empty"})
            response = websocket.receive_text()
            assert response == ""

            # Test string "0" (truthy)
            websocket.send_json({"value": "zero"})
            response = websocket.receive_text()
            assert response == "0"

            # Test single space (truthy)
            websocket.send_json({"value": "space"})
            response = websocket.receive_text()
            assert response == " "

        # Verify handler was called for all tests
        assert len(message_log) >= 4

        # Note: We still can't test None responses without hanging because
        # they don't send anything and receive_text() will wait forever.
        # This is the intended behavior - only None means "don't send".
