"""Debug SSE merge fragments - test different scenarios"""

from starhtml import star_app, Div, Button, P, H1, Pre, Code
from starhtml.datastar import ds_signals, ds_on, ds_text, sse_response, update_fragments, update_signals
from starhtml.core import serve

app, rt = star_app(
    title="SSE Debugging Demo",
    debug=True
)

@rt('/')
def home():
    return Div(
        H1("SSE Merge Fragments Debugging"),
        
        Div(
            Button("Test Simple Fragment", **ds_on(click="@get('/test-simple')")),
            Button("Test Multiple Fragments", **ds_on(click="@get('/test-multiple')")),
            Button("Test With Selector", **ds_on(click="@get('/test-selector')")),
            Button("Test Complex HTML", **ds_on(click="@get('/test-complex')")),
            Button("Reset All", **ds_on(click="@get('/reset')"), style="background: #ff5252; color: white;"),
            style="display: flex; gap: 10px; margin: 20px 0; flex-wrap: wrap;"
        ),
        
        Div(
            P("Initial content - will be replaced"),
            id="target",
            style="border: 1px solid #ccc; padding: 20px; margin: 20px 0;"
        ),
        
        Div(
            P("Second target - for multiple fragment tests"),
            id="target2",
            style="border: 1px solid #ccc; padding: 20px; margin: 20px 0;"
        ),
        
        
        **ds_signals(status="ready")
    )

@rt('/test-simple')
@sse_response
def test_simple():
    """Test simple fragment replacement"""
    yield update_fragments(
        Div(
            P("Simple fragment replacement worked!", style="color: green; font-weight: bold;"),
            id="target"  # Maintain the ID for subsequent updates
        ),
        "#target"
    )

@rt('/test-multiple') 
@sse_response
def test_multiple():
    """Test multiple fragment updates to different targets"""
    # Update first target with multiple child elements
    yield update_fragments(
        Div(
            Div(P("First fragment"), id="part1", style="background: #e8f5e9; padding: 10px; margin: 5px;"),
            Div(P("Second fragment"), id="part2", style="background: #fff3e0; padding: 10px; margin: 5px;"),
            id="target"  # Keep the same ID so subsequent updates work
        ),
        "#target"
    )
    # Also update the second target
    yield update_fragments(
        Div(
            P("Target 2 also updated!", style="color: red; font-weight: bold;"),
            id="target2"
        ),
        "#target2"
    )

@rt('/test-selector')
@sse_response  
def test_selector():
    """Test updating different selectors"""
    yield update_fragments(
        Div(P("Updated target 1", style="color: blue;"), id="target"),
        "#target"
    )
    yield update_fragments(
        Div(P("Updated target 2", style="color: purple;"), id="target2"),
        "#target2"
    )

@rt('/test-complex')
@sse_response
def test_complex():
    """Test complex HTML with special characters"""
    # Use proper multi-line string with explicit line breaks
    code_content = """function test() {
  console.log('Hello');
  // This is a comment
  return 42;
}"""
    
    yield update_fragments(
        Div(
            H1("Complex <HTML> Test"),
            P('Text with "quotes" and \'apostrophes\''),
            P("Special chars: < > & \" '"),
            Pre(
                Code(code_content),
                style="background: #2d2d2d; color: #f8f8f2; padding: 10px; border-radius: 5px; white-space: pre-wrap; font-family: monospace;"
            ),
            id="target",  # Maintain the ID
            style="background: #e0e0e0; padding: 10px;"
        ),
        "#target"
    )

@rt('/reset')
@sse_response
def reset():
    """Reset all targets to initial state"""
    yield update_fragments(
        Div(
            P("Initial content - will be replaced"),
            id="target"
        ),
        "#target"
    )
    yield update_fragments(
        Div(
            P("Second target - for multiple fragment tests"),
            id="target2"
        ),
        "#target2"
    )
    yield update_signals(status="Reset complete")

if __name__ == "__main__":
    print("SSE Debugging Demo running on http://localhost:5001")
    print("Open browser console to see SSE events")
    serve()