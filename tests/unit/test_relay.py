"""Behavior tests for the Relay pub/sub class."""

import asyncio

from starhtml.realtime import (
    ElementEvent,
    Relay,
    ScriptEvent,
    SignalEvent,
)


class TestSubscribeUnsubscribe:
    def test_subscribe_returns_a_queue(self):
        relay = Relay()
        q = relay.subscribe()
        assert isinstance(q, asyncio.Queue)

    def test_events_arrive_after_subscribe(self):
        relay = Relay()
        q = relay.subscribe()
        event = SignalEvent({"x": 1})
        relay.emit(event)
        assert q.get_nowait() is event

    def test_events_stop_after_unsubscribe(self):
        relay = Relay()
        q = relay.subscribe()
        relay.unsubscribe(q)
        relay.emit(SignalEvent({"x": 1}))
        assert q.empty()

    def test_unsubscribe_idempotent(self):
        relay = Relay()
        q = relay.subscribe()
        relay.unsubscribe(q)
        relay.unsubscribe(q)  # should not raise

    def test_unsubscribe_unknown_queue(self):
        relay = Relay()
        unknown = asyncio.Queue()
        relay.unsubscribe(unknown)  # should not raise


class TestFanOut:
    def test_emit_delivers_to_all_subscribers(self):
        relay = Relay()
        q1 = relay.subscribe()
        q2 = relay.subscribe()
        q3 = relay.subscribe()
        event = SignalEvent({"k": "v"})
        relay.emit(event)
        assert q1.get_nowait() is event
        assert q2.get_nowait() is event
        assert q3.get_nowait() is event


class TestEventDelivery:
    def test_events_arrive_in_emit_order(self):
        relay = Relay()
        q = relay.subscribe()
        e1 = SignalEvent({"a": 1})
        e2 = SignalEvent({"b": 2})
        e3 = SignalEvent({"c": 3})
        relay.emit(e1)
        relay.emit(e2)
        relay.emit(e3)
        assert q.get_nowait() is e1
        assert q.get_nowait() is e2
        assert q.get_nowait() is e3

    def test_multiple_events_all_arrive(self):
        relay = Relay()
        q = relay.subscribe()
        events = [SignalEvent({"i": i}) for i in range(10)]
        for e in events:
            relay.emit(e)
        received = [q.get_nowait() for _ in range(10)]
        assert received == events


class TestBackpressure:
    def test_full_queue_drops_events_silently(self):
        relay = Relay(maxsize=2)
        q = relay.subscribe()
        relay.emit(SignalEvent({"a": 1}))
        relay.emit(SignalEvent({"b": 2}))
        relay.emit(SignalEvent({"c": 3}))  # dropped
        assert q.qsize() == 2
        assert q.get_nowait().signals == {"a": 1}
        assert q.get_nowait().signals == {"b": 2}

    def test_full_queue_does_not_affect_other_subscribers(self):
        relay = Relay(maxsize=2)
        qa = relay.subscribe()
        qb = relay.subscribe()
        # Emit one event to both
        relay.emit(SignalEvent({"x": 1}))
        # Drain qb so it has more room than qa
        qb.get_nowait()
        relay.emit(SignalEvent({"x": 2}))
        relay.emit(SignalEvent({"x": 3}))
        # qa is full after 2 events; 3rd is dropped for qa
        assert qa.qsize() == 2
        # qb had room and received all three it wasn't drained from
        assert qb.qsize() == 2
        assert qb.get_nowait().signals == {"x": 2}
        assert qb.get_nowait().signals == {"x": 3}


class TestCustomMaxsize:
    def test_relay_maxsize_applied_to_queues(self):
        relay = Relay(maxsize=5)
        q = relay.subscribe()
        assert q.maxsize == 5

    def test_default_maxsize_is_500(self):
        relay = Relay()
        q = relay.subscribe()
        assert q.maxsize == 500


class TestNoSubscribers:
    def test_emit_with_no_subscribers(self):
        relay = Relay()
        relay.emit(SignalEvent({"x": 1}))  # should not raise

    def test_emit_after_all_unsubscribed(self):
        relay = Relay()
        q = relay.subscribe()
        relay.unsubscribe(q)
        relay.emit(SignalEvent({"x": 1}))  # should not raise
        assert q.empty()


class TestConvenienceMethods:
    def test_emit_signals_puts_signal_event(self):
        relay = Relay()
        q = relay.subscribe()
        relay.emit_signals({"x": 1})
        event = q.get_nowait()
        assert isinstance(event, SignalEvent)
        assert event.signals == {"x": 1}

    def test_emit_signals_empty_dict_no_event(self):
        relay = Relay()
        q = relay.subscribe()
        relay.emit_signals({})
        assert q.empty()

    def test_emit_element_puts_element_event_with_default_mode(self):
        relay = Relay()
        q = relay.subscribe()
        relay.emit_element("<div>hi</div>", "#foo")
        event = q.get_nowait()
        assert isinstance(event, ElementEvent)
        assert event.element == "<div>hi</div>"
        assert event.selector == "#foo"
        assert event.mode == "outer"

    def test_emit_element_with_explicit_mode(self):
        relay = Relay()
        q = relay.subscribe()
        relay.emit_element("<p/>", "#bar", mode="append")
        event = q.get_nowait()
        assert isinstance(event, ElementEvent)
        assert event.mode == "append"

    def test_emit_script_puts_script_event_with_auto_remove(self):
        relay = Relay()
        q = relay.subscribe()
        relay.emit_script("alert(1)")
        event = q.get_nowait()
        assert isinstance(event, ScriptEvent)
        assert event.script == "alert(1)"
        assert event.auto_remove is True

    def test_emit_script_auto_remove_false(self):
        relay = Relay()
        q = relay.subscribe()
        relay.emit_script("console.log(1)", auto_remove=False)
        event = q.get_nowait()
        assert isinstance(event, ScriptEvent)
        assert event.auto_remove is False
