# ruff: noqa: F841
"""StarHTML Debugger Demo - exercises the debug panel with SSE events, DOM morphs,
and diverse signal types for the Signals tab."""

import time

from starelements import Local, element
from starhtml import *
from starhtml.plugins import persist

app, rt = star_app(
    debug=True,
    title="Debugger Demo",
    htmlkw={"lang": "en"},
    hdrs=[
        Script(src="https://cdn.jsdelivr.net/npm/@tailwindcss/browser@4"),
        Style("""
            body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; -webkit-font-smoothing: antialiased; }
        """),
        iconify_script(),
    ],
)

app.register(persist)


@element("demo-counter")
def DemoCounter():
    count = Local("count", 0)
    label = Local("label", "Clicks")
    return Div(
        Div(
            Span(data_text=label, cls="text-gray-500 text-sm"),
            Span(data_text=count, cls="text-3xl font-black"),
            cls="flex flex-col items-center gap-1",
        ),
        Div(
            Button(
                "+1",
                data_on_click=count.add(1),
                cls="px-3 py-1 bg-black text-white font-medium hover:bg-gray-800 transition-colors",
            ),
            Button(
                "Reset",
                data_on_click=count.set(0),
                cls="px-3 py-1 border border-gray-300 font-medium hover:border-gray-500 transition-colors",
            ),
            cls="flex gap-2",
        ),
        cls="flex flex-col items-center gap-4 p-6 border border-gray-200 rounded",
    )


app.register(DemoCounter)


BTN = "inline-flex items-center px-4 py-2 font-medium transition-colors"
BTN_PRIMARY = f"{BTN} bg-black text-white hover:bg-gray-800"
BTN_OUTLINE = f"{BTN} border border-gray-300 hover:border-gray-500"


@rt("/")
def home():
    return Div(
        (count := Signal("count", 0)),
        (accent := Signal("accent", "blue")),
        (size := Signal("size", "medium")),
        (tags := Signal("tags", ["alpha", "beta"])),
        Signal("meta", {"version": "1.0", "env": "dev"}),
        (ticker := Signal("ticker", 0)),

        # -- Header --
        Div(
            H1("30", cls="text-8xl font-black text-gray-200 leading-none"),
            H1("Debugger", cls="text-5xl md:text-6xl font-bold mt-2"),
            P("Open the debug panel with Ctrl/Cmd+Shift+. or click the tab at the bottom-right.",
              cls="text-lg text-gray-500 mt-4"),
            cls="mb-16",
        ),

        # -- Reactive Expressions --
        Div(
            H3("Reactive Expressions", cls="text-2xl font-bold mb-6"),
            P("Signals drive visual changes through match(), .one_of(), .clamp(), and collect().",
              cls="text-gray-500 mb-6"),

            # Accent color picker — match() maps value to Tailwind classes
            Div(
                Span("Accent:", cls="text-gray-500 text-sm font-medium"),
                *[Button(
                    color.capitalize(),
                    data_on_click=accent.set(color),
                    data_attr_class=collect([
                        (True, "px-3 py-1 text-sm font-medium rounded transition-colors"),
                        (accent == color, f"bg-{color}-600 text-white"),
                        (accent != color, "bg-gray-100 text-gray-600 hover:bg-gray-200"),
                    ]),
                ) for color in ("blue", "green", "red", "amber")],
                cls="flex items-center gap-2 mb-4",
            ),

            # Size selector — .one_of() guards the value
            Div(
                Span("Size:", cls="text-gray-500 text-sm font-medium"),
                *[Button(
                    s.capitalize(),
                    data_on_click=size.set(s),
                    data_attr_class=(size.one_of("small", "medium", "large") == s).if_(
                        "px-3 py-1 text-sm font-medium rounded bg-black text-white",
                        "px-3 py-1 text-sm font-medium rounded bg-gray-100 text-gray-600 hover:bg-gray-200",
                    ),
                ) for s in ("small", "medium", "large")],
                cls="flex items-center gap-2 mb-6",
            ),

            # Preview box — driven by accent + size signals
            Div(
                Span(
                    data_text="Hello, " + accent.one_of("blue", "green", "red", "amber") + " world!",
                    cls="font-semibold",
                ),
                data_attr_class=collect([
                    (True, "p-6 rounded border-2 transition-all"),
                    (accent == "blue", "border-blue-400 bg-blue-50 text-blue-900"),
                    (accent == "green", "border-green-400 bg-green-50 text-green-900"),
                    (accent == "red", "border-red-400 bg-red-50 text-red-900"),
                    (accent == "amber", "border-amber-400 bg-amber-50 text-amber-900"),
                ]),
                data_attr_style=match(size,
                    small="font-size: 0.875rem",
                    medium="font-size: 1.125rem",
                    large="font-size: 1.5rem",
                    default="font-size: 1.125rem",
                ),
            ),
            cls="mb-12 p-8 bg-white border border-gray-200 rounded",
        ),

        # -- Counter with SSE + clamp --
        Div(
            H3("Signal Updates", cls="text-2xl font-bold mb-6"),
            P("Count is persisted to localStorage via the persist plugin.",
              cls="text-gray-500 mb-6"),
            Div(
                Button(
                    Icon("material-symbols:add", cls="mr-2"),
                    "Increment",
                    data_on_click=get("increment"),
                    cls=BTN_PRIMARY,
                ),
                Button(
                    Icon("material-symbols:remove", cls="mr-2"),
                    "Decrement",
                    data_on_click=get("decrement"),
                    cls=BTN_OUTLINE,
                ),
                Button("Reset", data_on_click=count.set(0), cls=BTN_OUTLINE),
                cls="mb-6 flex flex-wrap gap-2",
            ),
            Div(
                Span("Count: ", cls="text-gray-500 text-lg"),
                Span(data_text=count, id="counter", cls="text-6xl font-black"),
                cls="p-8 bg-gray-50 border border-gray-200 rounded",
            ),
            Div(data_persist=count, style="display:none"),
            cls="mb-12 p-8 bg-white border border-gray-200 rounded",
        ),

        # -- Component Signals --
        Div(
            H3("Component Signals", cls="text-2xl font-bold mb-6"),
            P("Each counter is a StarElements component with its own namespaced signals.",
              cls="text-gray-500 mb-6"),
            Div(DemoCounter(), DemoCounter(), cls="flex gap-6"),
            cls="mb-12 p-8 bg-white border border-gray-200 rounded",
        ),

        # -- DOM Mutations --
        Div(
            H3("DOM Mutations", cls="text-2xl font-bold mb-6"),
            Div(
                Button(
                    Icon("material-symbols:add-box-outline", cls="mr-2"),
                    "Append Element",
                    data_on_click=get("add-element"),
                    cls=f"{BTN} bg-blue-600 text-white hover:bg-blue-700",
                ),
                Button(
                    Icon("material-symbols:border-color", cls="mr-2"),
                    "Update Attribute",
                    data_on_click=get("update-attr"),
                    cls=BTN_OUTLINE,
                ),
                cls="mb-6 flex flex-wrap gap-2",
            ),
            Div(id="dynamic-content", cls="min-h-[100px] p-4 bg-gray-50 border border-gray-200 rounded space-y-2"),
            cls="mb-12 p-8 bg-white border border-gray-200 rounded",
        ),

        # -- Rapid Signal Changes --
        Div(
            H3("Rapid Updates", cls="text-2xl font-bold mb-6"),
            P("A client-side timer increments every 500ms to test change flash in the debugger.",
              cls="text-gray-500 mb-4"),
            Button("Reset Timer", data_on_click=ticker.set(0), cls=BTN_OUTLINE + " mb-4"),
            Div(
                Span("Ticker: ", cls="text-gray-500"),
                Span(data_text=ticker, cls="text-2xl font-black"),
                data_init=js("setInterval(() => { $ticker++ }, 500)"),
                cls="p-4 bg-gray-50 border border-gray-200 rounded",
            ),
            cls="mb-12 p-8 bg-white border border-gray-200 rounded",
        ),
        cls="max-w-5xl mx-auto px-8 sm:px-12 lg:px-16 py-16 sm:py-20 md:py-24 min-h-screen",
    )


@rt("/increment")
@sse
def increment(req, count: int = 0):
    yield signals(count=count + 1)


@rt("/decrement")
@sse
def decrement(req, count: int = 0):
    yield signals(count=count - 1)


@rt("/add-element")
@sse
def add_element(req):
    yield elements(
        Div(
            Icon("material-symbols:check-circle", cls="mr-2 text-green-600"),
            f"Added at {time.strftime('%H:%M:%S')}",
            cls="flex items-center p-3 bg-white border border-green-200 text-green-900 rounded",
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
            cls="min-h-[100px] p-4 bg-blue-50 border-2 border-blue-400 rounded space-y-2",
        ),
        "#dynamic-content",
    )


if __name__ == "__main__":
    serve(port=5030)
