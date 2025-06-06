"""SSE fragments demo - shows server-sent updates"""

from starhtml import *
import time
import random

app, rt = star_app(
    title="SSE Fragments Demo"
)

@rt('/')
def home():
    return Div(
        H1("SSE Fragments Demo"),
        
        Div(
            Button("Load Data", ds_on_click="@get('/api/load-data')"),
            Button("Add Item", ds_on_click="@get('/api/add-item')"),
            Button("Clear", ds_on_click="@get('/api/clear')"),
            
            P("Status: ", ds_text="$status", style="font-weight: bold; margin: 20px 0;"),
            
            Div(id="items", style="border: 1px solid #ccc; padding: 10px; min-height: 200px;"),
            
            ds_signals={"status": "Ready"}
        ),
        
        style="padding: 20px; max-width: 600px; margin: 0 auto;"
    )

@rt('/api/load-data')
@sse
def load_data():
    yield signal(status="Loading...")
    time.sleep(0.5)
    
    # Add some sample items
    items = ["Apple", "Banana", "Cherry", "Date", "Elderberry"]
    for i, item in enumerate(items):
        yield fragment(
            P(f"{i+1}. {item}", style="margin: 5px 0; padding: 5px; background: #f0f0f0;"),
            "#items",
            "append"
        )
        time.sleep(0.2)
    
    yield signal(status=f"Loaded {len(items)} items")

@rt('/api/add-item')
@sse
def add_item():
    yield signal(status="Adding item...")
    time.sleep(0.3)
    
    # Add a random item
    items = ["Orange", "Grape", "Mango", "Pineapple", "Strawberry", "Blueberry"]
    item = random.choice(items)
    
    yield fragment(
        P(f"• {item}", style="margin: 5px 0; padding: 5px; background: #e8f5e8; border-left: 3px solid green;"),
        "#items",
        "append"
    )
    
    yield signal(status=f"Added {item}")

@rt('/api/clear')
@sse
def clear():
    yield signal(status="Clearing...")
    time.sleep(0.2)
    
    # Use a single space or empty div to clear content
    yield fragment(Div("", id="empty-placeholder"), "#items", "inner")
    yield signal(status="Cleared")

if __name__ == "__main__":
    print("SSE Fragments Demo running on http://localhost:5001")
    serve()