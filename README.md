# StarHTML

A streamlined Python-first HTML framework forked from FastHTML, built on [Datastar](https://data-star.dev/) instead of HTMX.

## Installation

```bash
pip install starhtml
```

## Quick Start

```python
from starhtml.common import *

app, rt = fast_app()

@rt('/')
def get(): 
    return Div(
        H1("StarHTML Demo"),
        # Client-side reactivity with signals
        Div(data_signals_count="0"),
        P("Count: ", Span(data_text="$count")),
        Button("++", data_on_click="$count++"),
        Button("Reset", data_on_click="$count = 0"),
        
        # Server-side interactions
        Button("Load Data", data_on_click="@get('/api/data')"),
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
| HTMX | Datastar |
| nbdev notebooks | Regular Python files |
| Broader ecosystem | Minimal dependencies |
| Jupyter integration | Standard development |

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
