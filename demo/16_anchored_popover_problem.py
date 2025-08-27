"""Demo showing the current problem: manual scroll tracking for floating UI elements."""

from starhtml import *

app, rt = star_app(
    title="Anchored Popover - Current Problem",
    hdrs=[
        Script(src="https://cdn.jsdelivr.net/npm/@tailwindcss/browser@4"),
        scroll_handler(),
    ],
)


@rt("/")
def home():
    return Div(
        Header(
            H1("Current Problem: Manual Scroll Tracking", cls="text-3xl font-bold mb-2"),
            P(
                "This demo shows the boilerplate code needed for floating elements",
                cls="text-muted-foreground",
            ),
            cls="text-center py-8 border-b bg-background sticky top-0 z-10",
        ),
        Main(
            Section(
                H2("Manual Implementation Required", cls="text-2xl font-semibold mb-4"),
                P(
                    "Each floating element needs 20+ lines of scroll handling code:",
                    cls="mb-4 text-muted-foreground",
                ),
                
                # Example with manual scroll tracking
                Div(
                    Button(
                        "Click to Open Popover",
                        id="popoverTrigger",
                        ds_on_click("""
                            // Calculate position relative to trigger
                            const rect = popoverTrigger.getBoundingClientRect();
                            $popover_top = rect.bottom + 8;
                            $popover_left = rect.left;
                            
                            // Store initial scroll position for delta tracking
                            $popover_initialScrollY = window.scrollY;
                            $popover_initialScrollX = window.scrollX;
                            
                            // Toggle popover
                            $popover_open = !$popover_open;
                        """),
                        cls="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700",
                    ),
                    
                    # Popover content
                    Div(
                        H3("Floating Popover", cls="font-bold mb-2"),
                        P("This popover tracks scroll position manually", cls="text-sm"),
                        P("Scroll the page to see it follow the trigger", cls="text-sm text-gray-600 mt-2"),
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
                        cls="p-4 bg-white border-2 border-blue-300 rounded-lg shadow-xl min-w-[200px]",
                    ),
                    
                    # Manual scroll tracking - THIS IS THE PROBLEM WE'RE SOLVING
                    ds_on_scroll("""
                        if ($popover_open) {
                            // Calculate scroll deltas
                            const deltaY = window.scrollY - $popover_initialScrollY;
                            const deltaX = window.scrollX - $popover_initialScrollX;
                            
                            // Apply inverse delta to maintain position relative to trigger
                            $popover_top = $popover_top - deltaY;
                            $popover_left = $popover_left - deltaX;
                            
                            // Update initial scroll position for next frame
                            $popover_initialScrollY = window.scrollY;
                            $popover_initialScrollX = window.scrollX;
                            
                            // Check if trigger is still visible (throttled for performance)
                            if (Math.floor(window.scrollY / 100) !== Math.floor((window.scrollY - deltaY) / 100)) {
                                const tr = popoverTrigger.getBoundingClientRect();
                                const triggerVisible = tr.bottom > 0 && tr.top < window.innerHeight && 
                                                     tr.right > 0 && tr.left < window.innerWidth;
                                if (!triggerVisible) {
                                    $popover_open = false;
                                }
                            }
                        }
                    """, throttle="16"),
                    
                    ds_signals(
                        popover_open=False,
                        popover_top=0,
                        popover_left=0,
                        popover_initialScrollY=0,
                        popover_initialScrollX=0,
                    ),
                    cls="mb-8",
                ),
                
                # Code example showing the problem
                Div(
                    H3("Required Boilerplate Code", cls="font-bold mb-3"),
                    Pre(
                        Code("""// For EVERY floating element, you need:

// 1. Initial position calculation
ds_on_click(\"""
    const rect = trigger.getBoundingClientRect();
    $signal_top = rect.bottom + 8;
    $signal_left = rect.left;
    $signal_initialScrollY = window.scrollY;
    $signal_initialScrollX = window.scrollX;
    $signal_open = true;
\""")

// 2. Scroll handler with delta tracking
ds_on_scroll(\"""
    if ($signal_open) {
        const deltaY = window.scrollY - $signal_initialScrollY;
        const deltaX = window.scrollX - $signal_initialScrollX;
        $signal_top = $signal_top - deltaY;
        $signal_left = $signal_left - deltaX;
        $signal_initialScrollY = window.scrollY;
        $signal_initialScrollX = window.scrollX;
        
        // Visibility check (throttled)
        if (Math.floor(window.scrollY / 100) !== 
            Math.floor((window.scrollY - deltaY) / 100)) {
            const tr = trigger.getBoundingClientRect();
            const triggerVisible = tr.bottom > 0 && 
                                 tr.top < window.innerHeight && 
                                 tr.right > 0 && 
                                 tr.left < window.innerWidth;
            if (!triggerVisible) {
                $signal_open = false;
            }
        }
    }
\""", throttle="16")

// 3. Multiple signals for tracking
ds_signals(
    signal_open=False,
    signal_top=0,
    signal_left=0,
    signal_initialScrollY=0,
    signal_initialScrollX=0,
)""",
                            cls="text-xs overflow-x-auto",
                        ),
                        cls="bg-gray-100 p-4 rounded-lg",
                    ),
                    cls="mb-8",
                ),
                
                # Problem summary
                Div(
                    H3("⚠️ Problems with Current Approach", cls="font-bold mb-3 text-orange-600"),
                    Ul(
                        Li("20+ lines of boilerplate per floating element", cls="mb-2"),
                        Li("Easy to forget visibility checks", cls="mb-2"),
                        Li("Performance issues if not properly throttled", cls="mb-2"),
                        Li("Duplicate code across components", cls="mb-2"),
                        Li("Manual signal management", cls="mb-2"),
                        cls="list-disc list-inside space-y-1",
                    ),
                    cls="p-4 bg-orange-50 border border-orange-200 rounded-lg mb-8",
                ),
                
                cls="mb-12",
            ),
            
            # Multiple examples to show the repetition
            Section(
                H2("Multiple Floating Elements = More Boilerplate", cls="text-2xl font-semibold mb-4"),
                Div(
                    # Select dropdown
                    Div(
                        Button(
                            "Select Option ▼",
                            id="selectTrigger",
                            ds_on_click("""
                                const rect = selectTrigger.getBoundingClientRect();
                                $select_top = rect.bottom + 4;
                                $select_left = rect.left;
                                $select_initialScrollY = window.scrollY;
                                $select_initialScrollX = window.scrollX;
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
                        ds_on_scroll("""
                            if ($select_open) {
                                const deltaY = window.scrollY - $select_initialScrollY;
                                const deltaX = window.scrollX - $select_initialScrollX;
                                $select_top = $select_top - deltaY;
                                $select_left = $select_left - deltaX;
                                $select_initialScrollY = window.scrollY;
                                $select_initialScrollX = window.scrollX;
                                
                                if (Math.floor(window.scrollY / 100) !== Math.floor((window.scrollY - deltaY) / 100)) {
                                    const tr = selectTrigger.getBoundingClientRect();
                                    if (tr.bottom < 0 || tr.top > window.innerHeight) {
                                        $select_open = false;
                                    }
                                }
                            }
                        """, throttle="16"),
                        ds_signals(
                            select_open=False,
                            select_top=0,
                            select_left=0,
                            select_initialScrollY=0,
                            select_initialScrollX=0,
                        ),
                        cls="inline-block mr-4",
                    ),
                    
                    # Tooltip
                    Div(
                        Button(
                            "Hover for Tooltip",
                            id="tooltipTrigger",
                            ds_on_mouseenter("""
                                const rect = tooltipTrigger.getBoundingClientRect();
                                $tooltip_top = rect.top - 40;
                                $tooltip_left = rect.left + rect.width / 2 - 75;
                                $tooltip_initialScrollY = window.scrollY;
                                $tooltip_initialScrollX = window.scrollX;
                                $tooltip_open = true;
                            """),
                            ds_on_mouseleave("$tooltip_open = false"),
                            cls="px-4 py-2 bg-green-600 text-white rounded hover:bg-green-700",
                        ),
                        Div(
                            "This is a tooltip",
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
                        ds_on_scroll("""
                            if ($tooltip_open) {
                                const deltaY = window.scrollY - $tooltip_initialScrollY;
                                const deltaX = window.scrollX - $tooltip_initialScrollX;
                                $tooltip_top = $tooltip_top - deltaY;
                                $tooltip_left = $tooltip_left - deltaX;
                                $tooltip_initialScrollY = window.scrollY;
                                $tooltip_initialScrollX = window.scrollX;
                                
                                if (Math.floor(window.scrollY / 100) !== Math.floor((window.scrollY - deltaY) / 100)) {
                                    const tr = tooltipTrigger.getBoundingClientRect();
                                    if (tr.bottom < 0 || tr.top > window.innerHeight) {
                                        $tooltip_open = false;
                                    }
                                }
                            }
                        """, throttle="16"),
                        ds_signals(
                            tooltip_open=False,
                            tooltip_top=0,
                            tooltip_left=0,
                            tooltip_initialScrollY=0,
                            tooltip_initialScrollX=0,
                        ),
                        cls="inline-block",
                    ),
                    cls="mb-8",
                ),
                P(
                    "Each floating element requires the same boilerplate scroll tracking code!",
                    cls="text-red-600 font-semibold",
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
    print("Anchored Popover Problem Demo running on http://localhost:5001")
    serve(port=5001)