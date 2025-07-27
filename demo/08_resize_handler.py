"""
Comprehensive demo showcasing the resize handler capabilities.

This demo uses the custom resize handler with proper Datastar signal integration.
Available variables in ds_on_resize expressions:
  width, height, windowWidth, windowHeight, aspectRatio, breakpoints, isMobile, isTablet, isDesktop, currentBreakpoint
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from starhtml import *
from starhtml.handlers import resize_handler
from starhtml.xtend import Script

app, rt = star_app(
    title="Resize Handler Demo",
    hdrs=[
        Script(src="https://cdn.jsdelivr.net/npm/@tailwindcss/browser@4"),
        resize_handler(),  # Use our custom resize handler
    ],
)

# Global counter for dynamic boxes
box_counter = 0


@rt("/")
def home():
    return Div(
        # Page Header
        Header(
            H1("📏 Resize Handler Demo", cls="text-3xl font-bold mb-2"),
            P("Demonstrating data-on-resize functionality with ResizeObserver", cls="text-muted-foreground"),
            cls="text-center py-8 border-b",
        ),
        # Main Content
        Main(
            # Basic Resize Detection
            Section(
                H2("Basic Resize Detection", cls="text-2xl font-semibold mb-4"),
                P("Resize the boxes below to see real-time dimension updates:", cls="mb-4 text-muted-foreground"),
                Div(
                    Div(
                        H3("Resizable Box 1", cls="font-medium mb-2"),
                        P("Width: ", Span(ds_text="$box1Width"), "px", cls="text-sm"),
                        P("Height: ", Span(ds_text="$box1Height"), "px", cls="text-sm"),
                        P("💡 Drag the resize handle in the bottom-right corner", cls="text-xs text-gray-600 mt-2"),
                        ds_on_resize="$box1Width = width; $box1Height = height;",
                        ds_signals={"box1Width": 0, "box1Height": 0},
                        cls="p-4 border-2 border-solid border-blue-400 bg-blue-50 overflow-auto min-h-32 min-w-48",
                        style="resize: both; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);",
                    ),
                    Div(
                        H3("Resizable Box 2", cls="font-medium mb-2"),
                        P("Width: ", Span(ds_text="$box2Width"), "px", cls="text-sm"),
                        P("Height: ", Span(ds_text="$box2Height"), "px", cls="text-sm"),
                        P("💡 Drag the resize handle in the bottom-right corner", cls="text-xs text-gray-600 mt-2"),
                        ds_on_resize="$box2Width = width; $box2Height = height;",
                        ds_signals={"box2Width": 0, "box2Height": 0},
                        cls="p-4 border-2 border-solid border-green-400 bg-green-50 overflow-auto min-h-32 min-w-48",
                        style="resize: both; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);",
                    ),
                    cls="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8",
                ),
                cls="mb-12",
            ),
            # Responsive Breakpoint Demo
            Section(
                H2("Responsive Breakpoint Detection", cls="text-2xl font-semibold mb-4"),
                P(
                    "This container changes its layout based on its own width (container queries simulation):",
                    cls="mb-4 text-muted-foreground",
                ),
                Div(
                    H3("Responsive Container", cls="font-medium mb-4"),
                    Div(
                        Div("Item 1", cls="p-4 bg-purple-100 border border-purple-300 rounded"),
                        Div("Item 2", cls="p-4 bg-purple-100 border border-purple-300 rounded"),
                        Div("Item 3", cls="p-4 bg-purple-100 border border-purple-300 rounded"),
                        Div("Item 4", cls="p-4 bg-purple-100 border border-purple-300 rounded"),
                        ds_attr_class="$gridClass",
                    ),
                    P("Current layout: ", Span(ds_text="$layoutText"), cls="text-sm text-muted-foreground mt-4"),
                    P("💡 Drag the right edge to change container width", cls="text-xs text-gray-600 mt-2"),
                    ds_on_resize="""
                        $width = width;
                        $layoutText = width < 301 ? '1 column (narrow)' : width < 501 ? '2 columns (medium)' : '4 columns (wide)';
                        $gridClass = width < 301 ? 'gap-4 grid grid-cols-1' : width < 501 ? 'gap-4 grid grid-cols-2' : 'gap-4 grid grid-cols-4';
                    """,
                    ds_signals={"width": 0, "layoutText": "4 columns (wide)", "gridClass": "gap-4 grid grid-cols-4"},
                    cls="p-6 border-2 border-solid border-purple-400 bg-purple-50 overflow-auto min-h-64",
                    style="resize: horizontal; min-width: 200px; width: 100%; max-width: 100%; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);",
                ),
                cls="mb-12",
            ),
            # Throttling and Debouncing Demo
            Section(
                H2("Throttling and Debouncing", cls="text-2xl font-semibold mb-4"),
                P("Different timing strategies for performance optimization:", cls="mb-4 text-muted-foreground"),
                Div(
                    Div(
                        H3("Throttle (50ms)", cls="font-medium mb-2"),
                        P("Updates: ", Span(ds_text="$throttleCount"), cls="text-sm font-mono"),
                        P("💡 Drag corner to resize - updates every 50ms", cls="text-xs text-gray-600 mt-2"),
                        ds_on_resize__throttle_50ms="$throttleCount++;",
                        ds_signals={"throttleCount": 0},
                        cls="p-4 border-2 border-solid border-red-400 bg-red-50 overflow-auto min-h-32 min-w-48",
                        style="resize: both; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);",
                    ),
                    Div(
                        H3("Debounce (150ms)", cls="font-medium mb-2"),
                        P("Updates: ", Span(ds_text="$debounceCount"), cls="text-sm font-mono"),
                        P("💡 Drag corner to resize - updates after 150ms pause", cls="text-xs text-gray-600 mt-2"),
                        ds_on_resize__debounce_150ms="$debounceCount++;",
                        ds_signals={"debounceCount": 0},
                        cls="p-4 border-2 border-solid border-yellow-400 bg-yellow-50 overflow-auto min-h-32 min-w-48",
                        style="resize: both; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);",
                    ),
                    Div(
                        H3("Throttle (500ms)", cls="font-medium mb-2"),
                        P("Updates: ", Span(ds_text="$slowThrottleCount"), cls="text-sm font-mono"),
                        P("💡 Drag corner to resize - updates every 500ms", cls="text-xs text-gray-600 mt-2"),
                        ds_on_resize__throttle_500ms="$slowThrottleCount++;",
                        ds_signals={"slowThrottleCount": 0},
                        cls="p-4 border-2 border-solid border-blue-400 bg-blue-50 overflow-auto min-h-32 min-w-48",
                        style="resize: both; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);",
                    ),
                    cls="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8",
                ),
                cls="mb-12",
            ),
            # Window vs Element Dimensions
            Section(
                H2("Window vs Element Dimensions", cls="text-2xl font-semibold mb-4"),
                P("Access both element and window dimensions for responsive design:", cls="mb-4 text-muted-foreground"),
                Div(
                    H3("Dimension Reporter", cls="font-medium mb-4"),
                    Div(
                        P("Element Width: ", Span(ds_text="$elWidth"), "px", cls="text-sm"),
                        P("Element Height: ", Span(ds_text="$elHeight"), "px", cls="text-sm"),
                        P("Window Width: ", Span(ds_text="$winWidth"), "px", cls="text-sm"),
                        P("Window Height: ", Span(ds_text="$winHeight"), "px", cls="text-sm"),
                        P(
                            "Element vs Window: ",
                            Span(ds_text="$sizeRatio"),
                            "% of window width",
                            cls="text-sm font-medium",
                        ),
                        cls="space-y-2",
                    ),
                    P("💡 Drag corners to resize this container", cls="text-xs text-gray-600 mt-2"),
                    ds_on_resize="""
                        $elWidth = width;
                        $elHeight = height;
                        $winWidth = windowWidth;
                        $winHeight = windowHeight;
                        $sizeRatio = Math.round((width / windowWidth) * 100);
                    """,
                    ds_signals={"elWidth": 0, "elHeight": 0, "winWidth": 0, "winHeight": 0, "sizeRatio": 0},
                    cls="p-6 border-2 border-solid border-indigo-400 bg-indigo-50 overflow-auto min-h-32 min-w-48",
                    style="resize: both; min-width: 300px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);",
                ),
                cls="mb-12",
            ),
            # Dynamic Content Demo
            Section(
                H2("Dynamic Content Addition", cls="text-2xl font-semibold mb-4"),
                P("New elements automatically get resize detection:", cls="mb-4 text-muted-foreground"),
                Div(
                    Button(
                        "Add Resizable Box",
                        ds_on_click="@get('/add-box')",
                        cls="mb-4 px-4 py-2 bg-teal-600 text-white rounded hover:bg-teal-700",
                    ),
                    # Dynamic boxes container
                    Div(id="dynamic-boxes", cls="space-y-4"),
                    cls="mb-8",
                ),
                cls="mb-12",
            ),
            # Performance Information
            Section(
                H2("Performance Information", cls="text-2xl font-semibold mb-4"),
                Div(
                    Div(
                        H3("🚀 Optimizations", cls="font-medium mb-2"),
                        Ul(
                            Li("Single shared ResizeObserver for all elements"),
                            Li("WeakMap for memory-efficient element tracking"),
                            Li("Automatic cleanup when elements are removed"),
                            Li("Configurable throttling and debouncing"),
                            Li("Rounded dimensions to avoid float precision issues"),
                            cls="text-sm space-y-1 list-disc list-inside",
                        ),
                        cls="p-4 bg-green-50 border border-green-200 rounded",
                    ),
                    Div(
                        H3("📊 Usage Patterns", cls="font-medium mb-2"),
                        Ul(
                            Li('ds_on_resize="code" - Default behavior'),
                            Li('ds_on_resize__throttle_50ms="code" - Throttle (50ms)'),
                            Li('ds_on_resize__debounce_150ms="code" - Debounce (150ms)'),
                            Li("Variables: $el, width, height, windowWidth, windowHeight"),
                            Li("Automatic execution on element creation"),
                            Li("Works with dynamically added elements"),
                            cls="text-sm space-y-1 list-disc list-inside",
                        ),
                        cls="p-4 bg-blue-50 border border-blue-200 rounded",
                    ),
                    cls="grid grid-cols-1 md:grid-cols-2 gap-6",
                ),
                cls="mb-12",
            ),
            cls="container mx-auto px-4 py-8 max-w-6xl",
        ),
        # Footer
        Footer(
            P(
                "Resize Handler Demo - Powered by StarHTML ResizeObserver",
                cls="text-center text-sm text-muted-foreground py-4",
            ),
            cls="border-t",
        ),
        # All keyword arguments at the end
        cls="min-h-screen bg-background text-foreground",
    )


@rt("/add-box")
@sse
def add_box(req):
    global box_counter
    box_counter += 1
    box_id = box_counter

    # Yield the HTML element to be appended
    yield elements(
        Div(
            H4(f"Dynamic Box {box_id}", cls="font-medium mb-2"),
            P(
                "Size: ",
                Span(ds_text=f"$dynamicWidth{box_id}"),
                "x",
                Span(ds_text=f"$dynamicHeight{box_id}"),
                "px",
                cls="text-sm",
            ),
            cls="p-4 border-2 border-dashed border-teal-300 bg-teal-50 resize overflow-auto min-h-32 min-w-48 mb-4",
            style="resize: both;",
            ds_on_resize=f"$dynamicWidth{box_id} = width; $dynamicHeight{box_id} = height;",
            ds_signals={f"dynamicWidth{box_id}": 0, f"dynamicHeight{box_id}": 0},
        ),
        "#dynamic-boxes",
        "append",
    )


if __name__ == "__main__":
    print("Resize Handler Demo running on http://localhost:5010")
    serve(port=5010)
