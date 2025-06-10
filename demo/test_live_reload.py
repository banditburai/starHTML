"""Test live reload functionality"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from starhtml import *

app, rt = star_app(title="Live Reload Test", live=True)


@rt("/")
def home():
    return Div(
        H1("Live Reload Test"),
        P("This page should reload automatically when you save changes."),
        P("Check the browser console for 'LiveReload connected' message."),
        # Simple counter to test Datastar
        Div(Button("Count: ", Span(ds_text="$count"), ds_on_click="$count++"), ds_signals={"count": 0}),
        style="padding: 2rem; max-width: 600px; margin: 0 auto;",
    )


if __name__ == "__main__":
    print("Live Reload Test running on http://localhost:5004")
    serve(port=5004)
