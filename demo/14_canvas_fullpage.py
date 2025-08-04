"""Demo: Full-Page Infinite Canvas with Advanced Interactions

Demonstrates:
- Full viewport infinite canvas
- Context menu handling
- Keyboard shortcuts
- Touch/trackpad optimizations
"""

from starhtml import *

app, rt = star_app(
    title="Full-Page Canvas Demo",
    hdrs=[
        Script(src="https://cdn.jsdelivr.net/npm/@tailwindcss/browser@4"),
        canvas_handler(grid_color="rgba(255,255,255,0.1)", minor_grid_color="rgba(255,255,255,0.05)"),
        # Override viewport background for dark theme
        Style("[data-canvas-viewport] { background: #2a2a2a !important; }"),
    ],
)


@rt("/")
def fullpage_canvas():
    """Full-page infinite canvas with advanced interactions."""
    return Div(
        # Full-page canvas viewport
        Div(
            # Canvas container with content
            Div(
                # Canvas items
                Div("🎯 Origin (0,0)", cls="canvas-item origin", style="left: 0px; top: 0px;"),
                Div("📍 Node A", cls="canvas-item", style="left: 200px; top: -100px;"),
                Div("📍 Node B", cls="canvas-item", style="left: -300px; top: 200px;"),
                Div("📍 Node C", cls="canvas-item", style="left: 400px; top: 300px;"),
                ds_canvas_container(),
                cls="canvas-container",
            ),
            ds_canvas_viewport(),
            ds_on_canvas(
                "console.log(`Canvas interaction: pan=(${$canvas_pan_x},${$canvas_pan_y}) zoom=${$canvas_zoom}`)"
            ),
            cls="canvas-viewport fullpage",
        ),
        # Modern dark toolbar - top right
        Div(
            Button("R", ds_on_click("$canvas_reset_view()"), cls="toolbar-btn reset-btn", title="Reset View"),
            Button("−", ds_on_click("$canvas_zoom_out()"), cls="toolbar-btn zoom-btn", title="Zoom Out"),
            Button("+", ds_on_click("$canvas_zoom_in()"), cls="toolbar-btn zoom-btn", title="Zoom In"),
            Div(Span(ds_text("Math.round($canvas_zoom * 100) + '%'"), cls="zoom-indicator"), cls="status-display"),
            cls="modern-toolbar",
        ),
        # Context menu (simplified for now)
        # Div(
        #     Div("Add Node", ds_on_click("console.log('Add node')"), cls="menu-item"),
        #     cls="context-menu"
        # ),
        # CSS Styles
        Style("""
            body {
                margin: 0;
                padding: 0;
                overflow: hidden;
                font-family: system-ui;
            }
            
            .canvas-viewport.fullpage {
                position: fixed;
                top: 0;
                left: 0;
                width: 100vw;
                height: 100vh;
                overflow: hidden;
                background: #f8f9fa;
                cursor: grab;
                touch-action: none;
                user-select: none;
                -webkit-user-select: none;
                overscroll-behavior: none;
            }
            
            .canvas-viewport.fullpage:active {
                cursor: grabbing;
            }
            
            .canvas-container {
                position: relative;
                width: 100%;
                height: 100%;
                transform-origin: 0 0;
            }
            
            .canvas-item {
                position: absolute;
                padding: 0.75rem 1.25rem;
                background: #3b82f6;
                color: white;
                border-radius: 8px;
                font-size: 0.9rem;
                font-weight: 500;
                box-shadow: 0 4px 6px rgba(0,0,0,0.1);
                user-select: none;
                transform: translate(-50%, -50%);
                cursor: pointer;
                transition: transform 0.1s ease;
            }
            
            .canvas-item:hover {
                transform: translate(-50%, -50%) scale(1.05);
                box-shadow: 0 6px 12px rgba(0,0,0,0.15);
            }
            
            .canvas-item.origin {
                background: #ef4444;
                font-weight: 600;
            }
            
            .modern-toolbar {
                position: fixed;
                top: 1rem;
                right: 1rem;
                display: flex;
                align-items: center;
                gap: 4px;
                padding: 8px;
                background: rgba(30, 30, 30, 0.95);
                backdrop-filter: blur(12px);
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 12px;
                box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
                z-index: 1000;
            }
            
            .toolbar-btn {
                width: 32px;
                height: 32px;
                border: none;
                border-radius: 8px;
                font-size: 14px;
                font-weight: 600;
                cursor: pointer;
                transition: all 0.2s ease;
                display: flex;
                align-items: center;
                justify-content: center;
                color: #e5e7eb;
                background: rgba(255, 255, 255, 0.08);
            }
            
            .toolbar-btn:hover {
                background: rgba(255, 255, 255, 0.15);
                color: #ffffff;
                transform: translateY(-1px);
            }
            
            .toolbar-btn:active {
                transform: translateY(0);
                background: rgba(255, 255, 255, 0.2);
            }
            
            .reset-btn {
                background: rgba(59, 130, 246, 0.2);
                color: #60a5fa;
            }
            
            .reset-btn:hover {
                background: rgba(59, 130, 246, 0.3);
                color: #93c5fd;
            }
            
            .status-display {
                margin-left: 8px;
                padding: 0 12px;
                border-left: 1px solid rgba(255, 255, 255, 0.15);
            }
            
            .zoom-indicator {
                font-family: 'SF Mono', 'Monaco', 'Inconsolata', 'Roboto Mono', monospace;
                font-size: 12px;
                font-weight: 500;
                color: #9ca3af;
                white-space: nowrap;
            }
            
            
            /* Prevent mobile browser chrome from appearing */
            @media (max-width: 768px) {
                .canvas-viewport.fullpage {
                    position: fixed;
                    top: 0;
                    left: 0;
                    right: 0;
                    bottom: 0;
                    width: 100%;
                    height: 100%;
                }
            }
        """),
        # Auto-focus container on load
        ds_on_load("el.focus()"),
        # Keyboard shortcuts
        ds_on_keydown("""
              if (evt.target.tagName === 'INPUT') return;
              
              switch(evt.key) {
                  case 'r':
                  case 'R':
                      $canvas_reset_view();
                      evt.preventDefault();
                      break;
                  case '+':
                  case '=':
                      $canvas_zoom_in();
                      evt.preventDefault();
                      break;
                  case '-':
                  case '_':
                      $canvas_zoom_out();
                      evt.preventDefault();
                      break;
              }
          """),
        cls="fullpage-canvas-demo",
        tabindex="0",  # Make div focusable for keyboard events
        style="outline: none;",  # Remove focus outline
    )


if __name__ == "__main__":
    print("=" * 60)
    print("🌌 FULL-PAGE CANVAS DEMO")
    print("=" * 60)
    print("📍 Running on: http://localhost:5001")
    print("🎨 Features:")
    print("   • Full-screen infinite canvas")
    print("   • Dark theme with subtle grid")
    print("   • Floating control toolbar")
    print("   • Keyboard shortcuts (R, +, -)")
    print("   • Context menu interactions")
    print("=" * 60)
    serve(port=5001)
