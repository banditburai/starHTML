"""Position Handler Demo - Floating UI-powered automatic positioning and collision detection."""

from starhtml import *

app, rt = star_app(
    title="Position Handler Demo",
    hdrs=[
        Script(src="https://cdn.jsdelivr.net/npm/@tailwindcss/browser@4"),
        position_handler(),
    ],
)


@rt("/")
def home():
    return Div(
        # Initialize signals for all floating elements
        ds_signals(
            popover_open=False,
            file_open=False,
            tooltip_open=False,
            context_open=False,
            cursor_x=-1000,
            cursor_y=-1000,
        ),
        # Click outside to close floating elements
        ds_on_click("""
            const clickedTrigger = evt.target.closest('#popoverTrigger, #fileButton, #testPlacementButton, #testOffsetButton, #testFlipButton, #testStrategyButton');
            const clickedInsideMenu = evt.target.closest('#popoverContent, #fileMenu, #contextMenu, #testPlacementMenu, #testOffsetMenu, #testFlipMenu, #testStrategyMenu');
            
            if (!clickedTrigger && !clickedInsideMenu) {
                $popover_open = false;
                $file_open = false;
                $context_open = false;
                $test_placement_open = false;
                $test_offset_open = false;
                $test_flip_open = false;
                $test_strategy_open = false;
            }
        """),
        # Right-click outside context area closes menu (only prevent default if menu is open)
        ds_on_contextmenu("""
            if (!evt.target.closest('#contextArea') && $context_open) {
                evt.preventDefault();
                $context_open = false;
            }
        """),
        # Page Header
        Header(
            H1("🎯 Position Handler Demo", cls="text-3xl font-bold mb-2"),
            P(
                "Floating UI-powered automatic positioning with collision detection",
                cls="text-muted-foreground",
            ),
            cls="text-center py-8 border-b bg-background sticky top-0 z-10",
        ),
        Main(
            # Basic Popover Example
            Section(
                H2("📌 Basic Popover", cls="text-2xl font-semibold mb-4"),
                P(
                    "Click to open a popover with automatic positioning:",
                    cls="mb-4 text-muted-foreground",
                ),
                Div(
                    Button(
                        "Open Popover",
                        ds_on_click("$popover_open = !$popover_open"),
                        id="popoverTrigger",
                        cls="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700",
                    ),
                    Div(
                        H3("Floating Popover", cls="font-bold mb-2"),
                        P("Positioned with Floating UI!", cls="text-sm"),
                        P("✨ Automatic scroll tracking", cls="text-sm text-green-600 mt-2"),
                        P("🎯 Collision detection built-in", cls="text-sm text-blue-600"),
                        P("🔄 Auto-flip when near edges", cls="text-sm text-purple-600"),
                        ds_position(anchor="popoverTrigger"),
                        ds_show("$popover_open"),
                        id="popoverContent",
                        cls="p-4 bg-white border-2 border-blue-300 rounded-lg shadow-xl min-w-[200px]",
                    ),
                    cls="mb-16 py-8",
                ),
                cls="mb-20",
            ),
            # Dropdown Menu Example
            Section(
                H2("🔽 Dropdown Menu", cls="text-2xl font-semibold mb-4"),
                P("Click the button to see a dropdown menu positioned below:", cls="mb-4 text-muted-foreground"),
                Div(
                    Button(
                        "File Menu ▼",
                        ds_on_click("""
                            console.log('File button clicked, current state:', $file_open);
                            $file_open = !$file_open;
                            console.log('File button new state:', $file_open);
                            
                            // Trigger position update after show/hide
                            if ($file_open) {
                                setTimeout(() => {
                                    const menu = document.getElementById('fileMenu');
                                    menu.dispatchEvent(new Event('position-update'));
                                }, 10);
                            }
                        """),
                        id="fileButton",
                        cls="px-4 py-2 bg-gray-600 text-white rounded hover:bg-gray-700",
                    ),
                    Div(
                        Div(
                            "New File",
                            ds_on_click("alert('New File'); $file_open = false"),
                            cls="px-4 py-2 hover:bg-gray-100 cursor-pointer",
                        ),
                        Div("Open...", cls="px-4 py-2 hover:bg-gray-100 cursor-pointer"),
                        Div("Save", cls="px-4 py-2 hover:bg-gray-100 cursor-pointer"),
                        Hr(cls="my-1"),
                        Div("Exit", cls="px-4 py-2 hover:bg-gray-100 cursor-pointer"),
                        ds_show("$file_open"),
                        ds_position(anchor="fileButton"),
                        id="fileMenu",
                        cls="bg-white border border-gray-300 rounded-lg shadow-xl min-w-[200px] py-1",
                    ),
                    cls="mb-16 py-4",
                ),
                cls="mb-20",
            ),
            # Tooltip Example
            Section(
                H2("💡 Tooltips", cls="text-2xl font-semibold mb-4"),
                P("Hover over the element below to see a tooltip:", cls="mb-4 text-muted-foreground"),
                Div(
                    Span(
                        "Hover over me",
                        ds_on_mouseenter("$tooltip_open = true"),
                        ds_on_mouseleave("$tooltip_open = false"),
                        id="tooltipTrigger",
                        cls="inline-block px-4 py-2 bg-purple-600 text-white rounded cursor-help",
                    ),
                    Div(
                        "This tooltip uses Floating UI!",
                        ds_position(anchor="tooltipTrigger", placement="top", offset=10),
                        ds_show("$tooltip_open"),
                        id="tooltipContent",
                        cls="px-3 py-1 bg-gray-800 text-white text-sm rounded shadow-lg",
                    ),
                    cls="mb-8",
                ),
                cls="mb-20",
            ),
            # Context Menu Example
            Section(
                H2("📋 Context Menu", cls="text-2xl font-semibold mb-4"),
                P("Right-click in the gray area for context menu:", cls="mb-4 text-muted-foreground"),
                Div(
                    Div(
                        "Right-click in this area",
                        ds_on_contextmenu("""
                            evt.preventDefault();
                            evt.stopPropagation();
                            
                            $context_open = false;
                            $cursor_x = evt.pageX;
                            $cursor_y = evt.pageY;
                            
                            setTimeout(() => {
                                $context_open = true;
                            }, 10);
                        """),
                        id="contextArea",
                        cls="h-32 bg-gray-100 border-2 border-dashed border-gray-400 rounded flex items-center justify-center cursor-context-menu",
                    ),
                    Div(
                        Div("Cut", cls="px-4 py-2 hover:bg-gray-100 cursor-pointer"),
                        Div("Copy", cls="px-4 py-2 hover:bg-gray-100 cursor-pointer"),
                        Div("Paste", cls="px-4 py-2 hover:bg-gray-100 cursor-pointer"),
                        Hr(cls="my-1"),
                        Div("Delete", cls="px-4 py-2 hover:bg-red-50 text-red-600 cursor-pointer"),
                        ds_on_click("evt.stopPropagation(); $context_open = false"),
                        id="contextMenu",
                        cls="bg-white border border-gray-300 rounded-lg shadow-xl min-w-[150px] py-1 absolute z-[1000]",
                        style="position: absolute !important;",
                        data_style_left="$cursor_x + 'px'",
                        data_style_top="$cursor_y + 'px'",
                        data_style_display="$context_open ? 'block' : 'none'",
                    ),
                    cls="mb-16 py-8",
                ),
                cls="mb-20",
            ),
            # Modifier Testing Section
            Section(
                H2("🧪 Modifier Testing", cls="text-2xl font-semibold mb-4"),
                P(
                    "Test different positioning modifiers to ensure they work correctly:",
                    cls="mb-4 text-muted-foreground",
                ),
                # Test signals for modifier tests
                ds_signals(
                    test_placement_open=False,
                    test_offset_open=False,
                    test_flip_open=False,
                    test_strategy_open=False,
                ),
                # Test grid
                Div(
                    # Placement test
                    Div(
                        H3("Placement Test", cls="font-bold mb-2"),
                        Button(
                            "Test bottom-end",
                            ds_on_click("$test_placement_open = !$test_placement_open"),
                            id="testPlacementButton",
                            cls="px-3 py-1 bg-green-600 text-white text-sm rounded",
                        ),
                        Div(
                            "Should appear at bottom-end of button",
                            ds_show("$test_placement_open"),
                            ds_position(anchor="testPlacementButton", placement="bottom-end"),
                            id="testPlacementMenu",
                            cls="bg-yellow-100 border border-yellow-400 rounded p-2 text-sm shadow-lg min-w-[150px] max-w-[200px]",
                        ),
                        cls="mb-4",
                    ),
                    # Offset test
                    Div(
                        H3("Offset Test", cls="font-bold mb-2"),
                        Button(
                            "Test offset=20",
                            ds_on_click("$test_offset_open = !$test_offset_open"),
                            id="testOffsetButton",
                            cls="px-3 py-1 bg-orange-600 text-white text-sm rounded",
                        ),
                        Div(
                            "Should be 20px away from button",
                            ds_show("$test_offset_open"),
                            ds_position(anchor="testOffsetButton", offset=20),
                            id="testOffsetMenu",
                            cls="bg-orange-100 border border-orange-400 rounded p-2 text-sm shadow-lg min-w-[150px] max-w-[200px]",
                        ),
                        cls="mb-4",
                    ),
                    # Flip test
                    Div(
                        H3("Flip Test", cls="font-bold mb-2"),
                        Button(
                            "Test flip=False",
                            ds_on_click("$test_flip_open = !$test_flip_open"),
                            id="testFlipButton",
                            cls="px-3 py-1 bg-red-600 text-white text-sm rounded",
                        ),
                        Div(
                            "Should NOT flip even if near edge",
                            ds_show("$test_flip_open"),
                            ds_position(anchor="testFlipButton", placement="top", flip=False),
                            id="testFlipMenu",
                            cls="bg-red-100 border border-red-400 rounded p-2 text-sm shadow-lg min-w-[150px] max-w-[200px]",
                        ),
                        cls="mb-4",
                    ),
                    # Strategy test
                    Div(
                        H3("Strategy Test", cls="font-bold mb-2"),
                        Button(
                            "Test strategy=fixed",
                            ds_on_click("$test_strategy_open = !$test_strategy_open"),
                            id="testStrategyButton",
                            cls="px-3 py-1 bg-purple-600 text-white text-sm rounded",
                        ),
                        Div(
                            "Should use fixed positioning",
                            ds_show("$test_strategy_open"),
                            ds_position(anchor="testStrategyButton", strategy="fixed"),
                            id="testStrategyMenu",
                            cls="bg-purple-100 border border-purple-400 rounded p-2 text-sm shadow-lg min-w-[150px] max-w-[200px]",
                        ),
                        cls="mb-4",
                    ),
                    cls="grid grid-cols-1 md:grid-cols-2 gap-6",
                ),
                cls="mb-20",
            ),
            # Features Summary
            Section(
                H2("✨ Features", cls="text-2xl font-semibold mb-4"),
                Div(
                    Div(
                        H3("🚀 Powered by Floating UI", cls="font-bold mb-3"),
                        Ul(
                            Li("Industry-standard positioning library", cls="mb-2"),
                            Li("Battle-tested with millions of users", cls="mb-2"),
                            Li("Handles all edge cases automatically", cls="mb-2"),
                            Li("53KB built size for complete functionality", cls="mb-2"),
                            cls="list-disc list-inside",
                        ),
                        cls="p-4 bg-blue-50 border border-blue-200 rounded-lg",
                    ),
                    Div(
                        H3("🎯 Automatic Features", cls="font-bold mb-3"),
                        Ul(
                            Li("Scroll tracking (no manual calculations!)", cls="mb-2"),
                            Li("Resize detection", cls="mb-2"),
                            Li("Collision detection with viewport edges", cls="mb-2"),
                            Li("Auto-flip when not enough space", cls="mb-2"),
                            Li("Shift to stay visible", cls="mb-2"),
                            Li("Hide when anchor off-screen", cls="mb-2"),
                            cls="list-disc list-inside",
                        ),
                        cls="p-4 bg-green-50 border border-green-200 rounded-lg",
                    ),
                    cls="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8",
                ),
                cls="mb-12",
            ),
            # Code Examples
            Section(
                H2("📝 API Usage", cls="text-2xl font-semibold mb-4"),
                Div(
                    H3("Python Code", cls="font-bold mb-2"),
                    Pre(
                        Code(
                            """# Basic usage
ds_position(anchor="buttonId")

# Advanced options
ds_position(
    anchor="triggerId",
    placement="bottom-start",
    offset=8,
    flip=True,
    shift=True,
    hide=True,
    strategy="fixed"
)""",
                            cls="text-xs overflow-x-auto",
                        ),
                        cls="bg-gray-100 p-4 rounded-lg",
                    ),
                    cls="mb-8",
                ),
                cls="mb-12",
            ),
            # Spacer for scrolling
            Div(cls="h-[1000px]"),
            cls="container mx-auto px-4 py-8 max-w-4xl",
        ),
        cls="min-h-screen bg-background text-foreground",
    )


if __name__ == "__main__":
    print("Position Handler Demo running on http://localhost:5001")
    serve(port=5001)
