# StarHTML

<div align="center">

![PyPI Version](https://img.shields.io/pypi/v/starhtml?style=for-the-badge)
![License](https://img.shields.io/github/license/banditburai/starhtml?style=for-the-badge)

**A Python-first hypermedia framework, forked from FastHTML. Uses [Datastar](https://data-star.dev/) instead of HTMX for the same hypermedia-driven approach with a different flavor.**

[📚 Documentation](https://github.com/banditburai/starhtml/blob/main/api.md) • [🚀 Quick Start](#quick-start) • [💬 Community](https://github.com/banditburai/starhtml/discussions) • [🐛 Issues](https://github.com/banditburai/starhtml/issues)

</div>

## ✨ Key Features

- **🐍 Python-First** - Write reactive UIs using Python syntax with type safety and IDE support
- **🔄 Reactive Signals** - Hypermedia approach with data attribute powered client-side reactivity where needed
- **📡 Server-Sent Events** - Built-in SSE support for real-time server interactions
- **🎨 Framework Agnostic** - Works with any CSS framework (Tailwind, DaisyUI)
- **🛠️ JavaScript Escape Hatch** - Drop into raw JavaScript when needed for complex interactions
- **🎯 Type Safety** - Full IDE support with autocomplete and error detection

## 🚀 Quick Start

### Installation

```bash
pip install starhtml
```

### Your First App

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

## 🆚 What's Different?

| FastHTML | StarHTML |
|----------|----------|
| HTMX for server interactions | Datastar for reactive UI |
| Built with nbdev notebooks | Standard Python modules |
| Multiple JS extensions | Single reactive framework |
| WebSockets for real-time | SSE for real-time |


## 🛠️ Development

```bash
git clone https://github.com/banditburai/starhtml.git
cd starhtml
uv sync  # or pip install -e ".[dev]"
pytest && ruff check .
```

### Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 🤝 Community & Support

- **💬 Discussions**: [GitHub Discussions](https://github.com/banditburai/starhtml/discussions) - Ask questions, share ideas
- **🐛 Issues**: [GitHub Issues](https://github.com/banditburai/starhtml/issues) - Report bugs, request features
- **📚 Documentation**: [API Reference](https://github.com/banditburai/starhtml/blob/main/api.md)
- **💡 Examples**: Check out the `/examples` directory for more complex use cases

## 📄 License

This project is licensed under the Apache License 2.0 - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

*StarHTML is a respectful fork of [FastHTML](https://github.com/AnswerDotAI/fasthtml). We're grateful to the FastHTML team for the excellent foundation.*

- **[FastHTML](https://github.com/AnswerDotAI/fasthtml)** - The original framework that inspired StarHTML
- **[Datastar](https://data-star.dev/)** - The reactive JavaScript library powering client-side interactions
- **Contributors** - Thank you to everyone who has contributed to making StarHTML better

---

<div align="center">

**[⭐ Star us on GitHub](https://github.com/banditburai/starhtml) if you find StarHTML useful!**

</div>
