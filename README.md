<div align="center">

<a href="https://starhtml.com"><img src="web/static/images/og/starhtml.jpg" alt="StarHTML — Python Web Framework" width="100%"></a>

<a href="https://ui.starhtml.com"><img src="web/static/images/og/starui.jpg" alt="StarUI — Python Component Library" width="100%"></a>

![PyPI Version](https://img.shields.io/pypi/v/starhtml?style=for-the-badge)
![License](https://img.shields.io/github/license/banditburai/starhtml?style=for-the-badge)

**A Python-first hypermedia framework, forked from FastHTML. Uses [Datastar](https://data-star.dev/) instead of HTMX for the same hypermedia-driven approach with a different flavor.**

[Documentation](https://starhtml.com) · [UI Components](https://ui.starhtml.com) · [Quick Start](#quick-start) · [Community](https://github.com/banditburai/starhtml/discussions) · [Issues](https://github.com/banditburai/starhtml/issues)

</div>

## Key Features

- **Python-First** — Write reactive UIs using Python syntax with type safety and IDE support
- **Reactive Signals** — Hypermedia approach with data-attribute-powered client-side reactivity where needed
- **Server-Sent Events** — Built-in SSE support for real-time server interactions
- **Framework Agnostic** — Works with any CSS framework (Tailwind, DaisyUI)
- **JavaScript Escape Hatch** — Drop into raw JavaScript when needed for complex interactions

## Quick Start

```bash
pip install starhtml
```

```python
from starhtml import *

app, rt = star_app()

@rt('/')
def home():
    return Div(
        H1("StarHTML Demo"),

        # Define reactive state with signals
        Div(
            (counter := Signal("counter", 0)),  # Python-first signal definition

            # Reactive UI that updates automatically
            P("Count: ", Span(data_text=counter)),
            Button("+", data_on_click=counter.add(1)),
            Button("Reset", data_on_click=counter.set(0)),

            # Conditional styling
            data_class_active=counter > 0
        ),

        # Server-side interactions
        Button("Load Data", data_on_click=get("/api/data")),
        Div(id="content")
    )

@rt('/api/data')
def api_data():
    return Div("Data loaded from server!", id="content")

serve()
```

Run with `python app.py` and visit `http://localhost:5001`.

## What's Different?

| FastHTML | StarHTML |
|----------|----------|
| HTMX for server interactions | Datastar for reactive UI |
| Built with nbdev notebooks | Standard Python modules |
| Multiple JS extensions | Single reactive framework |
| WebSockets for real-time | SSE for real-time |

## Development

```bash
git clone https://github.com/banditburai/starhtml.git
cd starhtml
uv sync  # or pip install -e ".[dev]"
pytest && ruff check .
```

Contributions welcome — see [CONTRIBUTING.md](CONTRIBUTING.md).

## Acknowledgments

StarHTML is a fork of [FastHTML](https://github.com/AnswerDotAI/fasthtml). Built on [Datastar](https://data-star.dev/) for client-side reactivity.
