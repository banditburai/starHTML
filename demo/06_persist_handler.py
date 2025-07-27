"""Comprehensive demo showcasing the persist handler capabilities.

This demo shows how to use the persist handler to automatically save and restore
signal values across page reloads using localStorage and sessionStorage.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import json
from pathlib import Path

from starhtml import *
from starhtml.handlers import persist_handler
from starhtml.xtend import Script

# Mocked Server-side todo state management
TODOS_FILE = Path(__file__).parent / "todos.json"


def load_todos():
    """Load todos from persistent storage."""
    if TODOS_FILE.exists():
        try:
            with open(TODOS_FILE) as f:
                return json.load(f)
        except (OSError, json.JSONDecodeError):
            return []
    return []


def save_todos(todos):
    """Save todos to persistent storage."""
    try:
        with open(TODOS_FILE, "w") as f:
            json.dump(todos, f)
    except OSError:
        pass  # Graceful fallback


def render_todo_list(todos):
    """Render the todo list as StarHTML elements."""
    if not todos:
        return Div(P("No todos yet. Add some above!", cls="text-gray-500 italic text-center py-4"), id="todo-list")

    todo_items = []
    for i, todo in enumerate(todos):
        todo_items.append(
            Div(
                Span(todo, cls="flex-1"),
                Button(
                    "×",
                    ds_on_click=f"@delete('todos/{i}')",
                    cls="bg-red-500 hover:bg-red-600 text-white px-2 py-1 rounded text-sm ml-2",
                ),
                cls="flex items-center justify-between p-2 bg-purple-50 border border-purple-200 rounded mb-2",
            )
        )

    # Add clear all button if there are todos
    if todos:
        todo_items.append(
            Button(
                "Clear All Todos",
                ds_on_click="@delete('todos/all')",
                cls="bg-red-500 hover:bg-red-600 text-white px-3 py-1 rounded text-sm mt-2",
            )
        )

    return Div(P("Todo Items:", cls="font-semibold mb-2"), *todo_items, id="todo-list")


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
                            placeholder="Type something and reload the page...",
                            ds_bind="persistedText",
                            cls="w-full p-3 border-2 border-blue-200 rounded-lg mb-3",
                        ),
                        P("Current value: ", Span(ds_text="$persistedText", cls="font-bold text-blue-600")),
                        P("💡 Try typing, then refresh the page!", cls="text-sm text-gray-600 mt-2"),
                        cls="space-y-2",
                    ),
                    ds_signals={"persistedText": ""},
                    ds_persist="persistedText",  # Persist the text signal
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
                            Span(ds_text="$counter || 0", cls="text-2xl font-bold text-green-600"),
                            cls="mb-4",
                        ),
                        Div(
                            Button(
                                "Increment (+1)",
                                ds_on_click="$counter = Number($counter ?? 0) + 1",
                                cls="bg-green-500 hover:bg-green-600 text-white px-4 py-2 rounded mr-2",
                            ),
                            Button(
                                "Add 5 (+5)",
                                ds_on_click="$counter = Number($counter ?? 0) + 5",
                                cls="bg-green-600 hover:bg-green-700 text-white px-4 py-2 rounded mr-2",
                            ),
                            Button(
                                "Reset to 0",
                                ds_on_click="$counter = 0",
                                cls="bg-red-500 hover:bg-red-600 text-white px-4 py-2 rounded",
                            ),
                            cls="space-x-2",
                        ),
                        cls="space-y-3",
                    ),
                    ds_signals={"counter": 0},  # Provide fallback value
                    ds_persist="counter",  # Persist the counter signal
                    cls="p-6 bg-white border-2 border-green-300 rounded-lg shadow-lg mb-8",
                ),
                cls="mb-12",
            ),
            # Todo List with Server-Driven Persistence
            Section(
                H2("Todo List with Server-Driven Persistence", cls="text-2xl font-semibold mb-4"),
                P(
                    "Add items to the list - they'll persist server-side using Datastar SSE:",
                    cls="mb-4 text-muted-foreground",
                ),
                Div(
                    H3("Server-Driven Todo List", cls="font-medium mb-4 text-purple-800"),
                    # Input form
                    Div(
                        Div(
                            Input(
                                name="todo_text",
                                placeholder="Add a todo item...",
                                ds_bind="newTodo",
                                ds_on_keyup__enter="if($newTodo.trim()) { @post('/todos/add'); $newTodo = ''; }",
                                cls="flex-1 p-2 border-2 border-purple-200 rounded-l-lg",
                            ),
                            Button(
                                "Add Todo",
                                ds_on_click="if($newTodo.trim()) { @post('/todos/add'); $newTodo = ''; }",
                                cls="bg-purple-500 hover:bg-purple-600 text-white px-4 py-2 rounded-r-lg",
                            ),
                            cls="flex mb-4",
                        )
                    ),
                    # Todo list container (server-rendered)
                    Div(
                        render_todo_list(load_todos()),  # Load persisted todos
                        id="todo-list",
                    ),
                    ds_signals={"newTodo": ""},
                    cls="p-6 bg-white border-2 border-purple-300 rounded-lg shadow-lg mb-8",
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
                            placeholder="Tab-specific data...",
                            ds_bind="sessionValue",
                            cls="w-full p-3 border-2 border-orange-200 rounded-lg mb-3",
                        ),
                        P("Session value: ", Span(ds_text="$sessionValue", cls="font-bold text-orange-600")),
                        P("🔄 Refresh this tab: data persists", cls="text-sm text-green-600"),
                        P("🆕 Open in new tab: data doesn't persist", cls="text-sm text-red-600"),
                        cls="space-y-2",
                    ),
                    ds_signals={"sessionValue": ""},
                    ds_persist__session="*",  # Use sessionStorage instead of localStorage
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
                            P("Persistent Score: ", Span(ds_text="$persistentScore", cls="font-bold text-teal-600")),
                            P("Temporary Lives: ", Span(ds_text="$temporaryLives", cls="font-bold text-red-600")),
                            cls="mb-4 space-y-2",
                        ),
                        Div(
                            Button(
                                "Add Score (+10)",
                                ds_on_click="$persistentScore += 10",
                                cls="bg-teal-500 hover:bg-teal-600 text-white px-3 py-2 rounded mr-2",
                            ),
                            Button(
                                "Lose Life (-1)",
                                ds_on_click="$temporaryLives = Math.max(0, $temporaryLives - 1)",
                                cls="bg-red-500 hover:bg-red-600 text-white px-3 py-2 rounded mr-2",
                            ),
                            Button(
                                "Reset Lives",
                                ds_on_click="$temporaryLives = 3",
                                cls="bg-gray-500 hover:bg-gray-600 text-white px-3 py-2 rounded",
                            ),
                            cls="space-x-2",
                        ),
                        P("💡 Reload the page: score persists, lives reset to 3", cls="text-sm text-gray-600 mt-4"),
                        cls="space-y-3",
                    ),
                    ds_signals={"persistentScore": 0, "temporaryLives": 3},
                    ds_persist="persistentScore",  # Only persist the score, not lives
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
                                    ds_text="$isDarkMode ? 'Dark' : 'Light'",
                                    cls="font-bold",
                                    ds_class="$isDarkMode ? 'text-gray-200' : 'text-gray-800'",
                                ),
                            ),
                            cls="mb-4",
                        ),
                        Button(
                            Span(ds_text="$isDarkMode ? '☀️ Switch to Light' : '🌙 Switch to Dark'"),
                            ds_on_click="$isDarkMode = !$isDarkMode; document.body.classList.toggle('dark', $isDarkMode);",
                            cls="bg-indigo-500 hover:bg-indigo-600 text-white px-4 py-2 rounded transition-colors",
                        ),
                        P("🔄 Your theme choice persists across page reloads!", cls="text-sm text-gray-600 mt-4"),
                        cls="space-y-3",
                    ),
                    ds_signals={"isDarkMode": False},
                    ds_persist="isDarkMode",
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
                        P("Temp counter: ", Span(ds_text="$tempCounter", cls="font-bold text-gray-600")),
                        P(
                            "This counter will reset on every page reload (persistence disabled).",
                            cls="text-sm text-gray-500 mb-3",
                        ),
                        Button(
                            "Increment (No Persistence)",
                            ds_on_click="$tempCounter++",
                            cls="bg-gray-500 hover:bg-gray-600 text-white px-3 py-2 rounded",
                        ),
                        cls="space-y-2",
                    ),
                    ds_signals={"tempCounter": 0},
                    # No persistence - omit ds_persist attribute
                    cls="p-6 bg-white border-2 border-gray-300 rounded-lg shadow-lg mb-6",
                ),
                # Example with custom storage key
                Div(
                    H3("Custom Storage Key", cls="font-medium mb-4 text-indigo-800"),
                    Div(
                        P("App Version: ", Span(ds_text="$appVersion", cls="font-bold text-indigo-600")),
                        P("User Preference: ", Span(ds_text="$userPref", cls="font-bold text-indigo-600")),
                        P(
                            "These values use a custom storage key: 'starhtml-persist-myapp'",
                            cls="text-sm text-gray-500 mb-3",
                        ),
                        Button(
                            "Update Version",
                            ds_on_click="$appVersion = 'v' + Math.floor(Math.random() * 100)",
                            cls="bg-indigo-500 hover:bg-indigo-600 text-white px-3 py-2 rounded mr-2",
                        ),
                        Button(
                            "Toggle Preference",
                            ds_on_click="$userPref = $userPref === 'compact' ? 'expanded' : 'compact'",
                            cls="bg-indigo-600 hover:bg-indigo-700 text-white px-3 py-2 rounded",
                        ),
                        cls="space-y-2",
                    ),
                    ds_signals={"appVersion": "v1.0", "userPref": "compact"},
                    ds_persist__as_myapp="*",  # Custom storage key
                    cls="p-6 bg-white border-2 border-indigo-300 rounded-lg shadow-lg mb-6",
                ),
                # Example with session storage for specific signal
                Div(
                    H3("Session-Only Specific Signal", cls="font-medium mb-4 text-pink-800"),
                    Div(
                        P("Tab ID: ", Span(ds_text="$tabId", cls="font-bold text-pink-600")),
                        P("Page views: ", Span(ds_text="$pageViews", cls="font-bold text-gray-600")),
                        P(
                            "Only tabId persists in this tab session. Page views reset every reload.",
                            cls="text-sm text-gray-500 mb-3",
                        ),
                        Button(
                            "New Tab ID",
                            ds_on_click="$tabId = Math.random().toString(36).substr(2, 9)",
                            cls="bg-pink-500 hover:bg-pink-600 text-white px-3 py-2 rounded mr-2",
                        ),
                        Button(
                            "Add Page View",
                            ds_on_click="$pageViews++",
                            cls="bg-gray-500 hover:bg-gray-600 text-white px-3 py-2 rounded",
                        ),
                        cls="space-y-2",
                    ),
                    ds_signals={"tabId": "abc123", "pageViews": 1},
                    ds_persist__session="tabId",  # Persist only tabId signal in session storage
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
                            Li('ds_persist="*" - Persist all signals in localStorage'),
                            Li('ds_persist="signal1,signal2" - Persist specific signals only'),
                            Li('ds_persist__session="*" - Use sessionStorage (tab-only)'),
                            Li('ds_persist__as_mykey="*" - Use custom storage key'),
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


# SSE Endpoints for Todo CRUD Operations


@rt("/todos/add", methods=["POST"])
@sse
def add_todo(newTodo: str = ""):
    """Add a new todo item."""
    todo_text = newTodo.strip()

    if not todo_text:
        return  # No content if empty

    # Load current todos, add new one, save
    todos = load_todos()
    todos.append(todo_text)
    save_todos(todos)

    # Use correct StarHTML SSE pattern
    yield elements(render_todo_list(todos), "#todo-list")


@rt("/todos/all", methods=["DELETE"])
@sse
def clear_all_todos():
    """Clear all todo items."""
    save_todos([])

    # Use correct StarHTML SSE pattern
    yield elements(render_todo_list([]), "#todo-list")


@rt("/todos/{index}", methods=["DELETE"])
@sse
def delete_todo(index: int):
    """Delete a specific todo item."""
    todos = load_todos()

    # Remove the item if index is valid
    if 0 <= index < len(todos):
        todos.pop(index)
        save_todos(todos)

    # Use correct StarHTML SSE pattern
    yield elements(render_todo_list(todos), "#todo-list")


if __name__ == "__main__":
    print("Persist Handler Demo running on http://localhost:5001")
    serve(port=5001)
