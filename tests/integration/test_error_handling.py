"""Error handling and resilience tests for StarHTML framework.

This module tests error handling aspects including:
- Network failures and timeouts
- Malformed input handling
- Resource exhaustion scenarios
- Exception propagation and recovery
- Graceful degradation patterns
- Error boundary testing
"""

import time

from starlette.requests import Request
from starlette.testclient import TestClient

from starhtml import H1, Div, star_app
from starhtml.realtime import format_element_event, format_signal_event, signals, sse
from starhtml.server import JSONResponse


class TestMalformedInputHandling:
    """Test handling of malformed and invalid input."""

    def test_malformed_json_request(self):
        """Test handling of malformed JSON in requests."""
        app, rt = star_app()

        @rt("/api/data", methods=["POST"])
        async def handle_json(request: Request):
            try:
                data = await request.json()
                return {"received": data}
            except Exception as e:
                return JSONResponse({"error": "Invalid JSON", "details": str(e)}, status_code=400)

        client = TestClient(app)

        # Send malformed JSON
        response = client.post(
            "/api/data", content='{"invalid": json malformed}', headers={"content-type": "application/json"}
        )

        assert response.status_code == 400
        assert "Invalid JSON" in response.json()["error"]

    def test_missing_required_fields(self):
        """Test handling of missing required form fields."""
        app, rt = star_app()

        @rt("/submit", methods=["POST"])
        async def submit_form(request: Request):
            form_data = await request.form()
            required_fields = ["name", "email"]

            missing = [field for field in required_fields if not form_data.get(field)]
            if missing:
                return JSONResponse({"error": "Missing required fields", "missing": missing}, status_code=422)

            return {"success": True}

        client = TestClient(app)

        # Submit incomplete form
        response = client.post("/submit", data={"name": "John"})  # Missing email
        assert response.status_code == 422
        assert "email" in response.json()["missing"]

    def test_invalid_data_types(self):
        """Test handling of invalid data types in parameters."""
        app, rt = star_app()

        @rt("/user/{user_id}")
        def get_user(user_id: int):
            return {"user_id": user_id, "type": type(user_id).__name__}

        client = TestClient(app)

        # Send non-integer where integer expected
        response = client.get("/user/not-a-number")
        # StarHTML doesn't do automatic type validation - returns 404 for invalid paths
        assert response.status_code == 404

    def test_oversized_input(self):
        """Test handling of oversized input data."""
        app, rt = star_app()

        @rt("/upload", methods=["POST"])
        def upload_data(request: Request):
            content_length = request.headers.get("content-length")
            if content_length and int(content_length) > 1000:  # 1KB limit
                return JSONResponse({"error": "Payload too large"}, status_code=413)

            return {"status": "uploaded"}

        client = TestClient(app)

        # Send oversized data
        large_data = "x" * 2000
        response = client.post("/upload", content=large_data)
        assert response.status_code == 413
        assert "too large" in response.json()["error"]


class TestNetworkFailureSimulation:
    """Test network failure and timeout scenarios."""

    def test_slow_response_handling(self):
        """Test handling of slow responses."""
        app, rt = star_app()

        @rt("/slow")
        def slow_endpoint():
            time.sleep(0.1)  # Simulate slow processing
            return {"message": "slow response"}

        client = TestClient(app)

        start_time = time.time()
        response = client.get("/slow")
        elapsed = time.time() - start_time

        assert response.status_code == 200
        assert elapsed >= 0.1
        assert response.json()["message"] == "slow response"

    def test_connection_error_simulation(self):
        """Test simulated connection errors."""
        app, rt = star_app()

        @rt("/external-api")
        def external_api():
            # Simulate external API call failure
            try:
                # This would be an actual external call in real code
                raise ConnectionError("Cannot connect to external service")
            except ConnectionError as e:
                return JSONResponse({"error": "External service unavailable", "details": str(e)}, status_code=503)

        client = TestClient(app)
        response = client.get("/external-api")

        assert response.status_code == 503
        assert "unavailable" in response.json()["error"]

    def test_partial_response_handling(self):
        """Test handling of partial streaming responses with graceful error handling."""
        app, rt = star_app()

        @rt("/streaming")
        def streaming_response():
            def generate():
                try:
                    for i in range(5):
                        if i == 3:
                            # Simulate interruption - but yield error info instead of crashing
                            yield f"ERROR: Stream interrupted at chunk {i}\n"
                            break  # Stop streaming gracefully
                        yield f"data chunk {i}\n"
                except Exception as e:
                    yield f"EXCEPTION: {str(e)}\n"

            from starlette.responses import StreamingResponse

            return StreamingResponse(generate(), media_type="text/plain")

        client = TestClient(app)

        # The streaming will provide partial data then error info
        response = client.get("/streaming")

        # Verify streaming behavior
        assert response.status_code == 200

        # Read the content - should get partial data before interruption
        content = response.text

        # Should get initial chunks before interruption
        assert "data chunk 0" in content
        assert "data chunk 1" in content
        assert "data chunk 2" in content

        # Should get error information at chunk 3
        assert "ERROR: Stream interrupted at chunk 3" in content

        # Should not get chunk 4 since we stopped at 3
        assert "data chunk 4" not in content

        # The response should contain the error indication
        assert "Stream interrupted" in content


class TestResourceExhaustion:
    """Test resource exhaustion scenarios."""

    def test_large_data_processing(self):
        """Test handling of progressively larger data sets."""
        app, rt = star_app()

        @rt("/process-data/{size}")
        def process_data(size: int):
            # Process data of specified size
            max_safe_size = 1000  # Define clear limit

            if size > max_safe_size:
                return JSONResponse({"error": "Data size exceeds limit", "max_size": max_safe_size}, status_code=413)

            # Process the data
            data = ["item" * 10 for _ in range(size)]
            return {"processed": len(data), "total_chars": sum(len(item) for item in data), "status": "success"}

        client = TestClient(app)

        # Test within limits
        response = client.get("/process-data/100")
        assert response.status_code == 200
        data = response.json()
        assert data["processed"] == 100
        assert data["status"] == "success"

        # Test exceeding limits
        response = client.get("/process-data/2000")
        assert response.status_code == 413
        error_data = response.json()
        assert "exceeds limit" in error_data["error"]
        assert error_data["max_size"] == 1000

    def test_concurrent_request_handling(self):
        """Test handling of concurrent requests with proper sequencing."""
        app, rt = star_app()

        request_counter = {"count": 0, "active": 0, "max_concurrent": 0}

        @rt("/concurrent")
        def concurrent_endpoint():
            request_counter["active"] += 1
            request_counter["max_concurrent"] = max(request_counter["max_concurrent"], request_counter["active"])

            current_count = request_counter["count"]
            request_counter["count"] += 1

            time.sleep(0.02)  # Simulate processing time

            request_counter["active"] -= 1

            return {
                "request_number": current_count,
                "active_count": request_counter["active"] + 1,  # +1 for this request
                "total_processed": request_counter["count"],
            }

        client = TestClient(app)

        # TestClient processes requests sequentially
        responses = []
        for _i in range(3):
            response = client.get("/concurrent")
            responses.append(response)

        # Verify all requests succeeded with proper sequencing
        for i, response in enumerate(responses):
            assert response.status_code == 200
            data = response.json()
            assert data["request_number"] == i
            assert data["active_count"] == 1  # TestClient is sequential
            assert data["total_processed"] == i + 1

        # Verify counter state
        assert request_counter["count"] == 3
        assert request_counter["active"] == 0  # All completed
        assert request_counter["max_concurrent"] == 1  # TestClient is sequential

    def test_file_descriptor_management(self):
        """Test proper file descriptor management and cleanup."""
        app, rt = star_app()

        file_operations = {"opened": 0, "closed": 0, "errors": []}

        class TrackingFile:
            def __init__(self, *args, **kwargs):
                file_operations["opened"] += 1
                self.closed = False

            def write(self, data):
                if self.closed:
                    raise ValueError("I/O operation on closed file")
                return len(data)

            def flush(self):
                pass

            def close(self):
                if not self.closed:
                    file_operations["closed"] += 1
                    self.closed = True

            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc_val, exc_tb):
                self.close()

        @rt("/file-ops")
        def file_operations_endpoint():
            try:
                # Simulate multiple file operations
                files_data = []

                for i in range(3):
                    with TrackingFile() as f:
                        data = f"test data {i}"
                        f.write(data.encode())
                        f.flush()
                        files_data.append({"file": i, "size": len(data)})

                return {
                    "status": "success",
                    "files_processed": len(files_data),
                    "files_data": files_data,
                    "file_descriptors": {"opened": file_operations["opened"], "closed": file_operations["closed"]},
                }
            except Exception as e:
                file_operations["errors"].append(str(e))
                return JSONResponse({"error": "File operation failed", "details": str(e)}, status_code=500)

        client = TestClient(app)
        response = client.get("/file-ops")

        # Verify successful file operations
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["files_processed"] == 3

        # Verify all file descriptors were properly closed
        fd_data = data["file_descriptors"]
        assert fd_data["opened"] == 3
        assert fd_data["closed"] == 3  # All files should be closed

        # Verify no errors occurred
        assert len(file_operations["errors"]) == 0


class TestSSEErrorHandling:
    """Test error handling in Server-Sent Events."""

    def test_sse_malformed_signal_data(self):
        """Test SSE handling of malformed signal data."""
        # Test with non-serializable data
        try:
            non_serializable = {"func": lambda x: x}  # Functions aren't JSON serializable
            format_signal_event(non_serializable)
            raise AssertionError("Should have raised an error")
        except (TypeError, ValueError):
            # Expected - non-serializable data should raise error
            pass

    def test_sse_invalid_element_data(self):
        """Test SSE handling of invalid element data."""
        # Test with None element
        try:
            format_element_event(None, "#target")
            # Should handle None gracefully or raise appropriate error
        except (AttributeError, TypeError):
            # Expected behavior for invalid input
            pass


class TestExceptionPropagation:
    """Test exception propagation and recovery."""

    def test_unhandled_exception_response(self):
        """Test handling of unhandled exceptions."""
        app, rt = star_app()

        @rt("/error")
        def error_endpoint():
            raise ValueError("Intentional test error")

        client = TestClient(app, raise_server_exceptions=False)
        response = client.get("/error")

        # Starlette should return 500 for unhandled exceptions
        assert response.status_code == 500

    def test_custom_exception_handler(self):
        """Test custom exception handling."""
        app, rt = star_app()

        class CustomError(Exception):
            pass

        @app.exception_handler(CustomError)
        async def custom_error_handler(request, exc):
            return JSONResponse({"error": "Custom error occurred", "message": str(exc)}, status_code=400)

        @rt("/custom-error")
        def custom_error_endpoint():
            raise CustomError("This is a custom error")

        client = TestClient(app)
        response = client.get("/custom-error")

        assert response.status_code == 400
        assert "Custom error occurred" in response.json()["error"]

    def test_nested_exception_handling(self):
        """Test handling of nested exceptions."""
        app, rt = star_app()

        @rt("/nested-error")
        def nested_error():
            try:
                try:
                    raise ValueError("Inner error")
                except ValueError:
                    raise RuntimeError("Outer error") from ValueError("Inner error")
            except RuntimeError as e:
                return JSONResponse({"error": "Nested error", "details": str(e)}, status_code=500)

        client = TestClient(app)
        response = client.get("/nested-error")

        assert response.status_code == 500
        assert "Nested error" in response.json()["error"]


class TestGracefulDegradation:
    """Test graceful degradation patterns."""

    def test_fallback_when_service_unavailable(self):
        """Test fallback behavior when external service is unavailable."""
        app, rt = star_app()

        @rt("/with-fallback")
        def service_with_fallback():
            try:
                # Simulate external service call
                raise ConnectionError("External service down")
            except ConnectionError:
                # Provide fallback response
                return {"status": "degraded", "message": "Using cached data", "data": {"fallback": True}}

        client = TestClient(app)
        response = client.get("/with-fallback")

        assert response.status_code == 200
        assert response.json()["status"] == "degraded"
        assert response.json()["data"]["fallback"] is True

    def test_partial_functionality_on_error(self):
        """Test partial functionality when some components fail."""
        app, rt = star_app()

        @rt("/partial-features")
        def partial_features():
            results = {"core": None, "optional": None, "errors": []}

            # Core functionality (should always work)
            try:
                results["core"] = {"status": "working"}
            except Exception as e:
                results["errors"].append(f"Core failed: {e}")

            # Optional functionality (may fail)
            try:
                raise Exception("Optional feature failed")
            except Exception as e:
                results["errors"].append(f"Optional failed: {e}")
                results["optional"] = {"status": "disabled"}

            return results

        client = TestClient(app)
        response = client.get("/partial-features")

        assert response.status_code == 200
        data = response.json()
        assert data["core"]["status"] == "working"
        assert data["optional"]["status"] == "disabled"
        assert len(data["errors"]) == 1

    def test_timeout_with_partial_results(self):
        """Test returning partial results when operations timeout."""
        app, rt = star_app()

        @rt("/timeout-partial")
        def timeout_partial():
            results = {"completed": [], "timed_out": [], "total_time": 0}
            start_time = time.time()
            timeout = 0.05  # 50ms timeout

            for i in range(5):
                time.time()

                # Simulate variable task duration
                task_duration = 0.02 if i < 3 else 0.1  # First 3 are quick, last 2 are slow

                if time.time() - start_time + task_duration > timeout:
                    results["timed_out"].append(f"task_{i}")
                    break

                time.sleep(task_duration)
                results["completed"].append(f"task_{i}")

            results["total_time"] = time.time() - start_time
            return results

        client = TestClient(app)
        response = client.get("/timeout-partial")

        assert response.status_code == 200
        data = response.json()
        assert len(data["completed"]) >= 1  # At least some tasks completed
        assert data["total_time"] < 0.1  # Should have stopped before completing all


class TestErrorBoundaries:
    """Test error boundary patterns."""

    def test_isolated_component_failure(self):
        """Test that component failures don't affect other components."""
        app, rt = star_app()

        def safe_component(name, should_fail=False):
            try:
                if should_fail:
                    raise Exception(f"Component {name} failed")
                return Div(f"Component {name} working", id=f"component-{name}")
            except Exception as e:
                return Div(f"Component {name} error: {str(e)}", id=f"component-{name}-error")

        @rt("/components")
        def components_page():
            return Div(
                H1("Multi-Component Page"),
                safe_component("A", should_fail=False),
                safe_component("B", should_fail=True),  # This one fails
                safe_component("C", should_fail=False),
            )

        client = TestClient(app)
        response = client.get("/components")

        assert response.status_code == 200
        html = response.text
        assert "Component A working" in html
        assert "Component B error" in html
        assert "Component C working" in html

    def test_error_isolation_in_sse(self):
        """Test error isolation in SSE streams."""
        app, rt = star_app()

        @rt("/isolated-events")
        @sse
        def isolated_events(req):
            # Event 1: Success
            yield signals(event=1, status="success")

            # Event 2: Failure (but shouldn't break stream)
            try:
                raise Exception("Event 2 failed")
            except Exception as e:
                yield signals(event=2, status="error", error=str(e))

            # Event 3: Success (should still work)
            yield signals(event=3, status="success")

        client = TestClient(app)

        with client.stream("GET", "/isolated-events") as response:
            assert response.status_code == 200
            content = response.read().decode("utf-8")

            # All events should be present
            assert '"event": 1' in content
            assert '"event": 2' in content
            assert '"event": 3' in content
            assert "Event 2 failed" in content


class TestRobustnessScenarios:
    """Test robustness in various edge case scenarios."""

    def test_unicode_error_messages(self):
        """Test handling of Unicode in error messages."""
        app, rt = star_app()

        @rt("/unicode-error")
        def unicode_error():
            try:
                raise ValueError("Erreur avec caractères spéciaux: café 🚀")
            except ValueError as e:
                return JSONResponse({"error": str(e)}, status_code=400)

        client = TestClient(app)
        response = client.get("/unicode-error")

        assert response.status_code == 400
        error_msg = response.json()["error"]
        assert "café" in error_msg
        assert "🚀" in error_msg or "\\u" in error_msg

    def test_deeply_nested_error_context(self):
        """Test error handling with deeply nested context."""
        app, rt = star_app()

        def level_3():
            raise Exception("Deep error")

        def level_2():
            return level_3()

        def level_1():
            return level_2()

        @rt("/deep-error")
        def deep_error():
            try:
                return level_1()
            except Exception as e:
                import traceback

                return JSONResponse(
                    {
                        "error": str(e),
                        "traceback": traceback.format_exc().split("\n")[:5],  # Limited traceback
                    },
                    status_code=500,
                )

        client = TestClient(app)
        response = client.get("/deep-error")

        assert response.status_code == 500
        assert "Deep error" in response.json()["error"]
        assert len(response.json()["traceback"]) <= 5

    def test_resource_cleanup_on_error(self):
        """Test that resources are properly cleaned up on errors."""
        app, rt = star_app()

        resource_counter = {"active": 0}

        class ManagedResource:
            def __enter__(self):
                resource_counter["active"] += 1
                return self

            def __exit__(self, exc_type, exc_val, exc_tb):
                resource_counter["active"] -= 1

        @rt("/resource-error")
        def resource_error():
            try:
                with ManagedResource():
                    if True:  # Simulate error condition
                        raise Exception("Resource operation failed")
                    return {"status": "success"}
            except Exception as e:
                return JSONResponse(
                    {"error": str(e), "resources_cleaned": resource_counter["active"] == 0}, status_code=500
                )

        client = TestClient(app)
        response = client.get("/resource-error")

        assert response.status_code == 500
        assert response.json()["resources_cleaned"] is True
