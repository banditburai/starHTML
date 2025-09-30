"""Complex Modifier (.with_()) Usage - Advanced Examples

Demonstrates sophisticated usage of the .with_() method for adding modifiers
to expressions, including custom modifiers for plugins, event handling,
and advanced interaction patterns.
"""

from starhtml import *

app, rt = star_app(
    title="Complex Modifier Usage",
    hdrs=[
        Script(src="https://cdn.jsdelivr.net/npm/@tailwindcss/browser@4"),
        Style(
            """body{background:#fff;color:#000;margin:0;padding:0;-webkit-font-smoothing:antialiased;-moz-osx-font-smoothing:grayscale}::selection{background:#000;color:#fff}.form-field{margin-bottom:16px}.error-message{color:#dc2626;font-size:14px;margin-top:4px}.success-message{color:#059669;font-size:14px;margin-top:4px}.loading-indicator{display:inline-block;width:16px;height:16px;border:2px solid #e5e7eb;border-radius:50%;border-top-color:#3b82f6;animation:spin 1s linear infinite}@keyframes spin{to{transform:rotate(360deg)}}"""
        ),
    ],
    iconify=True,
    compression=False,
)


@rt("/")
def home():
    return Div(
        # Header section with large number
        Div(
            H1("19", cls="text-8xl font-black text-gray-100 leading-none"),
            H1("Complex Modifiers", cls="text-5xl md:text-6xl font-bold text-black mt-2"),
            P("Advanced .with_() modifier patterns for event handling", cls="text-lg text-gray-600 mt-4"),
            cls="mb-16",
        ),
        # === 1. EVENT MODIFIERS ===
        Div(
            H3("Event Modifiers", cls="text-2xl font-bold text-black mb-6"),
            P(
                "Using .with_() to modify event behavior with prevent, stop, debounce, throttle",
                cls="text-gray-600 mb-6",
            ),
            # Prevent & Stop Propagation
            Div(
                H3("Prevent Default & Stop Propagation", cls="text-lg font-medium mb-3"),
                # Explanation box
                Div(
                    P("🎯 What these modifiers do:", cls="font-medium mb-2"),
                    Ul(
                        Li(
                            "prevent=True → Stops browser's default action (form submit, link navigation, etc.)",
                            cls="mb-1",
                        ),
                        Li("stop=True → Stops event from bubbling up to parent elements", cls="mb-1"),
                        cls="list-disc list-inside text-sm",
                    ),
                    cls="bg-gray-50 p-3 rounded mb-4",
                ),
                Div(
                    (form_data := Signal("form_data", "")),
                    (form_dirty := Signal("form_dirty", False)),
                    # Form that prevents default submission
                    P("Try submitting this form - it won't reload the page:", cls="text-sm text-gray-600 mb-2"),
                    Form(
                        Input(
                            placeholder="Type something here...",
                            data_bind=form_data,
                            data_on_input=form_dirty.set(True),
                            cls="w-full p-3 border rounded-lg",
                        ),
                        Button(
                            "Submit Form",
                            # Prevent form submission, handle with JS instead
                            data_on_click=js("console.log('Form submitted with data:', $form_data)").with_(
                                prevent=True
                            ),
                            type="submit",
                            cls="mt-2 px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600",
                        ),
                        cls="space-y-2",
                    ),
                    P("✅ Check console: Form data logged but page didn't reload!", cls="text-sm text-green-600 mt-2"),
                    P(
                        "Without prevent=True, the form would submit and reload/navigate away",
                        cls="text-xs text-gray-500 mt-1",
                    ),
                    # Separator
                    Hr(cls="my-6"),
                    # Event bubbling example
                    P("Click the inner element to see stop propagation in action:", cls="text-sm text-gray-600 mb-2"),
                    Div(
                        "Outer container (click me) → logs 'Outer clicked'",
                        Div(
                            "Inner element (click me) → logs 'Inner clicked' ONLY",
                            data_on_click=js("console.log('Inner clicked')").with_(stop=True),
                            cls="bg-red-100 p-2 m-2 rounded cursor-pointer",
                        ),
                        data_on_click=js("console.log('Outer clicked')"),
                        cls="bg-blue-100 p-4 rounded cursor-pointer mt-4",
                    ),
                    P(
                        "✓ Clicking inner element won't trigger outer's click handler",
                        cls="text-sm text-green-600 mt-2",
                    ),
                    cls="p-6 bg-gray-50 rounded-lg",
                ),
                cls="mb-8",
            ),
            # Throttling Example
            Div(
                H3("Throttling for Performance", cls="text-lg font-medium mb-3"),
                Div(
                    (click_count := Signal("click_count", 0)),
                    # Throttled button
                    Div(
                        Label("Rate-Limited Button", cls="block font-medium mb-2"),
                        Button(
                            "Click Me Rapidly",
                            # Throttle clicks to max once per second
                            data_on_click=click_count.set(click_count + 1).with_(throttle=1000),
                            cls="px-4 py-2 bg-green-500 text-white rounded hover:bg-green-600",
                        ),
                        P("Clicks registered: ", Span(data_text=click_count, cls="font-bold text-2xl"), cls="mt-2"),
                        P("⚡ Throttled to 1 click per second maximum", cls="text-sm text-gray-600"),
                        P(
                            "Use throttle for: API calls, scroll events, resize handlers",
                            cls="text-xs text-gray-500 mt-1",
                        ),
                    ),
                    cls="p-6 bg-gray-50 rounded-lg",
                ),
                cls="mb-8",
            ),
            cls="mb-12 p-8 bg-white border border-gray-200",
        ),
        # === 2. KEYBOARD MODIFIERS ===
        Div(
            H3("Keyboard Modifiers", cls="text-2xl font-bold text-black mb-6"),
            P("Handle specific key combinations and keyboard events", cls="text-gray-600 mb-6"),
            Div(
                H3("Key-Specific Handlers", cls="text-lg font-medium mb-3"),
                Div(
                    (enter_input := Signal("enter_input", "")),
                    (search_query := Signal("search_query", "")),
                    (last_key := Signal("last_key", "")),
                    # Enter key handling
                    Div(
                        Label("Press Enter to Submit", cls="block font-medium mb-2"),
                        Input(
                            placeholder="Type and press Enter...",
                            data_bind=enter_input,
                            # Only trigger on Enter key
                            data_on_keydown=js("console.log('Enter pressed with:', $enter_input)").with_(key="Enter"),
                            cls="w-full p-3 border rounded-lg",
                        ),
                    ),
                    # Escape key handling
                    Div(
                        Label("Press Escape to Clear", cls="block font-medium mb-2 mt-4"),
                        Input(
                            placeholder="Type and press Escape to clear...",
                            data_bind=search_query,
                            # Clear on Escape key only
                            data_on_keydown=js("if (evt.key === 'Escape') { $search_query = ''; }"),
                            cls="w-full p-3 border rounded-lg",
                        ),
                    ),
                    # Key combination tracking
                    Div(
                        Label("Any Key Tracker", cls="block font-medium mb-2 mt-4"),
                        Input(
                            placeholder="Press any key...",
                            # Track last key pressed
                            data_on_keydown=last_key.set(js("evt.key")),
                            cls="w-full p-3 border rounded-lg",
                        ),
                        P(
                            "Last key: ",
                            Span(data_text=last_key, cls="font-mono bg-gray-100 px-2 py-1 rounded"),
                            cls="mt-2",
                        ),
                    ),
                    cls="p-6 bg-gray-50 rounded-lg",
                ),
                cls="mb-8",
            ),
            cls="mb-12 p-8 bg-white border border-gray-200",
        ),
        # === 3. ADVANCED MODIFIER PATTERNS ===
        Div(
            H3("Advanced Modifier Patterns", cls="text-2xl font-bold text-black mb-6"),
            P("Using multiple modifiers together for complex interactions", cls="text-gray-600 mb-6"),
            # One-time events
            Div(
                H3("Special Event Modifiers", cls="text-lg font-medium mb-3"),
                P("Modifiers that control how and when events fire", cls="text-gray-600 mb-4"),
                Div(
                    (scroll_position := Signal("scroll_position", 0)),
                    (menu_open := Signal("menu_open", False)),
                    # Once modifier example
                    Div(
                        Label("Click for a one-time welcome message", cls="block font-medium mb-2"),
                        Button(
                            "Show Welcome (Works Only Once)",
                            data_on_click=js("alert('Welcome! This message only shows once.')").with_(once=True),
                            cls="px-4 py-2 bg-purple-500 text-white rounded hover:bg-purple-600",
                        ),
                        P(
                            "The 'once' modifier ensures the event only fires on first click",
                            cls="text-sm text-gray-600 mt-2",
                        ),
                    ),
                    # Passive modifier for scroll performance
                    Div(
                        Label("High-Performance Scroll Area", cls="block font-medium mb-2 mt-6"),
                        Div(
                            "Scroll me! (with passive listener for better performance)",
                            *[P(f"Line {i}", cls="py-1") for i in range(20)],
                            data_on_scroll=scroll_position.set(js("evt.target.scrollTop")).with_(
                                passive=True,  # Won't block scrolling
                                throttle=100,  # Limit updates
                            ),
                            cls="h-32 overflow-y-auto bg-gray-100 p-4 rounded",
                            style="overscroll-behavior: contain;",
                        ),
                        P(
                            "Scroll position: ",
                            Span(data_text=scroll_position, cls="font-mono"),
                            "px",
                            cls="text-sm mt-2",
                        ),
                        P(
                            "Passive listeners improve scroll performance by not blocking the browser",
                            cls="text-xs text-gray-600",
                        ),
                    ),
                    # Advanced modifier combination example
                    Div(
                        Label("Modifier Combinations: Safe Form Submission", cls="block font-medium mb-2"),
                        P("Combining multiple modifiers for robust form handling", cls="text-sm text-gray-600 mb-2"),
                        Div(
                            (submit_form_data := Signal("submit_form_data", "")),
                            (submit_count := Signal("submit_count", 0)),
                            (last_submit := Signal("last_submit", "")),
                            Form(
                                Input(
                                    placeholder="Type something and hit Enter...",
                                    data_bind=submit_form_data,
                                    # Only prevent Enter key default, let other keys work normally
                                    data_on_keydown=js("""
                                        if (evt.key === 'Enter') {
                                            evt.preventDefault();
                                            $submit_count = $submit_count + 1;
                                            $last_submit = new Date().toLocaleTimeString();
                                            console.log('Form submitted via Enter key');
                                        }
                                    """),
                                    cls="w-full p-3 border rounded-lg mb-3",
                                ),
                                Button(
                                    "Submit (max once per 2 seconds)",
                                    type="submit",
                                    # Throttle the submission action
                                    data_on_click=js("""
                                        $submit_count = $submit_count + 1;
                                        $last_submit = new Date().toLocaleTimeString();
                                        console.log('Form submitted via button');
                                    """).with_(throttle=2000),
                                    cls="px-4 py-2 bg-green-500 text-white rounded hover:bg-green-600",
                                ),
                                # Prevent form's default submission behavior
                                data_on_submit=js("console.log('Form submit prevented')").with_(prevent=True),
                                cls="space-y-2",
                            ),
                            Div(
                                P("Submit count: ", Span(data_text=submit_count, cls="font-bold"), cls="text-sm"),
                                P("Last submit: ", Span(data_text=last_submit, cls="font-mono text-xs"), cls="text-sm"),
                                cls="mt-3 p-3 bg-gray-100 rounded",
                            ),
                            cls="p-4 bg-white border rounded",
                        ),
                        P(
                            "Form uses prevent on submit event, button uses throttle for rate limiting",
                            cls="text-xs text-gray-600 mt-2",
                        ),
                    ),
                    cls="p-6 bg-gray-50 rounded-lg",
                ),
                cls="mb-8",
            ),
            # Form validation example
            Div(
                H3("Form Validation with Modifiers", cls="text-lg font-medium mb-3"),
                P("Validating input and controlling form submission", cls="text-gray-600 mb-4"),
                Div(
                    (email_input := Signal("email_input", "")),
                    (validation_message := Signal("validation_message", "")),
                    (is_loading := Signal("is_loading", False)),
                    # Form with validation
                    Form(
                        Div(
                            Label("Email Address", cls="block font-medium mb-2"),
                            Input(
                                type="email",
                                placeholder="Enter email address...",
                                data_bind=email_input,
                                # Validate on blur (when clicking out)
                                data_on_blur=validation_message.set(
                                    js(
                                        "$email_input.includes('@') && $email_input.includes('.') ? 'Valid email' : ($email_input ? 'Invalid email format' : '')"
                                    )
                                ),
                                cls="w-full p-3 border rounded-lg",
                            ),
                            P("Click outside the field to validate", cls="text-xs text-gray-500 mt-1"),
                            Div(
                                data_text=validation_message,
                                data_show=(validation_message != ""),
                                data_attr_class=(validation_message == "Valid email").if_(
                                    "success-message", "error-message"
                                ),
                                cls="mt-1",
                            ),
                            cls="form-field",
                        ),
                        Button(
                            "Submit Form",
                            # Only allow submission if email is valid
                            data_on_click=js("""
                                if ($validation_message === 'Valid email') {
                                    $is_loading = true;
                                    console.log('Submitting email:', $email_input);
                                    setTimeout(() => {
                                        $is_loading = false;
                                        alert('Form submitted successfully!');
                                    }, 2000);
                                } else {
                                    alert('Please enter a valid email address');
                                }
                            """).with_(prevent=True),
                            data_attr_disabled=is_loading,
                            cls="px-4 py-2 bg-purple-500 text-white rounded hover:bg-purple-600 disabled:opacity-50",
                        ),
                        Div(
                            Span(cls="loading-indicator mr-2"),
                            "Processing your submission...",
                            data_show=is_loading,
                            cls="mt-2 text-sm text-gray-600 flex items-center",
                        ),
                        # Explanation
                        Div(
                            "💡 This example shows:",
                            Ul(
                                Li("Validation on blur (when you click out)", cls="text-sm"),
                                Li("Conditional submission based on validation", cls="text-sm"),
                                Li("Loading state only for valid submissions", cls="text-sm"),
                                cls="list-disc list-inside mt-2",
                            ),
                            cls="bg-gray-50 p-3 rounded mt-4 text-gray-700",
                        ),
                        cls="space-y-3",
                    ),
                    cls="p-6 bg-gray-50 rounded-lg",
                ),
                cls="mb-8",
            ),
            cls="mb-12 p-8 bg-white border border-gray-200",
        ),
        # === 4. REAL-WORLD PATTERNS ===
        Div(
            H3("Real-World Patterns", cls="text-2xl font-bold text-black mb-6"),
            P("Practical modifier combinations you'll use in real applications", cls="text-gray-600 mb-6"),
            Div(
                H3("Auto-Save Pattern", cls="text-lg font-medium mb-3"),
                Div(
                    (auto_save_content := Signal("auto_save_content", "")),
                    (auto_save_status := Signal("auto_save_status", "saved")),
                    # Auto-save example
                    Div(
                        Label("Document Editor with Auto-Save", cls="block font-medium mb-2"),
                        Textarea(
                            placeholder="Start typing... auto-saves 2 seconds after you stop",
                            data_bind=auto_save_content,
                            rows="5",
                            # Show typing status immediately
                            data_on_input=auto_save_status.set("typing..."),
                            # Auto-save after 2 seconds of no typing
                            data_on_keyup=js("""
                                $form_dirty = true;
                                $auto_save_status = 'saving...';
                                console.log('Auto-saving document...');
                                setTimeout(() => {
                                    $auto_save_status = 'saved ✓';
                                    $form_dirty = false;
                                    console.log('Document saved!');
                                }, 1000)
                            """).with_(
                                debounce=2000,  # Wait 2 seconds after typing stops
                            ),
                            cls="w-full p-3 border rounded-lg resize-none font-mono text-sm",
                        ),
                        Div(
                            "Status: ",
                            Span(
                                data_text=auto_save_status,
                                data_attr_class=switch(
                                    [
                                        (auto_save_status == "saved ✓", "text-green-600 font-semibold"),
                                        (auto_save_status == "saving...", "text-blue-600"),
                                        (auto_save_status == "typing...", "text-gray-500"),
                                    ],
                                    "text-gray-600",
                                ),
                                cls="font-medium",
                            ),
                            cls="mt-2 text-sm flex items-center gap-2",
                        ),
                        P("Perfect for: Blog editors, note-taking apps, form drafts", cls="text-xs text-gray-500 mt-2"),
                    ),
                    # Mouse tracking with throttling
                    (mouse_position := Signal("mouse_position", {"x": 0, "y": 0})),
                    Div(
                        Label("Mouse Position Tracker (Throttled)", cls="block font-medium mb-2 mt-6"),
                        Div(
                            "Move your mouse over this area",
                            data_on_mousemove=mouse_position.set(js("({x: evt.clientX, y: evt.clientY})")).with_(
                                throttle=50
                            ),  # 20fps max
                            cls="bg-gray-100 p-8 rounded-lg text-center min-h-[100px] cursor-crosshair",
                        ),
                        P(
                            "Mouse: x=",
                            Span(data_text=js("$mouse_position.x"), cls="font-mono"),
                            ", y=",
                            Span(data_text=js("$mouse_position.y"), cls="font-mono"),
                            cls="mt-2 text-sm",
                        ),
                    ),
                    cls="p-6 bg-gray-50 rounded-lg",
                ),
                cls="mb-8",
            ),
            cls="mb-12 p-8 bg-white border border-gray-200",
        ),
        # === BEST PRACTICES ===
        Div(
            H3("Best Practices", cls="text-2xl font-bold text-black mb-6"),
            Ul(
                Li("Use debounce (300-500ms) for search inputs and validation to avoid excessive requests", cls="mb-2"),
                Li("Use throttle (50-100ms) for high-frequency events like scroll, mousemove, or resize", cls="mb-2"),
                Li("Combine prevent=True with form submissions to handle them client-side", cls="mb-2"),
                Li("Use stop=True when you need to prevent event bubbling to parent elements", cls="mb-2"),
                Li("Use once=True for one-time actions like welcome messages or initial setup", cls="mb-2"),
                Li("Use passive=True for scroll/touch handlers to improve performance", cls="mb-2"),
                Li("Always consider the user experience impact of delays (debounce/throttle)", cls="mb-2"),
                cls="list-disc list-inside space-y-1 text-gray-700 p-6 bg-gray-50 rounded-lg",
            ),
            cls="mb-12 p-8 bg-white border border-gray-200",
        ),
        cls="max-w-5xl mx-auto px-8 sm:px-12 lg:px-16 py-16 sm:py-20 md:py-24 bg-white min-h-screen",
    )


if __name__ == "__main__":
    print("⚙️ Complex Modifier (.with_()) Usage Demo")
    print("=" * 45)
    print("🚀 Running on http://localhost:5021")
    print("✨ Features:")
    print("   • Event modifiers (prevent, stop, debounce, throttle)")
    print("   • Keyboard modifiers (key combinations)")
    print("   • Custom plugin modifiers")
    print("   • Complex chaining patterns")
    print("   • Real-world usage examples")
    serve(port=5021)
