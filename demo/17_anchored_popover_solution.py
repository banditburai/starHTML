"""Demo showing the enhanced scroll handler with anchored positioning."""

from starhtml import *

app, rt = star_app(
    title="Anchored Popover - Enhanced Solution",
    hdrs=[
        Script(src="https://cdn.jsdelivr.net/npm/@tailwindcss/browser@4"),
        scroll_handler(),
    ],
)


@rt("/")
def home():
    return Div(
        Header(
            H1("✨ Enhanced Solution: Anchored Positioning", cls="text-3xl font-bold mb-2"),
            P(
                "Automatic scroll tracking with the enhanced ds_on_scroll handler",
                cls="text-muted-foreground",
            ),
            cls="text-center py-8 border-b bg-background sticky top-0 z-10",
        ),
        Main(
            Section(
                H2("🎯 Simplified Implementation", cls="text-2xl font-semibold mb-4"),
                P(
                    "The enhanced scroll handler automatically handles positioning:",
                    cls="mb-4 text-muted-foreground",
                ),
                
                # Example with automatic anchored positioning
                Div(
                    Button(
                        "Click to Open Popover",
                        id="popoverTrigger",
                        ds_on_click("""
                            // Just calculate initial position
                            const rect = popoverTrigger.getBoundingClientRect();
                            $popover_top = rect.bottom + 8;
                            $popover_left = rect.left;
                            $popover_open = !$popover_open;
                        """),
                        cls="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700",
                    ),
                    
                    # Popover content
                    Div(
                        H3("Floating Popover", cls="font-bold mb-2"),
                        P("Automatically tracks scroll position!", cls="text-sm"),
                        P("No manual delta tracking needed 🎉", cls="text-sm text-green-600 mt-2 font-semibold"),
                        P(
                            "Current offset: Y=",
                            Span(ds_text("Math.round($popover_top)")),
                            " X=",
                            Span(ds_text("Math.round($popover_left)")),
                            cls="text-xs text-gray-500 mt-2",
                        ),
                        id="popoverContent",
                        ds_show("$popover_open"),
                        ds_style(
                            position="'fixed'",
                            top="$popover_top + 'px'",
                            left="$popover_left + 'px'",
                            zIndex="'100'",
                        ),
                        cls="p-4 bg-white border-2 border-green-300 rounded-lg shadow-xl min-w-[200px]",
                    ),
                    
                    # ENHANCED SCROLL HANDLER - ONE LINE! 🎉
                    ds_on_scroll(
                        "",  # Empty expression for pure anchored mode
                        anchor_to="popoverTrigger",
                        hide_when_offscreen=True,
                        throttle="16"
                    ),
                    
                    ds_signals(
                        popover_open=False,
                        popover_top=0,
                        popover_left=0,
                        # No need for initialScrollY/X anymore!
                    ),
                    cls="mb-8",
                ),
                
                # Code comparison
                Div(
                    H3("✨ New API - Just One Line!", cls="font-bold mb-3 text-green-600"),
                    Pre(
                        Code("""# Python API - Minimal configuration
ds_on_scroll(
    "",  # Empty expression for pure anchored mode
    anchor_to="popoverTrigger",  # Element to anchor to
    hide_when_offscreen=True,     # Auto-hide when scrolled out
    throttle="16"                 # Optional throttling
)

# That's it! The handler automatically:
# ✅ Detects signal prefix from trigger ID
# ✅ Tracks scroll deltas internally  
# ✅ Updates _top and _left signals
# ✅ Checks trigger visibility
# ✅ Hides when off-screen
# ✅ Manages all scroll state

# No more manual tracking of:
# ❌ ${signal}_initialScrollY
# ❌ ${signal}_initialScrollX  
# ❌ Delta calculations
# ❌ Visibility checks
# ❌ 20+ lines of boilerplate!""",
                            cls="text-xs overflow-x-auto",
                        ),
                        cls="bg-green-50 p-4 rounded-lg border border-green-200",
                    ),
                    cls="mb-8",
                ),
                
                cls="mb-12",
            ),
            
            # Multiple examples showing the simplification
            Section(
                H2("🚀 Multiple Elements - Same Simplicity", cls="text-2xl font-semibold mb-4"),
                Div(
                    # Select dropdown - SIMPLIFIED
                    Div(
                        Button(
                            "Select Option ▼",
                            id="selectTrigger",
                            ds_on_click("""
                                const rect = selectTrigger.getBoundingClientRect();
                                $select_top = rect.bottom + 4;
                                $select_left = rect.left;
                                $select_open = !$select_open;
                            """),
                            cls="px-4 py-2 bg-gray-600 text-white rounded hover:bg-gray-700",
                        ),
                        Div(
                            Div("Option 1", cls="p-2 hover:bg-gray-100 cursor-pointer"),
                            Div("Option 2", cls="p-2 hover:bg-gray-100 cursor-pointer"),
                            Div("Option 3", cls="p-2 hover:bg-gray-100 cursor-pointer"),
                            id="selectContent",
                            ds_show("$select_open"),
                            ds_style(
                                position="'fixed'",
                                top="$select_top + 'px'",
                                left="$select_left + 'px'",
                                zIndex="'100'",
                            ),
                            cls="bg-white border border-gray-300 rounded shadow-lg min-w-[150px]",
                        ),
                        # ONE LINE instead of 20+!
                        ds_on_scroll("", anchor_to="selectTrigger", throttle="16"),
                        ds_signals(
                            select_open=False,
                            select_top=0,
                            select_left=0,
                        ),
                        cls="inline-block mr-4",
                    ),
                    
                    # Tooltip - SIMPLIFIED
                    Div(
                        Button(
                            "Hover for Tooltip",
                            id="tooltipTrigger",
                            ds_on_mouseenter("""
                                const rect = tooltipTrigger.getBoundingClientRect();
                                $tooltip_top = rect.top - 40;
                                $tooltip_left = rect.left + rect.width / 2 - 75;
                                $tooltip_open = true;
                            """),
                            ds_on_mouseleave("$tooltip_open = false"),
                            cls="px-4 py-2 bg-green-600 text-white rounded hover:bg-green-700",
                        ),
                        Div(
                            "Enhanced tooltip!",
                            id="tooltipContent",
                            ds_show("$tooltip_open"),
                            ds_style(
                                position="'fixed'",
                                top="$tooltip_top + 'px'",
                                left="$tooltip_left + 'px'",
                                zIndex="'100'",
                            ),
                            cls="px-3 py-1 bg-gray-800 text-white text-sm rounded shadow-lg",
                        ),
                        # ONE LINE!
                        ds_on_scroll("", anchor_to="tooltipTrigger"),
                        ds_signals(
                            tooltip_open=False,
                            tooltip_top=0,
                            tooltip_left=0,
                        ),
                        cls="inline-block",
                    ),
                    cls="mb-8",
                ),
                P(
                    "Each element now just needs ONE line of scroll handling! 🎉",
                    cls="text-green-600 font-semibold text-lg",
                ),
                cls="mb-12",
            ),
            
            # Advanced options
            Section(
                H2("⚙️ Advanced Options", cls="text-2xl font-semibold mb-4"),
                Div(
                    H3("Custom Hide Actions", cls="font-bold mb-3"),
                    Pre(
                        Code("""# Use native popover API
ds_on_scroll(
    "",
    anchor_to="myTrigger",
    hide_action="myContent.hidePopover()"
)

# Custom cleanup logic
ds_on_scroll(
    "",
    anchor_to="hoverTrigger", 
    hide_action="clearTimeout(window.hoverTimer); $hover_open = false"
)

# Explicit signal prefix (when auto-detection isn't enough)
ds_on_scroll(
    "",
    anchor_to="complexElement",
    signal_prefix="modal",
    hide_when_offscreen=False  # Don't auto-hide
)

# Combine with custom scroll logic
ds_on_scroll(
    "$customCounter++",  # Your custom expression still works!
    anchor_to="trigger",
    throttle="50"
)""",
                            cls="text-xs overflow-x-auto",
                        ),
                        cls="bg-gray-100 p-4 rounded-lg",
                    ),
                    cls="mb-8",
                ),
                
                # Benefits summary
                Div(
                    H3("✅ Benefits of Enhanced Solution", cls="font-bold mb-3 text-green-600"),
                    Ul(
                        Li("90% less code for floating elements", cls="mb-2"),
                        Li("Automatic scroll delta tracking", cls="mb-2"),
                        Li("Built-in visibility checking with smart throttling", cls="mb-2"),
                        Li("Auto-detection of signal prefixes", cls="mb-2"),
                        Li("Consistent behavior across all components", cls="mb-2"),
                        Li("Performance optimizations built-in", cls="mb-2"),
                        Li("Backwards compatible with existing code", cls="mb-2"),
                        cls="list-disc list-inside space-y-1",
                    ),
                    cls="p-4 bg-green-50 border border-green-200 rounded-lg mb-8",
                ),
                
                cls="mb-12",
            ),
            
            # Migration guide
            Section(
                H2("📋 Migration Guide", cls="text-2xl font-semibold mb-4"),
                Div(
                    H3("Before (20+ lines)", cls="font-bold mb-2 text-red-600"),
                    Pre(
                        Code("""ds_on_scroll(\"\"\"
    if ($popover_open) {
        const deltaY = window.scrollY - $popover_initialScrollY;
        const deltaX = window.scrollX - $popover_initialScrollX;
        $popover_top = $popover_top - deltaY;
        $popover_left = $popover_left - deltaX;
        $popover_initialScrollY = window.scrollY;
        $popover_initialScrollX = window.scrollX;
        
        if (Math.floor(window.scrollY / 100) !== 
            Math.floor((window.scrollY - deltaY) / 100)) {
            const tr = popoverTrigger.getBoundingClientRect();
            const triggerVisible = tr.bottom > 0 && 
                                 tr.top < window.innerHeight;
            if (!triggerVisible) {
                $popover_open = false;
            }
        }
    }
\"\"\", throttle="16")""",
                            cls="text-xs overflow-x-auto",
                        ),
                        cls="bg-red-50 p-3 rounded-lg border border-red-200 mb-4",
                    ),
                    
                    H3("After (1 line)", cls="font-bold mb-2 text-green-600"),
                    Pre(
                        Code("""ds_on_scroll("", anchor_to="popoverTrigger", throttle="16")""",
                            cls="text-xs",
                        ),
                        cls="bg-green-50 p-3 rounded-lg border border-green-200",
                    ),
                    cls="mb-8",
                ),
                
                P(
                    "That's a 95% reduction in code! 🚀",
                    cls="text-xl font-bold text-center text-green-600",
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
    print("Anchored Popover Solution Demo running on http://localhost:5001")
    serve(port=5001)