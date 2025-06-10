"""Basic tests for StarHTML functionality."""


def test_starhtml_imports():
    """Test that StarHTML can be imported without errors."""
    from starhtml import star_app

    assert star_app is not None


def test_app_creation():
    """Test that a basic StarHTML app can be created."""
    from starhtml import star_app

    app, rt = star_app()
    assert app is not None
    assert rt is not None
    assert hasattr(app, "hdrs")
    assert len(app.hdrs) > 0  # Should have default headers


def test_route_creation():
    """Test that routes can be created."""
    from starhtml import H1, Div, star_app

    app, rt = star_app()

    @rt("/")
    def get():
        return Div(H1("Test"))

    # Should not raise any errors
    assert get is not None


def test_components_import():
    """Test that HTML components can be imported."""
    from starhtml import H1, Button, Div, P

    # Should be able to create components
    div = Div("test")
    h1 = H1("title")
    p = P("paragraph")
    button = Button("click me")

    assert div is not None
    assert h1 is not None
    assert p is not None
    assert button is not None
