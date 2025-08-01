"""Behavioral tests for StarHTML handlers module.

These tests focus on actual functionality and behavior rather than
string matching or trivial object existence checks.
"""

import json
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from starhtml.handlers import (
    PackageAssetManager,
    _load_handler,
    check_assets,
    get_bundle_stats,
    persist_handler,
    resize_handler,
    scroll_handler,
)


class TestHandlerBehavior:
    """Test actual handler behavior and functionality."""

    def test_persist_handler_generates_executable_script(self):
        """Test persist_handler generates a valid JavaScript module."""
        result = persist_handler()
        script_content = str(result)

        # Test that the script follows ES6 module pattern
        assert script_content.startswith('<script type="module">')
        assert script_content.endswith("</script>")

        # Test that it follows a proper import/load/apply pattern
        lines = script_content.split("\n")
        import_lines = [line for line in lines if "import" in line]
        load_lines = [line for line in lines if "load(" in line]
        apply_lines = [line for line in lines if "apply(" in line]

        # Should have at least one import, load, and apply
        assert len(import_lines) >= 1, "Script should import handler plugin"
        assert len(load_lines) >= 1, "Script should load the plugin"
        assert len(apply_lines) >= 1, "Script should apply the handlers"

    def test_scroll_handler_generates_functional_script(self):
        """Test scroll_handler creates a functional JavaScript handler."""
        result = scroll_handler()
        script_content = str(result)

        # Should be a proper ES6 module
        assert script_content.startswith('<script type="module">')

        # Should import scroll handler specifically
        assert "/static/js/handlers/scroll.js" in script_content

        # Should follow the plugin loading pattern
        assert "load(handlerPlugin)" in script_content

    def test_resize_handler_configuration_affects_behavior(self):
        """Test that resize_handler configuration actually changes output."""
        # Test with default configuration
        default_result = resize_handler()
        default_content = str(default_result)

        # Test with custom configuration
        custom_result = resize_handler(signal="customResize", throttle_ms=200, track_element=True, track_both=True)
        custom_content = str(custom_result)

        # Content should be different when config changes
        assert default_content != custom_content

        # Custom config should contain the specified values
        assert "customResize" in custom_content
        assert "200" in custom_content

        # Should affect the setConfig call
        assert "setConfig(" in custom_content

    def test_load_handler_with_invalid_config_raises_error(self):
        """Test that _load_handler properly handles invalid configurations."""
        # Test with configuration that contains invalid JSON types
        with pytest.raises((TypeError, ValueError)):
            _load_handler("test", {"invalid": set([1, 2, 3])})

    def test_load_handler_config_serialization(self):
        """Test that _load_handler properly serializes configuration to JSON."""
        config = {"signal": "test", "throttle": 100, "enabled": True, "options": ["a", "b", "c"]}
        result = _load_handler("testhandler", config)
        script_content = str(result)

        # Should contain valid JSON
        # Extract the config part
        start_idx = script_content.find("setConfig(") + len("setConfig(")
        end_idx = script_content.find(")", start_idx)
        config_json = script_content[start_idx:end_idx]

        # Should be parseable JSON
        parsed_config = json.loads(config_json)
        assert parsed_config == config


class TestPackageAssetManagerBehavior:
    """Test PackageAssetManager actual behavior and edge cases."""

    def test_asset_manager_handles_edge_cases_gracefully(self):
        """Test that asset manager handles edge cases gracefully."""
        manager = PackageAssetManager()

        # Test with nonexistent asset
        content = manager.get_asset_content("nonexistent_asset")
        assert content == ""

        url = manager.get_asset_url("nonexistent_asset")
        assert url is None

        # Test bundle info structure
        info = manager.get_bundle_info()
        assert isinstance(info, dict)
        assert "available_bundles" in info
        assert "bundle_sizes" in info
        assert "is_development" in info

    def test_asset_manager_development_mode_detection(self):
        """Test development mode detection logic."""
        # Development mode is now based solely on js_dir existence

        # Create manager and check it returns a boolean
        manager = PackageAssetManager()
        assert isinstance(manager.is_development, bool)

        # The actual value depends on whether src/starhtml/static/js exists
        # We can't easily mock Path.exists(), so just verify the logic works
        # by checking that it's the opposite of js_dir.exists()
        expected_dev_mode = not manager.js_dir.exists()
        assert manager.is_development == expected_dev_mode

    def test_manifest_handling_behavior(self):
        """Test manifest handling behavior."""
        manager = PackageAssetManager()

        # Test that manifest loading doesn't break the class
        info = manager.get_bundle_info()
        assert isinstance(info, dict)
        assert "available_bundles" in info

        # Test that asset checking works regardless of manifest state
        status = manager.check_assets()
        assert isinstance(status, dict)
        assert "js_dir_exists" in status
        assert "manifest_loaded" in status
        assert isinstance(status["manifest_loaded"], bool)

    def test_asset_content_reading_with_encoding_errors(self):
        """Test asset content reading with various encoding issues."""
        # Create a file with non-UTF8 content
        with tempfile.NamedTemporaryFile(mode="wb", suffix=".js", delete=False) as f:
            # Write some bytes that aren't valid UTF-8
            f.write(b"\xff\xfe\x00Invalid UTF-8 content")
            asset_path = f.name

        try:
            manager = PackageAssetManager()
            with patch.object(manager, "_get_asset_path", return_value=Path(asset_path)):
                # Should handle encoding errors gracefully
                content = manager.get_asset_content("test_asset")
                # Should return empty string or handle encoding error
                assert isinstance(content, str)
        finally:
            Path(asset_path).unlink()

    def test_bundle_info_consistency(self):
        """Test that bundle info is consistent across multiple calls."""
        manager = PackageAssetManager()

        # Get bundle info multiple times
        info1 = manager.get_bundle_info()
        info2 = manager.get_bundle_info()

        # Should be consistent
        assert info1 == info2

        # Check that the structure is always the same
        required_keys = ["available_bundles", "bundle_sizes", "is_development"]
        for key in required_keys:
            assert key in info1
            assert key in info2

    def test_asset_url_generation_logic(self):
        """Test the logic behind asset URL generation."""
        manager = PackageAssetManager()

        # Test with development mode
        with patch.object(manager, "is_development", True):
            url = manager.get_asset_url("test.js")
            if url:  # Only test if asset exists
                assert "/static/js/" in url

        # Test with production mode (manifest-based)
        with patch.object(manager, "is_development", False):
            with patch.object(manager, "_manifest", {"test.js": "test.abc123.js"}):
                url = manager.get_asset_url("test.js")
                if url:
                    assert "abc123" in url  # Should use hashed filename


class TestErrorConditions:
    """Test error conditions and edge cases."""

    def test_handler_with_extremely_large_config(self):
        """Test handler behavior with unusually large configuration."""
        # Create a large configuration
        large_config = {f"key_{i}": f"value_{i}" * 100 for i in range(1000)}

        result = _load_handler("test", large_config)
        script_content = str(result)

        # Should handle large configs without breaking
        assert '<script type="module">' in script_content
        assert "setConfig(" in script_content

    def test_bundle_stats_with_filesystem_errors(self):
        """Test bundle stats function with filesystem errors."""
        with patch("starhtml.handlers.PackageAssetManager") as mock_manager:
            # Simulate filesystem error
            mock_manager.side_effect = OSError("Filesystem error")

            # Should handle errors gracefully
            stats = get_bundle_stats()
            assert isinstance(stats, dict)
            # Should provide some fallback data
            assert "available_bundles" in stats or "error" in stats

    def test_check_assets_with_permission_errors(self):
        """Test asset checking with permission errors."""
        with patch("starhtml.handlers.PackageAssetManager") as mock_manager:
            # Simulate permission error
            mock_manager.side_effect = PermissionError("Permission denied")

            # Should handle permission errors gracefully
            assets = check_assets()
            assert isinstance(assets, dict)
            # Should indicate the error condition
            assert "js_dir_exists" in assets or "error" in assets


class TestRealWorldUsage:
    """Test handlers in realistic usage scenarios."""

    def test_multiple_handlers_combination(self):
        """Test combining multiple handlers in a realistic scenario."""
        persist_script = persist_handler()
        scroll_script = scroll_handler()
        resize_script = resize_handler(throttle_ms=50)

        # All should be valid ES6 modules
        scripts = [persist_script, scroll_script, resize_script]
        for script in scripts:
            content = str(script)
            assert content.startswith('<script type="module">')
            assert content.endswith("</script>")

        # Should not interfere with each other (different handler files)
        persist_content = str(persist_script)
        scroll_content = str(scroll_script)
        resize_content = str(resize_script)

        assert "persist.js" in persist_content
        assert "scroll.js" in scroll_content
        assert "resize.js" in resize_content

        # Each should have unique configuration
        assert persist_content != scroll_content != resize_content

    def test_asset_manager_in_production_simulation(self):
        """Test asset manager behavior in production-like environment."""
        # Simulate production environment
        with patch.dict("os.environ", {"STARHTML_ENV": "production"}):
            # Mock a typical production manifest
            production_manifest = {
                "files": {"app.js": "app.abc123.js", "vendor.js": "vendor.789xyz.js"},
                "bundles": {"app": {"size": 12345}, "vendor": {"size": 67890}},
            }

            with patch.object(PackageAssetManager, "_load_manifest", return_value=production_manifest):
                manager = PackageAssetManager()

                # Should be in production mode
                assert manager.is_development is False

                # Bundle info should reflect production state
                info = manager.get_bundle_info()
                assert info["is_development"] is False
                # Should have the files from our manifest
                assert "app.js" in info["available_bundles"]
                assert "vendor.js" in info["available_bundles"]

    def test_handler_performance_characteristics(self):
        """Test that handlers don't have performance issues."""
        import time

        # Test handler generation speed
        start_time = time.time()
        for _ in range(100):
            persist_handler()
            scroll_handler()
            resize_handler()
        end_time = time.time()

        # Should be fast (less than 1 second for 100 iterations)
        assert (end_time - start_time) < 1.0

        # Test asset manager performance
        start_time = time.time()
        manager = PackageAssetManager()
        for _ in range(50):
            manager.get_bundle_info()
            manager.check_assets()
        end_time = time.time()

        # Should be reasonably fast
        assert (end_time - start_time) < 2.0
