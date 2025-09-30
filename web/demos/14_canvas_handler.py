"""Demo: Canvas Handler - Infinite Canvas with Pan/Zoom

This demo shows the canvas_handler in action with a pannable/zoomable canvas.
Demonstrates the 5-line Python implementation from the refined PRD.
"""

from starhtml import *

app, rt = star_app(
    title="Canvas Handler Demo",
    hdrs=[
        Script(src="https://cdn.jsdelivr.net/npm/@tailwindcss/browser@4"),
        Style(
            """body{background:#fff;color:#000;margin:0;padding:0;-webkit-font-smoothing:antialiased;-moz-osx-font-smoothing:grayscale}::selection{background:#000;color:#fff}.canvas-viewport{width:100%;height:500px;border:1px solid #e5e7eb;border-top:0;border-radius:0 0 0.5rem 0.5rem;overflow:hidden;position:relative;cursor:grab;background:#fafafa}.canvas-viewport:active{cursor:grabbing}.canvas-container{position:relative;width:100%;height:100%;transform-origin:0 0;z-index:1}.canvas-item{position:absolute;padding:0.5rem 1rem;background:#3b82f6;color:white;border-radius:6px;font-size:0.9rem;font-weight:500;box-shadow:0 2px 4px rgba(0,0,0,0.1);user-select:none;transform:translate(-50%, -50%)}"""
        ),
        # Canvas handler with default gray grid
        (canvas := canvas_handler()),
    ],
    iconify=True,
    compression=False,
)


@rt("/")
def infinite_canvas():
    """Infinite canvas demo - exactly 5 lines of Python as promised."""
    return Div(
        # Header section with large number
        Div(
            H1("14", cls="text-8xl font-black text-gray-100 leading-none"),
            H1("Canvas Handler", cls="text-5xl md:text-6xl font-bold text-black mt-2"),
            P("Infinite canvas with pan and zoom capabilities", cls="text-lg text-gray-600 mt-4"),
            cls="mb-16",
        ),
        # Interactive Canvas Section - All integrated
        Div(
            H3("Interactive Canvas", cls="text-2xl font-bold text-black mb-6"),
            P("Click and drag to pan, scroll to zoom", cls="text-gray-600 mb-6"),
            # Controls bar at top of canvas
            Div(
                # Left side - controls
                Div(
                    Button(
                        Icon("material-symbols:reset-wrench", cls="mr-2"),
                        "Reset View",
                        data_on_click=canvas.reset_view(),
                        cls="px-4 py-2 bg-black text-white font-medium hover:bg-gray-800 transition-colors",
                    ),
                    Button(
                        Icon("material-symbols:zoom-in", cls="mr-2"),
                        "Zoom In",
                        data_on_click=canvas.zoom_in(),
                        cls="px-4 py-2 bg-blue-600 text-white font-medium hover:bg-blue-700 transition-colors",
                    ),
                    Button(
                        Icon("material-symbols:zoom-out", cls="mr-2"),
                        "Zoom Out",
                        data_on_click=canvas.zoom_out(),
                        cls="px-4 py-2 bg-gray-600 text-white font-medium hover:bg-gray-700 transition-colors",
                    ),
                    cls="flex flex-wrap gap-2",
                ),
                # Right side - status
                Div(
                    Div(
                        Span("Pan: ", cls="text-gray-600"),
                        Span(
                            data_text=f("({x}, {y})", x=canvas.pan_x.round(), y=canvas.pan_y.round()),
                            cls="font-mono text-black",
                        ),
                    ),
                    Div(
                        Span("Zoom: ", cls="text-gray-600"),
                        Span(data_text=f("{z}%", z=(canvas.zoom * 100).round()), cls="font-mono text-black"),
                    ),
                    cls="flex gap-6 text-sm",
                ),
                cls="flex flex-wrap justify-between items-center p-4 bg-gray-50 border border-gray-200 border-b-0 rounded-t-lg",
            ),
            # Canvas viewport - directly attached to controls
            Div(
                Div(
                    # Sample canvas content
                    Div("Center Point", cls="canvas-item", style="left: 0px; top: 0px;"),
                    Div("Point A", cls="canvas-item", style="left: -400px; top: -200px;"),
                    Div("Point B", cls="canvas-item", style="left: 300px; top: -150px;"),
                    Div("Point C", cls="canvas-item", style="left: -200px; top: 200px;"),
                    Div("Point D", cls="canvas-item", style="left: 200px; top: 150px;"),
                    data_canvas_container=True,
                    cls="canvas-container",
                ),
                data_canvas_viewport=True,
                data_on_canvas=console.log(
                    f("Canvas: pan=({x},{y}) zoom={z}", x=canvas.pan_x, y=canvas.pan_y, z=canvas.zoom)
                ),
                cls="canvas-viewport",
            ),
            cls="mb-12 p-8 bg-white border border-gray-200",
        ),
        # Instructions
        Div(
            H3("Instructions", cls="text-2xl font-bold text-black mb-6"),
            Ul(
                Li("Click and drag to pan around the canvas", cls="mb-2"),
                Li("Scroll wheel to zoom in/out", cls="mb-2"),
                Li("On mobile: drag to pan, pinch to zoom", cls="mb-2"),
                Li("Use toolbar buttons for quick actions"),
                cls="list-disc list-inside text-gray-700",
            ),
            cls="mb-12 p-8 bg-gray-50",
        ),
        cls="max-w-5xl mx-auto px-8 sm:px-12 lg:px-16 py-16 sm:py-20 md:py-24 bg-white min-h-screen",
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
