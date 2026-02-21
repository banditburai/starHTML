"""Tests for the icon system: IconResolver 2-tier caching, Icon() component, and CLI scanner."""

import json
import os
from unittest.mock import MagicMock, patch

import pytest

from starhtml.icons import Icon, IconData, IconResolver, _find_project_root

LUCIDE_JSON = {
    "prefix": "lucide",
    "width": 24,
    "height": 24,
    "icons": {
        "house": {
            "body": '<path d="M15 21v-8a1 1 0 0 0-1-1h-4a1 1 0 0 0-1 1v8"/><path d="M3 10a2 2 0 0 1 .709-1.528l7-5.999a2 2 0 0 1 2.582 0l7 5.999A2 2 0 0 1 21 10v9a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/>',
        },
        "star": {
            "body": '<polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/>',
        },
    },
    "aliases": {
        "home": {"parent": "house"},
    },
}

FA_JSON = {
    "prefix": "fa-solid",
    "width": 512,
    "height": 512,
    "icons": {
        "house": {
            "body": '<path d="M575.8 255.5"/>',
            "width": 576,
        },
    },
}


@pytest.fixture(autouse=True)
def _reset_project_root():
    """Reset cached project root between tests."""
    import starhtml.icons as mod

    original = mod._project_root
    yield
    mod._project_root = original


class TestIconData:
    def test_frozen(self):
        data = IconData(body="<path/>")
        with pytest.raises(AttributeError):
            data.body = "changed"

    def test_defaults(self):
        data = IconData(body="<circle/>")
        assert data.width == 24
        assert data.height == 24

    def test_custom_dimensions(self):
        data = IconData(body="<rect/>", width=512, height=256)
        assert data.width == 512
        assert data.height == 256


class TestFindProjectRoot:
    def test_finds_pyproject_toml(self, tmp_path):
        (tmp_path / "pyproject.toml").write_text("[project]\nname='test'\n")
        sub = tmp_path / "src" / "pkg"
        sub.mkdir(parents=True)

        import starhtml.icons as mod

        mod._project_root = None
        with patch("starhtml.icons.Path.cwd", return_value=sub):
            root = _find_project_root()
        assert root == tmp_path

    def test_fallback_to_cwd(self, tmp_path):
        sub = tmp_path / "no_project"
        sub.mkdir()

        import starhtml.icons as mod

        mod._project_root = None
        with patch("starhtml.icons.Path.cwd", return_value=sub):
            root = _find_project_root()
        assert root == sub

    def test_caches_result(self, tmp_path):
        (tmp_path / "pyproject.toml").write_text("[project]\n")

        import starhtml.icons as mod

        mod._project_root = None
        with patch("starhtml.icons.Path.cwd", return_value=tmp_path):
            first = _find_project_root()
            second = _find_project_root()
        assert first is second


class TestResolverMemory:
    def test_register_and_resolve(self):
        r = IconResolver()
        r.inline = True
        icon = IconData(body="<path/>")
        r.register("test", "icon1", icon)
        assert r.resolve("test", "icon1") is icon

    def test_memory_miss_returns_none_without_disk_or_api(self, tmp_path):
        r = IconResolver()
        r.inline = True
        with (
            patch("starhtml.icons._project_cache_dir", return_value=tmp_path / "nope"),
            patch("httpx.get", side_effect=Exception("no network")),
        ):
            result = r.resolve("nonexistent", "icon")
        assert result is None

    def test_inline_defaults_false(self):
        r = IconResolver()
        assert r.inline is False

    def test_second_resolve_hits_memory(self, tmp_path):
        mock_resp = MagicMock()
        mock_resp.json.return_value = LUCIDE_JSON
        mock_resp.raise_for_status = MagicMock()

        r = IconResolver()
        with (
            patch("starhtml.icons._project_cache_dir", return_value=tmp_path / "cache"),
            patch("httpx.get", return_value=mock_resp) as mock_get,
        ):
            first = r.resolve("lucide", "house")
            second = r.resolve("lucide", "house")

        assert first is second
        mock_get.assert_called_once()


class TestResolverDisk:
    def test_disk_cache_hit(self, tmp_path):
        cache_dir = tmp_path / "icons"
        cache_dir.mkdir()
        (cache_dir / "lucide.json").write_text(json.dumps(LUCIDE_JSON))

        r = IconResolver()
        r.inline = True
        with patch("starhtml.icons._project_cache_dir", return_value=cache_dir):
            result = r.resolve("lucide", "house")

        assert result is not None
        assert "path" in result.body
        assert result.width == 24
        assert result.height == 24

    def test_alias_resolution(self, tmp_path):
        cache_dir = tmp_path / "icons"
        cache_dir.mkdir()
        (cache_dir / "lucide.json").write_text(json.dumps(LUCIDE_JSON))

        r = IconResolver()
        with patch("starhtml.icons._project_cache_dir", return_value=cache_dir):
            result = r.resolve("lucide", "home")

        assert result is not None
        assert "path" in result.body

    def test_per_icon_dimension_override(self, tmp_path):
        cache_dir = tmp_path / "icons"
        cache_dir.mkdir()
        (cache_dir / "fa-solid.json").write_text(json.dumps(FA_JSON))

        r = IconResolver()
        with patch("starhtml.icons._project_cache_dir", return_value=cache_dir):
            result = r.resolve("fa-solid", "house")

        assert result is not None
        assert result.width == 576
        assert result.height == 512

    def test_corrupt_json_returns_none(self, tmp_path):
        cache_dir = tmp_path / "cache"
        cache_dir.mkdir()
        (cache_dir / "lucide.json").write_text("NOT VALID JSON{{{")

        r = IconResolver()
        with (
            patch("starhtml.icons._project_cache_dir", return_value=cache_dir),
            patch("httpx.get", side_effect=Exception("no network")),
        ):
            result = r.resolve("lucide", "house")

        assert result is None

    def test_bulk_load_on_first_disk_hit(self, tmp_path):
        cache_dir = tmp_path / "icons"
        cache_dir.mkdir()
        (cache_dir / "lucide.json").write_text(json.dumps(LUCIDE_JSON))

        r = IconResolver()
        with patch("starhtml.icons._project_cache_dir", return_value=cache_dir):
            r.resolve("lucide", "house")

        assert "star" in r._memory.get("lucide", {})
        assert "home" in r._memory.get("lucide", {})


class TestResolverAPI:
    def test_api_fallback(self, tmp_path):
        mock_resp = MagicMock()
        mock_resp.json.return_value = LUCIDE_JSON
        mock_resp.raise_for_status = MagicMock()

        cache_dir = tmp_path / "cache"
        r = IconResolver()
        r.inline = True
        with (
            patch("starhtml.icons._project_cache_dir", return_value=cache_dir),
            patch("httpx.get", return_value=mock_resp) as mock_get,
        ):
            result = r.resolve("lucide", "house")

        assert result is not None
        assert "path" in result.body
        mock_get.assert_called_once()
        assert (cache_dir / "lucide.json").exists()

    def test_api_failure_returns_none(self, tmp_path):
        r = IconResolver()
        r.inline = True
        with (
            patch("starhtml.icons._project_cache_dir", return_value=tmp_path / "nope"),
            patch("httpx.get", side_effect=Exception("network error")),
        ):
            result = r.resolve("lucide", "missing")

        assert result is None

    def test_api_runtime_warning_in_inline_mode(self, tmp_path, caplog):
        mock_resp = MagicMock()
        mock_resp.json.return_value = LUCIDE_JSON
        mock_resp.raise_for_status = MagicMock()

        r = IconResolver()
        r.inline = True
        with (
            patch("starhtml.icons._project_cache_dir", return_value=tmp_path / "cache"),
            patch("httpx.get", return_value=mock_resp),
            caplog.at_level("WARNING", logger="starhtml.icons"),
        ):
            r.resolve("lucide", "house")

        assert "starhtml icons scan" in caplog.text


class TestDiskMerge:
    def test_merge_adds_without_overwriting(self, tmp_path):
        cache_dir = tmp_path / "cache"
        cache_dir.mkdir()

        existing = {"icons": {"star": {"body": "<star/>"}}, "width": 24, "height": 24}
        (cache_dir / "lucide.json").write_text(json.dumps(existing))

        r = IconResolver()
        new_data = {"icons": {"house": {"body": "<house/>"}}, "width": 24, "height": 24, "prefix": "lucide"}
        with patch("starhtml.icons._project_cache_dir", return_value=cache_dir):
            r._merge_to_disk("lucide", new_data)

        merged = json.loads((cache_dir / "lucide.json").read_text())
        assert "star" in merged["icons"]
        assert "house" in merged["icons"]

    def test_merge_with_corrupt_existing_json(self, tmp_path):
        cache_dir = tmp_path / "cache"
        cache_dir.mkdir()
        (cache_dir / "lucide.json").write_text("CORRUPT{{{")

        r = IconResolver()
        new_data = {"icons": {"house": {"body": "<house/>"}}, "width": 24, "height": 24}
        with patch("starhtml.icons._project_cache_dir", return_value=cache_dir):
            r._merge_to_disk("lucide", new_data)

        merged = json.loads((cache_dir / "lucide.json").read_text())
        assert "house" in merged["icons"]

    def test_merge_survives_write_failure(self, tmp_path, caplog):
        r = IconResolver()
        blocked = tmp_path / "blocked"
        blocked.write_text("file blocking mkdir")

        with (
            patch("starhtml.icons._project_cache_dir", return_value=blocked / "subdir"),
            caplog.at_level("WARNING", logger="starhtml.icons"),
        ):
            r._merge_to_disk("lucide", {"icons": {"x": {"body": "<x/>"}}})

        assert "Failed to write icon cache" in caplog.text


class TestPreload:
    def test_preload_all(self, tmp_path):
        cache_dir = tmp_path / "icons"
        cache_dir.mkdir()
        (cache_dir / "lucide.json").write_text(json.dumps(LUCIDE_JSON))

        r = IconResolver()
        with patch("starhtml.icons._project_cache_dir", return_value=cache_dir):
            r.preload("lucide")

        assert "house" in r._memory.get("lucide", {})
        assert "star" in r._memory.get("lucide", {})
        assert "home" in r._memory.get("lucide", {})

    def test_preload_specific_names(self, tmp_path):
        cache_dir = tmp_path / "icons"
        cache_dir.mkdir()
        (cache_dir / "lucide.json").write_text(json.dumps(LUCIDE_JSON))

        r = IconResolver()
        with patch("starhtml.icons._project_cache_dir", return_value=cache_dir):
            r.preload("lucide", names=["star"])

        assert "star" in r._memory.get("lucide", {})
        assert "house" not in r._memory.get("lucide", {})

    def test_preload_nonexistent_prefix_is_noop(self, tmp_path):
        r = IconResolver()
        with patch("starhtml.icons._project_cache_dir", return_value=tmp_path / "nope"):
            r.preload("nonexistent")

        assert r._memory == {}

    def test_preload_from_disk(self, tmp_path):
        cache_dir = tmp_path / "icons"
        cache_dir.mkdir()
        (cache_dir / "lucide.json").write_text(json.dumps(LUCIDE_JSON))
        (cache_dir / "fa-solid.json").write_text(json.dumps(FA_JSON))

        r = IconResolver()
        with patch("starhtml.icons._project_cache_dir", return_value=cache_dir):
            r.preload_from_disk()

        assert "house" in r._memory.get("lucide", {})
        assert "star" in r._memory.get("lucide", {})
        assert "house" in r._memory.get("fa-solid", {})

    def test_preload_from_disk_no_cache_dir(self, tmp_path):
        r = IconResolver()
        with patch("starhtml.icons._project_cache_dir", return_value=tmp_path / "nope"):
            r.preload_from_disk()

        assert r._memory == {}


class TestBatchFetch:
    def test_batch_fetch_all_cached(self):
        r = IconResolver()
        r.register("lucide", "house", IconData(body="<house/>"))
        r.register("lucide", "star", IconData(body="<star/>"))

        results = r.batch_fetch("lucide", ["house", "star"])
        assert results["house"] is not None
        assert results["star"] is not None

    def test_batch_fetch_from_disk(self, tmp_path):
        cache_dir = tmp_path / "icons"
        cache_dir.mkdir()
        (cache_dir / "lucide.json").write_text(json.dumps(LUCIDE_JSON))

        r = IconResolver()
        with patch("starhtml.icons._project_cache_dir", return_value=cache_dir):
            results = r.batch_fetch("lucide", ["house", "star"])

        assert results["house"] is not None
        assert results["star"] is not None

    def test_batch_fetch_api_call(self, tmp_path):
        mock_resp = MagicMock()
        mock_resp.json.return_value = LUCIDE_JSON
        mock_resp.raise_for_status = MagicMock()

        r = IconResolver()
        with (
            patch("starhtml.icons._project_cache_dir", return_value=tmp_path / "cache"),
            patch("httpx.get", return_value=mock_resp) as mock_get,
        ):
            results = r.batch_fetch("lucide", ["house", "star"])

        assert results["house"] is not None
        assert results["star"] is not None
        mock_get.assert_called_once()
        call_url = mock_get.call_args[0][0]
        assert "house" in call_url and "star" in call_url

    def test_batch_fetch_partial_cache(self, tmp_path):
        mock_resp = MagicMock()
        mock_resp.json.return_value = LUCIDE_JSON
        mock_resp.raise_for_status = MagicMock()

        r = IconResolver()
        r.register("lucide", "house", IconData(body="<house/>"))

        with (
            patch("starhtml.icons._project_cache_dir", return_value=tmp_path / "cache"),
            patch("httpx.get", return_value=mock_resp) as mock_get,
        ):
            results = r.batch_fetch("lucide", ["house", "star"])

        assert results["house"] is not None
        assert results["star"] is not None
        call_url = mock_get.call_args[0][0]
        assert "star" in call_url
        assert "house" not in call_url


class TestStarAppIntegration:
    @patch("starhtml.starapp._app_factory")
    def test_env_var_overrides_inline_icons_param(self, mock_factory):
        from starhtml.icons import resolver
        from starhtml.starapp import star_app

        mock_app = MagicMock()
        mock_app.route = MagicMock()
        mock_app.static_route_exts = MagicMock()
        mock_factory.return_value = mock_app

        for val in ("1", "true", "yes", "TRUE", "Yes"):
            with patch.dict(os.environ, {"STARHTML_INLINE_ICONS": val}):
                star_app()
            assert resolver.inline is True

        for val in ("0", "false", "no"):
            with patch.dict(os.environ, {"STARHTML_INLINE_ICONS": val}):
                star_app()
            assert resolver.inline is False

        resolver.inline = False

    @patch("starhtml.starapp._app_factory")
    def test_inline_icons_true_omits_iconify_script(self, mock_factory):
        from starhtml.starapp import star_app

        mock_app = MagicMock()
        mock_app.route = MagicMock()
        mock_app.static_route_exts = MagicMock()
        mock_factory.return_value = mock_app

        star_app(inline_icons=True, hdrs=["custom"])

        call_kwargs = mock_factory.call_args[1]
        hdrs_html = [str(h) for h in call_kwargs["hdrs"]]
        assert not any("iconify-icon" in h for h in hdrs_html)
        assert "custom" in call_kwargs["hdrs"]

        from starhtml.icons import resolver

        resolver.inline = False

    @patch("starhtml.starapp._app_factory")
    def test_cdn_mode_prepends_iconify_script(self, mock_factory):
        from starhtml.starapp import star_app

        mock_app = MagicMock()
        mock_app.route = MagicMock()
        mock_app.static_route_exts = MagicMock()
        mock_factory.return_value = mock_app

        star_app(hdrs=["custom"])

        call_kwargs = mock_factory.call_args[1]
        first_hdr = str(call_kwargs["hdrs"][0])
        assert "iconify-icon" in first_hdr
        assert call_kwargs["hdrs"][-1] == "custom"


class TestCLIScan:
    def test_regex_scan_finds_icons(self, tmp_path):
        from starhtml.icons import _scan_icons_regex

        py_file = tmp_path / "app.py"
        py_file.write_text("""
from starhtml import *
Icon("lucide:home")
Icon("lucide:star")
Icon("mdi:account")
""")
        found = _scan_icons_regex([tmp_path])
        assert found == {"lucide": {"home", "star"}, "mdi": {"account"}}

    def test_regex_scan_ignores_non_icon_patterns(self, tmp_path):
        from starhtml.icons import _scan_icons_regex

        py_file = tmp_path / "app.py"
        py_file.write_text("""
Icon("no-colon")
SomeOtherFunc("lucide:home")
""")
        found = _scan_icons_regex([tmp_path])
        assert found == {}

    def test_regex_scan_empty_dir(self, tmp_path):
        from starhtml.icons import _scan_icons_regex

        found = _scan_icons_regex([tmp_path])
        assert found == {}

    def test_cli_scan_no_icons(self, tmp_path):
        from starhtml.icons import main

        result = main(["icons", "scan", str(tmp_path)])
        assert result == 0

    def test_cli_help(self):
        from starhtml.icons import main

        result = main([])
        assert result == 0

    def test_default_excludes_skip_tests_dir(self, tmp_path):
        from starhtml.icons import _scan_icons_regex

        src = tmp_path / "src"
        src.mkdir()
        (src / "app.py").write_text('Icon("lucide:home")')
        tests = tmp_path / "tests"
        tests.mkdir()
        (tests / "test_app.py").write_text('Icon("fake:icon")')
        found = _scan_icons_regex([tmp_path])
        assert found == {"lucide": {"home"}}

    def test_default_excludes_skip_venv(self, tmp_path):
        from starhtml.icons import _scan_icons_regex

        (tmp_path / "app.py").write_text('Icon("lucide:home")')
        venv = tmp_path / ".venv" / "lib"
        venv.mkdir(parents=True)
        (venv / "some_pkg.py").write_text('Icon("mdi:alert")')
        found = _scan_icons_regex([tmp_path])
        assert found == {"lucide": {"home"}}

    def test_no_default_excludes_scans_tests(self, tmp_path):
        from starhtml.icons import _scan_icons_regex

        src = tmp_path / "src"
        src.mkdir()
        (src / "app.py").write_text('Icon("lucide:home")')
        tests = tmp_path / "tests"
        tests.mkdir()
        (tests / "test_app.py").write_text('Icon("mdi:alert")')
        found = _scan_icons_regex([tmp_path], exclude_dirs=frozenset())
        assert found == {"lucide": {"home"}, "mdi": {"alert"}}

    def test_exclude_pattern_filters_files(self, tmp_path):
        from starhtml.icons import _scan_icons_regex

        (tmp_path / "app.py").write_text('Icon("lucide:home")')
        (tmp_path / "scratch.py").write_text('Icon("mdi:alert")')
        found = _scan_icons_regex([tmp_path], exclude_dirs=frozenset(), exclude_patterns=["*/scratch.py"])
        assert found == {"lucide": {"home"}}

    def test_exclude_pattern_additive_with_defaults(self, tmp_path):
        from starhtml.icons import _DEFAULT_EXCLUDE_DIRS, _scan_icons_regex

        src = tmp_path / "src"
        src.mkdir()
        (src / "app.py").write_text('Icon("lucide:home")')
        (src / "demo.py").write_text('Icon("mdi:alert")')
        tests = tmp_path / "tests"
        tests.mkdir()
        (tests / "test_app.py").write_text('Icon("fake:icon")')
        found = _scan_icons_regex([tmp_path], exclude_dirs=_DEFAULT_EXCLUDE_DIRS, exclude_patterns=["*/demo.py"])
        assert found == {"lucide": {"home"}}

    def test_cli_no_default_excludes_flag(self):
        from starhtml.icons import main

        # Verify the flag parses without error
        args = main(["icons", "scan", "--no-default-excludes", "/nonexistent"])
        # Returns 0 because no .py files found
        assert args == 0

    def test_single_file_path_respects_exclude_pattern(self, tmp_path):
        from starhtml.icons import _scan_icons_regex

        f = tmp_path / "scratch.py"
        f.write_text('Icon("lucide:home")')
        found = _scan_icons_regex([f], exclude_dirs=frozenset(), exclude_patterns=[str(f)])
        assert found == {}


class TestIconEdgeCases:
    def test_no_colon_in_icon_name_cdn_mode(self):
        from starhtml.icons import resolver

        resolver.inline = False
        icon = Icon("home")
        html = str(icon)
        assert 'icon="home"' in html
        assert "iconify-icon" in html

    def test_no_colon_in_icon_name_inline_mode(self):
        from starhtml.icons import resolver

        resolver.inline = True
        try:
            icon = Icon("home")
            html = str(icon)
            assert "<span" in html
            assert "<svg" not in html
        finally:
            resolver.inline = False

    def test_empty_icon_string_inline_mode(self):
        from starhtml.icons import resolver

        resolver.inline = True
        try:
            icon = Icon("")
            html = str(icon)
            assert "<span" in html
            assert "<svg" not in html
        finally:
            resolver.inline = False

    def test_empty_cls_omits_class_attr(self):
        icon = Icon("lucide:home")
        html = str(icon)
        assert 'class=""' not in html

    def test_tailwind_bracket_value(self):
        from starhtml.icons import resolver

        resolver.inline = True
        resolver.register("lucide", "home", IconData(body="<path/>"))
        try:
            icon = Icon("lucide:home", cls="w-[2rem] h-[3rem]")
            html = str(icon)
            assert "width:2rem" in html
            assert "height:3rem" in html
        finally:
            resolver.inline = False
            resolver._memory.clear()

    def test_tailwind_computed_fallback_size(self):
        from starhtml.icons import resolver

        resolver.inline = True
        resolver.register("lucide", "home", IconData(body="<path/>"))
        try:
            icon = Icon("lucide:home", cls="size-16")
            html = str(icon)
            assert "4.0rem" in html
        finally:
            resolver.inline = False
            resolver._memory.clear()

    def test_tailwind_w_only_fills_height(self):
        from starhtml.icons import resolver

        resolver.inline = True
        resolver.register("lucide", "home", IconData(body="<path/>"))
        try:
            icon = Icon("lucide:home", cls="w-6")
            html = str(icon)
            assert "width:1.5rem" in html
            assert "height:1.5rem" in html
        finally:
            resolver.inline = False
            resolver._memory.clear()

    def test_stable_false_cdn_mode_passes_kwargs(self):
        from fastcore.xml import to_xml

        icon = Icon("lucide:home", stable=False, data_show="$visible")
        html = to_xml(icon)
        assert 'data-show="$visible"' in html
        assert "iconify-icon" in html


class TestIconDualModeStructure:
    """Inline SVG and CDN modes must place kwargs on the inner element,
    keeping the outer span as a stable sizing wrapper."""

    @pytest.fixture(autouse=True)
    def _setup(self):
        from starhtml.icons import resolver

        resolver.register("lucide", "home", IconData(body="<path/>"))
        yield
        resolver.inline = False
        resolver._memory.clear()

    def test_inline_has_inner_span_with_data_icon_inner(self):
        from starhtml.icons import resolver

        resolver.inline = True
        html = str(Icon("lucide:home"))
        assert "data-icon-sh" in html

    def test_inline_kwargs_on_inner_not_outer(self):
        from fastcore.xml import to_xml

        from starhtml.icons import resolver

        resolver.inline = True
        html = to_xml(Icon("lucide:home", style="transform:rotate(0deg)"))
        # style="transform:..." should be on the inner span, not the outer
        # Outer span should have the sizing style
        assert "display:inline-block" in html
        assert "transform:rotate(0deg)" in html

    def test_inline_outer_span_keeps_sizing(self):
        from fastcore.xml import to_xml

        from starhtml.icons import resolver

        resolver.inline = True
        html = to_xml(Icon("lucide:home", cls="text-green-500", style="opacity:0.5"))
        # Outer span has sizing and cls
        assert "display:inline-block" in html
        assert "text-green-500" in html
        # User style on inner, not clobbering sizing
        assert "opacity:0.5" in html

    def test_cdn_kwargs_on_iconify_not_outer(self):
        from fastcore.xml import to_xml

        from starhtml.icons import resolver

        resolver.inline = False
        html = to_xml(Icon("lucide:home", style="transform:rotate(0deg)"))
        assert "iconify-icon" in html
        assert "display:inline-block" in html
        assert "transform:rotate(0deg)" in html

    def test_inline_fallback_has_inner_span(self):
        from starhtml.icons import resolver

        resolver.inline = True
        # Use a prefix:name that won't resolve (no disk, mock API failure)
        with patch("httpx.get", side_effect=Exception("no network")):
            html = str(Icon("nonexistent:icon"))
        assert "data-icon-sh" in html

    def test_inline_id_goes_to_outer_span(self):
        from fastcore.xml import to_xml

        from starhtml.icons import resolver

        resolver.inline = True
        html = to_xml(Icon("lucide:home", id="my-icon"))
        assert 'id="my-icon"' in html


class TestIconInlineCss:
    @patch("starhtml.starapp._app_factory")
    def test_inline_mode_includes_icon_css(self, mock_factory):
        from starhtml.starapp import star_app

        mock_app = MagicMock()
        mock_app.route = MagicMock()
        mock_app.static_route_exts = MagicMock()
        mock_factory.return_value = mock_app

        star_app(inline_icons=True)

        call_kwargs = mock_factory.call_args[1]
        hdrs_html = [str(h) for h in call_kwargs["hdrs"]]
        assert any("data-icon-sh" in h for h in hdrs_html)
        assert not any("iconify-icon" in h for h in hdrs_html)

        from starhtml.icons import resolver

        resolver.inline = False

    def test_icon_inline_css_content(self):
        from starhtml.starapp import icon_inline_css

        html = str(icon_inline_css())
        assert "[data-icon-sh]" in html
        assert "display:block" in html
        assert "width:100%" in html
        assert "height:100%" in html
        assert "!important" in html
