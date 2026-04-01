"""Tests for stream_sse_items() generator finalization on disconnect."""

import asyncio

from starhtml.realtime import Relay, signals, stream_sse_items


class TestAsyncGeneratorFinalization:
    def test_async_generator_closed_on_aclose(self):
        """When stream_sse_items is aclosed, the wrapped async generator is also closed."""
        closed = False

        async def user_gen():
            nonlocal closed
            try:
                yield signals(status="hello")
                await asyncio.sleep(999)
                yield signals(status="never")
            finally:
                closed = True

        async def _run():
            stream = stream_sse_items(user_gen())
            item = await stream.__anext__()
            assert "hello" in item
            await stream.aclose()
            return closed

        assert asyncio.run(_run()) is True

    def test_normal_exhaustion_still_works(self):
        """If the generator exhausts normally, finalization still happens."""
        closed = False

        async def user_gen():
            nonlocal closed
            try:
                yield signals(status="only")
            finally:
                closed = True

        async def _run():
            stream = stream_sse_items(user_gen())
            items = []
            async for item in stream:
                items.append(item)
            return items, closed

        items, was_closed = asyncio.run(_run())
        assert len(items) == 1
        assert was_closed is True


class TestSyncGeneratorFinalization:
    def test_sync_generator_closed_on_aclose(self):
        """When stream_sse_items is aclosed, the wrapped sync generator is also closed."""
        closed = False

        def user_gen():
            nonlocal closed
            try:
                yield signals(status="hello")
                yield signals(status="world")
                yield signals(status="never")
            finally:
                closed = True

        async def _run():
            stream = stream_sse_items(user_gen())
            item = await stream.__anext__()
            assert "hello" in item
            await stream.aclose()
            return closed

        assert asyncio.run(_run()) is True


class TestRelayIntegration:
    def test_relay_stream_cleanup_on_disconnect(self):
        """Relay.stream() unsubscribes when stream_sse_items is closed (disconnect sim)."""
        relay = Relay()

        async def _run():
            stream = stream_sse_items(relay.stream())
            # Drive the generator chain so subscribe() runs inside relay.stream()
            next_task = asyncio.ensure_future(stream.__anext__())
            await asyncio.sleep(0.05)
            assert len(relay._subscribers) == 1
            # Cancel the pending __anext__ first, then close the stream
            next_task.cancel()
            try:
                await next_task
            except (asyncio.CancelledError, StopAsyncIteration):
                pass
            await stream.aclose()
            return len(relay._subscribers)

        count = asyncio.run(_run())
        assert count == 0
