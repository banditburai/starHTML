"""StarHTML Debugger Demo - demonstrates the debug panel."""

import time

from starhtml import *

app, rt = star_app(
    debug=True,
    title="Debugger Demo",
)

count = Signal("count", 0)


@rt("/")
def home():
    return Div(
        H1("Debugger Demo"),
        P("Open the debug panel with Ctrl/Cmd+Shift+. or click the tab at the bottom-right."),
        Div(
            Button("Increment", data_on_click=get("/increment"), style="margin-right:8px"),
            Button("Add Element", data_on_click=get("/add-element"), style="margin-right:8px"),
            Button("Update Attribute", data_on_click=get("/update-attr")),
            style="margin:16px 0",
        ),
        P("Count: ", Span(data_text=count, id="counter"), style="font-size:1.2em"),
        Div(id="dynamic-content", style="margin-top:16px"),
    )


@rt("/increment")
@sse
def increment(req):
    yield signals(count=count + 1)


@rt("/add-element")
@sse
def add_element(req):
    yield elements(
        P(f"New paragraph added at {time.strftime('%H:%M:%S')}!", style="color:green"),
        "#dynamic-content",
        "append",
    )


@rt("/update-attr")
@sse
def update_attr(req):
    yield elements(
        Div(id="dynamic-content", style="margin-top:16px;border:2px solid blue;padding:8px"),
        "#dynamic-content",
        "morph",
    )


if __name__ == "__main__":
    print("Debugger Demo running on http://localhost:5030")
    serve(port=5030)
