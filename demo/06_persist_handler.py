"""Comprehensive demo showcasing the persist handler capabilities.

This demo shows how to use the persist handler to automatically save and restore
signal values across page reloads using localStorage and sessionStorage.
"""

from starhtml import *

app, rt = star_app(
    title="Persist Handler Demo",
    hdrs=[
        Script(src="https://cdn.jsdelivr.net/npm/@tailwindcss/browser@4"),
        persist_handler(),  # Enable persistence (configure via data attributes)
    ],
)


@rt("/")
def home():
    return Div(
        # Page Header
        Header(
            H1("💾 Persist Handler Demo", cls="text-3xl font-bold mb-2"),
            P(
                "Demonstrating automatic signal persistence with localStorage and sessionStorage",
                cls="text-muted-foreground",
            ),
            cls="text-center py-8 border-b bg-background",
        ),
        # Main Content
        Main(
            # Basic Persistence
            Section(
                H2("Basic Signal Persistence", cls="text-2xl font-semibold mb-4"),
                P(
                    "Values automatically saved to localStorage and restored on page load:",
                    cls="mb-4 text-muted-foreground",
                ),
                Div(
                    H3("Text Input Persistence", cls="font-medium mb-4 text-blue-800"),
                    Div(
                        Input(
                            ds_bind("persisted_text"),
                            placeholder="Type something and reload the page...",
                            cls="w-full p-3 border-2 border-blue-200 rounded-lg mb-3",
                        ),
                        P("Current value: ", Span(ds_text("$persisted_text"), cls="font-bold text-blue-600")),
                        P("💡 Try typing, then refresh the page!", cls="text-sm text-gray-600 mt-2"),
                        cls="space-y-2",
                    ),
                    ds_signals(persisted_text=""),
                    ds_persist("persisted_text"),  # Persist the text signal
                    cls="p-6 bg-white border-2 border-blue-300 rounded-lg shadow-lg mb-8",
                ),
                cls="mb-12",
            ),
            # Counter with Reset
            Section(
                H2("Counter with Reset Button", cls="text-2xl font-semibold mb-4"),
                P(
                    "Counter persists across page reloads, but reset clears both display and storage:",
                    cls="mb-4 text-muted-foreground",
                ),
                Div(
                    H3("Persistent Counter", cls="font-medium mb-4 text-green-800"),
                    Div(
                        Div(
                            Span("Count: ", cls="text-lg"),
                            Span(ds_text("$counter || 0"), cls="text-2xl font-bold text-green-600"),
                            cls="mb-4",
                        ),
                        Div(
                            Button(
                                "Increment (+1)",
                                ds_on_click("$counter = Number($counter ?? 0) + 1"),
                                cls="bg-green-500 hover:bg-green-600 text-white px-4 py-2 rounded mr-2",
                            ),
                            Button(
                                "Add 5 (+5)",
                                ds_on_click("$counter = Number($counter ?? 0) + 5"),
                                cls="bg-green-600 hover:bg-green-700 text-white px-4 py-2 rounded mr-2",
                            ),
                            Button(
                                "Reset to 0",
                                ds_on_click("$counter = 0"),
                                cls="bg-red-500 hover:bg-red-600 text-white px-4 py-2 rounded",
                            ),
                            cls="space-x-2",
                        ),
                        cls="space-y-3",
                    ),
                    ds_signals(counter=0),  # Provide fallback value
                    ds_persist("counter"),  # Persist the counter signal
                    cls="p-6 bg-white border-2 border-green-300 rounded-lg shadow-lg mb-8",
                ),
                cls="mb-12",
            ),
            # Session Storage Demo
            Section(
                H2("Session Storage (Tab-Only)", cls="text-2xl font-semibold mb-4"),
                P(
                    "This data is only saved for this browser tab and cleared when the tab closes:",
                    cls="mb-4 text-muted-foreground",
                ),
                Div(
                    H3("Session-Only Data", cls="font-medium mb-4 text-orange-800"),
                    Div(
                        Input(
                            ds_bind("session_value"),
                            placeholder="Tab-specific data...",
                            cls="w-full p-3 border-2 border-orange-200 rounded-lg mb-3",
                        ),
                        P("Session value: ", Span(ds_text("$session_value"), cls="font-bold text-orange-600")),
                        P("🔄 Refresh this tab: data persists", cls="text-sm text-green-600"),
                        P("🆕 Open in new tab: data doesn't persist", cls="text-sm text-red-600"),
                        cls="space-y-2",
                    ),
                    ds_signals(session_value=""),
                    ds_persist(session=True),  # Use sessionStorage instead of localStorage
                    cls="p-6 bg-white border-2 border-orange-300 rounded-lg shadow-lg mb-8",
                ),
                cls="mb-12",
            ),
            # Selective Persistence
            Section(
                H2("Selective Signal Persistence", cls="text-2xl font-semibold mb-4"),
                P("Choose which signals to persist and which to keep temporary:", cls="mb-4 text-muted-foreground"),
                Div(
                    H3("Mixed Persistence", cls="font-medium mb-4 text-teal-800"),
                    Div(
                        Div(
                            P("Persistent Score: ", Span(ds_text("$persistent_score"), cls="font-bold text-teal-600")),
                            P("Temporary Lives: ", Span(ds_text("$temporary_lives"), cls="font-bold text-red-600")),
                            cls="mb-4 space-y-2",
                        ),
                        Div(
                            Button(
                                "Add Score (+10)",
                                ds_on_click("$persistent_score += 10"),
                                cls="bg-teal-500 hover:bg-teal-600 text-white px-3 py-2 rounded mr-2",
                            ),
                            Button(
                                "Lose Life (-1)",
                                ds_on_click("$temporary_lives = Math.max(0, $temporary_lives - 1)"),
                                cls="bg-red-500 hover:bg-red-600 text-white px-3 py-2 rounded mr-2",
                            ),
                            Button(
                                "Reset Lives",
                                ds_on_click("$temporary_lives = 3"),
                                cls="bg-gray-500 hover:bg-gray-600 text-white px-3 py-2 rounded",
                            ),
                            cls="space-x-2",
                        ),
                        P("💡 Reload the page: score persists, lives reset to 3", cls="text-sm text-gray-600 mt-4"),
                        cls="space-y-3",
                    ),
                    ds_signals(persistent_score=0, temporary_lives=3),
                    ds_persist("persistent_score"),  # Only persist the score, not lives
                    cls="p-6 bg-white border-2 border-teal-300 rounded-lg shadow-lg mb-8",
                ),
                cls="mb-12",
            ),
            # Theme Toggle with Persistence
            Section(
                H2("Theme Toggle with Persistence", cls="text-2xl font-semibold mb-4"),
                P(
                    "Toggle between light and dark themes - your preference is remembered:",
                    cls="mb-4 text-muted-foreground",
                ),
                Div(
                    H3("Theme Preferences", cls="font-medium mb-4 text-indigo-800"),
                    Div(
                        Div(
                            P(
                                "Current theme: ",
                                Span(
                                    ds_text("$is_dark_mode ? 'Dark' : 'Light'"),
                                    ds_class(**{"$is_dark_mode ? 'text-gray-200' : 'text-gray-800'": True}),
                                    cls="font-bold",
                                ),
                            ),
                            cls="mb-4",
                        ),
                        Button(
                            Span(ds_text("$is_dark_mode ? '☀️ Switch to Light' : '🌙 Switch to Dark'")),
                            ds_on_click(
                                "$is_dark_mode = !$is_dark_mode; document.body.classList.toggle('dark', $is_dark_mode);"
                            ),
                            cls="bg-indigo-500 hover:bg-indigo-600 text-white px-4 py-2 rounded transition-colors",
                        ),
                        P("🔄 Your theme choice persists across page reloads!", cls="text-sm text-gray-600 mt-4"),
                        cls="space-y-3",
                    ),
                    ds_signals(is_dark_mode=False),
                    ds_persist("is_dark_mode"),
                    cls="p-6 bg-white border-2 border-indigo-300 rounded-lg shadow-lg mb-8",
                ),
                cls="mb-12",
            ),
            # New API Features Demo
            Section(
                H2("New API Features", cls="text-2xl font-semibold mb-4"),
                P("Demonstrating different persistence patterns:", cls="mb-4 text-muted-foreground"),
                # Example with explicit "none"
                Div(
                    H3("Disabled Persistence", cls="font-medium mb-4 text-gray-800"),
                    Div(
                        P("Temp counter: ", Span(ds_text("$temp_counter"), cls="font-bold text-gray-600")),
                        P(
                            "This counter will reset on every page reload (persistence disabled).",
                            cls="text-sm text-gray-500 mb-3",
                        ),
                        Button(
                            "Increment (No Persistence)",
                            ds_on_click("$temp_counter++"),
                            cls="bg-gray-500 hover:bg-gray-600 text-white px-3 py-2 rounded",
                        ),
                        cls="space-y-2",
                    ),
                    ds_signals(temp_counter=0),
                    # No persistence - omit ds_persist attribute
                    cls="p-6 bg-white border-2 border-gray-300 rounded-lg shadow-lg mb-6",
                ),
                # Example with custom storage key
                Div(
                    H3("Custom Storage Key", cls="font-medium mb-4 text-indigo-800"),
                    Div(
                        P("App Version: ", Span(ds_text("$app_version"), cls="font-bold text-indigo-600")),
                        P("User Preference: ", Span(ds_text("$user_pref"), cls="font-bold text-indigo-600")),
                        P(
                            "These values use a custom storage key: 'starhtml-persist-myapp'",
                            cls="text-sm text-gray-500 mb-3",
                        ),
                        Button(
                            "Update Version",
                            ds_on_click("$app_version = 'v' + Math.floor(Math.random() * 100)"),
                            cls="bg-indigo-500 hover:bg-indigo-600 text-white px-3 py-2 rounded mr-2",
                        ),
                        Button(
                            "Toggle Preference",
                            ds_on_click("$user_pref = $user_pref === 'compact' ? 'expanded' : 'compact'"),
                            cls="bg-indigo-600 hover:bg-indigo-700 text-white px-3 py-2 rounded",
                        ),
                        cls="space-y-2",
                    ),
                    ds_signals(app_version="v1.0", user_pref="compact"),
                    ds_persist(key="myapp"),  # Custom storage key
                    cls="p-6 bg-white border-2 border-indigo-300 rounded-lg shadow-lg mb-6",
                ),
                # Example with session storage for specific signal
                Div(
                    H3("Session-Only Specific Signal", cls="font-medium mb-4 text-pink-800"),
                    Div(
                        P("Tab ID: ", Span(ds_text("$tab_id"), cls="font-bold text-pink-600")),
                        P("Page views: ", Span(ds_text("$page_views"), cls="font-bold text-gray-600")),
                        P(
                            "Only tabId persists in this tab session. Page views reset every reload.",
                            cls="text-sm text-gray-500 mb-3",
                        ),
                        Button(
                            "New Tab ID",
                            ds_on_click("$tab_id = Math.random().toString(36).substr(2, 9)"),
                            cls="bg-pink-500 hover:bg-pink-600 text-white px-3 py-2 rounded mr-2",
                        ),
                        Button(
                            "Add Page View",
                            ds_on_click("$page_views++"),
                            cls="bg-gray-500 hover:bg-gray-600 text-white px-3 py-2 rounded",
                        ),
                        cls="space-y-2",
                    ),
                    ds_signals(tab_id="abc123", page_views=1),
                    ds_persist("tab_id", session=True),  # Persist only tab_id signal in session storage
                    cls="p-6 bg-white border-2 border-pink-300 rounded-lg shadow-lg mb-6",
                ),
                cls="mb-12",
            ),
            # Storage Management
            Section(
                H2("Storage Management", cls="text-2xl font-semibold mb-4"),
                P("Tools to manage and debug your persisted data:", cls="mb-4 text-muted-foreground"),
                Div(
                    H3("Clear Storage", cls="font-medium mb-4 text-red-800"),
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
                            cls="bg-red-500 hover:bg-red-600 text-white px-4 py-2 rounded mr-2",
                        ),
                        Button(
                            "Clear Demo sessionStorage",
                            onclick="""
                                const keys = Object.keys(sessionStorage).filter(k => k.startsWith('starhtml-persist'));
                                keys.forEach(k => sessionStorage.removeItem(k));
                                location.reload();
                            """,
                            cls="bg-orange-500 hover:bg-orange-600 text-white px-4 py-2 rounded mr-2",
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
                            cls="bg-gray-500 hover:bg-gray-600 text-white px-4 py-2 rounded",
                        ),
                        cls="space-x-2",
                    ),
                    cls="p-6 bg-white border-2 border-red-300 rounded-lg shadow-lg mb-8",
                ),
                cls="mb-12",
            ),
            # Performance Information
            Section(
                H2("How Persistence Works", cls="text-2xl font-semibold mb-4"),
                P(
                    "The persist handler uses a two-phase approach for optimal performance:",
                    cls="mb-4 text-muted-foreground",
                ),
                Div(
                    Div(
                        H3("🔧 Persistence Options", cls="font-medium mb-2"),
                        Ul(
                            Li('ds_persist("*") - Persist all signals in localStorage'),
                            Li('ds_persist("signal1,signal2") - Persist specific signals only'),
                            Li('ds_persist("*", session=True) - Use sessionStorage (tab-only)'),
                            Li('ds_persist("*", key="mykey") - Use custom storage key'),
                            Li("Preprocessing phase updates data-signals before Datastar init"),
                            Li("Runtime phase handles dynamic updates and saves"),
                            Li("MutationObserver catches dynamically added elements"),
                            cls="text-sm space-y-1 list-disc list-inside",
                        ),
                        cls="p-4 bg-blue-50 border border-blue-200 rounded",
                    ),
                    Div(
                        H3("⚡ Performance Features", cls="font-medium mb-2"),
                        Ul(
                            Li("Debounced writes to prevent excessive storage calls"),
                            Li("Automatic cleanup of old or invalid data"),
                            Li("JSON serialization for complex data types"),
                            Li("Error handling for storage quota exceeded"),
                            Li("Fallback behavior when storage is unavailable"),
                            Li("Memory-efficient signal watching"),
                            cls="text-sm space-y-1 list-disc list-inside",
                        ),
                        cls="p-4 bg-green-50 border border-green-200 rounded",
                    ),
                    Div(
                        H3("🚀 Two-Phase Architecture", cls="font-medium mb-2"),
                        Ul(
                            Li("Phase 1: onGlobalInit preprocesses elements before Datastar"),
                            Li("MutationObserver intercepts data-persist elements early"),
                            Li("Updates data-signals attributes with stored values"),
                            Li("Phase 2: onLoad handles runtime persistence"),
                            Li("Watches for signal changes and saves to storage"),
                            Li("Significantly reduces flash on slow connections"),
                            cls="text-sm space-y-1 list-disc list-inside",
                        ),
                        cls="p-4 bg-purple-50 border border-purple-200 rounded",
                    ),
                    cls="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6",
                ),
                cls="mb-12",
            ),
            cls="container mx-auto px-4 py-8 max-w-6xl",
        ),
        # Footer
        Footer(
            P(
                "Persist Handler Demo - Powered by StarHTML Signal Persistence",
                cls="text-center text-sm text-muted-foreground py-8",
            ),
            cls="border-t",
        ),
        cls="min-h-screen bg-background text-foreground",
    )


if __name__ == "__main__":
    print("Persist Handler Demo running on http://localhost:5001")
    serve(port=5001)
