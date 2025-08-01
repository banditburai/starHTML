"""Debug SSE merge fragments - test different scenarios"""

from starhtml import *

app, rt = star_app(
    title="SSE Debugging Demo",
    hdrs=[
        Script(src="https://cdn.jsdelivr.net/npm/@tailwindcss/browser@4"),
    ],
)


@rt("/")
def home():
    return Div(
        Style("""
            body {
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%);
                margin: 0;
                min-height: 100vh;
            }
            .container {
                max-width: 900px;
                margin: 0 auto;
                padding: 2rem;
            }
            .card {
                background: white;
                border-radius: 12px;
                box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
                border: 1px solid #e5e7eb;
                padding: 1.5rem;
                margin-bottom: 1.5rem;
            }
            .btn {
                padding: 0.75rem 1.5rem;
                border-radius: 8px;
                border: none;
                font-weight: 500;
                cursor: pointer;
                transition: all 0.2s;
                font-size: 0.9rem;
            }
            .btn-primary {
                background: linear-gradient(135deg, #3b82f6 0%, #1e40af 100%);
                color: white;
            }
            .btn-primary:hover {
                background: linear-gradient(135deg, #2563eb 0%, #1e3a8a 100%);
                transform: translateY(-1px);
                box-shadow: 0 8px 15px rgba(59, 130, 246, 0.3);
            }
            .btn-secondary {
                background: linear-gradient(135deg, #10b981 0%, #047857 100%);
                color: white;
            }
            .btn-secondary:hover {
                background: linear-gradient(135deg, #059669 0%, #065f46 100%);
                transform: translateY(-1px);
                box-shadow: 0 8px 15px rgba(16, 185, 129, 0.3);
            }
            .btn-danger {
                background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%);
                color: white;
            }
            .btn-danger:hover {
                background: linear-gradient(135deg, #dc2626 0%, #b91c1c 100%);
                transform: translateY(-1px);
                box-shadow: 0 8px 15px rgba(239, 68, 68, 0.3);
            }
            .status-bar {
                background: linear-gradient(135deg, #dbeafe 0%, #bfdbfe 100%);
                border: 1px solid #93c5fd;
                border-radius: 8px;
                padding: 1rem;
                display: flex;
                justify-content: space-between;
                align-items: center;
            }
        """),
        Div(
            H1("SSE Merge Elements Debugging", cls="text-3xl font-bold text-center mb-6"),
            Div(
                Button("Test Simple Element", ds_on_click("@get('/test-simple')"), cls="btn btn-primary"),
                Button("Test Multiple Elements", ds_on_click("@get('/test-multiple')"), cls="btn btn-primary"),
                Button("Test With Selector", ds_on_click("@get('/test-selector')"), cls="btn btn-secondary"),
                Button("Test Complex HTML", ds_on_click("@get('/test-complex')"), cls="btn btn-secondary"),
                Button("Reset All", ds_on_click("@get('/reset')"), cls="btn btn-danger"),
                style="display: flex; gap: 10px; margin: 20px 0; flex-wrap: wrap;",
            ),
            Div(
                P("Initial content - will be replaced"),
                id="target",
                cls="card",
            ),
            Div(
                P("Secondary target - for selector tests"),
                id="target2",
                style="border: 1px solid #00c853; padding: 20px; margin: 20px 0; border-radius: 8px; background: white;",
            ),
            Div(P("Status: ", ds_text("$status")), cls="status-bar"),
            Div(
                Pre(
                    Code(ds_text("$last_action"), style="white-space: pre-wrap;"),
                    style="background: #f5f5f5; padding: 15px; overflow-x: auto; border-radius: 8px;",
                ),
                cls="card",
            ),
            cls="container",
        ),
        ds_signals(status="Ready", last_action="No action yet"),
    )


@rt("/test-simple")
@sse
def test_simple(req):
    yield signals(status="Testing simple element...")
    # Auto-detection: Since Div has id="target", selector "#target" is auto-detected
    yield elements(
        Div(
            P("✅ Simple element replaced successfully!"),
            P("Notice: No manual selector needed - auto-detected from id!"),
            id="target",
            style="border: 1px solid #ccc; padding: 20px; margin: 20px 0;",
        )
    )
    yield signals(status="Simple element complete", last_action="elements(Div(id='target')) - auto-detected #target!")


@rt("/test-multiple")
@sse
def test_multiple(req):
    yield signals(status="Testing multiple elements...")

    fragments = [
        P("Element 1: First paragraph"),
        P("Element 2: Second paragraph", style="color: blue;"),
        Div(
            P("Element 3: Nested content"),
            P("Element 4: More nested content"),
            style="background: #f0f0f0; padding: 10px; margin: 10px 0;",
        ),
    ]

    # Auto-detection: id="target" automatically becomes selector "#target"
    yield elements(Div(*fragments, id="target", style="border: 1px solid #ccc; padding: 20px; margin: 20px 0;"))
    yield signals(
        status="Multiple fragments complete", last_action="elements(Div(*fragments, id='target')) - auto-detected!"
    )


@rt("/test-selector")
@sse
def test_selector(req):
    yield signals(status="Testing auto-detection vs manual selectors...")

    # Auto-detection: id="target" automatically becomes "#target"
    yield elements(
        Div(
            P("✅ Auto-detected from id='target'"),
            id="target",
            style="border: 1px solid #ccc; padding: 20px; margin: 20px 0;",
        )
    )

    # Manual override: explicitly specify different selector
    yield elements(
        Div(
            P("✅ Manual override: targeting #target2", style="color: green;"),
            P("(Even though this div has id='target2', we could target anywhere)"),
            id="target2",
            style="border: 1px solid #00c853; padding: 20px; margin: 20px 0;",
        ),
        "#target2",  # Manual selector (could be different from id)
    )

    yield signals(status="Selector test complete", last_action="Auto-detected #target + manual #target2")


@rt("/test-complex")
@sse
def test_complex(req):
    yield signals(status="Testing complex HTML...")

    complex_content = Div(
        H1("Complex Content", style="font-size: 1.5em;"),
        P("This has special characters: < > & \" '"),
        Pre("Code block with\nmultiple lines\n    and indentation"),
        Div(
            Button("Nested button", ds_on_click("alert('Clicked!')")),
            P("With dynamic content", ds_text("'[dynamic text here]'")),
            style="background: #e3f2fd; padding: 10px;",
        ),
    )

    # Auto-detection works with complex nested content too
    yield elements(Div(complex_content, id="target", style="border: 1px solid #ccc; padding: 20px; margin: 20px 0;"))
    yield signals(status="Complex HTML complete", last_action="Complex HTML with auto-detected selector")


@rt("/reset")
@sse
def reset(req):
    yield signals(status="Resetting...")

    # Both use auto-detection
    yield elements(
        Div(
            P("Initial content - will be replaced"),
            id="target",
            style="border: 1px solid #ccc; padding: 20px; margin: 20px 0;",
        )
    )

    yield elements(
        Div(
            P("Secondary target - for selector tests"),
            id="target2",
            style="border: 1px solid #00c853; padding: 20px; margin: 20px 0;",
        )
    )

    yield signals(status="Ready", last_action="Reset with auto-detected selectors")


if __name__ == "__main__":
    print("SSE Debugging Demo running on http://localhost:5001")
    serve(port=5001)
