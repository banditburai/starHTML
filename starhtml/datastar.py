"""Datastar SSE and helper functions for StarHTML."""

from typing import Any, Callable, Dict, Optional, Tuple, List
from functools import wraps
from starlette.responses import StreamingResponse
import json

from .components import to_xml

# SSE headers for proper event streaming
SSE_HEADERS = {
    'Content-Type': 'text/event-stream',
    'Cache-Control': 'no-cache', 
    'Connection': 'keep-alive'
}

class ServerSentEventGenerator:
    """Generate properly formatted SSE events for Datastar."""
    
    @staticmethod
    def _send(event_type: str, data_lines: List[str], event_id: Optional[str] = None, retry_duration: int = 1000) -> str:
        """Format an SSE event."""
        sse_msg = []
        if event_id:
            sse_msg.append(f"id: {event_id}")
        sse_msg.append(f"event: {event_type}")
        sse_msg.append(f"retry: {retry_duration}")
        for line in data_lines:
            sse_msg.append(f"data: {line}")
        sse_msg.append("")  # Empty line to signal end of event
        return "\n".join(sse_msg) + "\n"  # Extra newline for proper SSE format
    
    @classmethod
    def merge_signals(cls, signals: Dict[str, Any]) -> str:
        """Generate a datastar-merge-signals event."""
        # Datastar v1 RC expects this format
        return cls._send("datastar-merge-signals", [f"signals {json.dumps(signals)}"])
    
    @classmethod  
    def merge_fragments(cls, fragments: List[Any], selector: Optional[str] = None, merge_mode: str = "morph") -> str:
        """Generate a datastar-merge-fragments event."""
        # Convert fragments to XML/HTML first
        html_content = []
        for fragment in (fragments if isinstance(fragments, list) else [fragments]):
            # Check if it's a StarHTML component
            if hasattr(fragment, '__ft__') or hasattr(fragment, 'tag') or isinstance(fragment, (list, tuple)):
                html_content.append(to_xml(fragment, indent=False))
            else:
                html_content.append(str(fragment))
        
        # Join all HTML content into a single string
        all_html = ''.join(html_content)
        
        # SSE spec: newlines within data must be sent as multiple data: lines
        # But for Datastar, we keep fragments on a single line
        # Escape newlines as HTML entities to preserve them
        all_html = all_html.replace('\r\n', '&#10;').replace('\n', '&#10;').replace('\r', '&#10;')
        
        # Datastar v1 RC expects this format:
        # data: selector #targetElementId  
        # data: mergeMode morph
        # data: fragments <html fragment>
        data_lines = []
        if selector:
            data_lines.append(f"selector {selector}")
        data_lines.append(f"mergeMode {merge_mode}")
        data_lines.append(f"fragments {all_html}")
            
        return cls._send("datastar-merge-fragments", data_lines)


def sse_response(handler: Callable) -> Callable:    
    """Decorator that handles sequential signal/fragment updates for Datastar"""
    @wraps(handler)
    def wrapped(*args, **kwargs):
        def stream_generator():
            # Get the generator from the handler
            gen = handler(*args, **kwargs)
            
            # Process items from generator
            for item_type, payload in gen:
                if item_type == "signals":
                    yield ServerSentEventGenerator.merge_signals(payload)
                elif item_type == "fragments":
                    # Allow flexible fragment definitions
                    if isinstance(payload, tuple):
                        fragment, selector, merge_mode = payload + (None, "morph")[:3-len(payload)]
                    else:
                        fragment, selector, merge_mode = payload, None, "morph"
                    
                    yield ServerSentEventGenerator.merge_fragments(
                        fragment,
                        selector=selector,
                        merge_mode=merge_mode
                    )
        
        return StreamingResponse(stream_generator(), headers=SSE_HEADERS)
    return wrapped

# Alias for compatibility with ft-datastar
sse = sse_response

def update_signals(**signals: Any) -> Tuple[str, Dict[str, Any]]:
    """Helper to create signal updates for SSE responses
    
    Example:
        yield update_signals(count=5, message="Hello")
        # Generates: event: datastar-signal
        #           data: {"count": 5, "message": "Hello"}
    """
    return "signals", signals

def update_fragments(fragment: Any, selector: Optional[str] = None, 
                    merge_mode: str = "morph") -> Tuple[str, Tuple[Any, Optional[str], str]]:
    """Helper to create fragment updates for SSE responses
    
    Example:
        yield update_fragments(Div("Hello"), "#content", "morph")
        # Generates: event: datastar-fragment
        #           data: merge morph #content
        #           data: <div>Hello</div>
    """
    return "fragments", (fragment, selector, merge_mode)

# Helper functions similar to ft-datastar reference
class _DSHelper(dict):
    """Special dictionary that converts keys to proper data-* attributes"""
    def __init__(self, attrs: dict):
        super().__init__({
            key.replace('_', '-'): value 
            for key, value in attrs.items()
        })
    
    def __getitem__(self, key):
        # Support both hyphenated and underscore access
        try:
            return super().__getitem__(key)
        except KeyError:
            return super().__getitem__(key.replace('-', '_'))
    
    def get(self, key, default=None):
        try:
            return self[key]
        except KeyError:
            return default

def ds_attrs(**exprs: str) -> _DSHelper:
    """Convert expressions to DataStar data-attr-* attributes."""
    return _DSHelper({
        f"data_attr_{key}": value 
        for key, value in exprs.items()
    })

def ds_signals(exprs: Optional[Dict[str, Any]] = None, **kwargs: Any) -> _DSHelper:
    """Convert signals to a single data-signals attribute with JSON object"""
    import json
    
    def process_key(key: str) -> str:
        # Convert double underscores to dots for namespacing
        return key.replace('__', '.')
    
    inputs = {**(exprs or {}), **kwargs}
    
    # Process the inputs directly as a Python dict, then serialize to JSON
    processed_dict = {}
    for k, v in inputs.items():
        processed_key = process_key(k)
        # Handle different value types properly for JSON serialization
        if isinstance(v, str) and v.startswith("'") and v.endswith("'"):
            # String values with quotes - remove the quotes for JSON
            processed_dict[processed_key] = v[1:-1]
        elif isinstance(v, str) and v in ('true', 'false'):
            # Boolean strings
            processed_dict[processed_key] = v == 'true'
        elif isinstance(v, bool):
            # Python booleans
            processed_dict[processed_key] = v
        elif isinstance(v, (int, float)):
            # Numbers
            processed_dict[processed_key] = v
        elif isinstance(v, str) and v.isdigit():
            # String numbers
            processed_dict[processed_key] = int(v)
        else:
            # Everything else (including already quoted strings)
            processed_dict[processed_key] = v
    
    # Serialize to JSON
    json_signals = json.dumps(processed_dict)
    
    return _DSHelper({"data_signals": json_signals})

def ds_on(**events: str) -> _DSHelper:
    """Convert event handlers to DataStar data-on-* attributes."""
    return _DSHelper({
        f"data_on_{k}": v 
        for k, v in events.items()
    })

def ds_show(*args, **conditions: str) -> _DSHelper:
    """Convert expressions to DataStar data-show attributes."""
    if args:
        if conditions:
            raise ValueError("Cannot mix positional and keyword arguments")
        return _DSHelper({"data_show": args[0]})
    if "when" in conditions:
        return _DSHelper({"data_show": conditions["when"]})
    return _DSHelper({"data_show": next(iter(conditions.values()))})

def ds_bind(name: str) -> _DSHelper:
    """Create data-bind attribute helper for direct value syntax."""
    return _DSHelper({"data_bind": name})

def ds_text(expr: str) -> _DSHelper:
    """Create data-text attribute helper."""
    return _DSHelper({"data_text": expr})

def ds_indicator(signal_name: str) -> _DSHelper:
    """Track request state with a boolean signal."""
    return _DSHelper({"data_indicator": signal_name})