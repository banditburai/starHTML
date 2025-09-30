"""Comprehensive demo showcasing the persist handler capabilities.

This demo shows how to use the persist handler to automatically save and restore
signal values across page reloads using localStorage and sessionStorage.
"""

from starhtml import *

app, rt = star_app(
    title="Persist Handler Demo",
    hdrs=[
        Script(src="https://cdn.jsdelivr.net/npm/@tailwindcss/browser@4"),
        Style("""
            body { background: white; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; -webkit-font-smoothing: antialiased; }
        """),
        persist_handler(),  # Enable persistence (configure via data attributes)
    ],
    iconify=True,
    compression=False,
)


@rt("/")
def home():
    return Div(
        # Main container
        Div(
            (persisted_text := Signal("persisted_text", "")),
            (counter := Signal("counter", 0)),
            (session_value := Signal("session_value", "")),
            (persistent_score := Signal("persistent_score", 0)),
            (temporary_lives := Signal("temporary_lives", 3)),
            (is_dark_mode := Signal("is_dark_mode", False)),
            (temp_counter := Signal("temp_counter", 0)),
            (app_version := Signal("app_version", "v1.0")),
            (user_pref := Signal("user_pref", "compact")),
            (tab_id := Signal("tab_id", "abc123")),
            (page_views := Signal("page_views", 1)),
            # Header with bold typography
            Div(
                H1("09", cls="text-8xl font-black text-gray-100 leading-none"),
                H1("Persist Handler", cls="text-5xl md:text-6xl font-bold text-black mt-2"),
                P(
                    "Automatic signal persistence with localStorage and sessionStorage",
                    cls="text-lg text-gray-600 mt-4",
                ),
                cls="mb-16",
            ),
            # Basic Persistence
            Div(
                H3("Basic Signal Persistence", cls="text-2xl font-bold text-black mb-6"),
                P("Values automatically saved to localStorage and restored on page load:", cls="text-gray-600 mb-6"),
                Div(
                    H4("Text Input Persistence", cls="text-lg font-bold text-black mb-4"),
                    Div(
                        Input(
                            placeholder="Type something and reload the page...",
                            data_bind=persisted_text,
                            cls="w-full px-3 py-2 border border-gray-300 focus:border-gray-500 focus:outline-none mb-4",
                        ),
                        Div(
                            Span("Current value: ", cls="text-gray-600"),
                            Span(data_text=persisted_text, cls="font-bold text-black"),
                            cls="mb-2",
                        ),
                        P("Try typing, then refresh the page!", cls="text-sm text-gray-500"),
                    ),
                    data_persist=persisted_text,  # Persist the text signal
                    cls="p-6 bg-white border border-gray-200",
                ),
                cls="mb-12 p-8 bg-gray-50",
            ),
            # Counter with Reset
            Div(
                H3("Counter with Reset Button", cls="text-2xl font-bold text-black mb-6"),
                P(
                    "Counter persists across page reloads, but reset clears both display and storage:",
                    cls="text-gray-600 mb-6",
                ),
                Div(
                    H4("Persistent Counter", cls="text-lg font-bold text-black mb-4"),
                    Div(
                        Div(
                            Span("Count: ", cls="text-gray-600"),
                            Span(data_text=counter | value(0), cls="text-4xl font-bold text-black"),
                            cls="mb-6",
                        ),
                        Div(
                            Button(
                                "Increment (+1)",
                                data_on_click=counter.add(1),  # JS: $counter++
                                cls="px-4 py-2 bg-green-600 text-white font-medium hover:bg-green-700 transition-colors mr-2",
                            ),
                            Button(
                                "Add 5 (+5)",
                                data_on_click=counter.add(5),  # JS: $counter += 5
                                cls="px-4 py-2 bg-green-700 text-white font-medium hover:bg-green-800 transition-colors mr-2",
                            ),
                            Button(
                                "Reset to 0",
                                data_on_click=counter.set(0),
                                cls="px-4 py-2 border border-gray-300 text-black font-medium hover:border-gray-500 transition-colors",
                            ),
                            cls="flex gap-2",
                        ),
                    ),
                    data_persist=counter,  # Persist the counter signal
                    cls="p-6 bg-white border border-gray-200",
                ),
                cls="mb-12 p-8 bg-white border border-gray-200",
            ),
            # Session Storage Demo
            Div(
                H3("Session Storage (Tab-Only)", cls="text-2xl font-bold text-black mb-6"),
                P(
                    "This data is only saved for this browser tab and cleared when the tab closes:",
                    cls="text-gray-600 mb-6",
                ),
                Div(
                    H4("Session-Only Data", cls="text-lg font-bold text-black mb-4"),
                    Div(
                        Input(
                            placeholder="Tab-specific data...",
                            data_bind=session_value,
                            cls="w-full px-3 py-2 border border-gray-300 focus:border-gray-500 focus:outline-none mb-4",
                        ),
                        Div(
                            Span("Session value: ", cls="text-gray-600"),
                            Span(data_text=session_value, cls="font-bold text-black"),
                            cls="mb-2",
                        ),
                        P("🔄 Refresh this tab: data persists", cls="text-sm text-green-600 mb-1"),
                        P("🆕 Open in new tab: data doesn't persist", cls="text-sm text-red-600"),
                    ),
                    data_persist=session_value.with_(session=True),  # Use sessionStorage instead of localStorage
                    cls="p-6 bg-white border border-gray-200",
                ),
                cls="mb-12 p-8 bg-gray-50",
            ),
            # Selective Persistence
            Div(
                H3("Selective Signal Persistence", cls="text-2xl font-bold text-black mb-6"),
                P("Choose which signals to persist and which to keep temporary:", cls="text-gray-600 mb-6"),
                Div(
                    H4("Mixed Persistence", cls="text-lg font-bold text-black mb-4"),
                    Div(
                        Div(
                            Div(
                                Span("Persistent Score: ", cls="text-gray-600"),
                                Span(data_text=persistent_score, cls="font-bold text-black text-xl"),
                                cls="mb-2",
                            ),
                            Div(
                                Span("Temporary Lives: ", cls="text-gray-600"),
                                Span(data_text=temporary_lives, cls="font-bold text-black text-xl"),
                            ),
                            cls="mb-6",
                        ),
                        Div(
                            Button(
                                "Add Score (+10)",
                                data_on_click=persistent_score.set(persistent_score + 10),
                                cls="px-4 py-2 bg-blue-600 text-white font-medium hover:bg-blue-700 transition-colors mr-2",
                            ),
                            Button(
                                "Lose Life (-1)",
                                data_on_click=temporary_lives.set(
                                    (temporary_lives - 1).max(0)
                                ),  # JS: $temporary_lives = Math.max(0, ($temporary_lives - 1))
                                cls="px-4 py-2 bg-red-600 text-white font-medium hover:bg-red-700 transition-colors mr-2",
                            ),
                            Button(
                                "Reset Lives",
                                data_on_click=temporary_lives.set(3),
                                cls="px-4 py-2 border border-gray-300 text-black font-medium hover:border-gray-500 transition-colors",
                            ),
                            cls="flex gap-2 mb-4",
                        ),
                        P("Reload the page: score persists, lives reset to 3", cls="text-sm text-gray-500"),
                    ),
                    data_persist=persistent_score,  # Only persist the score, not lives
                    cls="p-6 bg-white border border-gray-200",
                ),
                cls="mb-12 p-8 bg-white border border-gray-200",
            ),
            # Theme Toggle with Persistence
            Div(
                H3("Theme Toggle with Persistence", cls="text-2xl font-bold text-black mb-6"),
                P("Toggle between light and dark themes - your preference is remembered:", cls="text-gray-600 mb-6"),
                Div(
                    H4("Theme Preferences", cls="text-lg font-bold text-black mb-4"),
                    Div(
                        Div(
                            Span("Current theme: ", cls="text-gray-600"),
                            Span(
                                data_text=is_dark_mode.if_("Dark", "Light"),  # JS: ($is_dark_mode ? "Dark" : "Light")
                                cls="font-bold text-black",
                            ),
                            cls="mb-4",
                        ),
                        Button(
                            Span(
                                data_text=is_dark_mode.if_("☀️ Switch to Light", "🌙 Switch to Dark")
                            ),  # JS: ($is_dark_mode ? "☀️ Switch to Light" : "🌙 Switch to Dark")
                            data_on_click=is_dark_mode.toggle(),  # JS: $is_dark_mode = !$is_dark_mode
                            cls="px-4 py-2 bg-black text-white font-medium hover:bg-gray-800 transition-colors mb-4",
                        ),
                        P("Your theme choice persists across page reloads!", cls="text-sm text-gray-500"),
                    ),
                    data_persist=is_dark_mode,
                    cls="p-6 bg-white border border-gray-200",
                ),
                cls="mb-12 p-8 bg-gray-50",
            ),
            # Features Demo
            Div(
                H3("Features", cls="text-2xl font-bold text-black mb-6"),
                P("Demonstrating different persistence patterns:", cls="text-gray-600 mb-6"),
                # Example with explicit "none"
                Div(
                    H4("Disabled Persistence", cls="text-lg font-bold text-black mb-4"),
                    Div(
                        Div(
                            Span("Temp counter: ", cls="text-gray-600"),
                            Span(data_text=temp_counter, cls="font-bold text-black text-xl"),
                            cls="mb-4",
                        ),
                        P(
                            "This counter will reset on every page reload (persistence disabled).",
                            cls="text-sm text-gray-500 mb-4",
                        ),
                        Button(
                            "Increment (No Persistence)",
                            data_on_click=temp_counter.set(temp_counter + 1),
                            cls="px-4 py-2 bg-gray-600 text-white font-medium hover:bg-gray-700 transition-colors",
                        ),
                    ),
                    # No persistence - omit data_persist attribute
                    cls="p-6 bg-white border border-gray-200 mb-6",
                ),
                # Example with custom storage key
                Div(
                    H4("Custom Storage Key", cls="text-lg font-bold text-black mb-4"),
                    Div(
                        Div(
                            Span("App Version: ", cls="text-gray-600"),
                            Span(data_text=app_version, cls="font-bold text-black"),
                            cls="mb-2",
                        ),
                        Div(
                            Span("User Preference: ", cls="text-gray-600"),
                            Span(data_text=user_pref, cls="font-bold text-black"),
                            cls="mb-4",
                        ),
                        P(
                            "These values use a custom storage key: 'starhtml-persist-myapp'",
                            cls="text-sm text-gray-500 mb-4",
                        ),
                        Div(
                            Button(
                                "Update Version",
                                data_on_click=app_version.set(
                                    js("'v' + Math.floor(Math.random() * 100)")
                                ),  # JS: generates random version like "v42"
                                cls="px-4 py-2 bg-purple-600 text-white font-medium hover:bg-purple-700 transition-colors mr-2",
                            ),
                            Button(
                                "Toggle Preference",
                                data_on_click=user_pref.toggle(
                                    "compact", "expanded"
                                ),  # JS: $user_pref = ($user_pref === "compact" ? "expanded" : "compact")
                                cls="px-4 py-2 bg-purple-700 text-white font-medium hover:bg-purple-800 transition-colors",
                            ),
                            cls="flex gap-2",
                        ),
                    ),
                    data_persist=(
                        [app_version, user_pref],
                        dict(key="myapp"),
                    ),  # Custom storage key - list with modifiers
                    cls="p-6 bg-white border border-gray-200 mb-6",
                ),
                # Example with session storage for specific signal
                Div(
                    H4("Session-Only Specific Signal", cls="text-lg font-bold text-black mb-4"),
                    Div(
                        Div(
                            Span("Tab ID: ", cls="text-gray-600"),
                            Span(data_text=tab_id, cls="font-bold text-black"),
                            cls="mb-2",
                        ),
                        Div(
                            Span("Page views: ", cls="text-gray-600"),
                            Span(data_text=page_views, cls="font-bold text-black"),
                            cls="mb-4",
                        ),
                        P(
                            "Only tabId persists in this tab session. Page views reset every reload.",
                            cls="text-sm text-gray-500 mb-4",
                        ),
                        Div(
                            Button(
                                "New Tab ID",
                                data_on_click=tab_id.set(
                                    js("Math.random().toString(36).substr(2, 9)")
                                ),  # JS: generates random 9-char ID like "x4k2n5p1q"
                                cls="px-4 py-2 bg-pink-600 text-white font-medium hover:bg-pink-700 transition-colors mr-2",
                            ),
                            Button(
                                "Add Page View",
                                data_on_click=page_views.set(page_views + 1),  # JS: $page_views = ($page_views + 1)
                                cls="px-4 py-2 bg-gray-600 text-white font-medium hover:bg-gray-700 transition-colors",
                            ),
                            cls="flex gap-2",
                        ),
                    ),
                    data_persist=tab_id.with_(session=True),  # Persist tab_id in sessionStorage
                    cls="p-6 bg-white border border-gray-200 mb-6",
                ),
                cls="mb-12 p-8 bg-white border border-gray-200",
            ),
            # Storage Management
            Div(
                H3("Storage Management", cls="text-2xl font-bold text-black mb-6"),
                P("Tools to manage and debug your persisted data:", cls="text-gray-600 mb-6"),
                Div(
                    H4("Clear Storage", cls="text-lg font-bold text-black mb-4"),
                    P(
                        "⚠️ These actions will only clear StarHTML persist data from this demo",
                        cls="text-sm text-amber-600 mb-4",
                    ),
                    Div(
                        Button(
                            "Clear Demo localStorage",
                            onclick="""
                                const keys = Object.keys(localStorage).filter(k => k.startsWith('starhtml-persist'));
                                keys.forEach(k => localStorage.removeItem(k));
                                location.reload();
                            """,
                            cls="px-4 py-2 bg-red-600 text-white font-medium hover:bg-red-700 transition-colors mb-2 w-full sm:w-auto",
                        ),
                        Button(
                            "Clear Demo sessionStorage",
                            onclick="""
                                const keys = Object.keys(sessionStorage).filter(k => k.startsWith('starhtml-persist'));
                                keys.forEach(k => sessionStorage.removeItem(k));
                                location.reload();
                            """,
                            cls="px-4 py-2 bg-orange-600 text-white font-medium hover:bg-orange-700 transition-colors mb-2 w-full sm:w-auto",
                        ),
                        Button(
                            "View StarHTML Storage",
                            onclick="""
                                const localKeys = Object.keys(localStorage).filter(k => k.startsWith('starhtml-persist'));
                                const sessionKeys = Object.keys(sessionStorage).filter(k => k.startsWith('starhtml-persist'));
                                
                                console.log('%c🗄️ StarHTML Storage Contents', 'font-size: 18px; font-weight: bold; color: #4A5568; padding: 10px 0;');
                                
                                console.log('%c📦 localStorage:', 'font-size: 14px; font-weight: bold; color: #2563EB; margin-top: 10px;');
                                localKeys.forEach(key => {
                                    const value = localStorage.getItem(key);
                                    try {
                                        const parsed = JSON.parse(value);
                                        console.log(`%c  ${key}:`, 'color: #059669; font-weight: bold;');
                                        console.log('   ', parsed);
                                    } catch (e) {
                                        console.log(`%c  ${key}:`, 'color: #059669; font-weight: bold;', value);
                                    }
                                });
                                if (localKeys.length === 0) {
                                    console.log('   %c(empty)', 'color: #9CA3AF; font-style: italic;');
                                }
                                
                                console.log('%c📋 sessionStorage:', 'font-size: 14px; font-weight: bold; color: #DC2626; margin-top: 15px;');
                                sessionKeys.forEach(key => {
                                    const value = sessionStorage.getItem(key);
                                    try {
                                        const parsed = JSON.parse(value);
                                        console.log(`%c  ${key}:`, 'color: #7C3AED; font-weight: bold;');
                                        console.log('   ', parsed);
                                    } catch (e) {
                                        console.log(`%c  ${key}:`, 'color: #7C3AED; font-weight: bold;', value);
                                    }
                                });
                                if (sessionKeys.length === 0) {
                                    console.log('   %c(empty)', 'color: #9CA3AF; font-style: italic;');
                                }
                                
                                console.log('%c' + '─'.repeat(60), 'color: #E5E7EB;');
                                alert('StarHTML storage contents displayed in console.');
                            """,
                            cls="px-4 py-2 border border-gray-300 text-black font-medium hover:border-gray-500 transition-colors w-full sm:w-auto",
                        ),
                        cls="flex flex-col sm:flex-row gap-2",
                    ),
                    cls="p-6 bg-white border border-gray-200",
                ),
                cls="mb-12 p-8 bg-gray-50",
            ),
            # How Persistence Works
            Div(
                H3("How Persistence Works", cls="text-2xl font-bold text-black mb-6"),
                P("The persist handler is a simple yet powerful Datastar attribute plugin:", cls="text-gray-600 mb-6"),
                Div(
                    Div(
                        H4("Usage Patterns", cls="text-lg font-bold text-black mb-4"),
                        Ul(
                            Li(
                                Code('data_persist="signal_name"', cls="text-xs bg-gray-100 px-1 py-0.5 rounded"),
                                " - Persist a specific signal",
                            ),
                            Li(
                                Code('data_persist="signal1,signal2"', cls="text-xs bg-gray-100 px-1 py-0.5 rounded"),
                                " - Persist multiple signals",
                            ),
                            Li(
                                Code(
                                    "data_persist=signal.with_(session=True)",
                                    cls="text-xs bg-gray-100 px-1 py-0.5 rounded",
                                ),
                                " - Use sessionStorage",
                            ),
                            Li(
                                Code(
                                    'data_persist=([signal1], dict(key="mykey"))',
                                    cls="text-xs bg-gray-100 px-1 py-0.5 rounded",
                                ),
                                " - Custom storage key",
                            ),
                            Li(
                                "Default storage key: ",
                                Code("starhtml-persist", cls="text-xs bg-gray-100 px-1 py-0.5 rounded"),
                            ),
                            Li("Supports comma or semicolon separated signal names"),
                            cls="text-sm space-y-2 list-disc list-inside text-gray-700",
                        ),
                    ),
                    Div(
                        H4("Implementation Details", cls="text-lg font-bold text-black mb-4"),
                        Ul(
                            Li("Loads stored values on element initialization"),
                            Li("Watches specified signals for changes"),
                            Li("Debounced writes (500ms) prevent excessive storage calls"),
                            Li("JSON serialization for complex data types"),
                            Li("Error handling for storage quota exceeded"),
                            Li("Fallback behavior when storage is unavailable"),
                            cls="text-sm space-y-2 list-disc list-inside text-gray-700",
                        ),
                    ),
                    cls="grid grid-cols-1 lg:grid-cols-2 gap-8",
                ),
                cls="mb-12 p-8 bg-white border border-gray-200",
            ),
        ),
        cls="max-w-5xl mx-auto px-8 sm:px-12 lg:px-16 py-16 sm:py-20 md:py-24 bg-white min-h-screen",
    )


if __name__ == "__main__":
    print("Persist Handler Demo running on http://localhost:5001")
    serve(port=5001)
