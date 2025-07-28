# New Datastar API for StarHTML

## Overview

The new Datastar API provides a clean, Pythonic interface for creating reactive web applications. Instead of string-based attributes, you now use functions that integrate seamlessly with FastHTML/StarHTML elements.

## Key Features

### 1. Function-Based API

Every `ds_*` attribute is now a function:

```python
from starhtml import Div, Button
from starhtml.datastar import ds_show, ds_on_click, ds_class

# Old API (string-based)
Div("Content", ds_show="$visible")

# New API (function-based)
Div("Content", ds_show("$visible"))
```

### 2. Helper Functions for Expressions

**Template Literals** with `t()`:
```python
from starhtml.datastar import t, ds_text

Span(ds_text(t("Hello {$userName}! You have {$count} messages.")))
# Outputs: data-text="`Hello ${$userName}! You have ${$count} messages.`"
```

**Conditionals** with `if_()`:
```python
from starhtml.datastar import if_, ds_style

# Simple ternary
Div(ds_style(
    opacity=if_("$loading", 0.5, 1),
    cursor=if_("$disabled", "not-allowed", "pointer")
))

# Pattern matching (CSS-aligned)
Div(ds_style(
    color=if_("$status",
        success="green",
        error="red",
        warning="orange",
        _="gray"  # default case
    )
))
```

**Condition Helpers**:
```python
from starhtml.datastar import equals, gt, lt, gte, lte

# equals("$status", "active") → "$status === 'active'"
# gt("$count", 0) → "$count > 0"
# lt("$width", 600) → "$width < 600"
# gte("$score", 80) → "$score >= 80"
# lte("$age", 65) → "$age <= 65"
```

### 3. HTML-Style Event Modifiers

Boolean modifiers can be passed as positional arguments (HTML style) or kwargs:

```python
# HTML style (positional args)
Button("Submit", ds_on_click("submit()", "once", "prevent"))

# Kwargs style
Button("Submit", ds_on_click("submit()", once=True, prevent=True))

# Mixed style
Input(ds_on_input("search()", "prevent", debounce="500ms"))
```

### 4. Smart Type Handling

Python types automatically convert to JavaScript:

```python
ds_show(True)                    # → data-show="true"
ds_signals(count=0, active=True) # → data-signals-count="0" data-signals-active="true"
ds_style(opacity=0.5)            # → data-style-opacity="0.5"
```

### 5. Flexible Pattern Matching

For `ds_persist` and `ds_json_signals`, use flexible string/list patterns:

```python
# Single pattern
ds_persist(include="user", exclude="temp")

# Multiple patterns
ds_persist(include=["user", "profile"], exclude=["temp", "cache"])

# Regex patterns
import re
ds_persist(include=[re.compile(r"user_\d+")])
```

## Complete API Reference

### Core Attributes

```python
ds_show(value: bool | str)                  # Show/hide element
ds_text(value: str)                         # Set text content
ds_html(value: str)                         # Set HTML content
ds_bind(signal: str, case=None)             # Two-way binding
ds_ref(name: str)                           # Element reference
ds_indicator(name: str)                     # Loading indicator
ds_effect(expression: str)                  # Side effects
ds_for(expression: str)                     # Loop over items
ds_key(expression: str)                     # Unique key for loops
ds_disabled(value: bool | str)              # Disable element
ds_cloak()                                  # Hide until loaded
```

### Conditional Attributes

```python
ds_class(**classes)                         # Conditional classes
ds_style(**styles)                          # Inline styles  
ds_attr(**attrs)                            # Element attributes
```

### Signals & State

```python
ds_signals(*args, **kwargs)                 # Define signals
ds_computed(name, expression, case=None)    # Computed signals
ds_persist(*signals, include=None, exclude=None, session=False, key=None)
ds_json_signals(show=True, include=None, exclude=None, terse=False)
```

### Event Handlers

```python
ds_on_click(expr, *modifiers, **kwargs)
ds_on_input(expr, *modifiers, **kwargs)
ds_on_change(expr, *modifiers, **kwargs)
ds_on_submit(expr, *modifiers, **kwargs)
ds_on_keydown(expr, *modifiers, **kwargs)
ds_on_keyup(expr, *modifiers, **kwargs)
ds_on_focus(expr, *modifiers, **kwargs)
ds_on_blur(expr, *modifiers, **kwargs)
ds_on_scroll(expr, *modifiers, **kwargs)
ds_on_resize(expr, *modifiers, **kwargs)
ds_on_load(expr, *modifiers, **kwargs)
ds_on_interval(expr, *modifiers, **kwargs)
ds_on_intersect(expr, *modifiers, **kwargs)
ds_on(event, expr, *modifiers, **kwargs)    # Custom events
```

### Special Attributes

```python
ds_ignore(*modifiers)                       # Ignore from processing
ds_preserve_attr(*attrs)                    # Preserve during morphing
```

## Usage Examples

### Basic Form

```python
from starhtml import Form, Input, Button
from starhtml.datastar import ds_signals, ds_bind, ds_disabled, ds_on_submit

Form(
    Input(type="email", ds_bind("email", case="lower")),
    Input(type="password", ds_bind("password")),
    Button("Login", ds_disabled("!$email || !$password")),
    ds_signals(email="", password=""),
    ds_on_submit("login()", "prevent")
)
```

### Interactive Card

```python
from starhtml import Div, H3, P
from starhtml.datastar import ds_signals, ds_style, ds_on, if_

Div(
    H3("Hover Card"),
    P("Hover to see effects!"),
    
    ds_signals(hovered=False),
    ds_style(
        background=if_("$hovered", "#e3f2fd", "#fff"),
        transform=if_("$hovered", "scale(1.05)", "scale(1)"),
        transition="all 0.3s ease"
    ),
    ds_on("mouseenter", "$hovered = true"),
    ds_on("mouseleave", "$hovered = false")
)
```

### Todo List

```python
from starhtml import Ul, Li, Input, Span
from starhtml.datastar import ds_bind, ds_text, ds_style, ds_for, ds_show, if_

Ul(
    Li(
        Input(type="checkbox", ds_bind("todo.completed")),
        Span(
            ds_text("$todo.text"),
            ds_style(
                text_decoration=if_("$todo.completed", "line-through", "none")
            )
        ),
        ds_for("todo in $todos"),
        ds_show("$filter === 'all' || !$todo.completed")
    )
)
```

## Migration from Old API

```python
# Old API
Div(
    ds_show="$visible",
    ds_text="Hello",
    ds_on_click__once__prevent="handleClick()",
    ds_class_active="$isActive"
)

# New API  
Div(
    ds_show("$visible"),
    ds_text("Hello"),
    ds_on_click("handleClick()", "once", "prevent"),
    ds_class(active="$isActive")
)
```

## Best Practices

1. **Direct function usage** - Functions work seamlessly without unpacking
2. **Explicit `$` references** - Always use `$` when referencing signals
3. **Leverage helpers** - Use `t()`, `if_()`, and condition helpers for cleaner code
4. **Group related attributes** - Use `ds_class()`, `ds_style()` for multiple values
5. **Type hints** - The API is fully typed for better IDE support
