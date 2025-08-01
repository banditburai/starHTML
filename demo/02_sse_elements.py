"""SSE elements demo - shows server-sent updates"""

import random
import time

from starhtml import *

app, rt = star_app(
    title="SSE Elements Demo",
    hdrs=[
        Script(src="https://cdn.jsdelivr.net/npm/@tailwindcss/browser@4"),
    ],
)

items_store = []


@rt("/")
def home():
    return Div(
        Style("""
            body {
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%);
                margin: 0;
                min-height: 100vh;
            }
            .container {
                max-width: 900px;
                margin: 0 auto;
                padding: 2rem;
            }
            .card {
                background: white;
                border-radius: 12px;
                box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
                border: 1px solid #e5e7eb;
                padding: 1.5rem;
                margin-bottom: 1.5rem;
            }
            .btn {
                padding: 0.75rem 1.5rem;
                border-radius: 8px;
                border: none;
                font-weight: 500;
                cursor: pointer;
                transition: all 0.2s;
                font-size: 0.9rem;
            }
            .btn-primary {
                background: linear-gradient(135deg, #3b82f6 0%, #1e40af 100%);
                color: white;
            }
            .btn-primary:hover {
                background: linear-gradient(135deg, #2563eb 0%, #1e3a8a 100%);
                transform: translateY(-1px);
                box-shadow: 0 8px 15px rgba(59, 130, 246, 0.3);
            }
            .btn-secondary {
                background: linear-gradient(135deg, #10b981 0%, #047857 100%);
                color: white;
            }
            .btn-secondary:hover {
                background: linear-gradient(135deg, #059669 0%, #065f46 100%);
                transform: translateY(-1px);
                box-shadow: 0 8px 15px rgba(16, 185, 129, 0.3);
            }
            .btn-danger {
                background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%);
                color: white;
            }
            .btn-danger:hover {
                background: linear-gradient(135deg, #dc2626 0%, #b91c1c 100%);
                transform: translateY(-1px);
                box-shadow: 0 8px 15px rgba(239, 68, 68, 0.3);
            }
            .status-bar {
                background: linear-gradient(135deg, #dbeafe 0%, #bfdbfe 100%);
                border: 1px solid #93c5fd;
                border-radius: 8px;
                padding: 1rem;
                display: flex;
                justify-content: space-between;
                align-items: center;
            }
            .loading-spinner {
                display: inline-block;
                width: 16px;
                height: 16px;
                border: 2px solid #ffffff;
                border-radius: 50%;
                border-top-color: transparent;
                animation: spin 1s ease-in-out infinite;
                margin-right: 0.5rem;
            }
            @keyframes spin {
                to { transform: rotate(360deg); }
            }
            .item {
                background: #f8fafc;
                border: 1px solid #e5e7eb;
                border-radius: 6px;
                padding: 0.75rem 1rem;
                margin-bottom: 0.5rem;
                animation: slideIn 0.3s ease-out;
            }
            .item-new {
                background: linear-gradient(135deg, #ecfdf5 0%, #d1fae5 100%);
                border-color: #10b981;
                border-left: 4px solid #10b981;
            }
            @keyframes slideIn {
                from { opacity: 0; transform: translateY(-10px); }
                to { opacity: 1; transform: translateY(0); }
            }
            .empty-state {
                text-align: center;
                padding: 3rem 1rem;
                color: #6b7280;
            }
            .empty-icon {
                width: 64px;
                height: 64px;
                margin: 0 auto 1rem;
                opacity: 0.5;
            }
            .controls {
                display: flex;
                gap: 1rem;
                flex-wrap: wrap;
            }
        """),
        Div(
            # Header
            Div(
                H1(
                    "SSE Elements Demo",
                    style="color: #1f2937; margin-bottom: 0.5rem; font-size: 2.5rem; font-weight: 700;",
                ),
                P("Real-time server-sent events", style="color: #6b7280; font-size: 1.1rem; margin-bottom: 2rem;"),
                style="text-align: center;",
            ),
            # Control Panel
            Div(
                H2("Controls", style="color: #374151; margin-bottom: 1rem; font-size: 1.3rem; font-weight: 600;"),
                Div(
                    Button(
                        Span("🔄", ds_show("$loading"), cls="loading-spinner"),
                        Span("Load Sample Data", ds_show("!$loading")),
                        Span("Loading...", ds_show("$loading")),
                        ds_on_click("@get('/api/load-data')"),
                        ds_indicator("loading"),
                        cls="btn btn-primary",
                    ),
                    Button("➕ Add Random Item", ds_on_click("@get('/api/add-item')"), cls="btn btn-secondary"),
                    Button("🗑️ Clear All", ds_on_click("@get('/api/clear')"), cls="btn btn-danger"),
                    cls="controls",
                ),
                cls="card",
            ),
            # Status Bar
            Div(
                Div(
                    Span("📊 Status: ", style="font-weight: 500; color: #374151;"),
                    Span(ds_text("$status"), style="color: #1f2937; font-weight: 600;"),
                ),
                Div(
                    Span("📦 Items: ", style="font-weight: 500; color: #374151;"),
                    Span(ds_text("$itemcount"), style="color: #2563eb; font-weight: 700; font-size: 1.1rem;"),
                ),
                cls="status-bar",
            ),
            # Items Container
            Div(
                H3("Items", style="color: #374151; margin-bottom: 1rem; font-size: 1.2rem; font-weight: 600;"),
                # Empty state - visible when itemCount is 0
                Div(
                    Div("📦", cls="empty-icon", style="font-size: 4rem;"),
                    P("No items yet", style="font-weight: 500; font-size: 1.1rem; margin-bottom: 0.5rem;"),
                    P("Click 'Load Sample Data' to get started", style="font-size: 0.9rem; opacity: 0.7;"),
                    ds_show("$itemcount === 0"),
                    cls="empty-state",
                ),
                Div(id="items"),
                cls="card",
            ),
            # Footer
            Div(
                P(
                    "Powered by StarHTML",
                    style="text-align: center; color: #9ca3af; font-size: 0.9rem; margin-top: 2rem;",
                ),
            ),
            ds_signals(status="Ready", loading=False, itemcount=0),
            cls="container",
        ),
    )


@rt("/api/load-data")
@sse
def load_data(req):
    # Use in-memory storage

    yield signals(status="Loading sample data...", loading=True)
    time.sleep(0.5)  # simulate network latency

    # Add some sample items (append to existing)
    sample_items = ["🍎 Apple", "🍌 Banana", "🍒 Cherry", "🥝 Kiwi", "🫐 Elderberry"]
    for item_text in sample_items:
        # Create item with unique ID
        new_item = {"id": len(items_store) + 1, "text": f"📋 {item_text}", "created_at": time.strftime("%H:%M:%S")}
        items_store.append(new_item)

        # Send element to DOM
        yield elements(Div(new_item["text"], cls="item", **{"data-id": str(new_item["id"])}), "#items", "append")
        # Update count from actual storage
        yield signals(itemcount=len(items_store))
        time.sleep(0.3)

    yield signals(status=f"Added {len(sample_items)} sample items", loading=False)


@rt("/api/add-item")
@sse
def add_item(req):
    # Use in-memory storage

    yield signals(status="Adding new item...")
    time.sleep(0.4)

    # Add a random item
    fruits = ["🍊 Orange", "🍇 Grape", "🥭 Mango", "🍍 Pineapple", "🍓 Strawberry", "🫐 Blueberry"]
    item_text = random.choice(fruits)

    # Create new item with unique ID
    new_item = {
        "id": max([item["id"] for item in items_store], default=0) + 1,
        "text": f"🆕 {item_text}",
        "created_at": time.strftime("%H:%M:%S"),
    }
    items_store.append(new_item)

    # Send element to DOM
    yield elements(Div(new_item["text"], cls="item item-new", **{"data-id": str(new_item["id"])}), "#items", "append")

    yield signals(status=f"Added {item_text.split(' ')[1]}", itemcount=len(items_store))


@rt("/api/clear")
@sse
def clear(req):
    yield signals(status="Clearing all items...")
    time.sleep(0.3)

    # Clear in-memory storage
    global items_store
    items_store = []

    # Clear DOM
    yield elements(Div(), "#items", "inner")

    # Update count from actual storage
    yield signals(status="All items cleared", itemcount=0)


if __name__ == "__main__":
    print("SSE Elements Demo running on http://localhost:5001")
    serve(port=5001)
