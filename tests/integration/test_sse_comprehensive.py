"""Comprehensive tests for SSE (Server-Sent Events) functionality in StarHTML.

This module consolidates SSE-related tests from multiple files:
- SSE format compliance with Datastar specification
- Real-time functionality tests
- Async SSE handler tests
- Helper functions and utilities
- Error handling and edge cases
"""

import asyncio
import time

from starlette.testclient import TestClient

from starhtml import H1, Div, P, star_app
from starhtml.realtime import (
    SSE_HEADERS,
    elements,
    format_element_event,
    format_signal_event,
    signals,
    sse,
)


class TestSSEFormatCompliance:
    """Test SSE format compliance with Datastar specification."""

    def test_signal_sse_format(self):
        """Test that signal SSE events use correct v1 RC format."""
        signals_data = {"status": "test", "count": 42}
        output = format_signal_event(signals_data)

        expected_lines = [
            "event: datastar-patch-signals",
            'data: signals {"status": "test", "count": 42}',
            "",
            "",
        ]
        expected = "\n".join(expected_lines)

        assert output == expected

    def test_fragment_sse_format(self):
        """Test that fragment SSE events use correct v1 RC format."""
        html = "<div>Test content</div>"
        output = format_element_event(html, "#target", "outer")

        expected_lines = [
            "event: datastar-patch-elements",
            "data: selector #target",
            "data: elements &lt;div&gt;Test content&lt;/div&gt;",
            "",
            "",
        ]
        expected = "\n".join(expected_lines)

        assert output == expected

    def test_fragment_sse_format_no_selector(self):
        """Test fragment SSE format when no selector provided."""
        html = "<p>No selector</p>"
        output = format_element_event(html, mode="append")

        expected_lines = [
            "event: datastar-patch-elements",
            "data: mode append",
            "data: elements &lt;p&gt;No selector&lt;/p&gt;",
            "",
            "",
        ]
        expected = "\n".join(expected_lines)

        assert output == expected

    def test_multiple_elements_format(self):
        """Test handling multiple elements in SSE format."""
        # Join elements as a single string
        elements_html = "<div>First</div><div>Second</div>"
        output = format_element_event(elements_html, "#target", "append")

        expected_lines = [
            "event: datastar-patch-elements",
            "data: mode append",
            "data: selector #target",
            "data: elements &lt;div&gt;First&lt;/div&gt;&lt;div&gt;Second&lt;/div&gt;",
            "",
            "",
        ]
        expected = "\n".join(expected_lines)

        assert output == expected

    def test_complex_signals_format(self):
        """Test complex signal data types in SSE format."""
        signals_data = {"user": {"name": "John", "age": 30}, "items": [1, 2, 3], "active": True, "count": 0}
        output = format_signal_event(signals_data)

        # Should contain the event type and data prefix
        assert "event: datastar-patch-signals" in output
        assert "data: signals " in output
        assert '"user": {"name": "John", "age": 30}' in output
        assert '"items": [1, 2, 3]' in output
        assert '"active": true' in output


class TestSSEConstants:
    """Test SSE constants and headers."""

    def test_sse_headers(self):
        """Test SSE_HEADERS constant."""
        required_headers = {
            "Content-Type": "text/event-stream",
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }

        for key, value in required_headers.items():
            assert key in SSE_HEADERS
            assert SSE_HEADERS[key] == value


class TestRealTimeDataFlow:
    """Test the real-time data flow patterns."""

    def test_signal_to_sse_conversion(self):
        """Test converting signals to SSE format."""
        # Create signal data
        signal_data = signals(progress=75, status="loading")

        # Convert to SSE format
        sse_output = format_signal_event(signal_data[1]["payload"])

        # Verify SSE format
        assert "event: datastar-patch-signals" in sse_output
        assert "75" in sse_output
        assert "loading" in sse_output

    def test_element_to_sse_conversion(self):
        """Test converting elements to SSE format."""
        # Create element data
        element_data = elements(Div(H1("Progress"), P("75% complete")), "#progress-container", "inner")

        # Convert to SSE format
        sse_output = format_element_event(
            element_data[1][0],  # content
            element_data[1][1],  # selector
            element_data[1][2],  # mode
        )

        # Verify SSE format
        assert "event: datastar-patch-elements" in sse_output
        assert "data: selector #progress-container" in sse_output
        assert "data: mode inner" in sse_output
        assert "Progress" in sse_output
        assert "75% complete" in sse_output

    def test_mixed_updates_pattern(self):
        """Test pattern of mixing signals and elements creates coherent SSE stream."""
        # Simulate a real-time update sequence
        updates = []

        # Step 1: Update signal
        updates.append(signals(step=1, message="Starting"))

        # Step 2: Update UI element
        updates.append(elements(Div("Step 1 complete"), "#status", "append"))

        # Step 3: Final signal update
        updates.append(signals(step=2, message="Complete"))

        # Test that all updates can be converted to a coherent SSE stream
        sse_stream = []
        for update in updates:
            if update[0] == "signals":
                sse_stream.append(format_signal_event(update[1]["payload"]))
            elif update[0] == "elements":
                sse_stream.append(format_element_event(update[1][0], update[1][1], update[1][2]))

        # Verify the stream tells a coherent story
        full_stream = "\n".join(sse_stream)
        assert "Starting" in full_stream
        assert "Step 1 complete" in full_stream
        assert "Complete" in full_stream
        assert full_stream.count("event: datastar-patch-signals") == 2
        assert full_stream.count("event: datastar-patch-elements") == 1


class TestAsyncSSEHandlers:
    """Test async SSE handler functionality."""

    def test_sync_sse_handler(self):
        """Test that sync SSE handlers still work"""
        app, rt = star_app()

        @rt("/sync-test")
        @sse
        def sync_handler(req):
            yield signals(status="Starting")
            time.sleep(0.1)  # Simulate work
            yield elements(Div("Done", id="result"))
            yield signals(status="Complete")

        client = TestClient(app)

        with client.stream("GET", "/sync-test") as response:
            assert response.status_code == 200
            assert response.headers["content-type"] == "text/event-stream"

            content = b""
            for chunk in response.iter_bytes():
                content += chunk

            text = content.decode("utf-8")
            assert "event: datastar-patch-signals" in text
            assert "event: datastar-patch-elements" in text
            assert '"status": "Starting"' in text
            assert '"status": "Complete"' in text

    def test_async_sse_handler(self):
        """Test that async SSE handlers work correctly"""
        app, rt = star_app()

        @rt("/async-test")
        @sse
        async def async_handler(req):
            yield signals(status="Starting async")
            await asyncio.sleep(0.1)  # Simulate async work
            yield elements(Div("Async done", id="result"))
            yield signals(status="Async complete")

        # TestClient handles async routes automatically
        client = TestClient(app)

        with client.stream("GET", "/async-test") as response:
            assert response.status_code == 200
            assert response.headers["content-type"] == "text/event-stream"

            content = b""
            for chunk in response.iter_bytes():
                content += chunk

            text = content.decode("utf-8")
            assert "event: datastar-patch-signals" in text
            assert "event: datastar-patch-elements" in text
            assert '"status": "Starting async"' in text
            assert '"status": "Async complete"' in text
            assert "Async done" in text

    def test_async_with_concurrent_operations(self):
        """Test async SSE with concurrent operations"""
        app, rt = star_app()

        @rt("/concurrent-test")
        @sse
        async def concurrent_handler(req):
            yield signals(status="Starting concurrent operations")

            # Simulate concurrent operations
            async def task1():
                await asyncio.sleep(0.1)
                return "Task 1 result"

            async def task2():
                await asyncio.sleep(0.1)
                return "Task 2 result"

            # Run concurrently
            results = await asyncio.gather(task1(), task2())

            yield elements(Div(P(f"Result 1: {results[0]}"), P(f"Result 2: {results[1]}"), id="results"))

            yield signals(status="All tasks complete")

        client = TestClient(app)

        start_time = time.time()
        with client.stream("GET", "/concurrent-test") as response:
            assert response.status_code == 200

            content = b""
            for chunk in response.iter_bytes():
                content += chunk

        elapsed = time.time() - start_time

        # Should complete in ~0.1s, not 0.2s (if sequential)
        assert elapsed < 0.15  # Allow some overhead

        text = content.decode("utf-8")
        assert "Task 1 result" in text
        assert "Task 2 result" in text

    def test_mixed_sync_async_handlers(self):
        """Test that both sync and async handlers can coexist"""
        app, rt = star_app()

        @rt("/sync")
        @sse
        def sync_handler(req):
            yield signals(type="sync")
            yield elements(Div("Sync", id="sync"))

        @rt("/async")
        @sse
        async def async_handler(req):
            yield signals(type="async")
            await asyncio.sleep(0.01)
            yield elements(Div("Async", id="async"))

        client = TestClient(app)

        # Test sync endpoint
        with client.stream("GET", "/sync") as response:
            assert response.status_code == 200
            content = response.read().decode("utf-8")
            assert '"type": "sync"' in content

        # Test async endpoint
        with client.stream("GET", "/async") as response:
            assert response.status_code == 200
            content = response.read().decode("utf-8")
            assert '"type": "async"' in content

    def test_async_error_handling(self):
        """Test error handling in async SSE handlers"""
        app, rt = star_app()

        @rt("/async-error")
        @sse
        async def async_error_handler(req):
            yield signals(status="Starting")

            try:
                await asyncio.sleep(0.01)
                # Simulate an error
                raise ValueError("Test error")
            except ValueError as e:
                yield signals(error=str(e), status="Error occurred")
                yield elements(Div(P("An error occurred", cls="error"), id="error"))

        client = TestClient(app)

        with client.stream("GET", "/async-error") as response:
            assert response.status_code == 200
            content = response.read().decode("utf-8")
            assert '"error": "Test error"' in content
            assert "An error occurred" in content

    def test_async_with_auto_selector(self):
        """Test that auto-selector detection works with async handlers"""
        app, rt = star_app()

        @rt("/async-auto-selector")
        @sse
        async def async_auto_selector(req):
            yield signals(status="Testing auto-selector")
            await asyncio.sleep(0.01)

            # Should auto-detect #my-target selector
            yield elements(Div("Auto-detected", id="my-target"))

        client = TestClient(app)

        with client.stream("GET", "/async-auto-selector") as response:
            content = response.read().decode("utf-8")
            assert "data: selector #my-target" in content


class TestSSEEdgeCases:
    """Test SSE edge cases and error conditions."""

    def test_special_characters_in_signals(self):
        """Test signals with special characters."""
        # Unicode characters (JSON escapes them)
        signal_data = {"message": "Hello 世界", "emoji": "🚀"}
        result = format_signal_event(signal_data)
        assert "\\u4e16\\u754c" in result  # Escaped unicode
        assert "\\ud83d\\ude80" in result  # Escaped emoji

        # HTML-like content (should be preserved in JSON)
        signal_data = {"html": "<div>test</div>", "script": "<script>alert('test')</script>"}
        result = format_signal_event(signal_data)
        # Should be properly JSON-encoded
        assert "&lt;div&gt;" not in result  # Not HTML escaped in JSON
        assert "<div>test</div>" in result

    def test_large_data_handling(self):
        """Test handling of large data structures."""
        # Large array
        large_array = list(range(1000))
        signal_data = {"large_array": large_array}
        result = format_signal_event(signal_data)
        assert "999" in result  # Should contain the last element

        # Deep nesting
        deep_object = {"level1": {"level2": {"level3": {"data": "deep"}}}}
        result = format_signal_event(deep_object)
        assert "deep" in result

    def test_empty_content_handling(self):
        """Test handling of empty content."""
        # Empty signal
        result = format_signal_event({})
        assert "event: datastar-patch-signals" in result
        assert "data: signals {}" in result

        # Empty element
        result = format_element_event("", "#target")
        assert "event: datastar-patch-elements" in result
        assert "data: selector #target" in result
        assert "data: elements" in result


class TestSSEErrorHandling:
    """Test SSE error handling and resilience scenarios."""

    def test_sse_stream_interruption(self):
        """Test SSE stream interruption handling."""
        app, rt = star_app()

        @rt("/events")
        @sse
        def event_stream(req):
            try:
                yield signals(status="starting")
                # Simulate error during stream
                raise Exception("Stream error")
            except Exception as e:
                yield signals(error=str(e), status="error")

        client = TestClient(app)

        # Test that the stream handles errors gracefully
        with client.stream("GET", "/events") as response:
            assert response.status_code == 200
            assert response.headers["content-type"] == "text/event-stream"

            content = response.iter_lines()
            events = list(content)
            assert len(events) > 0

            event_data = "\n".join(str(line, "utf-8") if isinstance(line, bytes) else line for line in events)
            assert "starting" in event_data
            assert "error" in event_data

    def test_async_sse_error_handling(self):
        """Test async SSE error handling."""
        app, rt = star_app()

        @rt("/async-events")
        @sse
        async def async_event_stream(req):
            try:
                yield signals(status="async_starting")
                await asyncio.sleep(0.01)
                # Simulate async error
                raise ValueError("Async error")
            except ValueError as e:
                yield signals(error=str(e), status="async_error")

        client = TestClient(app)

        with client.stream("GET", "/async-events") as response:
            assert response.status_code == 200

            content = response.iter_lines()
            events = list(content)
            assert len(events) > 0

            event_data = "\n".join(str(line, "utf-8") if isinstance(line, bytes) else line for line in events)
            assert "async_starting" in event_data
            assert "async_error" in event_data

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

            # Event 3: Recovery
            yield signals(event=3, status="recovered")

        client = TestClient(app)

        with client.stream("GET", "/isolated-events") as response:
            assert response.status_code == 200

            content = response.iter_lines()
            events = list(content)

            event_data = "\n".join(str(line, "utf-8") if isinstance(line, bytes) else line for line in events)
            # All three events should be present
            assert '"event": 1' in event_data
            assert '"event": 2' in event_data
            assert '"event": 3' in event_data
            assert "success" in event_data
            assert "error" in event_data
            assert "recovered" in event_data


class TestSSEPerformance:
    """Test SSE performance and scalability scenarios."""

    def test_sse_concurrent_streams(self):
        """Test SSE concurrent stream handling."""
        app, rt = star_app()

        stream_counter = {"active": 0, "max_active": 0}

        @rt("/events")
        @sse
        def event_stream(req):
            stream_counter["active"] += 1
            stream_counter["max_active"] = max(stream_counter["max_active"], stream_counter["active"])

            try:
                for i in range(3):
                    yield signals(stream_id=id(req), event=i, timestamp=time.time())
                    time.sleep(0.05)
            finally:
                stream_counter["active"] -= 1

        client = TestClient(app)

        # Test single stream
        with client.stream("GET", "/events") as response:
            assert response.status_code == 200
            content = response.iter_lines()
            events = list(content)
            assert len(events) > 0

        # Verify stream counter worked
        assert stream_counter["max_active"] >= 1
        assert stream_counter["active"] == 0  # All streams closed

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

        # Stream should handle many events without issues
        with client.stream("GET", "/memory-events") as response:
            assert response.status_code == 200

            content = response.iter_lines()
            events = list(content)

            # Should have processed all events
            assert len(events) > 100  # Each event generates multiple SSE lines

            # Check for presence of first and last events
            event_data = "\n".join(str(line, "utf-8") if isinstance(line, bytes) else line for line in events)
            assert '"event_id": 0' in event_data
            assert '"event_id": 99' in event_data

    def test_sse_stream_scalability(self):
        """Test SSE stream scalability."""
        app, rt = star_app()

        @rt("/scalable-events")
        @sse
        def scalable_events(req):
            # Generate events efficiently
            for i in range(20):
                yield signals(event=i, batch_size=20)
                if i % 5 == 0:
                    # Yield control occasionally
                    time.sleep(0.001)

        client = TestClient(app)

        start_time = time.time()
        with client.stream("GET", "/scalable-events") as response:
            assert response.status_code == 200

            content = response.iter_lines()
            events = list(content)

        elapsed = time.time() - start_time

        # Should complete quickly (under 1 second)
        assert elapsed < 1.0
        assert len(events) > 20  # Multiple lines per event

        event_data = "\n".join(str(line, "utf-8") if isinstance(line, bytes) else line for line in events)
        assert '"event": 0' in event_data
        assert '"event": 19' in event_data
