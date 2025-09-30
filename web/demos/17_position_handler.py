"""Position Handler Demo - Floating UI-powered automatic positioning and collision detection."""

from starhtml import *

app, rt = star_app(
    title="Position Handler Demo",
    hdrs=[
        Script(src="https://cdn.jsdelivr.net/npm/@tailwindcss/browser@4"),
        Style("""
            body { background: white; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; -webkit-font-smoothing: antialiased; }
        """),
        position_handler(),
    ],
    iconify=True,
    compression=False,
)


@rt("/")
def home():
    return Div(
        # Initialize signals for all floating elements (walrus makes them positional)
        (popover_open := Signal("popover_open", False)),
        (file_open := Signal("file_open", False)),
        (tooltip_open := Signal("tooltip_open", False)),
        (context_open := Signal("context_open", False)),
        (cursor_x := Signal("cursor_x", -1000)),
        (cursor_y := Signal("cursor_y", -1000)),
        # Test signals for modifier tests
        (test_placement_open := Signal("test_placement_open", False)),
        (test_offset_open := Signal("test_offset_open", False)),
        (test_flip_open := Signal("test_flip_open", False)),
        (test_strategy_open := Signal("test_strategy_open", False)),
        # Main container
        Div(
            # Header
            Div(
                H1("17", cls="text-8xl font-black text-gray-100 leading-none"),
                H1("Position Handler", cls="text-5xl md:text-6xl font-bold text-black mt-2"),
                P(
                    "Floating UI-powered automatic positioning with collision detection",
                    cls="text-lg text-gray-600 mt-4",
                ),
                cls="mb-16",
            ),
            # === BASIC POPOVER ===
            Div(
                H3("Basic Popover", cls="text-2xl font-bold text-black mb-6"),
                P("Click to open a popover with automatic positioning:", cls="text-gray-600 mb-6"),
                Div(
                    Button(
                        "Open Popover",
                        data_on_click=popover_open.toggle(),
                        id="popoverTrigger",
                        cls="px-4 py-2 bg-black text-white font-medium hover:bg-gray-800 transition-colors",
                    ),
                    Div(
                        H4("Floating Popover", cls="text-lg font-bold text-black mb-3"),
                        P("Positioned with Floating UI!", cls="text-gray-600 mb-3"),
                        Ul(
                            Li("Automatic scroll tracking", cls="text-sm text-gray-700"),
                            Li("Collision detection built-in", cls="text-sm text-gray-700"),
                            Li("Auto-flip when near edges", cls="text-sm text-gray-700"),
                            cls="list-disc list-inside space-y-1",
                        ),
                        data_position=("popoverTrigger", dict(placement="right", flip=True, shift=True)),
                        data_show=popover_open,
                        id="popoverContent",
                        cls="p-4 bg-white border border-gray-200 rounded shadow-lg min-w-[200px]",
                    ),
                ),
                cls="mb-12 p-8 bg-gray-50",
            ),
            # === DROPDOWN MENU ===
            Div(
                H3("Dropdown Menu", cls="text-2xl font-bold text-black mb-6"),
                P("Click the button to see a dropdown menu positioned below:", cls="text-gray-600 mb-6"),
                Div(
                    Button(
                        "File Menu ▼",
                        data_on_click=file_open.toggle(),
                        id="fileButton",
                        cls="px-4 py-2 bg-black text-white font-medium hover:bg-gray-800 transition-colors",
                    ),
                    Div(
                        Div(
                            "New File",
                            data_on_click=f"alert('New File'); {file_open.set(False)}",
                            cls="px-4 py-2 text-gray-700 hover:bg-gray-50 cursor-pointer",
                        ),
                        Div("Open...", cls="px-4 py-2 text-gray-700 hover:bg-gray-50 cursor-pointer"),
                        Div("Save", cls="px-4 py-2 text-gray-700 hover:bg-gray-50 cursor-pointer"),
                        Div(cls="border-t border-gray-100 my-1"),
                        Div("Exit", cls="px-4 py-2 text-gray-700 hover:bg-gray-50 cursor-pointer"),
                        data_show=file_open,
                        data_position=("fileButton", dict(placement="bottom", flip=True, shift=True)),
                        id="fileMenu",
                        cls="bg-white border border-gray-200 rounded shadow-lg min-w-[200px] py-1",
                    ),
                ),
                cls="mb-12 p-8 bg-gray-50",
            ),
            # === TOOLTIPS ===
            Div(
                H3("Tooltips", cls="text-2xl font-bold text-black mb-6"),
                P("Hover over the element below to see a tooltip:", cls="text-gray-600 mb-6"),
                Div(
                    Span(
                        "Hover over me",
                        data_on_mouseenter=tooltip_open.set(True),
                        data_on_mouseleave=tooltip_open.set(False),
                        id="tooltipTrigger",
                        cls="inline-block px-4 py-2 bg-black text-white font-medium cursor-help",
                    ),
                    Div(
                        "This tooltip uses Floating UI!",
                        data_position=("tooltipTrigger", dict(placement="top", offset=10, flip=True, shift=True)),
                        data_show=tooltip_open,
                        id="tooltipContent",
                        cls="px-3 py-1 bg-gray-800 text-white text-sm rounded shadow-lg",
                    ),
                ),
                cls="mb-12 p-8 bg-gray-50",
            ),
            # === CONTEXT MENU ===
            Div(
                H3("Context Menu", cls="text-2xl font-bold text-black mb-6"),
                P("Right-click in the gray area for context menu:", cls="text-gray-600 mb-6"),
                Div(
                    Div(
                        "Right-click in this area",
                        data_on_contextmenu=f"""
                            evt.preventDefault();
                            {cursor_x.set(js("evt.pageX"))};
                            {cursor_y.set(js("evt.pageY"))};
                            {context_open.set(True)};
                            requestAnimationFrame(() => {{
                                const menu = document.getElementById('contextMenu');
                                if (menu) menu.dispatchEvent(new Event('position-update'));
                            }});
                        """,
                        id="contextArea",
                        cls="h-32 bg-gray-100 border-2 border-dashed border-gray-400 rounded flex items-center justify-center cursor-context-menu",
                    ),
                    Div(
                        Div("Cut", cls="px-4 py-2 text-gray-700 hover:bg-gray-50 cursor-pointer"),
                        Div("Copy", cls="px-4 py-2 text-gray-700 hover:bg-gray-50 cursor-pointer"),
                        Div("Paste", cls="px-4 py-2 text-gray-700 hover:bg-gray-50 cursor-pointer"),
                        Div(cls="border-t border-gray-100 my-1"),
                        Div("Delete", cls="px-4 py-2 text-red-600 hover:bg-red-50 cursor-pointer"),
                        data_on_click=f"evt.stopPropagation(); {context_open.set(False)}",
                        data_position=(
                            "contextArea",
                            dict(
                                placement="right-start",
                                offset=5,
                                flip=True,
                                shift=True,
                                cursor_x="$cursor_x",
                                cursor_y="$cursor_y",
                            ),
                        ),
                        data_show=context_open,
                        id="contextMenu",
                        cls="z-[1000] bg-white border border-gray-200 rounded shadow-lg min-w-[150px] py-1",
                    ),
                ),
                cls="mb-12 p-8 bg-gray-50",
            ),
            # === MODIFIER TESTING ===
            Div(
                H3("Modifier Testing", cls="text-2xl font-bold text-black mb-6"),
                P("Test different positioning modifiers:", cls="text-gray-600 mb-6"),
                # Test grid
                Div(
                    # Placement test
                    Div(
                        H3("Placement Test", cls="font-bold mb-2"),
                        Button(
                            "Test bottom-end",
                            data_on_click=test_placement_open.toggle(),
                            id="testPlacementButton",
                            cls="px-3 py-1 bg-black text-white text-sm font-medium hover:bg-gray-800 transition-colors",
                        ),
                        Div(
                            "Should appear at bottom-end of button",
                            data_show=test_placement_open,
                            data_position=("testPlacementButton", dict(placement="bottom-end", flip=True, shift=True)),
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
                            data_on_click=test_offset_open.toggle(),
                            id="testOffsetButton",
                            cls="px-3 py-1 bg-black text-white text-sm font-medium hover:bg-gray-800 transition-colors",
                        ),
                        Div(
                            "Should be 20px away from button",
                            data_show=test_offset_open,
                            data_position=(
                                "testOffsetButton",
                                dict(placement="bottom", offset=20, flip=True, shift=True),
                            ),
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
                            data_on_click=test_flip_open.toggle(),
                            id="testFlipButton",
                            cls="px-3 py-1 bg-black text-white text-sm font-medium hover:bg-gray-800 transition-colors",
                        ),
                        Div(
                            "Should NOT flip even if near edge",
                            data_show=test_flip_open,
                            data_position=("testFlipButton", dict(placement="top", flip=False, shift=True)),
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
                            data_on_click=test_strategy_open.toggle(),
                            id="testStrategyButton",
                            cls="px-3 py-1 bg-black text-white text-sm font-medium hover:bg-gray-800 transition-colors",
                        ),
                        Div(
                            "Should use fixed positioning",
                            data_show=test_strategy_open,
                            data_position=(
                                "testStrategyButton",
                                dict(placement="bottom", strategy="fixed", flip=True, shift=True),
                            ),
                            id="testStrategyMenu",
                            cls="bg-purple-100 border border-purple-400 rounded p-2 text-sm shadow-lg min-w-[150px] max-w-[200px]",
                        ),
                        cls="mb-4",
                    ),
                    cls="grid grid-cols-1 md:grid-cols-2 gap-6",
                ),
                cls="mb-12 p-8 bg-gray-50",
            ),
            # === FEATURES ===
            Div(
                H3("Features", cls="text-2xl font-bold text-black mb-6"),
                Div(
                    Div(
                        H4("Powered by Floating UI", cls="text-lg font-bold text-black mb-4"),
                        Ul(
                            Li("Industry-standard positioning library"),
                            Li("Battle-tested with millions of users"),
                            Li("Handles all edge cases automatically"),
                            Li("53KB built size for complete functionality"),
                            cls="text-sm space-y-2 list-disc list-inside text-gray-700",
                        ),
                    ),
                    Div(
                        H4("Automatic Features", cls="text-lg font-bold text-black mb-4"),
                        Ul(
                            Li("Scroll tracking (no manual calculations!)"),
                            Li("Resize detection"),
                            Li("Collision detection with viewport edges"),
                            Li("Auto-flip when not enough space"),
                            Li("Shift to stay visible"),
                            Li("Hide when anchor off-screen"),
                            cls="text-sm space-y-2 list-disc list-inside text-gray-700",
                        ),
                    ),
                    cls="grid grid-cols-1 lg:grid-cols-2 gap-8",
                ),
                cls="mb-12 p-8 bg-white border border-gray-200",
            ),
            # === API USAGE ===
            Div(
                H3("API Usage", cls="text-2xl font-bold text-black mb-6"),
                Div(
                    H4("Python Code Usage", cls="text-lg font-bold text-black mb-4"),
                    Pre(
                        Code(
                            """# Basic usage
data_position="buttonId"

# With modifiers using tuple format
data_position=("triggerId", dict(
    placement="bottom-start",
    offset=8,
    flip=True,
    shift=True,
    hide=True,
    strategy="fixed"
))""",
                            cls="text-xs",
                        ),
                        cls="bg-gray-100 p-4 rounded overflow-x-auto",
                    ),
                ),
                cls="mb-12 p-8 bg-white border border-gray-200",
            ),
            # Spacer for scrolling
            Div(cls="h-[1000px]"),
        ),
        # Click outside to close floating elements
        data_on_click="""
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
        """,
        # Right-click outside context area closes menu (only prevent default if menu is open)
        data_on_contextmenu="""
            if (!evt.target.closest('#contextArea') && $context_open) {
                evt.preventDefault();
                $context_open = false;
            }
        """,
        cls="max-w-5xl mx-auto px-8 sm:px-12 lg:px-16 py-16 sm:py-20 md:py-24 bg-white min-h-screen",
    )


if __name__ == "__main__":
    print("Position Handler Demo running on http://localhost:5017")
    serve(port=5017)
