"""Basic Datastar Signals Demo - Showcasing the new typed signal API"""

from starhtml import *

app, rt = star_app(
    title="Basic Datastar Signals",
    hdrs=[
        Script(src="https://cdn.jsdelivr.net/npm/@tailwindcss/browser@4"),
        Style("""
            body { background: white; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; -webkit-font-smoothing: antialiased; }
        """),
    ],
    iconify=True,
    compression=False,  # Disable compression for demo
)


@rt("/")
def home():
    return Div(
        # Define signals using walrus operator
        (counter := Signal("counter", 0)),  # Infers int from 0
        (step := Signal("step", 5)),  # Infers int from 5
        # Header with bold typography
        Div(
            H1("01", cls="text-8xl font-black text-gray-100 leading-none"),
            H1("Basic Signals", cls="text-5xl md:text-6xl font-bold text-black mt-2"),
            P("Reactive data binding with Datastar", cls="text-lg text-gray-600 mt-4"),
            cls="mb-16",
        ),
        # Simple Operations Section
        Div(
            H3("Simple Operations", cls="text-2xl font-bold text-black mb-6"),
            Div(
                Button(
                    "+1",
                    data_on_click=counter.add(1),
                    cls="px-4 py-2 bg-black text-white font-medium hover:bg-gray-800 transition-colors mr-2",
                ),
                Button(
                    "-1",
                    data_on_click=counter.sub(1),
                    cls="px-4 py-2 bg-black text-white font-medium hover:bg-gray-800 transition-colors mr-2",
                ),
                Button(
                    "Reset",
                    data_on_click=counter.set(0),
                    cls="px-4 py-2 border border-gray-300 text-black font-medium hover:border-gray-500 transition-colors",
                ),
                cls="mb-6",
            ),
            Div(
                Span("Counter: ", cls="text-gray-600 text-lg"),
                Span(data_text=counter, cls="text-6xl font-black text-black"),
                cls="p-8 bg-gray-50 border border-gray-200",
            ),
            cls="mb-12 p-8 bg-white border border-gray-200",
        ),
        # Math Operations Section
        Div(
            H3("Math Operations", cls="text-2xl font-bold text-black mb-6"),
            Div(
                Label("Step size: ", cls="text-gray-600 font-medium mr-2"),
                Input(
                    type="number",
                    data_bind=step,
                    min="1",
                    max="100",
                    cls="w-20 px-3 py-2 border border-gray-300 focus:border-gray-500 focus:outline-none",
                ),
                cls="mb-6 flex items-center",
            ),
            Div(
                Button(
                    "Add Step",
                    data_on_click=counter.add(step),
                    cls="px-4 py-2 bg-gray-900 text-white font-medium hover:bg-gray-700 transition-colors mr-2",
                ),
                Button(
                    "Subtract Step",
                    data_on_click=counter.sub(step),
                    cls="px-4 py-2 bg-gray-900 text-white font-medium hover:bg-gray-700 transition-colors mr-2",
                ),
                Button(
                    "Double",
                    data_on_click=counter.mul(2),
                    cls="px-4 py-2 bg-gray-900 text-white font-medium hover:bg-gray-700 transition-colors mr-2",
                ),
                Button(
                    "Halve",
                    data_on_click=counter.div(2),
                    cls="px-4 py-2 bg-gray-900 text-white font-medium hover:bg-gray-700 transition-colors",
                ),
                cls="flex flex-wrap gap-2",
            ),
            cls="mb-12 p-8 bg-gray-50",
        ),
        # Conditional Display Section
        Div(
            H3("Conditional Display", cls="text-2xl font-bold text-black mb-6"),
            # Three separate indicators, each with their own condition
            Div(
                # Counter is positive - shows when counter > 0
                Div(
                    Icon("material-symbols:check-circle", width="24", height="24", cls="mr-3 text-green-600"),
                    "Counter is positive",
                    data_show=counter > 0,
                    cls="flex items-center p-4 mb-3 rounded-lg border bg-green-50 border-green-200 text-green-900",
                ),
                # Counter > 10 - shows when counter > 10
                Div(
                    Icon("material-symbols:trending-up", width="24", height="24", cls="mr-3 text-blue-600"),
                    "Counter is greater than 10",
                    data_show=counter > 10,
                    cls="flex items-center p-4 mb-3 rounded-lg border bg-blue-50 border-blue-200 text-blue-900",
                ),
                # Counter is even - shows when counter is even
                Div(
                    Icon("material-symbols:balance", width="24", height="24", cls="mr-3 text-purple-600"),
                    "Counter is even",
                    data_show=(counter % 2) == 0,
                    cls="flex items-center p-4 mb-3 rounded-lg border bg-purple-50 border-purple-200 text-purple-900",
                ),
                # Show message when counter is 0 or negative
                Div(
                    Icon("material-symbols:info-outline", width="24", height="24", cls="mr-3 text-gray-500"),
                    "Increase the counter to see conditions activate",
                    data_show=counter <= 0,
                    cls="flex items-center p-4 rounded-lg border bg-gray-50 border-gray-200 text-gray-600 italic",
                ),
            ),
            cls="mb-12",
        ),
        cls="max-w-5xl mx-auto px-8 sm:px-12 lg:px-16 py-16 sm:py-20 md:py-24 bg-white min-h-screen",
    )


if __name__ == "__main__":
    serve(port=5012)
