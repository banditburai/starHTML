from contextlib import asynccontextmanager

from starhtml import StarHTML, TestClient


def test_constructor_lifecycle_hooks_run():
    events = []

    def on_startup():
        events.append("startup")

    def on_shutdown():
        events.append("shutdown")

    app = StarHTML(on_startup=[on_startup], on_shutdown=[on_shutdown])

    with TestClient(app):
        assert events == ["startup"]

    assert events == ["startup", "shutdown"]


def test_on_event_decorator():
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


def test_lifespan_wraps_hooks_in_defined_order():
    events = []

    @asynccontextmanager
    async def lifespan(app):
        events.append("lifespan_enter")
        yield
        events.append("lifespan_exit")

    app = StarHTML(lifespan=lifespan, on_startup=[lambda: events.append("startup")])

    @app.on_event("shutdown")
    def on_shutdown():
        events.append("shutdown")

    with TestClient(app):
        assert events == ["lifespan_enter", "startup"]

    assert events == ["lifespan_enter", "startup", "shutdown", "lifespan_exit"]
