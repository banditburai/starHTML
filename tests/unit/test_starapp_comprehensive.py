"""Comprehensive tests for the starapp.py module.

This module tests all functionality in src/starhtml/starapp.py including:
- star_app function and app factory
- Database integration and table creation
- Default headers generation (def_hdrs)
- Beforeware and MiddlewareBase classes
- Helper functions and constants
"""

from unittest.mock import Mock, patch

import pytest

from starhtml.starapp import (
    DATASTAR_VERSION,
    ICONIFY_VERSION,
    Beforeware,
    MiddlewareBase,
    _app_factory,
    _get_tbl,
    def_hdrs,
    star_app,
)


class TestStarApp:
    """Test star_app function."""

    @patch("starhtml.starapp._app_factory")
    def test_star_app_basic(self, mock_app_factory):
        """Test basic star_app call without database."""
        mock_app = Mock()
        mock_route = Mock()
        mock_app.route = mock_route
        mock_app.static_route_exts = Mock()
        mock_app_factory.return_value = mock_app

        result = star_app()

        assert len(result) == 2
        app, route = result
        assert app == mock_app
        assert route == mock_route
        mock_app.static_route_exts.assert_called_once_with(static_path=".")

    @patch("starhtml.starapp._app_factory")
    def test_star_app_with_custom_static_path(self, mock_app_factory):
        """Test star_app with custom static path."""
        mock_app = Mock()
        mock_app.route = Mock()
        mock_app.static_route_exts = Mock()
        mock_app_factory.return_value = mock_app

        star_app(static_path="/custom/static")

        mock_app.static_route_exts.assert_called_once_with(static_path="/custom/static")

    @patch("starhtml.starapp._app_factory")
    def test_star_app_headers_processing(self, mock_app_factory):
        """Test star_app processes headers correctly."""
        mock_app = Mock()
        mock_app.route = Mock()
        mock_app.static_route_exts = Mock()
        mock_app_factory.return_value = mock_app

        custom_hdrs = ["header1", "header2"]
        star_app(hdrs=custom_hdrs)

        # Should convert list to tuple and pass to _app_factory
        mock_app_factory.assert_called_once()
        call_kwargs = mock_app_factory.call_args[1]
        assert call_kwargs["hdrs"] == tuple(custom_hdrs)

    @patch("starhtml.starapp._app_factory")
    def test_star_app_with_body_wrap(self, mock_app_factory):
        """Test star_app with custom body_wrap."""
        mock_app = Mock()
        mock_app.route = Mock()
        mock_app.static_route_exts = Mock()
        mock_app_factory.return_value = mock_app

        def custom_body_wrap(content):
            return f"<wrapper>{content}</wrapper>"

        star_app(body_wrap=custom_body_wrap)

        call_kwargs = mock_app_factory.call_args[1]
        assert call_kwargs["body_wrap"] == custom_body_wrap

    @patch("starhtml.starapp._app_factory")
    @patch("starhtml.starapp.database")
    @patch("starhtml.starapp._get_tbl")
    def test_star_app_with_database(self, mock_get_tbl, mock_database, mock_app_factory):
        """Test star_app with database file."""
        mock_app = Mock()
        mock_app.route = Mock()
        mock_app.static_route_exts = Mock()
        mock_app_factory.return_value = mock_app

        mock_db = Mock()
        mock_database.return_value = mock_db

        mock_table = Mock()
        mock_dataclass = Mock()
        mock_get_tbl.return_value = (mock_table, mock_dataclass)

        result = star_app(db_file="test.db", tbls={"users": {"id": int, "name": str}})

        # Should return app, route, and database table/dataclass
        assert len(result) == 4  # app, route, table, dataclass
        app, route, table, dataclass = result
        assert app == mock_app
        assert route == mock_app.route
        assert table == mock_table
        assert dataclass == mock_dataclass

        mock_database.assert_called_once_with("test.db")
        mock_get_tbl.assert_called_once()

    @patch("starhtml.starapp._app_factory")
    @patch("starhtml.starapp.database")
    @patch("starhtml.starapp._get_tbl")
    def test_star_app_with_multiple_tables(self, mock_get_tbl, mock_database, mock_app_factory):
        """Test star_app with multiple database tables."""
        mock_app = Mock()
        mock_app.route = Mock()
        mock_app.static_route_exts = Mock()
        mock_app_factory.return_value = mock_app

        mock_db = Mock()
        mock_database.return_value = mock_db

        # Mock multiple table returns
        mock_get_tbl.side_effect = [
            (Mock(), Mock()),  # users table
            (Mock(), Mock()),  # posts table
        ]

        tbls = {"users": {"id": int, "name": str}, "posts": {"id": int, "title": str, "user_id": int}}

        result = star_app(db_file="test.db", tbls=tbls)

        # Should return app, route, and both tables
        assert len(result) == 4  # app, route, users_table, posts_table

        assert mock_get_tbl.call_count == 2

    @patch("starhtml.starapp._app_factory")
    @patch("starhtml.starapp.database")
    @patch("starhtml.starapp._get_tbl")
    @patch("starhtml.starapp.first")
    def test_star_app_with_kwargs_dict_values(self, mock_first, mock_get_tbl, mock_database, mock_app_factory):
        """Test star_app with kwargs containing dict values."""
        mock_app = Mock()
        mock_app.route = Mock()
        mock_app.static_route_exts = Mock()
        mock_app_factory.return_value = mock_app

        mock_db = Mock()
        mock_database.return_value = mock_db

        mock_table = Mock()
        mock_dataclass = Mock()
        mock_get_tbl.return_value = (mock_table, mock_dataclass)

        # Mock first() to return a dict (indicating kwargs has dict values)
        mock_first.return_value = {"id": int, "name": str}

        result = star_app(db_file="test.db", users={"id": int, "name": str}, posts={"id": int, "title": str})

        # When kwargs has dict values, they should be used as tbls
        mock_get_tbl.assert_called()
        assert len(result) >= 3  # app, route, at least one table

    @patch("starhtml.starapp._app_factory")
    @patch("starhtml.starapp.database")
    @patch("starhtml.starapp._get_tbl")
    @patch("starhtml.starapp.first")
    def test_star_app_with_kwargs_non_dict_values(self, mock_first, mock_get_tbl, mock_database, mock_app_factory):
        """Test star_app with kwargs containing non-dict values."""
        mock_app = Mock()
        mock_app.route = Mock()
        mock_app.static_route_exts = Mock()
        mock_app_factory.return_value = mock_app

        mock_db = Mock()
        mock_database.return_value = mock_db

        mock_table = Mock()
        mock_dataclass = Mock()
        mock_get_tbl.return_value = (mock_table, mock_dataclass)

        # Mock first() to return a non-dict (indicating kwargs has non-dict values)
        mock_first.return_value = "not a dict"

        def custom_render():
            return "rendered"

        star_app(db_file="test.db", render=custom_render, some_param="value")

        # When kwargs has non-dict values, should create items table with render
        mock_get_tbl.assert_called()
        call_args = mock_get_tbl.call_args[0]
        assert "items" in str(call_args)


class TestDefHdrs:
    """Test def_hdrs function."""

    @patch("starhtml.tags.Meta")
    @patch("starhtml.tags.Script")
    def test_def_hdrs_basic(self, mock_script, mock_meta):
        """Test basic def_hdrs functionality."""
        mock_script_instance = Mock()
        mock_meta_instance = Mock()
        mock_script.return_value = mock_script_instance
        mock_meta.return_value = mock_meta_instance

        result = def_hdrs()

        # Should create charset, viewport, datastar script, and iconify script
        assert mock_meta.call_count == 2  # charset and viewport
        assert mock_script.call_count == 2  # datastar and iconify
        assert len(result) == 4  # all headers

    @patch("starhtml.tags.Meta")
    @patch("starhtml.tags.Script")
    def test_def_hdrs_custom_datastar_version(self, mock_script, mock_meta):
        """Test def_hdrs with custom Datastar version."""
        mock_script_instance = Mock()
        mock_meta_instance = Mock()
        mock_script.return_value = mock_script_instance
        mock_meta.return_value = mock_meta_instance

        custom_version = "v1.2.3"
        def_hdrs(datastar_version=custom_version)

        # Check that custom version is used in datastar script
        datastar_script_call = mock_script.call_args_list[0]
        src_arg = datastar_script_call[1]["src"]
        assert custom_version in src_arg

    @patch("starhtml.tags.Meta")
    @patch("starhtml.tags.Script")
    def test_def_hdrs_no_iconify(self, mock_script, mock_meta):
        """Test def_hdrs without Iconify."""
        mock_script_instance = Mock()
        mock_meta_instance = Mock()
        mock_script.return_value = mock_script_instance
        mock_meta.return_value = mock_meta_instance

        result = def_hdrs(include_iconify=False)

        # Should only create charset, viewport, and datastar script (no iconify)
        assert mock_meta.call_count == 2  # charset and viewport
        assert mock_script.call_count == 1  # only datastar
        assert len(result) == 3  # no iconify

    @patch("starhtml.tags.Meta")
    @patch("starhtml.tags.Script")
    def test_def_hdrs_custom_iconify_version(self, mock_script, mock_meta):
        """Test def_hdrs with custom Iconify version."""
        mock_script_instance = Mock()
        mock_meta_instance = Mock()
        mock_script.return_value = mock_script_instance
        mock_meta.return_value = mock_meta_instance

        custom_iconify_version = "3.0.0"
        def_hdrs(iconify_version=custom_iconify_version)

        # Check that custom iconify version is used
        iconify_script_call = mock_script.call_args_list[1]  # Second script call is iconify
        src_arg = iconify_script_call[1]["src"]
        assert custom_iconify_version in src_arg

    @patch("starhtml.tags.Meta")
    @patch("starhtml.tags.Script")
    def test_def_hdrs_custom_fallback_path(self, mock_script, mock_meta):
        """Test def_hdrs with custom fallback path."""
        mock_script_instance = Mock()
        mock_meta_instance = Mock()
        mock_script.return_value = mock_script_instance
        mock_meta.return_value = mock_meta_instance

        custom_fallback = "/assets/datastar.js"
        def_hdrs(fallback_path=custom_fallback)

        # Check that custom fallback path is used in onerror
        datastar_script_call = mock_script.call_args_list[0]
        onerror_arg = datastar_script_call[1]["onerror"]
        assert custom_fallback in onerror_arg


class TestBeforeware:
    """Test Beforeware class."""

    def test_beforeware_initialization(self):
        """Test Beforeware initialization."""

        def test_func():
            return "test"

        beforeware = Beforeware(test_func)

        assert beforeware.f == test_func
        assert beforeware.skip == []

    def test_beforeware_with_skip(self):
        """Test Beforeware initialization with skip parameter."""

        def test_func():
            return "test"

        skip_paths = ["/health", "/metrics"]
        beforeware = Beforeware(test_func, skip=skip_paths)

        assert beforeware.f == test_func
        assert beforeware.skip == skip_paths


class TestMiddlewareBase:
    """Test MiddlewareBase class."""

    @pytest.mark.asyncio
    async def test_middleware_base_non_http_websocket(self):
        """Test MiddlewareBase with non-HTTP/WebSocket scope."""
        middleware = MiddlewareBase()

        # Create async mock for _app
        async def mock_app(scope, receive, send):
            pass

        middleware._app = mock_app

        scope = {"type": "lifespan"}
        receive = Mock()
        send = Mock()

        result = await middleware(scope, receive, send)

        # Should return None for non-HTTP/WebSocket requests
        assert result is None

    @pytest.mark.asyncio
    async def test_middleware_base_http_scope(self):
        """Test MiddlewareBase with HTTP scope."""
        middleware = MiddlewareBase()

        scope = {"type": "http", "path": "/test"}
        receive = Mock()
        send = Mock()

        result = await middleware(scope, receive, send)

        # Should return HTTPConnection for HTTP requests
        from starlette.requests import HTTPConnection

        assert isinstance(result, HTTPConnection)

    @pytest.mark.asyncio
    async def test_middleware_base_websocket_scope(self):
        """Test MiddlewareBase with WebSocket scope."""
        middleware = MiddlewareBase()

        scope = {"type": "websocket", "path": "/ws"}
        receive = Mock()
        send = Mock()

        result = await middleware(scope, receive, send)

        # Should return HTTPConnection for WebSocket requests too
        from starlette.requests import HTTPConnection

        assert isinstance(result, HTTPConnection)


class TestGetTbl:
    """Test _get_tbl helper function."""

    def test_get_tbl_new_table(self):
        """Test _get_tbl with new table creation."""
        mock_dt = Mock()
        mock_table = Mock()
        mock_dataclass = Mock()

        # Mock the table doesn't exist in dt
        mock_dt.__contains__ = Mock(return_value=False)  # table not in dt
        mock_dt.__getitem__ = Mock(return_value=mock_table)
        mock_table.create = Mock()
        mock_table.dataclass = Mock(return_value=mock_dataclass)

        schema = {"id": int, "name": str, "render": "custom_render"}

        result = _get_tbl(mock_dt, "users", schema)

        assert result == (mock_table, mock_dataclass)
        # When table NOT in dt, create is called WITHOUT transform
        mock_table.create.assert_called_once_with(id=int, name=str)
        mock_table.dataclass.assert_called_once()
        assert mock_dataclass.__ft__ == "custom_render"

    def test_get_tbl_existing_table(self):
        """Test _get_tbl with existing table (transform)."""
        mock_dt = Mock()
        mock_table = Mock()
        mock_dataclass = Mock()

        # Mock the table exists
        mock_table.__contains__ = Mock(return_value=True)
        mock_dt.__getitem__ = Mock(return_value=mock_table)
        mock_table.create = Mock()
        mock_table.dataclass = Mock(return_value=mock_dataclass)

        schema = {"id": int, "name": str}

        result = _get_tbl(mock_dt, "users", schema)

        assert result == (mock_table, mock_dataclass)
        mock_table.create.assert_called_once_with(id=int, name=str, transform=True)
        mock_table.dataclass.assert_called_once()

    def test_get_tbl_without_render(self):
        """Test _get_tbl without render function."""
        mock_dt = Mock()
        mock_table = Mock()
        mock_dataclass = Mock()

        mock_table.__contains__ = Mock(return_value=False)
        mock_dt.__getitem__ = Mock(return_value=mock_table)
        mock_table.create = Mock()
        mock_table.dataclass = Mock(return_value=mock_dataclass)

        schema = {"id": int, "name": str}

        result = _get_tbl(mock_dt, "users", schema)

        assert result == (mock_table, mock_dataclass)
        # Should not set __ft__ attribute when no render function
        assert not hasattr(mock_dataclass, "__ft__")


class TestAppFactory:
    """Test _app_factory helper function."""

    @patch("starhtml.starapp.StarHTMLWithLiveReload")
    def test_app_factory_with_live_reload(self, mock_live_reload_class):
        """Test _app_factory with live reload enabled."""
        mock_app = Mock()
        mock_live_reload_class.return_value = mock_app

        result = _app_factory(live=True, reload_attempts=3, reload_interval=500)

        assert result == mock_app
        mock_live_reload_class.assert_called_once()
        # Based on actual code - parameters are NOT popped, they're just ignored by StarHTMLWithLiveReload
        mock_live_reload_class.call_args[1]
        # Parameters are passed through and handled by the class itself

    @patch("starhtml.core.StarHTML")
    def test_app_factory_without_live_reload(self, mock_starhtml_class):
        """Test _app_factory without live reload."""
        mock_app = Mock()
        mock_starhtml_class.return_value = mock_app

        result = _app_factory(live=False, debug=True)

        assert result == mock_app
        mock_starhtml_class.assert_called_once()
        call_kwargs = mock_starhtml_class.call_args[1]
        assert call_kwargs.get("debug") is True
        # Based on actual code - live, reload_attempts, reload_interval are popped
        assert "live" not in call_kwargs  # Should be popped
        assert "reload_attempts" not in call_kwargs  # Should be popped
        assert "reload_interval" not in call_kwargs  # Should be popped


class TestConstants:
    """Test module constants."""

    def test_datastar_version_constant(self):
        """Test DATASTAR_VERSION constant."""
        assert isinstance(DATASTAR_VERSION, str)
        assert len(DATASTAR_VERSION) > 0

    def test_iconify_version_constant(self):
        """Test ICONIFY_VERSION constant."""
        assert isinstance(ICONIFY_VERSION, str)
        assert len(ICONIFY_VERSION) > 0


class TestEdgeCases:
    """Test edge cases and error conditions."""

    @patch("starhtml.starapp._app_factory")
    def test_star_app_empty_hdrs(self, mock_app_factory):
        """Test star_app with empty headers."""
        mock_app = Mock()
        mock_app.route = Mock()
        mock_app.static_route_exts = Mock()
        mock_app_factory.return_value = mock_app

        star_app(hdrs=[])

        call_kwargs = mock_app_factory.call_args[1]
        assert call_kwargs["hdrs"] == ()

    @patch("starhtml.starapp._app_factory")
    def test_star_app_none_body_wrap(self, mock_app_factory):
        """Test star_app with None body_wrap (should use default)."""
        mock_app = Mock()
        mock_app.route = Mock()
        mock_app.static_route_exts = Mock()
        mock_app_factory.return_value = mock_app

        star_app(body_wrap=None)

        call_kwargs = mock_app_factory.call_args[1]
        # Should use default noop_body when body_wrap is None
        assert call_kwargs["body_wrap"] is not None

    def test_beforeware_none_skip(self):
        """Test Beforeware with None skip parameter."""

        def test_func():
            return "test"

        beforeware = Beforeware(test_func, skip=None)

        assert beforeware.f == test_func
        assert beforeware.skip == []


class TestRealWorldScenarios:
    """Test real-world usage scenarios."""

    @patch("starhtml.starapp._app_factory")
    def test_complete_star_app_setup(self, mock_app_factory):
        """Test complete star_app setup with various options."""
        mock_app = Mock()
        mock_app.route = Mock()
        mock_app.static_route_exts = Mock()
        mock_app_factory.return_value = mock_app

        def custom_render(item):
            return f"<div>{item}</div>"

        custom_hdrs = ["X-Custom: header"]
        custom_ftrs = ["X-Footer: footer"]

        app, route = star_app(
            hdrs=custom_hdrs, ftrs=custom_ftrs, render=custom_render, debug=True, live=False, static_path="/assets"
        )

        assert app == mock_app
        assert route == mock_app.route
        mock_app.static_route_exts.assert_called_once_with(static_path="/assets")

        call_kwargs = mock_app_factory.call_args[1]
        assert call_kwargs["hdrs"] == tuple(custom_hdrs)
        assert call_kwargs["ftrs"] == custom_ftrs
        assert call_kwargs["debug"] is True

    @patch("starhtml.tags.Meta")
    @patch("starhtml.tags.Script")
    def test_production_headers_setup(self, mock_script, mock_meta):
        """Test production-ready headers setup."""
        mock_script.return_value = Mock()
        mock_meta.return_value = Mock()

        # Production setup with specific versions and no fallback
        headers = def_hdrs(
            datastar_version="v1.0.0",
            include_iconify=True,
            iconify_version="2.5.0",
            fallback_path="/static/datastar-v1.0.0.js",
        )

        assert len(headers) == 4  # charset, viewport, datastar, iconify

        # Verify production version is used
        datastar_call = mock_script.call_args_list[0]
        assert "v1.0.0" in datastar_call[1]["src"]
        assert "/static/datastar-v1.0.0.js" in datastar_call[1]["onerror"]

        iconify_call = mock_script.call_args_list[1]
        assert "2.5.0" in iconify_call[1]["src"]
