"""SSE elements demo - shows server-sent updates with new Signal API"""

import random
import time

from starhtml import *

app, rt = star_app(
    title="SSE Elements Demo",
    hdrs=[
        Script(src="https://cdn.jsdelivr.net/npm/@tailwindcss/browser@4"),
        Style("""
            body { background: white; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; -webkit-font-smoothing: antialiased; }
            @keyframes slideIn { from { opacity: 0; transform: translateY(-10px); } to { opacity: 1; transform: translateY(0); } }
        """),
    ],
    iconify=True,
    compression=False,
)

items_store = []  # mocked in-memory storage
next_id = 1  # Track next ID separately


@rt("/")
def home():
    return Div(
        # Define signals for this page - itemcount should reflect current store
        (status := Signal("status", "Ready")),
        (loading := Signal("loading", False)),
        (itemcount := Signal("itemcount", len(items_store))),
        (filter_text := Signal("filter_text", "")),
        Div(
            # Header with bold typography
            Div(
                H1("02", cls="text-8xl font-black text-gray-100 leading-none"),
                H1("SSE Elements", cls="text-5xl md:text-6xl font-bold text-black mt-2"),
                P("Real-time server-sent events", cls="text-lg text-gray-600 mt-4"),
                cls="mb-16",
            ),
            # Control Panel
            Div(
                H3("Controls", cls="text-2xl font-bold text-black mb-6"),
                Div(
                    Button(
                        Icon("material-symbols:sync", cls="mr-2 animate-spin", data_show=loading),
                        Span("Load Sample Data", data_show=~loading),  # JS: data_show="!$loading"
                        Span("Loading...", data_show=loading),  # JS: data_show="$loading"
                        data_on_click=get("api/load-data"),
                        data_indicator="loading",
                        cls="px-4 py-2 bg-black text-white font-medium hover:bg-gray-800 transition-colors mr-2",
                    ),
                    Button(
                        Icon("material-symbols:add", cls="mr-2"),
                        "Add Random Item",
                        data_on_click=get("api/add-item"),
                        cls="px-4 py-2 bg-blue-600 text-white font-medium hover:bg-blue-700 transition-colors mr-2",
                    ),
                    Button(
                        Icon("material-symbols:delete-outline", cls="mr-2"),
                        "Clear All",
                        data_on_click=get("api/clear"),
                        cls="px-4 py-2 border border-gray-300 text-black font-medium hover:border-gray-500 transition-colors",
                    ),
                    cls="flex flex-wrap gap-2",
                ),
                # Progress indicator for loading operations
                Div(
                    P("Loading in progress...", cls="text-gray-600 text-sm mt-1"),
                    data_show=loading,  # JS: data_show="$loading"
                    cls="mt-4",
                ),
                cls="mb-12 p-8 bg-white border border-gray-200",
            ),
            # Search/Filter Panel
            Div(
                H3("Filter Items", cls="text-2xl font-bold text-black mb-6"),
                Div(
                    Div(
                        Icon(
                            "material-symbols:search",
                            cls="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400",
                        ),
                        Input(
                            type="text",
                            placeholder="Type to filter items...",
                            data_bind=filter_text,  # JS: data_bind="filter_text"
                            cls="w-full pl-10 pr-4 py-2 border border-gray-300 focus:border-gray-500 focus:outline-none",
                        ),
                        cls="relative",
                    ),
                    P(
                        "Showing items containing: '",
                        Span(data_text=filter_text, cls="font-bold text-blue-600"),  # JS: data_text="$filter_text"
                        "'",
                        data_show=filter_text,  # JS: data_show="$filter_text"
                        cls="mt-2 text-gray-600 text-sm",
                    ),
                ),
                cls="mb-12 p-8 bg-gray-50",
            ),
            # Status Bar
            Div(
                Div(
                    Icon("material-symbols:info-outline", cls="mr-2"),
                    Span("Status: ", cls="font-medium"),
                    Span(data_text=status, cls="font-semibold"),  # JS: data_text="$status"
                    cls="flex items-center",
                ),
                Div(
                    Icon("material-symbols:inventory-2-outline", cls="mr-2"),
                    Span("Items: ", cls="font-medium"),
                    Span(data_text=itemcount, cls="font-bold text-lg"),  # JS: data_text="$itemcount"
                    cls="flex items-center",
                ),
                cls="flex justify-between items-center p-4 bg-blue-50 border border-blue-200 text-blue-900 mb-6",
            ),
            # Items Container
            Div(
                H3(
                    "Items", data_show=itemcount, cls="text-2xl font-bold text-black mb-6"
                ),  # JS: data_show="$itemcount"
                # Empty state - visible when itemCount is 0
                Div(
                    Icon("material-symbols:package-2-outline", cls="text-6xl text-gray-300 mb-4"),
                    P("No items yet", cls="font-medium text-lg mb-2 text-gray-700"),
                    P("Click 'Load Sample Data' to get started", cls="text-sm text-gray-500"),
                    data_show=~itemcount,  # JS: data_show="!$itemcount"
                    cls="text-center py-12",
                ),
                Div(
                    # Render existing items if any
                    *[
                        Div(
                            Icon("material-symbols:article-outline", cls="mr-3 text-gray-500"),
                            item["text"].replace("📋 ", "").replace("🆕 ", ""),
                            cls="flex items-center p-3 bg-white border border-gray-200 mb-2 hover:border-gray-400 transition-colors",
                            data_id=str(item["id"]),
                            data_show=~filter_text
                            | value(item["text"].lower()).contains(
                                filter_text.lower()
                            ),  # JS: data_show="!$filter_text || '{{item_text}}'.toLowerCase().includes($filter_text.toLowerCase())"
                        )
                        for item in items_store
                    ],
                    id="items",
                ),
                cls="mb-12 p-8 bg-gray-50 border border-gray-200 min-h-[200px]",
            ),
        ),
        cls="max-w-5xl mx-auto px-8 sm:px-12 lg:px-16 py-16 sm:py-20 md:py-24 bg-white min-h-screen",
    )


@rt("/api/load-data")
@sse
def load_data(req, filter_text: Signal):
    global next_id
    yield signals(status="Loading sample data...", loading=True)
    time.sleep(0.5)  # simulate network latency

    # Add some sample items (append to existing)
    sample_items = ["🍎 Apple", "🍌 Banana", "🍒 Cherry", "🥝 Kiwi", "🫐 Elderberry"]

    for item_text in sample_items:
        # Create item with unique ID
        new_item = {"id": next_id, "text": item_text, "created_at": time.strftime("%H:%M:%S")}
        next_id += 1
        items_store.append(new_item)

        # Send element to DOM with filter support using injected Signal
        item_div = Div(
            Icon("material-symbols:article-outline", cls="mr-3 text-gray-500"),
            new_item["text"],
            cls="flex items-center p-3 bg-white border border-gray-200 mb-2 hover:border-gray-400 transition-colors animate-[slideIn_0.3s_ease-out]",
            data_id=str(new_item["id"]),
            # Show if filter is empty OR item text contains filter text (case-insensitive)
            data_show=~filter_text
            | value(new_item["text"].lower()).contains(
                filter_text.lower()
            ),  # JS: data_show="!$filter_text || '{{text}}'.toLowerCase().includes($filter_text.toLowerCase())"
        )
        yield elements(item_div, "#items", "append")
        # Update item count
        yield signals(itemcount=len(items_store))
        time.sleep(0.3)

    yield signals(status=f"Added {len(sample_items)} sample items", loading=False)


@rt("/api/add-item")
@sse
def add_item(req, filter_text: Signal):
    global next_id
    yield signals(status="Adding new item...")
    time.sleep(0.4)

    # Add a random item
    fruits = ["🍊 Orange", "🍇 Grape", "🥭 Mango", "🍍 Pineapple", "🍓 Strawberry", "🫐 Blueberry"]
    item_text = random.choice(fruits)

    # Create new item with unique ID
    new_item = {
        "id": next_id,
        "text": item_text,
        "created_at": time.strftime("%H:%M:%S"),
    }
    next_id += 1
    items_store.append(new_item)

    # Send element to DOM with filter support using composable primitives
    item_div = Div(
        Icon("material-symbols:fiber-new", cls="mr-3 text-green-600"),
        new_item["text"],
        cls="flex items-center p-3 bg-green-50 border border-green-200 border-l-4 border-l-green-500 mb-2 hover:border-green-400 transition-colors animate-[slideIn_0.3s_ease-out]",
        data_id=str(new_item["id"]),
        # Show if filter is empty OR item text contains filter text (case-insensitive)
        data_show=~filter_text
        | value(new_item["text"])
        .lower()
        .contains(
            filter_text.lower()
        ),  # JS: data_show="!$filter_text || '{{text}}'.toLowerCase().includes($filter_text.toLowerCase())"
    )
    yield elements(item_div, "#items", "append")

    # Update status and count
    yield signals(status=f"Added {new_item['text']}", itemcount=len(items_store))


@rt("/api/clear")
@sse
def clear(req):
    global items_store, next_id
    yield signals(status="Clearing all items...")
    time.sleep(0.3)

    # Clear mocked in-memory storage and reset ID counter
    items_store.clear()
    next_id = 1

    # Clear DOM
    yield elements(Div(), "#items", "inner")

    # Reset counters
    yield signals(status="All items cleared", itemcount=0, filter_text="")


if __name__ == "__main__":
    print("SSE Elements Demo running on http://localhost:5002")
    serve(port=5002)
