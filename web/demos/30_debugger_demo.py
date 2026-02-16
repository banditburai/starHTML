"""StarHTML Debugger Demo - exercises the debug panel with SSE events and DOM morphs."""

import time

from starhtml import *

app, rt = star_app(
    debug=True,
    title="Debugger Demo",
    htmlkw={"lang": "en"},
    hdrs=[
        Script(src="https://cdn.jsdelivr.net/npm/@tailwindcss/browser@4"),
        Style("""
            body { background: white; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; -webkit-font-smoothing: antialiased; }
        """),
        iconify_script(),
    ],
)

count = Signal("count", 0)


@rt("/")
def home():
    return Div(
        count,
        Div(
            H1("30", cls="text-8xl font-black text-gray-100 leading-none"),
            H1("Debugger", cls="text-5xl md:text-6xl font-bold text-black mt-2"),
            P("Open the debug panel with Ctrl/Cmd+Shift+. or click the tab at the bottom-right.",
              cls="text-lg text-gray-600 mt-4"),
            cls="mb-16",
        ),
        Div(
            H3("Signal Updates", cls="text-2xl font-bold text-black mb-6"),
            Div(
                Button(
                    Icon("material-symbols:add", cls="mr-2"),
                    "Increment",
                    data_on_click=get("increment"),
                    cls="inline-flex items-center px-4 py-2 bg-black text-white font-medium hover:bg-gray-800 transition-colors",
                ),
                cls="mb-6",
            ),
            Div(
                Span("Count: ", cls="text-gray-600 text-lg"),
                Span(data_text=count, id="counter", cls="text-6xl font-black text-black"),
                cls="p-8 bg-gray-50 border border-gray-200",
            ),
            cls="mb-12 p-8 bg-white border border-gray-200",
        ),
        Div(
            H3("DOM Mutations", cls="text-2xl font-bold text-black mb-6"),
            Div(
                Button(
                    Icon("material-symbols:add-box-outline", cls="mr-2"),
                    "Append Element",
                    data_on_click=get("add-element"),
                    cls="inline-flex items-center px-4 py-2 bg-blue-600 text-white font-medium hover:bg-blue-700 transition-colors mr-2",
                ),
                Button(
                    Icon("material-symbols:border-color", cls="mr-2"),
                    "Update Attribute",
                    data_on_click=get("update-attr"),
                    cls="inline-flex items-center px-4 py-2 border border-gray-300 text-black font-medium hover:border-gray-500 transition-colors",
                ),
                cls="mb-6 flex flex-wrap gap-2",
            ),
            Div(id="dynamic-content", cls="min-h-[100px] p-4 bg-gray-50 border border-gray-200 space-y-2"),
            cls="mb-12 p-8 bg-white border border-gray-200",
        ),
        cls="max-w-5xl mx-auto px-8 sm:px-12 lg:px-16 py-16 sm:py-20 md:py-24 bg-white min-h-screen",
    )


@rt("/increment")
@sse
def increment(req, count: int = 0):
    yield signals(count=count + 1)


@rt("/add-element")
@sse
def add_element(req):
    yield elements(
        Div(
            Icon("material-symbols:check-circle", cls="mr-2 text-green-600"),
            f"Added at {time.strftime('%H:%M:%S')}",
            cls="flex items-center p-3 bg-white border border-green-200 text-green-900",
        ),
        "#dynamic-content",
        "append",
    )


@rt("/update-attr")
@sse
def update_attr(req):
    yield elements(
        Div(
            id="dynamic-content",
            cls="min-h-[100px] p-4 bg-blue-50 border-2 border-blue-400 space-y-2",
        ),
        "#dynamic-content",
    )


if __name__ == "__main__":
    serve(port=5030)
