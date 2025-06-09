"""Datastar SSE functionality for StarHTML - Concise version."""

import inspect
import re
from collections.abc import AsyncGenerator, Callable, Generator
from functools import wraps
from typing import Any

from starlette.responses import StreamingResponse

try:
    from orjson import dumps as _orjson_dumps

    def json_dumps(obj):
        return _orjson_dumps(obj).decode("utf-8")
except ImportError:
    from json import dumps as json_dumps

from .components import to_xml

# Configuration
SSE_HEADERS = {
    "Content-Type": "text/event-stream",
    "Cache-Control": "no-cache",
    "Connection": "keep-alive",
    "X-Accel-Buffering": "no",  # Disable nginx buffering
    "X-Content-Type-Options": "nosniff",
}

RETRY_DURATION = 1000
DEFAULT_MERGE_MODE = "morph"
VALID_MERGE_MODES = frozenset(["morph", "inner", "outer", "append", "prepend", "before", "after", "replace", "remove"])

# Pre-compiled regex for newline replacement
NEWLINE_REGEX = re.compile(r"\r\n|\r|\n")


def format_sse_event(
    event_type: str, data_lines: list[str], event_id: str | None = None, retry: int = RETRY_DURATION
) -> str:
    """Format an SSE event efficiently."""
    parts = [f"id: {event_id}"] if event_id else []
    parts.extend([f"event: {event_type}", f"retry: {retry}"])
    parts.extend(f"data: {line}" for line in data_lines)
    return "\n".join(parts) + "\n\n"


def escape_newlines(text: str) -> str:
    """Escape newlines for SSE format using regex."""
    return NEWLINE_REGEX.sub("&#10;", text)


def format_signal_event(signals: dict[str, Any]) -> str:
    """Format a datastar-merge-signals event."""
    try:
        return format_sse_event("datastar-merge-signals", [f"signals {json_dumps(signals)}"])
    except (TypeError, ValueError) as e:
        raise ValueError(f"Failed to serialize signals: {e}")


def format_fragment_event(
    fragments: Any | list[Any], selector: str | None = None, merge_mode: str = DEFAULT_MERGE_MODE
) -> str:
    """Format a datastar-merge-fragments event."""
    # Validate inputs
    if selector and not (selector := selector.strip()):
        selector = None
    if selector and not re.match(r"^[#.\[\w:*-]", selector):
        raise ValueError(f"Invalid selector: {selector}")
    if merge_mode not in VALID_MERGE_MODES:
        raise ValueError(f"Invalid merge mode: {merge_mode}. Valid: {', '.join(VALID_MERGE_MODES)}")

    # Convert fragments to HTML
    if not isinstance(fragments, list):
        fragments = [fragments]

    html_parts = []
    for fragment in fragments:
        # Check if it's a StarHTML component
        if getattr(fragment, "__ft__", None) or getattr(fragment, "tag", None) or isinstance(fragment, list | tuple):
            html_parts.append(to_xml(fragment, indent=False))
        else:
            html_parts.append(str(fragment))

    # Build data lines
    all_html = escape_newlines("".join(html_parts))
    data_lines = []
    if selector:
        data_lines.append(f"selector {selector}")
    data_lines.append(f"mergeMode {merge_mode}")
    data_lines.append(f"fragments {all_html}")

    return format_sse_event("datastar-merge-fragments", data_lines)


def process_sse_item(item_type: str, payload: Any) -> str | None:
    """Process an SSE item and return the formatted output."""
    if item_type == "signals":
        return format_signal_event(payload)
    elif item_type == "fragments":
        # Unpack payload
        if isinstance(payload, tuple):
            parts = list(payload) + [None, DEFAULT_MERGE_MODE]
            fragment, selector, merge_mode = parts[:3]
        else:
            fragment, selector, merge_mode = payload, None, DEFAULT_MERGE_MODE

        # Auto-detect selector if not provided and fragment has id
        if selector is None:
            attrs = getattr(fragment, "attrs", {})
            if fragment_id := attrs.get("id"):
                selector = f"#{fragment_id}"

        return format_fragment_event(fragment, selector, merge_mode)
    else:
        raise ValueError(f"Unknown SSE item type: {item_type}")


async def stream_sse_items(generator: Generator | AsyncGenerator) -> AsyncGenerator[str, None]:
    """Stream SSE items from a generator (sync or async)."""
    if inspect.isasyncgen(generator):
        async for item in generator:
            if isinstance(item, tuple) and len(item) == 2 and (result := process_sse_item(*item)):
                yield result
    else:
        for item in generator:
            if isinstance(item, tuple) and len(item) == 2 and (result := process_sse_item(*item)):
                yield result


def sse(handler: Callable) -> Callable:
    """Decorator that handles sequential signal/fragment updates for Datastar.

    Supports both sync and async handlers:

        @sse
        def sync_handler():
            yield signals(status="Loading...")
            yield fragments(Div("Done"))

        @sse
        async def async_handler():
            yield signals(status="Loading...")
            data = await fetch_data()
            yield fragments(Div(data))
    """

    @wraps(handler)
    async def wrapped(*args, **kwargs) -> StreamingResponse:
        """Wrapped SSE handler."""
        generator = handler(*args, **kwargs)
        return StreamingResponse(stream_sse_items(generator), headers=SSE_HEADERS)

    return wrapped


def signals(**signals: Any) -> tuple[str, dict[str, Any]]:
    """Helper to create signal updates for SSE responses.

    Example:
        yield signals(count=5, message="Hello")
    """
    return "signals", signals


def fragments(
    content: Any, selector: str | None = None, mode: str = DEFAULT_MERGE_MODE
) -> tuple[str, tuple[Any, str | None, str]]:
    """Helper to create fragment updates for SSE responses.

    Auto-detects selector from element id if not provided.

    Examples:
        yield fragments(Div("Hello", id="msg"))  # Auto-detects #msg selector
        yield fragments(Div("Hello"), "#content", "append")  # Explicit selector and mode
    """
    return "fragments", (content, selector, mode)
