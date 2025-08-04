"""Demo: Drag Handler - Sortable Todo List

This demo shows the drag_handler in action with a simple sortable todo list.
Demonstrates the 3-line Python implementation from the refined PRD.
"""

from starhtml import *

# Sample todo data
todos = [
    {"id": 1, "text": "Learn StarHTML", "completed": False},
    {"id": 2, "text": "Build drag interface", "completed": False},
    {"id": 3, "text": "Test on mobile", "completed": False},
    {"id": 4, "text": "Deploy to production", "completed": False},
]

app, rt = star_app(
    title="Drag Handler Demo",
    hdrs=[
        Script(src="https://cdn.jsdelivr.net/npm/@tailwindcss/browser@4"),
        drag_handler("todos", mode="sortable"),
    ],
)


@rt("/")
def sortable_todos():
    """Sortable todo list demo - exactly 3 lines of Python as promised."""
    return Div(
        H1("Sortable Todo List"),
        # Accessibility instructions for screen readers
        Div(
            "Use space or enter to grab an item. While dragging, use arrow keys to move, "
            "tab to cycle through drop zones, and space or enter to drop. Press escape to cancel.",
            id="drag-instructions",
            cls="sr-only",
        ),
        # Live region for screen reader announcements
        Div(id="drag-status", **{"aria-live": "polite", "aria-atomic": "true"}, cls="sr-only"),
        # Original todo list as a drop zone
        Div(
            H3("Todo List"),
            Div(
                *[Div(todo["text"], ds_draggable(), id=f"todo-{todo['id']}", cls="todo-item") for todo in todos],
                ds_drop_zone("inbox"),
                cls="drop-zone inbox-zone",
            ),
        ),
        # Additional drop zones
        Div(
            H3("Drop Zones"),
            Div("Active Tasks", ds_drop_zone("active"), cls="drop-zone"),
            Div("Completed Tasks", ds_drop_zone("completed"), cls="drop-zone"),
            cls="zones",
        ),
        # Debug info using ds_json_signals
        Div(
            H3("Drag State"),
            Pre(ds_json_signals(include="^(isDragging|elementId|x|y|dropZone|zone_)"), cls="json-signals"),
            cls="debug",
        ),
        # CSS Styles
        Style("""
            body {
                font-family: system-ui;
                padding: 2rem;
                background: #f5f5f5;
            }
            
            .todo-item {
                background: white;
                padding: 1rem;
                margin: 0.5rem 0;
                border-radius: 8px;
                border: 2px solid #e5e5e5;
                cursor: grab;
                user-select: none;
                transition: border-color 0.2s ease, box-shadow 0.2s ease;
            }
            
            .todo-item:hover {
                border-color: #3b82f6;
                box-shadow: 0 4px 8px rgba(0,0,0,0.1);
            }
            
            .todo-item.is-dragging {
                cursor: grabbing;
                opacity: 0.9;
                z-index: 9999;
                box-shadow: 0 8px 16px rgba(0,0,0,0.2);
                transition: none !important;
            }
            
            .drop-zone {
                min-height: 100px;
                border: 2px dashed #ccc;
                border-radius: 8px;
                padding: 1rem;
                margin: 0.5rem;
                background: #fafafa;
                display: flex;
                align-items: center;
                justify-content: center;
                color: #666;
                font-weight: 500;
            }
            
            .drop-zone.drop-zone-active {
                border-color: #3b82f6;
                background: #eff6ff;
                color: #3b82f6;
            }
            
            .inbox-zone {
                min-height: 200px;
                margin-bottom: 2rem;
                background: white;
                display: block;
                padding: 1rem;
            }
            
            .inbox-zone .todo-item {
                margin: 0.5rem 0;
            }
            
            .zones {
                display: flex;
                gap: 1rem;
                margin: 2rem 0;
            }
            
            .debug {
                background: white;
                padding: 1rem;
                border-radius: 8px;
                margin-top: 2rem;
                border: 1px solid #e5e5e5;
            }
            
            .debug h3 {
                margin-top: 0;
                color: #333;
            }
            
            .json-signals {
                margin: 0;
                padding: 1rem;
                background: #f8f9fa;
                border-radius: 4px;
                font-family: 'SF Mono', Monaco, monospace;
                font-size: 0.85rem;
                line-height: 1.5;
                overflow-x: auto;
                color: #374151;
            }
            
            body.is-drag-active {
                cursor: grabbing;
            }
            
            /* Accessibility styles */
            .sr-only {
                position: absolute;
                width: 1px;
                height: 1px;
                padding: 0;
                margin: -1px;
                overflow: hidden;
                clip: rect(0, 0, 0, 0);
                white-space: nowrap;
                border: 0;
            }
            
            /* Enhanced focus indicators */
            [data-draggable]:focus {
                outline: 3px solid #005fcc;
                outline-offset: 2px;
            }
            
            .keyboard-dragging {
                outline: 3px solid #005fcc;
                outline-offset: 2px;
                box-shadow: 0 0 0 6px rgba(0, 95, 204, 0.2);
            }
            
            /* High contrast support */
            @media (prefers-contrast: high) {
                .drop-zone-active {
                    border-color: #000;
                    background-color: #fff;
                }
                
                .is-dragging {
                    border: 3px solid #000;
                }
            }
            
            /* Reduced motion support */
            @media (prefers-reduced-motion: reduce) {
                .todo-item,
                .drop-zone {
                    transition: none !important;
                    animation: none !important;
                }
            }
            
            /* Touch target sizing */
            [data-draggable] {
                min-height: 44px;
                min-width: 44px;
                touch-action: none;
            }
        """),
        cls="sortable-demo",
    )


if __name__ == "__main__":
    print("=" * 60)
    print("🎯 DRAG HANDLER DEMO")
    print("=" * 60)
    print("📍 Running on: http://localhost:5001")
    print("🎨 Features:")
    print("   • Sortable todo list")
    print("   • Drag and drop between zones")
    print("   • Real-time state tracking")
    print("   • JSON signal debugging")
    print("=" * 60)
    serve(port=5001)
