"""Demo showing the Floating UI-powered position handler for anchored elements."""

from starhtml import *
from starhtml.handlers import position_handler

app, rt = star_app(
    title="Position Handler - Floating UI",
    hdrs=[
        Script(src="https://cdn.jsdelivr.net/npm/@tailwindcss/browser@4"),
        position_handler(),  # Load the position handler
    ],
)


@rt("/")
def home():
    return Div(
        # Define all signals at the top level so they're accessible globally
        ds_signals(
            popover_open=False,
            file_open=False,
            tooltip_open=False,
            context_open=False,
            cursor_x=-1000,
            cursor_y=-1000
        ),
        
        # Global click handler for closing menus when clicking outside
        ds_on_click("""
            console.log('[Global Click] Event type:', event.type, 'Button:', event.button);
            console.log('[Global Click] Target:', event.target);
            console.log('[Global Click] Target ID:', event.target.id);
            console.log('[Global Click] Current states - popover:', $popover_open, 'file:', $file_open, 'context:', $context_open);
            
            // Check if context menu exists and is visible
            const contextMenuEl = document.getElementById('contextMenu');
            if (contextMenuEl) {
                const styles = window.getComputedStyle(contextMenuEl);
                console.log('[Global Click] Context menu display:', styles.display);
                console.log('[Global Click] Context menu visibility:', styles.visibility);
            }
            
            // Check if click was on a trigger or inside a menu
            const clickedTrigger = event.target.closest('#popoverTrigger, #fileButton');
            const clickedInsideMenu = event.target.closest('#popoverContent, #fileMenu, #contextMenu');
            
            console.log('[Global Click] Clicked trigger?', !!clickedTrigger);
            console.log('[Global Click] Clicked inside menu?', !!clickedInsideMenu);
            
            // If clicked outside all menus and triggers, close everything
            if (!clickedTrigger && !clickedInsideMenu) {
                console.log('[Global Click] Attempting to close all menus...');
                console.log('[Global Click] Before - context_open:', $context_open);
                $popover_open = false;
                $file_open = false;
                $context_open = false;
                console.log('[Global Click] After - context_open:', $context_open);
                
                // Force a check after a delay
                setTimeout(() => {
                    console.log('[Global Click] Delayed check - context_open:', $context_open);
                    const menu = document.getElementById('contextMenu');
                    if (menu) {
                        console.log('[Global Click] Menu still visible?', window.getComputedStyle(menu).display);
                    }
                }, 100);
            } else {
                console.log('[Global Click] Not closing - clicked on trigger or menu');
            }
        """),
        # Global right-click handler to close context menu when right-clicking outside context area
        ds_on_contextmenu("""
            console.log('[Global Right-click] Target:', event.target);
            console.log('[Global Right-click] In context area?', !!event.target.closest('#contextArea'));
            
            // If right-clicking outside the context area, close the context menu
            if (!event.target.closest('#contextArea')) {
                console.log('[Global Right-click] Closing context menu');
                event.preventDefault();
                $context_open = false;
            }
        """),
        Header(
            H1("🎯 Position Handler with Floating UI", cls="text-3xl font-bold mb-2"),
            P(
                "Automatic positioning, collision detection, and scroll tracking",
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
                        ds_on_click("""
                            $popover_open = !$popover_open;
                        """),
                        id="popoverTrigger",
                        cls="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700",
                    ),
                    
                    Div(
                        H3("Floating Popover", cls="font-bold mb-2"),
                        P("Positioned with Floating UI!", cls="text-sm"),
                        P("✨ Automatic scroll tracking", cls="text-sm text-green-600 mt-2"),
                        P("🎯 Collision detection built-in", cls="text-sm text-blue-600"),
                        P("🔄 Auto-flip when near edges", cls="text-sm text-purple-600"),
                        
                        # Position handler does all the work!
                        ds_position(anchor="popoverTrigger"),
                        ds_show("$popover_open"),
                        id="popoverContent",
                        cls="p-4 bg-white border-2 border-blue-300 rounded-lg shadow-xl min-w-[200px]",
                    ),
                    
                    cls="mb-8",
                ),
                cls="mb-12",
            ),
            
            # Dropdown Menu Example
            Section(
                H2("🔽 Dropdown Menu", cls="text-2xl font-semibold mb-4"),
                Div(
                    Button(
                        "File Menu ▼",
                        ds_on_click("$file_open = !$file_open"),
                        id="fileButton",
                        cls="px-4 py-2 bg-gray-600 text-white rounded hover:bg-gray-700",
                    ),
                    
                    Div(
                        Div("New File", ds_on_click("alert('New File'); $file_open = false"),
                            cls="px-4 py-2 hover:bg-gray-100 cursor-pointer"),
                        Div("Open...", cls="px-4 py-2 hover:bg-gray-100 cursor-pointer"),
                        Div("Save", cls="px-4 py-2 hover:bg-gray-100 cursor-pointer"),
                        Hr(cls="my-1"),
                        Div("Exit", cls="px-4 py-2 hover:bg-gray-100 cursor-pointer"),
                        
                        ds_position(
                            anchor="fileButton",
                            placement="bottom-start",
                            offset=4
                        ),
                        ds_show("$file_open"),
                        id="fileMenu",
                        cls="bg-white border border-gray-300 rounded-lg shadow-xl min-w-[200px] py-1",
                    ),
                    
                    cls="mb-8",
                ),
                cls="mb-12",
            ),
            
            # Tooltip Example
            Section(
                H2("💡 Tooltips", cls="text-2xl font-semibold mb-4"),
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
                        ds_position(
                            anchor="tooltipTrigger",
                            placement="top",
                            offset=10
                        ),
                        ds_show("$tooltip_open"),
                        id="tooltipContent",
                        cls="px-3 py-1 bg-gray-800 text-white text-sm rounded shadow-lg",
                    ),
                    
                    cls="mb-8",
                ),
                cls="mb-12",
            ),
            
            # Context Menu Example
            Section(
                H2("📋 Context Menu", cls="text-2xl font-semibold mb-4"),
                P("Right-click in the gray area. Check console for debug logs.", cls="mb-2 text-muted-foreground"),
                # Debug button to manually test closing
                Button(
                    "Debug: Close Context Menu",
                    ds_on_click("""
                        console.log('[Debug Button] Manually closing context menu');
                        console.log('[Debug Button] Before - context_open:', $context_open);
                        $context_open = false;
                        console.log('[Debug Button] After - context_open:', $context_open);
                    """),
                    cls="mb-4 px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700",
                ),
                Div(
                    Div(
                        "Right-click in this area",
                        ds_on_contextmenu("""
                            event.preventDefault();
                            event.stopPropagation(); // Stop this from bubbling to global handler
                            console.log('[ContextArea Right-click] at:', event.pageX, event.pageY);
                            console.log('[ContextArea Right-click] Current context_open:', $context_open);
                            
                            // Close any existing menu first
                            $context_open = false;
                            
                            // Use pageX/pageY for absolute positioning (scrolls with content)
                            $cursor_x = event.pageX;
                            $cursor_y = event.pageY;
                            
                            // Show the menu at new position
                            setTimeout(() => {
                                console.log('[ContextArea Right-click] Opening menu after delay');
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
                        # Use reactive CSS positioning  
                        ds_on_click("""
                            console.log('[ContextMenu Click] Closing menu');
                            event.stopPropagation();
                            $context_open = false;
                        """),
                        id="contextMenu",
                        cls="bg-white border border-gray-300 rounded-lg shadow-xl min-w-[150px] py-1 absolute z-[1000]",
                        style="position: absolute !important;",
                        data_style_left="$cursor_x + 'px'",
                        data_style_top="$cursor_y + 'px'",
                        data_style_display="$context_open ? 'block' : 'none'",
                        ds_show="$context_open",
                        
                    ),
                    
                    cls="mb-8",
                ),
                cls="mb-12",
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
                            Li("5KB gzipped for complete functionality", cls="mb-2"),
                            cls="list-disc list-inside",
                        ),
                        cls="p-4 bg-blue-50 border border-blue-200 rounded-lg",
                    ),
                    
                    Div(
                        H3("🎯 Automatic Features", cls="font-bold mb-3"),
                        Ul(
                            Li("Scroll tracking (no manual delta calculations!)", cls="mb-2"),
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
            
            # API Example
            Section(
                H2("📝 Clean API", cls="text-2xl font-semibold mb-4"),
                Div(
                    H3("Python API", cls="font-bold mb-2"),
                    Pre(
                        Code("""# Simple usage
ds_position(anchor="buttonId")

# With options
ds_position(
    anchor="triggerId",
    placement="bottom-start",  # Placement options
    offset=8,                   # Distance from anchor
    flip=True,                  # Auto-flip on collision
    shift=True,                 # Slide along edges
    hide=True,                  # Hide when off-screen
    strategy="fixed"            # or "absolute"
)

# Placement options:
# 'top', 'top-start', 'top-end'
# 'bottom', 'bottom-start', 'bottom-end'
# 'left', 'left-start', 'left-end'
# 'right', 'right-start', 'right-end'""",
                            cls="text-xs overflow-x-auto",
                        ),
                        cls="bg-gray-100 p-4 rounded-lg",
                    ),
                    cls="mb-8",
                ),
                
                Div(
                    H3("Comparison", cls="font-bold mb-3"),
                    Pre(
                        Code("""# Before: Manual scroll tracking (20+ lines)
ds_on_scroll(\"\"\"
    if ($popover_open) {
        const deltaY = window.scrollY - $popover_initialScrollY;
        // ... 15+ more lines of manual tracking
    }
\"\"\", throttle="16")

# After: Clean positioning (1 line)
ds_position(anchor="popoverTrigger")""",
                            cls="text-xs overflow-x-auto",
                        ),
                        cls="bg-gray-100 p-4 rounded-lg",
                    ),
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