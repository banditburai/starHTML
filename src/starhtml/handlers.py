"""StarHTML Datastar plugin handlers with bundled signals."""

import json
import time
from dataclasses import dataclass
from functools import cached_property
from pathlib import Path
from typing import Any

from fastcore.xml import FT

from .datastar import Signal, js
from .xtend import Script

__all__ = [
    "HandlerBundle",
    "PackageAssetManager",
    "get_bundle_stats",
    "check_assets",
    "persist_handler",
    "scroll_handler",
    "resize_handler",
    "drag_handler",
    "canvas_handler",
    "position_handler",
    "split_handler",
    "clipboard_action",
]


@dataclass(frozen=True)
class HandlerBundle:
    """Bundle containing handler script(s) and signal definitions."""

    scripts: list[FT]
    signals: dict[str, Any]

    def __iter__(self):
        return iter(self.scripts)

    def __getattr__(self, name):
        if name in self.signals:
            return self.signals[name]
        raise AttributeError(f"'{self.__class__.__name__}' has no signal '{name}'")


def _load_handler(name: str, config: dict | None = None, debug: bool = False) -> list[FT]:
    from .starapp import DATASTAR_VERSION

    config_json = json.dumps(config or {})
    datastar_cdn = f"https://cdn.jsdelivr.net/gh/starfederation/datastar@{DATASTAR_VERSION}/bundles/datastar.js"
    cache_bust = f"?v={int(time.time())}" if debug else ""

    return [
        Script(
            f"""
        import handlerPlugin from '/static/js/handlers/{name}.js{cache_bust}';
        import {{ load, apply }} from '{datastar_cdn}';
        
        if (!window.__starhtml_handlers) window.__starhtml_handlers = {{}};
        
        if (!window.__starhtml_handlers['{name}']) {{
            window.__starhtml_handlers['{name}'] = handlerPlugin;
            load(handlerPlugin);
            apply();
            {f'console.log("[{name.upper()}] Handler loaded");' if debug else ""}
        }}
        
        if (handlerPlugin.setConfig) {{
            handlerPlugin.setConfig({config_json});
            {f'console.log("[{name.upper()}] Configured:", {config_json});' if debug else ""}
        }}
    """,
            type="module",
        )
    ]


class PackageAssetManager:
    """JavaScript asset management with manifest-based cache busting."""

    def __init__(self):
        self.package_dir = Path(__file__).parent.resolve()
        self.js_dir = self.package_dir / "static" / "js"
        self._manifest = self._load_manifest()

    @cached_property
    def is_development(self) -> bool:
        return not self.js_dir.exists()

    def _load_manifest(self) -> dict:
        manifest_file = self.js_dir / "manifest.json"
        if not manifest_file.is_file():
            return {}
        try:
            return json.loads(manifest_file.read_text())
        except (OSError, json.JSONDecodeError):
            return {}

    def _get_asset_path(self, bundle_name: str) -> Path | None:
        if files := self._manifest.get("files"):
            filename = files.get(f"{bundle_name}.js", f"{bundle_name}.min.js")
        else:
            filename = f"{bundle_name}.min.js"
        asset_file = self.js_dir / filename
        return asset_file if asset_file.is_file() else None

    def get_asset_url(self, bundle_name: str) -> str | None:
        return f"/static/js/{path.name}" if (path := self._get_asset_path(bundle_name)) else None

    def get_asset_content(self, bundle_name: str) -> str:
        if not (path := self._get_asset_path(bundle_name)):
            return ""
        try:
            return path.read_text(encoding="utf-8")
        except Exception:
            return ""

    def get_bundle_info(self) -> dict:
        return {
            "available_bundles": list(self._manifest.get("files", {}).keys()),
            "bundle_sizes": self._manifest.get("bundles", {}),
            "is_development": self.is_development,
        }

    def check_assets(self) -> dict:
        return {
            "js_dir_exists": self.js_dir.exists(),
            "manifest_loaded": bool(self._manifest),
            "manifest_entries": len(self._manifest.get("files", {})),
            "package_dir": str(self.package_dir),
        }


def get_bundle_stats() -> dict:
    try:
        return PackageAssetManager().get_bundle_info()
    except Exception as e:
        return {"error": str(e)}


def check_assets() -> dict:
    try:
        return PackageAssetManager().check_assets()
    except Exception as e:
        return {"error": str(e)}


def drag_handler(
    signal: str = "drag",
    mode: str = "freeform",
    throttle_ms: int = 16,
    constrain_to_parent: bool = False,
    touch_enabled: bool = True,
    debug: bool = False,
) -> HandlerBundle:
    """Enable drag-and-drop with reactive signal management."""
    signals = {
        "is_dragging": js(f"${signal}_is_dragging"),
        "element_id": js(f"${signal}_element_id"),
        "x": js(f"${signal}_x"),
        "y": js(f"${signal}_y"),
        "drop_zone": js(f"${signal}_drop_zone"),
    }

    if mode in ("sortable", "freeform"):
        signals["zone_items"] = lambda zone: js(f"${signal}_zone_{zone}_items")

    return HandlerBundle(
        _load_handler(
            "drag",
            {
                "signal": signal,
                "mode": mode,
                "throttleMs": throttle_ms,
                "constrainToParent": constrain_to_parent,
                "touchEnabled": touch_enabled,
            },
            debug=debug,
        ),
        signals,
    )


def scroll_handler(debug: bool = False) -> HandlerBundle:
    """Track scroll position, velocity, and visibility."""
    signal_names = [
        "x",
        "y",
        "direction",
        "velocity",
        "delta",
        "visible",
        "visible_percent",
        "progress",
        "page_progress",
        "element_top",
        "element_bottom",
        "is_top",
        "is_bottom",
    ]

    return HandlerBundle(_load_handler("scroll", debug=debug), {name: js(f"$scroll_{name}") for name in signal_names})


def resize_handler(
    signal: str = "resize",
    throttle_ms: int = 16,
    track_element: bool = False,
    track_both: bool = False,
    debug: bool = False,
) -> HandlerBundle:
    """Track window/element resize events with responsive state."""
    signal_names = [
        "width",
        "height",
        "window_width",
        "window_height",
        "aspect_ratio",
        "current_breakpoint",
        "is_mobile",
        "is_tablet",
        "is_desktop",
        "xs",
        "sm",
        "md",
        "lg",
        "xl",
    ]

    return HandlerBundle(
        _load_handler(
            "resize",
            {"signal": signal, "throttleMs": throttle_ms, "trackElement": track_element, "trackBoth": track_both},
            debug=debug,
        ),
        {name: js(f"$resize_{name}") for name in signal_names},
    )


def persist_handler(debug: bool = False) -> HandlerBundle:
    """Auto-persist signals to localStorage/sessionStorage."""
    return HandlerBundle(_load_handler("persist", debug=debug), {})


def canvas_handler(
    signal: str = "canvas",
    enable_pan: bool = True,
    enable_zoom: bool = True,
    min_zoom: float = 0.1,
    max_zoom: float = 10.0,
    touch_enabled: bool = True,
    background_color: str = "#f8f9fa",
    enable_grid: bool = True,
    grid_size: int = 100,
    grid_color: str = "#e0e0e0",
    minor_grid_size: int = 20,
    minor_grid_color: str = "#f0f0f0",
    debug: bool = False,
) -> HandlerBundle:
    """Canvas drawing handler with infinite pan/zoom capabilities."""
    signal_names = [
        "pan_x",
        "pan_y",
        "zoom",
        "reset_view",
        "zoom_in",
        "zoom_out",
        "context_menu_x",
        "context_menu_y",
        "context_menu_screen_x",
        "context_menu_screen_y",
    ]

    return HandlerBundle(
        _load_handler(
            "canvas",
            {
                "signal": signal,
                "enablePan": enable_pan,
                "enableZoom": enable_zoom,
                "minZoom": min_zoom,
                "maxZoom": max_zoom,
                "touchEnabled": touch_enabled,
                "backgroundColor": background_color,
                "enableGrid": enable_grid,
                "gridSize": grid_size,
                "gridColor": grid_color,
                "minorGridSize": minor_grid_size,
                "minorGridColor": minor_grid_color,
            },
            debug=debug,
        ),
        {name: js(f"${signal}_{name}") for name in signal_names},
    )


def position_handler(
    signal: str = "position",
    defaults: dict[str, Any] | None = None,
    auto_update: dict[str, bool] | None = None,
    debug: bool = False,
) -> HandlerBundle:
    """Position floating elements using Floating UI."""
    config = {"signal": signal}
    if defaults:
        config["defaults"] = defaults
    if auto_update:
        config["autoUpdate"] = auto_update

    signal_names = ["x", "y", "placement", "visible", "is_positioning"]

    return HandlerBundle(
        _load_handler("position", config, debug=debug), {name: js(f"${signal}_{name}") for name in signal_names}
    )


def split_handler(
    signal: str = "split",
    direction: str = "horizontal",
    min_size: int | list[int] = 10,
    max_size: int | list[int] = 90,
    default_sizes: list[int] | None = None,
    default_position: int = 50,
    persist: bool = True,
    persist_key: str = "split-position",
    snap_points: list[int] | None = None,
    snap_offset: int = 5,
    collapsible: bool | list[bool] = False,
    collapse_size: int = 40,
    keyboard: bool = True,
    nested: bool = False,
    corners: bool = False,
    responsive: bool = False,
    responsive_breakpoint: int = 768,
    debug: bool = False,
) -> HandlerBundle:
    """Split panel handler with CSS custom properties for styling."""

    config = {
        "signal": signal,
        "direction": direction,
        "minSize": min_size,
        "maxSize": max_size,
        "persist": persist,
        "persistKey": persist_key,
        "snapOffset": snap_offset,
        "collapseSize": collapse_size,
        "keyboard": keyboard,
        "nested": nested,
        "corners": corners,
        "responsive": responsive,
        "responsiveBreakpoint": responsive_breakpoint,
    }

    if default_sizes:
        config["defaultSizes"] = default_sizes
    else:
        config["defaultPosition"] = default_position

    if snap_points:
        config["snapPoints"] = snap_points

    if collapsible is not False:
        config["collapsible"] = collapsible

    return HandlerBundle(
        _load_handler("split", config, debug=debug),
        {
            "position": Signal(f"{signal}_position", default_position if not default_sizes else 50),
            "sizes": Signal(f"{signal}_sizes", default_sizes or [50, 50]),
            "is_dragging": Signal(f"{signal}_is_dragging", False),
            "direction": Signal(f"{signal}_direction", direction),
            "collapsed": Signal(f"{signal}_collapsed", []),
        },
    )


def clipboard_action() -> dict:
    return {
        "type": "action",
        "name": "clipboard",
        "code": """{
    type: 'action',
    name: 'clipboard',
    fn: ({ peek, mergePatch }, text, signal, timeout = 2000) => {
        const setSignal = (value) => signal && peek(() => mergePatch({ [signal]: value }));
        
        const fallback = () => {
            const ta = document.createElement('textarea');
            ta.value = text;
            ta.style.cssText = 'position:fixed;top:-9999px;opacity:0;';
            document.body.appendChild(ta);
            ta.select();
            try {
                setSignal(document.execCommand('copy'));
                setTimeout(() => setSignal(false), timeout);
            } finally {
                document.body.removeChild(ta);
            }
        };
        
        if (navigator.clipboard?.writeText) {
            navigator.clipboard.writeText(text).then(() => {
                setSignal(true);
                setTimeout(() => setSignal(false), timeout);
            }).catch(fallback);
        } else {
            fallback();
        }
    }
}""",
    }
