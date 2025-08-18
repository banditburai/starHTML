"""Test bodykw parameter handling with live reload."""

from src.starhtml.starapp import star_app


class TestBodyKw:
    def test_bodykw_without_live(self):
        app, _ = star_app(bodykw={"cls": "test-class"})
        assert app.bodykw == {"cls": "test-class"}

    def test_bodykw_with_live(self):
        app, _ = star_app(live=True, bodykw={"cls": "test-class"})
        assert app.bodykw == {"cls": "test-class"}

    def test_complex_bodykw_with_live(self):
        attrs = {"cls": "min-h-screen bg-background", "id": "app-body", "data-theme": "light"}
        app, _ = star_app(live=True, bodykw=attrs)
        assert app.bodykw == attrs

    def test_empty_bodykw(self):
        app1, _ = star_app(bodykw={})
        app2, _ = star_app(live=True, bodykw={})
        assert app1.bodykw == app2.bodykw == {}

    def test_none_bodykw(self):
        app1, _ = star_app()
        app2, _ = star_app(live=True)
        assert app1.bodykw == app2.bodykw == {}

    def test_bodykw_with_debug(self):
        app, _ = star_app(live=True, debug=True, bodykw={"cls": "custom-body-class"})
        assert app.bodykw == {"cls": "custom-body-class"}
