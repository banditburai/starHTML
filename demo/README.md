# StarHTML Demo Collection

This demo collection showcases StarHTML's integration with Datastar v1 RC for reactive UI components and Server-Sent Events (SSE).

## Running the Demos

Run any individual demo:
```bash
uv run demo/01_basic_signals.py
uv run demo/02_sse_fragments.py
uv run demo/03_forms_binding.py
uv run demo/04_sse_debugging.py
```

Each demo runs on http://localhost:5001/

## Available Demos

1. **Basic Signals** (`01_basic_signals.py`)
   - Client-side reactivity with counters
   - Signal state management
   - Simple click handlers

2. **SSE Fragments** (`02_sse_fragments.py`)
   - Server-Sent Events for real-time updates
   - Dynamic content loading
   - Fragment append and clear operations

3. **Forms & Binding** (`03_forms_binding.py`)
   - Two-way data binding with form inputs
   - Live preview of form data
   - Form submission and clearing

4. **SSE Debugging** (`04_sse_debugging.py`)
   - Test various SSE fragment scenarios
   - Multiple target updates
   - Complex HTML with special characters

5. **Syntax Helper** (`10_syntax_helper.py`)
   - Common StarHTML patterns
   - How to avoid positional/keyword argument errors
   - Best practices for component structure

## Key Features Demonstrated

1. **Reactive Signals** - Using `ds_signals()` for client-side state
2. **Two-way Binding** - Using `ds_bind()` for form inputs  
3. **Event Handling** - Using `ds_on()` for click events
4. **Conditional Display** - Using `ds_show()` for visibility
5. **Text Interpolation** - Using `ds_text()` for dynamic content
6. **SSE Updates** - Real-time server-to-client updates
7. **Fragment Merging** - Dynamic HTML injection via SSE

## What Was Fixed

The main fragment issue was in the SSE event format. The implementation now uses the correct Datastar v1 RC format:

### Fixed Signal Format
```
event: datastar-merge-signals
retry: 1000
data: signals {"key": "value", "key2": "value2"}
```

### Fixed Fragment Format  
```
event: datastar-merge-fragments
retry: 1000
data: selector #target-element
data: mergeMode morph
data: fragments <div>HTML content</div>
```

## Changes Made

- ✅ Updated event names from `datastar-signal` to `datastar-merge-signals`
- ✅ Updated event names from `datastar-fragment` to `datastar-merge-fragments`  
- ✅ Fixed data line format to match v1 RC specification
- ✅ Cleaned up demo folder (removed debugging clutter)
- ✅ Created comprehensive tests for SSE format
- ✅ Added proper fragment merging with selectors and merge modes
- ✅ **Baked Datastar into StarHTML** - Datastar v1 RC is now automatically included like HTMX in FastHTML