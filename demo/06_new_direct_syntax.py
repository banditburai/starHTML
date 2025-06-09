"""Demo: New direct attribute syntax for Datastar (no ** unpacking needed!)"""

from starhtml import *

app, rt = star_app()

@rt('/')
def home():
    """Demo of the new direct attribute syntax."""
    return Div(
        H1("StarHTML Direct Attribute Syntax", cls="text-3xl font-bold mb-6"),
        P("No more ** unpacking! Use Datastar attributes directly.", cls="text-lg mb-8"),

        # Example 1: Basic signals and binding
        Div(
            H2("1. Basic Signals & Binding", cls="text-xl font-semibold mb-4"),
            Form(
                Input(
                    type="text",
                    ds_bind="$username",
                    placeholder="Enter username",
                    cls="border p-2 rounded"
                ),
                P(
                    "Hello, ",
                    ds_text="$username || 'Guest'",
                    cls="mt-2"
                ),
                cls="space-y-2 mb-8"
            )
        ),

        # Example 2: Event handlers
        Div(
            H2("2. Event Handlers", cls="text-xl font-semibold mb-4"),
            Button(
                "Click Count: ",
                ds_text="`Click Count: ${$clickCount}`",
                ds_on_click="$clickCount++",
                cls="bg-blue-500 text-white px-4 py-2 rounded hover:bg-blue-600"
            ),
            cls="mb-8"
        ),

        # Example 3: Conditional rendering
        Div(
            H2("3. Conditional Rendering", cls="text-xl font-semibold mb-4"),
            Button(
                "Toggle Visibility",
                ds_on_click="$showContent = !$showContent",
                cls="bg-green-500 text-white px-4 py-2 rounded hover:bg-green-600 mb-2"
            ),
            Div(
                "This content is conditionally visible!",
                ds_show="$showContent",
                cls="p-4 bg-yellow-100 rounded"
            ),
            cls="mb-8"
        ),

        # Example 4: Dynamic attributes
        Div(
            H2("4. Dynamic Attributes", cls="text-xl font-semibold mb-4"),
            Button(
                "Toggle Loading",
                ds_on_click="$isLoading = !$isLoading",
                cls="bg-purple-500 text-white px-4 py-2 rounded hover:bg-purple-600 mb-2"
            ),
            Button(
                "Submit",
                ds_attr_disabled="$isLoading",
                ds_class="{ 'opacity-50 cursor-not-allowed': $isLoading }",
                cls="bg-gray-500 text-white px-4 py-2 rounded"
            ),
            cls="mb-8"
        ),

        # Example 5: SSE with indicators
        Div(
            H2("5. Server-Sent Events", cls="text-xl font-semibold mb-4"),
            Button(
                "Load Data",
                ds_on_click="@get('/sse-data')",
                ds_indicator="loading",
                cls="bg-indigo-500 text-white px-4 py-2 rounded hover:bg-indigo-600"
            ),
            Div(
                "Loading...",
                ds_show="$loading",
                cls="mt-2 text-gray-600"
            ),
            Div(
                id="sse-content",
                cls="mt-4 p-4 bg-gray-100 rounded min-h-[50px]"
            ),
            cls="mb-8"
        ),

        # Initialize all signals
        ds_signals={
            "username": "",
            "clickCount": 0,
            "showContent": False,
            "isLoading": False,
            "loading": False
        },
        cls="max-w-4xl mx-auto p-8"
    )

@rt('/sse-data')
@sse
def sse_data(req):
    """Demo SSE endpoint."""
    import time
    time.sleep(1)  # Simulate loading

    yield fragments(
        Div(
            P("Data loaded successfully!", cls="font-semibold text-green-600"),
            P("This content was loaded via SSE.", cls="text-gray-600"),
            P(f"Timestamp: {time.strftime('%Y-%m-%d %H:%M:%S')}", cls="text-sm text-gray-500"),
            id="sse-content"  # Auto-detects #sse-content selector
        )
    )

if __name__ == "__main__":
    print("SSE Debugging Demo running on http://localhost:5001")
    serve()
