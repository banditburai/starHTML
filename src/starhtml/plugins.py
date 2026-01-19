"""Datastar plugin system: attributes (scroll, canvas) and actions (clipboard)."""

import functools
import inspect
import json
import time
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Callable

from fastcore.xml import FT

from .datastar import Signal, js
from .xtend import Script


class PluginType(Enum):
    """Type of Datastar plugin."""

    ATTRIBUTE = "attribute"
    ACTION = "action"


def _to_camel_case(snake_str: str) -> str:
    """Convert snake_case to camelCase for JavaScript config."""
    components = snake_str.split("_")
    return components[0] + "".join(x.title() for x in components[1:])


@dataclass(frozen=True)
class PluginDef:
    """Datastar plugin definition with config, signals, and static/inline JavaScript."""

    name: str
    config: dict[str, Any]
    signals: dict[str, Any]
    static_path: Path
    inline: str | None = None
    plugin_type: PluginType = PluginType.ATTRIBUTE

    def __getattr__(self, name: str):
        """Access signals as attributes (e.g., canvas.zoom)."""
        if name in self.signals:
            return self.signals[name]
        raise AttributeError(f"'{self.__class__.__name__}' has no signal '{name}'")

    @property
    def is_inline(self) -> bool:
        """Check if this plugin uses inline JavaScript."""
        return self.inline is not None

    def get_package_name(self) -> str:
        """Return package name for URL routing."""
        return "starhtml/plugins"

    def get_static_path(self) -> Path:
        """Return filesystem path to static files."""
        return self.static_path

    def get_headers(self, base_url: str) -> tuple:
        """Generate header elements for this plugin."""
        return plugins_hdrs(self, base_url=base_url)


_plugin_registry: dict[str, Callable] = {}


def plugin(name: str, inline: str | None = None, plugin_type: PluginType = PluginType.ATTRIBUTE):
    """Decorator to create Datastar plugin. Captures snake_case params, converts to camelCase config, returns PluginDef."""

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> PluginDef:
            sig = inspect.signature(func)
            bound = sig.bind(*args, **kwargs)
            bound.apply_defaults()
            config = {_to_camel_case(k): v for k, v in bound.arguments.items()}
            signals = func(*args, **kwargs)

            return PluginDef(
                name=name,
                config=config,
                signals=signals,
                static_path=Path(__file__).parent / "static" / "js" / "plugins",
                inline=inline,
                plugin_type=plugin_type,
            )

        _plugin_registry[name] = wrapper
        return wrapper

    return decorator


def get_registered_plugins() -> list[Callable]:
    """Get all registered plugin functions."""
    return list(_plugin_registry.values())


def _deduplicate_plugins(plugins: tuple[PluginDef, ...]) -> list[dict]:
    """Validate and deduplicate plugins, return configs."""
    plugin_configs = []
    plugin_names = set()

    for plugin in plugins:
        if not isinstance(plugin, PluginDef):
            raise TypeError(f"Expected PluginDef, got {type(plugin).__name__}")

        if not plugin.name:
            raise ValueError("PluginDef missing required 'name' field")

        if plugin.name in plugin_names:
            continue

        plugin_names.add(plugin.name)
        plugin_configs.append({
            "name": plugin.name,
            "config": plugin.config,
            "inline": plugin.inline,
            "plugin_type": plugin.plugin_type,
        })

    return plugin_configs


def _build_import_statements(plugin_configs: list[dict], base_url: str, cache_bust: str) -> list[str]:
    """Generate JavaScript import statements for plugins."""
    imports = []
    for i, plugin in enumerate(plugin_configs):
        if plugin.get("inline"):
            imports.append(f"const plugin_{i} = {plugin['inline']};")
        else:
            plugin_url = f"{base_url}/{plugin['name']}.js{cache_bust}"
            imports.append(f"const plugin_{i} = await import('{plugin_url}').then(m => m.default);")
    return imports


def _build_init_statements(plugin_configs: list[dict], debug: bool) -> list[str]:
    """Generate JavaScript initialization statements for plugins."""
    inits = []
    for i, plugin in enumerate(plugin_configs):
        name = plugin["name"]
        config_json = json.dumps(plugin["config"])
        inline = plugin.get("inline")
        plugin_type = plugin.get("plugin_type", PluginType.ATTRIBUTE)

        if not inline:
            if debug:
                inits.append(f"plugin_{i}.setConfig?.({config_json}); console.log('[{name.upper()}] Configured:', {config_json});")
                inits.append(f"console.log('[{name.upper()}] Handler loaded');")
            else:
                inits.append(f"plugin_{i}.setConfig?.({config_json});")

        if plugin_type == PluginType.ACTION:
            inits.append(f"action(plugin_{i});")
        else:
            inits.append(f"attribute(plugin_{i});")

    return inits


def _get_datastar_imports(plugin_configs: list[dict]) -> str:
    """Determine which Datastar functions to import based on plugin types."""
    has_action = any(p.get("plugin_type") == PluginType.ACTION for p in plugin_configs)
    has_attribute = any(p.get("plugin_type") != PluginType.ACTION for p in plugin_configs)

    imports = []
    if has_attribute:
        imports.append("attribute")
    if has_action:
        imports.append("action")
    imports.extend(["getPath", "mergePatch", "effect"])

    return ", ".join(imports)


def plugins_hdrs(
    *plugins: PluginDef,
    datastar_path: str = "/static/datastar.js",
    base_url: str = "/_pkg/starhtml/plugins",
    debug: bool = False,
) -> tuple[FT, ...]:
    """Generate batched header script for plugins. Loads all plugins in parallel and registers with Datastar."""
    if not plugins:
        return tuple()

    plugin_configs = _deduplicate_plugins(plugins)
    cache_bust = f"?v={int(time.time())}" if debug else ""

    plugin_imports = _build_import_statements(plugin_configs, base_url, cache_bust)
    plugin_inits = _build_init_statements(plugin_configs, debug)
    import_str = _get_datastar_imports(plugin_configs)

    js_code = f"""
        const {{ {import_str} }} = await import('{datastar_path}');

        if (!window.__datastar_getPath) {{
            Object.assign(window, {{
                __datastar_getPath: getPath,
                __datastar_mergePatch: mergePatch,
                __datastar_effect: effect
            }});
        }}

        {chr(10).join(plugin_imports)}

        {chr(10).join(plugin_inits)}
    """

    return (Script(js_code, type="module"),)


CLIPBOARD_CODE = """{
    name: 'clipboard',
    apply: async ({ el, evt, error }, text, signal, timeout = 2000) => {
        const setSignal = (value) => {
            if (signal) {
                const event = new CustomEvent('datastar-signal-patch', {
                    detail: { [signal]: value }
                });
                document.dispatchEvent(event);
            }
        };

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
}"""


@plugin("clipboard", inline=CLIPBOARD_CODE, plugin_type=PluginType.ACTION)
def clipboard(debug: bool = False):
    """Copy text to clipboard with optional success signal. Action-only plugin with inline JavaScript."""
    return {}  # No Python-accessible signals for action-only plugins


@plugin("persist")
def persist(debug: bool = False):
    """Auto-persist signals to localStorage/sessionStorage."""
    return {}  # No signals for persist plugin


@plugin("scroll")
def scroll(debug: bool = False):
    """Track scroll position, velocity, direction, visibility, and progress."""
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

    return {name: js(f"$scroll_{name}") for name in signal_names}


@plugin("resize")
def resize(
    signal: str = "resize",
    throttle_ms: int = 16,
    track_element: bool = False,
    track_both: bool = False,
    debug: bool = False,
):
    """Track window/element resize with responsive breakpoints."""
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

    return {name: js(f"$resize_{name}") for name in signal_names}


@plugin("canvas")
def canvas(
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
):
    """Canvas with infinite pan/zoom, grid, and touch support."""
    value_signals = [
        "pan_x",
        "pan_y",
        "zoom",
        "context_menu_x",
        "context_menu_y",
        "context_menu_screen_x",
        "context_menu_screen_y",
    ]

    signals = {name: js(f"${signal}_{name}") for name in value_signals}
    signals["reset_view"] = js(f"window.__{signal}.resetView")
    signals["zoom_in"] = js(f"window.__{signal}.zoomIn")
    signals["zoom_out"] = js(f"window.__{signal}.zoomOut")

    return signals


@plugin("drag")
def drag(
    signal: str = "drag",
    mode: str = "freeform",
    throttle_ms: int = 16,
    constrain_to_parent: bool = False,
    touch_enabled: bool = True,
    debug: bool = False,
):
    """Drag-and-drop with freeform, sortable, or constrained modes."""
    signals = {
        "is_dragging": js(f"${signal}_is_dragging"),
        "element_id": js(f"${signal}_element_id"),
        "x": js(f"${signal}_x"),
        "y": js(f"${signal}_y"),
        "drop_zone": js(f"${signal}_drop_zone"),
        "has_drop_zone": js(f"${signal}_has_drop_zone"),
    }

    if mode in ("sortable", "freeform"):
        signals["zone_items"] = lambda zone: js(f"${signal}_zone_{zone}_items")

    return signals


@plugin("position")
def position(
    signal: str = "position",
    defaults: dict | None = None,
    auto_update: dict | None = None,
    debug: bool = False,
):
    """Position floating elements using Floating UI."""
    signal_names = ["x", "y", "placement", "visible", "is_positioning"]

    return {name: js(f"${signal}_{name}") for name in signal_names}


@plugin("split")
def split(
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
):
    """Split panel with drag, snap, collapse, and persistence."""
    return {
        "position": Signal(f"{signal}_position", default_position if not default_sizes else 50),
        "sizes": Signal(f"{signal}_sizes", default_sizes or [50, 50]),
        "is_dragging": Signal(f"{signal}_is_dragging", False),
        "direction": Signal(f"{signal}_direction", direction),
        "collapsed": Signal(f"{signal}_collapsed", []),
    }


__all__ = [
    "PluginDef",
    "PluginType",
    "plugin",
    "get_registered_plugins",
    "plugins_hdrs",
    # Built-in plugins
    "canvas",
    "clipboard",
    "drag",
    "persist",
    "position",
    "resize",
    "scroll",
    "split",
]
