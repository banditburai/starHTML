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
data_effect=search_query.length >= 3 & post("/api/search", q=search_query)
```

**Key Differences:**
- **Computed signals** (e.g., `Signal("doubled", count * 2)`): Returns a value (read-only, automatically updates)
- **`data_effect`**: Performs actions (assignments, API calls, DOM changes)

### HTTP Actions

```python
# Simple requests
data_on_click=get("/api/data")
data_on_click=post("/api/submit")
data_on_click=delete(f"/api/items/{item_id}")

# With parameters
data_on_click=get("/api/search", q=search_term)
data_on_click=post("/api/contact", name=name, email=email)

# Conditional requests
data_on_click=is_valid.then(post("/api/submit", data=form_data))
```

## Advanced Features

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

def contact_form():
    return Form(
        H2("Contact Us"),
        
        # Name field with inline signal definition
        Div(
            Label("Name", for_="name"),
        Input(
                (name := Signal("name", "")),         # Define signal inline
                type="text",
                id="name",
            data_bind=name,
                data_on_input=(name_error := Signal("name_error", "")).set(
                switch([
                        (~name, "Name is required"),
                        (name.length < 2, "Name too short")
                    ], default="")
                ),
                cls="form-input",
            data_class_error=name_error
        ),
            Span(data_text=name_error, data_show=name_error, cls="error-text")
        ),
        
        # Email field with inline signal definition
        Div(
            Label("Email", for_="email"),
        Input(
                (email := Signal("email", "")),       # Define signal inline
            type="email",
                id="email", 
            data_bind=email,
                data_on_input=(email_error := Signal("email_error", "")).set(
                    switch([
                        (~email, "Email is required"),
                        (~email.contains("@"), "Invalid email format")
                    ], default="")
                ),
                cls="form-input",
                data_class_error=email_error
            ),
            Span(data_text=email_error, data_show=email_error, cls="error-text")
        ),
        
        # Message field
        Div(
            Label("Message", for_="message"),
        Textarea(
                (message := Signal("message", "")),   # Define signal inline
                id="message",
            data_bind=message,
                rows="4",
                cls="form-input"
            )
        ),
        
        # Submit button
        Button(
            (is_submitting := Signal("is_submitting", False)),  # Define inline
            data_text=is_submitting.if_("Sending...", "Send Message"),
            type="submit",
            data_attr_disabled=is_submitting | name_error | email_error | ~all(name, email, message),
            cls="btn btn-primary"
        ),
        
        # Form submission
        data_on_submit=([
            is_submitting.set(True),
            post("/api/contact", name=name, email=email, message=message)
        ], {"prevent": True}),
        
        cls="contact-form"
    )
```

### Chat with Server-Sent Events (SSE)

```python
from starhtml import *

def chat_app():
    return Div(
        H1("Live Chat"),
        
        # Messages container
        Div(
            id="messages",
            cls="messages-container"
        ),
        
        # Chat input form
        Form(
            Input(
                (message := Signal("message", "")),
                (sending := Signal("sending", False)),
                placeholder="Type your message...",
                data_bind=message,
                data_attr_disabled=sending,
                cls="message-input"
            ),
            
            Button(
                data_text=sending.if_("Sending...", "Send"),
                type="submit",
                data_attr_disabled=sending | ~message,
                cls="send-button"
            ),
            
            # Submit triggers SSE endpoint
            data_on_submit=(post("/chat/send", text=message), {"prevent": True}),
            cls="chat-form"
        ),
        
        cls="chat-app"
    )

# SSE endpoint for sending messages
@rt("/chat/send", methods=["POST"])
@sse
def send_message(message: str = ""):
    import time
    
    # Show sending state
    yield signals(sending=True)
    
    # Simulate message processing
    time.sleep(0.5)
    
    # Add message to chat
    message_element = Div(
        Span("You", cls="username"),
        Span(message, cls="message-text"),
        Span(time.strftime("%H:%M"), cls="timestamp"),
        cls="message user-message"
    )
    
    # Append new message to chat
    yield elements(message_element, "#messages", "append")
    
    # Simulate server response
    time.sleep(1)
    
    # Add bot response
    bot_response = Div(
        Span("Bot", cls="username"),
        Span(f"Echo: {message}", cls="message-text"),
        Span(time.strftime("%H:%M"), cls="timestamp"),
        cls="message bot-message"
    )
    
    yield elements(bot_response, "#messages", "append")
    
    # Clear form and reset state
    yield signals(
        message="",      # Clear input
        sending=False    # Reset sending state
    )

# ⚠️ SSE Best Practice: When replacing elements (not appending), 
# always preserve id attributes to allow future targeting:
# 
# yield elements(
#     Div("New content", id="messages", cls="messages-container"),
#     "#messages"  # ← Same id preserved in replacement
# )
```

---

This comprehensive API reference covers most StarHTML features with practical examples, best practices, and common pitfalls. Use the quick reference for immediate needs, then dive deeper into specific sections as required.
