"""Minimal Datastar plugin system - glue between Python templates and JS plugins."""

import json
import time
from pathlib import Path

from .datastar import js
from .xtend import Script, Style

_STATIC_PATH = Path(__file__).parent / "static" / "js" / "plugins"
_PKG_NAME = "starhtml/plugins"


class PluginInstance:
    """A named plugin instance with signal/method references."""

    def __init__(
        self,
        name,
        base_name,
        signals,
        methods,
        inline,
        is_action,
        config,
        static_path=None,
        package_name=None,
        critical_css=None,
    ):
        self.name, self.config = name, config
        self._base_name, self._inline, self._is_action = base_name, inline, is_action
        self._static_path, self._package_name, self._critical_css = static_path, package_name, critical_css
        self._refs = {s: js(f"${name}_{s}") for s in signals}
        self._refs.update({m: js(f"window.__{name}.{m}") for m in methods})

    @property
    def inline(self):
        return self._inline

    @property
    def is_action(self):
        return self._is_action

    def __getattr__(self, attr):
        if attr.startswith("_"):
            raise AttributeError(f"'{type(self).__name__}' has no attribute '{attr}'")
        if attr in self._refs:
            return self._refs[attr]
        raise AttributeError(f"Plugin '{self.name}' has no signal or method '{attr}'")

    def __str__(self):
        return self.name

    def __repr__(self):
        return f"PluginInstance({self.name!r})"

    def get_package_name(self) -> str:
        return self._package_name or _PKG_NAME

    def get_static_path(self) -> Path | None:
        return self._static_path or _STATIC_PATH

    def get_headers(self, base_url: str) -> tuple:
        return plugins_hdrs(self, base_url=base_url)


class Plugin:
    """Factory for creating plugin instances. Delegates to lazy singleton when accessed directly."""

    def __init__(
        self,
        base_name,
        signals=(),
        methods=(),
        inline=None,
        is_action=False,
        static_path=None,
        package_name=None,
        critical_css=None,
    ):
        self._base_name, self._signals, self._methods = base_name, signals, methods
        self._inline, self._is_action, self._default = inline, is_action, None
        self._static_path, self._package_name = static_path, package_name
        self._critical_css = critical_css

    def __call__(self, *, name=None, **config):
        return PluginInstance(
            name or self._base_name,
            self._base_name,
            self._signals,
            self._methods,
            self._inline,
            self._is_action,
            config,
            self._static_path,
            self._package_name,
            self._critical_css,
        )

    def __getattr__(self, attr):
        if attr.startswith("_"):
            raise AttributeError(f"'{type(self).__name__}' has no attribute '{attr}'")
        if self._default is None:
            self._default = self()
        return getattr(self._default, attr)

    def __repr__(self):
        return f"Plugin({self._base_name!r})"

    @property
    def name(self):
        return self._base_name

    @property
    def inline(self):
        return self._inline

    @property
    def is_action(self):
        return self._is_action

    def get_package_name(self) -> str:
        return self._package_name or _PKG_NAME

    def get_static_path(self) -> Path | None:
        return self._static_path or _STATIC_PATH

    def get_headers(self, base_url: str) -> tuple:
        return plugins_hdrs(self, base_url=base_url)


def _snake2camel(s: str) -> str:
    """Convert snake_case to camelCase."""
    parts = s.split("_")
    return parts[0] + "".join(p.capitalize() for p in parts[1:])


def _get_plugin_config(p) -> dict | None:
    """Get JS config dict from plugin, converting snake_case to camelCase."""
    config = getattr(p, "config", None)
    if not config:
        return None
    return {"signal": p.name, **{_snake2camel(k): v for k, v in config.items()}}


def plugins_hdrs(
    *plugins,
    datastar_path: str = "/static/datastar.js",
    base_url: str = "/_pkg/starhtml/plugins",
    debug: bool = False,
) -> tuple:
    """Generate import map and loader script for plugins."""
    if not plugins:
        return ()

    v = f"?v={int(time.time())}" if debug else ""

    import_map = {
        "imports": {
            "datastar": f"{datastar_path}{v}",
            **{
                f"@starhtml/plugins/{p._base_name}": f"{base_url}/{p._base_name}.js{v}"
                for p in plugins
                if not p._inline
            },
        }
    }

    # Build loader: import/define each plugin, then register it
    lines = []
    for i, p in enumerate(plugins):
        reg = "action" if p._is_action else "attribute"
        lines.append(
            f"const plugin_{i}={p._inline};"
            if p._inline
            else f"import plugin_{i} from'@starhtml/plugins/{p._base_name}';"
        )
        # Pass config to plugin via setConfig if available
        config = _get_plugin_config(p)
        if config:
            lines.append(f"plugin_{i}.setConfig({json.dumps(config)});")
        lines.append(f"{reg}(plugin_{i});")

    needed = []
    if any(not p._is_action for p in plugins):
        needed.append("attribute")
    if any(p._is_action for p in plugins):
        needed.append("action")
    js_code = f"import{{{','.join(needed)}}}from'datastar';\n" + "\n".join(lines)

    # Critical CSS prevents flash of unprocessed content
    css = "".join(p._critical_css for p in plugins if p._critical_css)

    return (
        *((Style(css),) if css else ()),
        Script(json.dumps(import_map), type="importmap"),
        Script(js_code, type="module"),
    )


CLIPBOARD_CODE = """{
    name: 'clipboard',
    apply: async ({ el, evt, error }, text, signal, timeout = 2000) => {
        const setSignal = (value) => {
            if (signal) {
                document.dispatchEvent(new CustomEvent('datastar-signal-patch', {
                    detail: { [signal]: value }
                }));
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

clipboard = Plugin("clipboard", inline=CLIPBOARD_CODE, is_action=True)
persist = Plugin(
    "persist",
    critical_css="[data-persist]:not([data-persist-ready]){visibility:hidden}",
)
scroll = Plugin(
    "scroll",
    signals=(
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
    ),
)
resize = Plugin(
    "resize",
    signals=(
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
    ),
)
canvas = Plugin(
    "canvas",
    signals=(
        "pan_x",
        "pan_y",
        "zoom",
        "context_menu_x",
        "context_menu_y",
        "context_menu_screen_x",
        "context_menu_screen_y",
    ),
    methods=("resetView", "zoomIn", "zoomOut"),
)
drag = Plugin(
    "drag",
    signals=("is_dragging", "element_id", "x", "y", "drop_zone", "has_drop_zone"),
    critical_css="[data-drag]{touch-action:none}",
)
position = Plugin(
    "position",
    signals=("x", "y", "placement", "visible", "is_positioning"),
    critical_css="[data-positioning=true]:not([popover]){visibility:hidden!important;opacity:0!important}[data-positioning=false]:not([popover]){visibility:visible!important;opacity:1!important;transition:opacity 150ms ease-out}",
)
split = Plugin(
    "split",
    signals=(
        "position",
        "sizes",
        "is_dragging",
        "direction",
        "collapsed",
    ),
)

# Content processor plugins (use data-markdown, data-katex, data-mermaid)
# Critical CSS hides raw content until JS processes it (prevents flash)
markdown = Plugin(
    "markdown",
    critical_css="[data-markdown]:not(:has(p,h1,h2,h3,ul,ol,blockquote)){visibility:hidden;position:absolute;pointer-events:none}",
)
katex = Plugin(
    "katex",  # Note: requires KaTeX CSS for proper rendering
    critical_css="[data-katex]:not(:has(.katex)){visibility:hidden;position:absolute;pointer-events:none}",
)
mermaid = Plugin(
    "mermaid",
    critical_css="[data-mermaid]:not(:has(svg)){visibility:hidden;position:absolute;pointer-events:none}",
)

__all__ = [
    "Plugin",
    "PluginInstance",
    "plugins_hdrs",
    "canvas",
    "clipboard",
    "drag",
    "katex",
    "markdown",
    "mermaid",
    "persist",
    "position",
    "resize",
    "scroll",
    "split",
]
