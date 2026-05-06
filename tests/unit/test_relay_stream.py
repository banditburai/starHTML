"""Tests for Relay.stream() — the canonical SSE async generator."""

import asyncio

import pytest

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

    def test_shutdown_does_not_wait_for_keepalive_poll(self):
        """stream() must exit on shutdown without waiting for the keepalive poll.

        Asserted as a contract on the consumer side: an async-for that started
        before shutdown completes well before the keepalive interval would
        have fired (we set keepalive to 5s, then assert exit < 1s).
        """
        relay = Relay()

        async def _run(monkey_keepalive):
            import starhtml.realtime as rt

            rt.SSE_KEEPALIVE_TIMEOUT = monkey_keepalive
            gen = relay.stream()
            done = asyncio.Event()

            async def _drain():
                async for _ in gen:
                    pass
                done.set()

            asyncio.create_task(_drain())
            await asyncio.sleep(0.05)
            relay.shutdown()
            # If shutdown waits for the keepalive poll we'd block 5s.
            await asyncio.wait_for(done.wait(), timeout=1.0)

        import starhtml.realtime as rt

        original = rt.SSE_KEEPALIVE_TIMEOUT
        try:
            asyncio.run(_run(5.0))
        finally:
            rt.SSE_KEEPALIVE_TIMEOUT = original


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
    def test_closed_stream_does_not_receive_further_emits(self):
        """After stream is closed, later emits do not reach a fresh stream's first item."""
        relay = Relay()

        async def _run():
            gen = relay.stream()
            next_task = asyncio.ensure_future(gen.__anext__())
            await asyncio.sleep(0.05)
            next_task.cancel()
            try:
                await next_task
            except (asyncio.CancelledError, StopAsyncIteration):
                pass
            await gen.aclose()

            # Emit after close: no observer should pick it up.
            relay.emit_signals({"after_close": True})
            # A fresh stream sees only events emitted while it is alive.
            gen2 = relay.stream()
            second_task = asyncio.ensure_future(gen2.__anext__())
            await asyncio.sleep(0.05)
            relay.shutdown()
            try:
                first = await asyncio.wait_for(second_task, timeout=1.0)
            except (StopAsyncIteration, asyncio.CancelledError):
                first = None
            await gen2.aclose()
            return first

        first = asyncio.run(_run())
        # A fresh stream after the closed one's emit must not surface that emit.
        assert first is None or first[0] != "signals" or first[1].get("payload") != {"after_close": True}

    def test_shutdown_terminates_active_stream(self):
        """The visible contract: an async-for over stream() exits after shutdown()."""
        relay = Relay()

        async def _run():
            gen = relay.stream()

            async def _delayed_shutdown():
                await asyncio.sleep(0.05)
                relay.shutdown()

            asyncio.create_task(_delayed_shutdown())
            async for _ in gen:
                pass

        # If shutdown didn't propagate, this would hang past the timeout.
        asyncio.run(asyncio.wait_for(_run(), timeout=3.0))


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
    def test_emits_keepalive_on_idle(self, monkeypatch):
        """stream() yields a keepalive comment when no events arrive within the interval."""
        import starhtml.realtime as rt

        monkeypatch.setattr(rt, "SSE_KEEPALIVE_TIMEOUT", 0.1)
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

        items = asyncio.run(asyncio.wait_for(_run(), timeout=3.0))
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
    def test_install_uses_internal_lifecycle_handler(self):
        calls = []

        class FakeApp:
            def add_lifecycle_handler(self, event, handler):
                calls.append((event, handler))

        relay = Relay()
        relay.install(FakeApp())

        assert len(calls) == 1
        assert calls[0][0] == "shutdown"
        # Invoking the registered shutdown handler must put the relay into
        # the shut-down state, observable via subscribe() raising.
        calls[0][1]()
        with pytest.raises(RuntimeError, match="shut-down"):
            relay.subscribe()

    def test_install_wraps_server_exit_before_original_handler(self):
        events = []

        class FakeApp:
            def add_lifecycle_handler(self, event, handler): ...

        class FakeServer:
            def handle_exit(self, sig, frame):
                events.append(("server", sig, frame))

        class TestRelay(Relay):
            def shutdown(self):
                events.append(("relay", None, None))

        relay = TestRelay()
        server = FakeServer()

        relay.install(FakeApp(), server=server)
        server.handle_exit("SIGTERM", "frame")

        assert events == [("relay", None, None), ("server", "SIGTERM", "frame")]

    def test_install_does_not_double_wrap_server_exit(self):
        calls = []

        class FakeApp:
            def add_lifecycle_handler(self, event, handler):
                calls.append((event, handler))

        class FakeServer:
            def __init__(self):
                self.count = 0

            def handle_exit(self, sig, frame):
                self.count += 1

        shutdowns = []

        class TestRelay(Relay):
            def shutdown(self):
                shutdowns.append("shutdown")

        relay = TestRelay()
        server = FakeServer()

        relay.install(FakeApp(), server=server)
        relay.install(FakeApp(), server=server)
        server.handle_exit("SIGTERM", None)

        assert server.count == 1
        assert shutdowns == ["shutdown"]

    def test_install_raises_on_unsupported_app(self):
        relay = Relay()
        with pytest.raises(AttributeError, match="must support add_lifecycle_handler"):
            relay.install(object())
