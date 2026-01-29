"""Minimal Datastar plugin system - glue between Python templates and JS plugins."""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any, Literal

from .datastar import Expr, _JSRaw, _to_js, js
from .xtend import Script, Style

_STATIC_PATH = Path(__file__).parent / "static" / "js" / "plugins"
_PKG_NAME = "starhtml/plugins"


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
        # Action-only plugins (code but no signals/methods) use apply dispatch
        # Attribute plugins use window methods
        if self._code and not signals and not methods:
            self._refs.update({m: js(f"@{name}('{_snake2camel(m)}')") for m in methods})
        else:
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

    def get_headers(self, base_url: str) -> tuple:
        return plugins_hdrs(self, base_url=base_url)


class _ActionMethod:
    """Callable that generates @plugin('method', args) syntax."""

    def __init__(self, plugin_name: str, method_name: str):
        self._plugin_name = plugin_name
        self._method_name = method_name
        # Map Python names to JS names (e.g., from_ → from to avoid Python keyword)
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

    Actions can be defined as:
        - Tuple of method names: actions=("animate", "set", "pause") - uses generic _ActionMethod
        - Dict with custom implementations: actions={"copy": my_custom_func} - uses provided callable

    Plugin type is derived from structure:
        - code + no signals/methods → action only (registers with action())
        - code + signals/methods → both (attribute from file, action from code)
        - no code → attribute only (registers with attribute(), file-based)
        - file_actions=True → action plugin is also in the TS file (named export)

    Args:
        base_name: Plugin name (e.g., "motion", "clipboard")
        code: Inline JS code for action registration
        signals: Tuple of signal names exposed by the plugin
        methods: Tuple of method names for window.__plugin.method() calls
        actions: Tuple of method names OR dict mapping names to custom callables
        file_actions: If True, action plugin is in the TS file as named export {name}ActionPlugin
        extra_attributes: Tuple of additional attribute plugin suffixes to import/register
                         e.g., ("exit",) imports {motionExitAttributePlugin}
        static_path: Path to static JS files
        package_name: Package name for import map
        critical_css: CSS to prevent flash of unstyled content
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
        # Check if this looks like an action invocation vs instance creation
        # Action invocation: positional args, or kwargs other than 'name'
        has_action_args = args or (kwargs and name is None)

        # If has action args and has default action, invoke it
        if has_action_args and "" in self._actions:
            default_impl = self._actions[""]
            return default_impl(*args, **kwargs)

        # Otherwise create a PluginInstance (for named instances or config)
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
        # Check if it's a defined action method
        if attr in self._actions:
            custom_impl = self._actions[attr]
            if custom_impl is not None:
                return custom_impl  # Return custom callable directly
            return _ActionMethod(self._base_name, attr)  # Generic passthrough
        # Fall back to PluginInstance attributes (signals, etc.)
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
        """True if this plugin registers with attribute().

        Derived: has signals/methods OR no code (file-based default).
        """
        return bool(self._signals or self._methods or not self._code)

    @property
    def has_action(self):
        """True if this plugin registers with action().

        Derived: has inline code OR file_actions=True.
        """
        return bool(self._code or self._file_actions)

    @property
    def file_actions(self):
        """True if action plugin is in the TS file as a named export."""
        return self._file_actions

    def get_package_name(self) -> str:
        return self._package_name or _PKG_NAME

    def get_static_path(self) -> Path | None:
        return self._static_path or _STATIC_PATH

    def get_headers(self, base_url: str) -> tuple:
        return plugins_hdrs(self, base_url=base_url)


def _get_plugin_config(p) -> dict | None:
    """Config dict for setConfig - only needed for plugins with methods or user config."""
    methods = getattr(p, "_methods", ())
    config = getattr(p, "config", None) or {}
    if not methods and not config:
        return None
    return {"signal": p.name, **{_snake2camel(k): v for k, v in config.items()}}


def plugins_hdrs(
    *plugins,
    datastar_path: str = "/static/datastar.js",
    base_url: str = "/_pkg/starhtml/plugins",
    debug: bool = False,
) -> tuple:
    """Generate import map and loader script for plugins.

    Plugin type is derived from structure:
    - code + no signals/methods → action only (inline)
    - code + signals/methods → both (attribute from file, action from code)
    - no code → attribute only (file-based)
    - file_actions=True → action plugin also in file (named export)
    """
    if not plugins:
        return ()

    v = f"?v={int(time.time())}" if debug else ""

    # File-based imports for attribute plugins or file_actions plugins
    import_map = {
        "imports": {
            "datastar": f"{datastar_path}{v}",
            **{
                f"@starhtml/plugins/{p._base_name}": f"{base_url}/{p._base_name}.js{v}"
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

        # Register attribute plugin (always file-based)
        if p.has_attribute:
            needs_attribute = True
            extra_attrs = getattr(p, "_extra_attributes", ())

            # Build import statement
            if file_actions or extra_attrs:
                # Import default + named exports
                named_exports = []
                if file_actions:
                    named_exports.append(f"{p._base_name}ActionPlugin")
                    file_action_plugins.append(f"{p._base_name}ActionPlugin")
                # Add extra attribute plugins (e.g., "exit" → "motionExitAttributePlugin")
                for suffix in extra_attrs:
                    named_exports.append(f"{p._base_name}{suffix.capitalize()}AttributePlugin")
                lines.append(
                    f"import plugin_{counter},{{{','.join(named_exports)}}}from'@starhtml/plugins/{p._base_name}';"
                )
                # Register extra attribute plugins
                for suffix in extra_attrs:
                    lines.append(f"attribute({p._base_name}{suffix.capitalize()}AttributePlugin);")
            else:
                lines.append(f"import plugin_{counter} from'@starhtml/plugins/{p._base_name}';")

            config = _get_plugin_config(p)
            if config:
                lines.append(f"plugin_{counter}.setConfig({json.dumps(config)});")
            lines.append(f"attribute(plugin_{counter});")
            counter += 1
        elif file_actions:
            # Only file_actions, no attribute - just import action plugin
            needs_action = True
            lines.append(f"import{{{p._base_name}ActionPlugin}}from'@starhtml/plugins/{p._base_name}';")
            file_action_plugins.append(f"{p._base_name}ActionPlugin")

        # Register action plugin from inline code (not file_actions)
        if p.has_action and p._code and not file_actions:
            needs_action = True
            lines.append(f"const plugin_{counter}={p._code};")
            lines.append(f"action(plugin_{counter});")
            counter += 1

    # Register file-based action plugins
    for action_plugin in file_action_plugins:
        needs_action = True
        lines.append(f"action({action_plugin});")

    needed = []
    if needs_attribute:
        needed.append("attribute")
    if needs_action:
        needed.append("action")
    js_code = f"import{{{','.join(needed)}}}from'datastar';\n" + "\n".join(lines)

    # Critical CSS prevents flash of unprocessed content
    css = "".join(p._critical_css for p in plugins if p._critical_css)

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

    if hasattr(signal, "_id"):
        sig_id = signal._id
    elif isinstance(signal, _JSRaw):
        sig_str = str(signal)
        sig_id = sig_str[1:] if sig_str.startswith("$") else sig_str
    else:
        sig_id = str(signal)

    if not sig_id.startswith("$"):
        sig_id = f"${sig_id}"
    parts.append(f"signal:{sig_id}")

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


def _clipboard_copy(
    text: str | None = None,
    *,
    element: str | None = None,
    signal: Any = None,
    timeout: int | None = None,
) -> _JSRaw:
    """Copy text to clipboard with optional success signal.

    Args:
        text: Literal text to copy
        element: Element selector to copy text from ('el', '#id', '.class')
        signal: Signal to set True on success (auto-resets after timeout)
        timeout: Reset timeout in ms (default 2000)

    Examples:
        clipboard("Hello!")
        clipboard("Text", signal=copied)
        clipboard(element="#code-block", signal=copied)
        clipboard(element="el")  # Copy from current element
    """
    if (text is None) == (element is None):
        raise ValueError("clipboard() requires exactly one of: text or element")

    # Extract signal ID if it's a Signal object
    if signal is not None and hasattr(signal, "_id"):
        signal = signal._id

    # Build the text expression
    if text is not None:
        text_expr = _to_js(text, allow_expressions=True)
    elif element == "el":
        text_expr = "el.textContent"
    elif element.startswith(("#", ".")):
        text_expr = f"document.querySelector({_to_js(element, allow_expressions=True)}).textContent"
    else:
        text_expr = f"document.getElementById({_to_js(element, allow_expressions=True)}).textContent"

    # Build args list
    args = [text_expr]
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
