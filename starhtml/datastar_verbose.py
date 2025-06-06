"""Datastar SSE functionality for StarHTML with performance and quality improvements."""

from typing import Any, Callable, Dict, Optional, Tuple, List, Union, Protocol, TypedDict, overload, TypeVar, AsyncGenerator, Generator
from functools import wraps
from starlette.responses import StreamingResponse
from io import StringIO
import asyncio
import inspect
import re
import json

# Try to import orjson for better performance, fall back to stdlib json
try:
    import orjson
    HAS_ORJSON = True
    
    def json_dumps(obj: Any) -> str:
        """Fast JSON serialization with orjson."""
        return orjson.dumps(obj).decode('utf-8')
except ImportError:
    HAS_ORJSON = False
    json_dumps = json.dumps

from .components import to_xml

# Type definitions
T = TypeVar('T')

class SSEItem(TypedDict):
    """Type for SSE items."""
    type: str
    payload: Any

class FragmentPayload(TypedDict, total=False):
    """Type for fragment payload."""
    content: Any
    selector: Optional[str]
    mode: str

# SSE headers for proper event streaming with additional proxy headers
SSE_HEADERS = {
    'Content-Type': 'text/event-stream',
    'Cache-Control': 'no-cache', 
    'Connection': 'keep-alive',
    'X-Accel-Buffering': 'no',  # Disable nginx buffering
    'X-Content-Type-Options': 'nosniff',
}

# Constants
DEFAULT_RETRY_DURATION = 1000
DEFAULT_MERGE_MODE = "morph"
VALID_MERGE_MODES = frozenset(["morph", "inner", "outer", "append", "prepend", "before", "after", "replace", "remove"])

# Pre-compiled regex for newline replacement (performance optimization)
NEWLINE_REGEX = re.compile(r'\r\n|\r|\n')

# Custom exceptions
class SSEError(Exception):
    """Base exception for SSE-related errors."""
    pass

class InvalidSelectorError(SSEError):
    """Raised when a CSS selector is invalid."""
    pass

class InvalidEventTypeError(SSEError):
    """Raised when an SSE event type is invalid."""
    pass

class InvalidMergeModeError(SSEError):
    """Raised when a merge mode is invalid."""
    pass

# Protocols for type checking
class SSEHandler(Protocol):
    """Protocol for SSE handler functions."""
    def __call__(self, *args: Any, **kwargs: Any) -> Union[Generator[Tuple[str, Any], None, None], 
                                                            AsyncGenerator[Tuple[str, Any], None]]:
        ...

def validate_selector(selector: Optional[str]) -> Optional[str]:
    """Validate CSS selector format.
    
    Args:
        selector: CSS selector string or None
        
    Returns:
        Validated selector or None
        
    Raises:
        InvalidSelectorError: If selector format is invalid
    """
    if selector is None:
        return None
    
    selector = selector.strip()
    if not selector:
        return None
        
    # Basic validation - selector should start with valid characters
    if not re.match(r'^[#.\[\w:*-]', selector):
        raise InvalidSelectorError(f"Invalid selector format: {selector}")
    
    return selector

def validate_merge_mode(mode: str) -> str:
    """Validate merge mode.
    
    Args:
        mode: Merge mode string
        
    Returns:
        Validated merge mode
        
    Raises:
        InvalidMergeModeError: If merge mode is invalid
    """
    if mode not in VALID_MERGE_MODES:
        raise InvalidMergeModeError(
            f"Invalid merge mode: {mode}. Valid modes are: {', '.join(VALID_MERGE_MODES)}"
        )
    return mode

def format_sse_event(event_type: str, 
                    data_lines: List[str], 
                    event_id: Optional[str] = None, 
                    retry_duration: int = DEFAULT_RETRY_DURATION) -> str:
    """Format an SSE event efficiently using StringIO.
    
    Args:
        event_type: SSE event type
        data_lines: Lines of data to include
        event_id: Optional event ID
        retry_duration: Retry duration in milliseconds
        
    Returns:
        Formatted SSE event string
    """
    buffer = StringIO()
    
    if event_id:
        buffer.write(f"id: {event_id}\n")
    
    buffer.write(f"event: {event_type}\n")
    buffer.write(f"retry: {retry_duration}\n")
    
    for line in data_lines:
        buffer.write(f"data: {line}\n")
    
    buffer.write("\n")  # Empty line to signal end of event
    return buffer.getvalue()

def escape_newlines_for_sse(text: str) -> str:
    """Escape newlines for SSE format using regex (performance optimized).
    
    Args:
        text: Text to escape
        
    Returns:
        Text with newlines escaped as HTML entities
    """
    return NEWLINE_REGEX.sub('&#10;', text)

def format_signal_event(signals: Dict[str, Any]) -> str:
    """Format a datastar-merge-signals event.
    
    Args:
        signals: Dictionary of signals to merge
        
    Returns:
        Formatted SSE event
    """
    try:
        signals_json = json_dumps(signals)
    except (TypeError, ValueError) as e:
        raise SSEError(f"Failed to serialize signals to JSON: {e}")
    
    return format_sse_event("datastar-merge-signals", [f"signals {signals_json}"])

def format_fragment_event(fragments: Union[Any, List[Any]], 
                         selector: Optional[str] = None, 
                         merge_mode: str = DEFAULT_MERGE_MODE) -> str:
    """Format a datastar-merge-fragments event.
    
    Args:
        fragments: Fragment(s) to send
        selector: CSS selector for target element
        merge_mode: How to merge the fragment
        
    Returns:
        Formatted SSE event
    """
    # Validate inputs
    selector = validate_selector(selector)
    merge_mode = validate_merge_mode(merge_mode)
    
    # Convert fragments to HTML
    if not isinstance(fragments, list):
        fragments = [fragments]
    
    html_parts = []
    for fragment in fragments:
        # Optimize attribute access with getattr
        if getattr(fragment, '__ft__', None) or getattr(fragment, 'tag', None) or isinstance(fragment, (list, tuple)):
            html_parts.append(to_xml(fragment, indent=False))
        else:
            html_parts.append(str(fragment))
    
    # Join and escape newlines efficiently
    all_html = escape_newlines_for_sse(''.join(html_parts))
    
    # Build data lines
    data_lines = []
    if selector:
        data_lines.append(f"selector {selector}")
    data_lines.append(f"mergeMode {merge_mode}")
    data_lines.append(f"fragments {all_html}")
    
    return format_sse_event("datastar-merge-fragments", data_lines)

def process_sse_item(item_type: str, payload: Any) -> Optional[str]:
    """Process an SSE item and return the formatted output.
    
    Args:
        item_type: Type of SSE item ("signals" or "fragments")
        payload: Item payload
        
    Returns:
        Formatted SSE event or None
        
    Raises:
        InvalidEventTypeError: If item_type is not recognized
    """
    if item_type == "signals":
        return format_signal_event(payload)
    elif item_type == "fragments":
        # Allow flexible fragment definitions
        if isinstance(payload, tuple):
            fragment, selector, merge_mode = payload + (None, DEFAULT_MERGE_MODE)[:3-len(payload)]
        else:
            fragment, selector, merge_mode = payload, None, DEFAULT_MERGE_MODE
        
        # Auto-detect selector if not provided and fragment has id
        if selector is None:
            fragment_attrs = getattr(fragment, 'attrs', {})
            if fragment_id := fragment_attrs.get('id'):
                selector = f"#{fragment_id}"
        
        return format_fragment_event(fragment, selector, merge_mode)
    else:
        raise InvalidEventTypeError(f"Unknown SSE item type: {item_type}")

async def stream_sse_items(generator: Union[Generator, AsyncGenerator]) -> AsyncGenerator[str, None]:
    """Stream SSE items from a generator (sync or async).
    
    Args:
        generator: Source generator
        
    Yields:
        Formatted SSE events
    """
    if inspect.isasyncgen(generator):
        async for item in generator:
            if isinstance(item, tuple) and len(item) == 2:
                if result := process_sse_item(item[0], item[1]):
                    yield result
    else:
        # Sync generator
        for item in generator:
            if isinstance(item, tuple) and len(item) == 2:
                if result := process_sse_item(item[0], item[1]):
                    yield result

def sse(handler: Callable[..., T]) -> Callable[..., StreamingResponse]:    
    """Decorator that handles sequential signal/fragment updates for Datastar.
    
    Supports both sync and async handlers:
    
        @sse
        def sync_handler():
            yield signal(status="Loading...")
            yield fragment(Div("Done"))
            
        @sse
        async def async_handler():
            yield signal(status="Loading...")
            data = await fetch_data()
            yield fragment(Div(data))
            
    Args:
        handler: Generator function (sync or async)
        
    Returns:
        Wrapped function that returns StreamingResponse
    """
    is_async = asyncio.iscoroutinefunction(handler) or inspect.isasyncgenfunction(handler)
    
    @wraps(handler)
    async def wrapped(*args: Any, **kwargs: Any) -> StreamingResponse:
        """Wrapped SSE handler."""
        # Get generator from handler
        generator = handler(*args, **kwargs)
        
        # Create streaming response with optimized SSE streaming
        return StreamingResponse(
            stream_sse_items(generator), 
            headers=SSE_HEADERS
        )
    
    return wrapped

def signal(**signals: Any) -> Tuple[str, Dict[str, Any]]:
    """Helper to create signal updates for SSE responses.
    
    Example:
        yield signal(count=5, message="Hello")
        # Generates: event: datastar-merge-signals
        #           data: signals {"count": 5, "message": "Hello"}
        
    Args:
        **signals: Signal key-value pairs
        
    Returns:
        Tuple of ("signals", signal_dict)
    """
    return "signals", signals

@overload
def fragment(content: Any) -> Tuple[str, Tuple[Any, None, str]]: ...

@overload
def fragment(content: Any, selector: str) -> Tuple[str, Tuple[Any, str, str]]: ...

@overload
def fragment(content: Any, selector: str, mode: str) -> Tuple[str, Tuple[Any, str, str]]: ...

def fragment(content: Any, 
            selector: Optional[str] = None, 
            mode: str = DEFAULT_MERGE_MODE) -> Tuple[str, Tuple[Any, Optional[str], str]]:
    """Helper to create fragment updates for SSE responses.
    
    Auto-detects selector from element id if not provided.
    
    Examples:
        yield fragment(Div("Hello", id="msg"))  # Auto-detects #msg selector
        yield fragment(Div("Hello"), "#content")  # Explicit selector
        yield fragment(Div("Hello"), "#content", "append")  # With merge mode
        
    Args:
        content: Fragment content (HTML element or string)
        selector: CSS selector for target element (auto-detected if None)
        mode: Merge mode (morph, append, prepend, etc.)
        
    Returns:
        Tuple of ("fragments", (content, selector, mode))
    """
    return "fragments", (content, selector, mode)

# For backward compatibility with old naming
class ServerSentEventGenerator:
    """Legacy class for backward compatibility."""
    
    @staticmethod
    def _send(event_type: str, data_lines: List[str], event_id: Optional[str] = None, retry_duration: int = DEFAULT_RETRY_DURATION) -> str:
        return format_sse_event(event_type, data_lines, event_id, retry_duration)
    
    @classmethod
    def merge_signals(cls, signals: Dict[str, Any]) -> str:
        return format_signal_event(signals)
    
    @classmethod  
    def merge_fragments(cls, fragments: List[Any], selector: Optional[str] = None, merge_mode: str = DEFAULT_MERGE_MODE) -> str:
        return format_fragment_event(fragments, selector, merge_mode)