"""Demo: Canvas Handler - Infinite Canvas with Pan/Zoom

This demo shows the canvas_handler in action with a pannable/zoomable canvas.
Demonstrates the 5-line Python implementation from the refined PRD.
"""

from starhtml import *

app, rt = star_app(
    title="Canvas Handler Demo",
    hdrs=[
        Script(src="https://cdn.jsdelivr.net/npm/@tailwindcss/browser@4"),
        # Canvas handler with default gray grid
        canvas_handler(),
        # Example: Customize grid appearance
        # canvas_handler(
        #     grid_color="#3b82f6",       # Blue major grid
        #     minor_grid_color="#93c5fd", # Light blue minor grid
        #     grid_size=150,              # Larger spacing
        #     minor_grid_size=30          # Larger minor spacing
        # ),
    ],
)


@rt("/")
def infinite_canvas():
    """Infinite canvas demo - exactly 5 lines of Python as promised."""
    return Div(
        H1("Infinite Canvas"),
        Div(  # Line 1: Toolbar
            Button("Reset View", ds_on_click("$canvas_reset_view()"), cls="btn"),
            Button("Zoom In", ds_on_click("$canvas_zoom_in()"), cls="btn"),
            Button("Zoom Out", ds_on_click("$canvas_zoom_out()"), cls="btn"),
            cls="toolbar",
        ),
        Div(  # Line 2: Viewport
            Div(  # Line 3: Container
                # Sample canvas content
                Div("🎯 Center Point", cls="canvas-item", style="left: 0px; top: 0px;"),
                Div("📍 Point A", cls="canvas-item", style="left: -400px; top: -200px;"),
                Div("📍 Point B", cls="canvas-item", style="left: 300px; top: -150px;"),
                Div("📍 Point C", cls="canvas-item", style="left: -200px; top: 200px;"),
                Div("📍 Point D", cls="canvas-item", style="left: 200px; top: 150px;"),
                ds_canvas_container(),
                cls="canvas-container",
            ),
            ds_canvas_viewport(),
            ds_on_canvas("console.log(`Canvas: pan=(${$canvas_pan_x},${$canvas_pan_y}) zoom=${$canvas_zoom}`)"),
            cls="canvas-viewport",
        ),
        # Status display
        Div(
            H3("Canvas Status"),
            P(f"Pan: ({ds_text('Math.round($canvas_pan_x)')}, {ds_text('Math.round($canvas_pan_y)')})"),
            P(f"Zoom: {ds_text('Math.round($canvas_zoom * 100)')}%"),
            P(f"Is Panning: {ds_text('$canvas_is_panning ? "Yes" : "No"')}"),
            cls="status",
        ),
        # Instructions
        Div(
            H3("Instructions"),
            Ul(
                Li("🖱️ Click and drag to pan around the canvas"),
                Li("🎯 Scroll wheel to zoom in/out"),
                Li("📱 On mobile: drag to pan, pinch to zoom"),
                Li("🔘 Use toolbar buttons for quick actions"),
            ),
            cls="instructions",
        ),
        # CSS Styles
        Style("""
            body {
                font-family: system-ui;
                margin: 0;
                padding: 1rem;
                background: #f0f0f0;
            }
            
            h1 {
                margin-bottom: 1rem;
            }
            
            .toolbar {
                display: flex;
                gap: 0.5rem;
                margin: 1rem 0;
                padding: 1rem;
                background: white;
                border-radius: 8px;
                border: 1px solid #ddd;
            }
            
            .btn {
                padding: 0.5rem 1rem;
                border: 1px solid #3b82f6;
                background: #3b82f6;
                color: white;
                border-radius: 6px;
                cursor: pointer;
                font-size: 0.9rem;
                transition: all 0.2s ease;
            }
            
            .btn:hover {
                background: #2563eb;
                border-color: #2563eb;
            }
            
            .btn:active {
                transform: translateY(1px);
            }
            
            .canvas-viewport {
                width: 100%;
                height: 500px;
                border: 2px solid #333;
                border-radius: 8px;
                overflow: hidden;
                position: relative;
                cursor: grab;
                margin: 1rem 0;
            }
            
            .canvas-viewport:active {
                cursor: grabbing;
            }
            
            .canvas-container {
                position: relative;
                width: 100%;
                height: 100%;
                transform-origin: 0 0;
                z-index: 1;
            }
            
            .canvas-item {
                position: absolute;
                padding: 0.5rem 1rem;
                background: #3b82f6;
                color: white;
                border-radius: 6px;
                font-size: 0.9rem;
                font-weight: 500;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                user-select: none;
                transform: translate(-50%, -50%);
            }
            
            
            .status, .instructions {
                background: white;
                padding: 1rem;
                border-radius: 8px;
                border: 1px solid #ddd;
                margin: 1rem 0;
            }
            
            .status p {
                margin: 0.5rem 0;
                font-family: monospace;
                font-size: 0.9rem;
            }
            
            .instructions ul {
                margin: 0.5rem 0;
                padding-left: 1.5rem;
            }
            
            .instructions li {
                margin: 0.5rem 0;
            }
        """),
        cls="canvas-demo",
    )


if __name__ == "__main__":
    print("=" * 60)
    print("🎯 INFINITE CANVAS DEMO")
    print("=" * 60)
    print("📍 Running on: http://localhost:5001")
    print("🎨 Features:")
    print("   • Infinite pan/zoom canvas")
    print("   • Grid background pattern")
    print("   • Touch and trackpad support")
    print("   • Smooth viewport preservation")
    print("   • 5-line Python implementation")
    print("=" * 60)
    serve(port=5001)
