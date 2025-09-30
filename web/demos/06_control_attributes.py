"""Demo of Datastar lifecycle and control attributes.

Showcases:
- data-ignore: Skip Datastar processing
- data-on-load: Execute on element load
- data-json-signals: Debug signal state
"""

from starhtml import *

app, rt = star_app(
    title="Datastar Control Attributes Demo",
    hdrs=[
        Script(src="https://cdn.jsdelivr.net/npm/@tailwindcss/browser@4"),
        Style("""
            body { background: white; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; -webkit-font-smoothing: antialiased; }
        """),
    ],
    iconify=True,
    compression=False,
)


@rt("/fetch-user-data")
@sse
def fetch_user_data(req, user_data: Signal):
    import time

    # Simulate API call
    time.sleep(0.5)

    # Return realistic user profile data as a dict
    # This will display nicely in both data-text and data-json-signals
    profile_data = {
        "user": {
            "id": "usr_12345",
            "name": "John Doe",
            "email": "john@example.com",
            "role": "Developer",
            "joined": "2024-01-15",
        },
        "stats": {"projects": 12, "commits": 347, "reviews": 89},
        "status": "active",
        "last_login": time.strftime("%Y-%m-%d %H:%M:%S"),
    }

    # Store as dict - Datastar will handle display formatting
    yield signals(user_data=profile_data)


@rt("/")
def home():
    return Div(
        # Main container
        Div(
            # Header with bold typography
            Div(
                H1("06", cls="text-8xl font-black text-gray-100 leading-none"),
                H1("Control Attributes", cls="text-5xl md:text-6xl font-bold text-black mt-2"),
                P("Lifecycle events, morphing control, and debugging features", cls="text-lg text-gray-600 mt-4"),
                cls="mb-16",
            ),
            # data-ignore demo
            Div(
                (counter := Signal("counter", 0)),
                (ignored_signal := Signal("ignored_signal", "This won't update!")),
                H3("data-ignore Demo", cls="text-2xl font-bold text-black mb-6"),
                P("The section below is ignored by Datastar (no reactivity):", cls="text-gray-600 mb-4"),
                Div(
                    P("This content is ignored: ", Span(data_text=ignored_signal, cls="font-medium"), cls="mb-4"),
                    Button(
                        "Won't work",
                        data_on_click=counter.add(1),
                        cls="px-4 py-2 bg-gray-400 text-white font-medium cursor-not-allowed opacity-75",
                    ),
                    data_ignore=True,
                    cls="p-6 bg-gray-100 border border-gray-200",
                ),
                Div(
                    P("This button outside works normally:", cls="text-gray-600 mb-4"),
                    Button(
                        "Increment",
                        data_on_click=counter.add(1),
                        cls="px-4 py-2 bg-black text-white font-medium hover:bg-gray-800 transition-colors mr-4",
                    ),
                    Span("Counter: ", cls="text-gray-600"),
                    Span(data_text=counter, cls="text-2xl font-bold text-black"),
                    cls="mt-4",
                ),
                cls="mb-12 p-8 bg-white border border-gray-200",
            ),
            # data-ignore with 'self' modifier demo
            Div(
                (update_time := Signal("update_time", "Not updated yet")),
                H3("data-ignore='self' Demo", cls="text-2xl font-bold text-black mb-6"),
                P("Video below won't be disrupted during morphing:", cls="text-gray-600 mb-4"),
                Video(
                    Source(src="https://www.w3schools.com/html/mov_bbb.mp4", type="video/mp4"),
                    data_ignore="self",
                    controls=True,
                    cls="w-full max-w-md border border-gray-200",
                ),
                Div(
                    Button(
                        "Update page (video keeps playing)",
                        data_on_click=update_time.set(js("new Date().toLocaleTimeString()")),
                        cls="px-4 py-2 bg-green-600 text-white font-medium hover:bg-green-700 transition-colors",
                    ),
                    Div(
                        Span("Last update: ", cls="text-gray-600"),
                        Span(data_text=update_time, cls="font-bold text-black"),
                        cls="mt-4",
                    ),
                    cls="mt-6",
                ),
                cls="mb-12 p-8 bg-gray-50",
            ),
            # data-on-load demo
            Div(
                (user_data := Signal("user_data", {})),  # Empty dict initially
                (component_status := Signal("component_status", "Initializing...")),
                (analytics_sent := Signal("analytics_sent", False)),
                H3("data-on-load Demo", cls="text-2xl font-bold text-black mb-6"),
                P("Run initialization code when elements load into the DOM:", cls="text-gray-600 mb-6"),
                # Fetch data on component load
                Div(
                    P("Auto-fetch user data on load:", cls="text-blue-700 font-medium mb-4"),
                    Pre(
                        Code(
                            data_text=js("JSON.stringify($user_data, null, 2) || 'Loading user data...'"),
                            cls="text-green-400",
                        ),
                        data_on_load=get("fetch-user-data"),
                        cls="bg-gray-900 p-4 font-mono text-sm overflow-auto whitespace-pre border border-gray-200",
                    ),
                    cls="p-6 bg-blue-50 border border-blue-200 mb-6",
                ),
                # Initialize component state with delay
                Div(
                    P("Initialize component (with 300ms delay):", cls="text-green-700 font-medium mb-4"),
                    Div(
                        Span("Status: ", cls="text-gray-600"),
                        Span(data_text=component_status, cls="font-bold text-black"),
                        data_on_load=(
                            component_status.set(js("'Component ready at ' + new Date().toLocaleTimeString()")),
                            dict(delay="300ms"),
                        ),
                    ),
                    cls="p-6 bg-green-50 border border-green-200 mb-6",
                ),
                # Track analytics on load
                Div(
                    P("Send analytics when visible:", cls="text-purple-700 font-medium mb-4"),
                    Div(
                        Span("Analytics sent: ", cls="text-gray-600"),
                        Span(data_text=analytics_sent.if_("✅ Yes", "⏳ No"), cls="font-bold text-black"),
                        data_on_load=analytics_sent.set(True),
                    ),
                    cls="p-6 bg-purple-50 border border-purple-200 mb-6",
                ),
                P(
                    "Common uses: API calls, component initialization, analytics tracking, lazy loading",
                    cls="text-sm text-gray-500 italic",
                ),
                cls="mb-12 p-8 bg-white border border-gray-200",
            ),
            # data-json-signals demo
            Div(
                H3("data-json-signals Demo (Debug View)", cls="text-2xl font-bold text-black mb-6"),
                Div(
                    P("All signals displayed as JSON:", cls="text-gray-600 mb-4"),
                    Pre(
                        data_json_signals=True,
                        cls="bg-gray-900 text-green-400 p-4 font-mono text-sm overflow-auto border border-gray-200",
                    ),
                    cls="mb-6",
                ),
                Div(
                    P("Filtered signals (only those containing 'counter' or 'time'):", cls="text-gray-600 mb-4"),
                    Pre(
                        data_json_signals=dict(include=regex("(counter|time)")),
                        cls="bg-gray-900 text-blue-400 p-4 font-mono text-sm overflow-auto border border-gray-200",
                    ),
                ),
                cls="mb-12 p-8 bg-gray-50",
            ),
            # slot_attrs demo
            Div(
                (task_done := Signal("task_done", False)),
                (item_selected := Signal("item_selected", False)),
                (form_valid := Signal("form_valid", True)),
                H3("slot_attrs Demo", cls="text-2xl font-bold text-black mb-6"),
                P("Apply attributes to multiple elements based on their data-slot:", cls="text-gray-600 mb-6"),
                # Example 1: Task list with conditional styling
                Div(
                    H4("Task Component:", cls="text-lg font-bold text-black mb-4"),
                    P("Click the checkbox - data_bind is applied via slot_task_check:", cls="text-gray-600 mb-4"),
                    Div(
                        Input(type="checkbox", data_slot="task-check", cls="w-5 h-5 cursor-pointer"),
                        Span("Complete important task", data_slot="task-text", cls="text-lg ml-4 flex-1"),
                        Span("✓", data_slot="task-mark", cls="text-2xl text-green-600 font-bold"),
                        # Slot attributes applied to matching data-slot elements
                        # The checkbox binding is applied HERE, not on the input directly!
                        slot_task_check=dict(data_bind=task_done),
                        slot_task_text=dict(
                            data_attr_class=task_done.if_("line-through text-gray-500", "text-gray-900")
                        ),
                        slot_task_mark=dict(data_show=task_done),
                        cls="flex items-center gap-3 p-6 bg-white border border-gray-200 hover:border-gray-400 transition-colors cursor-pointer",
                        data_on_click=task_done.toggle(),
                    ),
                    Div(
                        Span("Status: ", cls="text-gray-600"),
                        Span(
                            data_text=task_done.if_("✅ Task completed!", "⏳ Task pending"), cls="font-bold text-black"
                        ),
                        cls="mt-4",
                    ),
                    cls="mb-8 p-6 bg-white border border-gray-200",
                ),
                # Example 2: List items with shared hover state
                Div(
                    H4("List with Shared Hover Effects:", cls="text-lg font-bold text-black mb-4"),
                    P(
                        "Hover over items - slot attributes apply styling to ALL matching slots:",
                        cls="text-gray-600 mb-4",
                    ),
                    Div(
                        Div(
                            Span("📁", data_slot="item-icon", cls="text-xl transition-transform"),
                            Span("Projects", data_slot="item-text", cls="flex-1 font-medium mx-6"),
                            Span("12 files", data_slot="item-count", cls="text-sm text-gray-500"),
                            data_on_mouseenter=item_selected.set(True),
                            data_on_mouseleave=item_selected.set(False),
                            cls="flex items-center px-6 py-4 border border-gray-200 transition-all duration-200 hover:bg-gray-50 gap-2",
                        ),
                        Div(
                            Span("⚙️", data_slot="item-icon", cls="text-xl transition-transform"),
                            Span("Settings", data_slot="item-text", cls="flex-1 font-medium mx-6"),
                            Span("8 files", data_slot="item-count", cls="text-sm text-gray-500"),
                            data_on_mouseenter=item_selected.set(True),
                            data_on_mouseleave=item_selected.set(False),
                            cls="flex items-center px-6 py-4 border border-gray-200 border-t-0 transition-all duration-200 hover:bg-gray-50 gap-2",
                        ),
                        Div(
                            Span("📊", data_slot="item-icon", cls="text-xl transition-transform"),
                            Span("Analytics", data_slot="item-text", cls="flex-1 font-medium mx-6"),
                            Span("24 files", data_slot="item-count", cls="text-sm text-gray-500"),
                            data_on_mouseenter=item_selected.set(True),
                            data_on_mouseleave=item_selected.set(False),
                            cls="flex items-center px-6 py-4 border border-gray-200 border-t-0 transition-all duration-200 hover:bg-gray-50 gap-2",
                        ),
                        # These slot attributes apply to ALL elements with matching data-slot names
                        slot_item_icon=dict(
                            data_attr_class=item_selected.if_(
                                "text-blue-600 transform scale-125 rotate-12", "text-gray-600"
                            )
                        ),
                        slot_item_text=dict(
                            data_attr_class=item_selected.if_("text-blue-700 font-semibold", "text-gray-700")
                        ),
                        slot_item_count=dict(
                            data_attr_class=item_selected.if_("text-blue-500 font-medium", "text-gray-500")
                        ),
                        cls="bg-white",
                    ),
                    P(
                        "Notice: ALL icons, text, and counts change together when hovering ANY item",
                        cls="mt-4 text-sm text-gray-500 italic",
                    ),
                    cls="mb-8 p-6 bg-gray-50 border border-gray-200",
                ),
                # Example 3: Form with multiple slot attributes
                Div(
                    H4("Form with Validation States:", cls="text-lg font-bold text-black mb-4"),
                    P("Toggle form validity to see multiple slot attributes in action:", cls="text-gray-600 mb-4"),
                    Form(
                        Div(
                            Label("Username:", cls="block text-sm font-medium mb-2 text-gray-700"),
                            Input(
                                type="text",
                                placeholder="Enter username",
                                data_slot="form-input",
                                cls="w-full px-3 py-2 border border-gray-300 focus:border-gray-500 focus:outline-none transition-colors",
                            ),
                            cls="mb-4",
                        ),
                        Div(
                            Label("Email:", cls="block text-sm font-medium mb-2 text-gray-700"),
                            Input(
                                type="email",
                                placeholder="Enter email",
                                data_slot="form-input",
                                cls="w-full px-3 py-2 border border-gray-300 focus:border-gray-500 focus:outline-none transition-colors",
                            ),
                            cls="mb-4",
                        ),
                        Div(
                            Span(
                                "⚠️ Please fix errors before submitting",
                                data_slot="error-message",
                                cls="text-red-600 text-sm font-medium bg-red-50 px-3 py-2 border border-red-200 inline-block",
                            ),
                            cls="mb-4",
                        ),
                        Div(
                            Button(
                                "Submit Form",
                                data_slot="submit-btn",
                                type="submit",
                                data_on_click="event.preventDefault(); alert('Form submitted!')",
                                cls="px-4 py-2 bg-black text-white font-medium hover:bg-gray-800 transition-colors disabled:bg-gray-400 disabled:cursor-not-allowed disabled:hover:bg-gray-400",
                            ),
                            cls="flex",
                        ),
                        # Slot attributes for form elements
                        slot_form_input=dict(
                            data_attr_class=form_valid.if_(
                                "w-full px-3 py-2 border border-green-400 bg-green-50 focus:border-green-500 focus:outline-none transition-colors",
                                "w-full px-3 py-2 border border-red-400 bg-red-50 focus:border-red-500 focus:outline-none transition-colors",
                            )
                        ),
                        slot_submit_btn=dict(data_attr_disabled=js("!$form_valid")),
                        slot_error_message=dict(data_show=js("!$form_valid")),
                        cls="bg-white p-6 border border-gray-200",
                    ),
                    Div(
                        Button(
                            data_text=form_valid.if_("❌ Make form invalid", "✅ Make form valid"),
                            data_on_click=form_valid.toggle(),
                            cls="px-4 py-2 border border-gray-300 text-black font-medium hover:border-gray-500 transition-colors",
                        ),
                        Div(
                            Span("Form status: ", cls="text-gray-600"),
                            Span(data_text=form_valid.if_("✅ Valid", "❌ Invalid"), cls="font-bold text-black"),
                            cls="mt-4",
                        ),
                    ),
                    cls="mb-8 p-6 bg-white border border-gray-200",
                ),
                P(
                    "Copy-paste syntax: Use slot_{name}=dict(...) with exact same attributes you'd use on elements directly!",
                    cls="text-sm text-gray-500 italic",
                ),
                cls="mb-12 p-8 bg-gray-50",
            ),
        ),
        cls="max-w-5xl mx-auto px-8 sm:px-12 lg:px-16 py-16 sm:py-20 md:py-24 bg-white min-h-screen",
    )


if __name__ == "__main__":
    print("Datastar Control Attributes Demo running on http://localhost:5001")
    serve(port=5001)
