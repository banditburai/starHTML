"""Dynamic Mermaid Diagrams Demo - Content processor plugin with live updates"""

from starhtml import *
from starhtml.plugins import mermaid

app, rt = star_app(
    title="Dynamic Mermaid Diagrams",
    htmlkw={"lang": "en"},
    hdrs=[
        Script(src="https://cdn.jsdelivr.net/npm/@tailwindcss/browser@4"),
        Style("""
            body { background: white; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; }
            .mermaid-container { overflow-x: auto; -webkit-overflow-scrolling: touch; }
            .mermaid-container svg { max-width: 100%; height: auto; }
            .mermaid-render { min-width: 0; }
            /* Reset pre wrapper styling */
            .mermaid-render > pre[data-mermaid] {
                background: none;
                color: inherit;
                padding: 0;
                margin: 0;
                font-family: inherit;
                white-space: normal;
            }
        """),
    ],
)
app.register(mermaid)

# Sample diagrams
DIAGRAMS = {
    "flowchart": """flowchart TD
    A[Start] --> B{Is it working?}
    B -->|Yes| C[Great!]
    B -->|No| D[Debug]
    D --> B""",
    "sequence": """sequenceDiagram
    participant Client
    participant Server
    participant Database
    Client->>Server: HTTP Request
    Server->>Database: Query
    Database-->>Server: Results
    Server-->>Client: Response""",
    "class": """classDiagram
    class Animal {
        +String name
        +int age
        +makeSound()
    }
    class Dog {
        +fetch()
    }
    class Cat {
        +scratch()
    }
    Animal <|-- Dog
    Animal <|-- Cat""",
    "state": """stateDiagram-v2
    [*] --> Idle
    Idle --> Loading: fetch
    Loading --> Success: data
    Loading --> Error: fail
    Success --> Idle: reset
    Error --> Loading: retry
    Error --> Idle: cancel""",
}


def diagram_content(code: str):
    """The actual diagram content that gets replaced."""
    return Div(
        # Content-based ID: morphing treats as new element only when content changes
        Pre(code, data_mermaid=True, id=f"mermaid-{hash(code)}"),
        cls="mermaid-render",
    )


@rt("/")
def home():
    return Div(
        (custom_code := Signal("custom_code", DIAGRAMS["flowchart"])),
        # Header
        Div(
            H1("15", cls="text-8xl font-black text-gray-100 leading-none"),
            H1("Mermaid Diagrams", cls="text-5xl md:text-6xl font-bold text-black mt-2"),
            P("Dynamic diagram rendering with the mermaid plugin", cls="text-lg text-gray-600 mt-4"),
            cls="mb-16",
        ),
        # Diagram selector
        Div(
            H3("Select a Diagram", cls="text-2xl font-bold text-black mb-6"),
            Div(
                Button(
                    "Flowchart",
                    data_on_click=get("diagram/flowchart"),
                    cls="px-4 py-2 bg-black text-white font-medium hover:bg-gray-800 transition-colors",
                ),
                Button(
                    "Sequence",
                    data_on_click=get("diagram/sequence"),
                    cls="px-4 py-2 bg-black text-white font-medium hover:bg-gray-800 transition-colors",
                ),
                Button(
                    "Class",
                    data_on_click=get("diagram/class"),
                    cls="px-4 py-2 bg-black text-white font-medium hover:bg-gray-800 transition-colors",
                ),
                Button(
                    "State",
                    data_on_click=get("diagram/state"),
                    cls="px-4 py-2 bg-black text-white font-medium hover:bg-gray-800 transition-colors",
                ),
                cls="mb-8 flex flex-wrap gap-2",
            ),
            cls="mb-8",
        ),
        # Diagram display
        Div(
            diagram_content(DIAGRAMS["flowchart"]),
            cls="mermaid-container p-4 sm:p-8 bg-gray-50 border border-gray-200 rounded-lg min-h-[300px] sm:min-h-[400px]",
            id="diagram-display",
        ),
        # Custom diagram editor with debounced auto-render
        Div(
            H3("Custom Diagram", cls="text-xl sm:text-2xl font-bold text-black mb-6"),
            P("Edit the code below - diagram updates automatically:", cls="text-gray-600 mb-4 text-sm sm:text-base"),
            Textarea(
                DIAGRAMS["flowchart"],
                data_bind=custom_code,
                data_on_input=get("diagram/custom").with_(debounce=500),
                rows="8",
                cls="w-full p-3 sm:p-4 font-mono text-xs sm:text-sm border border-gray-300 rounded-lg focus:border-gray-500 focus:outline-none mb-4",
            ),
            Div(
                diagram_content(DIAGRAMS["flowchart"]),
                cls="mermaid-container p-4 sm:p-8 bg-gray-50 border border-gray-200 rounded-lg min-h-[300px] sm:min-h-[400px]",
                id="custom-diagram-display",
            ),
            cls="mt-8 sm:mt-12 p-4 sm:p-8 bg-white border border-gray-200 rounded-lg",
        ),
        cls="max-w-5xl mx-auto px-4 sm:px-8 lg:px-16 py-12 sm:py-16 md:py-24 bg-white min-h-screen",
    )


@rt("/diagram/custom")
@sse
def get_custom(custom_code: str = ""):
    """Render custom diagram - signal auto-extracted by StarHTML."""
    code = custom_code or DIAGRAMS["flowchart"]
    yield elements(diagram_content(code), "#custom-diagram-display", "inner")


@rt("/diagram/{name}")
@sse
def get_diagram(name: str):
    """Return a diagram by name via SSE."""
    code = DIAGRAMS.get(name, DIAGRAMS["flowchart"])
    yield elements(diagram_content(code), "#diagram-display", "inner")


if __name__ == "__main__":
    serve(port=5015)
