"""Additional error handling tests for StarHTML framework.

This module extends the main error handling tests with additional scenarios:
- Database connection failures and recovery
- External service timeouts and retries
- File I/O errors and permission issues
- Memory and resource constraint handling
- Complex error propagation scenarios
"""

import json
import time
from pathlib import Path

from starlette.requests import Request
from starlette.testclient import TestClient

from starhtml import star_app
from starhtml.realtime import signals, sse
from starhtml.server import JSONResponse


class TestDatabaseFailureHandling:
    """Test database connection and operation failure scenarios."""

    def test_database_connection_failure(self):
        """Test handling of database connection failures."""
        app, rt = star_app()

        # Simulate database connection failure
        @rt("/api/users")
        def get_users():
            # Simulate database connection error
            try:
                # This would normally be a database call
                raise ConnectionError("Database connection failed: Connection refused")
            except ConnectionError as e:
                return JSONResponse({"error": "Database unavailable", "details": str(e)}, status_code=503)

        client = TestClient(app)
        response = client.get("/api/users")

        assert response.status_code == 503
        error_data = response.json()
        assert "Database unavailable" in error_data["error"]
        assert "Connection refused" in error_data["details"]

    def test_database_timeout_handling(self):
        """Test handling of database query timeouts."""
        app, rt = star_app()

        @rt("/api/slow-query")
        def slow_query():
            try:
                # Simulate slow database query that times out
                time.sleep(0.1)  # Simulate processing
                raise TimeoutError("Query timeout: operation took too long")
            except TimeoutError as e:
                return JSONResponse({"error": "Query timeout", "details": str(e)}, status_code=504)

        client = TestClient(app)
        response = client.get("/api/slow-query")

        assert response.status_code == 504
        error_data = response.json()
        assert "Query timeout" in error_data["error"]

    def test_database_integrity_errors(self):
        """Test handling of database integrity constraint violations."""
        app, rt = star_app()

        @rt("/api/create-user", methods=["POST"])
        async def create_user(request: Request):
            form_data = await request.form()
            email = form_data.get("email")

            # Simulate unique constraint violation
            if email == "existing@example.com":
                return JSONResponse(
                    {"error": "Integrity constraint violation", "details": f"User with email {email} already exists"},
                    status_code=409,
                )

            return {"success": True, "email": email}

        client = TestClient(app)

        # Test duplicate email error
        response = client.post("/api/create-user", data={"email": "existing@example.com"})
        assert response.status_code == 409
        assert "already exists" in response.json()["details"]

        # Test successful creation
        response = client.post("/api/create-user", data={"email": "new@example.com"})
        assert response.status_code == 200
        assert response.json()["success"] is True


class TestExternalServiceFailures:
    """Test external service integration failure scenarios."""

    def test_external_api_timeout(self):
        """Test handling of external API timeouts."""
        app, rt = star_app()

        @rt("/api/external-data")
        def get_external_data():
            try:
                # Simulate external API timeout
                time.sleep(0.05)  # Brief processing
                raise TimeoutError("External API timeout after 30 seconds")
            except TimeoutError as e:
                return JSONResponse(
                    {
                        "error": "External service timeout",
                        "details": str(e),
                        "fallback_data": {"status": "unavailable"},
                    },
                    status_code=504,
                )

        client = TestClient(app)
        response = client.get("/api/external-data")

        assert response.status_code == 504
        data = response.json()
        assert "External service timeout" in data["error"]
        assert "fallback_data" in data

    def test_external_api_invalid_response(self):
        """Test handling of invalid responses from external APIs."""
        app, rt = star_app()

        @rt("/api/external-parse")
        def parse_external_data():
            try:
                # Simulate invalid JSON response from external API
                invalid_json = '{"incomplete": json response'
                json.loads(invalid_json)  # This will fail
            except json.JSONDecodeError as e:
                return JSONResponse(
                    {
                        "error": "Invalid response from external service",
                        "details": f"JSON decode error: {str(e)}",
                        "fallback": True,
                    },
                    status_code=502,
                )

        client = TestClient(app)
        response = client.get("/api/external-parse")

        assert response.status_code == 502
        data = response.json()
        assert "Invalid response" in data["error"]
        assert data["fallback"] is True

    def test_external_service_rate_limiting(self):
        """Test handling of external service rate limiting."""
        app, rt = star_app()

        request_count = {"count": 0}

        @rt("/api/rate-limited")
        def rate_limited_endpoint():
            request_count["count"] += 1

            # Simulate rate limiting after 3 requests
            if request_count["count"] > 3:
                return JSONResponse(
                    {
                        "error": "Rate limit exceeded",
                        "details": "Too many requests to external service",
                        "retry_after": 60,
                    },
                    status_code=429,
                )

            return {"success": True, "request_number": request_count["count"]}

        client = TestClient(app)

        # First 3 requests should succeed
        for _i in range(3):
            response = client.get("/api/rate-limited")
            assert response.status_code == 200

        # 4th request should be rate limited
        response = client.get("/api/rate-limited")
        assert response.status_code == 429
        data = response.json()
        assert "Rate limit exceeded" in data["error"]
        assert data["retry_after"] == 60


class TestFileIOErrorHandling:
    """Test file I/O and permission error scenarios."""

    def test_file_not_found_error(self):
        """Test handling of missing file access."""
        app, rt = star_app()

        @rt("/api/read-file")
        def read_file(filename: str = "default.txt"):
            try:
                # Attempt to read non-existent file
                file_path = Path(f"/nonexistent/path/{filename}")
                content = file_path.read_text()
                return {"content": content}
            except FileNotFoundError as e:
                return JSONResponse(
                    {"error": "File not found", "details": str(e), "filename": filename}, status_code=404
                )

        client = TestClient(app)
        response = client.get("/api/read-file?filename=missing.txt")

        assert response.status_code == 404
        data = response.json()
        assert "File not found" in data["error"]
        assert data["filename"] == "missing.txt"

    def test_permission_denied_error(self):
        """Test handling of file permission errors."""
        app, rt = star_app()

        @rt("/api/write-file", methods=["POST"])
        async def write_file(request: Request):
            form_data = await request.form()
            form_data.get("content", "")

            try:
                # Simulate permission denied error
                raise PermissionError("Permission denied: Cannot write to /root/protected.txt")
            except PermissionError as e:
                return JSONResponse(
                    {
                        "error": "Permission denied",
                        "details": str(e),
                        "suggestion": "Check file permissions or write to a different location",
                    },
                    status_code=403,
                )

        client = TestClient(app)
        response = client.post("/api/write-file", data={"content": "test"})

        assert response.status_code == 403
        data = response.json()
        assert "Permission denied" in data["error"]
        assert "suggestion" in data

    def test_disk_space_error(self):
        """Test handling of disk space exhaustion."""
        app, rt = star_app()

        @rt("/api/large-upload", methods=["POST"])
        def upload_large_file():
            try:
                # Simulate disk space error
                raise OSError("No space left on device")
            except OSError as e:
                return JSONResponse(
                    {"error": "Storage error", "details": str(e), "suggestion": "Free up disk space and try again"},
                    status_code=507,  # Insufficient Storage
                )

        client = TestClient(app)
        response = client.post("/api/large-upload")

        assert response.status_code == 507
        data = response.json()
        assert "Storage error" in data["error"]
        assert "No space left on device" in data["details"]


class TestMemoryConstraintHandling:
    """Test memory and resource constraint scenarios."""

    def test_memory_exhaustion_handling(self):
        """Test handling of memory exhaustion scenarios."""
        app, rt = star_app()

        @rt("/api/memory-intensive")
        def memory_intensive_operation():
            try:
                # Simulate memory error
                raise MemoryError("Cannot allocate memory for large dataset")
            except MemoryError as e:
                return JSONResponse(
                    {
                        "error": "Memory exhaustion",
                        "details": str(e),
                        "suggestion": "Reduce data size or use streaming approach",
                    },
                    status_code=507,
                )

        client = TestClient(app)
        response = client.get("/api/memory-intensive")

        assert response.status_code == 507
        data = response.json()
        assert "Memory exhaustion" in data["error"]
        assert "suggestion" in data

    def test_resource_limit_handling(self):
        """Test handling of resource limit scenarios."""
        app, rt = star_app()

        active_connections = {"count": 0}
        MAX_CONNECTIONS = 5

        @rt("/api/resource-limited")
        def resource_limited():
            active_connections["count"] += 1

            if active_connections["count"] > MAX_CONNECTIONS:
                return JSONResponse(
                    {
                        "error": "Resource limit exceeded",
                        "details": f"Maximum {MAX_CONNECTIONS} concurrent connections allowed",
                        "current_count": active_connections["count"],
                    },
                    status_code=503,
                )

            # Simulate work then cleanup
            result = {"success": True, "connection_id": active_connections["count"]}
            active_connections["count"] -= 1
            return result

        client = TestClient(app)

        # Test within limits
        response = client.get("/api/resource-limited")
        assert response.status_code == 200

        # Simulate exceeding limits
        active_connections["count"] = MAX_CONNECTIONS + 1
        response = client.get("/api/resource-limited")
        assert response.status_code == 503
        data = response.json()
        assert "Resource limit exceeded" in data["error"]


class TestComplexErrorPropagation:
    """Test complex error propagation and recovery scenarios."""

    def test_cascading_failure_handling(self):
        """Test handling of cascading failures across multiple services."""
        app, rt = star_app()

        service_status = {"auth": "up", "database": "up", "cache": "up"}

        @rt("/api/complex-operation")
        def complex_operation():
            errors = []

            # Check each service
            if service_status["auth"] != "up":
                errors.append("Authentication service unavailable")

            if service_status["database"] != "up":
                errors.append("Database service unavailable")

            if service_status["cache"] != "up":
                errors.append("Cache service unavailable")

            if errors:
                return JSONResponse(
                    {"error": "Service dependencies unavailable", "failed_services": errors, "status": "degraded"},
                    status_code=503,
                )

            return {"success": True, "all_services": "operational"}

        @rt("/api/fail-service/{service}")
        def fail_service(service: str):
            if service in service_status:
                service_status[service] = "down"
                return {"service": service, "status": "failed"}
            return JSONResponse({"error": "Unknown service"}, status_code=404)

        client = TestClient(app)

        # Test normal operation
        response = client.get("/api/complex-operation")
        assert response.status_code == 200

        # Fail a service
        client.get("/api/fail-service/database")

        # Test cascading failure
        response = client.get("/api/complex-operation")
        assert response.status_code == 503
        data = response.json()
        assert "Service dependencies unavailable" in data["error"]
        assert "Database service unavailable" in data["failed_services"]

    def test_partial_failure_recovery(self):
        """Test handling of partial failures with recovery mechanisms."""
        app, rt = star_app()

        @rt("/api/resilient-operation")
        def resilient_operation():
            results = {"primary": None, "fallback": None, "status": "unknown"}

            try:
                # Try primary operation
                raise ConnectionError("Primary service failed")
            except ConnectionError:
                try:
                    # Try fallback operation
                    results["fallback"] = "fallback_data"
                    results["status"] = "degraded"
                except Exception:
                    results["status"] = "failed"
                    return JSONResponse({"error": "All operations failed", "results": results}, status_code=503)

            return {"success": True, "results": results, "message": "Operation completed with fallback"}

        client = TestClient(app)
        response = client.get("/api/resilient-operation")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["results"]["status"] == "degraded"
        assert data["results"]["fallback"] == "fallback_data"


class TestSSEConnectionFailures:
    """Test SSE connection and streaming error scenarios."""

    def test_sse_connection_drop(self):
        """Test handling of SSE connection drops."""
        app, rt = star_app()

        @rt("/events")
        @sse
        def event_stream():
            try:
                yield signals(status="connected")
                # Simulate connection drop
                raise ConnectionResetError("Connection reset by peer")
            except ConnectionResetError as e:
                # In real SSE, connection would just close
                # We'll test the error handling logic
                yield signals(error=f"Connection error: {str(e)}")

        client = TestClient(app)

        # Test SSE endpoint
        with client.stream("GET", "/events") as response:
            assert response.status_code == 200
            assert response.headers["content-type"] == "text/event-stream"

            # Read first event
            content = response.iter_lines()
            events = list(content)

            # Should have status event and error event
            assert len(events) >= 2  # Event data comes in multiple lines

    def test_sse_error_recovery(self):
        """Test SSE error recovery and continued streaming."""
        app, rt = star_app()

        @rt("/error-recovery-events")
        @sse
        def error_recovery_stream():
            # Send a series of events with some errors
            yield signals(status="starting", count=1)
            yield signals(status="processing", count=2)

            # Simulate a processing error (but handle it gracefully)
            yield signals(status="error_occurred", error="Simulated processing error", count=3, recovery=True)

            # Continue streaming after error
            yield signals(status="recovered", count=4)
            yield signals(status="completed", count=5)

        client = TestClient(app)

        with client.stream("GET", "/error-recovery-events") as response:
            assert response.status_code == 200
            assert response.headers["content-type"] == "text/event-stream"

            content = response.iter_lines()
            events = list(content)

            # Should have multiple events despite the error
            assert len(events) > 0

            # Check that we got progression through all states
            event_data = "\n".join(str(line, "utf-8") if isinstance(line, bytes) else line for line in events)
            assert "starting" in event_data
            assert "error_occurred" in event_data
            assert "recovered" in event_data
            assert "completed" in event_data


class TestInputValidationEdgeCases:
    """Test edge cases in input validation and malformed data."""

    def test_extremely_large_input(self):
        """Test handling of extremely large input data."""
        app, rt = star_app()

        @rt("/api/validate-input", methods=["POST"])
        async def validate_input(request: Request):
            try:
                body = await request.body()

                # Check size limit (1MB)
                if len(body) > 1024 * 1024:
                    return JSONResponse(
                        {"error": "Input too large", "size": len(body), "max_size": 1024 * 1024},
                        status_code=413,  # Payload Too Large
                    )

                return {"success": True, "size": len(body)}
            except Exception as e:
                return JSONResponse({"error": "Input processing failed", "details": str(e)}, status_code=400)

        client = TestClient(app)

        # Test normal size
        response = client.post("/api/validate-input", content="normal data")
        assert response.status_code == 200

        # Test large input
        large_data = "x" * (1024 * 1024 + 1)  # 1MB + 1 byte
        response = client.post("/api/validate-input", content=large_data)
        assert response.status_code == 413
        data = response.json()
        assert "Input too large" in data["error"]

    def test_null_byte_injection(self):
        """Test handling of null byte injection attempts."""
        app, rt = star_app()

        @rt("/api/process-text", methods=["POST"])
        async def process_text(request: Request):
            form_data = await request.form()
            text = form_data.get("text", "")

            # Check for null bytes
            if isinstance(text, str) and "\x00" in text:
                return JSONResponse(
                    {"error": "Invalid characters detected", "details": "Null bytes not allowed in text input"},
                    status_code=400,
                )

            return {"processed_text": text.strip(), "length": len(text)}

        client = TestClient(app)

        # Test normal text
        response = client.post("/api/process-text", data={"text": "normal text"})
        assert response.status_code == 200

        # Test null byte injection
        malicious_text = "text with\x00null byte"
        response = client.post("/api/process-text", data={"text": malicious_text})
        assert response.status_code == 400
        data = response.json()
        assert "Invalid characters" in data["error"]

    def test_unicode_normalization_issues(self):
        """Test handling of Unicode normalization edge cases."""
        app, rt = star_app()

        @rt("/api/normalize-text", methods=["POST"])
        async def normalize_text(request: Request):
            import unicodedata

            form_data = await request.form()
            text = form_data.get("text", "")

            try:
                # Normalize Unicode
                normalized = unicodedata.normalize("NFC", text)
                return {"original": text, "normalized": normalized, "same": text == normalized}
            except Exception as e:
                return JSONResponse({"error": "Unicode processing failed", "details": str(e)}, status_code=400)

        client = TestClient(app)

        # Test Unicode normalization
        # These are different representations of the same character
        text1 = "café"  # é as single character
        text2 = "cafe\u0301"  # é as e + combining accent

        response = client.post("/api/normalize-text", data={"text": text1})
        assert response.status_code == 200

        response = client.post("/api/normalize-text", data={"text": text2})
        assert response.status_code == 200
        data = response.json()
        assert "normalized" in data
