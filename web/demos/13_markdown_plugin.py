"""Dynamic Markdown Demo - Content processor plugin with live updates"""

from starhtml import *
from starhtml.plugins import markdown

app, rt = star_app(
    title="Dynamic Markdown",
    htmlkw={"lang": "en"},
    hdrs=[
        Script(src="https://cdn.jsdelivr.net/npm/@tailwindcss/browser@4"),
        Style("""
            body { background: white; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Noto Sans', sans-serif; }

            /* Prose styling inspired by Tailwind Typography */
            .markdown-content {
                color: #374151;
                line-height: 1.75;
                max-width: 65ch;
            }

            /* Headings - graduated weights, tighter line-height */
            .markdown-content h1 {
                color: #111827;
                font-size: 2.25em;
                font-weight: 800;
                line-height: 1.1;
                margin: 0 0 0.9em 0;
            }
            .markdown-content h2 {
                color: #111827;
                font-size: 1.5em;
                font-weight: 700;
                line-height: 1.33;
                margin: 2em 0 1em 0;
                padding-bottom: 0.3em;
                border-bottom: 1px solid #e5e7eb;
            }
            .markdown-content h3 {
                color: #111827;
                font-size: 1.25em;
                font-weight: 600;
                line-height: 1.6;
                margin: 1.6em 0 0.6em 0;
            }

            /* Paragraphs */
            .markdown-content p { margin: 1.25em 0; }

            /* Lists - proper indentation and spacing */
            .markdown-content ul, .markdown-content ol {
                margin: 1.25em 0;
                padding-left: 1.625em;
            }
            .markdown-content li { margin: 0.5em 0; padding-left: 0.375em; }
            .markdown-content li::marker { color: #6b7280; }

            /* Reset the outer pre[data-markdown] wrapper - it's not a code block */
            .markdown-content > pre[data-markdown] {
                background: none;
                color: inherit;
                padding: 0;
                margin: 0;
                font-family: inherit;
                font-size: inherit;
                white-space: normal;
                overflow: visible;
            }

            /* Inline code */
            .markdown-content code {
                background: #f3f4f6;
                color: #1f2937;
                padding: 0.2em 0.4em;
                border-radius: 6px;
                font-size: 0.875em;
                font-family: ui-monospace, SFMono-Regular, 'SF Mono', Menlo, monospace;
                font-weight: 500;
            }

            /* Code blocks (pre elements inside the rendered markdown) */
            .markdown-content pre:not([data-markdown]) {
                background: #f3f4f6;
                color: #1f2937;
                padding: 1em;
                border-radius: 8px;
                overflow-x: auto;
                font-size: 0.875em;
                line-height: 1.7;
                margin: 1.75em 0;
                font-family: ui-monospace, SFMono-Regular, 'SF Mono', Menlo, monospace;
            }
            .markdown-content pre:not([data-markdown]) code {
                background: none;
                padding: 0;
                font-size: inherit;
                font-weight: 400;
            }

            /* Blockquotes */
            .markdown-content blockquote {
                border-left: 4px solid #e5e7eb;
                margin: 1.6em 0;
                padding: 0 0 0 1em;
                color: #6b7280;
                font-style: italic;
            }
            .markdown-content blockquote p { margin: 0.5em 0; }

            /* Links */
            .markdown-content a {
                color: #2563eb;
                text-decoration: underline;
                text-underline-offset: 2px;
                font-weight: 500;
            }
            .markdown-content a:hover { color: #1d4ed8; }

            /* Horizontal rules */
            .markdown-content hr {
                border: none;
                height: 1px;
                background: #e5e7eb;
                margin: 2em 0;
            }

            /* Strong and emphasis */
            .markdown-content strong { color: #111827; font-weight: 600; }
            .markdown-content em { font-style: italic; }
        """),
    ],
)
app.register(markdown)

# Sample markdown content
SAMPLES = {
    "intro": """# Welcome to Markdown

This is a **dynamic markdown** demo using the StarHTML markdown plugin.

## Features

- Real-time rendering
- Server-side updates via SSE
- Full markdown syntax support

> "Markdown is a lightweight markup language for creating formatted text."

Try the buttons above to load different content!""",
    "code": """# Code Examples

Here's some inline `code` and a code block:

```python
def hello_world():
    print("Hello from StarHTML!")
    return {"status": "success"}
```

## Lists

1. First item
2. Second item
3. Third item

### Unordered list:

- Apples
- Oranges
- Bananas""",
    "links": """# Links and Formatting

Visit [StarHTML on GitHub](https://github.com) for more info.

## Text Formatting

This is **bold text** and this is *italic text*.

You can also use ***bold italic*** together.

---

## Blockquotes

> This is a blockquote.
> It can span multiple lines.

### Nested quote:

> Level 1
> > Level 2
> > > Level 3""",
}

DEFAULT_CUSTOM = """# My Custom Markdown

Edit this text and click **Render** to see the result!

- Item 1
- Item 2
- Item 3

`inline code` works too."""


def markdown_content(text: str):
    """Render markdown content with the plugin."""
    return Div(
        # Content-based ID: morphing treats as new element only when content changes
        Pre(text, data_markdown=True, id=f"md-{hash(text)}"),
        cls="markdown-content",
    )


@rt("/")
def home():
    return Div(
        # Signal for custom markdown
        (custom_md := Signal("custom_md", DEFAULT_CUSTOM)),
        # Header
        Div(
            H1("25", cls="text-8xl font-black text-gray-100 leading-none"),
            H1("Markdown Rendering", cls="text-5xl md:text-6xl font-bold text-black mt-2"),
            P("Dynamic markdown processing with the markdown plugin", cls="text-lg text-gray-600 mt-4"),
            cls="mb-16",
        ),
        # Content selector
        Div(
            H3("Sample Content", cls="text-2xl font-bold text-black mb-6"),
            Div(
                Button(
                    "Introduction",
                    data_on_click=get("/content/intro"),
                    cls="px-4 py-2 bg-black text-white font-medium hover:bg-gray-800 transition-colors",
                ),
                Button(
                    "Code Examples",
                    data_on_click=get("/content/code"),
                    cls="px-4 py-2 bg-black text-white font-medium hover:bg-gray-800 transition-colors",
                ),
                Button(
                    "Links & Formatting",
                    data_on_click=get("/content/links"),
                    cls="px-4 py-2 bg-black text-white font-medium hover:bg-gray-800 transition-colors",
                ),
                cls="mb-8 flex flex-wrap gap-2",
            ),
            cls="mb-8",
        ),
        # Markdown display
        Div(
            markdown_content(SAMPLES["intro"]),
            cls="p-8 bg-gray-50 border border-gray-200 rounded-lg min-h-[300px]",
            id="markdown-display",
        ),
        # Custom markdown editor with debounced auto-render
        Div(
            H3("Custom Markdown", cls="text-2xl font-bold text-black mb-6"),
            P("Edit the markdown below - preview updates automatically:", cls="text-gray-600 mb-4"),
            Textarea(
                DEFAULT_CUSTOM,
                data_bind=custom_md,
                data_on_input=get("/content/custom").with_(debounce=500),
                rows="10",
                cls="w-full p-4 font-mono text-sm border border-gray-300 rounded-lg focus:border-gray-500 focus:outline-none mb-4",
            ),
            Div(
                markdown_content(DEFAULT_CUSTOM),
                cls="p-8 bg-gray-50 border border-gray-200 rounded-lg min-h-[200px]",
                id="custom-markdown-display",
            ),
            cls="mt-12 p-8 bg-white border border-gray-200 rounded-lg",
        ),
        cls="max-w-4xl mx-auto px-8 sm:px-12 lg:px-16 py-16 sm:py-20 md:py-24 bg-white min-h-screen",
    )


@rt("/content/custom")
@sse
def get_custom(custom_md: str = ""):
    """Render custom markdown - signal auto-extracted by StarHTML."""
    text = custom_md or DEFAULT_CUSTOM
    yield elements(markdown_content(text), "#custom-markdown-display", "inner")


@rt("/content/{name}")
@sse
def get_content(name: str):
    """Return markdown content by name via SSE."""
    text = SAMPLES.get(name, SAMPLES["intro"])
    yield elements(markdown_content(text), "#markdown-display", "inner")


if __name__ == "__main__":
    serve(port=5013)
