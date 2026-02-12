"""Edge-case, concurrency, and integration tests for the Relay class.

Complements basic behavior tests with:
- Thread safety under concurrent emit
- Subscribe/unsubscribe during fanout
- Full roundtrip through format_event
- Mixed event type ordering
- Large payloads
- Backpressure isolation
- Rapid churn resilience
"""

import asyncio
import threading

import pytest

from starhtml import Div, P, Span
from starhtml.realtime import (
    ElementEvent,
    Relay,
    ScriptEvent,
    SignalEvent,
    format_event,
)


class TestThreadSafety:
    """Verify Relay is safe under concurrent access from multiple threads."""

    def test_concurrent_emit_no_crash(self):
        """Multiple threads emitting simultaneously must not corrupt state or crash."""
        relay = Relay(maxsize=0)  # unlimited so no drops under contention
        q = relay.subscribe()
        num_threads = 8
        events_per_thread = 100
        barrier = threading.Barrier(num_threads)

        def emitter(thread_id):
            barrier.wait()
            for i in range(events_per_thread):
                relay.emit(SignalEvent({"thread": thread_id, "i": i}))

        threads = [threading.Thread(target=emitter, args=(t,)) for t in range(num_threads)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        total = 0
        while not q.empty():
            q.get_nowait()
            total += 1
        assert total == num_threads * events_per_thread

    def test_concurrent_emit_preserves_all_subscribers(self):
        """After concurrent emits, all subscribers still exist and received events."""
        relay = Relay()
        queues = [relay.subscribe() for _ in range(5)]
        barrier = threading.Barrier(5)

        def emitter(thread_id):
            barrier.wait()
            relay.emit(SignalEvent({"t": thread_id}))

        threads = [threading.Thread(target=emitter, args=(i,)) for i in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        for q in queues:
            count = 0
            while not q.empty():
                q.get_nowait()
                count += 1
            # Each subscriber gets all 5 events
            assert count == 5

    def test_concurrent_subscribe_and_emit(self):
        """Subscribing from one thread while another emits must not raise."""
        relay = Relay()
        collected_queues = []
        errors = []
        barrier = threading.Barrier(2)

        def subscriber():
            barrier.wait()
            for _ in range(50):
                q = relay.subscribe()
                collected_queues.append(q)

        def emitter():
            barrier.wait()
            for i in range(50):
                try:
                    relay.emit(SignalEvent({"i": i}))
                except Exception as exc:
                    errors.append(exc)

        t1 = threading.Thread(target=subscriber)
        t2 = threading.Thread(target=emitter)
        t1.start()
        t2.start()
        t1.join()
        t2.join()

        assert errors == []
        assert len(collected_queues) == 50


class TestSubscribeDuringEmit:
    """Snapshot pattern in emit() protects against mutation during iteration."""

    def test_subscribe_during_fanout_does_not_error(self):
        """Adding a subscriber while emit iterates over the snapshot is safe."""
        relay = Relay()
        q1 = relay.subscribe()
        new_queues = []

        # Monkey-patch put_nowait on q1 to subscribe a new queue mid-fanout
        original_put = q1.put_nowait

        def intercepting_put(item):
            original_put(item)
            if not new_queues:
                new_queues.append(relay.subscribe())

        q1.put_nowait = intercepting_put

        relay.emit(SignalEvent({"x": 1}))

        # q1 received the event
        assert q1.get_nowait().signals == {"x": 1}
        # The new subscriber was added after the snapshot, so it should NOT
        # have received this event
        assert len(new_queues) == 1
        assert new_queues[0].empty()

    def test_new_subscriber_gets_subsequent_events(self):
        """A subscriber added mid-fanout receives future events."""
        relay = Relay()
        q1 = relay.subscribe()
        new_queues = []

        original_put = q1.put_nowait

        def intercepting_put(item):
            original_put(item)
            if not new_queues:
                new_queues.append(relay.subscribe())

        q1.put_nowait = intercepting_put

        relay.emit(SignalEvent({"first": True}))
        relay.emit(SignalEvent({"second": True}))

        # New subscriber missed the first but got the second
        assert new_queues[0].get_nowait().signals == {"second": True}


class TestUnsubscribeDuringEmit:
    """Removing a subscriber during fanout must not crash."""

    def test_unsubscribe_during_fanout_no_crash(self):
        """Unsubscribing a queue while emit iterates over snapshot is safe."""
        relay = Relay()
        q1 = relay.subscribe()
        q2 = relay.subscribe()

        original_put = q1.put_nowait

        def intercepting_put(item):
            original_put(item)
            relay.unsubscribe(q2)

        q1.put_nowait = intercepting_put

        # Should not raise even though q2 is removed during iteration
        relay.emit(SignalEvent({"v": 1}))

        # q1 received it
        assert q1.get_nowait().signals == {"v": 1}
        # q2 also received it because emit uses a snapshot taken before unsubscribe
        assert q2.get_nowait().signals == {"v": 1}

    def test_unsubscribed_queue_does_not_get_future_events(self):
        """After unsubscribe, queue stops receiving events."""
        relay = Relay()
        q1 = relay.subscribe()
        q2 = relay.subscribe()

        relay.unsubscribe(q1)
        relay.emit(SignalEvent({"after": True}))

        assert q1.empty()
        assert q2.get_nowait().signals == {"after": True}


class TestFullRoundtrip:
    """emit -> queue.get_nowait -> format_event -> validate SSE string."""

    def test_signal_roundtrip(self):
        relay = Relay()
        q = relay.subscribe()
        relay.emit(SignalEvent({"count": 42}))
        event = q.get_nowait()
        sse_str = format_event(event)
        assert "event: datastar-patch-signals" in sse_str
        assert '"count": 42' in sse_str
        assert sse_str.endswith("\n\n")

    def test_element_roundtrip(self):
        relay = Relay()
        q = relay.subscribe()
        relay.emit(ElementEvent(element=P("hi"), selector="#box", mode="inner"))
        event = q.get_nowait()
        sse_str = format_event(event)
        assert "event: datastar-patch-elements" in sse_str
        assert "selector #box" in sse_str
        assert "elements <p>hi</p>" in sse_str

    def test_script_roundtrip(self):
        relay = Relay()
        q = relay.subscribe()
        relay.emit(ScriptEvent(script="alert(1)", auto_remove=True))
        event = q.get_nowait()
        sse_str = format_event(event)
        assert "event: datastar-patch-elements" in sse_str
        assert "mode append" in sse_str
        assert "selector body" in sse_str
        assert "alert(1)" in sse_str
        assert "el.remove()" in sse_str

    def test_script_roundtrip_no_auto_remove(self):
        relay = Relay()
        q = relay.subscribe()
        relay.emit(ScriptEvent(script="console.log('stay')", auto_remove=False))
        event = q.get_nowait()
        sse_str = format_event(event)
        assert "console.log('stay')" in sse_str
        assert "el.remove()" not in sse_str


class TestMixedEventOrdering:
    """Multiple event types emitted in sequence arrive in order with correct types."""

    def test_three_event_types_in_order(self):
        relay = Relay()
        q = relay.subscribe()

        relay.emit(SignalEvent({"step": 1}))
        relay.emit(ElementEvent(element="<div>two</div>", selector="#a", mode="outer"))
        relay.emit(ScriptEvent(script="void 0"))

        e1 = q.get_nowait()
        e2 = q.get_nowait()
        e3 = q.get_nowait()

        assert isinstance(e1, SignalEvent)
        assert e1.signals == {"step": 1}

        assert isinstance(e2, ElementEvent)
        assert e2.selector == "#a"
        assert e2.mode == "outer"

        assert isinstance(e3, ScriptEvent)
        assert e3.script == "void 0"

    def test_convenience_methods_ordering(self):
        """emit_signals, emit_element, emit_script produce correct event types."""
        relay = Relay()
        q = relay.subscribe()

        relay.emit_signals({"a": 1})
        relay.emit_element("<b>x</b>", "#b", "append")
        relay.emit_script("run()")

        assert isinstance(q.get_nowait(), SignalEvent)
        assert isinstance(q.get_nowait(), ElementEvent)
        assert isinstance(q.get_nowait(), ScriptEvent)

    def test_emit_signals_skips_empty_dict(self):
        """emit_signals with empty dict should not emit."""
        relay = Relay()
        q = relay.subscribe()
        relay.emit_signals({})
        assert q.empty()


class TestLargePayloads:
    """Large data must not be truncated or corrupted."""

    def test_large_signal_dict(self):
        relay = Relay()
        q = relay.subscribe()
        big_signals = {f"key_{i}": f"value_{i}" for i in range(1000)}
        relay.emit(SignalEvent(big_signals))

        event = q.get_nowait()
        assert len(event.signals) == 1000
        sse_str = format_event(event)
        # Verify a sampling of keys survived the roundtrip
        assert '"key_0"' in sse_str
        assert '"key_500"' in sse_str
        assert '"key_999"' in sse_str

    def test_large_html_element(self):
        relay = Relay()
        q = relay.subscribe()
        big_html = "<div>" + "x" * 50_000 + "</div>"
        relay.emit(ElementEvent(element=big_html, selector="#big", mode="inner"))

        event = q.get_nowait()
        sse_str = format_event(event)
        assert len(sse_str) > 50_000
        assert "x" * 100 in sse_str


class TestUnlimitedQueueSize:
    """Relay with maxsize=0 creates unlimited queues."""

    def test_maxsize_zero_accepts_many_events(self):
        relay = Relay(maxsize=0)
        q = relay.subscribe()

        for i in range(2000):
            relay.emit(SignalEvent({"i": i}))

        count = 0
        while not q.empty():
            q.get_nowait()
            count += 1
        assert count == 2000


class TestBackpressure:
    """Full queue for one subscriber must not block others."""

    def test_full_queue_does_not_block_healthy_subscriber(self):
        """With one full and one healthy subscriber, healthy one still gets events."""
        relay = Relay()

        # Manually create a tiny queue to simulate a full subscriber
        full_q = asyncio.Queue(maxsize=2)
        healthy_q = asyncio.Queue(maxsize=100)

        with relay._lock:
            relay._subscribers.append(full_q)
            relay._subscribers.append(healthy_q)

        # Fill up the small queue
        relay.emit(SignalEvent({"a": 1}))
        relay.emit(SignalEvent({"b": 2}))
        # full_q is now at capacity (2/2)

        # This event should be dropped for full_q but delivered to healthy_q
        relay.emit(SignalEvent({"c": 3}))

        assert healthy_q.qsize() == 3
        assert full_q.qsize() == 2  # Still at max, third was dropped

        # Verify healthy_q got all three
        assert healthy_q.get_nowait().signals == {"a": 1}
        assert healthy_q.get_nowait().signals == {"b": 2}
        assert healthy_q.get_nowait().signals == {"c": 3}

    def test_all_queues_full_does_not_raise(self):
        """When every subscriber queue is full, emit still completes without error."""
        relay = Relay()
        tiny_q = asyncio.Queue(maxsize=1)
        with relay._lock:
            relay._subscribers.append(tiny_q)

        relay.emit(SignalEvent({"first": True}))
        relay.emit(SignalEvent({"dropped": True}))  # Should not raise

        assert tiny_q.qsize() == 1
        assert tiny_q.get_nowait().signals == {"first": True}


class TestFormatEventWithFTObjects:
    """format_event works with starhtml FT element objects, not just raw HTML strings."""

    def test_div_element(self):
        event = ElementEvent(element=Div("hello", id="test"), selector="#test", mode="inner")
        sse_str = format_event(event)
        assert "event: datastar-patch-elements" in sse_str
        assert 'id="test"' in sse_str
        assert "hello" in sse_str

    def test_nested_ft_elements(self):
        event = ElementEvent(
            element=Div(P("paragraph"), Span("inline"), cls="wrapper"),
            selector="#root",
            mode="outer",
        )
        sse_str = format_event(event)
        assert "paragraph" in sse_str
        assert "inline" in sse_str
        assert "wrapper" in sse_str

    def test_signal_event_format_event_type_error(self):
        """format_event raises TypeError for unknown event types."""
        with pytest.raises(TypeError, match="Unknown event type"):
            format_event("not an event")


class TestSubscribeUnsubscribeChurn:
    """Rapid subscribe/unsubscribe must not leak queues."""

    def test_rapid_churn_no_leaked_queues(self):
        relay = Relay()
        for _ in range(100):
            q = relay.subscribe()
            relay.unsubscribe(q)

        assert len(relay._subscribers) == 0

    def test_rapid_churn_with_concurrent_emit(self):
        """Subscribe/unsubscribe churn with concurrent emits has no leaks or crashes."""
        relay = Relay()
        stable_q = relay.subscribe()
        errors = []
        barrier = threading.Barrier(2)

        def churner():
            barrier.wait()
            for _ in range(100):
                q = relay.subscribe()
                relay.unsubscribe(q)

        def emitter():
            barrier.wait()
            for i in range(100):
                try:
                    relay.emit(SignalEvent({"i": i}))
                except Exception as exc:
                    errors.append(exc)

        t1 = threading.Thread(target=churner)
        t2 = threading.Thread(target=emitter)
        t1.start()
        t2.start()
        t1.join()
        t2.join()

        assert errors == []
        # Only the stable subscriber should remain
        assert len(relay._subscribers) == 1
        # Stable subscriber got all events
        count = 0
        while not stable_q.empty():
            stable_q.get_nowait()
            count += 1
        assert count == 100

    def test_double_unsubscribe_is_safe(self):
        """Unsubscribing the same queue twice does not raise."""
        relay = Relay()
        q = relay.subscribe()
        relay.unsubscribe(q)
        relay.unsubscribe(q)  # Should not raise
        assert len(relay._subscribers) == 0


class TestEdgeCases:
    """Miscellaneous edge-case behaviors."""

    def test_emit_with_no_subscribers(self):
        """Emitting with no subscribers is a no-op, no error."""
        relay = Relay()
        relay.emit(SignalEvent({"lonely": True}))  # Should not raise

    def test_subscribe_returns_queue_with_correct_maxsize(self):
        relay = Relay(maxsize=42)
        q = relay.subscribe()
        assert q.maxsize == 42

    def test_default_maxsize_is_500(self):
        relay = Relay()
        q = relay.subscribe()
        assert q.maxsize == 500

    def test_element_event_default_mode(self):
        """ElementEvent defaults mode to 'inner'."""
        event = ElementEvent(element="<p>x</p>", selector="#s")
        assert event.mode == "inner"

    def test_script_event_default_auto_remove(self):
        """ScriptEvent defaults auto_remove to True."""
        event = ScriptEvent(script="x()")
        assert event.auto_remove is True

    def test_emit_same_event_object_to_multiple_subscribers(self):
        """The same event object is shared across all subscriber queues (not copied)."""
        relay = Relay()
        q1 = relay.subscribe()
        q2 = relay.subscribe()

        event = SignalEvent({"shared": True})
        relay.emit(event)

        e1 = q1.get_nowait()
        e2 = q2.get_nowait()
        assert e1 is e2  # Same object, not a copy
