"""Nested Property Access - From Messy to Clean

Progressively learn how to access nested object properties in StarHTML signals.
Start with common problems, then discover clean, Pythonic solutions.
"""

from starhtml import *

app, rt = star_app(
    title="Nested Property Access Demo",
    hdrs=[
        Script(src="https://cdn.jsdelivr.net/npm/@tailwindcss/browser@4"),
        Style(
            """body{background:white;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;-webkit-font-smoothing:antialiased}.code-example{background:#1e293b;color:#e2e8f0;border-radius:6px;padding:16px;font-family:'Monaco','Menlo',monospace;font-size:14px;margin:12px 0;white-space:pre;overflow-x:auto}.code-bad{background:#fef2f2;border:1px solid #fecaca;color:#991b1b}.code-good{background:#f0fdf4;border:1px solid #bbf7d0;color:#166534}.property-display{background:#f8fafc;border:1px solid #e2e8f0;border-radius:6px;padding:12px;margin:8px 0;font-family:monospace;display:flex;justify-content:space-between;align-items:center}.status-badge{padding:4px 8px;border-radius:4px;font-size:12px;font-weight:600}.status-enabled{background:#dcfce7;color:#166534}.status-disabled{background:#fee2e2;color:#991b1b}.theme-dark{background:#374151;color:#f3f4f6}.theme-light{background:#f3f4f6;color:#374151}"""
        ),
    ],
    iconify=True,
    compression=False,
)


@rt("/")
def home():
    # Define signals for examples
    user_data = Signal(
        "user_data",
        {
            "id": 123,
            "name": "John Doe",
            "profile": {
                "bio": "Software developer",
                "preferences": {"theme": "dark", "notifications": {"email": True, "push": False}},
            },
            "stats": {"posts": 42, "followers": 1337},
        },
    )

    # Toggle for showing clean vs messy code
    show_clean = Signal("show_clean", True)

    # Playground signals for experimentation
    playground_path = Signal("playground_path", "")
    playground_value = Signal("playground_value", "")

    # Extract clean intermediate variables
    profile = user_data.profile
    preferences = profile.preferences
    notifications = preferences.notifications
    stats = user_data.stats

    return Div(
        user_data,
        show_clean,
        playground_path,
        playground_value,
        # Header with design system pattern
        Div(
            H1("20", cls="text-8xl font-black text-gray-100 leading-none"),
            H1("Nested Property Access", cls="text-5xl md:text-6xl font-bold text-black mt-2"),
            P("From messy chaining to clean, Pythonic patterns", cls="text-lg text-gray-600 mt-4"),
            cls="mb-16",
        ),
        # === 1. DATA STRUCTURE ===
        Div(
            H2("📋 The Data Structure", cls="text-2xl font-bold text-black mb-6"),
            P("First, let's see what we're working with - a nested user profile object:", cls="text-gray-600 mb-6"),
            Div(
                "user_data = {\n  'id': ",
                Span(data_text=user_data.id, cls="text-blue-600"),
                ",\n  'name': '",
                Span(data_text=user_data.name, cls="text-blue-600"),
                "',\n  'profile': {\n    'bio': '",
                Span(data_text=profile.bio, cls="text-blue-600"),
                "',\n    'preferences': {\n      'theme': '",
                Span(data_text=preferences.theme, cls="text-blue-600"),
                "',\n      'notifications': {\n        'email': ",
                Span(data_text=notifications.email, cls="text-blue-600"),
                ",\n        'push': ",
                Span(data_text=notifications["push"], cls="text-blue-600"),
                "\n      }\n    }\n  },\n  'stats': {\n    'posts': ",
                Span(data_text=stats.posts, cls="text-blue-600"),
                ",\n    'followers': ",
                Span(data_text=stats.followers, cls="text-blue-600"),
                "\n  }\n}",
                cls="code-example",
            ),
            P("Now let's learn how to access this data cleanly in StarHTML templates.", cls="text-gray-600 mt-6"),
            cls="mb-12 p-8 bg-white border border-gray-200",
        ),
        # === 2. CODING APPROACHES ===
        Div(
            H2("💡 Two Approaches: Messy vs Clean", cls="text-2xl font-bold text-black mb-6"),
            P("There are two ways to access nested properties. See the difference:", cls="text-gray-600 mb-6"),
            # Toggle between messy and clean
            Div(
                Button(
                    "Show Messy Code",
                    data_on_click=show_clean.set(False),
                    data_attr_class=show_clean.if_(
                        "px-4 py-2 border border-gray-300 text-black font-medium hover:border-gray-500 transition-colors",
                        "px-4 py-2 bg-black text-white font-medium hover:bg-gray-800 transition-colors",
                    ),
                    cls="mr-2",
                ),
                Button(
                    "Show Clean Code",
                    data_on_click=show_clean.set(True),
                    data_attr_class=show_clean.if_(
                        "px-4 py-2 bg-black text-white font-medium hover:bg-gray-800 transition-colors",
                        "px-4 py-2 border border-gray-300 text-black font-medium hover:border-gray-500 transition-colors",
                    ),
                ),
                cls="mb-6",
            ),
            # Messy code example
            Div(
                "# ❌ Hard to read, error-prone, and unmaintainable\n"
                "Span(data_text=user_data.profile.preferences.theme)\n"
                "Button(data_on_click=user_data.profile.preferences.notifications.email.set(~user_data.profile.preferences.notifications.email))\n"
                "Span(data_text=user_data.profile.preferences.notifications['push'])\n"
                "Input(data_bind=user_data.profile.preferences.theme)",
                data_show=~show_clean,
                cls="code-example code-bad",
            ),
            # Clean code example
            Div(
                "# ✅ Clean, readable, and maintainable\n"
                "profile = user_data.profile\n"
                "preferences = profile.preferences\n"
                "notifications = preferences.notifications\n\n"
                "# Now use clean references:\n"
                "Span(data_text=preferences.theme)\n"
                "Button(data_on_click=notifications.email.set(~notifications.email))\n"
                "Input(data_bind=preferences.theme)",
                data_show=show_clean,
                cls="code-example code-good",
            ),
            cls="mb-12 p-8 bg-gray-50",
        ),
        # === 3. SIMPLE EXAMPLE ===
        Div(
            H2("📍 Start Simple: Top-Level Properties", cls="text-2xl font-bold text-black mb-6"),
            P("Begin with straightforward, top-level properties from our data structure:", cls="text-gray-600 mb-6"),
            Div(
                Div(
                    "👤 User ID: ",
                    Span(data_text=user_data.id, cls="font-mono font-bold text-blue-600"),
                    cls="property-display",
                ),
                Div(
                    "📛 Name: ",
                    Span(data_text=user_data.name, cls="font-mono font-bold text-blue-600"),
                    cls="property-display",
                ),
                cls="mb-6",
            ),
            Div(
                "# Direct access to top-level properties\n"
                "user_data.id    # Simple and clean\n"
                "user_data.name  # No intermediate variables needed",
                cls="code-example",
            ),
            cls="mb-12 p-8 bg-white border border-gray-200",
        ),
        # === 4. INTERMEDIATE VARIABLES ===
        Div(
            H2("🔗 Add One Level: Intermediate Variables", cls="text-2xl font-bold text-black mb-6"),
            P("When you need nested data, extract logical sections:", cls="text-gray-600 mb-6"),
            Div(
                Div(
                    "📝 Bio: ",
                    Span(data_text=profile.bio, cls="font-mono font-bold text-green-600"),
                    cls="property-display",
                ),
                Div(
                    "🎨 Theme: ",
                    Span(
                        data_text=preferences.theme,
                        data_attr_class=preferences.theme.eq("dark").if_("theme-dark", "theme-light"),
                        cls="font-mono font-bold px-3 py-1 rounded",
                    ),
                    cls="property-display",
                ),
                cls="mb-6",
            ),
            Div(
                "# Extract logical sections first\n"
                "profile = user_data.profile\n"
                "preferences = profile.preferences\n\n"
                "# Then use clean references\n"
                "profile.bio         # Much cleaner!\n"
                "preferences.theme   # Easy to read",
                cls="code-example",
            ),
            cls="mb-12 p-8 bg-gray-50",
        ),
        # === 5. GROUPED PROPERTIES ===
        Div(
            H2("📦 Group Related Data", cls="text-2xl font-bold text-black mb-6"),
            P("Extract common parents for related properties:", cls="text-gray-600 mb-6"),
            Div(
                Div(
                    "📧 Email notifications: ",
                    Span(
                        data_text=notifications.email.if_("Enabled", "Disabled"),
                        data_attr_class=notifications.email.if_("status-enabled", "status-disabled"),
                        cls="status-badge",
                    ),
                    cls="property-display",
                ),
                Div(
                    "🔔 Push notifications: ",
                    Span(
                        data_text=notifications["push"].if_("Enabled", "Disabled"),
                        data_attr_class=notifications["push"].if_("status-enabled", "status-disabled"),
                        cls="status-badge",
                    ),
                    cls="property-display",
                ),
                Div(
                    Button(
                        "Toggle Email",
                        data_on_click=notifications.email.set(~notifications.email),
                        cls="px-4 py-2 bg-black text-white font-medium hover:bg-gray-800 transition-colors mr-2",
                    ),
                    Button(
                        "Toggle Push",
                        data_on_click=notifications["push"].set(~notifications["push"]),
                        cls="px-4 py-2 bg-black text-white font-medium hover:bg-gray-800 transition-colors",
                    ),
                    cls="mt-4",
                ),
                cls="mb-6",
            ),
            Div(
                "# Group related properties under common parent\n"
                "notifications = preferences.notifications\n\n"
                "# All notification properties are now clean\n"
                "notifications.email\n"
                "notifications['push']  # Bracket notation for reserved words",
                cls="code-example",
            ),
            cls="mb-12 p-8 bg-white border border-gray-200",
        ),
        # === 6. ADVANCED: COMPUTED PROPERTIES ===
        Div(
            H2("🧮 Advanced: Computed Properties", cls="text-2xl font-bold text-black mb-6"),
            P("Combine intermediate signals with calculations:", cls="text-gray-600 mb-6"),
            Div(
                Div(
                    "📊 Posts: ",
                    Span(data_text=stats.posts, cls="font-mono font-bold text-purple-600"),
                    cls="property-display",
                ),
                Div(
                    "👥 Followers: ",
                    Div(
                        Span(data_text=stats.followers, cls="font-mono font-bold text-purple-600 mr-2"),
                        Span(data_text=(stats.followers > 1000).if_("(Popular!)"), cls="text-purple-600 font-bold"),
                        cls="flex items-center",
                    ),
                    cls="property-display",
                ),
                Div(
                    "🎯 Status: ",
                    Span(
                        data_text=(stats.followers > 1000).if_("Influencer", "Regular"),
                        cls="font-mono font-bold text-purple-600",
                    ),
                    cls="property-display",
                ),
                cls="mb-6",
            ),
            Div(
                "# Use intermediate signals in calculations\n"
                "stats = user_data.stats\n\n"
                "# Complex expressions stay readable\n"
                "(stats.followers > 1000).if_('Influencer', 'Regular')\n"
                "(stats.followers > 1000).if_('(Popular!)', '')",
                cls="code-example",
            ),
            cls="mb-12 p-8 bg-gray-50",
        ),
        # === 7. INTERACTIVE PLAYGROUND ===
        Div(
            H2("🎮 Interactive Playground", cls="text-2xl font-bold text-black mb-6"),
            P("Experiment with accessing and updating different properties:", cls="text-gray-600 mb-6"),
            Div(
                "Try these examples:",
                Div(
                    Button(
                        "user_data.name",
                        data_on_click=[
                            playground_value.set(user_data.name),
                            playground_path.set("user_data.name"),
                            js("document.getElementById('playground_input').value = null"),
                        ],
                        cls="px-3 py-1 mr-2 mb-2 text-sm bg-gray-100 hover:bg-gray-200 border border-gray-300 rounded",
                    ),
                    Button(
                        "profile.bio",
                        data_on_click=[
                            playground_value.set(profile.bio),
                            playground_path.set("profile.bio"),
                            js("document.getElementById('playground_input').value = null"),
                        ],
                        cls="px-3 py-1 mr-2 mb-2 text-sm bg-gray-100 hover:bg-gray-200 border border-gray-300 rounded",
                    ),
                    Button(
                        "preferences.theme",
                        data_on_click=[
                            playground_value.set(preferences.theme),
                            playground_path.set("preferences.theme"),
                            js("document.getElementById('playground_input').value = null"),
                        ],
                        cls="px-3 py-1 mr-2 mb-2 text-sm bg-gray-100 hover:bg-gray-200 border border-gray-300 rounded",
                    ),
                    Button(
                        "notifications.email",
                        data_on_click=[
                            playground_value.set(notifications.email),
                            playground_path.set("notifications.email"),
                            js("document.getElementById('playground_input').value = null"),
                        ],
                        cls="px-3 py-1 mr-2 mb-2 text-sm bg-gray-100 hover:bg-gray-200 border border-gray-300 rounded",
                    ),
                    Button(
                        "stats.followers",
                        data_on_click=[
                            playground_value.set(stats.followers),
                            playground_path.set("stats.followers"),
                            js("document.getElementById('playground_input').value = null"),
                        ],
                        cls="px-3 py-1 mr-2 mb-2 text-sm bg-gray-100 hover:bg-gray-200 border border-gray-300 rounded",
                    ),
                    cls="flex flex-wrap mb-6",
                ),
            ),
            Div(
                Div(
                    Label("Current path: ", cls="text-gray-600 font-medium"),
                    Span(
                        data_text=playground_path.if_(playground_path, "(click an example above)"),
                        data_attr_class=playground_path.if_("font-mono text-blue-600", "text-gray-400 italic"),
                        cls="",
                    ),
                    cls="mb-3",
                ),
                Div(
                    Label("Current value: ", cls="text-gray-600 font-medium"),
                    Span(
                        data_text=playground_value.if_(playground_value, "(no value selected)"),
                        data_attr_class=playground_value.if_("font-mono font-bold", "text-gray-400 italic"),
                        cls="",
                    ),
                    cls="mb-4",
                ),
                cls="p-4 bg-gray-50 border border-gray-200 rounded mb-6",
            ),
            Div(
                H4("Update the value:", cls="text-lg font-semibold text-black mb-3"),
                # Text input for string/number values
                Div(
                    Input(
                        id="playground_input",
                        placeholder="Enter new value",
                        cls="px-3 py-2 border border-gray-300 focus:border-gray-500 focus:outline-none flex-1 mr-3",
                    ),
                    Button(
                        "Update Name",
                        data_on_click=[
                            user_data.name.set(js("document.getElementById('playground_input').value")),
                            playground_value.set(js("document.getElementById('playground_input').value")),
                        ],
                        data_show=playground_path.eq("user_data.name"),
                        cls="px-4 py-2 bg-black text-white font-medium hover:bg-gray-800 transition-colors",
                    ),
                    Button(
                        "Update Bio",
                        data_on_click=[
                            profile.bio.set(js("document.getElementById('playground_input').value")),
                            playground_value.set(js("document.getElementById('playground_input').value")),
                        ],
                        data_show=playground_path.eq("profile.bio"),
                        cls="px-4 py-2 bg-black text-white font-medium hover:bg-gray-800 transition-colors",
                    ),
                    Button(
                        "Update Followers",
                        data_on_click=[
                            stats.followers.set(js("parseInt(document.getElementById('playground_input').value) || 0")),
                            playground_value.set(
                                js("parseInt(document.getElementById('playground_input').value) || 0")
                            ),
                        ],
                        data_show=playground_path.eq("stats.followers"),
                        cls="px-4 py-2 bg-black text-white font-medium hover:bg-gray-800 transition-colors",
                    ),
                    data_show=(
                        playground_path.eq("user_data.name")
                        | playground_path.eq("profile.bio")
                        | playground_path.eq("stats.followers")
                    ),
                    cls="flex items-center mb-4",
                ),
                # Theme toggle buttons (only show opposite of current)
                Div(
                    Button(
                        "Switch to Light Theme",
                        data_on_click=[preferences.theme.set("light"), playground_value.set("light")],
                        data_show=(playground_path.eq("preferences.theme") & preferences.theme.eq("dark")),
                        cls="px-4 py-2 bg-black text-white font-medium hover:bg-gray-800 transition-colors mr-2",
                    ),
                    Button(
                        "Switch to Dark Theme",
                        data_on_click=[preferences.theme.set("dark"), playground_value.set("dark")],
                        data_show=(playground_path.eq("preferences.theme") & preferences.theme.eq("light")),
                        cls="px-4 py-2 bg-black text-white font-medium hover:bg-gray-800 transition-colors mr-2",
                    ),
                    data_show=playground_path.eq("preferences.theme"),
                    cls="mb-4",
                ),
                # Email notifications toggle
                Div(
                    Button(
                        "Enable Email Notifications",
                        data_on_click=[notifications.email.set(True), playground_value.set(True)],
                        data_show=(playground_path.eq("notifications.email") & ~notifications.email),
                        cls="px-4 py-2 bg-black text-white font-medium hover:bg-gray-800 transition-colors mr-2",
                    ),
                    Button(
                        "Disable Email Notifications",
                        data_on_click=[notifications.email.set(False), playground_value.set(False)],
                        data_show=(playground_path.eq("notifications.email") & notifications.email),
                        cls="px-4 py-2 bg-black text-white font-medium hover:bg-gray-800 transition-colors mr-2",
                    ),
                    data_show=playground_path.eq("notifications.email"),
                    cls="mb-4",
                ),
            ),
            P(
                "💡 Try clicking the examples above, then update values to see how changes affect the entire page!",
                cls="text-sm text-gray-600 mt-6 italic",
            ),
            cls="mb-12 p-8 bg-white border border-gray-200",
        ),
        # === KEY TAKEAWAYS ===
        Div(
            H3("Key Takeaways", cls="text-2xl font-bold text-black mb-6"),
            Div(
                Div(
                    Icon(
                        "material-symbols:code-blocks",
                        width="20",
                        height="20",
                        cls="mr-3 text-green-600 flex-shrink-0 mt-1",
                    ),
                    "Extract logical sections into variables for better readability",
                    cls="flex items-start p-4 mb-3 bg-green-50 border border-green-200 rounded-lg text-green-900",
                ),
                Div(
                    Icon(
                        "material-symbols:code-blocks",
                        width="20",
                        height="20",
                        cls="mr-3 text-blue-600 flex-shrink-0 mt-1",
                    ),
                    "Use bracket notation for reserved words and dynamic keys",
                    cls="flex items-start p-4 mb-3 bg-blue-50 border border-blue-200 rounded-lg text-blue-900",
                ),
                Div(
                    Icon(
                        "material-symbols:account-tree",
                        width="20",
                        height="20",
                        cls="mr-3 text-purple-600 flex-shrink-0 mt-1",
                    ),
                    "Group related properties under common parent objects",
                    cls="flex items-start p-4 mb-3 bg-purple-50 border border-purple-200 rounded-lg text-purple-900",
                ),
                Div(
                    Icon(
                        "material-symbols:visibility",
                        width="20",
                        height="20",
                        cls="mr-3 text-orange-600 flex-shrink-0 mt-1",
                    ),
                    "Keep expressions short and readable in templates",
                    cls="flex items-start p-4 mb-3 bg-orange-50 border border-orange-200 rounded-lg text-orange-900",
                ),
                Div(
                    Icon(
                        "material-symbols:code", width="20", height="20", cls="mr-3 text-indigo-600 flex-shrink-0 mt-1"
                    ),
                    "Follow Python naming conventions for maintainable code",
                    cls="flex items-start p-4 bg-indigo-50 border border-indigo-200 rounded-lg text-indigo-900",
                ),
            ),
            cls="mb-12 p-8 bg-white border border-gray-200",
        ),
        cls="max-w-5xl mx-auto px-8 sm:px-12 lg:px-16 py-16 sm:py-20 md:py-24 bg-white min-h-screen",
    )


if __name__ == "__main__":
    print("🔗 Nested Property Access Demo")
    print("=" * 40)
    print("🚀 Running on http://localhost:5019")
    print("📚 From messy to clean: Learn Pythonic property access!")
    serve(port=5019)
