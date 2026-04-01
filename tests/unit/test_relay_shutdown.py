"""Tests for Relay.shutdown() graceful shutdown mechanism."""

import asyncio
import threading
from collections import deque

import pytest

from starhtml.realtime import (
    RELAY_SHUTDOWN,
    Relay,
    SignalEvent,
)


class TestShutdownBasics:
    def test_shutdown_delivers_sentinel_to_all_subscribers(self):
        relay = Relay()
        q1 = relay.subscribe()
        q2 = relay.subscribe()
        relay.shutdown()
        assert q1.get_nowait() is RELAY_SHUTDOWN
        assert q2.get_nowait() is RELAY_SHUTDOWN

    def test_shutdown_clears_subscriber_list(self):
        relay = Relay()
        relay.subscribe()
        relay.subscribe()
        relay.shutdown()
        assert len(relay._subscribers) == 0

    def test_shutdown_idempotent(self):
        relay = Relay()
        q = relay.subscribe()
        relay.shutdown()
        relay.shutdown()  # should not raise or double-deliver
        assert q.get_nowait() is RELAY_SHUTDOWN
        assert q.empty()

    def test_shutdown_with_no_subscribers(self):
        relay = Relay()
        relay.shutdown()  # should not raise


class TestShutdownBlocksEmit:
    def test_emit_after_shutdown_is_noop(self):
        relay = Relay()
        q = relay.subscribe()
        relay.shutdown()
        q.get_nowait()  # drain sentinel
        relay.emit(SignalEvent({"x": 1}))
        assert q.empty()

    def test_emit_signals_after_shutdown_is_noop(self):
        relay = Relay()
        q = relay.subscribe()
        relay.shutdown()
        q.get_nowait()  # drain sentinel
        relay.emit_signals({"x": 1})
        assert q.empty()


class TestShutdownBlocksSubscribe:
    def test_subscribe_after_shutdown_raises(self):
        relay = Relay()
        relay.shutdown()
        with pytest.raises(RuntimeError, match="shut-down"):
            relay.subscribe()


class TestShutdownFullQueue:
    def test_sentinel_delivered_to_full_queue(self):
        """Shutdown drains one item if needed to deliver the sentinel."""
        relay = Relay(maxsize=1)
        q = relay.subscribe()
        relay.emit(SignalEvent({"a": 1}))
        # Queue is full (1/1)
        relay.shutdown()
        # The pending event was dropped, sentinel was delivered
        items = []
        while not q.empty():
            items.append(q.get_nowait())
        assert any(item is RELAY_SHUTDOWN for item in items)


class TestShutdownUnblocksConsumer:
    def test_consumer_blocked_on_get_unblocks(self):
        """An asyncio consumer waiting on queue.get() unblocks immediately."""
        relay = Relay()
        q = relay.subscribe()

        async def _run():
            async def _delayed_shutdown():
                await asyncio.sleep(0.05)
                relay.shutdown()

            asyncio.create_task(_delayed_shutdown())
            return await asyncio.wait_for(q.get(), timeout=2.0)

        result = asyncio.run(_run())
        assert result is RELAY_SHUTDOWN


class TestShutdownThreadSafety:
    def test_shutdown_from_different_thread(self):
        relay = Relay()
        q = relay.subscribe()
        t = threading.Thread(target=relay.shutdown)
        t.start()
        t.join()
        assert q.get_nowait() is RELAY_SHUTDOWN

    def test_concurrent_emit_and_shutdown(self):
        """Shutdown during concurrent emit should not crash."""
        relay = Relay(maxsize=0)
        q = relay.subscribe()
        errors = []
        barrier = threading.Barrier(2)

        def emitter():
            barrier.wait()
            for _ in range(100):
                try:
                    relay.emit(SignalEvent({"i": 1}))
                except Exception as exc:
                    errors.append(exc)

        def shutdowner():
            barrier.wait()
            relay.shutdown()

        t1 = threading.Thread(target=emitter)
        t2 = threading.Thread(target=shutdowner)
        t1.start()
        t2.start()
        t1.join()
        t2.join()
        assert errors == []
        # Sentinel must be in the queue somewhere
        found = False
        while not q.empty():
            if q.get_nowait() is RELAY_SHUTDOWN:
                found = True
                break
        assert found

    def test_emit_cannot_append_after_shutdown_sentinel(self):
        relay = Relay()

        class BlockingQueue:
            def __init__(self):
                self.items = deque()
                self.started = threading.Event()
                self.release = threading.Event()

            def put_nowait(self, item):
                if item is not RELAY_SHUTDOWN:
                    self.started.set()
                    assert self.release.wait(timeout=1)
                self.items.append(item)

            def get_nowait(self):
                if not self.items:
                    raise asyncio.QueueEmpty
                return self.items.popleft()

            def empty(self):
                return not self.items

        q = BlockingQueue()
        relay._subscribers.append(q)  # type: ignore[arg-type]

        emitter = threading.Thread(target=lambda: relay.emit(SignalEvent({"i": 1})))
        shutdowner = threading.Thread(target=relay.shutdown)
        emitter.start()
        assert q.started.wait(timeout=1)
        shutdowner.start()
        q.release.set()
        emitter.join()
        shutdowner.join()

        assert list(q.items) == [SignalEvent({"i": 1}), RELAY_SHUTDOWN]


class TestUnsubscribeAfterShutdown:
    def test_unsubscribe_after_shutdown_is_safe(self):
        """relay.stream() always calls unsubscribe in finally — must not raise."""
        relay = Relay()
        q = relay.subscribe()
        relay.shutdown()
        relay.unsubscribe(q)  # should not raise


class TestAsyncContextManager:
    def test_context_manager_calls_shutdown(self):
        async def _run():
            relay = Relay()
            q = relay.subscribe()
            async with relay:
                relay.emit(SignalEvent({"x": 1}))
            items = []
            while not q.empty():
                items.append(q.get_nowait())
            return items

        items = asyncio.run(_run())
        sentinels = [i for i in items if i is RELAY_SHUTDOWN]
        assert len(sentinels) == 1

    def test_context_manager_returns_relay(self):
        async def _run():
            relay = Relay()
            async with relay as r:
                return r is relay

        assert asyncio.run(_run())


class TestSentinelRepr:
    def test_sentinel_repr(self):
        assert repr(RELAY_SHUTDOWN) == "RELAY_SHUTDOWN"

    def test_sentinel_is_singleton(self):
        from starhtml.realtime import RELAY_SHUTDOWN as IMPORTED_SHUTDOWN

        assert IMPORTED_SHUTDOWN is RELAY_SHUTDOWN
