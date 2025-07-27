# StarHTML Demo Hub

Interactive examples to learn StarHTML step by step.

## Quick Start

```bash
# Run all demos through the hub (recommended)
uv run demo/hub.py

# Visit http://localhost:5001
```

## Individual Demos

You can also run individual demos for development:

```bash
# Run individual demos
uv run demo/01_basic_signals.py    # port 5002
uv run demo/02_sse_elements.py     # port 5003
uv run demo/06_persist_handler.py  # port 5004
# ... etc
```

## Learning Path

### 🚀 Foundation (Start Here)
- **00_syntax_patterns.py** - StarHTML syntax patterns and best practices
- **01_basic_signals.py** - Reactive data binding with Datastar signals
- **02_sse_elements.py** - Real-time updates with Server-Sent Events
- **03_forms_binding.py** - Form handling and data binding patterns

### 🔧 Intermediate
- **04_sse_debugging.py** - Debug SSE merge elements and real-time updates
- **05_async_sse.py** - Asynchronous SSE handlers and patterns

### ⚡ Advanced
- **06_persist_handler.py** - Data persistence with localStorage/sessionStorage
- **07_scroll_handler.py** - Scroll detection and position tracking
- **08_resize_handler.py** - Window and element resize detection

## Features

- **One Entry Point**: `uv run demo/hub.py` runs everything
- **Separate Files**: Each demo is its own clean, copyable file
- **Individual Testing**: Each demo can also run standalone
- **Progressive Learning**: Organized by difficulty level
- **Clear Examples**: Users can copy entire files as starting points

## Copy-Paste Ready

Each demo file is designed to be copied as a starting point for your own projects. They contain complete, working examples with minimal dependencies.

## Key Features Demonstrated

1. **Reactive Signals** - Using `ds_signals()` for client-side state
2. **Two-way Binding** - Using `ds_bind()` for form inputs  
3. **Event Handling** - Using `ds_on()` for click events
4. **Conditional Display** - Using `ds_show()` for visibility
5. **Text Interpolation** - Using `ds_text()` for dynamic content
6. **SSE Updates** - Real-time server-to-client updates
7. **Fragment Merging** - Dynamic HTML injection via SSE
8. **Handler Patterns** - Persist, scroll, and resize handlers

