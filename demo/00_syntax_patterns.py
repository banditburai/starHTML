"""Demo 00: Common StarHTML syntax patterns and best practices"""

from starhtml import *

app, rt = star_app(
    title="StarHTML Syntax Patterns",
    hdrs=[
        Script(src="https://cdn.jsdelivr.net/npm/@tailwindcss/browser@4"),
    ],
)


@rt("/")
def home():
    return Div(
        H1("Common StarHTML Syntax Patterns"),
        # CORRECT: All positional args (children) first, then keyword args
        Div(
            P("This is correct syntax"),
            P("Children come first"),
            id="correct-example",
            style="border: 1px solid green; padding: 10px; margin: 10px 0;",
        ),
        # Pattern 1: When you need an ID/class early, put ALL attrs at the end
        Div(
            H1("Pattern 1: Attributes Last"),
            P("All children first"),
            P("Then all attributes"),
            id="example1",
            cls="my-class",
            style="background: #f0f0f0; padding: 10px; margin: 10px 0;",
        ),
        # Pattern 2: Use nested structure to make it clearer
        Div(
            H1("Pattern 2: Nested Structure"),
            Div(P("Inner content here"), id="inner", style="border: 1px solid #ccc; padding: 10px;"),
            id="outer",
            style="background: #e0e0e0; padding: 10px; margin: 10px 0;",
        ),
        # Pattern 3: Extract complex components
        example_component(),
        # Common Error Examples (commented out - would cause SyntaxError)
        Pre(
            Code("""
# WRONG - SyntaxError:
# Div(id="test", P("content"), style="...")

# CORRECT - Attributes after children:
# Div(P("content"), id="test", style="...")

# WRONG - Mixing positions:
# Button("Click", id="btn", Icon("arrow"), cls="primary")

# CORRECT - All children first:
# Button("Click", Icon("arrow"), id="btn", cls="primary")
"""),
            style="background: #333; color: #0f0; padding: 15px; margin: 20px 0;",
        ),
        style="max-width: 800px; margin: 0 auto; padding: 20px;",
    )


def example_component():
    """Extract complex components to avoid syntax errors"""
    return Div(
        H1("Pattern 3: Component Functions"),
        P("Extract complex structures into functions"),
        P("This makes the code cleaner and avoids syntax issues"),
        id="component-example",
        style="background: #f8f8f8; padding: 10px; margin: 10px 0;",
    )


if __name__ == "__main__":
    print("StarHTML Syntax Patterns Demo running on http://localhost:5001")
    serve(port=5001)
