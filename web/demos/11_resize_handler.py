"""
Comprehensive demo showcasing the resize handler capabilities.

This demo uses the custom resize handler with proper Datastar signal integration.
Available variables in data_resize expressions (flattened like scroll):
  resize_width, resize_height, resize_window_width, resize_window_height, resize_aspect_ratio, resize_current_breakpoint, etc.
"""

from starhtml import *

app, rt = star_app(
    title="Resize Handler Demo",
    hdrs=[
        Script(src="https://cdn.jsdelivr.net/npm/@tailwindcss/browser@4"),
        Style(
            """body{background:#fff;color:#000;margin:0;padding:0;-webkit-font-smoothing:antialiased;-moz-osx-font-smoothing:grayscale}::selection{background:#000;color:#fff}"""
        ),
        resize_handler(),
    ],
    iconify=True,
    compression=False,
)

# Global counter for dynamic boxes
box_counter = 0


@rt("/")
def home():
    return Div(
        # Header section with large number
        Div(
            H1("11", cls="text-8xl font-black text-gray-100 leading-none"),
            H1("Resize Handler", cls="text-5xl md:text-6xl font-bold text-black mt-2"),
            P("Track window and element resize events with ResizeObserver", cls="text-lg text-gray-600 mt-4"),
            cls="mb-16",
        ),
        # Main Content
        Div(
            # Basic Resize Detection
            Div(
                H3("Basic Resize Detection", cls="text-2xl font-bold text-black mb-6"),
                P("Resize the boxes below to see real-time dimension updates:", cls="mb-6 text-gray-600"),
                Div(
                    Div(
                        # Define signals inline using walrus operator
                        (box1_width := Signal("box1_width", 0)),
                        (box1_height := Signal("box1_height", 0)),
                        H3("Resizable Box 1", cls="font-medium mb-2"),
                        P("Width: ", Span(data_text=box1_width), "px", cls="text-sm"),
                        P("Height: ", Span(data_text=box1_height), "px", cls="text-sm"),
                        P("💡 Drag the resize handle in the bottom-right corner", cls="text-xs text-gray-600 mt-2"),
                        data_resize="$box1_width = $resize_width; $box1_height = $resize_height;",
                        cls="p-4 border-2 border-solid border-blue-400 bg-blue-50 overflow-auto min-h-32 min-w-48",
                        style="resize: both; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);",
                    ),
                    Div(
                        # Define signals inline using walrus operator
                        (box2_width := Signal("box2_width", 0)),
                        (box2_height := Signal("box2_height", 0)),
                        H3("Resizable Box 2", cls="font-medium mb-2"),
                        P("Width: ", Span(data_text=box2_width), "px", cls="text-sm"),
                        P("Height: ", Span(data_text=box2_height), "px", cls="text-sm"),
                        P("💡 Drag the resize handle in the bottom-right corner", cls="text-xs text-gray-600 mt-2"),
                        data_resize="$box2_width = $resize_width; $box2_height = $resize_height;",
                        cls="p-4 border-2 border-solid border-green-400 bg-green-50 overflow-auto min-h-32 min-w-48",
                        style="resize: both; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);",
                    ),
                    cls="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8",
                ),
                cls="mb-12 p-8 bg-white border border-gray-200",
            ),
            # Responsive Breakpoint Demo
            Div(
                H3("Responsive Breakpoint Detection", cls="text-2xl font-bold text-black mb-6"),
                P(
                    "This container changes its layout based on its own width (container queries simulation):",
                    cls="mb-4 text-muted-foreground",
                ),
                Div(
                    # Local signals for responsive container
                    (container_width := Signal("container_width", 0)),
                    (layout_text := Signal("layout_text", "4 columns (wide)")),
                    (grid_class := Signal("grid_class", "gap-4 grid grid-cols-4")),
                    H3("Responsive Container", cls="font-medium mb-4"),
                    Div(
                        Div("Item 1", cls="p-4 bg-purple-100 border border-purple-300 rounded"),
                        Div("Item 2", cls="p-4 bg-purple-100 border border-purple-300 rounded"),
                        Div("Item 3", cls="p-4 bg-purple-100 border border-purple-300 rounded"),
                        Div("Item 4", cls="p-4 bg-purple-100 border border-purple-300 rounded"),
                        data_attr_class=grid_class,
                    ),
                    P("Current layout: ", Span(data_text=layout_text), cls="text-sm text-muted-foreground mt-4"),
                    P("💡 Drag the right edge to change container width", cls="text-xs text-gray-600 mt-2"),
                    data_resize="""
                        $container_width = $resize_width;
                        $layout_text = $resize_width < 301 ? '1 column (narrow)' : $resize_width < 501 ? '2 columns (medium)' : '4 columns (wide)';
                        $grid_class = $resize_width < 301 ? 'gap-4 grid grid-cols-1' : $resize_width < 501 ? 'gap-4 grid grid-cols-2' : 'gap-4 grid grid-cols-4';
                    """,
                    cls="p-6 border-2 border-solid border-purple-400 bg-purple-50 overflow-auto min-h-64",
                    style="resize: horizontal; min-width: 200px; width: 100%; max-width: 100%; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);",
                ),
                cls="mb-12 p-8 bg-gray-50",
            ),
            # Throttling and Debouncing Demo
            Div(
                H3("Throttling and Debouncing", cls="text-2xl font-bold text-black mb-6"),
                P("Different timing strategies for performance optimization:", cls="mb-6 text-gray-600"),
                Div(
                    Div(
                        (throttle_count := Signal("throttle_count", 0)),
                        H3("Throttle (50ms)", cls="font-medium mb-2"),
                        P("Updates: ", Span(data_text=throttle_count), cls="text-sm font-mono"),
                        P("💡 Drag corner to resize - updates every 50ms", cls="text-xs text-gray-600 mt-2"),
                        data_resize=(throttle_count.add(1), dict(throttle=50)),
                        cls="p-4 border-2 border-solid border-red-400 bg-red-50 overflow-auto min-h-32 min-w-48",
                        style="resize: both; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);",
                    ),
                    Div(
                        (debounce_count := Signal("debounce_count", 0)),
                        H3("Debounce (150ms)", cls="font-medium mb-2"),
                        P("Updates: ", Span(data_text=debounce_count), cls="text-sm font-mono"),
                        P("💡 Drag corner to resize - updates after 150ms pause", cls="text-xs text-gray-600 mt-2"),
                        data_resize=(debounce_count.add(1), dict(debounce=150)),
                        cls="p-4 border-2 border-solid border-yellow-400 bg-yellow-50 overflow-auto min-h-32 min-w-48",
                        style="resize: both; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);",
                    ),
                    Div(
                        (slow_throttle_count := Signal("slow_throttle_count", 0)),
                        H3("Throttle (500ms)", cls="font-medium mb-2"),
                        P("Updates: ", Span(data_text=slow_throttle_count), cls="text-sm font-mono"),
                        P("💡 Drag corner to resize - updates every 500ms", cls="text-xs text-gray-600 mt-2"),
                        data_resize=(slow_throttle_count.add(1), dict(throttle=500)),
                        cls="p-4 border-2 border-solid border-blue-400 bg-blue-50 overflow-auto min-h-32 min-w-48",
                        style="resize: both; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);",
                    ),
                    cls="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8",
                ),
                cls="mb-12 p-8 bg-white border border-gray-200",
            ),
            # Window vs Element Dimensions
            Div(
                H3("Window vs Element Dimensions", cls="text-2xl font-bold text-black mb-6"),
                P("Access both element and window dimensions for responsive design:", cls="mb-6 text-gray-600"),
                Div(
                    # Local signals for dimension reporter
                    (el_width := Signal("el_width", 0)),
                    (el_height := Signal("el_height", 0)),
                    (win_width := Signal("win_width", 0)),
                    (win_height := Signal("win_height", 0)),
                    (size_ratio := Signal("size_ratio", 0)),
                    H3("Dimension Reporter", cls="font-medium mb-4"),
                    Div(
                        P("Element Width: ", Span(data_text=el_width), "px", cls="text-sm"),
                        P("Element Height: ", Span(data_text=el_height), "px", cls="text-sm"),
                        P("Window Width: ", Span(data_text=win_width), "px", cls="text-sm"),
                        P("Window Height: ", Span(data_text=win_height), "px", cls="text-sm"),
                        P(
                            "Element vs Window: ",
                            Span(data_text=size_ratio),
                            "% of window width",
                            cls="text-sm font-medium",
                        ),
                        cls="space-y-2",
                    ),
                    P("💡 Drag corners to resize this container", cls="text-xs text-gray-600 mt-2"),
                    data_resize="""
                        $el_width = $resize_width;
                        $el_height = $resize_height;
                        $win_width = $resize_window_width;
                        $win_height = $resize_window_height;
                        $size_ratio = Math.round(($resize_width / $resize_window_width) * 100);
                    """,
                    cls="p-6 border-2 border-solid border-indigo-400 bg-indigo-50 overflow-auto min-h-32 min-w-48",
                    style="resize: both; min-width: 300px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);",
                ),
                cls="mb-12 p-8 bg-gray-50",
            ),
            # Dynamic Content Demo
            Div(
                H3("Dynamic Content Addition", cls="text-2xl font-bold text-black mb-6"),
                P("New elements automatically get resize detection:", cls="mb-6 text-gray-600"),
                Div(
                    Button(
                        "Add Resizable Box",
                        data_on_click=get("add-box"),
                        cls="mb-4 px-4 py-2 bg-black text-white font-medium hover:bg-gray-800 transition-colors",
                    ),
                    # Dynamic boxes container
                    Div(id="dynamic-boxes", cls="space-y-4"),
                    cls="mb-8",
                ),
                cls="mb-12 p-8 bg-white border border-gray-200",
            ),
            # Performance Information
            Div(
                H3("Performance Information", cls="text-2xl font-bold text-black mb-6"),
                Div(
                    Div(
                        H4("Implementation Details", cls="font-semibold mb-4"),
                        Ul(
                            Li("Single shared ResizeObserver for all elements"),
                            Li("WeakMap for memory-efficient element tracking"),
                            Li("Automatic cleanup when elements are removed"),
                            Li("Configurable throttling (default 16ms) and debouncing"),
                            Li("Rounded dimensions to avoid float precision issues"),
                            Li("RAF-based throttling for smooth animations"),
                            cls="text-sm space-y-2 list-disc list-inside text-gray-700",
                        ),
                        cls="p-6 bg-green-50 border border-green-200 rounded-lg",
                    ),
                    Div(
                        H4("API Usage", cls="font-semibold mb-4"),
                        Ul(
                            Li(
                                Code(
                                    'data_resize="$width = $resize_width; $height = $resize_height"',
                                    cls="text-xs bg-gray-100 px-1 py-0.5 rounded",
                                ),
                                " - Direct assignment",
                            ),
                            Li(
                                Code(
                                    "data_resize=(signal.add(1), dict(throttle=50))",
                                    cls="text-xs bg-gray-100 px-1 py-0.5 rounded",
                                ),
                                " - With throttling",
                            ),
                            Li(
                                Code(
                                    "data_resize=(signal.add(1), dict(debounce=150))",
                                    cls="text-xs bg-gray-100 px-1 py-0.5 rounded",
                                ),
                                " - With debouncing",
                            ),
                            Li(
                                "Available variables: ",
                                Code(
                                    "resize_width, resize_height, resize_window_width, resize_window_height",
                                    cls="text-xs bg-gray-100 px-1 py-0.5 rounded",
                                ),
                            ),
                            Li(
                                "Also: ",
                                Code(
                                    "resize_aspect_ratio, resize_current_breakpoint, resize_is_mobile/tablet/desktop",
                                    cls="text-xs bg-gray-100 px-1 py-0.5 rounded",
                                ),
                            ),
                            Li(
                                "Breakpoints: ",
                                Code(
                                    "resize_xs, resize_sm, resize_md, resize_lg, resize_xl",
                                    cls="text-xs bg-gray-100 px-1 py-0.5 rounded",
                                ),
                            ),
                            cls="text-sm space-y-2 list-disc list-inside text-gray-700",
                        ),
                        cls="p-6 bg-blue-50 border border-blue-200 rounded-lg",
                    ),
                    cls="grid grid-cols-1 md:grid-cols-2 gap-6",
                ),
                cls="mb-12",
            ),
        ),
        cls="max-w-5xl mx-auto px-8 sm:px-12 lg:px-16 py-16 sm:py-20 md:py-24 bg-white min-h-screen",
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
            (width_sig := Signal(f"dynamic_width_{box_id}", 0)),
            (height_sig := Signal(f"dynamic_height_{box_id}", 0)),
            H4(f"Dynamic Box {box_id}", cls="font-medium mb-2"),
            P(
                "Size: ",
                Span(data_text=width_sig),
                "x",
                Span(data_text=height_sig),
                "px",
                cls="text-sm",
            ),
            data_resize=f"$dynamic_width_{box_id} = $resize_width; $dynamic_height_{box_id} = $resize_height;",
            cls="p-4 border-2 border-dashed border-teal-300 bg-teal-50 resize overflow-auto min-h-32 min-w-48 mb-4",
            style="resize: both;",
        ),
        "#dynamic-boxes",
        "append",
    )


if __name__ == "__main__":
    print("Resize Handler Demo running on http://localhost:5001")
    serve(port=5001)
