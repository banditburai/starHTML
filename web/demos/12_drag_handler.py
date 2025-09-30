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
        Style(
            """body{background:#fff;color:#000;margin:0;padding:0;-webkit-font-smoothing:antialiased;-moz-osx-font-smoothing:grayscale}::selection{background:#000;color:#fff}[data-draggable]{display:flex;align-items:center;padding:1rem;background-color:white;border:1px solid rgb(229 231 235);margin-bottom:0.5rem;border-radius:0.5rem;cursor:move;transition:border-color 0.2s;width:100%}[data-draggable]:hover{border-color:rgb(156 163 175)}[data-draggable].is-dragging{opacity:0.5;cursor:grabbing !important}[data-drop-zone].drop-zone-active{background-color:rgb(239 246 255) !important;border-color:rgb(59 130 246) !important}[data-drop-zone]{display:block !important}[data-drop-zone]:not(:has([data-draggable])) > div:first-child{margin:auto;padding:2rem}[data-drop-zone]:has([data-draggable]) > div:first-child{margin-bottom:1rem}"""
        ),
        # Use walrus operator to assign and include handler in one line
        (todos_drag := drag_handler(signal="todos", mode="sortable")),
    ],
    iconify=True,
    compression=False,
)


@rt("/")
def sortable_todos():
    """Sortable todo list demo - exactly 3 lines of Python as promised."""
    return Div(
        # Header section with large number
        Div(
            H1("12", cls="text-8xl font-black text-gray-100 leading-none"),
            H1("Drag Handler", cls="text-5xl md:text-6xl font-bold text-black mt-2"),
            P("Sortable lists with keyboard navigation and accessibility", cls="text-lg text-gray-600 mt-4"),
            cls="mb-16",
        ),
        # Accessibility instructions for screen readers
        Div(
            "Use space or enter to grab an item. While dragging, use arrow keys to move, "
            "tab to cycle through drop zones, and space or enter to drop. Press escape to cancel.",
            id="drag-instructions",
            cls="sr-only",
        ),
        # Live region for screen reader announcements
        Div(id="drag-status", **{"aria-live": "polite", "aria-atomic": "true"}, cls="sr-only"),
        # Main sortable todo list
        Div(
            H3("Todo List", cls="text-2xl font-bold text-black mb-6"),
            P("Drag items to reorder them or move to different zones", cls="text-gray-600 mb-6"),
            Div(
                *[
                    Div(
                        Icon("material-symbols:drag-indicator", cls="mr-3 text-gray-400"),
                        todo["text"],
                        data_draggable=True,
                        id=f"todo-{todo['id']}",
                        cls="flex items-center p-4 bg-white border border-gray-200 mb-2 rounded-lg hover:border-gray-400 transition-colors cursor-move",
                    )
                    for todo in todos
                ],
                data_drop_zone="inbox",
                cls="min-h-[200px] p-4 bg-gray-50 border-2 border-dashed border-gray-300 rounded-lg",
            ),
            cls="mb-12 p-8 bg-white border border-gray-200",
        ),
        # Additional drop zones
        Div(
            H3("Drop Zones", cls="text-2xl font-bold text-black mb-6"),
            P("Drag todos into these zones to organize them", cls="text-gray-600 mb-6"),
            Div(
                Div(
                    Div(
                        Icon("material-symbols:bolt", cls="text-4xl text-blue-400 mb-2"),
                        "Active Tasks",
                        cls="flex flex-col items-center text-blue-700 font-medium mb-4",
                    ),
                    data_drop_zone="active",
                    cls="min-h-[200px] p-4 bg-blue-50 border-2 border-dashed border-blue-300 rounded-lg",
                ),
                Div(
                    Div(
                        Icon("material-symbols:check-circle", cls="text-4xl text-green-400 mb-2"),
                        "Completed Tasks",
                        cls="flex flex-col items-center text-green-700 font-medium mb-4",
                    ),
                    data_drop_zone="completed",
                    cls="min-h-[200px] p-4 bg-green-50 border-2 border-dashed border-green-300 rounded-lg",
                ),
                cls="grid grid-cols-1 md:grid-cols-2 gap-6",
            ),
            cls="mb-12 p-8 bg-gray-50",
        ),
        # Debug info - display bundled signal values
        Div(
            H3("Drag State", cls="text-2xl font-bold text-black mb-6"),
            P("Real-time drag handler state using bundled signals", cls="text-gray-600 mb-6"),
            Div(
                H4("Signal State:", cls="text-sm font-semibold text-gray-700 mb-2"),
                Pre(
                    data_json_signals=dict(include=regex("^todos_")),
                    cls="p-4 bg-gray-900 text-green-400 rounded-lg font-mono text-xs overflow-x-auto",
                ),
                cls="p-6 bg-gray-50 rounded-lg",
            ),
            cls="mb-12 p-8 bg-white border border-gray-200",
        ),
        cls="max-w-5xl mx-auto px-8 sm:px-12 lg:px-16 py-16 sm:py-20 md:py-24 bg-white min-h-screen",
    )


if __name__ == "__main__":
    print("Drag Handler Demo running on http://localhost:5001")
    serve(port=5001)
