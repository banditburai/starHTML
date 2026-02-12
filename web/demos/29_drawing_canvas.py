"""Demo: Drawing Canvas - SVG Drawing Canvas

Demonstrates <drawing-canvas> starelements component with full floating toolbar.
Full-page canvas with floating toolbar overlay.
"""

from star_drawing import DrawingCanvas, drawing_toolbar

from starhtml import *

app, rt = star_app(
    title="Drawing Canvas Demo",
    htmlkw={"lang": "en"},
    hdrs=[
        Link(rel="preconnect", href="https://fonts.googleapis.com"),
        Link(rel="preconnect", href="https://fonts.gstatic.com", crossorigin=""),
        Link(
            rel="stylesheet",
            href="https://fonts.googleapis.com/css2?family=Shantell+Sans:wght@400;700&display=swap",
        ),
        Script(src="https://cdn.jsdelivr.net/npm/@tailwindcss/browser@4"),
        iconify_script(),
        Style(
            """html,body{margin:0;padding:0;width:100%;height:100%;overflow:hidden}.toolbar-island{position:fixed;top:12px;left:50%;transform:translateX(-50%);z-index:10;max-width:calc(100vw - 24px)}.toolbar-bar{display:inline-flex;align-items:center;gap:2px;padding:4px;background:white;border-radius:12px;box-shadow:0 0 0 1px rgba(0,0,0,0.04),0 2px 4px rgba(0,0,0,0.06),0 8px 16px rgba(0,0,0,0.04)}.tool-btn{display:flex;align-items:center;justify-content:center;width:36px;height:36px;border-radius:8px;border:none;background:transparent;color:#374151;cursor:pointer;transition:background 0.12s,color 0.12s;flex-shrink:0}.tool-btn:hover{background:#f3f4f6}.tool-btn:focus-visible{outline:2px solid #93c5fd;outline-offset:-2px}.tool-btn:focus:not(:focus-visible){outline:none}.tool-btn.selected{background:#dbeafe;color:#1d4ed8}.tool-btn.selected:hover{background:#bfdbfe}.action-btn{display:flex;align-items:center;justify-content:center;width:32px;height:32px;border-radius:8px;border:none;background:transparent;color:#6b7280;cursor:pointer;transition:background 0.12s,color 0.12s;flex-shrink:0}.action-btn:hover{background:#f3f4f6;color:#374151}.action-btn[disabled="true"]{opacity:0.3;cursor:not-allowed;pointer-events:none}.action-btn.danger:hover{background:#fee2e2;color:#dc2626}.toolbar-divider{width:1px;height:20px;background:#e5e7eb;margin:0 2px;flex-shrink:0}.color-trigger{width:28px;height:28px;border-radius:8px;border:none;cursor:pointer;padding:0;transition:box-shadow 0.12s;flex-shrink:0;position:relative;box-sizing:border-box}.color-trigger:hover{box-shadow:0 0 0 2px rgba(0,0,0,0.15)}.color-trigger:focus-visible{outline:2px solid #93c5fd;outline-offset:1px}.color-trigger-fill{position:absolute;inset:4px;border-radius:4px}.popover-anchor{position:relative;display:inline-flex}.toolbar-popover{position:absolute;top:calc(100% + 8px);right:0;background:white;border-radius:12px;padding:12px;box-shadow:0 0 0 1px rgba(0,0,0,0.06),0 4px 8px rgba(0,0,0,0.08),0 12px 24px rgba(0,0,0,0.06);min-width:220px;z-index:20;animation:popover-in 0.12s ease-out}@keyframes popover-in{from{opacity:0;transform:translateY(-4px)}to{opacity:1;transform:translateY(0)}}.panel-section{margin-bottom:10px}.panel-section:last-child{margin-bottom:0}.panel-section-header{display:flex;align-items:center;gap:8px;margin-bottom:6px}.panel-label{display:block;font-size:11px;font-weight:600;color:#6b7280;text-transform:uppercase;letter-spacing:0.05em;margin-bottom:6px;user-select:none}.panel-section-header .panel-label{margin-bottom:0}.panel-value{font-size:11px;font-weight:500;color:#6b7280;font-variant-numeric:tabular-nums}.swatch-grid{display:flex;flex-wrap:wrap;gap:4px;align-items:center}.color-swatch{width:26px;height:26px;border-radius:6px;border:2.5px solid transparent;cursor:pointer;transition:transform 0.1s,border-color 0.1s;padding:0;flex-shrink:0;box-shadow:inset 0 0 0 1px rgba(0,0,0,0.1)}.color-swatch:hover{transform:scale(1.1);border-color:rgba(0,0,0,0.12)}.color-swatch.selected{border-color:#3b82f6;box-shadow:0 0 0 2px rgba(59,130,246,0.25)}.color-picker{width:26px;height:26px;border:none;border-radius:6px;cursor:pointer;padding:0;background:conic-gradient(red,yellow,lime,aqua,blue,magenta,red)}.color-picker::-webkit-color-swatch-wrapper{padding:2px}.color-picker::-webkit-color-swatch{border:2px solid rgba(255,255,255,0.8);border-radius:4px}.color-picker::-moz-color-swatch{border:2px solid rgba(255,255,255,0.8);border-radius:4px}.no-fill-swatch{width:100%;height:100%;border-radius:4px;background:linear-gradient(to top right,transparent calc(50% - 1px),#dc2626 calc(50% - 1px),#dc2626 calc(50% + 1px),transparent calc(50% + 1px)),white;border:1px solid #e5e7eb}.btn-row{display:flex;gap:4px;flex-wrap:wrap}.style-btn{padding:5px 10px;border-radius:6px;border:1px solid #e5e7eb;background:white;font-size:11px;font-weight:500;cursor:pointer;transition:background 0.12s,border-color 0.12s;display:flex;align-items:center;justify-content:center}.style-btn:hover{background:#f9fafb;border-color:#d1d5db}.style-btn.selected{background:#dbeafe;border-color:#93c5fd;color:#1d4ed8}.width-btn{width:32px;height:32px;padding:0}.width-dot{border-radius:50%;background:currentColor}.dash-preview{width:24px;height:2px}.dash-preview.solid{background:currentColor}.dash-preview.dashed{background:repeating-linear-gradient(90deg,currentColor 0 6px,transparent 6px 10px)}.dash-preview.dotted{background:repeating-linear-gradient(90deg,currentColor 0 2px,transparent 2px 6px)}.styled-slider{-webkit-appearance:none;appearance:none;height:4px;background:#e5e7eb;border-radius:2px;cursor:pointer}.styled-slider.full-width{width:100%}.styled-slider::-webkit-slider-thumb{-webkit-appearance:none;appearance:none;width:14px;height:14px;border-radius:50%;background:#3b82f6;border:2px solid white;box-shadow:0 1px 3px rgba(0,0,0,0.2);cursor:grab}.styled-slider::-webkit-slider-thumb:active{cursor:grabbing}.styled-slider::-moz-range-thumb{width:14px;height:14px;border-radius:50%;background:#3b82f6;border:2px solid white;box-shadow:0 1px 3px rgba(0,0,0,0.2);cursor:grab}@media (max-width:640px){.toolbar-bar{max-width:calc(100vw - 32px);overflow-x:auto;scrollbar-width:none}.toolbar-bar::-webkit-scrollbar{display:none}.toolbar-popover{min-width:200px}}"""
        ),
    ],
)

app.register(DrawingCanvas)

canvas = DrawingCanvas(
    name="drawing",
    style="position:fixed;inset:0;width:100%;height:100%;background:white;touch-action:none;z-index:0;",
)


@rt("/")
def drawing_demo():
    return Div(
        # Full-page canvas layer
        canvas,
        drawing_toolbar(canvas),
        # Header overlay - visible but doesn't block drawing
        Div(
            H1("29", cls="text-8xl font-black text-gray-100 leading-none"),
            H1("Drawing Canvas", cls="text-5xl md:text-6xl font-bold text-black mt-2"),
            P(
                "SVG drawing canvas with floating toolbar",
                cls="text-lg text-gray-600 mt-4",
            ),
            cls="fixed bottom-6 left-6 pointer-events-none select-none z-20",
        ),
    )


if __name__ == "__main__":
    print("Drawing Canvas Demo: http://localhost:5029")
    serve(port=5029)
