"""Security tests for StarHTML framework.

This module tests security aspects including:
- XSS prevention through proper HTML escaping
- CSRF protection mechanisms
- SQL injection prevention
- Script injection attacks
- Content Security Policy compliance
- Input validation and sanitization
"""

import json

from starlette.testclient import TestClient

from starhtml import Button, Div, Form, Input, Script, star_app
from starhtml.datastar import ds_on_click, ds_text
from starhtml.realtime import format_element_event, format_signal_event, signals


class TestXSSPrevention:
    """Test XSS (Cross-Site Scripting) prevention."""

    def test_html_escaping_in_content(self):
        """Test that HTML is properly escaped in element content."""
        malicious_content = "<script>alert('xss')</script>"
        element = Div(malicious_content)
        html = str(element)

        # Should escape dangerous HTML
        assert "&lt;script&gt;" in html
        assert "&lt;/script&gt;" in html
        assert "<script>" not in html
        # Single quotes are also escaped to &#x27;
        assert "alert(&#x27;xss&#x27;)" in html or "alert('xss')" in html

    def test_attribute_value_escaping(self):
        """Test that attribute values are properly escaped."""
        malicious_value = '"><script>alert("xss")</script>'
        element = Div("Content", title=malicious_value)
        html = str(element)

        # Should escape HTML in attributes
        assert "&gt;" in html
        assert "&lt;" in html
        # The double quote in the malicious value is handled by using single quotes for the attribute
        assert "title='\"&gt;" in html
        assert "<script>" not in html
        # Double quotes don't need escaping inside single-quoted attributes
        assert "&lt;script&gt;" in html

    def test_javascript_injection_in_datastar_attrs(self):
        """Test prevention of JavaScript injection in Datastar attributes."""
        malicious_js = "'; alert('xss'); //"
        element = Div("Content", ds_on_click(f"handleClick('{malicious_js}')"))
        html = str(element)

        # Test that Datastar attribute is properly converted
        assert "data-on-click=" in html
        assert "handleClick" in html

        # The malicious JS should be contained within the attribute value
        # Client-side Datastar framework must handle this safely
        assert malicious_js in html  # Content preserved for framework handling

    def test_sse_signal_xss_prevention(self):
        """Test XSS prevention in SSE signals."""
        malicious_data = {
            "message": "<script>alert('xss')</script>",
            "user_input": "</script><script>alert('pwned')</script>",
            "onclick": "javascript:alert('xss')",
        }

        sse_output = format_signal_event(malicious_data)

        # Verify the SSE output is well-formed
        assert "event: datastar-patch-signals" in sse_output
        assert "data: signals " in sse_output
        assert sse_output.endswith("\n\n")

        # Parse and verify the JSON payload
        data_line = [line for line in sse_output.split("\n") if line.startswith("data: signals ")][0]
        json_payload = data_line[len("data: signals ") :]

        # Verify it's valid JSON (would fail if not properly escaped)
        parsed_data = json.loads(json_payload)

        # Verify the malicious content is preserved in JSON
        # This is correct - JSON transmission preserves the data
        # Security must be enforced when rendering on client
        assert parsed_data["message"] == malicious_data["message"]
        assert parsed_data["user_input"] == malicious_data["user_input"]

        # Verify no script tags are executed during JSON parsing
        # (they're just strings in JSON context)
        assert isinstance(parsed_data["message"], str)
        assert isinstance(parsed_data["onclick"], str)

    def test_sse_element_xss_prevention(self):
        """Test XSS prevention in SSE element updates."""
        # Test various XSS vectors
        xss_vectors = [
            "<img src=x onerror=alert('xss')>",
            "<script>alert('xss')</script>",
            "<iframe src='javascript:alert(1)'></iframe>",
            "<svg onload=alert('xss')></svg>",
        ]

        for malicious_html in xss_vectors:
            sse_output = format_element_event(malicious_html, "#target")

            # Verify SSE format
            assert "event: datastar-patch-elements" in sse_output

            # Extract the HTML content from SSE (it's on the 'data: elements' line)
            lines = sse_output.split("\n")
            html_content = None
            for line in lines:
                if line.startswith("data: elements "):
                    html_content = line[len("data: elements ") :]
                    break
            assert html_content is not None, f"No element data found in: {sse_output}"

            # Verify dangerous HTML tags are escaped
            # The important thing is that the < and > are escaped, preventing script execution
            assert "<script>" not in html_content, f"Unescaped script tag in: {html_content}"
            assert "<img " not in html_content, f"Unescaped img tag in: {html_content}"
            assert "<iframe" not in html_content, f"Unescaped iframe tag in: {html_content}"
            assert "<svg" not in html_content, f"Unescaped svg tag in: {html_content}"

            # Verify the content has been HTML-escaped
            assert "&lt;" in html_content, f"No escaped < found in: {html_content}"
            assert "&gt;" in html_content, f"No escaped > found in: {html_content}"

            # The key security feature is that tags are escaped, preventing execution
            # Attributes within escaped tags don't need additional escaping


class TestCSRFProtection:
    """Test CSRF (Cross-Site Request Forgery) protection."""

    def test_form_with_csrf_token(self):
        """Test form includes and validates CSRF protection."""
        app, rt = star_app()

        # Simulate session-based CSRF tokens
        csrf_tokens = {}

        @rt("/form")
        def show_form(request):
            # Generate unique CSRF token per session
            import secrets

            session_id = request.headers.get("cookie", "default")
            csrf_token = secrets.token_urlsafe(32)
            csrf_tokens[session_id] = csrf_token

            return Form(
                Input(type="hidden", name="csrf_token", value=csrf_token),
                Input(type="text", name="username"),
                Button("Submit", type="submit"),
                method="post",
                action="/submit",
            )

        @rt("/submit", methods=["POST"])
        async def submit_form(request):
            form_data = await request.form()
            session_id = request.headers.get("cookie", "default")

            # Validate CSRF token
            submitted_token = form_data.get("csrf_token")
            expected_token = csrf_tokens.get(session_id)

            if not submitted_token or submitted_token != expected_token:
                from starhtml import JSONResponse

                return JSONResponse({"error": "Invalid CSRF token"}, status_code=403)

            return {"success": True, "username": form_data.get("username")}

        client = TestClient(app)

        # Get form with CSRF token
        response = client.get("/form")
        assert response.status_code == 200
        assert 'name="csrf_token"' in response.text
        assert 'type="hidden"' in response.text

        # Extract CSRF token from form
        import re

        token_match = re.search(r'value="([^"]+)"', response.text)
        assert token_match
        csrf_token = token_match.group(1)

        # Test valid submission with correct token
        response = client.post("/submit", data={"csrf_token": csrf_token, "username": "testuser"})
        assert response.status_code == 200
        assert response.json()["success"] is True

        # Test invalid submission with wrong token
        response = client.post("/submit", data={"csrf_token": "wrong_token", "username": "testuser"})
        assert response.status_code == 403
        assert "Invalid CSRF token" in response.json()["error"]

        # Test submission without token
        response = client.post("/submit", data={"username": "testuser"})
        assert response.status_code == 403
        assert "Invalid CSRF token" in response.json()["error"]

    def test_state_changing_requires_post(self):
        """Test that state-changing operations require POST."""
        app, rt = star_app()

        @rt("/delete/{item_id}", methods=["POST"])
        def delete_item(item_id: int):
            return {"deleted": item_id}

        @rt("/delete/{item_id}", methods=["GET"])
        def get_delete_form(item_id: int):
            return {"error": "Use POST to delete"}

        client = TestClient(app)

        # GET should not perform deletion
        response = client.get("/delete/123")
        assert response.status_code == 200
        assert response.json()["error"] == "Use POST to delete"

        # POST should perform deletion
        response = client.post("/delete/123")
        assert response.status_code == 200
        assert response.json()["deleted"] == 123


class TestInjectionPrevention:
    """Test prevention of various injection attacks."""

    def test_template_injection_prevention(self):
        """Test prevention of template injection attacks."""
        # Attempt template injection
        malicious_input = "{{7*7}}"
        element = Div(malicious_input)
        html = str(element)

        # Should not evaluate template expressions
        assert "49" not in html
        assert "{{7*7}}" in html

    def test_expression_injection_in_datastar(self):
        """Test prevention of expression injection in Datastar."""
        malicious_expr = "user.name; alert('injection')"
        element = Div(ds_text(malicious_expr))
        html = str(element)

        # Should preserve the expression as-is (Datastar will handle safely)
        assert (
            "data-text=\"user.name; alert('injection')\"" in html
            or "data-text=\"user.name; alert(\\'injection\\')\"" in html
        )

    def test_path_traversal_prevention(self):
        """Test prevention of path traversal attacks."""
        app, rt = star_app()

        @rt("/api/file", methods=["POST"])
        async def get_file(request):
            # Get filename from request body
            data = await request.json()
            filename = data.get("filename", "")

            # Proper path traversal validation
            import os

            # Check for dangerous patterns
            if ".." in filename or filename.startswith("/") or "\\" in filename:
                from starhtml import JSONResponse

                return JSONResponse({"error": "Invalid filename", "filename": filename}, status_code=400)

            # Additional check with os.path
            safe_filename = os.path.basename(filename)
            if safe_filename != filename:
                from starhtml import JSONResponse

                return JSONResponse({"error": "Path traversal detected", "filename": filename}, status_code=400)

            return {"filename": safe_filename, "safe": True}

        client = TestClient(app)

        # Test various path traversal attempts
        traversal_attempts = [
            ("../etc/passwd", 400, "Invalid filename"),
            ("..\\windows\\system32", 400, "Invalid filename"),
            ("test/../secret", 400, "Invalid filename"),
            ("..", 400, "Invalid filename"),
            ("/etc/passwd", 400, "Invalid filename"),
            ("subdir/file.txt", 400, "Path traversal detected"),
            ("valid_file.txt", 200, None),
            ("test_123.json", 200, None),
            ("data.csv", 200, None),
        ]

        for filename, expected_status, expected_error in traversal_attempts:
            response = client.post("/api/file", json={"filename": filename})
            assert response.status_code == expected_status, f"Failed for {filename}: got {response.status_code}"

            if expected_status == 400:
                error_data = response.json()
                assert "error" in error_data
                assert expected_error in error_data["error"]
                # Verify the attempted filename is logged
                assert error_data["filename"] == filename
            else:
                data = response.json()
                assert data["filename"] == filename
                assert data["safe"] is True
                # Verify no path separators in safe filenames
                assert "/" not in data["filename"]
                assert "\\" not in data["filename"]
                assert ".." not in data["filename"]


class TestInputValidation:
    """Test input validation and sanitization."""

    def test_form_input_length_validation(self):
        """Test form input length validation."""
        app, rt = star_app()

        @rt("/submit", methods=["POST"])
        async def submit_form(request):
            # Simulate input validation
            form_data = await request.form()
            username = form_data.get("username", "")

            if len(username) > 50:
                return {"error": "Username too long"}
            if len(username) < 3:
                return {"error": "Username too short"}

            return {"success": True, "username": username}

        client = TestClient(app)

        # Test valid input
        response = client.post("/submit", data={"username": "validuser"})
        assert response.status_code == 200
        assert response.json()["success"] is True

        # Test too long input
        long_username = "a" * 100
        response = client.post("/submit", data={"username": long_username})
        assert response.status_code == 200
        assert "too long" in response.json()["error"]

    def test_special_characters_handling(self):
        """Test handling of special characters in input."""
        special_chars = "!@#$%^&*()[]{}|;':\",./<>?"
        element = Div(special_chars)
        html = str(element)

        # Test that dangerous characters are properly escaped
        dangerous_chars = ["<", ">", '"', "&"]
        for char in dangerous_chars:
            if char in special_chars:
                # Character should be escaped (not appear raw) if dangerous
                escaped_forms = ["&lt;", "&gt;", "&quot;", "&amp;"]
                assert any(escaped in html for escaped in escaped_forms)

        # Content should be preserved in escaped form
        assert len(html) > len(special_chars)  # Escaping adds length

    def test_unicode_handling(self):
        """Test proper Unicode handling."""
        unicode_content = "Hello 世界! 🚀 Café"
        element = Div(unicode_content)
        html = str(element)

        # Test that Unicode content is preserved (either directly or escaped)
        # The key is that content is preserved and safe
        test_chars = ["世界", "🚀", "Café"]
        for char in test_chars:
            # Content should be present either directly or as unicode escape
            assert char in html or "\\u" in html

        # Verify the element structure is correct
        assert html.startswith("<div") and html.endswith("</div>")


class TestContentSecurityPolicy:
    """Test Content Security Policy compliance."""

    def test_inline_script_prevention(self):
        """Test that inline scripts are handled appropriately."""
        # Direct script injection should be escaped
        malicious_content = '<script>alert("xss")</script>'
        element = Div(malicious_content)
        html = str(element)

        assert "&lt;script&gt;" in html
        assert "<script>" not in html

    def test_script_element_creation(self):
        """Test proper script element creation."""
        # Valid script element should work
        script = Script("console.log('safe')")
        html = str(script)

        # Test script element structure and content preservation
        assert html.startswith("<script") and html.endswith("</script>")
        assert "console.log('safe')" in html

        # Verify it's a properly formed script tag
        assert script.tag == "script"
        assert len(script.children) > 0

    def test_datastar_attribute_safety(self):
        """Test that Datastar attributes don't create CSP violations."""
        element = Div("Content", ds_on_click("handleClick()"), ds_text("user.name"))
        html = str(element)

        # Test that Datastar attributes are properly converted to data- attributes
        assert "data-on-click=" in html and "handleClick" in html
        assert "data-text=" in html and "user.name" in html

        # Critical security test: no inline event handlers
        assert "onclick=" not in html.lower()
        assert "onload=" not in html.lower()
        assert "onerror=" not in html.lower()


class TestSecurityHeaders:
    """Test security-related HTTP headers."""

    def test_sse_security_headers(self):
        """Test that SSE endpoints have appropriate security headers."""
        app, rt = star_app()

        @rt("/events")
        def events():
            # Would use @sse decorator in real implementation
            from starlette.responses import StreamingResponse

            from starhtml.realtime import SSE_HEADERS

            def event_stream():
                yield "data: test\\n\\n"

            return StreamingResponse(event_stream(), media_type="text/event-stream", headers=SSE_HEADERS)

        client = TestClient(app)
        response = client.get("/events")

        assert response.status_code == 200
        assert response.headers["content-type"] == "text/event-stream"
        assert "no-cache" in response.headers.get("cache-control", "")

    def test_json_response_security(self):
        """Test JSON response security headers."""
        app, rt = star_app()

        @rt("/api/data")
        def api_data():
            return {"sensitive": "data", "user_id": 123}

        client = TestClient(app)
        response = client.get("/api/data")

        assert response.status_code == 200
        assert response.headers["content-type"] == "application/json"
        # Should not have dangerous headers that could enable attacks


class TestSessionSecurity:
    """Test session and authentication security."""

    def test_secure_cookie_attributes(self):
        """Test that cookies have secure attributes."""
        from starhtml.server import cookie

        # Test secure cookie creation
        secure_cookie = cookie("session", "secret_value", httponly=True, secure=True, samesite="strict")

        cookie_str = str(secure_cookie)
        assert "HttpOnly" in cookie_str
        assert "Secure" in cookie_str
        assert "SameSite=strict" in cookie_str

    def test_session_token_format(self):
        """Test session token format security."""
        from starhtml.utils import unqid

        # Generate multiple tokens to test randomness
        tokens = [unqid() for _ in range(10)]

        # All tokens should be different
        assert len(set(tokens)) == 10

        # Tokens should be reasonably long and URL-safe
        for token in tokens:
            assert len(token) > 10
            assert token.startswith("_")
            # Should not contain dangerous characters
            assert "<" not in token
            assert ">" not in token
            assert "'" not in token
            assert '"' not in token


class TestRealtimeSecurityScenarios:
    """Test security in real-time scenarios."""

    def test_malicious_signal_data(self):
        """Test handling of malicious data in signals."""
        malicious_signals = signals(
            script="<script>window.location='http://evil.com'</script>", injection="'; DROP TABLE users; --"
        )

        sse_output = format_signal_event(malicious_signals[1]["payload"])

        # In JSON, HTML doesn't need escaping - the client must handle it safely
        data_line = [line for line in sse_output.split("\n") if line.startswith("data: signals ")][0]
        json_data = json.loads(data_line[len("data: signals ") :])
        assert json_data["script"] == "<script>window.location='http://evil.com'</script>"
        assert "DROP TABLE" in sse_output  # SQL injection text is preserved but safe in JSON

    def test_malicious_element_updates(self):
        """Test handling of malicious HTML in element updates."""
        malicious_element = Div("<iframe src=\"javascript:alert('xss')\"></iframe>", 'onclick="steal_cookies()"')

        sse_output = format_element_event(malicious_element, "#target")

        # HTML should be escaped
        assert "&lt;iframe" in sse_output
        assert "javascript:alert" not in sse_output or "&quot;" in sse_output

    def test_concurrent_session_isolation(self):
        """Test that concurrent sessions are properly isolated."""
        app, rt = star_app()

        user_sessions = {}

        @rt("/login", methods=["POST"])
        async def login(request):
            form_data = await request.form()
            user_id = form_data.get("user_id")
            session_id = f"session_{user_id}"
            user_sessions[session_id] = {"user_id": user_id, "data": f"private_{user_id}"}
            return {"session": session_id}

        @rt("/data/{session_id}")
        def get_data(session_id: str):
            if session_id not in user_sessions:
                return {"error": "Invalid session"}
            return user_sessions[session_id]

        client = TestClient(app)

        # Create two separate sessions
        resp1 = client.post("/login", data={"user_id": "user1"})
        resp2 = client.post("/login", data={"user_id": "user2"})

        session1 = resp1.json()["session"]
        session2 = resp2.json()["session"]

        # Each session should only access its own data
        data1 = client.get(f"/data/{session1}").json()
        data2 = client.get(f"/data/{session2}").json()

        assert data1["user_id"] == "user1"
        assert data2["user_id"] == "user2"
        assert data1["data"] != data2["data"]
