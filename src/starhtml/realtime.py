"""Real-time functionality: WebSockets, SSE, and live reload for StarHTML."""

import inspect
import re
from collections.abc import AsyncGenerator, Callable, Generator
from functools import partial, wraps
from typing import Any, Literal, Protocol, runtime_checkable
from warnings import warn

from fastcore.utils import dict2obj, noop
from fastcore.xml import FT, to_xml
from starlette.endpoints import WebSocketEndpoint
from starlette.responses import StreamingResponse
from starlette.routing import WebSocketRoute
from starlette.websockets import WebSocket

from .html import fh_cfg
from .utils import _params, empty

__all__ = [
    "setup_ws",
    "sse",
    "format_sse_event",
    "format_element_event",
    "format_signal_event",
    "signals",
    "elements",
    "execute_script",
    "SSE_HEADERS",
    "RETRY_DURATION",
    "EventStream",
    "sse_message",
    "LiveReloadJs",
    "live_reload_ws",
    "StarHTMLWithLiveReload",
]

# ============================================================================
# WebSocket Functionality
# ============================================================================


def _find_wsp(ws, data, hdrs, arg: str, p):
    """Find WebSocket parameter in the provided context using guard clauses for clarity."""
    from starlette.applications import Starlette

    from .utils import _fix_anno

    anno = p.annotation

    if isinstance(anno, type):
        if issubclass(anno, Starlette):
            return ws.scope["app"]
        if issubclass(anno, WebSocket):
            return ws

    if anno is empty:
        match arg.lower():
            case "ws":
                return ws
            case "scope":
                return dict2obj(ws.scope)
            case "data":
                return data
            case "app":
                return ws.scope["app"]
            case "send":
                return partial(_send_ws, ws)
            case session_arg if "session".startswith(session_arg):
                return ws.scope.get("session", {})
            case _:
                return None

    res = data.get(arg)
    if res is None or res is empty:
        res = hdrs.get(arg)
    if res is None or res is empty:
        res = p.default

    if not isinstance(res, list | str) or anno is empty:
        return res
    return [_fix_anno(anno, o) for o in res] if isinstance(res, list) else _fix_anno(anno, res)


def _wrap_ws(ws, data, params):
    "Wrap WebSocket parameters"
    hdrs = {k.lower().replace("-", "_"): v for k, v in data.pop("HEADERS", {}).items()}
    return [_find_wsp(ws, data, hdrs, arg, p) for arg, p in params.items()]


async def _send_ws(ws, resp):
    """Send WebSocket response.

    IMPORTANT: Only None prevents sending. Empty strings ("") are valid responses
    and will be sent. This aligns with standard web API behavior where empty
    string is a valid response, unlike Python's general falsy handling.

    Changed from 'if not resp:' to 'if resp is None:' to fix issue where
    empty strings were incorrectly treated as "no response". This change makes
    behavior consistent with JavaScript/DOM APIs where empty string !== null.

    Args:
        ws: WebSocket connection
        resp: Response to send. Only None means "don't send anything"
    """
    if resp is None:
        return
    res = to_xml(resp, indent=fh_cfg.indent) if isinstance(resp, list | tuple | FT) or hasattr(resp, "__ft__") else resp
    await ws.send_text(res)


def _ws_endp(recv, conn=None, disconn=None):
    "Create WebSocket endpoint class"
    from json import loads

    from .server import _handle

    cls = type("WS_Endp", (WebSocketEndpoint,), {"encoding": "text"})

    async def _generic_handler(handler, ws, data=None):
        wd = _wrap_ws(ws, loads(data) if data else {}, _params(handler))
        resp = await _handle(handler, wd)
        if resp is not None:
            await _send_ws(ws, resp)

    async def _connect(self, ws):
        await ws.accept()
        await _generic_handler(conn, ws)

    async def _disconnect(self, ws, close_code):
        await _generic_handler(disconn, ws)

    async def _recv(self, ws, data):
        await _generic_handler(recv, ws, data)

    if conn:
        cls.on_connect = _connect
    if disconn:
        cls.on_disconnect = _disconnect
    cls.on_receive = _recv
    return cls


def setup_ws(app, f=noop):
    "Set up WebSocket connection management"
    conns = {}

    async def on_connect(scope, send):
        conns[scope.client] = send

    async def on_disconnect(scope):
        conns.pop(scope.client)

    app.ws("/ws", conn=on_connect, disconn=on_disconnect)(f)

    async def send(s):
        for o in conns.values():
            await o(s)

    app._send = send
    return send


# ============================================================================
# SSE Functionality
# ============================================================================

SSE_HEADERS = {
    "Content-Type": "text/event-stream",
    "Cache-Control": "no-cache",
    "Connection": "keep-alive",
    "X-Accel-Buffering": "no",  # Disable nginx buffering
    "X-Content-Type-Options": "nosniff",
}

RETRY_DURATION = 1000
DEFAULT_MODE = "outer"
VALID_MODES = frozenset(["outer", "inner", "replace", "prepend", "append", "before", "after", "remove"])

SSEMode = Literal["outer", "inner", "replace", "prepend", "append", "before", "after", "remove"]

NEWLINE_REGEX = re.compile(r"\r\n|\r|\n")
SELECTOR_VALIDATION_REGEX = re.compile(r"^[#.\[\]_\w:*-]+$")

try:
    from orjson import dumps as _orjson_dumps

    def json_dumps(obj: Any) -> str:
        """Fast JSON serialization with orjson."""
        return _orjson_dumps(obj).decode("utf-8")
except ImportError:
    from json import dumps as json_dumps


def EventStream(s):
    "Create a text/event-stream response from `s`"
    return StreamingResponse(s, media_type="text/event-stream")


def format_sse_event(
    event_type: str, data_lines: list[str], event_id: str | None = None, retry: int = RETRY_DURATION
) -> str:
    """Format an SSE event according to Datastar specification.

    Order per spec:
    1. event: EVENT_TYPE
    2. id: EVENT_ID (if provided)
    3. retry: RETRY_DURATION (unless default of 1000)
    4. data: DATA (for each of the dataLines)
    5. \n (end of event)
    """
    parts = [f"event: {event_type}"]

    if event_id:
        parts.append(f"id: {event_id}")

    if retry != RETRY_DURATION:
        parts.append(f"retry: {retry}")

    parts.extend([f"data: {line}" for line in data_lines])

    return "\n".join(parts) + "\n\n"


def escape_newlines(text: str) -> str:
    """Replace newlines with escaped versions for SSE data lines."""
    return NEWLINE_REGEX.sub("&#10;", text)


def split_multiline_html(html: str) -> list[str]:
    """Split multiline HTML into separate lines for SSE data format.

    Per Datastar spec, multiline HTML should be split into multiple data: elements lines.
    """
    lines = html.split("\n")
    return [line for line in lines if line.strip()]  # Remove empty lines


def format_signal_event(signals_dict: dict[str, Any], only_if_missing: bool = False) -> str:
    """Format a signals event for Datastar using JSON Merge Patch semantics (RFC 7386)."""
    data_lines = []

    if only_if_missing:
        data_lines.append("onlyIfMissing true")

    try:
        data = json_dumps(signals_dict)
    except (TypeError, ValueError) as e:
        raise ValueError(f"Failed to serialize signals: {e}") from e

    data_lines.append(f"signals {escape_newlines(data)}")
    return format_sse_event("datastar-patch-signals", data_lines)


def format_element_event(
    element: Any, selector: str | None = None, mode: SSEMode = DEFAULT_MODE, use_view_transition: bool = False
) -> str:
    """Format an element/fragment event for Datastar.

    Per Datastar spec, data format (only include non-defaults):
    - mode PATCH_MODE (if not 'outer')
    - selector SELECTOR (if provided)
    - elements HTML_LINE (for each line of HTML)
    """
    if mode not in VALID_MODES:
        raise ValueError(f"Invalid mode '{mode}'. Must be one of: {', '.join(sorted(VALID_MODES))}")

    element_html = to_xml(element)
    data_lines = []

    if mode != DEFAULT_MODE:
        data_lines.append(f"mode {mode}")

    if selector and selector.strip():
        if not SELECTOR_VALIDATION_REGEX.match(selector):
            warn(f"Potentially unsafe selector: {selector}", stacklevel=2)
        data_lines.append(f"selector {selector}")

    if use_view_transition:
        data_lines.append("useViewTransition true")

    if "\n" in element_html:
        html_lines = element_html.split("\n")
        for line in html_lines:
            if line.strip():  # Skip empty lines
                data_lines.append(f"elements {line}")
    else:
        data_lines.append(f"elements {element_html}")

    return format_sse_event("datastar-patch-elements", data_lines)


def signals(only_if_missing: bool = False, **kwargs) -> tuple[str, dict[str, Any]]:
    """Create a signals SSE item for the @sse decorator."""
    return ("signals", {"payload": kwargs, "options": {"only_if_missing": only_if_missing}})


def elements(
    element, selector: str | None = None, mode: SSEMode = DEFAULT_MODE, use_view_transition: bool = False
) -> tuple[str, tuple]:
    """Create an elements SSE item for the @sse decorator."""
    return ("elements", (element, selector, mode, use_view_transition))


def execute_script(
    script_content: str, auto_remove: bool = True, attributes: dict[str, Any] | None = None
) -> tuple[str, tuple]:
    """Create an SSE item to execute JavaScript in the browser.

    Per Datastar SDK spec, this sends a script element that gets appended to the body.
    The script automatically executes when added to the DOM.

    Args:
        script_content: JavaScript code to execute
        auto_remove: If True, script element removes itself after execution
        attributes: Additional attributes to add to the script tag

    Returns:
        An SSE item tuple for use with the @sse decorator
    """
    from .xtend import Script

    script_attrs = attributes or {}
    if auto_remove:
        script_attrs["data-effect"] = "el.remove()"
    script_element = Script(script_content, **script_attrs)

    return elements(script_element, selector="body", mode="append")


def sse_message(elm, event="message"):
    """Convert element `elm` into a format suitable for SSE streaming.

    This is a lower-level utility for custom SSE message formatting.
    For standard Datastar SSE events, prefer format_element_event() or format_signal_event().
    """
    data = "\n".join(f"data: {o}" for o in to_xml(elm).splitlines())
    return f"event: {event}\n{data}\n\n"


def process_sse_item(item_type: str, payload: Any) -> str | None:
    """Process an SSE item and return the formatted output."""
    match item_type:
        case "signals":
            if isinstance(payload, dict) and "payload" in payload:
                signal_data = payload["payload"]
                options = payload.get("options", {})
                only_if_missing = options.get("only_if_missing", False)
                return format_signal_event(signal_data, only_if_missing=only_if_missing)
            else:
                return format_signal_event(payload)
        case "elements":
            if isinstance(payload, tuple):
                element = payload[0]
                selector = payload[1] if len(payload) > 1 else None
                mode = payload[2] if len(payload) > 2 else DEFAULT_MODE
                use_view_transition = payload[3] if len(payload) > 3 else False
            else:
                element, selector, mode, use_view_transition = payload, None, DEFAULT_MODE, False

            # Auto-detect selector if not provided and element has id
            if selector is None and hasattr(element, "attrs"):
                if element_id := element.attrs.get("id"):
                    selector = f"#{element_id}"

            return format_element_event(element, selector, mode, use_view_transition)
        case _:
            raise ValueError(f"Unknown SSE item type: {item_type}")


@runtime_checkable
class SSEItem(Protocol):
    """Protocol for SSE items."""

    def __getitem__(self, index: int) -> Any: ...
    def __len__(self) -> int: ...


async def stream_sse_items(generator: Generator | AsyncGenerator) -> AsyncGenerator[str, None]:
    """Stream SSE items from a generator (sync or async) with type checking."""
    if inspect.isasyncgen(generator):
        async for item in generator:
            if isinstance(item, tuple) and len(item) == 2:
                if result := process_sse_item(item[0], item[1]):
                    yield result
    else:
        for item in generator:
            if isinstance(item, tuple) and len(item) == 2:
                if result := process_sse_item(item[0], item[1]):
                    yield result


def sse(handler: Callable) -> Callable:
    """Decorator that handles sequential signal/fragment updates for Datastar.

    Supports both sync and async handlers:

        @sse
        def sync_handler():
            yield signals(status="Loading...")
            yield elements(Div("Done"))

        @sse
        async def async_handler():
            yield signals(status="Loading...")
            data = await fetch_data()
            yield elements(Div(data))
    """

    @wraps(handler)
    async def sse_wrapper(*args, **kwargs) -> StreamingResponse:
        """Unified SSE handler wrapper for both sync and async generators."""
        generator = handler(*args, **kwargs)
        return StreamingResponse(stream_sse_items(generator), headers=SSE_HEADERS, media_type="text/event-stream")

    return sse_wrapper


# ============================================================================
# Live Reload Functionality (from live_reload.py)
# ============================================================================


def LiveReloadJs(reload_attempts: int = 20, reload_interval: int = 1000, **kwargs):
    "Generate live reload JavaScript"
    src = """
    (() => {
        let attempts = 0;
        const connect = () => {
            const socket = new WebSocket(`ws://${window.location.host}/live-reload`);
            socket.onopen = async() => {
                const res = await fetch(window.location.href);
                if (res.ok) {
                    attempts ? window.location.reload() : console.log('LiveReload connected');
                }};
            socket.onclose = () => {
                !attempts++ ? connect() : setTimeout(() => { connect(); }, %d);
                if (attempts > %d) window.location.reload();
            };
        };
        connect();
    })();
    """
    from .xtend import Script

    return Script(src % (reload_interval, reload_attempts))


async def live_reload_ws(websocket):
    "WebSocket handler for live reload"
    await websocket.accept()


class StarHTMLWithLiveReload:
    """StarHTML with live reloading enabled.

    This means that any code changes saved on the server will automatically
    trigger a reload of both the server and browser window.

    How does it work:
      - a websocket is created at `/live-reload`
      - a small js snippet is injected into each webpage
      - this snippet connects to the websocket at `/live-reload` and listens for an `onclose` event
      - when the `onclose` event is detected the browser is reloaded

    Why do we listen for an `onclose` event?
      When code changes are saved the server automatically reloads if the --reload flag is set.
      The server reload kills the websocket connection. The `onclose` event serves as a proxy
      for "developer has saved some changes".

    Usage:
        >>> from starhtml.realtime import StarHTMLWithLiveReload
        >>> app = StarHTMLWithLiveReload()
    """

    def __new__(cls, *args, **kwargs):
        """
        Factory using __new__ to dynamically create a StarHTML subclass.

        This pattern is used to inject live-reload routes and headers into the
        StarHTML application at instantiation time without requiring the user
        to manually inherit from StarHTML or configure live-reload manually.
        """
        from .core import StarHTML

        class _StarHTMLWithLiveReload(StarHTML):
            def __init__(self, *args, **kwargs):
                # "hdrs" and "routes" can be missing, None, a list or a tuple.
                kwargs["hdrs"] = [*(kwargs.get("hdrs") or []), LiveReloadJs(**kwargs)]
                kwargs["routes"] = [
                    *(kwargs.get("routes") or []),
                    WebSocketRoute("/live-reload", endpoint=live_reload_ws),
                ]
                super().__init__(*args, **kwargs)

        return _StarHTMLWithLiveReload(*args, **kwargs)
