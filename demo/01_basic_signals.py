"""Basic Datastar signals demo - minimal example using new function-based API"""

from starhtml import *

app, rt = star_app(
    title="Basic Signals Demo",
    hdrs=[
        Script(src="https://cdn.jsdelivr.net/npm/@tailwindcss/browser@4"),
    ],
)


@rt("/")
def home():
    return Div(
        H1("Basic Datastar Signals", cls="text-3xl font-bold mb-6 text-center"),
        Div(
            Button("Increment", ds_on_click("$counter++"), cls="bg-blue-600 text-white px-4 py-2 rounded mr-2"),
            Button("Decrement", ds_on_click("$counter--"), cls="bg-red-600 text-white px-4 py-2 rounded mr-2"),
            Button("Reset", ds_on_click("$counter = 0"), cls="bg-gray-600 text-white px-4 py-2 rounded"),
            P("Counter: ", ds_text("$counter"), cls="text-2xl font-bold mt-4"),
            ds_signals(counter=0),
            cls="text-center",
        ),
        # Example code section
        Div(
            H2("Code Example", cls="text-xl font-semibold mb-4"),
            Pre(
                Code(
                    """Button("Increment", ds_on_click("$counter++"))
Button("Decrement", ds_on_click("$counter--"))
Button("Reset", ds_on_click("$counter = 0"))
P("Counter: ", ds_text("$counter"))
ds_signals(counter=0)""",
                    cls="language-python",
                ),
                cls="bg-gray-100 p-4 rounded-lg overflow-x-auto",
            ),
            cls="mt-8",
        ),
        cls="max-w-2xl mx-auto p-6",
    )


if __name__ == "__main__":
    serve(port=5001)
