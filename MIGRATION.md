# StarHTML Migration Guide: Old API → New API

This guide helps you migrate from the old StarHTML Datastar API to the new keyword-based API with typed Signal objects.

## The Key Change: Functions → Keywords

The old API used wrapper functions that returned dictionaries. The new API uses direct keyword arguments, making your code cleaner and more Pythonic:

```python
# OLD: Function wrappers that spread dictionaries
Div("Hello", **ds_show("$visible"), **ds_on_click("handler()"))

# NEW: Direct keyword arguments
Div("Hello", data_show=visible, data_on_click="handler()")
```

Remember the pattern:
- **Positional args** = content (what goes inside)
- **Keyword args** = configuration (how it behaves)

## Quick Overview

| Old API | New API |  
|---------|---------|
| `**ds_show("$visible")` | `data_show=visible` |
| `**ds_signals(count=0)` | `(count := Signal("count", 0))` |
| `**toggle_class("$active", "on", "off")` | `data_attr_class=active.if_("on", "off")` |

## Step-by-Step Migration

### 1. Update Imports

Remove old imports:
```python
# OLD
from starhtml.datastar import ds_show, ds_bind, ds_on_click, toggle_class, ds_signals
```

Add new imports:
```python
# NEW
from starhtml import *  # Includes Signal, switch, js, etc.
from starhtml.utils import clear_form_signals

# JavaScript global objects (as Python objects that generate JS code)
from starhtml.datastar import console, Math, JSON, Object, Array, Date, Number, String, Boolean
```

### 2. Convert Signal Definitions

#### Old: Manual ds_signals()
```python
def component():
    return Div(
        **ds_signals(
            count=0,
            name="",
            is_active=False
        ),
        # content...
    )
```

#### New: Automatic Signal Collection
```python
def component():
    return Div(
        # Define signals with walrus operator - automatically collected
        (count := Signal("count", 0)),
        (name := Signal("name", "")),
        (is_active := Signal("is_active", False)),
        # content...
    )
```

**Key differences:**
- Signals are defined with walrus operator `:=`
- Type is inferred from initial value
- Automatically injected into `data-signals` attribute
- Must use snake_case naming (enforced)

### 2a. Convert Computed Signals (NEW APPROACH)

#### Old: data_computed_* keyword arguments
```python
def component():
    return Div(
        (name := Signal("name", "")),
        (email := Signal("email", "")),
        (age := Signal("age", 0)),

        # Computed defined at the END as keyword
        data_computed_is_valid=all(name, email, age >= 18)
    )
```

#### New: Signal() with expression values
```python
def component():
    return Div(
        # Regular signals
        (name := Signal("name", "")),
        (email := Signal("email", "")),
        (age := Signal("age", 0)),

        # Computed signals - defined WITH expressions
        (is_valid := Signal("is_valid", all(name, email, age >= 18))),

        # Now you can reference is_valid throughout your component!
        Button("Submit", data_attr_disabled=~is_valid),
        Div(data_text=is_valid.if_("Valid ✓", "Invalid"))
    )
```

**Key differences:**
- **Pass literal value** → regular signal: `Signal("count", 0)`
- **Pass Expr object** → computed signal: `Signal("doubled", count * 2)`
- Computed signals generate `data-computed-*` attributes automatically
- You get a Python reference to use throughout your component
- No more `js("$computed_name")` wrappers needed!

**Examples:**

```python
# Regular signals (literal values)
(counter := Signal("counter", 0))
(name := Signal("name", ""))
(items := Signal("items", []))

# Computed signals (expressions)
(doubled := Signal("doubled", counter * 2))
(full_name := Signal("full_name", first + " " + last))
(is_valid := Signal("is_valid", all(name, email, age >= 18)))
(progress := Signal("progress", js("Math.round($completed / $total * 100)")))
```

### 3. Convert Basic Attributes

#### Show/Hide Elements
```python
# OLD
Div("Content", **ds_show("$visible"))
Div("Loading...", **ds_show("!$loading"))

# NEW
Div("Content", data_show=visible)
Div("Loading...", data_show=~loading)
```

#### Text Content
```python
# OLD
Span(**ds_text("$message"))
P(**ds_text("'Count: ' + $counter"))

# NEW
Span(data_text=message)
P(data_text="Count: " + counter)  # String concatenation creates template literal
```

#### Form Binding
```python
# OLD
Input(**ds_bind("email"), type="email")
Textarea(**ds_bind("message"))

# NEW
Input(data_bind=email, type="email")
Textarea(data_bind=message)
```

### 4. Convert Event Handlers

#### Basic Events
```python
# OLD
Button("Click", **ds_on_click("handleClick()"))
Button("+", **ds_on_click("$counter++"))
Button("-", **ds_on_click("$counter--"))

# NEW
Button("Click", data_on_click="handleClick()")
Button("+", data_on_click=counter.add(1))  # Generates: $counter++
Button("-", data_on_click=counter.sub(1))  # Generates: $counter--
```

#### Events with Modifiers
```python
# OLD
**ds_on_submit("submit()", "prevent", "once")
**ds_on_input("search()", debounce=300)

# NEW - Option 1: Tuple with dictionary literal
data_on_submit=("submit()", {"prevent": True, "once": True})
data_on_input=("search()", {"debounce": 300})

# NEW - Option 2: Tuple with dict() constructor
data_on_submit=("submit()", dict(prevent=True, once=True))
data_on_input=("search()", dict(debounce=300))

# NEW - Option 3: .with_() method (only works on Expr objects)
data_on_submit=js("submit()").with_(prevent=True, once=True)
data_on_input=search.with_(debounce=300)
```

### 5. Convert toggle_class() and Conditional Logic

The old `toggle_class()` and global `if()` functions have been replaced with new approaches:

#### Simple Binary Toggle
```python
# OLD
**toggle_class("$active", "bg-blue-500", "bg-gray-300")

# NEW - Use .if_() method on signals/expressions
data_attr_class=active.if_("bg-blue-500", "bg-gray-300")
```

#### Pattern Matching (was if() with kwargs)
```python
# OLD - Global if() with pattern matching
**if_("$status", "gray",
    loading="yellow",
    success="green",
    error="red"
)

# NEW - Use match() function
data_attr_class=match(status,
    loading="yellow",
    success="green",
    error="red",
    default="gray"  # 'default' instead of first positional arg
)
```

#### Multi-State Conditions (if/elif/else chains)
```python
# OLD - Nested ternaries or complex if()
**if_("$count > 100 ? 'high' : $count > 50 ? 'medium' : 'low'")

# NEW - Use switch() for sequential conditions  
data_attr_class=switch([
    (count > 100, "high"),
    (count > 50, "medium"),
    (count > 0, "low")
], default="empty")
```

#### Combining Multiple Classes
```python
# OLD - Manual string concatenation
**toggle_class("$active", "active", "", base="btn") + " " + 
  toggle_class("$disabled", "disabled", "")

# NEW - Use collect() to combine conditionals
data_attr_class=collect([
    (True, "btn"),  # Always included
    (active, "active"),
    (disabled, "disabled"),
    (loading, "loading")
])  # Automatically joins with spaces
```

#### With Base Classes (NEW data_attr_cls)
```python
# OLD - Manual base class handling
**toggle_class("$expanded", "h-auto", "h-0", base="transition-all")

# NEW Option 1 - Use data_attr_cls (special tuple syntax)
data_attr_cls=("transition-all", expanded.if_("h-auto", "h-0"))
# Renders: class="transition-all" data-attr-class="`transition-all ${$expanded ? 'h-auto' : 'h-0'}`"
# Note: Base classes appear in both static class AND reactive expression

# NEW Option 2 - Manual concatenation
data_attr_class="transition-all " + expanded.if_("h-auto", "h-0")
```

### 6. Convert Signal Operations

#### Setting Values
```python
# OLD
**ds_on_click("$counter = 0")
**ds_on_click("$counter = $counter + 1")
**ds_on_click("$counter = $counter + 5")
**ds_on_click("$counter = $counter * 2")

# NEW - Use arithmetic methods for cleaner code
data_on_click=counter.set(0)          # Direct set
data_on_click=counter.add(1)          # Increment by 1 (generates $counter++)
data_on_click=counter.add(5)          # Add 5 (generates $counter = $counter + 5)
data_on_click=counter.mul(2)          # Double (generates $counter = $counter * 2)
data_on_click=counter.div(2)          # Halve
data_on_click=counter.sub(1)          # Decrement by 1 (generates $counter--)
```

#### Toggle Operations
```python
# OLD
**ds_on_click("$visible = !$visible")
**ds_on_click("$theme = $theme === 'light' ? 'dark' : 'light'")

# NEW
data_on_click=visible.toggle()
data_on_click=theme.toggle("light", "dark")
```

#### Multiple State Cycling
```python
# OLD - complex ternary logic
**ds_on_click("$size = $size === 'sm' ? 'md' : $size === 'md' ? 'lg' : 'sm'")

# NEW - clean toggle method
data_on_click=size.toggle("sm", "md", "lg")
```

#### Additional Signal Methods (NEW)

```python
# Math operations - defined as computed signals
(rounded := Signal("rounded", value.round()))           # Math.round(value)
(precise := Signal("precise", value.round(2)))          # Math.round(value * 100) / 100
(absolute := Signal("absolute", number.abs()))          # Math.abs(number)
(limited := Signal("limited", score.min(100)))          # Math.min(score, 100)
(boosted := Signal("boosted", score.max(0)))            # Math.max(score, 0)
(clamped := Signal("clamped", value.clamp(0, 100)))     # Clamp between 0 and 100

# String operations - defined as computed signals
(lower := Signal("lower", name.lower()))                # name.toLowerCase()
(upper := Signal("upper", name.upper()))                # name.toUpperCase()
(clean := Signal("clean", input.strip()))               # input.trim()
(has_admin := Signal("has_admin", role.contains("admin"))) # role.includes("admin")

# Array operations
data_effect=items.push(new_item)              # items.push(new_item)
(total := Signal("total", js("$prices.reduce((a,b) => a+b, 0)"))) # Array reduce

# Control flow
data_effect=is_valid.then(save_data)          # if (is_valid) { save_data }

# JavaScript utility functions (NEW)
data_effect=console.log("Debug:", message)    # Console logging
(now := Signal("now", Date.now()))            # Current timestamp
(round := Signal("round", Math.round(value))) # Math operations
(json := Signal("json", JSON.stringify(data))) # JSON operations
(keys := Signal("keys", Object.keys(obj)))    # Object utilities
(is_array := Signal("is_array", Array.isArray(items))) # Array checks
```

### 7. Convert Conditional Logic

#### Simple Conditionals
```python
# OLD
**ds_show("$count > 0")
**ds_text("$count > 1 ? 'items' : 'item'")

# NEW  
data_show=count > 0
data_text=(count > 1).if_("items", "item")
```

#### Complex Conditionals  
```python
# OLD - nested ternaries
**ds_attr(
    class="$loading ? 'opacity-50' : $error ? 'bg-red-100' : 'bg-white'"
)

# NEW Option 1 - switch() for if/elif/else logic
data_attr_class=switch([
    (loading, "opacity-50"),
    (error, "bg-red-100")
], default="bg-white")

# NEW Option 2 - match() for value matching
data_attr_class=match(status,
    loading="opacity-50",
    error="bg-red-100",
    success="bg-green-100",
    default="bg-white"
)

# NEW Option 3 - collect() for combining multiple classes
data_attr_class=collect([
    (loading, "opacity-50"),
    (error, "border-red-500"),
    (disabled, "cursor-not-allowed")
])  # All true conditions are included
```

### 8. Convert Form Operations

#### Form Reset
```python
# OLD
**ds_on_click("$name = ''; $email = ''; $message = ''; $submitted = false")

# NEW
data_on_click=clear_form_signals(
    name, email, message,
    submitted=False
)
```

#### Validation Patterns
```python
# OLD
**ds_computed("is_valid", "$name && $email && $message")
**ds_show("$name_error || $email_error")

# NEW - Define computed signal for validation
(is_valid := Signal("is_valid", all(name, email, message)))
data_show=any(name_error, email_error)
```

### 9. Convert HTTP Actions

```python
# OLD
**ds_on_click("@post('/api/submit')")
**ds_on_click("@get('/api/data?id=' + $item_id)")

# NEW
data_on_click=post("/api/submit")
data_on_click=get("/api/data", id=item_id)

# With data
data_on_click=post("/api/submit", name=name, email=email)

# All HTTP methods available
data_on_click=get("/api/data")
data_on_click=post("/api/submit", data=form_data)
data_on_click=put("/api/update", id=item_id)
data_on_click=patch("/api/patch", field=value)
data_on_click=delete("/api/delete", id=item_id)

# Clipboard functionality (NEW)
data_on_click=clipboard("Copy this text")                    # Copy literal text
data_on_click=clipboard(element="#my-element")               # Copy element's text content
data_on_click=clipboard(text=message, signal="copied")      # Copy with feedback signal
data_on_click=clipboard(element="el", signal="copied")      # Copy current element with feedback
```

### 10. Migrate Slot Attributes (Component Composition)

The new API introduces powerful slot_attrs for component composition:

```python
# OLD - manual attribute passing
def modal_old(content):
    header = Div(**ds_class(active="$modal_open"), cls="modal-header")
    body = Div(content, **ds_show("$modal_open"))
    footer = Div(**ds_class(active="$modal_open"), cls="modal-footer")
    return Div(header, body, footer)

# NEW - slot_attrs with copy-paste syntax
def modal_new(content, **kwargs):
    return Div(
        Div(data_slot="header"),
        Div(content, data_slot="body"),
        Div(data_slot="footer"),
        
        # Copy-paste syntax - use same attributes as regular components!
        slot_header=dict(
            data_attr_class=modal_open.if_("modal-header active", "modal-header")
        ),
        slot_body=dict(
            data_show=modal_open
        ),
        slot_footer=dict(
            data_attr_class="modal-footer",
            data_show=modal_open
        ),
        **kwargs
    )
```

**Key points:**
- Snake_case slot names auto-convert to kebab-case: `slot_menu_item` → targets `data-slot="menu-item"`
- Use exact same attribute syntax as regular components
- Can use dictionary or dict() syntax

### 11. Prevent FOUC (Flash of Unstyled Content)

For attributes that need initial SSR values plus reactive updates:

```python
# OLD - manual initial value + reactive attribute
Div(
    style="width: 50%",  # Initial
    **ds_style(width="$progress + '%'")
)

# NEW - Use separate SSR and reactive attributes
Div(
    style=f"width: {initial_progress}%",    # SSR initial value
    data_attr_style=f("width: {p}%", p=progress)  # Reactive update
)
# Renders: style="width: 50%" data-attr-style="`width: ${$progress}%`"
```

Use this pattern for:
- Progress bars that shouldn't jump from 0
- ARIA attributes that need initial values
- Any attribute that changes after page load

## Complete Migration Examples

### Counter Component

```python
# OLD API
def counter_old():
    return Div(
        **ds_signals(count=0),
        H1("Counter"),
        P(**ds_text("$count")),
        Button("+", **ds_on_click("$count++")),
        Button("-", **ds_on_click("$count--")),
        Button("Reset", **ds_on_click("$count = 0")),
        Div("Positive!", **ds_show("$count > 0"))
    )

# NEW API
def counter_new():
    return Div(
        (count := Signal("count", 0)),
        H1("Counter"),
        P(data_text=count),
        Button("+", data_on_click=count.add(1)),    # Clean increment
        Button("-", data_on_click=count.sub(1)),    # Clean decrement
        Button("Reset", data_on_click=count.set(0)),
        Div("Positive!", data_show=count > 0)
    )
```

### Form with Validation

```python
# OLD API
def form_old():
    return Form(
        **ds_signals(name="", email="", valid=False),
        Input(**ds_bind("name"), placeholder="Name"),
        Input(**ds_bind("email"), type="email"),
        Button(
            "Submit",
            data_attr_disabled=~valid,
            data_on_click=("submitForm()", {"prevent": True})
        ),
        **ds_computed("valid", "$name.length > 0 && $email.includes('@')")
    )

# NEW API
def form_new():
    return Form(
        (name := Signal("name", "")),
        (email := Signal("email", "")),

        # Computed signal for validation
        (valid := Signal("valid", (name.length > 0) & email.contains("@"))),

        Input(data_bind=name, placeholder="Name"),
        Input(data_bind=email, type="email"),
        Button(
            "Submit",
            data_attr_disabled=~valid,
            data_on_click=js("submitForm()").with_(prevent=True)
        )
    )
```

### Todo Item with Toggling

```python
# OLD API  
def todo_item_old(todo):
    return Div(
        **ds_signals(completed=todo.completed),
        Input(
            type="checkbox",
            **ds_bind("completed"),
            **ds_on_click(f"toggleTodo({todo.id})")
        ),
        Span(
            todo.text,
            **toggle_class(
                "$completed",
                "line-through text-gray-500",
                "text-black",
                base="px-2"
            )
        )
    )

# NEW API
def todo_item_new(todo):
    (completed := Signal("completed", todo.completed))
    return Div(
        completed,
        Input(
            type="checkbox",
            data_bind=completed,
            data_on_click=post(f"/todos/{todo.id}/toggle")
        ),
        Span(
            todo.text,
            data_attr_class=completed.if_(
                "px-2 line-through text-gray-500",
                "px-2 text-black"
            )
        )
    )
```

## Advanced Migration Patterns

### String Templates: Complete Guide

#### Understanding Reactive vs Static Strings

```python
# REACTIVE - Updates when signal changes
# Use + operator for simple concatenation
data_text=counter + " items"           # → `${$counter} items`
data_text="Count: " + counter          # → `Count: ${$counter}`

# REACTIVE - Use f() for complex templates
from starhtml.datastar import f
data_text=f("You have {n} {type}", n=count, type=item_type)
# → `You have ${$count} ${$item_type}`

# STATIC - Evaluated once, won't update!
data_text=f"{counter} items"           # ❌ Wrong! Static string
# → "Signal('counter', 0) items"      # Literally shows "Signal"!
```

**When to use each:**
- `+` operator: Simple concatenation with 1-2 variables
- `f()` helper: Complex templates with multiple variables or formatting
- f-strings: ONLY for static content that never updates

### Advanced Toggle Patterns

```python
# Multi-state cycling (3+ values)
data_on_click=status.toggle("draft", "review", "approved", "published")
# Cycles: draft → review → approved → published → draft

# Conditional toggle
data_on_click=can_edit.then(status.toggle("draft", "published"))
# Only toggles if can_edit is true

# Toggle with validation
data_on_click=(form_valid & ~submitting).then(active.toggle())
```

### Using Pythonic Built-ins

```python
# OLD - JavaScript logical expressions
**ds_show("$a && $b && $c")
**ds_show("$error1 || $error2 || $error3")

# NEW - Multiple options available
data_show=a & b & c                    # Operator version
data_show=all(a, b, c)                 # Pythonic version (preferred)
data_show=any(error1, error2, error3)  # More readable than operators
```

### Advanced Modifier Patterns

```python
# Three ways to specify modifiers:

# 1. Dictionary literal syntax
data_on_click=(action, {"prevent": True, "once": True})
data_on_input=(search, {"debounce": 300, "throttle": 100})

# 2. dict() constructor syntax
data_on_click=(action, dict(prevent=True, once=True))
data_on_input=(search, dict(debounce=300, throttle=100))

# 3. .with_() method syntax (only on Expr objects)
data_on_click=action.with_(prevent=True, once=True)  # action must be an Expr
data_on_input=search.with_(debounce=300, throttle=100)  # search must be an Expr

# Different modifier value types (all syntax options support these)
{"debounce": "300ms"}     # String with units
{"threshold": 100}        # Numeric value
{"key": "Enter"}          # String literal
{"prevent": False}        # Explicit false

# Complex example showing all options
data_on_input=(
    is_valid.then(submit_form),
    {"debounce": 300, "prevent": True}
)
# OR
data_on_input=(
    is_valid.then(submit_form),
    dict(debounce=300, prevent=True)
)
# OR (if is_valid.then(submit_form) returns an Expr) 
data_on_input=is_valid.then(submit_form).with_(debounce=300, prevent=True)
```

## Common Migration Pitfalls

### 1. String Concatenation (Most Common Issue!)
```python
# WRONG - f-string is static, won't update reactively
data_text=f"{counter} items"  # Static string!

# RIGHT - Use + operator for reactive template
data_text=counter + " items"  # Creates template literal

# RIGHT - Use f() helper for complex formatting
data_text=f("{count} of {total}", count=done, total=todos.length)
```

### 2. Signal Naming
```python
# WRONG - camelCase causes ValueError
Signal("userName", "")

# RIGHT - snake_case required
Signal("user_name", "")
```

### 3. Forgetting Walrus Operator
```python
# WRONG - Signal not captured for auto-collection
counter = Signal("counter", 0)  # Won't be auto-injected!

# RIGHT - Use walrus to capture and include
(counter := Signal("counter", 0))  # Auto-collected
```

### 4. Boolean Logic
```python
# OLD - JavaScript strings
**ds_show("$a && $b && $c")

# NEW - Python operators
data_show=a & b & c

# NEW - Using all() helper
data_show=all(a, b, c)
```

### 5. Event Modifiers
```python
# OLD
**ds_on_click("handler()", "prevent", "once")

# NEW - Wrong (won't work)
data_on_click="handler()", "prevent", "once"

# NEW - Correct (tuple with dictionary literal)
data_on_click=("handler()", {"prevent": True, "once": True})

# NEW - Correct (tuple with dict() constructor)  
data_on_click=("handler()", dict(prevent=True, once=True))

# NEW - Correct (using .with_() method on js() expression)
data_on_click=js("handler()").with_(prevent=True, once=True)
```

## Testing Your Migration

1. **Check Signal Names**: Ensure all are snake_case
2. **Verify Walrus Usage**: Signals must use `:=` for auto-collection
3. **Test Reactive Updates**: Ensure dynamic content updates properly
4. **Validate Events**: Check that modifiers work correctly
5. **Review String Concatenation**: Ensure reactive strings use `+` not f-strings
6. **Verify HTML Output**: Compare before/after HTML to ensure attributes are correct
7. **Test SSE Integration**: Ensure server-sent events still update signals
8. **Check Slot Attributes**: Verify slot_attrs are targeting correct elements

## Removed Functions Reference

These old functions are completely replaced:

| Old Function | Replacement |
|--------------|------------|
| `ds_signals()` | Signal objects with walrus operator |
| `ds_show()` | `data_show=` |
| `ds_text()` | `data_text=` |
| `ds_bind()` | `data_bind=` |
| `ds_model()` | `data_model=` |
| `ds_on_*()` | `data_on_*=` |
| `ds_class()` | `data_class_*=` or `data_attr_class=` |
| `ds_style()` | `data_style_*=` or `data_attr_style=` |
| `ds_attr()` | `data_attr_*=` |
| `ds_computed()` | `Signal("name", expression)` (computed signals) |
| `ds_persist()` | `data_persist=` |
| `toggle_class()` | `.if_()` method, `match()`, `switch()`, or `collect()` |
| Global `if()` | Split into: `match()`, `switch()`, `collect()` |

## Migration Troubleshooting

### Common Errors and Solutions

#### ValueError: Signal name must be snake_case
```python
# Problem
Signal("userName", "")  # ❌ CamelCase

# Solution  
Signal("user_name", "")  # ✅ snake_case
```

#### Signal not appearing in data-signals
```python
# Problem
counter = Signal("counter", 0)  # Not captured!

# Solution
(counter := Signal("counter", 0))  # Use walrus operator
```

#### Static string instead of reactive
```python
# Problem - shows "Signal('counter', 0) items"
data_text=f"{counter} items"  

# Solution
data_text=counter + " items"  # Reactive
```

#### Type checker complains about Signal comparisons
```python
# Problem - Pyright narrows to bool
if counter == 0:  # Type: bool

# Solution - use .eq() for expressions
if counter.eq(0):  # Type: BinaryOp (expression)
```

## Performance Considerations

### Hidden Signals
Use `_ref_only=True` for signals used internally but not displayed:

```python
(cache := Signal("cache", {}, _ref_only=True))  # Not in data-signals
(temp := Signal("temp", 0, _ref_only=True))     # Internal only
```

### Computed Properties
Use computed properties for expensive calculations:

```python
# Instead of inline calculation everywhere
data_show=js("$items.filter(i => i.active).length > 0")

# Define once as computed signal
(active_count := Signal("active_count", js("$items.filter(i => i.active).length")))
data_show=active_count > 0  # Reuse computed value
```

## Getting Help

- Review working examples in `/demo/` directory (especially 01-16)
- Check test files in `/tests/unit/` for patterns
- The new API is designed to be intuitive - if something feels complex, there's likely a simpler approach