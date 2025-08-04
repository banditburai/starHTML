"""StarHTML Datastar plugin handlers for signal persistence, scrolling, and resizing."""

import json
from functools import cached_property
from pathlib import Path

from fastcore.xml import FT

from .starapp import DATASTAR_VERSION
from .xtend import Script

type ScriptOutput = FT | list[FT] | None

__all__ = [
    "persist_handler",
    "scroll_handler",
    "resize_handler",
    "drag_handler",
    "canvas_handler",
    "get_bundle_stats",
    "check_assets",
]

# =============================================================================
# PUBLIC API - High-level handler functions for end-users
# =============================================================================


def persist_handler() -> ScriptOutput:
    """Auto-persist signals to localStorage/sessionStorage.

    Use data-persist="signal1,signal2" or data-persist="*" on elements.
    Modifiers: __session, __as-{key}, __throttle.{ms}.
    """
    return _load_handler("persist")


def scroll_handler() -> ScriptOutput:
    """Track scroll position, velocity, and visibility.

    Creates: scrollX/Y, direction, velocity, visible, progress signals.
    """
    return _load_handler("scroll")


def resize_handler(
    signal: str = "resize",
    throttle_ms: int = 16,
    track_element: bool = False,
    track_both: bool = False,
) -> ScriptOutput:
    """Track window/element resize events with responsive state."""
    config = {"signal": signal, "throttleMs": throttle_ms, "trackElement": track_element, "trackBoth": track_both}
    return _load_handler("resize", config)


def drag_handler(
    signal: str = "drag",
    mode: str = "freeform",
    throttle_ms: int = 16,
    constrain_to_parent: bool = False,
    touch_enabled: bool = True,
) -> ScriptOutput:
    """Enable drag-and-drop with reactive state management.

    Creates signals: {signal}_is_dragging, {signal}_element_id, {signal}_x/y, {signal}_drop_zone.
    Use with ds_draggable() on elements and ds_drop_zone("name") for drop targets.
    """
    config = {
        "signal": signal,
        "mode": mode,
        "throttleMs": throttle_ms,
        "constrainToParent": constrain_to_parent,
        "touchEnabled": touch_enabled,
    }
    return _load_handler("drag", config)


def canvas_handler(
    signal: str = "canvas",
    enable_pan: bool = True,
    enable_zoom: bool = True,
    min_zoom: float = 0.1,
    max_zoom: float = 10.0,
    touch_enabled: bool = True,
    enable_grid: bool = True,
    grid_size: int = 100,
    grid_color: str = "#e0e0e0",
    minor_grid_size: int = 20,
    minor_grid_color: str = "#f0f0f0",
) -> ScriptOutput:
    """Enable infinite canvas with pan/zoom.

    Creates signals: {signal}_pan_x/y, {signal}_zoom, {signal}_is_panning.
    Functions: {signal}_reset_view(), {signal}_zoom_in/out().
    Use with ds_canvas_viewport() and ds_canvas_container().
    """
    config = {
        "signal": signal,
        "enablePan": enable_pan,
        "enableZoom": enable_zoom,
        "minZoom": min_zoom,
        "maxZoom": max_zoom,
        "touchEnabled": touch_enabled,
        "enableGrid": enable_grid,
        "gridSize": grid_size,
        "gridColor": grid_color,
        "minorGridSize": minor_grid_size,
        "minorGridColor": minor_grid_color,
    }

    if enable_grid:
        from .xtend import Style

        grid_styles = Style(f"""
        [data-canvas-viewport] {{
            background: #fafafa;
        }}
        
        [data-canvas-container]::before {{
            content: '';
            position: absolute;
            top: -50000px;
            left: -50000px;
            width: 100000px;
            height: 100000px;
            background:
                linear-gradient(to right, {grid_color} 1px, transparent 1px),
                linear-gradient(to bottom, {grid_color} 1px, transparent 1px),
                linear-gradient(to right, {minor_grid_color} 1px, transparent 1px),
                linear-gradient(to bottom, {minor_grid_color} 1px, transparent 1px);
            background-size: {grid_size}px {grid_size}px, {grid_size}px {grid_size}px, {minor_grid_size}px {minor_grid_size}px, {minor_grid_size}px {minor_grid_size}px;
            background-position: 0 0, 0 0, 0 0, 0 0;
            pointer-events: none;
            z-index: -1;
        }}
        """)
        return [_load_handler("canvas", config), grid_styles]

    return _load_handler("canvas", config)


def get_bundle_stats() -> dict:
    """Get JavaScript bundle statistics."""
    return _assets.get_bundle_info()


def check_assets() -> dict:
    """Check asset availability status."""
    return _assets.check_assets()


# =============================================================================
# SCRIPT GENERATION ENGINE - How handlers work
# =============================================================================


def _load_handler(handler_name: str, config: dict = None) -> ScriptOutput:
    """Load and register a Datastar plugin handler."""
    config_json = json.dumps(config) if config else "{}"
    datastar_cdn = f"https://cdn.jsdelivr.net/gh/starfederation/datastar@{DATASTAR_VERSION}/bundles/datastar.js"

    return Script(
        f"""
        import handlerPlugin from '/static/js/handlers/{handler_name}.js';
        import {{ load, apply }} from '{datastar_cdn}';
        
        if (handlerPlugin.setConfig) handlerPlugin.setConfig({config_json});
        load(handlerPlugin);
        apply();
    """,
        type="module",
    )


def get_production_script(bundle_name: str, use_external: bool = True, fallback: bool = True, **kwargs) -> ScriptOutput:
    """Production script with CDN fallback support."""
    if not use_external:
        return Script(content, **kwargs) if (content := _assets.get_asset_content(bundle_name)) else None

    if not (script_url := _assets.get_asset_url(bundle_name)):
        return Script(content, **kwargs) if (content := _assets.get_asset_content(bundle_name)) else None

    if not fallback:
        return Script(src=script_url, defer=True, **kwargs)

    if not (fallback_content := _assets.get_asset_content(bundle_name)):
        return Script(src=script_url, defer=True, **kwargs)

    return [
        Script(_FALLBACK_SCRIPT),
        Script(
            src=script_url,
            defer=True,
            type="module",
            onload=f"window.__starhtml_register_success('{bundle_name}')",
            onerror=f"window.__starhtml_run_with_fallback('{bundle_name}', function() {{ {fallback_content} }})",
            **kwargs,
        ),
    ]


# =============================================================================
# ASSET MANAGEMENT - Tools for finding and reading JavaScript files
# =============================================================================


class PackageAssetManager:
    """JavaScript asset management with manifest-based cache busting."""

    def __init__(self):
        self.package_dir = Path(__file__).parent.resolve()
        self.js_dir = self.package_dir / "static" / "js"
        self._manifest = self._load_manifest()

    @cached_property
    def is_development(self) -> bool:
        """Check if we're in development mode based on whether JS bundles exist."""
        return not self.js_dir.exists()

    def _load_manifest(self) -> dict:
        """Load asset manifest for cache-busted filenames."""
        manifest_file = self.js_dir / "manifest.json"
        if not manifest_file.is_file():
            return {}
        try:
            return json.loads(manifest_file.read_text())
        except (OSError, json.JSONDecodeError):
            return {}

    def _get_asset_path(self, bundle_name: str) -> Path | None:
        """Resolve asset path using manifest for cache-busted filenames."""
        filename = f"{bundle_name}.min.js"
        if files := self._manifest.get("files"):
            filename = files.get(f"{bundle_name}.js", filename)

        if (asset_file := self.js_dir / filename).is_file():
            return asset_file

        fallback = self.js_dir / f"{bundle_name}.min.js"
        return fallback if fallback.is_file() and fallback != asset_file else None

    def get_asset_url(self, bundle_name: str) -> str | None:
        """Bundle URL with cache-busted filename."""
        return f"/static/js/{path.name}" if (path := self._get_asset_path(bundle_name)) else None

    def get_asset_content(self, bundle_name: str) -> str:
        """Bundle content for inline embedding."""
        if not (path := self._get_asset_path(bundle_name)):
            return ""
        try:
            return path.read_text(encoding="utf-8")
        except Exception:
            return ""

    def get_bundle_info(self) -> dict:
        """Bundle metadata and development status."""
        return {
            "available_bundles": list(self._manifest.get("files", {}).keys()),
            "bundle_sizes": self._manifest.get("bundles", {}),
            "is_development": self.is_development,
        }

    def check_assets(self) -> dict:
        """Asset directory and manifest status."""
        return {
            "js_dir_exists": self.js_dir.exists(),
            "manifest_loaded": bool(self._manifest),
            "manifest_entries": len(self._manifest.get("files", {})),
            "package_dir": str(self.package_dir),
        }


_FALLBACK_SCRIPT = """
window.__starhtml_fallback_registry ??= {};
window.__starhtml_run_with_fallback = function(name, fallbackFn) {
    if (window.__starhtml_fallback_registry[name]) return;
    fallbackFn();
    window.__starhtml_fallback_registry[name] = true;
};
window.__starhtml_register_success = function(name) {
    window.__starhtml_fallback_registry[name] = true;
};
"""

_assets = PackageAssetManager()
