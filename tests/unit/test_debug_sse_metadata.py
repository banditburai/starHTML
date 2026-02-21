"""Tests for SSE debug metadata enrichment."""

import re

from starhtml.realtime import (
    SignalEvent,
    _debug_ctx_var,
    format_element_event,
    format_event,
    format_signal_event,
    format_sse_event,
    get_debug_context,
    process_sse_item,
    set_debug_context,
)


class TestSSEDebugMetadata:
    def test_signal_event_no_debug(self):
        event = format_signal_event({"count": 5})
        assert "x-debug" not in event

    def test_signal_event_with_debug(self):
        debug_ctx = {"handler": "update_count", "route": "/sse/counter", "seq": 1}
        event = format_signal_event({"count": 5}, debug_ctx=debug_ctx)
        assert "data: x-debug-seq 1" in event
        assert "data: x-debug-handler update_count" in event
        assert "data: x-debug-route /sse/counter" in event
        assert re.search(r"data: x-debug-ts \d+", event)

    def test_element_event_no_debug(self):
        event = format_element_event("<div>hello</div>")
        assert "x-debug" not in event

    def test_element_event_with_debug(self):
        debug_ctx = {"handler": "render_cell", "route": "/sse/notebook", "seq": 2}
        event = format_element_event("<div>hello</div>", debug_ctx=debug_ctx)
        assert "data: x-debug-seq 2" in event
        assert "data: x-debug-handler render_cell" in event
        assert "data: x-debug-route /sse/notebook" in event
        assert re.search(r"data: x-debug-ts \d+", event)

    def test_format_sse_event_no_debug(self):
        event = format_sse_event("datastar-patch-signals", ['signals {"x":1}'])
        assert "x-debug" not in event

    def test_format_sse_event_with_debug(self):
        debug_ctx = {"handler": "test_handler", "route": "/test", "seq": 42}
        event = format_sse_event("datastar-patch-signals", ['signals {"x":1}'], debug_ctx=debug_ctx)
        assert "data: x-debug-seq 42" in event
        assert "data: x-debug-handler test_handler" in event
        assert "data: x-debug-route /test" in event
        assert re.search(r"data: x-debug-ts \d+", event)

    def test_debug_metadata_order(self):
        """Debug metadata lines come after regular data lines."""
        debug_ctx = {"handler": "h", "route": "/r", "seq": 1}
        event = format_sse_event("datastar-patch-signals", ['signals {"x":1}'], debug_ctx=debug_ctx)
        lines = event.strip().split("\n")
        data_idx = next(i for i, line in enumerate(lines) if line.startswith("data: signals"))
        debug_idx = next(i for i, line in enumerate(lines) if line.startswith("data: x-debug"))
        assert debug_idx > data_idx

    def test_element_event_multiline_with_debug(self):
        """Debug metadata comes after all element data lines in multiline HTML."""
        debug_ctx = {"handler": "h", "route": "/r", "seq": 1}
        event = format_element_event("<div>\n<p>line1</p>\n<p>line2</p>\n</div>", debug_ctx=debug_ctx)
        lines = event.strip().split("\n")
        last_elements_idx = max(i for i, line in enumerate(lines) if line.startswith("data: elements"))
        first_debug_idx = next(i for i, line in enumerate(lines) if line.startswith("data: x-debug"))
        assert first_debug_idx > last_elements_idx


class TestDebugContextAutoRead:
    """Tests for context var auto-read in format functions."""

    def test_format_signal_event_reads_from_context_var(self):
        """format_signal_event auto-reads debug context when not explicitly passed."""
        token = set_debug_context(handler="my_handler", route="/my/route")
        try:
            event = format_signal_event({"x": 1})
            assert "x-debug-handler my_handler" in event
            assert "x-debug-route /my/route" in event
        finally:
            _debug_ctx_var.reset(token)

    def test_format_element_event_reads_from_context_var(self):
        """format_element_event auto-reads debug context when not explicitly passed."""
        token = set_debug_context(handler="render_page", route="/page")
        try:
            event = format_element_event("<div>test</div>")
            assert "x-debug-handler render_page" in event
            assert "x-debug-route /page" in event
        finally:
            _debug_ctx_var.reset(token)

    def test_no_context_var_means_no_debug(self):
        """Without context var set, no debug metadata appears."""
        assert get_debug_context() is None
        event = format_signal_event({"x": 1})
        assert "x-debug" not in event

    def test_explicit_debug_ctx_overrides_context_var(self):
        """Explicit debug_ctx parameter takes precedence over context var."""
        token = set_debug_context(handler="contextvar_handler", route="/cv")
        try:
            explicit = {"handler": "explicit_handler", "route": "/explicit", "seq": 99}
            event = format_signal_event({"x": 1}, debug_ctx=explicit)
            assert "x-debug-handler explicit_handler" in event
            assert "x-debug-route /explicit" in event
            assert "contextvar_handler" not in event
        finally:
            _debug_ctx_var.reset(token)

    def test_process_sse_item_gets_debug_via_auto_read(self):
        """process_sse_item delegates to format functions which auto-read context."""
        token = set_debug_context(handler="sse_handler", route="/sse/test")
        try:
            result = process_sse_item("signals", {"payload": {"count": 1}, "options": {}})
            assert result is not None
            assert "x-debug-handler sse_handler" in result
        finally:
            _debug_ctx_var.reset(token)

    def test_format_event_gets_debug_via_auto_read(self):
        """format_event delegates to format functions which auto-read context."""
        token = set_debug_context(handler="event_handler", route="/events")
        try:
            result = format_event(SignalEvent(signals={"x": 1}))
            assert "x-debug-handler event_handler" in result
        finally:
            _debug_ctx_var.reset(token)
