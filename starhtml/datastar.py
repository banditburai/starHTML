"""Datastar SSE functionality for StarHTML."""

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


def sse(handler: Callable) -> Callable:    
    """Decorator that handles sequential signal/fragment updates for Datastar."""
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
                    
                    # Auto-detect selector if not provided and fragment has id
                    if selector is None and hasattr(fragment, 'attrs') and 'id' in fragment.attrs:
                        selector = f"#{fragment.attrs['id']}"
                    
                    yield ServerSentEventGenerator.merge_fragments(
                        fragment,
                        selector=selector,
                        merge_mode=merge_mode
                    )
        
        return StreamingResponse(stream_generator(), headers=SSE_HEADERS)
    return wrapped

def signal(**signals: Any) -> Tuple[str, Dict[str, Any]]:
    """Helper to create signal updates for SSE responses.
    
    Example:
        yield signal(count=5, message="Hello")
        # Generates: event: datastar-merge-signals
        #           data: signals {"count": 5, "message": "Hello"}
    """
    return "signals", signals

def fragment(content: Any, selector: Optional[str] = None, 
            mode: str = "morph") -> Tuple[str, Tuple[Any, Optional[str], str]]:
    """Helper to create fragment updates for SSE responses.
    
    Auto-detects selector from element id if not provided.
    
    Examples:
        yield fragment(Div("Hello", id="msg"))  # Auto-detects #msg selector
        yield fragment(Div("Hello"), "#content", "morph")  # Explicit selector
    """
    return "fragments", (content, selector, mode)

