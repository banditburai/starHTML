"""Debug SSE merge fragments - test different scenarios"""

from starhtml import *

app, rt = star_app(
    title="SSE Debugging Demo",
    debug=True
)

@rt('/')
def home():
    return Div(
        H1("SSE Merge Fragments Debugging"),
        
        Div(
            Button("Test Simple Fragment", ds_on_click="@get('/test-simple')"),
            Button("Test Multiple Fragments", ds_on_click="@get('/test-multiple')"),
            Button("Test With Selector", ds_on_click="@get('/test-selector')"),
            Button("Test Complex HTML", ds_on_click="@get('/test-complex')"),
            Button("Reset All", ds_on_click="@get('/reset')", style="background: #ff5252; color: white;"),
            style="display: flex; gap: 10px; margin: 20px 0; flex-wrap: wrap;"
        ),
        
        Div(
            P("Initial content - will be replaced"),
            id="target",
            style="border: 1px solid #ccc; padding: 20px; margin: 20px 0;"
        ),
        
        Div(
            P("Secondary target - for selector tests"),
            id="target2",
            style="border: 1px solid #00c853; padding: 20px; margin: 20px 0;"
        ),
        
        Div(
            P("Status: ", ds_text="$status"),
            style="font-weight: bold; margin: 20px 0;"
        ),
        
        Div(
            Pre(
                Code(ds_text="$lastAction", style="white-space: pre-wrap;"),
                style="background: #f5f5f5; padding: 15px; overflow-x: auto;"
            ),
            style="margin-top: 20px;"
        ),
        
        ds_signals={"status": "Ready", "lastAction": "No action yet"}
    )

@rt('/test-simple')
@sse
def test_simple(req):
    yield signals(status="Testing simple fragment...")
    # Auto-detection: Since Div has id="target", selector "#target" is auto-detected
    yield fragments(
        Div(
            P("✅ Simple fragment replaced successfully!"),
            P("Notice: No manual selector needed - auto-detected from id!"),
            id="target",
            style="border: 1px solid #ccc; padding: 20px; margin: 20px 0;"
        )
    )
    yield signals(
        status="Simple fragment complete",
        lastAction="fragments(Div(id='target')) - auto-detected #target!"
    )

@rt('/test-multiple')
@sse
def test_multiple(req):
    yield signals(status="Testing multiple fragments...")
    
    fragments = [
        P("Fragment 1: First paragraph"),
        P("Fragment 2: Second paragraph", style="color: blue;"),
        Div(
            P("Fragment 3: Nested content"),
            P("Fragment 3: More nested content"),
            style="background: #f0f0f0; padding: 10px; margin: 10px 0;"
        )
    ]
    
    # Auto-detection: id="target" automatically becomes selector "#target"
    yield fragments(
        Div(
            *fragments,
            id="target",
            style="border: 1px solid #ccc; padding: 20px; margin: 20px 0;"
        )
    )
    yield signals(
        status="Multiple fragments complete",
        lastAction="fragments(Div(*fragments, id='target')) - auto-detected!"
    )

@rt('/test-selector')
@sse
def test_selector(req):
    yield signals(status="Testing auto-detection vs manual selectors...")
    
    # Auto-detection: id="target" automatically becomes "#target"
    yield fragments(
        Div(
            P("✅ Auto-detected from id='target'"),
            id="target",
            style="border: 1px solid #ccc; padding: 20px; margin: 20px 0;"
        )
    )
    
    # Manual override: explicitly specify different selector
    yield fragments(
        Div(
            P("✅ Manual override: targeting #target2", style="color: green;"),
            P("(Even though this div has id='target2', we could target anywhere)"),
            id="target2",
            style="border: 1px solid #00c853; padding: 20px; margin: 20px 0;"
        ),
        "#target2"  # Manual selector (could be different from id)
    )
    
    yield signals(
        status="Selector test complete",
        lastAction="Auto-detected #target + manual #target2"
    )

@rt('/test-complex')
@sse
def test_complex(req):
    yield signals(status="Testing complex HTML...")
    
    complex_content = Div(
        H1("Complex Content", style="font-size: 1.5em;"),
        P("This has special characters: < > & \" '"),
        Pre("Code block with\nmultiple lines\n    and indentation"),
        Div(
            Button("Nested button", ds_on_click="alert('Clicked!')"),
            P("With dynamic content", ds_text="'[dynamic text here]'"),
            style="background: #e3f2fd; padding: 10px;"
        )
    )
    
    # Auto-detection works with complex nested content too
    yield fragments(
        Div(
            complex_content,
            id="target",
            style="border: 1px solid #ccc; padding: 20px; margin: 20px 0;"
        )
    )
    yield signals(
        status="Complex HTML complete",
        lastAction="Complex HTML with auto-detected selector"
    )

@rt('/reset')
@sse
def reset(req):
    yield signals(status="Resetting...")
    
    # Both use auto-detection
    yield fragments(
        Div(
            P("Initial content - will be replaced"),
            id="target",
            style="border: 1px solid #ccc; padding: 20px; margin: 20px 0;"
        )
    )
    
    yield fragments(
        Div(
            P("Secondary target - for selector tests"),
            id="target2",
            style="border: 1px solid #00c853; padding: 20px; margin: 20px 0;"
        )
    )
    
    yield signals(
        status="Ready",
        lastAction="Reset with auto-detected selectors"
    )

if __name__ == "__main__":
    print("SSE Debugging Demo running on http://localhost:5001")
    serve()