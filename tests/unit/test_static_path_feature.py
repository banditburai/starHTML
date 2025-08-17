"""Tests for the static_path parameter in StarHTML."""

import shutil
from pathlib import Path

import pytest

from starhtml import Client, StarHTML, star_app


class TestStaticPathFeature:
    """Test the new static_path parameter functionality."""

    @pytest.fixture(autouse=True)
    def setup_static_files(self):
        """Set up test static files."""
        test_dir = Path("test_static_feature")
        if test_dir.exists():
            shutil.rmtree(test_dir)

        test_dir.mkdir()
        (test_dir / "root.css").write_text("/* Root CSS */")

        css_dir = test_dir / "css"
        css_dir.mkdir()
        (css_dir / "style.css").write_text("/* Nested CSS */")

        deep_dir = test_dir / "assets" / "images"
        deep_dir.mkdir(parents=True)
        (deep_dir / "logo.png").write_bytes(b"PNG fake content")

        yield

        # Cleanup
        if test_dir.exists():
            shutil.rmtree(test_dir)

    def test_starhtml_direct_static_path(self):
        """Test StarHTML direct instantiation with static_path."""
        app = StarHTML(static_path="test_static_feature")

        # Check that static route is registered
        routes = [str(r.path) for r in app.routes]
        assert "/{fname:path}.{ext:static}" in routes

        # Test file serving
        client = Client(app)

        # Root level file
        response = client.get("/root.css")
        assert response.status_code == 200
        assert "Root CSS" in response.text

        # Nested file
        response = client.get("/css/style.css")
        assert response.status_code == 200
        assert "Nested CSS" in response.text

        # Deep nested file
        response = client.get("/assets/images/logo.png")
        assert response.status_code == 200
        assert b"PNG fake content" in response.content

    def test_star_app_static_path(self):
        """Test star_app factory with static_path."""
        app, route = star_app(static_path="test_static_feature")

        # Check that static route is registered
        routes = [str(r.path) for r in app.routes]
        assert "/{fname:path}.{ext:static}" in routes

        # Test file serving
        client = Client(app)

        response = client.get("/root.css")
        assert response.status_code == 200

        response = client.get("/css/style.css")
        assert response.status_code == 200

    def test_manual_static_route_exts(self):
        """Test manual static_route_exts call."""
        app = StarHTML()
        app.static_route_exts(static_path="test_static_feature")

        # Check that static route is registered
        routes = [str(r.path) for r in app.routes]
        assert "/{fname:path}.{ext:static}" in routes

        # Test file serving
        client = Client(app)

        response = client.get("/root.css")
        assert response.status_code == 200

    def test_no_static_path(self):
        """Test that without static_path, no static route is added."""
        app = StarHTML()

        # Check that static route is NOT registered
        routes = [str(r.path) for r in app.routes]
        assert "/{fname:path}.{ext:static}" not in routes

    def test_nonexistent_file_404(self):
        """Test that nonexistent files return 404."""
        app = StarHTML(static_path="test_static_feature")
        client = Client(app)

        response = client.get("/nonexistent.css")
        assert response.status_code == 404

        response = client.get("/css/nonexistent.css")
        assert response.status_code == 404

    def test_file_without_extension(self):
        """Test that files without recognized extensions are not served."""
        app = StarHTML(static_path="test_static_feature")
        client = Client(app)

        # Create a file without extension
        (Path("test_static_feature") / "noext").write_text("No extension")

        response = client.get("/noext")
        assert response.status_code == 404  # Should not match the static route pattern

    def test_live_reload_with_static_path(self):
        """Test that live reload mode works with static_path."""
        app, route = star_app(static_path="test_static_feature", live=True)

        # Check that static route is registered even with live reload
        routes = [str(r.path) for r in app.routes]
        assert "/{fname:path}.{ext:static}" in routes

        # Test file serving
        client = Client(app)
        response = client.get("/root.css")
        assert response.status_code == 200
