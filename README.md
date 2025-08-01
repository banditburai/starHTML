# StarHTML

A Python-first hypermedia framework, forked from FastHTML. Uses [Datastar](https://data-star.dev/) instead of HTMX for the same hypermedia-driven approach with a different flavor.

## Installation

```bash
pip install starhtml
```

## Quick Start

```python
from starhtml import *
from starhtml.datastar import ds_text, ds_on_click, ds_signals

app, rt = star_app()

@rt('/')
def home(): 
    return Div(
        H1("StarHTML Demo"),
        # Client-side reactivity with signals
        Div(
            P("Count: ", Span(ds_text("$count"))),
            Button("++", ds_on_click("$count++")),
            Button("Reset", ds_on_click("$count = 0")),
            ds_signals(count=0)
        ),
        
        # Server-side interactions
        Button("Load Data", ds_on_click("@get('/api/data')")),
        Div(id="content")
    )

@rt('/api/data')
def get():
    return Div("Data loaded from server!", id="content")

serve()
```

Run with `python main.py` and visit `http://localhost:5001`.

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

## Links

- [Repository](https://github.com/banditburai/starhtml) • [Issues](https://github.com/banditburai/starhtml/issues) • [Discussions](https://github.com/banditburai/starhtml/discussions)
- [Original FastHTML](https://github.com/AnswerDotAI/fasthtml) • [Datastar](https://data-star.dev/)

---

*StarHTML is a respectful fork of [FastHTML](https://github.com/AnswerDotAI/fasthtml). We're grateful to the FastHTML team for the excellent foundation.*
