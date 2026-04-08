# StarHTML API Reference

**StarHTML provides a Pythonic API for building reactive web applications with Datastar.** Instead of writing JavaScript strings, you work with Python objects that compile to efficient JavaScript, giving you type safety, IDE support, and cleaner code.

## Core Philosophy

StarHTML follows these principles:

1. **Python First** - Write Python that feels natural and compiles to JavaScript
2. **Type Safety** - Signals know their types, enabling IDE support  
3. **Explicit is Better** - Clear, predictable APIs over magic
4. **Composable Primitives** - Small, powerful building blocks that combine well

## Quick Reference - Essential Patterns

```python
from starhtml import *

# 1. Define reactive state (walrus := for inline definition)
(counter := Signal("counter", 0))           # Define + assign in one line
(name := Signal("name", ""))                # Available throughout component
(is_visible := Signal("is_visible", True))  # All Signal() objects auto-collected  

# 2. Basic reactivity
data_show=is_visible                        # Show/hide elements
data_text=name                              # Display signal value
data_bind=name                              # Two-way form/input binding
data_class_active=is_visible                # Conditional CSS class

# 3. Event handling  
data_on_click=counter.add(1)               # Increment counter
data_on_input=name.set("")                 # Clear input
data_on_submit=post("/api/save")           # HTTP request

# 4. Signal operations
counter.add(1)                             # → $counter++
counter.set(0)                             # → $counter = 0
is_visible.toggle()                        # → $is_visible = !$is_visible
name.upper().contains("ADMIN")             # → $name.toUpperCase().includes("ADMIN")
count.default(0)                           # → ($count ?? 0)
theme.one_of("light", "dark")             # → ["light","dark"].includes($theme) ? $theme : "light"

# 5. Logical expressions
all(name, email, age)                      # All truthy → !!$name && !!$email && !!$age
any(error1, error2)                        # Any truthy → $error1 || $error2
name & email                               # Both truthy → $name && $email
~is_visible                                # Negation → !$is_visible

# 6. Conditional helpers  
status.if_("Active", "Inactive")           # Simple binary toggle (EXCLUSIVE)
match(theme, light="☀️", dark="🌙")        # Match signal value to outputs (EXCLUSIVE) 
switch([(~name, "Required"), (name.length < 2, "Too short")], default="Valid")  # First-match-wins (EXCLUSIVE)
collect([(is_active, "active"), (is_large, "lg")])  # Combine multiple classes (INCLUSIVE)
```

## Core Concepts

### Positional vs Keyword Arguments

StarHTML components follow Python's argument rules: **all positional arguments must come before any keyword arguments**.

- **Positional**: Content that goes *inside* the element (text, child elements) + setup code (signals)
- **Keywords**: Configuration of *how* the element behaves (attributes, handlers)

### ⚠️ Common Syntax Error

`SyntaxError: positional argument follows keyword argument`

```python
# ❌ ERROR: Positional after keyword
Div(
    cls="container",    # Keyword first
    "Hello World"       # ❌ Positional after keyword = SYNTAX ERROR
)

# ✅ CORRECT: Content first, then configuration
Div(
    "Hello World",      # ✅ Content (positional) first
    Button("Click"),    # ✅ More content
    
    cls="container",    # ✅ Configuration (keywords) after
    data_on_click=handler
)
```

**Rule**: Content → Configuration

### Signals - Reactive State

Signals are reactive variables that automatically update the UI when their values change.

#### Why Walrus Operator `:=`?

Signals are **setup code** - they must be positional arguments because you need to define them before using them in keywords.

**Walrus operator is preferred** because it's cleaner:

```python
# Two-step: Define then pass
counter = Signal("counter", 0)
return Div(counter, ...)  # Repetitive

# One-step: Define inline
return Div((counter := Signal("counter", 0)), ...)  # Cleaner
```

```python
Div(
    # ✅ Setup first (positional)
    (counter := Signal("counter", 0)),
    
    # ✅ Then use in configuration (keywords)
    Button("+", data_on_click=counter.add(1)),
    Span(data_text=counter)
)
```

#### Common Signal Methods

```python
counter.set(10)              # Set value
counter.add(1)               # Increment/add
counter.toggle()             # Boolean toggle
name.upper()                 # String methods
```

#### Value Guards

```python
# Nullish fallback — safe default when signal may be undefined
count.default(0)                        # → ($count ?? 0)
user.email.default("")                  # → ($user.email ?? "")
count.default(0).clamp(0, 99)           # Chains with other expressions

# Enum guard — constrain to allowed values, fallback to first (or explicit default)
theme.one_of("light", "dark")           # → (["light","dark"].includes($theme) ? $theme : "light")
theme.one_of("light", "dark", "auto", default="light")

# Practical: guard a display value
data_text=status.one_of("draft", "review", "published")

# Guard before match — ensure theme is valid, then map to classes
data_attr_class=match(theme.one_of("light", "dark"), light="bg-white", dark="bg-gray-900")
```

## Essential Reactivity

### Basic Reactive Attributes

| Attribute | Purpose | Example |
|-----------|---------|---------|
| `data_show` | Show/hide element | `data_show=is_visible` |
| `data_text` | Set text content | `data_text=message` |
| `data_bind` | Two-way binding | `data_bind=field` |
| `data_effect` | Side effects on signal changes | `data_effect=total.set(price * quantity)` |

### ⚠️ Critical: Signal Flash Prevention

**Problem**: Elements with `data_show` flash visible on page load before signals are defined.

**Solution 1: Display control (cleanest)**
```python
Div(
    "Modal content",
    style="display: none",     # Hidden by default
    data_show=is_modal_open    # Shows when signal is true
)
```

**Solution 2: Opacity transition (smooth)**  
```python
Div(
    "Modal content", 
    style="opacity: 0; transition: opacity 0.3s",  # Invisible + smooth transition
    data_style_opacity=is_modal_open.if_("1", "0") # Fades in/out
)
```

**Solution 3: CSS classes (Tailwind-friendly)**
```python
Div(
    "Modal content",
    cls="hidden",                    # Hidden by Tailwind class
    data_class_hidden=~is_modal_open # Removes 'hidden' when true
)
```

### Event Handling

**Common Events:**
```python
data_on_click=action         # Click handler
data_on_input=update_value   # Input change
data_on_submit=save_form     # Form submission
data_on_change=validate      # Value change
```

**Event Modifiers:**
```python
# Prevent default and control flow
data_on_submit=(save_form, dict(prevent=True))
data_on_click=(action, dict(stop=True, once= True))

# Debounce and throttle
data_on_input=(search, dict(debounce= 300))      # Wait 300ms after typing stops
data_on_scroll=update.with_(throttle=16)      # Max 60fps (16ms)
```

## Styling & Classes

### CSS Properties vs CSS Classes

**CSS Properties** (`style`, `data_style_*`, `data_attr_style`):
```python
# CSS properties - for colors, dimensions, positioning, etc.
style="background-color: red; font-size: 16px"          # SSR CSS properties
data_style_width=progress + "px"                        # Reactive CSS property
data_attr_style=f("background-color: {color}", color=theme_color)  # CSS template
```

**CSS Classes** (`cls`, `data_class_*`, `data_attr_class`):
```python
# CSS classes - including Tailwind, Daisy, custom classes, etc.
cls="btn bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded"  # SSR classes
data_class_active=is_active                             # Toggle single class (no special chars)
data_attr_class=theme.if_("dark:bg-gray-900 dark:text-white", "bg-white text-black")  # Class template
```

### SSR vs Reactive Attributes

| Use Case | SSR Needed? | Use This | Example |
|----------|-------------|----------|---------|
| **Toggle single class** | No | `data_class_active=signal` | Add/remove 'active' class |
| **Tailwind special chars** | No | `data_attr_class=signal.if_("hover:bg-blue-500/50", "")` | `:`, `/`, `[`, `]` characters |
| **Show/hide elements** | **Yes** | `style="display: none"` + `data_show=signal` | **Prevent flash on load** |
| **Base + toggle classes** | Yes | `cls="base"` + `data_class_*` | Button with base styles + individual toggles |
| **Base + dynamic classes** | Yes | `cls="base"` + `data_attr_cls=reactive` | Base classes preserved + reactive changes |

### Tailwind Special Characters

**For Tailwind classes with special characters (`:`, `/`, `[`, `]`), use `data_attr_class`:**

```python
# Pseudo-classes (colons)
data_attr_class=is_active.if_("hover:bg-blue-500 focus:ring-2", "")

# Opacity classes (slashes)  
data_attr_class=is_loading.if_("bg-blue-500/50 text-white/90", "bg-blue-500")

# Arbitrary values (square brackets)
data_attr_class=is_custom.if_("bg-[#1da1f2] text-[14px]", "bg-gray-500")

# Complex combinations
data_attr_class=is_button.if_("hover:bg-blue-500/75 focus:ring-2 active:scale-95", "")

# Simple class names work with data_class_*
data_class_active=is_active        # Toggles "active" class ✓
data_class_hidden=~is_visible      # Toggles "hidden" class ✓
```

**Rule: Special characters (`:`, `/`, `[`, `]`) → `data_attr_class` | Simple names → `data_class_*`**

### Class Management Patterns

```python
# ✅ SOLUTION 1: Use cls for SSR + data_class_* for reactive toggles
Button("Submit", 
    cls="btn",                    # SSR: Always present on page load
    data_class_success=is_valid,  # Reactive: Adds/removes 'success' class
    data_class_disabled=~is_valid # Reactive: Adds/removes 'disabled' class  
)

# ✅ SOLUTION 2: Use data_attr_cls for automatic base class preservation
Button("Submit", 
    cls="btn",                                                    # Base classes in HTML
    data_attr_cls=is_valid.if_("btn-success", "btn-disabled")   # Reactive classes only
)
# data_attr_cls automatically includes base classes from cls in the reactive expression

# Multiple classes support - all work with strings
cls="btn btn-primary bg-blue-500 text-white font-bold hover:bg-blue-600"
data_attr_class=is_error.if_("border-red-500 bg-red-50 text-red-700", "border-gray-300")
data_class="active selected current"  # All three classes applied together

# Dictionary syntax for conditional classes  
data_class={
    "active primary selected": user_role == "admin",
    "inactive secondary": user_role == "user", 
    "disabled pending": user_role == "guest"
}
```

## Expressions & Logic

### Operators

**Logical:**
```python
# Python operators → JavaScript
name & email                 # → $name && $email
error1 | error2              # → $error1 || $error2
~is_visible                  # → !$is_visible

# Helper functions (more readable)
all(name, email, age)        # → !!$name && !!$email && !!$age
any(error1, error2)          # → $error1 || $error2
```

**Comparisons & Math:**
```python
age >= 18                    # → $age >= 18
count == 0                   # → $count === 0
price * quantity             # → $price * $quantity
(current / total) * 100      # → ($current / $total) * 100
```

### String Concatenation (Critical!)

```python
# ⚠️ F-strings create STATIC JavaScript (evaluated once in Python)
message = f"Count: {counter}"        # → "Count: $counter" (static string)
# This won't update when counter changes in the browser!

# ✅ Use + operator for REACTIVE templates (1-2 variables)
message = "Count: " + counter        # → `Count: ${$counter}` (reactive template)
# This updates live when counter changes!

# ✅ Use f() helper for REACTIVE complex templates (3+ variables)
from starhtml.datastar import f
message = f("Hello {name}, you have {count} items", name=username, count=counter)
# → `Hello ${$username}, you have ${$counter} items` (reactive template)

# When to use each:
# - f-strings: Static text that never changes (like labels, titles)
# - + operator: Simple reactive concatenation (1-2 signals)  
# - f() helper: Complex reactive templates with multiple signals
```

### Conditional Helpers

**When to use each helper:**
- **`.if_()`** - Simple true/false choice (2 values) - **EXCLUSIVE**
- **`match()`** - Map signal value to specific outputs (like switch/case) - **EXCLUSIVE** 
- **`switch()`** - Validation chains, first-match-wins - **EXCLUSIVE**
- **`collect()`** - Combine multiple conditions/values - **INCLUSIVE** (multiple can be true)

#### .if_() - Simple True/False Choice

```python
# Simple conditional - true/false
status.if_("Active", "Inactive")     # → $status ? "Active" : "Inactive"
is_valid.if_("✓", "✗")              # → $is_valid ? "✓" : "✗"

# In practice
data_text=is_online.if_("Online", "Offline")
data_attr_class=is_error.if_("text-red-500", "text-green-500")
```

#### match() - Value-Based Mapping

```python
# Pattern matching like Python match/case
status_color = match(status,
    pending="yellow",
    approved="green", 
    rejected="red",
    default="gray"
)

# With signals in templates
data_attr_class=match(theme,
    light="bg-white text-black",
    dark="bg-gray-900 text-white",
    auto="bg-gray-100",
    default="bg-white"
)
```

#### switch() - Validation & Priority Chains

```python
# Sequential conditions (if/elif/else) - first match wins
validation_message = switch([
    (~name, "Name is required"),
    (name.length < 2, "Name too short"),
    (~email.contains("@"), "Invalid email"),
    (age < 18, "Must be 18+")
], default="Valid")

# Priority-based styling
data_attr_class=switch([
    (is_error, "bg-red-100 text-red-800"),
    (is_warning, "bg-yellow-100 text-yellow-800"),
    (is_success, "bg-green-100 text-green-800")
], default="bg-gray-100")
```

#### collect() - Combine Multiple Classes

```python
# Combines ALL true conditions (useful for CSS classes)
classes = collect([
    (is_active, "active"),
    (is_disabled, "disabled"),
    (has_error, "error"),
    (is_loading, "loading")
])  # Returns: "active error" if both are true

# Perfect for complex conditional styling
data_attr_class=collect([
    (True, "btn"),  # Always included
    (is_primary, "btn-primary"),
    (is_large, "btn-lg"),
    (is_disabled, "opacity-50 cursor-not-allowed")
])
```

## Side Effects & Computed

### Computed Properties

Computed signals are signals whose values are derived from other signals. Define them by passing an expression (not a literal value) to `Signal()`:

```python
# Define computed signals with expressions
(first := Signal("first", ""))
(last := Signal("last", ""))
(name := Signal("name", ""))
(email := Signal("email", ""))
(age := Signal("age", 0))
(price := Signal("price", 0))
(quantity := Signal("quantity", 1))
(tax_rate := Signal("tax_rate", 0.1))

# Computed signals - defined with expressions
(full_name := Signal("full_name", first + " " + last))
(is_valid := Signal("is_valid", all(name, email, age >= 18)))
(total := Signal("total", price * quantity * (1 + tax_rate)))

# Now you can reference computed signals throughout your component
Div(data_text=full_name)
Button(data_attr_disabled=~is_valid)
Span(data_text="Total: $" + total)
```

**How it works:**
- Pass a **literal value** → regular signal: `Signal("count", 0)`
- Pass an **Expr object** → computed signal: `Signal("doubled", count * 2)`
- StarHTML automatically detects the type and generates the appropriate `data-computed-*` attribute

### Side Effects with data_effect

**Purpose**: Execute expressions when signals change (for side effects, not computed values)

```python
# Update other signals based on changes
data_effect=total.set(price * quantity)           # Update total when price/quantity changes
data_effect=is_valid.set(all(name, email, age))   # Update validation when fields change

# Multiple effects (list of expressions)
data_effect=[
    total.set(price * quantity),
    discount.set(total * discount_rate),
    final_total.set(total - discount)
]

# Conditional side effects  
data_effect=is_form_complete.then(auto_save_data)

# API calls on signal changes
data_effect=search_query.length >= 3 & post("/api/search")
```

**Key Differences:**
- **Computed signals** (e.g., `Signal("doubled", count * 2)`): Returns a value (read-only, automatically updates)
- **`data_effect`**: Performs actions (assignments, API calls, DOM changes)

### HTTP Actions

Use `get()`, `post()`, `put()`, `patch()`, and `delete()` to make requests from the browser.

**Important:** Datastar automatically sends **all signals** as the request body. You don't pass user data as keyword arguments — your server-side route handler receives every signal value by default.

```python
# All signal values are sent automatically — no need to specify data
data_on_click=get("/api/data")
data_on_click=post("/api/submit")
data_on_click=delete(f"/api/items/{item_id}")  # item_id is a Python variable baked into the URL at render time

# Conditional requests
data_on_click=is_valid.then(post("/api/submit"))
```

**Sending specific data instead of all signals:**

Use the `payload` option to send only certain values. Use `js()` to reference browser-side values (like DOM events or element properties) that don't exist in Python:

```python
# Send only "text" — derived from a browser-side DOM value
data_on_blur=post("/api/edit", payload={"text": js("evt.target.innerText.trim()")})
```

**Action options:**

All keyword arguments are [Datastar action options](https://data-star.dev/reference/action_plugins/backend), not user data. Available options include `contentType`, `headers`, `payload`, `selector`, `filterSignals`, and others.

```python
# Set content type for form submissions
data_on_click=post("/api/submit", contentType="form")

# Send only signals whose names match a regex
data_on_click=post("/api/submit", filterSignals="name|email")
```

## Advanced Features

### Startup & Shutdown

Run code when your app starts (connect to a database, warm a cache) or stops (close connections, flush logs). There are four ways to register these handlers — pick whichever fits your situation.

**Constructor lists** — simplest for quick setup:

```python
app, rt = star_app(
    on_startup=[init_db, warm_cache],
    on_shutdown=[close_db],
)
```

**Lifespan context manager** — best when startup and shutdown are paired (e.g. open/close the same resource):

```python
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app):
    db = await connect_db()
    yield
    await db.close()

app, rt = star_app(lifespan=lifespan)
```

**Decorator** — register handlers after creating the app:

```python
@app.on_event("startup")
async def init_db():
    ...

@app.on_event("shutdown")
def cleanup():
    ...
```

**Programmatic** — useful when handlers come from plugins or configuration:

```python
app.add_lifecycle_handler("startup", init_db)
app.add_lifecycle_handler("shutdown", close_db)
```

All handlers can be sync or async, and can optionally accept the `app` instance as a parameter.

**Combining approaches**: You can use a lifespan context manager *and* individual handlers together. The handlers run inside the lifespan context, so they can access any resources it initializes (e.g. a database connection created in the lifespan is available to startup handlers).

### Slot Attributes System

```python
def Modal(content, **kwargs):
    return Div(
        Div(data_slot="header"),
        Div(content, data_slot="body"),
        Div(data_slot="footer"),
        
        # Apply attributes to slotted elements
        slot_header=dict(
            data_attr_class="modal-header",
            data_show=show_header
        ),
        slot_body=dict(
            data_attr_class=expanded.if_("modal-body-expanded", "modal-body")
        ),
        slot_footer=dict(
            data_show=has_actions
        ),
        cls="modal",
        **kwargs
    )
```

### Icon Component

StarHTML provides an `Icon()` component with two rendering modes: **CDN mode** (default) uses the Iconify web component, while **inline mode** renders server-side SVGs for zero JavaScript, zero layout shift, and offline support.

#### Basic Usage

```python
from starhtml import *

# Icons use "prefix:name" format from any Iconify-compatible set
Icon("lucide:home")                    # Lucide icon
Icon("mdi:account")                    # Material Design
Icon("ph:star")                        # Phosphor
Icon("tabler:settings")               # Tabler
```

#### Sizing

```python
# Explicit size (applied to both width and height)
Icon("lucide:home", size=24)           # 24px
Icon("lucide:home", size="1.5rem")     # 1.5rem

# Separate width/height
Icon("lucide:home", width=32, height=24)

# Tailwind size classes (extracted automatically)
Icon("lucide:home", cls="size-6")      # 1.5rem from Tailwind mapping
Icon("lucide:home", cls="w-8 h-8")    # 2rem
Icon("lucide:home", cls="size-[2rem]") # Arbitrary value

# No size specified → defaults to 1em (inherits from font size)
Icon("lucide:home")
```

#### Color & Styling

```python
# Colors inherit via currentColor — use text-* classes
Icon("lucide:heart", cls="text-red-500 size-6")
Icon("lucide:star", cls="text-amber-400 size-5")

# Spacing classes work on the wrapper span
Icon("lucide:home", cls="mr-2")

# In buttons
Button(
    Icon("lucide:download", cls="size-4 mr-2"),
    "Download",
    cls="inline-flex items-center px-4 py-2 bg-blue-600 text-white rounded",
)
```

#### Inline SVG Mode

By default, icons use the Iconify CDN web component. For production, enable inline SVGs:

```python
# Option 1: In code
app, rt = star_app(inline_icons=True)

# Option 2: Environment variable (overrides code setting)
# STARHTML_INLINE_ICONS=1  (accepts: 1, true, yes — case-insensitive)
```

**CDN mode** (default): Renders `<iconify-icon>` web components. Requires JavaScript; icons are fetched client-side on first load. Good for development.

**Inline mode**: Renders `<svg>` elements directly in HTML. Zero JavaScript, zero layout shift, works offline. Better for production.

#### How Caching Works

No extra setup needed — just use `Icon()` normally. Icons are resolved through a 2-tier cache with an API fallback:

| Layer | Source | When |
|-------|--------|------|
| Memory | In-process dict | After first access |
| Disk | `<project_root>/.starhtml/icons/{prefix}.json` | Memory miss |
| API (fallback) | `api.iconify.design` | Disk miss in dev — fetched once, then cached to disk |

The project root is detected by walking up from CWD looking for `pyproject.toml` (same heuristic as uv/ruff/pytest). Icons are cached to `<project_root>/.starhtml/icons/`.

When `inline_icons=True`, all cached icons are preloaded into memory at startup — no disk I/O on first request.

#### Production Workflow

This follows the same pattern as Astro, Nuxt, and other frameworks: **scan at build time, serve from local cache at runtime.** No runtime API calls in production.

```bash
# In CI/CD or before deploy: scan source and pre-cache all icons
starhtml icons scan web/ src/

# Commit the cache or bake into Docker image
git add .starhtml/icons/

# In production: inline_icons=True loads from disk cache at startup
# Zero API calls, zero external dependencies
```

The scan uses a regex to find literal `Icon("prefix:name")` calls in your `.py` files and batch-fetches any missing icons from the Iconify API (one request per prefix). Re-running skips already-cached icons. Dynamically constructed icon names (e.g., `Icon(f"{prefix}:home")` or `Icon(variable)`) are not detected — register these manually with `resolver.register()`.

Common non-production directories (`tests/`, `.venv/`, `__pycache__/`, `node_modules/`, `build/`, `dist/`, etc.) are excluded by default so test fixtures and third-party code don't trigger unnecessary fetches.

```bash
# Add extra exclude patterns (glob syntax, repeatable)
starhtml icons scan --exclude "*/fixtures/*.py" --exclude "demos/*"

# Disable default excludes to scan everything
starhtml icons scan --no-default-excludes
```

**Development** requires no setup — icons are fetched from the API on first use and cached automatically.

#### Custom Icons

```python
from starhtml.icons import resolver, IconData

# Register a custom SVG icon (e.g. your own logo)
resolver.register("custom", "logo", IconData(body='<path d="M..."/>', width=24, height=24))
Icon("custom:logo")  # Works like any other icon
```

#### CLS Prevention

The `Icon()` wrapper `<span>` reserves space with `display:inline-block`, `flex-shrink:0`, `vertical-align:middle`, `line-height:0`, and explicit width/height. This prevents layout shift whether using CDN or inline mode.

```python
# stable=True (default) — wrapper span with reserved space
Icon("lucide:home")

# stable=False — bare <iconify-icon> (CDN) or raw <svg> (inline), no wrapper span
Icon("lucide:home", stable=False)
```

### Handler System

```python
# Built-in handlers for common patterns
drag_handler()         # Drag & drop functionality
scroll_handler()       # Scroll position tracking
resize_handler()       # Window resize events
canvas_handler()       # Canvas drawing utilities
position_handler()     # Element positioning
persist_handler()      # LocalStorage persistence
```

### JavaScript Integration

#### js() - Raw JavaScript

```python
# Execute arbitrary JavaScript when needed
(timestamp := Signal("timestamp", js("Date.now()")))
data_on_click=js("confirm('Are you sure?') && deleteItem()")

# Browser APIs
data_effect=js("navigator.clipboard.writeText($message)")
js("document.querySelector('#modal').showModal()")

# Complex expressions
(filtered := Signal("filtered", js("$todos.filter(t => t.completed)")))
```

#### value() - Literal Values

```python
# Force Python values to be treated as JavaScript literals
# (Rarely needed - typically you just pass literals directly to Signal())
(pi := Signal("pi", value(3.14159)))              # Always 3.14159, never a signal reference
(config := Signal("config", value({"theme": "dark", "lang": "en"})))  # Static object
(items := Signal("items", value([1, 2, 3, 4])))     # Static array

# More commonly: just pass literals directly (they're not expressions)
(pi := Signal("pi", 3.14159))                     # Same as above
(config := Signal("config", {"theme": "dark"}))   # Same as above
```

#### regex() - Regular Expressions

```python
# Create JavaScript regex patterns
regex(r"^\d{3}-\d{4}$")       # → /^\d{3}-\d{4}$/
regex("^todo_")               # → /^todo_/

# Use in expressions
data_show=email.match(regex(r"^[^@]+@[^@]+\.[^@]+$"))
```

#### Global JavaScript Objects

```python
# Pre-defined for direct use
console.log("Debug:", message)
Math.round(value)
Math.random()
JSON.stringify(data)
Date.now()
Object.keys(obj)
Array.isArray(items)
```

## Best Practices

### 1. Signal Organization

Define signals inline where they're used for clarity:

```python
def component():
    return Div(
        # Define signals inline where they're needed
        Input(
            (name := Signal("name", "")),     # Define here, use throughout component
            data_bind=name
        ),
        Input(
            (email := Signal("email", "")),   # Each field owns its signal
            data_bind=email
        ),
        Button(
            (is_valid := Signal("is_valid", False)),  # Inline definition
            "Submit", 
            data_attr_disabled=~is_valid
        )
    )
```

### 2. Naming Conventions

Use descriptive, snake_case names:

```python
# ✅ Good
(user_name := Signal("user_name", ""))
(is_logged_in := Signal("is_logged_in", False))
(total_count := Signal("total_count", 0))

# ❌ Bad
(n := Signal("n", ""))           # Too short
(userName := Signal("userName", ""))  # Wrong case (will error)
```

### 3. Avoid Static Strings for Dynamic Content

```python
# ❌ Wrong - won't update
data_text=f"Count: {counter}"  # Static f-string!

# ✅ Right - will update
data_text="Count: " + counter  # Reactive concatenation
data_text=f("Count: {c}", c=counter)  # Reactive template
```

### 4. Use Helper Functions for Readability

```python
# ✅ Good - readable and clear
data_show=all(name, email, age >= 18)
data_class_error=any(name_error, email_error)

# ❌ Less clear
data_show=name & email & (age >= 18)
```

### 5. Flash Prevention for Modals

```python
# ✅ Always start hidden to prevent flash
Div(
    "Modal content",
    style="display: none",     # Hidden by default
    data_show=is_modal_open    # Shows when signal is true
)
```

### 6. Performance Optimization

```python
# ✅ Use _ref_only for internal signals
(cache := Signal("cache", {}, _ref_only=True))  # Not in data-signals output

# ✅ Throttle high-frequency events
data_on_scroll=(update_position, {"throttle": 100})   # Max 10 times/sec
data_on_input=(search, {"debounce": 300})             # Wait 300ms after typing
```

## Complete Examples

### Contact Form with Validation

```python
from starhtml import *

app, rt = star_app()

@rt("/")
def home():
    # Create signals for each form field
    name = Signal("name", "")
    em = Signal("email", "")
    message = Signal("message", "")

    # .validate() attaches a validation rule and returns attrs
    # (data-bind, blur/input handlers, aria-invalid) to spread into the Input
    name_v = name.validate(min_length, 2, "Name")
    em_v = em.validate(email)

    # form_submit() wires everything together:
    #   - Runs all validations on submit, POSTs only if all pass
    #   - Auto-creates contact_submitting / contact_submitted / contact_error signals
    #   - reset_on_success clears listed signals after a successful submit
    # Only validated signals need to be listed here — message has no rules.
    fs = form_submit("/submit", name, em, name="contact", reset_on_success=True)

    return Div(
        name, em, message,   # Place signals to emit their data-signals attrs

        Form(
            fs,              # FormAttrs dict — sets action, method, data-on-submit, etc.

            # Spread name_v into Input to get two-way binding + validation
            Div(
                Label("Name", fr="name"),
                Input(name_v, type="text", id="name", name="name", cls="form-input"),
                # name.err is the auto-created error signal (empty string = no error)
                Span(data_text=name.err, data_show=name.err, cls="error-text"),
            ),

            # Email field — same pattern
            Div(
                Label("Email", fr="email"),
                Input(em_v, type="email", id="email", name="email", cls="form-input"),
                Span(data_text=em.err, data_show=em.err, cls="error-text"),
            ),

            # Message — no validation, just two-way binding via data_bind
            Div(
                Label("Message", fr="message"),
                Textarea(data_bind=message, id="message", name="message", rows="4", cls="form-input"),
            ),

            # fs.submitting is a Signal — use it for loading state
            Button(
                data_text=fs.submitting.if_("Sending...", "Send Message"),
                type="submit",
                data_attr_disabled=fs.submitting,
                cls="btn btn-primary",
            ),
        ),
        cls="contact-form",
    )

@rt("/submit", methods=["POST"])
@sse
async def submit_form(name: str = "", email: str = "", message: str = ""):
    import asyncio
    # Show loading state on the button
    yield signals(contact_submitting=True)
    await asyncio.sleep(0.5)  # Simulate work
    # End loading and mark success — reset_on_success will clear the form
    yield signals(contact_submitting=False, contact_submitted=True)
```

### Chat with Server-Sent Events (SSE)

```python
from starhtml import *
import time

def chat_app():
    message = Signal("message", "")
    sending = Signal("sending", False)

    return Div(
        message, sending,  # Signals render as hidden setup attributes
        
        H1("Live Chat"),
        
        # Messages container
        Div(id="messages", cls="messages-container"),
        
        # Chat input form
        Form(
            Input(
                placeholder="Type your message...",
                data_bind=message,           # Two-way bind to message signal
                data_attr_disabled=sending,   # Disable while sending
                cls="message-input"
            ),
            
            Button(
                data_text=sending.if_("Sending...", "Send"),
                type="submit",
                data_attr_disabled=sending | ~message,  # Disabled when sending or empty
                cls="send-button"
            ),
            
            # post() sends all current signal values to the server
            data_on_submit=(post("/chat/send"), {"prevent": True}),
            cls="chat-form"
        ),
        
        cls="chat-app"
    )

# @sse makes the handler yield SSE events instead of returning a response
@rt("/chat/send", methods=["POST"])
@sse
def send_message(message: str = ""):  # Signal values arrive as parameters
    # Update sending signal on the client
    yield signals(sending=True)
    
    time.sleep(0.5)  # Simulated delay
    
    # Append user message to chat
    yield elements(
        Div(
            Span("You", cls="username"),
            Span(message, cls="message-text"),
            Span(time.strftime("%H:%M"), cls="timestamp"),
            cls="message user-message"
        ),
        "#messages", "append"
    )
    
    time.sleep(1)  # Simulated delay
    
    # Append bot response
    yield elements(
        Div(
            Span("Bot", cls="username"),
            Span(f"Echo: {message}", cls="message-text"),
            Span(time.strftime("%H:%M"), cls="timestamp"),
            cls="message bot-message"
        ),
        "#messages", "append"
    )
    
    # Clear input and reset sending state
    yield signals(message="", sending=False)

# ⚠️ SSE Best Practice: When replacing elements (not appending),
# preserve the id so the selector keeps working for future updates:
#
# yield elements(
#     Div("New content", id="messages", cls="messages-container"),
#     "#messages"  # Replacement still has id="messages"
# )
```

---

This comprehensive API reference covers most StarHTML features with practical examples, best practices, and common pitfalls. Use the quick reference for immediate needs, then dive deeper into specific sections as required.
