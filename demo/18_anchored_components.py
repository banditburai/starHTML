"""Comprehensive demo of various anchored UI components using the enhanced scroll handler."""

from starhtml import *

app, rt = star_app(
    title="Anchored Components Gallery",
    hdrs=[
        Script(src="https://cdn.jsdelivr.net/npm/@tailwindcss/browser@4"),
        scroll_handler(),
    ],
)


@rt("/")
def home():
    return Div(
        Header(
            H1("🎯 Anchored Components Gallery", cls="text-3xl font-bold mb-2"),
            P(
                "Various floating UI patterns with the enhanced scroll handler",
                cls="text-muted-foreground",
            ),
            cls="text-center py-8 border-b bg-background sticky top-0 z-10",
        ),
        Main(
            # Context Menu Example
            Section(
                H2("📋 Context Menu", cls="text-2xl font-semibold mb-4"),
                P("Right-click to show context menu", cls="mb-4 text-muted-foreground"),
                Div(
                    Div(
                        "Right-click anywhere in this box",
                        id="contextArea",
                        ds_on_contextmenu("""
                            event.preventDefault();
                            const rect = contextArea.getBoundingClientRect();
                            $context_top = event.clientY;
                            $context_left = event.clientX;
                            $context_open = true;
                        """),
                        ds_on_click("$context_open = false"),
                        cls="h-32 bg-gray-100 border-2 border-dashed border-gray-400 rounded flex items-center justify-center cursor-context-menu",
                    ),
                    
                    Div(
                        Div("Cut", cls="px-4 py-2 hover:bg-gray-100 cursor-pointer"),
                        Div("Copy", cls="px-4 py-2 hover:bg-gray-100 cursor-pointer"),
                        Div("Paste", cls="px-4 py-2 hover:bg-gray-100 cursor-pointer"),
                        Hr(cls="my-1"),
                        Div("Delete", cls="px-4 py-2 hover:bg-red-50 text-red-600 cursor-pointer"),
                        id="contextMenu",
                        ds_show("$context_open"),
                        ds_style(
                            position="'fixed'",
                            top="$context_top + 'px'",
                            left="$context_left + 'px'",
                            zIndex="'200'",
                        ),
                        cls="bg-white border border-gray-300 rounded-lg shadow-xl min-w-[150px] py-1",
                    ),
                    
                    ds_on_scroll("", anchor_to="contextArea", signal_prefix="context"),
                    ds_signals(context_open=False, context_top=0, context_left=0),
                    cls="mb-8",
                ),
                cls="mb-12",
            ),
            
            # Dropdown Menu Example
            Section(
                H2("🔽 Dropdown Menu", cls="text-2xl font-semibold mb-4"),
                Div(
                    Div(
                        Button(
                            Span("File", cls="mr-2"),
                            Span("▼", cls="text-xs"),
                            id="fileTrigger",
                            ds_on_click("""
                                const rect = fileTrigger.getBoundingClientRect();
                                $file_top = rect.bottom;
                                $file_left = rect.left;
                                $file_open = !$file_open;
                            """),
                            cls="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700",
                        ),
                        Div(
                            Div("New File", cls="px-4 py-2 hover:bg-blue-50 cursor-pointer", ds_on_click("$file_open = false; alert('New File')")),
                            Div("Open...", cls="px-4 py-2 hover:bg-blue-50 cursor-pointer"),
                            Div("Save", cls="px-4 py-2 hover:bg-blue-50 cursor-pointer"),
                            Hr(cls="my-1"),
                            Div("Exit", cls="px-4 py-2 hover:bg-blue-50 cursor-pointer"),
                            id="fileMenu",
                            ds_show("$file_open"),
                            ds_style(
                                position="'fixed'",
                                top="$file_top + 'px'",
                                left="$file_left + 'px'",
                                zIndex="'150'",
                            ),
                            cls="bg-white border border-gray-300 rounded-lg shadow-xl min-w-[200px] py-1",
                        ),
                        ds_on_scroll("", anchor_to="fileTrigger", signal_prefix="file", hide_when_offscreen=True),
                        ds_signals(file_open=False, file_top=0, file_left=0),
                        cls="inline-block mr-4",
                    ),
                    
                    Div(
                        Button(
                            Span("Edit", cls="mr-2"),
                            Span("▼", cls="text-xs"),
                            id="editTrigger",
                            ds_on_click("""
                                const rect = editTrigger.getBoundingClientRect();
                                $edit_top = rect.bottom;
                                $edit_left = rect.left;
                                $edit_open = !$edit_open;
                            """),
                            cls="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700",
                        ),
                        Div(
                            Div("Undo", cls="px-4 py-2 hover:bg-blue-50 cursor-pointer"),
                            Div("Redo", cls="px-4 py-2 hover:bg-blue-50 cursor-pointer"),
                            Hr(cls="my-1"),
                            Div("Cut", cls="px-4 py-2 hover:bg-blue-50 cursor-pointer"),
                            Div("Copy", cls="px-4 py-2 hover:bg-blue-50 cursor-pointer"),
                            Div("Paste", cls="px-4 py-2 hover:bg-blue-50 cursor-pointer"),
                            id="editMenu",
                            ds_show("$edit_open"),
                            ds_style(
                                position="'fixed'",
                                top="$edit_top + 'px'",
                                left="$edit_left + 'px'",
                                zIndex="'150'",
                            ),
                            cls="bg-white border border-gray-300 rounded-lg shadow-xl min-w-[200px] py-1",
                        ),
                        ds_on_scroll("", anchor_to="editTrigger", signal_prefix="edit", hide_when_offscreen=True),
                        ds_signals(edit_open=False, edit_top=0, edit_left=0),
                        cls="inline-block",
                    ),
                    cls="mb-8",
                ),
                cls="mb-12",
            ),
            
            # Autocomplete Example
            Section(
                H2("🔍 Autocomplete", cls="text-2xl font-semibold mb-4"),
                Div(
                    Input(
                        type="text",
                        placeholder="Type to search...",
                        id="searchInput",
                        ds_on_input("""
                            const val = searchInput.value.toLowerCase();
                            if (val.length > 0) {
                                const rect = searchInput.getBoundingClientRect();
                                $autocomplete_top = rect.bottom + 4;
                                $autocomplete_left = rect.left;
                                $autocomplete_open = true;
                                
                                // Simple filter logic
                                const items = ['Apple', 'Banana', 'Cherry', 'Date', 'Elderberry'];
                                $filtered_items = items.filter(i => i.toLowerCase().includes(val));
                            } else {
                                $autocomplete_open = false;
                            }
                        """),
                        ds_on_blur("setTimeout(() => $autocomplete_open = false, 200)"),
                        cls="px-4 py-2 border border-gray-300 rounded w-64",
                    ),
                    
                    Div(
                        Div("Apple", ds_show("$filtered_items && $filtered_items.includes('Apple')"), cls="px-4 py-2 hover:bg-gray-100 cursor-pointer"),
                        Div("Banana", ds_show("$filtered_items && $filtered_items.includes('Banana')"), cls="px-4 py-2 hover:bg-gray-100 cursor-pointer"),
                        Div("Cherry", ds_show("$filtered_items && $filtered_items.includes('Cherry')"), cls="px-4 py-2 hover:bg-gray-100 cursor-pointer"),
                        Div("Date", ds_show("$filtered_items && $filtered_items.includes('Date')"), cls="px-4 py-2 hover:bg-gray-100 cursor-pointer"),
                        Div("Elderberry", ds_show("$filtered_items && $filtered_items.includes('Elderberry')"), cls="px-4 py-2 hover:bg-gray-100 cursor-pointer"),
                        id="autocompleteMenu",
                        ds_show("$autocomplete_open"),
                        ds_style(
                            position="'fixed'",
                            top="$autocomplete_top + 'px'",
                            left="$autocomplete_left + 'px'",
                            zIndex="'100'",
                            width="'256px'",
                        ),
                        cls="bg-white border border-gray-300 rounded-lg shadow-xl max-h-48 overflow-y-auto",
                    ),
                    
                    ds_on_scroll("", anchor_to="searchInput", signal_prefix="autocomplete"),
                    ds_signals(
                        autocomplete_open=False,
                        autocomplete_top=0,
                        autocomplete_left=0,
                        filtered_items=[],
                    ),
                    cls="mb-8",
                ),
                cls="mb-12",
            ),
            
            # Hover Card Example
            Section(
                H2("🃏 Hover Cards", cls="text-2xl font-semibold mb-4"),
                P("Hover over the cards to see details", cls="mb-4 text-muted-foreground"),
                Div(
                    # Card 1
                    Div(
                        Div(
                            H3("Product A", cls="font-bold"),
                            P("$99.99", cls="text-lg text-green-600"),
                            id="card1Trigger",
                            ds_on_mouseenter("""
                                const rect = card1Trigger.getBoundingClientRect();
                                $card1_top = rect.top;
                                $card1_left = rect.right + 10;
                                $card1_open = true;
                                window.card1Timer = setTimeout(() => $card1_open = true, 100);
                            """),
                            ds_on_mouseleave("""
                                clearTimeout(window.card1Timer);
                                window.card1HideTimer = setTimeout(() => $card1_open = false, 300);
                            """),
                            cls="p-4 bg-white border border-gray-200 rounded shadow hover:shadow-lg transition-shadow cursor-pointer",
                        ),
                        Div(
                            H4("Product Details", cls="font-bold mb-2"),
                            P("High-quality product with premium features", cls="text-sm mb-2"),
                            Ul(
                                Li("Feature 1", cls="text-sm"),
                                Li("Feature 2", cls="text-sm"),
                                Li("Feature 3", cls="text-sm"),
                                cls="list-disc list-inside",
                            ),
                            id="card1Content",
                            ds_show("$card1_open"),
                            ds_style(
                                position="'fixed'",
                                top="$card1_top + 'px'",
                                left="$card1_left + 'px'",
                                zIndex="'100'",
                            ),
                            ds_on_mouseenter("clearTimeout(window.card1HideTimer); $card1_open = true"),
                            ds_on_mouseleave("$card1_open = false"),
                            cls="p-4 bg-white border-2 border-blue-300 rounded-lg shadow-xl w-64",
                        ),
                        ds_on_scroll(
                            "",
                            anchor_to="card1Trigger",
                            signal_prefix="card1",
                            hide_action="clearTimeout(window.card1Timer); clearTimeout(window.card1HideTimer); $card1_open = false"
                        ),
                        ds_signals(card1_open=False, card1_top=0, card1_left=0),
                        cls="inline-block mr-4",
                    ),
                    
                    # Card 2
                    Div(
                        Div(
                            H3("Product B", cls="font-bold"),
                            P("$149.99", cls="text-lg text-green-600"),
                            id="card2Trigger",
                            ds_on_mouseenter("""
                                const rect = card2Trigger.getBoundingClientRect();
                                $card2_top = rect.top;
                                $card2_left = rect.right + 10;
                                $card2_open = true;
                            """),
                            ds_on_mouseleave("$card2_open = false"),
                            cls="p-4 bg-white border border-gray-200 rounded shadow hover:shadow-lg transition-shadow cursor-pointer",
                        ),
                        Div(
                            H4("Product Details", cls="font-bold mb-2"),
                            P("Professional-grade solution for enterprises", cls="text-sm mb-2"),
                            Ul(
                                Li("Advanced Feature A", cls="text-sm"),
                                Li("Advanced Feature B", cls="text-sm"),
                                Li("Premium Support", cls="text-sm"),
                                cls="list-disc list-inside",
                            ),
                            id="card2Content",
                            ds_show("$card2_open"),
                            ds_style(
                                position="'fixed'",
                                top="$card2_top + 'px'",
                                left="$card2_left + 'px'",
                                zIndex="'100'",
                            ),
                            cls="p-4 bg-white border-2 border-purple-300 rounded-lg shadow-xl w-64",
                        ),
                        ds_on_scroll("", anchor_to="card2Trigger", signal_prefix="card2"),
                        ds_signals(card2_open=False, card2_top=0, card2_left=0),
                        cls="inline-block",
                    ),
                    cls="mb-8",
                ),
                cls="mb-12",
            ),
            
            # Info Banner
            Div(
                H3("💡 Implementation Notes", cls="font-bold mb-3"),
                Ul(
                    Li("All components use the enhanced ds_on_scroll handler", cls="mb-2"),
                    Li("Automatic scroll delta tracking keeps elements anchored", cls="mb-2"),
                    Li("Smart visibility checking prevents off-screen elements", cls="mb-2"),
                    Li("Each component requires minimal configuration", cls="mb-2"),
                    Li("Performance optimized with throttling and batching", cls="mb-2"),
                    cls="list-disc list-inside",
                ),
                cls="p-4 bg-blue-50 border border-blue-200 rounded-lg mb-8",
            ),
            
            # Code Examples
            Section(
                H2("📝 Code Patterns", cls="text-2xl font-semibold mb-4"),
                Div(
                    H3("Basic Pattern", cls="font-bold mb-2"),
                    Pre(
                        Code("""# 1. Set initial position on trigger
ds_on_click(\"\"\"
    const rect = trigger.getBoundingClientRect();
    $signal_top = rect.bottom + 8;
    $signal_left = rect.left;
    $signal_open = true;
\"\"\")

# 2. Add anchored scroll handler (one line!)
ds_on_scroll("", anchor_to="triggerId", signal_prefix="signal")

# 3. Define signals (no scroll tracking needed!)
ds_signals(signal_open=False, signal_top=0, signal_left=0)""",
                            cls="text-xs overflow-x-auto",
                        ),
                        cls="bg-gray-100 p-4 rounded-lg",
                    ),
                    cls="mb-8",
                ),
                cls="mb-12",
            ),
            
            # Spacer for scrolling
            Div(cls="h-[800px]"),
            
            cls="container mx-auto px-4 py-8 max-w-4xl",
        ),
        cls="min-h-screen bg-background text-foreground",
    )


if __name__ == "__main__":
    print("Anchored Components Gallery running on http://localhost:5001")
    serve(port=5001)