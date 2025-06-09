"""Test async SSE functionality"""

import pytest
import asyncio
from starhtml import star_app, Div, P
from starhtml.datastar import sse, signals, fragments
from starlette.testclient import TestClient
import time


def test_sync_sse_handler():
    """Test that sync SSE handlers still work"""
    app, rt = star_app()

    @rt("/sync-test")
    @sse
    def sync_handler(req):
        yield signals(status="Starting")
        time.sleep(0.1)  # Simulate work
        yield fragments(Div("Done", id="result"))
        yield signals(status="Complete")

    client = TestClient(app)

    with client.stream("GET", "/sync-test") as response:
        assert response.status_code == 200
        assert response.headers["content-type"] == "text/event-stream"

        content = b""
        for chunk in response.iter_bytes():
            content += chunk

        text = content.decode("utf-8")
        assert "event: datastar-merge-signals" in text
        assert "event: datastar-merge-fragments" in text
        assert '"status": "Starting"' in text
        assert '"status": "Complete"' in text


def test_async_sse_handler():
    """Test that async SSE handlers work correctly"""
    app, rt = star_app()

    @rt("/async-test")
    @sse
    async def async_handler(req):
        yield signals(status="Starting async")
        await asyncio.sleep(0.1)  # Simulate async work
        yield fragments(Div("Async done", id="result"))
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
        assert "event: datastar-merge-signals" in text
        assert "event: datastar-merge-fragments" in text
        assert '"status": "Starting async"' in text
        assert '"status": "Async complete"' in text
        assert "Async done" in text


def test_async_with_concurrent_operations():
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

        yield fragments(Div(P(f"Result 1: {results[0]}"), P(f"Result 2: {results[1]}"), id="results"))

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


def test_mixed_sync_async_handlers():
    """Test that both sync and async handlers can coexist"""
    app, rt = star_app()

    @rt("/sync")
    @sse
    def sync_handler(req):
        yield signals(type="sync")
        yield fragments(Div("Sync", id="sync"))

    @rt("/async")
    @sse
    async def async_handler(req):
        yield signals(type="async")
        await asyncio.sleep(0.01)
        yield fragments(Div("Async", id="async"))

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


def test_async_error_handling():
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
            yield fragments(Div(P("An error occurred", cls="error"), id="error"))

    client = TestClient(app)

    with client.stream("GET", "/async-error") as response:
        assert response.status_code == 200
        content = response.read().decode("utf-8")
        assert '"error": "Test error"' in content
        assert "An error occurred" in content


def test_async_with_auto_selector():
    """Test that auto-selector detection works with async handlers"""
    app, rt = star_app()

    @rt("/async-auto-selector")
    @sse
    async def async_auto_selector(req):
        yield signals(status="Testing auto-selector")
        await asyncio.sleep(0.01)

        # Should auto-detect #my-target selector
        yield fragments(Div("Auto-detected", id="my-target"))

    client = TestClient(app)

    with client.stream("GET", "/async-auto-selector") as response:
        content = response.read().decode("utf-8")
        assert "data: selector #my-target" in content
