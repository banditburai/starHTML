"""Todo List MVC - Bold & Improved with working Datastar patterns"""

from dataclasses import asdict, dataclass

from starhtml import *

# Bold app configuration
app, rt = star_app(
    title="✨ Todo List",
    hdrs=[
        Script(src="https://cdn.jsdelivr.net/npm/@tailwindcss/browser@4"),
        persist_handler(),
        Style("""
            /* Design System */
            :root {
                --gradient-primary: linear-gradient(135deg, #8b5cf6 0%, #ec4899 100%);
                --gradient-secondary: linear-gradient(135deg, #3b82f6 0%, #06b6d4 100%);
                --gradient-success: linear-gradient(135deg, #10b981 0%, #34d399 100%);
                --gradient-danger: linear-gradient(135deg, #ef4444 0%, #f97316 100%);
                --shadow-bold: 0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04);
                --shadow-glow: 0 0 20px rgba(139, 92, 246, 0.3);
            }
            
            body {
                background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%);
                font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
            }
            
            .hero-text {
                background: var(--gradient-primary);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
                background-clip: text;
                font-weight: 900;
                filter: drop-shadow(2px 2px 4px rgba(0,0,0,0.1));
            }
            
            .todo-item {
                transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
                border-left: 4px solid transparent;
                background: white;
                border-radius: 16px;
                box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
            }
            .todo-item:hover {
                transform: translateY(-2px) scale(1.02);
                box-shadow: var(--shadow-bold);
                border-left-color: #8b5cf6;
                background: linear-gradient(135deg, #ffffff 0%, #faf5ff 100%);
            }
            .todo-completed {
                opacity: 0.7;
                transform: scale(0.98);
            }
            .todo-completed .todo-text {
                text-decoration: line-through;
            }
            .delete-btn {
                transition: all 0.3s ease;
                opacity: 0;
                background: transparent !important;
            }
            .delete-btn iconify-icon {
                color: #8b5cf6;
                transition: all 0.3s ease;
            }
            .todo-item:hover .delete-btn {
                opacity: 1;
                transform: rotate(0deg);
            }
            .delete-btn:hover {
                transform: rotate(90deg) scale(1.1);
                background: transparent !important;
            }
            .delete-btn:hover iconify-icon {
                color: #ef4444;
            }
            
            /* Filter Tab Group Styling */
            .filter-group {
                background: #f8fafc;
                padding: 4px;
                border-radius: 16px;
                border: 1px solid #e2e8f0;
                display: inline-flex;
                box-shadow: 0 1px 3px rgba(0, 0, 0, 0.06);
            }
            
            .filter-btn {
                transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
                font-weight: 600;
                border-radius: 12px;
                position: relative;
                overflow: hidden;
                background: transparent;
                color: #6b7280;
                border: none;
                white-space: nowrap;
            }
            .filter-btn:hover {
                background: rgba(139, 92, 246, 0.1);
                color: #8b5cf6;
            }
            .filter-btn.active {
                background: var(--gradient-primary);
                color: white;
                box-shadow: 0 2px 4px rgba(139, 92, 246, 0.2);
                opacity: 0.85;
            }
            .filter-btn:hover .filter-badge,
            .filter-btn.active .filter-badge {
                background: rgba(255, 255, 255, 0.3);
                color: inherit;
            }
            .filter-badge {
                background: rgba(139, 92, 246, 0.1);
                color: #8b5cf6;
                border: none;
            }
            .filter-btn.active .filter-badge {
                background: rgba(255, 255, 255, 0.3);
                color: white;
            }
            
            .checkbox-button {
                background: transparent !important;
            }
            .checkbox-button:hover {
                background: transparent !important;
            }
            .checkbox-button:hover iconify-icon {
                transform: scale(1.15);
                filter: drop-shadow(0 4px 8px rgba(139, 92, 246, 0.3));
            }
            
            .todo-text {
                outline: none;
                border-radius: 12px;
                transition: all 0.3s ease;
            }
            .todo-text:focus {
                background: linear-gradient(135deg, #faf5ff 0%, #f3e8ff 100%) !important;
                box-shadow: 0 0 0 2px rgba(139, 92, 246, 0.3), 0 4px 12px rgba(139, 92, 246, 0.1);
                outline: none;
                transform: translateY(-1px);
            }
            .icon-sm {
                width: 24px;
                height: 24px;
            }
            
            .bold-button {
                background: var(--gradient-primary);
                font-weight: 800;
                border-radius: 12px;
                transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
                box-shadow: 0 4px 14px 0 rgba(139, 92, 246, 0.4);
            }
            .bold-button:hover {
                transform: translateY(-3px);
                box-shadow: 0 8px 25px 0 rgba(139, 92, 246, 0.6);
            }
            .bold-button:active {
                transform: translateY(-1px);
            }
            .bold-button:disabled {
                transform: none;
                opacity: 0.6;
                cursor: not-allowed;
            }
            
            .bold-input {
                border: 3px solid #e5e7eb;
                border-radius: 12px;
                font-weight: 600;
                transition: all 0.3s ease;
                background: white;
                outline: none;
            }
            .bold-input:focus {
                border-color: #8b5cf6;
                box-shadow: 0 0 0 3px rgba(139, 92, 246, 0.1), var(--shadow-glow);
                transform: translateY(-1px);
                outline: none;
            }
            
            .progress-container {
                background: white;
                border-radius: 16px;
                padding: 24px;
                box-shadow: var(--shadow-bold);
                border: 1px solid #f3f4f6;
            }
            
            .progress-bar {
                background: linear-gradient(90deg, #ec4899 0%, #8b5cf6 50%, #3b82f6 100%);
                border-radius: 12px;
                transition: all 0.6s cubic-bezier(0.4, 0, 0.2, 1);
                position: relative;
                overflow: hidden;
            }
            .progress-bar::after {
                content: '';
                position: absolute;
                top: 0;
                left: -100%;
                width: 100%;
                height: 100%;
                background: linear-gradient(90deg, transparent, rgba(255,255,255,0.4), transparent);
                animation: shimmer 2s infinite;
            }
            @keyframes shimmer {
                0% { left: -100%; }
                100% { left: 100%; }
            }
            
            .stat-card {
                background: white;
                border-radius: 16px;
                padding: 20px;
                box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
                border: 1px solid #f3f4f6;
                transition: all 0.3s ease;
            }
            .stat-card:hover {
                transform: translateY(-4px);
                box-shadow: var(--shadow-bold);
            }
            
            .empty-state {
                background: white;
                border-radius: 20px;
                padding: 48px 24px;
                text-align: center;
                box-shadow: var(--shadow-bold);
                border: 2px dashed #d1d5db;
            }
            
            @keyframes slideIn {
                from {
                    opacity: 0;
                    transform: translateX(-20px);
                }
                to {
                    opacity: 1;
                    transform: translateX(0);
                }
            }
            .slide-in {
                animation: slideIn 0.3s ease-out;
            }
            

            /* Footer Stats - HUD Style */
            .stats-footer {
                margin-top: 80px;
                background: rgba(255, 255, 255, 0.95);
                backdrop-filter: blur(10px);
                border-top: 1px solid rgba(139, 92, 246, 0.2);
                padding: 24px;
                border-radius: 24px 24px 0 0;
                box-shadow: 0 -10px 25px -5px rgba(0, 0, 0, 0.1);
            }
            
            .footer-stat {
                display: flex;
                flex-direction: column;
                align-items: center;
                justify-content: center;
                transition: all 0.3s ease;
                padding: 12px;
                border-radius: 12px;
            }
            
            .footer-stat:hover {
                background: rgba(139, 92, 246, 0.1);
                transform: translateY(-2px);
            }
            
            .footer-stat-value {
                font-size: 1.75rem;
                font-weight: 900;
                color: #1f2937;
                line-height: 1;
            }
            
            .footer-stat-label {
                font-size: 0.75rem;
                font-weight: 600;
                color: #6b7280;
                text-transform: uppercase;
                letter-spacing: 0.05em;
                margin-top: 4px;
            }
        """),
    ],
)

# ============================================================================
#  Todo Data Model
# ============================================================================


@dataclass
class Todo:
    """Todo item with serialization support."""

    id: int
    text: str
    completed: bool = False

    def to_dict(self):
        return asdict(self)


# In-memory storage (in production, use a database)
todos_store: list[Todo] = [
    Todo(1, "Learn Datastar patterns", False),
    Todo(2, "Build a clean todo app", False),
    Todo(3, "Master reactive programming", True),
]
next_id = 4

# ============================================================================
#  Components
# ============================================================================


def render_todo_item(todo: Todo):
    """Render a single todo item with bold styling."""
    # Visibility based on filter
    show_condition = (
        f"($active_filter === 'all') || "
        f"($active_filter === 'active' && !$todos.find(t => t.id === {todo.id}).completed) || "
        f"($active_filter === 'completed' && $todos.find(t => t.id === {todo.id}).completed)"
    )

    return Div(
        # Checkbox button
        Button(
            Icon(
                "mdi:checkbox-marked" if todo.completed else "mdi:checkbox-blank-outline",
                cls="text-3xl text-purple-500",
            ),
            ds_on_click(f"@post('todos/{todo.id}/toggle')"),
            cls="checkbox-button p-3 rounded-xl transition-all",
        ),
        # Todo text - bold contenteditable
        Div(
            todo.text,
            ds_on_blur(f"@post('todos/{todo.id}/edit', {{text: evt.target.innerText.trim()}})"),
            contenteditable="true",
            style="white-space: pre-wrap;",
            cls="todo-text flex-1 px-4 py-3 rounded-xl cursor-text font-semibold text-gray-800 hover:bg-gray-50",
        ),
        # Delete button
        Button(
            Icon("lucide:trash-2", cls="icon-sm"),
            ds_on_click(f"@delete('todos/{todo.id}')"),
            cls="delete-btn p-3 rounded-xl transition-all",
        ),
        # Container attributes with visibility
        ds_show(show_condition),
        ds_class(**{"todo-completed": todo.completed}),
        cls="todo-item slide-in flex items-center gap-3 p-2 mb-3",
        data_todo_id=str(todo.id),
    )


def render_empty_state():
    """Render bold empty state message."""
    return Div(
        Icon("lucide:sparkles", cls="text-6xl mx-auto mb-6 text-purple-400"),
        H3("No todos yet!", cls="text-2xl font-black text-gray-800 mb-3"),
        P("Add your first todo above and start conquering your day!", cls="text-lg font-medium text-gray-600"),
        cls="empty-state",
    )


def render_filter_button(label: str, filter_value: str, count: str = None):
    """Render a bold filter button."""
    return Button(
        label,
        Span(
            ds_text(f"${count}") if count else None,
            cls="filter-badge ml-2 px-2.5 py-1 bg-gray-200 rounded-full text-xs font-bold",
        )
        if count is not None
        else None,
        ds_on_click(f"$active_filter = '{filter_value}'"),
        ds_class(active=f"$active_filter === '{filter_value}'"),
        cls="filter-btn px-6 py-3 text-sm font-bold",
    )


# ============================================================================
#  Main Page
# ============================================================================


@rt("/")
def home():
    """Bold todo app home page."""
    return Div(
        # Hero Header
        Header(
            H1("✨ Todo Conqueror", cls="hero-text text-6xl font-black mb-4"),
            P("Dominate your tasks", cls="text-xl font-semibold text-gray-600"),
            cls="text-center py-12 mb-8",
        ),
        # Main container
        Main(
            Div(
                # Chunky progress bar
                Div(
                    Div(
                        Div(
                            ds_style(width="$progress_percent + '%'"),
                            cls="h-6 bg-gradient-to-r from-pink-400/60 via-purple-400/60 to-blue-400/60 rounded-full transition-all duration-700 ease-out",
                        ),
                        cls="w-full bg-gray-200/50 rounded-full h-6 overflow-hidden shadow-inner",
                    ),
                    Div(
                        Span(ds_text("$progress_percent + '% complete'"), cls="text-sm font-medium text-gray-600"),
                        Span(
                            ds_text("$completed_count + ' of ' + $todos.length + ' done'"),
                            cls="text-sm font-medium text-gray-500",
                        ),
                        cls="flex justify-between mt-3",
                    ),
                    cls="mb-8 opacity-80",
                ),
                # Combined todo management section
                Div(
                    # Add todo form (now inside the list container)
                    Div(
                        Form(
                            Div(
                                Textarea(
                                    ds_bind("todo_text"),
                                    ds_on_keydown(
                                        "if(evt.key === 'Enter' && !evt.shiftKey) { evt.preventDefault(); if($can_add_todo) { @post('todos/add', {todo_text: $todo_text}); } }"
                                    ),
                                    placeholder="What challenge will you conquer today?",
                                    autofocus=True,
                                    rows="1",
                                    cls="bold-input flex-1 px-6 py-4 text-lg font-semibold resize-none overflow-hidden",
                                    style="field-sizing: content; min-height: 3.5rem; max-height: 10rem;",
                                ),
                                Button(
                                    Icon("lucide:plus", cls="text-lg mr-2"),
                                    "Add",
                                    ds_on_click("@post('todos/add', {todo_text: $todo_text})"),
                                    ds_disabled("!$can_add_todo"),
                                    type="button",
                                    cls="bold-button px-6 py-4 text-lg font-bold text-white flex items-center",
                                ),
                                cls="flex gap-4",
                            ),
                            # Character count
                            Div(
                                Span(
                                    ds_text("$todo_error"),
                                    ds_show("$todo_error"),
                                    cls="text-red-500 text-sm font-medium",
                                ),
                                Span(
                                    ds_text("$todo_text.length + '/200'"),
                                    ds_class(
                                        **{
                                            "text-orange-500": "$todo_text.length > 150",
                                            "text-red-500": "$todo_text.length > 200",
                                        }
                                    ),
                                    cls="text-sm font-medium ml-auto text-gray-500",
                                ),
                                cls="flex justify-between mt-3 min-h-[1.25rem]",
                            ),
                            cls="mb-0",
                        ),
                        cls="border-b border-gray-200 pb-6 mb-6",
                    ),
                    # Filter buttons (now connected to list)
                    Div(
                        Div(
                            render_filter_button("All Quests", "all", "todos.length"),
                            render_filter_button("Active Battles", "active", "active_count"),
                            render_filter_button("Conquered", "completed", "completed_count"),
                            cls="filter-group",
                        ),
                        cls="flex justify-center mb-6",
                    ),
                    # Todo list container
                    Div(
                        # Render all todos - visibility controlled by filter in each item
                        *[render_todo_item(todo) for todo in todos_store],
                        # Empty state shown when no filtered todos
                        Div(render_empty_state(), ds_show("$filtered_todos.length === 0"), cls="empty-state-container")
                        if todos_store
                        else render_empty_state(),
                        id="todo-list",
                        cls="min-h-[200px]",
                    ),
                    # Clear completed button
                    Div(
                        Button(
                            Icon("lucide:trash", cls="text-xl mr-3"),
                            "Clear Conquered",
                            ds_on_click(
                                "if(confirm('Remove all conquered todos?')) { @delete('todos/clear-completed'); }"
                            ),
                            ds_show("$completed_count > 0"),
                            cls="px-6 py-3 bg-gradient-to-r from-red-500 to-pink-500 text-white rounded-xl font-bold hover:shadow-lg transition-all flex items-center",
                        ),
                        cls="mt-8 text-center",
                    ),
                    cls="bg-white p-8 rounded-2xl shadow-2xl border border-gray-100",
                ),
                cls="max-w-4xl mx-auto",
            ),
            cls="container mx-auto px-6 py-8",
        ),
        # Initialize signals
        ds_signals(todos=[todo.to_dict() for todo in todos_store], todo_text="", active_filter="all"),
        # Computed signals for derived state
        ds_computed("completed_count", "$todos.filter(t => t.completed).length"),
        ds_computed("active_count", "$todos.filter(t => !t.completed).length"),
        ds_computed("progress_percent", "Math.round($completed_count / Math.max($todos.length, 1) * 100)"),
        # Validation computed signals
        ds_computed(
            "todo_error",
            "$todo_text.length === 0 ? '' : " + "$todo_text.length > 200 ? 'Too long (max 200 chars)' : ''",
        ),
        ds_computed("can_add_todo", "$todo_text.trim().length > 0 && !$todo_error"),
        # Filtered todos based on active filter
        ds_computed(
            "filtered_todos",
            """
            $todos.filter(t =>
                $active_filter === 'all' ||
                ($active_filter === 'active' && !t.completed) ||
                ($active_filter === 'completed' && t.completed)
            )
        """,
        ),
        # Simple persistence
        ds_persist("todos", "active_filter", key="starhtml-todo"),
        # Stats Footer - Appears at bottom of content
        Div(
            Div(
                Div(
                    Div(
                        Span(ds_text("$completed_count"), cls="footer-stat-value"),
                        Span("Completed", cls="footer-stat-label"),
                        cls="footer-stat",
                    ),
                    Div(
                        Span(ds_text("$active_count"), cls="footer-stat-value"),
                        Span("Active", cls="footer-stat-label"),
                        cls="footer-stat",
                    ),
                    Div(
                        Span(ds_text("$todos.length"), cls="footer-stat-value"),
                        Span("Total", cls="footer-stat-label"),
                        cls="footer-stat",
                    ),
                    Div(
                        Span(ds_text("$progress_percent + '%'"), cls="footer-stat-value"),
                        Span("Progress", cls="footer-stat-label"),
                        cls="footer-stat",
                    ),
                    cls="grid grid-cols-2 md:grid-cols-4 gap-4 max-w-4xl mx-auto",
                ),
                cls="max-w-6xl mx-auto",
            ),
            cls="stats-footer",
        ),
        cls="min-h-screen",
    )


# ============================================================================
#  SSE Endpoints
# ============================================================================


@rt("/todos/add", methods=["POST"])
@sse
def add_todo(req, todo_text: str = ""):
    """Add a new todo - simplified."""
    global next_id

    # Get text from parameter
    text = todo_text.strip()
    if not text or len(text) > 200:
        return

    # Create new todo
    new_todo = Todo(id=next_id, text=text)
    todos_store.append(new_todo)
    next_id += 1

    # Surgical update - append just the new item
    yield elements(
        render_todo_item(new_todo),
        "#todo-list",  # Target the todo list container
        "append",
    )

    # Update signals
    yield signals(
        todos=[todo.to_dict() for todo in todos_store],
        todo_text="",  # Clear input
    )


@rt("/todos/{todo_id}/toggle", methods=["POST"])
@sse
def toggle_todo(req, todo_id: str):
    """Toggle todo completion - surgical update."""
    todo_id = int(todo_id)

    # Find and toggle
    for todo in todos_store:
        if todo.id == todo_id:
            todo.completed = not todo.completed

            # Surgical update - replace just this item
            yield elements(render_todo_item(todo), f'[data-todo-id="{todo_id}"]', "outer")

            # Update signals for computed values
            yield signals(todos=[todo.to_dict() for todo in todos_store])
            break


@rt("/todos/{todo_id}/edit", methods=["POST"])
@sse
def edit_todo(req, todo_id: str, text: str = ""):
    """Edit todo text."""
    todo_id = int(todo_id)
    text = text.strip()

    if not text or len(text) > 200:
        return

    # Find and update
    for todo in todos_store:
        if todo.id == todo_id:
            todo.text = text
            # Update signals only - contenteditable already shows the text
            yield signals(todos=[todo.to_dict() for todo in todos_store])
            break


@rt("/todos/clear-completed", methods=["DELETE"])
@sse
def clear_completed(req):
    """Clear all completed todos."""
    global todos_store

    # Get IDs to remove for surgical updates
    completed_ids = [t.id for t in todos_store if t.completed]

    # Remove from store
    todos_store = [t for t in todos_store if not t.completed]

    # Surgical removal - remove each completed item
    for todo_id in completed_ids:
        yield elements("", f'[data-todo-id="{todo_id}"]', "outer")

    # Update signals
    yield signals(todos=[todo.to_dict() for todo in todos_store])


@rt("/todos/{todo_id}", methods=["DELETE"])
@sse
def delete_todo(req, todo_id: str):
    """Delete a single todo - surgical removal."""
    global todos_store
    todo_id = int(todo_id)

    # Remove from store
    todos_store = [t for t in todos_store if t.id != todo_id]

    # Surgical removal
    yield elements("", f'[data-todo-id="{todo_id}"]', "outer")

    # Update signals
    yield signals(todos=[todo.to_dict() for todo in todos_store])


if __name__ == "__main__":
    print("=" * 60)
    print("🚀 TODO CONQUEROR")
    print("=" * 60)
    print("📍 Running on: http://localhost:5001")
    print("🎨 Design: Bold typography, vibrant gradients, smooth animations")
    print("⚡ Features:")
    print("   • Working Datastar patterns")
    print("   • Bold visual design")
    print("   • Smooth animations")
    print("   • Stats dashboard")
    print("   • Persistent state")
    print("=" * 60)
    serve(port=5001)
