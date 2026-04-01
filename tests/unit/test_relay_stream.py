"""Tests for Relay.stream() — the canonical SSE async generator."""

import asyncio

from starhtml.realtime import (
    SSE_KEEPALIVE,
    Relay,
    SignalEvent,
    signals,
    stream_sse_items,
)


class TestStreamYieldsEvents:
    def test_yields_signal_items(self):
        relay = Relay()

        async def _run():
            gen = relay.stream()

            async def _delayed_emit():
                await asyncio.sleep(0.05)
                relay.emit_signals({"status": "ok"})

            asyncio.create_task(_delayed_emit())
            item = await asyncio.wait_for(gen.__anext__(), timeout=2.0)
            await gen.aclose()
            return item

        result = asyncio.run(_run())
        assert isinstance(result, tuple) and len(result) == 2
        assert result[0] == "signals"
        assert result[1]["payload"] == {"status": "ok"}

    def test_yields_element_items(self):
        relay = Relay()

        async def _run():
            gen = relay.stream()

            async def _delayed_emit():
                await asyncio.sleep(0.05)
                relay.emit_element("<div>test</div>", "#target", "inner")

            asyncio.create_task(_delayed_emit())
            item = await asyncio.wait_for(gen.__anext__(), timeout=2.0)
            await gen.aclose()
            return item

        result = asyncio.run(_run())
        assert isinstance(result, tuple) and len(result) == 2
        assert result[0] == "elements"
        assert result[1][0] == "<div>test</div>"
        assert result[1][1] == "#target"

    def test_yields_script_items(self):
        relay = Relay()

        async def _run():
            gen = relay.stream()

            async def _delayed_emit():
                await asyncio.sleep(0.05)
                relay.emit_script("console.log('hello')")

            asyncio.create_task(_delayed_emit())
            item = await asyncio.wait_for(gen.__anext__(), timeout=2.0)
            await gen.aclose()
            return item

        result = asyncio.run(_run())
        assert isinstance(result, tuple) and len(result) == 2
        assert result[0] == "elements"  # execute_script wraps as elements


class TestStreamShutdownSentinel:
    def test_exits_on_relay_shutdown(self):
        """stream() should exit cleanly when relay.shutdown() is called."""
        relay = Relay()

        async def _run():
            gen = relay.stream()

            async def _delayed_shutdown():
                await asyncio.sleep(0.1)
                relay.shutdown()

            asyncio.create_task(_delayed_shutdown())
            items = []
            async for item in gen:
                items.append(item)
            return items

        result = asyncio.run(asyncio.wait_for(_run(), timeout=3.0))
        assert result == []

    def test_shutdown_is_immediate(self):
        """stream() should exit within ~0.1s of shutdown(), not wait for 1s timeout."""
        relay = Relay()

        async def _run():
            gen = relay.stream()

            async def _delayed_shutdown():
                await asyncio.sleep(0.05)
                relay.shutdown()

            asyncio.create_task(_delayed_shutdown())

            import time

            start = time.monotonic()
            async for _ in gen:
                pass
            return time.monotonic() - start

        elapsed = asyncio.run(asyncio.wait_for(_run(), timeout=3.0))
        # Should exit well under 1 second (the timeout poll interval)
        assert elapsed < 0.5


class TestStreamShutdownEvent:
    def test_exits_on_shutdown_event(self):
        relay = Relay()

        async def _run():
            shutdown = asyncio.Event()
            gen = relay.stream(shutdown=shutdown)

            async def _set_shutdown():
                await asyncio.sleep(0.1)
                shutdown.set()

            asyncio.create_task(_set_shutdown())
            items = []
            async for item in gen:
                items.append(item)
            return items

        result = asyncio.run(asyncio.wait_for(_run(), timeout=3.0))
        assert result == []

    def test_shutdown_event_exits_even_if_queue_is_full(self):
        class PreloadedRelay(Relay):
            def subscribe(self):
                q = asyncio.Queue(maxsize=1)
                q.put_nowait(SignalEvent({"queued": True}))
                return q

        relay = PreloadedRelay(maxsize=1)

        async def _run():
            shutdown = asyncio.Event()
            gen = relay.stream(shutdown=shutdown)
            first = await asyncio.wait_for(gen.__anext__(), timeout=1.0)
            shutdown.set()
            remaining = []
            async for item in gen:
                remaining.append(item)
            return first, remaining

        first, remaining = asyncio.run(asyncio.wait_for(_run(), timeout=3.0))
        assert first[0] == "signals"
        assert remaining == []


class TestStreamLifecycle:
    def test_unsubscribes_on_close(self):
        relay = Relay()

        async def _run():
            gen = relay.stream()
            # Advance the generator so subscribe() actually runs
            next_task = asyncio.ensure_future(gen.__anext__())
            await asyncio.sleep(0.05)
            assert len(relay._subscribers) == 1
            # Cancel the pending __anext__ first, then close the generator
            next_task.cancel()
            try:
                await next_task
            except (asyncio.CancelledError, StopAsyncIteration):
                pass
            await gen.aclose()
            return len(relay._subscribers)

        count = asyncio.run(_run())
        assert count == 0

    def test_unsubscribes_on_shutdown(self):
        relay = Relay()

        async def _run():
            gen = relay.stream()

            async def _delayed_shutdown():
                await asyncio.sleep(0.05)
                relay.shutdown()

            asyncio.create_task(_delayed_shutdown())
            async for _ in gen:
                pass
            # After shutdown + stream exit, subscribers should be empty
            # (shutdown clears them, and unsubscribe is a no-op)
            return len(relay._subscribers)

        count = asyncio.run(asyncio.wait_for(_run(), timeout=3.0))
        assert count == 0


class TestStreamEventOrdering:
    def test_preserves_emit_order(self):
        relay = Relay()

        async def _run():
            gen = relay.stream()

            async def _emit_and_shutdown():
                await asyncio.sleep(0.05)
                relay.emit_signals({"step": 1})
                relay.emit_element("<div>two</div>", "#a", "inner")
                relay.emit_script("void 0")
                await asyncio.sleep(0.1)
                relay.shutdown()

            asyncio.create_task(_emit_and_shutdown())
            items = []
            async for item in gen:
                items.append(item)
            return items

        items = asyncio.run(asyncio.wait_for(_run(), timeout=3.0))
        assert len(items) == 3
        assert items[0][0] == "signals"
        assert items[1][0] == "elements"
        assert items[2][0] == "elements"  # execute_script wraps as elements


class TestStreamKeepalive:
    def test_emits_keepalive_on_idle(self):
        """stream() yields a keepalive comment when no events arrive within the interval."""
        relay = Relay()

        async def _run():
            gen = relay.stream()

            async def _shutdown_later():
                await asyncio.sleep(0.35)
                relay.shutdown()

            asyncio.create_task(_shutdown_later())
            items = []
            async for item in gen:
                items.append(item)
            return items

        import starhtml.realtime as rt

        original = rt.SSE_KEEPALIVE_TIMEOUT
        rt.SSE_KEEPALIVE_TIMEOUT = 0.1
        try:
            items = asyncio.run(asyncio.wait_for(_run(), timeout=3.0))
        finally:
            rt.SSE_KEEPALIVE_TIMEOUT = original
        keepalives = [i for i in items if i == SSE_KEEPALIVE]
        assert len(keepalives) >= 2


class TestStreamSseItemsStringPassthrough:
    def test_string_passthrough(self):
        """Pre-formatted SSE strings pass through stream_sse_items unchanged."""

        async def gen():
            yield ": keepalive\n\n"
            yield signals(status="ok")

        async def _run():
            items = []
            async for item in stream_sse_items(gen()):
                items.append(item)
            return items

        items = asyncio.run(_run())
        assert items[0] == ": keepalive\n\n"
        assert "status" in items[1]


class TestInstallApp:
    def test_install_registers_shutdown_handler(self):
        """relay.install(app) registers shutdown so relay.shutdown() is called on app exit."""
        calls = []

        class FakeApp:
            def add_event_handler(self, event, handler):
                calls.append((event, handler))

        relay = Relay()
        relay.install(FakeApp())
        assert len(calls) == 1
        assert calls[0][0] == "shutdown"
        # Calling the registered handler should shut down the relay
        calls[0][1]()
        assert relay._closed is True
