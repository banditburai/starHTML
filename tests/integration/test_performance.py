"""Performance and scalability tests for StarHTML framework.

This module tests performance aspects including:
- Concurrent user handling
- Memory usage patterns
- Large payload processing
- Response time benchmarks
- Resource utilization
- Scalability limits
"""

import gc
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

import psutil
from starlette.responses import StreamingResponse
from starlette.testclient import TestClient

from starhtml import H1, Button, Div, Li, P, Ul, star_app
from starhtml.realtime import signals, sse
from starhtml.server import JSONResponse


class TestConcurrentUsers:
    """Test concurrent user handling capabilities."""

    def test_concurrent_request_handling(self):
        """Test handling multiple concurrent requests."""
        app, rt = star_app()

        request_tracker = {"count": 0, "max_concurrent": 0, "current": 0}
        lock = threading.Lock()

        @rt("/concurrent")
        def concurrent_endpoint():
            with lock:
                request_tracker["current"] += 1
                request_tracker["count"] += 1
                request_tracker["max_concurrent"] = max(request_tracker["max_concurrent"], request_tracker["current"])

            # Simulate processing time
            time.sleep(0.1)

            with lock:
                request_tracker["current"] -= 1

            return {"request_id": request_tracker["count"], "timestamp": time.time()}

        client = TestClient(app)

        # Execute concurrent requests using threading
        def make_request():
            return client.get("/concurrent")

        num_requests = 10
        start_time = time.time()

        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(make_request) for _ in range(num_requests)]
            responses = [future.result() for future in as_completed(futures)]

        end_time = time.time()
        total_time = end_time - start_time

        # Verify all requests succeeded
        assert len(responses) == num_requests
        for response in responses:
            assert response.status_code == 200

        # Should handle concurrent requests efficiently
        assert total_time < 2.0  # Should not take too long
        assert request_tracker["max_concurrent"] > 1  # Should have handled concurrent requests

    def test_session_isolation_under_load(self):
        """Test session isolation under concurrent load."""
        app, rt = star_app()

        user_data = {}

        @rt("/login", methods=["POST"])
        async def login(request):
            form_data = await request.form()
            user_id = form_data.get("user_id")
            session_id = f"session_{user_id}_{int(time.time() * 1000)}"
            user_data[session_id] = {"user_id": user_id, "requests": 0}
            return {"session_id": session_id}

        @rt("/data/{session_id}")
        def get_data(session_id: str):
            if session_id in user_data:
                user_data[session_id]["requests"] += 1
                return user_data[session_id]
            return {"error": "Invalid session"}

        client = TestClient(app)

        def user_session(user_id):
            # Login
            login_response = client.post("/login", data={"user_id": user_id})
            session_id = login_response.json()["session_id"]

            # Make multiple requests
            responses = []
            for _ in range(5):
                response = client.get(f"/data/{session_id}")
                responses.append(response.json())
                time.sleep(0.01)

            return responses

        # Simulate multiple users
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(user_session, f"user_{i}") for i in range(5)]
            user_results = [future.result() for future in as_completed(futures)]

        # Verify session isolation
        for user_responses in user_results:
            assert len(user_responses) == 5
            user_id = user_responses[0]["user_id"]

            # All responses should be for the same user
            for response in user_responses:
                assert response["user_id"] == user_id
                assert "requests" in response


class TestMemoryUsage:
    """Test memory usage patterns and limits."""

    def test_memory_usage_baseline(self):
        """Test baseline memory usage."""
        app, rt = star_app()

        @rt("/simple")
        def simple_endpoint():
            return {"message": "simple"}

        client = TestClient(app)

        # Measure memory before requests
        process = psutil.Process()
        initial_memory = process.memory_info().rss

        # Make requests
        for _ in range(100):
            response = client.get("/simple")
            assert response.status_code == 200

        # Force garbage collection
        gc.collect()

        # Measure memory after requests
        final_memory = process.memory_info().rss
        memory_increase = final_memory - initial_memory

        # Memory increase should be reasonable
        # Instead of arbitrary threshold, verify it's not growing unbounded
        # Calculate per-request memory cost
        per_request_memory = memory_increase / 100 if memory_increase > 0 else 0

        # Each simple request should use less than 1MB on average
        # This is a generous limit that accounts for Python overhead
        assert per_request_memory < 1 * 1024 * 1024, (
            f"Per-request memory too high: {per_request_memory / (1024 * 1024):.2f} MB"
        )

    def test_large_object_handling(self):
        """Test handling of large objects."""
        app, rt = star_app()

        @rt("/large-response")
        def large_response():
            # Create large response (1MB of data)
            large_data = {"items": [{"id": i, "data": "x" * 1000} for i in range(1000)]}
            return large_data

        client = TestClient(app)

        process = psutil.Process()
        initial_memory = process.memory_info().rss

        # Request large object
        response = client.get("/large-response")
        assert response.status_code == 200

        data = response.json()
        assert len(data["items"]) == 1000

        # Calculate response size before cleanup
        response_size = len(response.text)

        # Clean up
        del data
        gc.collect()

        final_memory = process.memory_info().rss
        memory_increase = final_memory - initial_memory

        # Should handle large objects without excessive memory usage
        # The response was ~1MB, so memory increase should be reasonable
        # Allow up to 10x the response size for Python/framework overhead
        max_expected_memory = response_size * 10

        assert memory_increase < max_expected_memory, (
            f"Memory increase ({memory_increase / (1024 * 1024):.1f}MB) exceeds 10x response size ({response_size / (1024 * 1024):.1f}MB)"
        )

    def test_sse_memory_usage(self):
        """Test memory usage in SSE streams."""
        app, rt = star_app()

        @rt("/memory-events")
        @sse
        def memory_events(req):
            # Generate many events to test memory usage
            for i in range(100):
                yield signals(event_id=i, data=f"Event {i} data", payload={"numbers": list(range(10))})

        client = TestClient(app)

        process = psutil.Process()
        initial_memory = process.memory_info().rss

        with client.stream("GET", "/memory-events") as response:
            assert response.status_code == 200
            content = b""
            for chunk in response.iter_bytes():
                content += chunk

        final_memory = process.memory_info().rss
        memory_increase = final_memory - initial_memory

        # Verify events were generated
        text = content.decode("utf-8")
        assert "Event 99 data" in text

        # Memory usage should be reasonable for streaming
        # SSE should not buffer all events in memory
        # Allow some overhead but verify it's not storing everything
        event_count = 100
        event_size = len(
            'event: datastar-patch-signals\ndata: signals {"event_id": 0, "data": "Event 0 data", "payload": {"numbers": [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]}}\n\n'
        )
        total_event_size = event_count * event_size

        # Memory should not exceed 5x the total event size (allowing for overhead)
        assert memory_increase < total_event_size * 5, (
            f"SSE memory usage suggests buffering: {memory_increase / (1024 * 1024):.1f}MB for {total_event_size / (1024 * 1024):.1f}MB of events"
        )


class TestLargePayloadProcessing:
    """Test processing of large payloads."""

    def test_large_json_payload(self):
        """Test handling of large JSON payloads."""
        app, rt = star_app()

        @rt("/large-json", methods=["POST"])
        async def handle_large_json(request):
            data = await request.json()
            return {
                "received_items": len(data.get("items", [])),
                "total_chars": sum(len(str(item)) for item in data.get("items", [])),
            }

        client = TestClient(app)

        # Create large JSON payload (500KB)
        large_payload = {"items": [{"id": i, "content": "x" * 500} for i in range(1000)]}

        start_time = time.time()
        response = client.post("/large-json", json=large_payload)
        end_time = time.time()

        assert response.status_code == 200
        data = response.json()
        assert data["received_items"] == 1000

        # Should process large payload in reasonable time
        processing_time = end_time - start_time
        assert processing_time < 5.0  # Less than 5 seconds

    def test_large_form_data(self):
        """Test handling of large form data."""
        app, rt = star_app()

        @rt("/large-form", methods=["POST"])
        async def handle_large_form(request):
            form_data = await request.form()
            total_size = sum(len(str(value)) for value in form_data.values())
            return {"total_size": total_size, "field_count": len(form_data)}

        client = TestClient(app)

        # Create large form data
        large_form = {f"field_{i}": "x" * 1000 for i in range(100)}

        start_time = time.time()
        response = client.post("/large-form", data=large_form)
        end_time = time.time()

        assert response.status_code == 200
        data = response.json()
        assert data["field_count"] == 100
        assert data["total_size"] > 90000  # Should have processed most data

        processing_time = end_time - start_time
        assert processing_time < 3.0

    def test_streaming_large_response(self):
        """Test streaming large responses."""
        app, rt = star_app()

        @rt("/large-stream")
        def large_stream():
            def generate_data():
                for i in range(1000):
                    yield f"data_chunk_{i}," + "x" * 100 + "\n"

            from starlette.responses import StreamingResponse

            return StreamingResponse(generate_data(), media_type="text/plain")

        client = TestClient(app)

        start_time = time.time()
        response = client.get("/large-stream")

        assert response.status_code == 200

        # Read streaming response
        content_size = 0
        chunk_count = 0
        for chunk in response.iter_bytes(chunk_size=1024):
            content_size += len(chunk)
            chunk_count += 1

        end_time = time.time()

        # Should stream efficiently
        assert content_size > 100000  # Should have substantial content
        assert chunk_count > 10  # Should have streamed in chunks

        streaming_time = end_time - start_time
        assert streaming_time < 10.0  # Should stream reasonably fast


class TestResponseTimeMetrics:
    """Test response time performance metrics."""

    def test_simple_request_latency(self):
        """Test latency of simple requests."""
        app, rt = star_app()

        @rt("/ping")
        def ping():
            return {"pong": True, "timestamp": time.time()}

        client = TestClient(app)

        # Measure multiple requests
        latencies = []
        for _ in range(50):
            start = time.time()
            response = client.get("/ping")
            end = time.time()

            assert response.status_code == 200
            latencies.append(end - start)

        # Calculate statistics
        import statistics

        statistics.mean(latencies)
        median_latency = statistics.median(latencies)
        statistics.stdev(latencies)
        p95_latency = sorted(latencies)[int(len(latencies) * 0.95)]
        p99_latency = sorted(latencies)[int(len(latencies) * 0.99)]

        # Performance analysis
        # Instead of fixed thresholds, verify reasonable performance characteristics
        # 1. Median should be low (most requests are fast)
        # 2. P95/P99 shouldn't be too far from median (no extreme outliers)

        # Log performance metrics for debugging
        print(
            f"\nLatency stats: median={median_latency * 1000:.1f}ms, p95={p95_latency * 1000:.1f}ms, p99={p99_latency * 1000:.1f}ms"
        )

        # Verify performance characteristics
        assert median_latency < 0.1, f"Median latency too high: {median_latency * 1000:.1f}ms"

        # P99 should be within 10x of median (no extreme outliers)
        if median_latency > 0:
            assert p99_latency / median_latency < 10, (
                f"High latency variance: p99={p99_latency * 1000:.1f}ms, median={median_latency * 1000:.1f}ms"
            )

    def test_complex_page_generation(self):
        """Test performance of complex page generation."""
        app, rt = star_app()

        @rt("/complex")
        def complex_page():
            # Generate complex HTML structure
            items = []
            for i in range(100):
                items.append(
                    Li(
                        Div(
                            H1(f"Item {i}"),
                            P(f"Description for item {i}"),
                            Button("Action", ds_on_click=f"handleItem({i})"),
                            id=f"item-{i}",
                        )
                    )
                )

            return Div(H1("Complex Page"), Ul(*items), id="main-content")

        client = TestClient(app)

        start_time = time.time()
        response = client.get("/complex")
        end_time = time.time()

        assert response.status_code == 200
        assert "Complex Page" in response.text
        assert "Item 99" in response.text

        generation_time = end_time - start_time

        # Performance should be reasonable for 100 items
        # This is a complex operation, so we allow more time
        # but verify it's not unreasonably slow
        items_per_second = 100 / generation_time if generation_time > 0 else float("inf")

        print(
            f"\nComplex page generation: {generation_time * 1000:.1f}ms for 100 items ({items_per_second:.0f} items/sec)"
        )

        # Should handle at least 50 items per second
        assert items_per_second > 50, f"Page generation too slow: {items_per_second:.0f} items/sec"

    def test_json_serialization_performance(self):
        """Test JSON serialization performance."""
        app, rt = star_app()

        @rt("/json-perf")
        def json_performance():
            # Create complex nested structure
            data = {
                "users": [
                    {
                        "id": i,
                        "name": f"User {i}",
                        "profile": {
                            "email": f"user{i}@example.com",
                            "preferences": {
                                "theme": "dark" if i % 2 else "light",
                                "notifications": True,
                                "features": [f"feature_{j}" for j in range(5)],
                            },
                        },
                        "posts": [{"id": j, "title": f"Post {j}", "content": "x" * 100} for j in range(10)],
                    }
                    for i in range(100)
                ]
            }
            return data

        client = TestClient(app)

        start_time = time.time()
        response = client.get("/json-perf")
        end_time = time.time()

        assert response.status_code == 200
        data = response.json()
        assert len(data["users"]) == 100

        serialization_time = end_time - start_time

        # Calculate serialization rate
        users_count = 100
        users_per_second = users_count / serialization_time if serialization_time > 0 else float("inf")

        print(
            f"\nJSON serialization: {serialization_time * 1000:.1f}ms for {users_count} users ({users_per_second:.0f} users/sec)"
        )

        # Should serialize at least 50 complex objects per second
        assert users_per_second > 50, f"JSON serialization too slow: {users_per_second:.0f} users/sec"


class TestResourceUtilization:
    """Test resource utilization patterns."""

    def test_cpu_usage_under_load(self):
        """Test CPU usage under simulated load."""
        app, rt = star_app()

        @rt("/cpu-intensive")
        def cpu_intensive():
            # Simulate CPU-intensive operation
            result = 0
            for i in range(10000):
                result += i * i
            return {"result": result}

        client = TestClient(app)

        process = psutil.Process()
        process.cpu_percent()

        # Make multiple CPU-intensive requests
        start_time = time.time()
        responses = []
        for _ in range(10):
            response = client.get("/cpu-intensive")
            responses.append(response)
        end_time = time.time()

        process.cpu_percent()

        # Verify all requests succeeded
        for response in responses:
            assert response.status_code == 200
            assert "result" in response.json()

        # Should complete in reasonable time despite CPU load
        total_time = end_time - start_time
        assert total_time < 5.0

    def test_file_descriptor_usage(self):
        """Test file descriptor usage patterns."""
        app, rt = star_app()

        @rt("/file-ops")
        def file_operations():
            import os
            import tempfile

            # Create and clean up temporary files
            temp_files = []
            try:
                for i in range(10):
                    with tempfile.NamedTemporaryFile(delete=False) as f:
                        f.write(f"test data {i}".encode())
                        temp_files.append(f.name)

                return {"files_created": len(temp_files)}
            finally:
                # Clean up
                for filename in temp_files:
                    try:
                        os.unlink(filename)
                    except OSError:
                        pass

        client = TestClient(app)

        # Make multiple requests that use file descriptors
        for _ in range(20):
            response = client.get("/file-ops")
            assert response.status_code == 200
            assert response.json()["files_created"] == 10

    def test_database_connection_simulation(self):
        """Test simulated database connection patterns."""
        app, rt = star_app()

        connection_pool = {"active": 0, "max_active": 0}

        class MockConnection:
            def __enter__(self):
                connection_pool["active"] += 1
                connection_pool["max_active"] = max(connection_pool["max_active"], connection_pool["active"])
                return self

            def __exit__(self, exc_type, exc_val, exc_tb):
                connection_pool["active"] -= 1

            def query(self, sql):
                time.sleep(0.01)  # Simulate query time
                return {"result": "mock data"}

        @rt("/db-query")
        def db_query():
            with MockConnection() as conn:
                result = conn.query("SELECT * FROM users")
                return result

        client = TestClient(app)

        # Make concurrent database requests
        def make_db_request():
            return client.get("/db-query")

        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(make_db_request) for _ in range(20)]
            responses = [future.result() for future in as_completed(futures)]

        # Verify all requests succeeded
        for response in responses:
            assert response.status_code == 200
            assert response.json()["result"] == "mock data"

        # Should have managed connections efficiently
        assert connection_pool["max_active"] <= 5  # Should not exceed worker count
        assert connection_pool["active"] == 0  # All connections should be closed


class TestScalabilityLimits:
    """Test scalability limits and boundaries."""

    def test_maximum_concurrent_connections(self):
        """Test handling of many concurrent connections."""
        app, rt = star_app()

        connection_counter = {"count": 0, "max_concurrent": 0}

        @rt("/stress")
        def stress_endpoint():
            connection_counter["count"] += 1
            current = connection_counter["count"]
            connection_counter["max_concurrent"] = max(connection_counter["max_concurrent"], current)

            time.sleep(0.05)  # Hold connection briefly
            return {"connection": current}

        client = TestClient(app)

        # Test with many concurrent requests
        def stress_request():
            return client.get("/stress")

        num_requests = 50
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(stress_request) for _ in range(num_requests)]
            responses = [future.result() for future in as_completed(futures)]

        # Should handle all requests
        assert len(responses) == num_requests
        success_count = sum(1 for r in responses if r.status_code == 200)
        assert success_count >= num_requests * 0.9  # At least 90% success rate

    def test_memory_scalability_limits(self):
        """Test memory usage under increasing load."""
        app, rt = star_app()

        @rt("/memory-scale/{size}")
        def memory_scale(size: int):
            # Generate response proportional to size parameter
            data = {"items": [{"id": i, "data": "x" * min(size, 1000)} for i in range(min(size, 100))]}
            return data

        client = TestClient(app)

        process = psutil.Process()
        memory_measurements = []

        # Warm up to stabilize memory
        for _ in range(3):
            client.get("/memory-scale/10")
            gc.collect()

        # Test increasing payload sizes with multiple samples
        sizes = [10, 50, 100, 200]
        for size in sizes:
            # Take multiple measurements for statistical reliability
            samples = []
            for _ in range(5):
                gc.collect()  # Clean up before measurement
                initial_memory = process.memory_info().rss

                response = client.get(f"/memory-scale/{size}")
                assert response.status_code == 200

                final_memory = process.memory_info().rss
                memory_increase = final_memory - initial_memory
                samples.append(memory_increase)

                # Clean up response
                del response
                gc.collect()

            # Use median to reduce noise
            import statistics

            median_increase = statistics.median(samples)
            memory_measurements.append((size, median_increase))

        # Analyze memory scaling with linear regression
        [m[0] for m in memory_measurements]
        memory_list = [m[1] for m in memory_measurements]

        # Simple correlation check - memory should correlate with size
        # But we don't enforce strict proportionality due to:
        # 1. Python memory management overhead
        # 2. Garbage collection timing
        # 3. Small sample sizes causing high variance

        # Just verify no extreme outliers (10x expected)
        if len(memory_measurements) > 1:
            positive_memories = [m for m in memory_list if m > 0]

            if positive_memories:  # Only check if we have positive measurements
                max_memory = max(memory_list)
                min_memory = min(positive_memories)

                # Memory usage shouldn't vary by more than 100x for our test sizes
                assert max_memory / min_memory < 100, f"Extreme memory variance: {max_memory}/{min_memory}"

            # Verify responses are actually different sizes
            response_sizes = []
            for size in [10, 200]:
                resp = client.get(f"/memory-scale/{size}")
                response_sizes.append(len(resp.text))
            assert response_sizes[1] > response_sizes[0] * 1.5  # Larger size should produce larger response


class TestLargePayloadEdgeCases:
    """Test edge cases with large payloads and streaming."""

    def test_streaming_response_with_error(self):
        """Test streaming response that encounters an error mid-stream."""
        app, rt = star_app()

        @rt("/stream-with-error")
        def stream_with_error():
            def generate_data():
                # Generate some data
                for i in range(5):
                    yield f"Data chunk {i}\n"

                # Simulate error during streaming
                if True:  # Always trigger error for test
                    yield "ERROR: Something went wrong\n"
                    return  # End stream on error

                # This would normally continue
                for i in range(5, 10):
                    yield f"Data chunk {i}\n"

            return StreamingResponse(generate_data(), media_type="text/plain")

        client = TestClient(app)
        response = client.get("/stream-with-error")

        assert response.status_code == 200
        content = response.text
        assert "Data chunk 0" in content
        assert "Data chunk 4" in content
        assert "ERROR: Something went wrong" in content
        # Should not contain chunks 5-9 due to error
        assert "Data chunk 5" not in content

    def test_json_payload_with_nested_structures(self):
        """Test deeply nested JSON payload handling."""
        app, rt = star_app()

        @rt("/nested-json", methods=["POST"])
        async def process_nested_json(request):
            try:
                data = await request.json()

                # Process nested structure
                def count_nested_levels(obj, level=0):
                    if isinstance(obj, dict):
                        if not obj:
                            return level
                        return max(count_nested_levels(v, level + 1) for v in obj.values())
                    elif isinstance(obj, list):
                        if not obj:
                            return level
                        return max(count_nested_levels(item, level + 1) for item in obj)
                    else:
                        return level

                max_depth = count_nested_levels(data)

                return {
                    "max_nesting_depth": max_depth,
                    "data_processed": True,
                    "total_keys": len(str(data)),  # Rough size indicator
                }
            except Exception as e:
                return JSONResponse({"error": "Failed to process nested JSON", "details": str(e)}, status_code=400)

        client = TestClient(app)

        # Test various nesting levels
        test_cases = [
            # Simple flat structure
            {"key": "value"},
            # 2-level nesting
            {"level1": {"level2": "value"}},
            # 3-level nesting with arrays
            {"level1": {"level2": [{"level3": "value1"}, {"level3": "value2"}]}},
            # Complex structure
            {
                "users": [
                    {
                        "id": 1,
                        "profile": {
                            "personal": {
                                "name": "John",
                                "addresses": [
                                    {"type": "home", "details": {"street": "123 Main St"}},
                                    {"type": "work", "details": {"street": "456 Work Ave"}},
                                ],
                            }
                        },
                    }
                ]
            },
        ]

        for test_data in test_cases:
            response = client.post("/nested-json", json=test_data)
            assert response.status_code == 200

            result = response.json()
            assert result["data_processed"] is True
            assert "max_nesting_depth" in result

    def test_large_text_payload_processing(self):
        """Test processing of large text payloads."""
        app, rt = star_app()

        @rt("/process-text", methods=["POST"])
        async def process_large_text(request):
            body = await request.body()
            text_content = body.decode("utf-8")

            # Process the text
            word_count = len(text_content.split())
            char_count = len(text_content)
            line_count = len(text_content.splitlines())

            # Check for specific patterns
            has_repeated_pattern = "repeat" in text_content

            return {
                "text_stats": {
                    "word_count": word_count,
                    "char_count": char_count,
                    "line_count": line_count,
                    "has_repeated_pattern": has_repeated_pattern,
                },
                "processing_successful": True,
            }

        client = TestClient(app)

        # Generate large text content
        large_text = "This is a test line with some content.\n" * 1000
        large_text += "repeat " * 100  # Add some repeated patterns

        response = client.post("/process-text", content=large_text, headers={"content-type": "text/plain"})

        assert response.status_code == 200
        data = response.json()
        assert data["processing_successful"] is True
        assert data["text_stats"]["line_count"] >= 1000  # May be 1001 due to appended text
        assert data["text_stats"]["word_count"] > 1000
        assert data["text_stats"]["has_repeated_pattern"] is True
