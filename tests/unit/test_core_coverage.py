"""Behavior tests for less-trafficked StarHTML core wiring:

datastar URL modes, after-middleware, register_package_static (incl. path
traversal), mount, register_package, static_route, devtools_json, devtools
context, and import-map merging.

The tests here go through public API and HTTP, not through line-numbered
private branches. If you find yourself reaching for ``app._registered_*``
or ``app.router.routes = [...]``, prefer expressing the contract through
a request instead.
"""

import tempfile
from pathlib import Path

from starlette.responses import PlainTextResponse
from starlette.testclient import TestClient

from starhtml import StarHTML


class TestDatastarURLConfig:
    def test_datastar_cdn_mode_emits_cdn_script(self):
        app = StarHTML(datastar="cdn")
        hdrs_html = "".join(str(h) for h in app.hdrs)
        assert "datastar" in hdrs_html.lower()
        assert "cdn" in hdrs_html.lower() or "https://" in hdrs_html

    def test_datastar_custom_url_emits_that_script(self):
        app = StarHTML(datastar="https://example.com/my-datastar.js")
        hdrs_html = "".join(str(h) for h in app.hdrs)
        assert "https://example.com/my-datastar.js" in hdrs_html


class TestAfterMiddleware:
    def test_after_handler_receives_response(self):
        seen = []
        app = StarHTML(after=[lambda resp: seen.append(resp)])

        @app.route("/test")
        def handler():
            return "hello"

        assert TestClient(app).get("/test").status_code == 200
        assert len(seen) == 1

    def test_after_handler_can_replace_response(self):
        from starlette.responses import Response

        app = StarHTML(after=[lambda resp: Response("replaced", status_code=200)])

        @app.route("/test")
        def handler():
            return "original"

        assert "replaced" in TestClient(app).get("/test").text

    def test_after_handler_can_inspect_request(self):
        seen = []
        app = StarHTML(after=[lambda resp, req: seen.append(req.url.path)])

        @app.route("/check")
        def handler():
            return "ok"

        TestClient(app).get("/check")
        assert seen == ["/check"]


class TestRegisterPackageStatic:
    def test_serves_existing_file(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            Path(tmpdir, "hello.txt").write_text("file content")
            app = StarHTML()
            app.register_package_static("testpkg", tmpdir)
            resp = TestClient(app).get("/_pkg/testpkg/hello.txt")
            assert resp.status_code == 200
            assert resp.text == "file content"

    def test_returns_404_for_missing_file(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            app = StarHTML()
            app.register_package_static("testpkg", tmpdir)
            assert TestClient(app).get("/_pkg/testpkg/missing.txt").status_code == 404

    def test_blocks_path_traversal(self):
        """A `..`-laden URL must not escape the package root.

        We pin both common rejection codes (403/404) since the precise
        status depends on whether Starlette or our own check refuses
        first; either is correct as long as the file is not served.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            Path(tmpdir, "ok.txt").write_text("ok")
            app = StarHTML()
            app.register_package_static("testpkg", tmpdir)
            resp = TestClient(app).get("/_pkg/testpkg/../../../etc/passwd")
            assert resp.status_code in (403, 404)
            assert "root:" not in resp.text


class TestMount:
    def test_mount_inserts_before_catch_all_static(self):
        async def child_app(scope, receive, send):
            await PlainTextResponse("mounted")(scope, receive, send)

        app = StarHTML(static_path=".")
        app.mount("/child", child_app)
        resp = TestClient(app).get("/child/")
        assert resp.status_code == 200
        assert resp.text == "mounted"

    def test_mounted_app_serves_at_prefix(self):
        async def child_app(scope, receive, send):
            await PlainTextResponse("api")(scope, receive, send)

        app = StarHTML()
        app.mount("/api", child_app)
        resp = TestClient(app).get("/api/")
        assert resp.status_code == 200
        assert resp.text == "api"


class TestRegisterPackage:
    def test_register_package_with_hdrs_emits_script(self):
        from starhtml.xtend import Script

        app = StarHTML()
        app.register_package("mypkg", hdrs=[Script("console.log('hi')")])
        hdrs_html = "".join(str(h) for h in app.hdrs)
        assert "console.log('hi')" in hdrs_html

    def test_register_package_with_static_path_serves_files(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            Path(tmpdir, "lib.js").write_text("// mypkg lib")
            app = StarHTML()
            app.register_package("mypkg", static_path=tmpdir)
            resp = TestClient(app).get("/_pkg/mypkg/lib.js")
            assert resp.status_code == 200
            assert "mypkg lib" in resp.text


class TestRegisterItemDependencies:
    def test_dependency_static_files_are_servable(self):
        """An item that declares a dependency makes that dep's static path
        reachable through the package URL prefix."""
        with tempfile.TemporaryDirectory() as tmpdir:
            dep_root = Path(tmpdir) / "dep_static"
            dep_root.mkdir()
            Path(dep_root, "lib.js").write_text("// dep lib")

            class ItemWithDeps:
                def get_package_name(self):
                    return "myitem"

                def get_static_path(self):
                    return None

                def get_headers(self, pkg_prefix):
                    return ()

                def get_dependencies(self):
                    return [("mydep", str(dep_root))]

            app = StarHTML()
            app.register(ItemWithDeps())
            resp = TestClient(app).get("/_pkg/mydep/lib.js")
            assert resp.status_code == 200
            assert "dep lib" in resp.text


class TestDuplicatePluginSkip:
    def test_re_registering_does_not_double_emit_headers(self):
        """Registering the same plugin twice must not duplicate its <script> tag."""
        from starhtml.plugins import persist

        app = StarHTML()
        app.register(persist)
        app.register(persist)
        hdrs_html = "".join(str(h) for h in app.hdrs)
        # The plugin's script URL should appear at most once.
        assert hdrs_html.count("/persist.js") <= 1


class TestStaticRoute:
    def test_static_route_serves_files(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            Path(tmpdir, "data.json").write_text('{"key": "value"}')
            app = StarHTML()
            app.static_route(ext=".json", static_path=tmpdir)
            resp = TestClient(app).get("/data.json")
            assert resp.status_code == 200
            assert "key" in resp.text


class TestDevtoolsJson:
    def test_devtools_json_returns_workspace_info(self):
        app = StarHTML()
        app.devtools_json(path="/my/project", uuid="test-uuid-123")
        data = TestClient(app).get("/.well-known/appspecific/com.chrome.devtools.json").json()
        assert data["workspace"]["root"] == "/my/project"
        assert data["workspace"]["uuid"] == "test-uuid-123"

    def test_devtools_json_defaults(self):
        app = StarHTML()
        app.devtools_json()
        data = TestClient(app).get("/.well-known/appspecific/com.chrome.devtools.json").json()
        assert "root" in data["workspace"]
        assert "uuid" in data["workspace"]


class TestDevtoolsContext:
    def test_devtools_does_not_break_request_handling(self):
        app = StarHTML(devtools=True)

        @app.route("/test")
        def handler():
            return "with devtools"

        resp = TestClient(app).get("/test")
        assert resp.status_code == 200
        assert "with devtools" in resp.text


class TestRegisterImportMap:
    def test_item_with_import_map_appears_in_html(self):
        """Items providing get_import_map() merge their mappings into the HTML import map."""

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

        # An importmap header is registered with the item's mapping inside it.
        hdrs_html = "".join(str(h) for h in app.hdrs)
        assert 'type="importmap"' in hdrs_html or "type='importmap'" in hdrs_html
        assert "my-lib" in hdrs_html
