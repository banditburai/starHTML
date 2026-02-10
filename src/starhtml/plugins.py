"""Minimal Datastar plugin system - glue between Python templates and JS plugins."""

import json
import re
import time
from pathlib import Path
from typing import Any, Literal

from .datastar import Expr, _JSRaw, _to_js, js
from .xtend import Script, Style

_STATIC_PATH = Path(__file__).parent / "static" / "js" / "plugins"
_PKG_NAME = "starhtml/plugins"
_DEFAULT_PREFIX = "/_pkg"
_CSS_IMPORT_RE = re.compile(r"@import\s+url\([^)]*\)\s*;?")


def _snake2camel(s: str) -> str:
    """Convert snake_case to camelCase."""
    parts = s.split("_")
    return parts[0] + "".join(p.capitalize() for p in parts[1:])


class PluginInstance:
    """A named plugin instance with signal/method references."""

    def __init__(
        self,
        name,
        base_name,
        code,
        signals,
        methods,
        config,
        static_path=None,
        package_name=None,
        critical_css=None,
    ):
        self.name, self.config = name, config
        self._base_name = base_name
        self._code = code
        self._signals, self._methods = signals, methods
        self._static_path, self._package_name, self._critical_css = static_path, package_name, critical_css
        self._refs = {s: js(f"${name}_{s}") for s in signals}
        self._refs.update({m: js(f"window.__{name}.{_snake2camel(m)}") for m in methods})

    @property
    def code(self):
        return self._code

    @property
    def has_attribute(self):
        """True if this plugin registers with attribute()."""
        return bool(self._signals or self._methods or not self._code)

    @property
    def has_action(self):
        """True if this plugin registers with action()."""
        return bool(self._code)

    def __getattr__(self, attr: str) -> Any:
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

    def get_headers(self, pkg_prefix: str) -> tuple:
        return plugins_hdrs(self, pkg_prefix=pkg_prefix)


class _ActionMethod:
    """Callable that generates @plugin('method', args) syntax."""

    def __init__(self, plugin_name: str, method_name: str):
        self._plugin_name = plugin_name
        # Strip trailing _ so Python-safe names (e.g., from_) map to JS names (from)
        self._js_name = method_name.rstrip("_")

    def __call__(self, *args, **kwargs) -> _JSRaw:
        parts = [_to_js(self._js_name, allow_expressions=True)]
        for arg in args:
            parts.append(_to_js(arg, allow_expressions=True))
        if kwargs:
            parts.append(_to_js(kwargs, allow_expressions=True, wrap_objects=False))
        return _JSRaw(f"@{self._plugin_name}({', '.join(parts)})")

    def __repr__(self):
        return f"@{self._plugin_name}('{self._js_name}', ...)"


class Plugin:
    """Factory for creating plugin instances with optional action methods.

    Plugins can expose action methods that generate @plugin('method', args) syntax:
        motion.animate("#el", x=100)  # → @motion('animate', '#el', {x: 100})
        clipboard.copy("text")        # → @clipboard('text')

    Actions: tuple of method names (generic) or dict mapping names to custom callables.
    """

    def __init__(
        self,
        base_name,
        code=None,
        signals=(),
        methods=(),
        actions=(),
        file_actions=False,
        extra_attributes=(),
        static_path=None,
        package_name=None,
        critical_css=None,
    ):
        self._base_name = base_name
        self._code = code
        self._signals, self._methods = signals, methods
        self._actions = actions if isinstance(actions, dict) else {name: None for name in actions}
        self._file_actions = file_actions
        self._extra_attributes = extra_attributes
        self._default = None
        self._static_path, self._package_name = static_path, package_name
        self._critical_css = critical_css

    def __call__(self, *args, name=None, **kwargs):
        """Call plugin as default action or create named PluginInstance.

        If called with args/kwargs (other than name=) and a default action ("") is defined,
        invokes the default action. Otherwise creates a PluginInstance.
        """
        has_action_args = args or (kwargs and name is None)
        if has_action_args and "" in self._actions:
            return self._actions[""](*args, **kwargs)

        if args:
            raise TypeError(
                f"Plugin '{self._base_name}' has no default action. "
                f"Use a method like {self._base_name}.method_name(...)"
            )
        return PluginInstance(
            name or self._base_name,
            self._base_name,
            self._code,
            self._signals,
            self._methods,
            kwargs,
            self._static_path,
            self._package_name,
            self._critical_css,
        )

    def __getattr__(self, attr: str) -> Any:
        if attr.startswith("_"):
            raise AttributeError(f"'{type(self).__name__}' has no attribute '{attr}'")
        if attr in self._actions:
            custom = self._actions[attr]
            return custom if custom is not None else _ActionMethod(self._base_name, attr)
        if self._default is None:
            self._default = self(name=self._base_name)
        return getattr(self._default, attr)

    def __repr__(self):
        return f"Plugin({self._base_name!r})"

    @property
    def name(self):
        return self._base_name

    @property
    def code(self):
        return self._code

    @property
    def has_attribute(self):
        """True if this plugin registers with attribute()."""
        return bool(self._signals or self._methods or not self._code)

    @property
    def has_action(self):
        """True if this plugin registers with action()."""
        return bool(self._code or self._file_actions)

    @property
    def file_actions(self):
        """True if action plugin is in the TS file as a named export."""
        return self._file_actions

    def get_package_name(self) -> str:
        return self._package_name or _PKG_NAME

    def get_static_path(self) -> Path | None:
        return self._static_path or _STATIC_PATH

    def get_headers(self, pkg_prefix: str) -> tuple:
        return plugins_hdrs(self, pkg_prefix=pkg_prefix)


def _get_plugin_config(p) -> dict | None:
    """Config dict for setConfig - only needed for plugins with methods or user config."""
    methods = getattr(p, "_methods", ())
    config = getattr(p, "config", None) or {}
    if not methods and not config:
        return None
    return {"signal": p.name, **{_snake2camel(k): v for k, v in config.items()}}


def _collect_critical_css(plugins) -> str:
    """Collect and merge critical CSS, hoisting @import rules to the top."""
    imports, rules = [], []
    for p in plugins:
        if not p._critical_css:
            continue
        for m in _CSS_IMPORT_RE.finditer(p._critical_css):
            imports.append(m.group().rstrip(";") + ";")
        remaining = _CSS_IMPORT_RE.sub("", p._critical_css).strip()
        if remaining:
            rules.append(remaining)
    return "".join(imports) + "".join(rules)


def _plugin_specifier(p) -> str:
    return f"@{p.get_package_name()}/{p._base_name}"


def plugins_hdrs(
    *plugins,
    datastar_path: str = "/static/datastar.js",
    pkg_prefix: str = _DEFAULT_PREFIX,
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
                _plugin_specifier(p): f"{pkg_prefix}/{p.get_package_name()}/{p._base_name}.js{v}"
                for p in plugins
                if p.has_attribute or getattr(p, "file_actions", False)
            },
        }
    }

    lines = []
    counter = 0
    needs_attribute = False
    needs_action = False
    file_action_plugins = []

    for p in plugins:
        file_actions = getattr(p, "file_actions", False)

        if p.has_attribute:
            needs_attribute = True
            extra_attrs = getattr(p, "_extra_attributes", ())

            if file_actions or extra_attrs:
                named_exports = []
                if file_actions:
                    named_exports.append(f"{p._base_name}ActionPlugin")
                    file_action_plugins.append(f"{p._base_name}ActionPlugin")
                for suffix in extra_attrs:
                    named_exports.append(f"{p._base_name}{suffix.capitalize()}AttributePlugin")
                lines.append(f"import plugin_{counter},{{{','.join(named_exports)}}}from'{_plugin_specifier(p)}';")
                for suffix in extra_attrs:
                    lines.append(f"attribute({p._base_name}{suffix.capitalize()}AttributePlugin);")
            else:
                lines.append(f"import plugin_{counter} from'{_plugin_specifier(p)}';")

            config = _get_plugin_config(p)
            if config:
                lines.append(f"plugin_{counter}.setConfig({json.dumps(config)});")
            lines.append(f"attribute(plugin_{counter});")
            counter += 1
        elif file_actions:
            needs_action = True
            lines.append(f"import{{{p._base_name}ActionPlugin}}from'{_plugin_specifier(p)}';")
            file_action_plugins.append(f"{p._base_name}ActionPlugin")

        if p.has_action and p._code and not file_actions:
            needs_action = True
            lines.append(f"const plugin_{counter}={p._code};")
            lines.append(f"action(plugin_{counter});")
            counter += 1

    for action_plugin in file_action_plugins:
        needs_action = True
        lines.append(f"action({action_plugin});")

    needed = []
    if needs_attribute:
        needed.append("attribute")
    if needs_action:
        needed.append("action")
    js_code = f"import{{{','.join(needed)}}}from'datastar';\n" + "\n".join(lines)

    css = _collect_critical_css(plugins)

    return (
        *((Style(css),) if css else ()),
        Script(json.dumps(import_map), type="importmap"),
        Script(js_code, type="module"),
    )


# ============================================================
# Motion Animation Helpers
# ============================================================

Spring = Literal["gentle", "bouncy", "tight", "slow"]
EnterPreset = Literal["fade", "slide-up", "slide-down", "scale", "bounce"]
InViewPreset = Literal["fade", "slide-up", "slide-down", "scale"]


def _motion_str(type_name: str, **kwargs) -> str:
    """Build motion config string from keyword args."""
    parts = [f"type:{type_name}"]
    for key, val in kwargs.items():
        if val is None:
            continue
        if isinstance(val, tuple):
            parts.append(f"{key}:{val[0]},{val[1]}")
        elif isinstance(val, bool):
            parts.append(f"{key}:{str(val).lower()}")
        else:
            parts.append(f"{key}:{val}")
    return " ".join(parts)


def enter(
    *,
    x: float | None = None,
    y: float | None = None,
    scale: float | None = None,
    rotate: float | None = None,
    opacity: float | None = None,
    preset: EnterPreset | None = None,
    duration: int | None = None,
    delay: int | None = None,
    ease: str | None = None,
    spring: Spring | None = None,
    repeat: int | Literal["infinite"] | None = None,
    stagger: int | None = None,
    name: str | None = None,
) -> str:
    """Enter/mount animation."""
    return _motion_str(
        "enter",
        x=x,
        y=y,
        scale=scale,
        rotate=rotate,
        opacity=opacity,
        preset=preset,
        duration=duration,
        delay=delay,
        ease=ease,
        spring=spring,
        repeat=repeat,
        stagger=stagger,
        name=name,
    )


def exit_(
    *,
    x: float | None = None,
    y: float | None = None,
    scale: float | None = None,
    rotate: float | None = None,
    opacity: float | None = None,
    duration: int | None = None,
    delay: int | None = None,
    ease: str | None = None,
    spring: Spring | None = None,
    repeat: int | Literal["infinite"] | None = None,
    stagger: int | None = None,
    name: str | None = None,
) -> str:
    """Exit/unmount animation."""
    return _motion_str(
        "exit",
        x=x,
        y=y,
        scale=scale,
        rotate=rotate,
        opacity=opacity,
        duration=duration,
        delay=delay,
        ease=ease,
        spring=spring,
        repeat=repeat,
        stagger=stagger,
        name=name,
    )


def hover(
    *,
    scale: float | None = None,
    y: float | None = None,
    rotate: float | None = None,
    duration: int | None = None,
    delay: int | None = None,
    ease: str | None = None,
    spring: Spring | None = None,
    repeat: int | Literal["infinite"] | None = None,
    stagger: int | None = None,
    name: str | None = None,
) -> str:
    """Hover gesture animation."""
    return _motion_str(
        "hover",
        scale=scale,
        y=y,
        rotate=rotate,
        duration=duration,
        delay=delay,
        ease=ease,
        spring=spring,
        repeat=repeat,
        stagger=stagger,
        name=name,
    )


def in_view(
    *,
    x: float | None = None,
    y: float | None = None,
    scale: float | None = None,
    opacity: float | None = None,
    preset: InViewPreset | None = None,
    threshold: float | None = None,
    once: bool | None = None,
    duration: int | None = None,
    delay: int | None = None,
    ease: str | None = None,
    spring: Spring | None = None,
    repeat: int | Literal["infinite"] | None = None,
    stagger: int | None = None,
    name: str | None = None,
) -> str:
    """Scroll-triggered in-view animation."""
    return _motion_str(
        "in-view",
        x=x,
        y=y,
        scale=scale,
        opacity=opacity,
        preset=preset,
        threshold=threshold,
        once=once,
        duration=duration,
        delay=delay,
        ease=ease,
        spring=spring,
        repeat=repeat,
        stagger=stagger,
        name=name,
    )


def scroll_link(
    *,
    x: tuple[float, float] | None = None,
    y: tuple[float, float] | None = None,
    scale: tuple[float, float] | None = None,
    opacity: tuple[float, float] | None = None,
    rotate: tuple[float, float] | None = None,
    duration: int | None = None,
    delay: int | None = None,
    ease: str | None = None,
    spring: Spring | None = None,
    repeat: int | Literal["infinite"] | None = None,
    stagger: int | None = None,
    name: str | None = None,
) -> str:
    """Scroll-linked animation (scrubbing)."""
    return _motion_str(
        "scroll",
        x=x,
        y=y,
        scale=scale,
        opacity=opacity,
        rotate=rotate,
        duration=duration,
        delay=delay,
        ease=ease,
        spring=spring,
        repeat=repeat,
        stagger=stagger,
        name=name,
    )


def resize_anim(
    *,
    scale: float | None = None,
    opacity: float | None = None,
    duration: int | None = None,
    delay: int | None = None,
    ease: str | None = None,
    spring: Spring | None = None,
    repeat: int | Literal["infinite"] | None = None,
    stagger: int | None = None,
    name: str | None = None,
) -> str:
    """Resize-triggered animation."""
    return _motion_str(
        "resize",
        scale=scale,
        opacity=opacity,
        duration=duration,
        delay=delay,
        ease=ease,
        spring=spring,
        repeat=repeat,
        stagger=stagger,
        name=name,
    )


def press(
    *,
    scale: float | None = None,
    y: float | None = None,
    duration: int | None = None,
    delay: int | None = None,
    ease: str | None = None,
    spring: Spring | None = None,
    repeat: int | Literal["infinite"] | None = None,
    stagger: int | None = None,
    name: str | None = None,
) -> str:
    """Press gesture animation."""
    return _motion_str(
        "press",
        scale=scale,
        y=y,
        duration=duration,
        delay=delay,
        ease=ease,
        spring=spring,
        repeat=repeat,
        stagger=stagger,
        name=name,
    )


tap = press


def visibility(*, signal, enter=None, exit_=None) -> str:
    """Create motion visibility config for animated show/hide.

    Returns a string for use with data_motion attribute directly.
    The TypeScript plugin handles signal watching, enter animations on show,
    and exit animations on hide.

    Args:
        signal: Signal that controls visibility (required, keyword-only)
        enter: EnterAnimation config for show animation
        exit_: ExitAnimation config for hide animation

    Example:
        Div("Modal", data_motion=visibility(
            signal=show_modal,
            enter=enter(preset="fade"),
            exit_=exit_(opacity=0, y=-20)
        ))
    """
    parts = ["type:visibility"]

    sig = str(signal)
    if not sig.startswith(("$", "(")):
        sig = f"${sig}"
    parts.append(f"signal:{sig}")

    if enter:
        for part in str(enter).split():
            if not part.startswith("type:"):
                parts.append(f"enter_{part}")

    if exit_:
        for part in str(exit_).split():
            if not part.startswith("type:"):
                parts.append(f"exit_{part}")

    return " ".join(parts)


def motion_remove(selector: str):
    """SSE helper: Remove element with exit animation. Requires data-motion-exit on target."""
    from .realtime import execute_script

    escaped = selector.replace("\\", "\\\\").replace("`", "\\`")
    return execute_script(
        f"document.querySelector(`{escaped}`)?.dispatchEvent("
        f'new CustomEvent("motion-trigger", {{detail: {{op: "remove"}}}}));'
    )


def motion_replace(selector: str, new_element):
    """SSE helper: Replace element with exit animation. Requires data-motion-exit on target."""
    from fastcore.xml import to_xml

    from .realtime import execute_script

    new_html = to_xml(new_element)
    escaped_sel = selector.replace("\\", "\\\\").replace("`", "\\`")
    escaped_html = new_html.replace("\\", "\\\\").replace("`", "\\`").replace("${", "\\${")

    return execute_script(
        f"document.querySelector(`{escaped_sel}`)?.dispatchEvent("
        f'new CustomEvent("motion-trigger", {{detail: {{op: "replace", html: `{escaped_html}`}}}}));'
    )


# ============================================================
# Built-in Plugins
# ============================================================


_CLIPBOARD_CODE = """{
    name: 'clipboard',
    apply: async ({ el, evt, error }, content, signal, timeout = 2000) => {
        const setSignal = (value) => {
            if (signal) {
                document.dispatchEvent(new CustomEvent('datastar-signal-patch', {
                    detail: { [signal]: value }
                }));
            }
        };
        const success = () => { setSignal(true); setTimeout(() => setSignal(false), timeout); };
        if (content instanceof Element) {
            const img = content.querySelector('img[src]');
            if (img && navigator.clipboard?.write) {
                try {
                    const r = await fetch(img.src);
                    const blob = await r.blob();
                    const png = blob.type === 'image/png' ? blob
                        : new Blob([await blob.arrayBuffer()], { type: 'image/png' });
                    await navigator.clipboard.write([new ClipboardItem({ 'image/png': png })]);
                    return success();
                } catch (_) { /* fall through to text copy */ }
            }
            content = content.textContent || '';
        }
        const text = String(content);
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
            navigator.clipboard.writeText(text).then(success).catch(fallback);
        } else {
            fallback();
        }
    }
}"""


def _clipboard_copy(
    text: str | None = None,
    *,
    element: str | None = None,
    signal: Any = None,
    timeout: int | None = None,
) -> _JSRaw:
    """Generate @clipboard() action expression.

    When element is used, the JS action copies images as PNG blobs if present,
    otherwise falls back to text content.
    """
    if (text is None) == (element is None):
        raise ValueError("clipboard() requires exactly one of: text or element")

    if signal is not None and hasattr(signal, "_id"):
        signal = signal._id

    if text is not None:
        content_expr = _to_js(text, allow_expressions=True)
    elif element == "el":
        content_expr = "el"
    elif element.startswith(("#", ".")):
        content_expr = f"document.querySelector({_to_js(element, allow_expressions=True)})"
    else:
        content_expr = f"document.getElementById({_to_js(element, allow_expressions=True)})"

    args = [content_expr]
    if signal is not None:
        args.append(_to_js(signal, allow_expressions=True))
    if timeout is not None:
        if signal is None:
            args.append("null")  # Need placeholder for signal
        args.append(str(timeout))

    return _JSRaw(f"@clipboard({', '.join(args)})")


clipboard = Plugin("clipboard", code=_CLIPBOARD_CODE, actions={"": _clipboard_copy})
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
        "page_progress",
        "is_top",
        "is_bottom",
        "visible_percent",
        "progress",
    ),
)
resize = Plugin(
    "resize",
    signals=(
        "width",
        "height",
        "window_width",
        "window_height",
        "current_breakpoint",
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
    methods=("reset_view", "zoom_in", "zoom_out"),
)
drag = Plugin(
    "drag",
    signals=("is_dragging", "element_id", "x", "y", "drop_zone"),
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
motion = Plugin(
    "motion",
    file_actions=True,
    actions=("animate", "sequence", "set", "pause", "play", "stop", "cancel", "remove", "replace"),
    extra_attributes=("exit",),
    critical_css="[data-motion]:not([data-motion-ready]){opacity:0}",
)
motion_svg = Plugin(
    "motion-svg",
    critical_css="[data-motion-svg]{will-change:transform}",
)


# ============================================================
# SVG Motion Animation Helpers
# ============================================================

SvgSpring = Literal["gentle", "bouncy", "tight", "slow", "snappy"]


def track(**kwargs) -> str:
    """Track signal values and animate SVG attributes.

    Animates actual SVG attributes (not CSS transforms) - perfect for
    data visualization. Accepts Signal objects or "$name" strings.

    Supported attributes: height, width, x, y, x1, y1, x2, y2, cx, cy, r, rx, ry,
    rotate, scale, translate_x, translate_y, skew_x, skew_y, stroke_width,
    stroke_dashoffset, stroke_dasharray, opacity, fill_opacity, stroke_opacity,
    font_size, font_weight, letter_spacing, word_spacing, stop_offset, std_deviation, d

    Timing: duration, delay, ease, spring (gentle|bouncy|tight|slow|snappy), name

    Example:
        (bar_height := Signal("bar_height", value * 100)),
        Rect(data_motion_svg=track(height=bar_height, spring="gentle"))
    """
    parts = []
    for key, val in kwargs.items():
        if val is None:
            continue
        if isinstance(val, Expr):
            val = val.to_js()
        parts.append(f"{key.replace('_', '-')}:{val}")
    return " ".join(parts)


# Content processor plugins - critical CSS prevents flash of unprocessed content
markdown = Plugin(
    "markdown",
    critical_css="[data-markdown]:not(:has(p,h1,h2,h3,ul,ol,blockquote)){visibility:hidden;position:absolute;pointer-events:none}",
)
katex = Plugin(
    "katex",
    critical_css=(
        "@import url('https://cdn.jsdelivr.net/npm/katex@0.16.11/dist/katex.min.css');"
        "[data-katex]:not(:has(.katex)){visibility:hidden;position:absolute;pointer-events:none}"
        ".katex-display{margin:1.5em 0;overflow-x:auto;overflow-y:hidden;-webkit-overflow-scrolling:touch}"
        ".katex-display::-webkit-scrollbar{height:4px}"
        ".katex-display::-webkit-scrollbar-track{background:transparent}"
        ".katex-display::-webkit-scrollbar-thumb{background:#d1d5db;border-radius:2px}"
    ),
)
mermaid = Plugin(
    "mermaid",
    critical_css="[data-mermaid]:not(:has(svg)){visibility:hidden;position:absolute;pointer-events:none}",
)

__all__ = [
    # Core
    "Plugin",
    "PluginInstance",
    "plugins_hdrs",
    # Motion animation helpers
    "enter",
    "exit_",
    "hover",
    "tap",
    "press",
    "in_view",
    "scroll_link",
    "resize_anim",
    "visibility",
    "motion_remove",
    "motion_replace",
    # SVG motion animation helper
    "track",
    # Plugins
    "canvas",
    "clipboard",
    "drag",
    "katex",
    "markdown",
    "mermaid",
    "motion",
    "motion_svg",
    "persist",
    "position",
    "resize",
    "scroll",
    "split",
]
