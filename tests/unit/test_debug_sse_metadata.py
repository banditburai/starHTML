"""Tests for SSE debug metadata enrichment."""

import re

from starhtml.realtime import format_signal_event, format_element_event, format_sse_event


class TestSSEDebugMetadata:
    def test_signal_event_no_debug(self):
        """Without debug context, no x-debug lines."""
        event = format_signal_event({"count": 5})
        assert "x-debug" not in event

    def test_signal_event_with_debug(self):
        """With debug context, x-debug lines are appended."""
        debug_ctx = {"handler": "update_count", "route": "/sse/counter", "seq": 1}
        event = format_signal_event({"count": 5}, debug_ctx=debug_ctx)
        assert "data: x-debug-seq 1" in event
        assert "data: x-debug-handler update_count" in event
        assert "data: x-debug-route /sse/counter" in event
        assert re.search(r"data: x-debug-ts \d+", event)

    def test_element_event_no_debug(self):
        """Without debug context, no x-debug lines."""
        event = format_element_event("<div>hello</div>")
        assert "x-debug" not in event

    def test_element_event_with_debug(self):
        """With debug context, x-debug lines are appended."""
        debug_ctx = {"handler": "render_cell", "route": "/sse/notebook", "seq": 2}
        event = format_element_event("<div>hello</div>", debug_ctx=debug_ctx)
        assert "data: x-debug-seq 2" in event
        assert "data: x-debug-handler render_cell" in event
        assert "data: x-debug-route /sse/notebook" in event
        assert re.search(r"data: x-debug-ts \d+", event)

    def test_format_sse_event_no_debug(self):
        """Base formatter without debug context."""
        event = format_sse_event("datastar-patch-signals", ["signals {\"x\":1}"])
        assert "x-debug" not in event

    def test_format_sse_event_with_debug(self):
        """Base formatter with debug context."""
        debug_ctx = {"handler": "test_handler", "route": "/test", "seq": 42}
        event = format_sse_event("datastar-patch-signals", ["signals {\"x\":1}"], debug_ctx=debug_ctx)
        assert "data: x-debug-seq 42" in event
        assert "data: x-debug-handler test_handler" in event
        assert "data: x-debug-route /test" in event
        assert re.search(r"data: x-debug-ts \d+", event)

    def test_debug_metadata_order(self):
        """Debug metadata lines come after regular data lines."""
        debug_ctx = {"handler": "h", "route": "/r", "seq": 1}
        event = format_sse_event("datastar-patch-signals", ["signals {\"x\":1}"], debug_ctx=debug_ctx)
        lines = event.strip().split("\n")
        # Find positions
        data_idx = next(i for i, l in enumerate(lines) if l.startswith("data: signals"))
        debug_idx = next(i for i, l in enumerate(lines) if l.startswith("data: x-debug"))
        assert debug_idx > data_idx, "Debug metadata should come after regular data"
