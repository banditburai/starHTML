"""Tests for the Lifespan class and lifecycle management."""

import asyncio
from contextlib import asynccontextmanager

import pytest

from starhtml import StarHTML, TestClient
from starhtml.core import _run_handler


class TestRunHandler:
    def test_handler_no_params(self):
        called = []

        def handler():
            called.append("ok")

        asyncio.run(_run_handler(handler, app=None))
        assert called == ["ok"]

    def test_handler_receives_app(self):
        called = []

        def handler(app):
            called.append(app)

        sentinel = object()
        asyncio.run(_run_handler(handler, sentinel))
        assert called == [sentinel]

    def test_async_handler(self):
        called = []

        async def handler():
            called.append("async")

        asyncio.run(_run_handler(handler, app=None))
        assert called == ["async"]

    def test_async_handler_with_app(self):
        called = []

        async def handler(app):
            called.append(("async", app))

        sentinel = object()
        asyncio.run(_run_handler(handler, sentinel))
        assert called == [("async", sentinel)]

    def test_handler_with_unresolvable_forward_ref_annotation(self):
        """Handlers with string annotations naming a class not importable from
        their module must still dispatch — lifespan only needs param count, not
        type resolution. Regression: starimo's `on_startup(self, app: "Starlette")`
        triggered NameError because `Starlette` isn't imported in plugin.py."""
        called = []

        async def handler(app: "NotImportedAnywhere") -> None:  # noqa: F821
            called.append(app)

        sentinel = object()
        asyncio.run(_run_handler(handler, sentinel))
        assert called == [sentinel]


class TestLifespan:
    def test_empty_lifespan(self):
        app = StarHTML()
        with TestClient(app):
            pass

    def test_runs_startup_shutdown(self):
        events = []
        app = StarHTML(on_startup=[lambda: events.append("startup")], on_shutdown=[lambda: events.append("shutdown")])
        with TestClient(app):
            assert events == ["startup"]
        assert events == ["startup", "shutdown"]

    def test_ordering_with_user_lifespan(self):
        """Handlers run INSIDE user lifespan: enter -> startup -> yield -> shutdown -> exit."""
        events = []

        @asynccontextmanager
        async def user_lifespan(app):
            events.append("lifespan_enter")
            yield
            events.append("lifespan_exit")

        app = StarHTML(
            lifespan=user_lifespan,
            on_startup=[lambda: events.append("startup")],
            on_shutdown=[lambda: events.append("shutdown")],
        )
        with TestClient(app):
            assert events == ["lifespan_enter", "startup"]
        assert events == ["lifespan_enter", "startup", "shutdown", "lifespan_exit"]

    def test_without_user_lifespan(self):
        events = []
        app = StarHTML(
            on_startup=[lambda: events.append("startup")],
            on_shutdown=[lambda: events.append("shutdown")],
        )
        with TestClient(app):
            assert events == ["startup"]
        assert events == ["startup", "shutdown"]

    def test_handler_receives_app_param(self):
        received = []

        def on_startup(app):
            received.append(app)

        app = StarHTML(on_startup=[on_startup])
        with TestClient(app):
            pass
        assert len(received) == 1
        assert received[0] is app

    def test_append_after_creation(self):
        events = []
        app = StarHTML()
        app.add_lifecycle_handler("startup", lambda: events.append("dynamic_startup"))
        app.add_lifecycle_handler("shutdown", lambda: events.append("dynamic_shutdown"))

        with TestClient(app):
            assert events == ["dynamic_startup"]
        assert events == ["dynamic_startup", "dynamic_shutdown"]

    def test_on_event_decorator(self):
        events = []
        app = StarHTML()

        @app.on_event("startup")
        def on_startup():
            events.append("startup")

        @app.on_event("shutdown")
        def on_shutdown():
            events.append("shutdown")

        with TestClient(app):
            assert events == ["startup"]
        assert events == ["startup", "shutdown"]

    def test_async_startup_handler(self):
        events = []

        async def async_startup():
            events.append("async_startup")

        app = StarHTML(on_startup=[async_startup])
        with TestClient(app):
            assert events == ["async_startup"]

    def test_async_shutdown_handler(self):
        events = []

        async def async_shutdown():
            events.append("async_shutdown")

        app = StarHTML(on_shutdown=[async_shutdown])
        with TestClient(app):
            pass
        assert events == ["async_shutdown"]

    def test_async_handler_with_app_param(self):
        received = []

        async def async_startup(app):
            received.append(app)

        app = StarHTML(on_startup=[async_startup])
        with TestClient(app):
            pass
        assert len(received) == 1
        assert received[0] is app

    def test_mixed_sync_async_handlers(self):
        events = []

        def sync_handler():
            events.append("sync")

        async def async_handler():
            events.append("async")

        app = StarHTML(on_startup=[sync_handler, async_handler])
        with TestClient(app):
            assert events == ["sync", "async"]

    def test_startup_exception_propagates(self):
        class StartupError(Exception):
            pass

        def bad_startup():
            raise StartupError("startup failed")

        app = StarHTML(on_startup=[bad_startup])
        with pytest.raises(StartupError, match="startup failed"):
            with TestClient(app, raise_server_exceptions=True):
                pass

    def test_multiple_handlers_order_preserved(self):
        events = []
        app = StarHTML(
            on_startup=[
                lambda: events.append("first"),
                lambda: events.append("second"),
                lambda: events.append("third"),
            ],
            on_shutdown=[
                lambda: events.append("close_first"),
                lambda: events.append("close_second"),
            ],
        )
        with TestClient(app):
            assert events == ["first", "second", "third"]
        assert events == ["first", "second", "third", "close_first", "close_second"]
