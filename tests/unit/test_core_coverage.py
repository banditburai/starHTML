"""Tests to cover uncovered lines in starhtml/core.py.

Targets: datastar URL modes, after middleware, _add_route method-name inference,
register_package_static file serving, mount method, register_package,
_register_item dependencies, duplicate plugin skip, static_route, devtools_json.
"""

import tempfile
from pathlib import Path

from starlette.responses import PlainTextResponse
from starlette.testclient import TestClient

from starhtml import StarHTML
from starhtml.core import _register_item

# ---------------------------------------------------------------------------
# datastar URL configuration (lines 170, 174)
# ---------------------------------------------------------------------------


class TestDatastarURLConfig:
    def test_datastar_cdn_mode(self):
        """datastar='cdn' uses the CDN URL."""
        app = StarHTML(datastar="cdn")
        assert "cdn" in app._datastar_url.lower() or "datastar" in app._datastar_url

    def test_datastar_custom_url(self):
        """datastar=<custom string> uses that string as the URL."""
        app = StarHTML(datastar="https://example.com/my-datastar.js")
        assert app._datastar_url == "https://example.com/my-datastar.js"


# ---------------------------------------------------------------------------
# after middleware in _endp (lines 363-366)
# ---------------------------------------------------------------------------


class TestAfterMiddleware:
    def test_after_handler_receives_response(self):
        """After handlers receive the response and can inspect it."""
        seen_responses = []

        def after_handler(resp):
            seen_responses.append(resp)

        app = StarHTML(after=[after_handler])

        @app.route("/test")
        def handler():
            return "hello"

        client = TestClient(app)
        resp = client.get("/test")
        assert resp.status_code == 200
        assert len(seen_responses) == 1

    def test_after_handler_can_replace_response(self):
        """After handler returning a value replaces the response."""
        from starlette.responses import Response

        def after_handler(resp):
            return Response("replaced", status_code=200)

        app = StarHTML(after=[after_handler])

        @app.route("/test")
        def handler():
            return "original"

        client = TestClient(app)
        resp = client.get("/test")
        assert resp.status_code == 200
        assert "replaced" in resp.text

    def test_after_handler_with_request_param(self):
        """After handler can also receive the request."""
        seen = []

        def after_handler(resp, req):
            seen.append(req.url.path)

        app = StarHTML(after=[after_handler])

        @app.route("/check")
        def handler():
            return "ok"

        client = TestClient(app)
        client.get("/check")
        assert seen == ["/check"]


# ---------------------------------------------------------------------------
# _add_route: method-name inference and index path (lines 400, 406)
# ---------------------------------------------------------------------------


class TestAddRouteMethodInference:
    def test_function_named_as_http_method_infers_method(self):
        """A function named 'get' with an explicit path infers GET method."""
        app = StarHTML()

        # Must use _add_route directly with a module-level-like function
        # so nested_name returns just 'get'
        def get():
            return "items list"

        # Override __qualname__ to simulate a module-level function
        get.__qualname__ = "get"
        app._add_route(get, "/items", methods=None, name=None, include_in_schema=True, body_wrap=None)

        client = TestClient(app)
        resp = client.get("/items")
        assert resp.status_code == 200
        assert "items list" in resp.text

    def test_function_named_index_gets_root_path(self):
        """A function named 'index' gets '/' as its path when path is None."""
        app = StarHTML()

        def index():
            return "home"

        index.__qualname__ = "index"
        app._add_route(index, None, methods=None, name=None, include_in_schema=True, body_wrap=None)

        client = TestClient(app)
        resp = client.get("/")
        assert resp.status_code == 200
        assert "home" in resp.text

    def test_function_named_other_gets_function_name_path(self):
        """A function with non-method name and no path gets /funcname."""
        app = StarHTML()

        def about():
            return "about page"

        about.__qualname__ = "about"
        app._add_route(about, None, methods=None, name=None, include_in_schema=True, body_wrap=None)

        client = TestClient(app)
        resp = client.get("/about")
        assert resp.status_code == 200
        assert "about page" in resp.text


# ---------------------------------------------------------------------------
# register_package_static: file serving, traversal protection (lines 466-479)
# ---------------------------------------------------------------------------


class TestRegisterPackageStatic:
    def test_serves_existing_file(self):
        """Static file serving returns the file content."""
        with tempfile.TemporaryDirectory() as tmpdir:
            Path(tmpdir, "hello.txt").write_text("file content")

            app = StarHTML()
            # Clear previously registered packages to allow fresh registration
            app._registered_packages.clear()
            app.register_package_static("testpkg", tmpdir)

            client = TestClient(app)
            resp = client.get("/_pkg/testpkg/hello.txt")
            assert resp.status_code == 200
            assert resp.text == "file content"

    def test_returns_404_for_missing_file(self):
        """Static file serving returns 404 for nonexistent files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            app = StarHTML()
            app._registered_packages.clear()
            app.register_package_static("testpkg", tmpdir)

            client = TestClient(app)
            resp = client.get("/_pkg/testpkg/missing.txt")
            assert resp.status_code == 404

    def test_blocks_path_traversal(self):
        """Static file serving blocks directory traversal attempts."""
        with tempfile.TemporaryDirectory() as tmpdir:
            Path(tmpdir, "ok.txt").write_text("ok")

            app = StarHTML()
            app._registered_packages.clear()
            app.register_package_static("testpkg", tmpdir)

            client = TestClient(app)
            resp = client.get("/_pkg/testpkg/../../../etc/passwd")
            assert resp.status_code in (403, 404)


# ---------------------------------------------------------------------------
# mount method (lines 489-494)
# ---------------------------------------------------------------------------


class TestMount:
    def test_mount_inserts_before_catch_all(self):
        """Mounted app is inserted before the catch-all static route."""

        async def child_app(scope, receive, send):
            resp = PlainTextResponse("mounted")
            await resp(scope, receive, send)

        app = StarHTML(static_path=".")
        app.mount("/child", child_app)

        client = TestClient(app)
        resp = client.get("/child/")
        assert resp.status_code == 200
        assert resp.text == "mounted"

    def test_mount_appends_when_no_catch_all(self):
        """When there's no catch-all route, mount appends to the end."""

        async def child_app(scope, receive, send):
            resp = PlainTextResponse("appended")
            await resp(scope, receive, send)

        app = StarHTML()
        # Remove any routes with {ext:...} pattern
        app.router.routes = [r for r in app.router.routes if ".{ext:" not in getattr(r, "path", "")]
        app.mount("/api", child_app)

        client = TestClient(app)
        resp = client.get("/api/")
        assert resp.status_code == 200
        assert resp.text == "appended"


# ---------------------------------------------------------------------------
# register_package with static_path and hdrs (lines 501, 503)
# ---------------------------------------------------------------------------


class TestRegisterPackage:
    def test_register_package_with_hdrs_only(self):
        """register_package with hdrs but no static_path adds headers."""
        from starhtml.xtend import Script

        app = StarHTML()
        initial_count = len(app.hdrs)
        app.register_package("mypkg", hdrs=[Script("console.log('hi')")])
        assert len(app.hdrs) == initial_count + 1

    def test_register_package_with_static_path_and_hdrs(self):
        """register_package with both static_path and hdrs does both."""
        from starhtml.xtend import Script

        with tempfile.TemporaryDirectory() as tmpdir:
            app = StarHTML()
            app._registered_packages.clear()
            initial_count = len(app.hdrs)
            app.register_package("mypkg", static_path=tmpdir, hdrs=[Script("console.log('hi')")])
            assert len(app.hdrs) == initial_count + 1
            # Static route should exist
            paths = [getattr(r, "path", "") for r in app.routes]
            assert any("mypkg" in p for p in paths)


# ---------------------------------------------------------------------------
# _register_item dependencies (lines 519, 526-527)
# ---------------------------------------------------------------------------


class TestRegisterItemDependencies:
    def test_item_with_dependencies_registers_dep_static(self):
        """Items with get_dependencies() get their deps registered."""
        with tempfile.TemporaryDirectory() as tmpdir:
            dep_path = Path(tmpdir) / "dep_static"
            dep_path.mkdir()
            Path(dep_path, "lib.js").write_text("// lib")

            class ItemWithDeps:
                def get_package_name(self):
                    return "myitem"

                def get_static_path(self):
                    return None

                def get_headers(self, pkg_prefix):
                    return ()

                def get_dependencies(self):
                    return [("mydep", str(dep_path))]

            app = StarHTML()
            app._registered_packages.clear()
            _register_item(app, ItemWithDeps())
            assert "mydep" in app._registered_packages


# ---------------------------------------------------------------------------
# Duplicate plugin skip in register (line 570)
# ---------------------------------------------------------------------------


class TestDuplicatePluginSkip:
    def test_registering_same_plugin_twice_skips_duplicate(self):
        """Registering the same plugin twice does not duplicate it."""
        from starhtml.plugins import persist

        app = StarHTML()
        app.register(persist)
        plugin_count_after_first = len(app._registered_plugins)

        app.register(persist)
        assert len(app._registered_plugins) == plugin_count_after_first


# ---------------------------------------------------------------------------
# static_route method (lines 617-619)
# ---------------------------------------------------------------------------


class TestStaticRoute:
    def test_static_route_serves_files(self):
        """static_route creates a route that serves files with a given extension."""
        with tempfile.TemporaryDirectory() as tmpdir:
            Path(tmpdir, "data.json").write_text('{"key": "value"}')

            app = StarHTML()
            app.static_route(ext=".json", static_path=tmpdir)

            client = TestClient(app)
            resp = client.get("/data.json")
            assert resp.status_code == 200
            assert "key" in resp.text


# ---------------------------------------------------------------------------
# devtools_json method (lines 628-635)
# ---------------------------------------------------------------------------


class TestDevtoolsJson:
    def test_devtools_json_returns_workspace_info(self):
        """devtools_json endpoint returns workspace root and uuid."""
        app = StarHTML()
        app.devtools_json(path="/my/project", uuid="test-uuid-123")

        client = TestClient(app)
        resp = client.get("/.well-known/appspecific/com.chrome.devtools.json")
        assert resp.status_code == 200
        data = resp.json()
        assert data["workspace"]["root"] == "/my/project"
        assert data["workspace"]["uuid"] == "test-uuid-123"

    def test_devtools_json_defaults(self):
        """devtools_json generates defaults when path/uuid not provided."""
        app = StarHTML()
        app.devtools_json()

        client = TestClient(app)
        resp = client.get("/.well-known/appspecific/com.chrome.devtools.json")
        assert resp.status_code == 200
        data = resp.json()
        assert "root" in data["workspace"]
        assert "uuid" in data["workspace"]


# ---------------------------------------------------------------------------
# set_devtools_context in _endp (line 350)
# ---------------------------------------------------------------------------


class TestDevtoolsContext:
    def test_devtools_flag_sets_context(self):
        """When devtools=True, requests still work (context is set internally)."""
        # We just verify the devtools path doesn't break request handling
        app = StarHTML(devtools=True)

        @app.route("/test")
        def handler():
            return "with devtools"

        client = TestClient(app)
        resp = client.get("/test")
        assert resp.status_code == 200
        assert "with devtools" in resp.text


# ---------------------------------------------------------------------------
# register import map for non-plugin items (line 595)
# ---------------------------------------------------------------------------


class TestRegisterImportMap:
    def test_item_with_import_map_merges_into_headers(self):
        """Items providing get_import_map() have their mappings merged."""

        class ItemWithImportMap:
            def get_package_name(self):
                return "mapped"

            def get_static_path(self):
                return None

            def get_headers(self, pkg_prefix):
                return ()

            def get_import_map(self, prefix):
                return {"my-lib": f"{prefix}/mapped/my-lib.js"}

        app = StarHTML()
        app.register(ItemWithImportMap())

        # Check the import map header contains our mapping
        import_maps = [h for h in app.hdrs if getattr(h, "attrs", {}).get("type") == "importmap"]
        assert len(import_maps) == 1
        content = str(import_maps[0])
        assert "my-lib" in content
