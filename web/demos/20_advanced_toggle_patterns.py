"""Advanced Toggle Patterns - Comprehensive Examples

Demonstrates advanced usage of the .toggle() method with multiple states,
edge cases, and real-world patterns that go beyond simple boolean toggles.
"""

from starhtml import *

app, rt = star_app(
    title="Advanced Toggle Patterns",
    hdrs=[
        Script(src="https://cdn.jsdelivr.net/npm/@tailwindcss/browser@4"),
        Style(
            """body{background:#fff;color:#000;margin:0;padding:0;-webkit-font-smoothing:antialiased;-moz-osx-font-smoothing:grayscale}::selection{background:#000;color:#fff}.state-indicator{transition:all 0.3s ease;border-radius:8px;padding:8px 16px;font-weight:600}.theme-light{background:#ffffff;color:#374151;border:1px solid #d1d5db}.theme-dark{background:#1f2937;color:#f9fafb;border:1px solid #374151}.theme-auto{background:linear-gradient(135deg,#ffffff 50%,#1f2937 50%);color:#6b7280;border:1px solid #6b7280}.status-draft{background:#fef3c7;color:#92400e}.status-review{background:#dbeafe;color:#1e40af}.status-approved{background:#d1fae5;color:#047857}.status-published{background:#e0e7ff;color:#3730a3}.priority-low{background:#f3f4f6;color:#4b5563}.priority-medium{background:#fef3c7;color:#92400e}.priority-high{background:#fecaca;color:#dc2626}.priority-urgent{background:#fde68a;color:#92400e;animation:pulse 2s infinite}@keyframes pulse{0%,100%{opacity:1}50%{opacity:0.7}}.connection-disconnected{color:#6b7280}.connection-connecting{color:#3b82f6;animation:pulse 1.5s infinite}.connection-connected{color:#10b981}.connection-error{color:#ef4444}"""
        ),
    ],
    iconify=True,
    compression=False,
)


@rt("/")
def home():
    return Div(
        # === SIGNAL DEFINITIONS ===
        (theme_mode := Signal("theme_mode", "light")),  # light -> dark -> auto -> light
        (
            connection_status := Signal("connection_status", "disconnected")
        ),  # disconnected -> connecting -> connected -> error -> disconnected
        (visibility := Signal("visibility", "visible")),  # visible -> hidden -> visible
        # Multi-state workflow
        (doc_status := Signal("doc_status", "draft")),  # draft -> review -> approved -> published -> draft
        (priority_level := Signal("priority_level", "low")),  # low -> medium -> high -> urgent -> low
        # Complex toggle with conditions
        (user_role := Signal("user_role", "viewer")),  # viewer -> editor -> admin -> viewer
        (feature_enabled := Signal("feature_enabled", False)),
        (notification_type := Signal("notification_type", "none")),  # none -> email -> push -> both -> none
        # Edge case demonstrations
        (single_state := Signal("single_state", "only")),
        (empty_toggle := Signal("empty_toggle", "")),
        (numeric_cycle := Signal("numeric_cycle", 1)),  # 1 -> 2 -> 3 -> 1
        # Header section with large number
        Div(
            H1("18", cls="text-8xl font-black text-gray-100 leading-none"),
            H1("Advanced Toggle Patterns", cls="text-5xl md:text-6xl font-bold text-black mt-2"),
            P("Complex state cycling and conditional toggles", cls="text-lg text-gray-600 mt-4"),
            cls="mb-16",
        ),
        # === 1. MULTI-STATE CYCLES ===
        Div(
            H3("Multi-State Cycles", cls="text-2xl font-bold text-black mb-6"),
            P("Cycle through 3+ states using toggle() with multiple arguments", cls="text-gray-600 mb-6"),
            # Theme Toggle (3 states) with dynamic button
            # Theme Selector (3-state cycle)
            Div(
                H3("Theme Selector (3-state cycle)", cls="text-lg font-semibold mb-3"),
                Div(
                    Button(
                        Span(
                            data_text=match(theme_mode, light="🌞 Light Mode", dark="🌙 Dark Mode", auto="✨ Auto Mode")
                        ),
                        data_on_click=theme_mode.toggle("light", "dark", "auto"),
                        cls="px-4 py-2 rounded bg-blue-500 text-white hover:bg-blue-600 transition-colors",
                    ),
                    Div(
                        "Current theme: ",
                        Span(data_text=theme_mode, data_attr_class="theme-" + theme_mode, cls="state-indicator ml-2"),
                        cls="mt-4",
                    ),
                    P("Click button to cycle: light → dark → auto", cls="text-sm text-gray-500 mt-2"),
                ),
                P(
                    "Button text changes based on current state using .switch() method",
                    cls="text-sm text-gray-500 mt-2",
                ),
                cls="mb-8 p-4 bg-gray-50 rounded-lg",
            ),
            # Document Workflow (4 states)
            Div(
                H3("Document Workflow (4-state)", cls="text-lg font-semibold mb-3"),
                Div(
                    Button(
                        Span(
                            data_text=match(
                                doc_status,
                                draft="📝 Submit for Review",
                                review="👁️ Send to Approval",
                                approved="✅ Publish Document",
                                published="🚀 Back to Draft",
                            )
                        ),
                        data_on_click=doc_status.toggle("draft", "review", "approved", "published"),
                        cls="px-4 py-2 rounded bg-purple-500 text-white hover:bg-purple-600",
                    ),
                    Div(
                        "Status: ",
                        Span(data_text=doc_status, data_attr_class="status-" + doc_status, cls="state-indicator ml-2"),
                        cls="mt-4",
                    ),
                ),
                P("Workflow: draft → review → approved → published → draft...", cls="text-sm text-gray-500 mt-2"),
                cls="mb-8 p-4 bg-gray-50 rounded-lg",
            ),
            # Connection Status (4 states)
            Div(
                H3("Connection Status Indicator", cls="text-lg font-semibold mb-3"),
                Div(
                    Button(
                        Span(
                            data_text=match(
                                connection_status,
                                disconnected="🔌 Connect",
                                connecting="⏳ Cancel",
                                connected="✅ Disconnect",
                                error="🔄 Retry Connection",
                            )
                        ),
                        data_on_click=connection_status.toggle("disconnected", "connecting", "connected", "error"),
                        cls="px-4 py-2 rounded bg-blue-500 text-white hover:bg-blue-600",
                    ),
                    Div(
                        "Status: ",
                        Span(
                            data_text=match(
                                connection_status,
                                disconnected="⭕ Disconnected",
                                connecting="🔄 Connecting...",
                                connected="🟢 Connected",
                                error="🔴 Connection Failed",
                            ),
                            data_attr_class="connection-" + connection_status,
                            cls="ml-2 font-semibold",
                        ),
                        cls="mt-4",
                    ),
                ),
                P("Cycle through connection states with visual feedback", cls="text-sm text-gray-500 mt-2"),
                cls="mb-8 p-4 bg-gray-50 rounded-lg",
            ),
            cls="mb-12 p-8 bg-white border border-gray-200",
        ),
        # === 2. CONDITIONAL TOGGLES ===
        Div(
            H3("Conditional Toggles", cls="text-2xl font-bold text-black mb-6"),
            P("Toggle behavior that changes based on other conditions", cls="text-gray-600 mb-6"),
            # Role-based toggle
            Div(
                H3("Role-Based Access Control", cls="text-lg font-semibold mb-3"),
                Div(
                    Div(
                        Button(
                            Span(data_text="Role: " + user_role),
                            data_on_click=user_role.toggle("viewer", "editor", "admin"),
                            cls="mr-2 px-4 py-2 rounded bg-indigo-500 text-white hover:bg-indigo-600",
                        ),
                        Button(
                            Span(data_text=feature_enabled.if_("✅ Enabled", "❌ Disabled")),
                            # Only allow feature toggle for editor/admin roles
                            data_on_click=(user_role != "viewer").then(feature_enabled.toggle()),
                            data_attr_disabled=user_role == "viewer",
                            cls="px-4 py-2 rounded bg-orange-500 text-white hover:bg-orange-600 disabled:opacity-50 disabled:cursor-not-allowed",
                        ),
                        cls="flex gap-2",
                    ),
                    Div(
                        Span(
                            data_text=(user_role == "viewer").if_(
                                "⚠️ Feature toggle disabled for viewers", "✅ Feature toggle enabled"
                            ),
                            data_attr_cls=(user_role == "viewer").if_("text-red-600", "text-green-600"),
                            cls="font-medium text-sm",
                        ),
                        cls="mt-3",
                    ),
                ),
                P("Feature toggle only works for editor/admin roles", cls="text-sm text-gray-500 mt-2"),
                cls="mb-8 p-4 bg-gray-50 rounded-lg",
            ),
            # Notification preferences with dependencies
            Div(
                H3("Notification Preferences", cls="text-lg font-semibold mb-3"),
                Div(
                    Button(
                        Span(
                            data_text=match(
                                notification_type, none="📴 None", email="📧 Email", push="📱 Push", both="📧📱 Both"
                            )
                        ),
                        data_on_click=notification_type.toggle("none", "email", "push", "both"),
                        cls="px-4 py-2 rounded bg-teal-500 text-white hover:bg-teal-600",
                    ),
                    # Show different messages based on notification type
                    Div(
                        Div(
                            "All notifications disabled",
                            data_show=notification_type == "none",
                            cls="p-2 bg-gray-100 rounded text-sm",
                        ),
                        Div(
                            "Email notifications only",
                            data_show=notification_type == "email",
                            cls="p-2 bg-blue-100 rounded text-sm",
                        ),
                        Div(
                            "Push notifications only",
                            data_show=notification_type == "push",
                            cls="p-2 bg-green-100 rounded text-sm",
                        ),
                        Div(
                            "Both email and push notifications",
                            data_show=notification_type == "both",
                            cls="p-2 bg-purple-100 rounded text-sm",
                        ),
                        cls="mt-3",
                    ),
                ),
                P("Cycles: none → email → push → both → none...", cls="text-sm text-gray-500 mt-2"),
                cls="mb-8 p-4 bg-gray-50 rounded-lg",
            ),
            cls="mb-12 p-8 bg-gray-50",
        ),
        # === 3. EDGE CASES & SPECIAL PATTERNS ===
        Div(
            H3("Special Patterns", cls="text-2xl font-bold text-black mb-6"),
            P("Handling edge cases and special toggle scenarios", cls="text-gray-600 mb-6"),
            # Priority with visual effects
            Div(
                H3("Priority Levels with Animation", cls="text-lg font-semibold mb-3"),
                Div(
                    Button(
                        Span(
                            data_text="Priority: "
                            + match(
                                priority_level, low="🟢 Low", medium="🟡 Medium", high="🔴 High", urgent="🚨 URGENT"
                            )
                        ),
                        data_on_click=priority_level.toggle("low", "medium", "high", "urgent"),
                        cls="px-4 py-2 rounded bg-red-500 text-white hover:bg-red-600",
                    ),
                    Div(
                        "Current priority: ",
                        Span(
                            data_text=priority_level,
                            data_attr_class="priority-" + priority_level,
                            cls="state-indicator ml-2",
                        ),
                        cls="mt-4",
                    ),
                    P("Notice the 'urgent' state pulses!", cls="text-sm text-gray-500 italic mt-2"),
                ),
                P("The urgent state includes a CSS pulse animation", cls="text-sm text-gray-500 mt-2"),
                cls="mb-8 p-4 bg-gray-50 rounded-lg",
            ),
            # Numeric cycling
            Div(
                H3("Numeric State Cycling", cls="text-lg font-semibold mb-3"),
                Div(
                    Button(
                        Span(data_text="Level " + numeric_cycle),
                        data_on_click=numeric_cycle.toggle(1, 2, 3),
                        cls="px-4 py-2 rounded bg-cyan-500 text-white hover:bg-cyan-600",
                    ),
                    Div(
                        Div("🥉 Bronze level", data_show=numeric_cycle == 1, cls="text-amber-600"),
                        Div("🥈 Silver level", data_show=numeric_cycle == 2, cls="text-gray-600"),
                        Div("🥇 Gold level", data_show=numeric_cycle == 3, cls="text-yellow-600"),
                        cls="mt-3 text-lg font-semibold",
                    ),
                ),
                P("Cycles through numbers: 1 → 2 → 3 → 1...", cls="text-sm text-gray-500 mt-2"),
                cls="mb-8 p-4 bg-gray-50 rounded-lg",
            ),
            # Boolean toggle with custom labels
            Div(
                H3("Enhanced Boolean Toggle", cls="text-lg font-semibold mb-3"),
                Div(
                    Button(
                        Span(data_text=match(visibility, visible="👁️ Hide Content", hidden="🙈 Show Content")),
                        data_on_click=visibility.toggle("visible", "hidden"),
                        cls="px-4 py-2 rounded bg-gray-500 text-white hover:bg-gray-600",
                    ),
                    # Conditional content
                    Div(
                        Div(
                            "✨ This content is visible!",
                            data_show=visibility == "visible",
                            cls="mt-3 p-3 bg-green-100 border border-green-300 rounded",
                        ),
                        Div(
                            "Content is hidden",
                            data_show=visibility == "hidden",
                            cls="mt-3 p-3 bg-red-100 border border-red-300 rounded",
                        ),
                    ),
                ),
                P("Boolean toggle with custom string values instead of true/false", cls="text-sm text-gray-500 mt-2"),
                cls="mb-8 p-4 bg-gray-50 rounded-lg",
            ),
            cls="mb-12 p-8 bg-white border border-gray-200",
        ),
        # === 4. ADVANCED PATTERNS ===
        Div(
            H3("Advanced Patterns", cls="text-2xl font-bold text-black mb-6"),
            P("Complex toggle patterns for real-world applications", cls="text-gray-600 mb-6"),
            # Combined actions
            Div(
                H3("Toggle with Side Effects", cls="text-lg font-semibold mb-3"),
                Div(
                    Button(
                        "Toggle Theme + Log",
                        data_on_click=[
                            theme_mode.toggle("light", "dark", "auto"),
                            console.log("Theme changed to:", theme_mode),
                        ],
                        cls="px-4 py-2 rounded bg-violet-500 text-white hover:bg-violet-600",
                    ),
                    P("Check browser console for logging", cls="text-sm text-gray-500 mt-2"),
                ),
                P("Combine toggle with logging, analytics, or other actions", cls="text-sm text-gray-500 mt-2"),
                cls="mb-8 p-4 bg-gray-50 rounded-lg",
            ),
            # State validation
            Div(
                H3("Validated State Changes", cls="text-lg font-semibold mb-3"),
                Div(
                    Div(
                        Button(
                            "Advance Workflow",
                            # Only allow status change if not currently published
                            data_on_click=(doc_status != "published").then(
                                doc_status.toggle("draft", "review", "approved", "published")
                            ),
                            data_attr_disabled=doc_status == "published",
                            cls="mr-2 px-4 py-2 rounded bg-amber-500 text-white hover:bg-amber-600 disabled:opacity-50",
                        ),
                        Button(
                            "Reset to Draft",
                            data_on_click=doc_status.set("draft"),
                            cls="px-4 py-2 rounded bg-gray-500 text-white hover:bg-gray-600",
                        ),
                        cls="flex gap-2",
                    ),
                    Div(
                        "Status: ",
                        Span(data_text=doc_status, cls="font-bold"),
                        Div(
                            "⚠️ Published documents cannot be changed via normal workflow",
                            data_show=doc_status == "published",
                            cls="text-sm text-amber-600 mt-1",
                        ),
                        cls="mt-3",
                    ),
                ),
                P("Prevent invalid state transitions with conditional logic", cls="text-sm text-gray-500 mt-2"),
                cls="mb-8 p-4 bg-gray-50 rounded-lg",
            ),
            cls="mb-12 p-8 bg-gray-50",
        ),
        cls="max-w-5xl mx-auto px-8 sm:px-12 lg:px-16 py-16 sm:py-20 md:py-24 bg-white min-h-screen",
    )


if __name__ == "__main__":
    print("🔄 Advanced Toggle Patterns Demo")
    print("=" * 40)
    print("🚀 Running on http://localhost:5020")
    print("✨ Features:")
    print("   • Multi-state cycling (3+ states)")
    print("   • Conditional toggles")
    print("   • Edge cases & special patterns")
    print("   • Side effects & validation")
    print("   • Real-world examples")
    serve(port=5020)
