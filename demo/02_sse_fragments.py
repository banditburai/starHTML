"""SSE fragments demo - shows server-sent updates"""

from starhtml import star_app, Div, Button, P, H1, Span
from starhtml.datastar import sse_response, update_signals, update_fragments, ds_signals, ds_on, ds_text
from starhtml.core import serve
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
            Button("Load Data", **ds_on(click="@get('/api/load-data')")),
            Button("Add Item", **ds_on(click="@get('/api/add-item')")),
            Button("Clear", **ds_on(click="@get('/api/clear')")),
            
            P("Status: ", **ds_text("$status"), style="font-weight: bold; margin: 20px 0;"),
            
            Div(id="items", style="border: 1px solid #ccc; padding: 10px; min-height: 200px;"),
            
            **ds_signals(status="Ready")
        ),
        
        style="padding: 20px; max-width: 600px; margin: 0 auto;"
    )

@rt('/api/load-data')
@sse_response
def load_data():
    yield update_signals(status="Loading...")
    time.sleep(0.5)
    
    # Add some sample items
    items = ["Apple", "Banana", "Cherry", "Date", "Elderberry"]
    for i, item in enumerate(items):
        yield update_fragments(
            P(f"{i+1}. {item}", style="margin: 5px 0; padding: 5px; background: #f0f0f0;"),
            "#items",
            "append"
        )
        time.sleep(0.2)
    
    yield update_signals(status=f"Loaded {len(items)} items")

@rt('/api/add-item')
@sse_response
def add_item():
    yield update_signals(status="Adding item...")
    time.sleep(0.3)
    
    # Add a random item
    items = ["Orange", "Grape", "Mango", "Pineapple", "Strawberry", "Blueberry"]
    item = random.choice(items)
    
    yield update_fragments(
        P(f"• {item}", style="margin: 5px 0; padding: 5px; background: #e8f5e8; border-left: 3px solid green;"),
        "#items",
        "append"
    )
    
    yield update_signals(status=f"Added {item}")

@rt('/api/clear')
@sse_response
def clear():
    yield update_signals(status="Clearing...")
    time.sleep(0.2)
    
    # Use a single space or empty div to clear content
    yield update_fragments(Div("", id="empty-placeholder"), "#items", "inner")
    yield update_signals(status="Cleared")

if __name__ == "__main__":
    print("SSE Fragments Demo running on http://localhost:5001")
    serve()