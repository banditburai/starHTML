"""Todo List MVC - Bold & Improved with working Datastar patterns"""

from dataclasses import asdict, dataclass

from starhtml import *

# Bold app configuration
app, rt = star_app(
    title="✨ Todo List",
    iconify=True,
    compression=False,
    hdrs=[
        Script(src="https://cdn.jsdelivr.net/npm/@tailwindcss/browser@4"),
        persist_handler(),
        Style(
            """:root{--gradient-primary:linear-gradient(135deg,#8b5cf6 0%,#ec4899 100%);--gradient-secondary:linear-gradient(135deg,#3b82f6 0%,#06b6d4 100%);--gradient-success:linear-gradient(135deg,#10b981 0%,#34d399 100%);--gradient-danger:linear-gradient(135deg,#ef4444 0%,#f97316 100%);--shadow-bold:0 20px 25px -5px rgba(0,0,0,0.1),0 10px 10px -5px rgba(0,0,0,0.04);--shadow-glow:0 0 20px rgba(139,92,246,0.3)}body{background:linear-gradient(135deg,#f8fafc 0%,#e2e8f0 100%);font-family:'Inter',-apple-system,BlinkMacSystemFont,sans-serif}.hero-text{background:var(--gradient-primary);-webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text;font-weight:900;filter:drop-shadow(2px 2px 4px rgba(0,0,0,0.1))}.todo-item{transition:all 0.3s cubic-bezier(0.4,0,0.2,1);border-left:4px solid transparent;background:white;border-radius:16px;box-shadow:0 4px 6px -1px rgba(0,0,0,0.1)}.todo-item:hover{transform:translateY(-2px) scale(1.02);box-shadow:var(--shadow-bold);border-left-color:#8b5cf6;background:linear-gradient(135deg,#ffffff 0%,#faf5ff 100%)}.todo-item:hover .delete-btn{opacity:1;transform:rotate(0deg)}.todo-completed{opacity:0.7;transform:scale(0.98)}.todo-completed .todo-text{text-decoration:line-through}.delete-btn,.checkbox-button{background:transparent !important;transition:all 0.3s ease}.delete-btn{opacity:0}.delete-btn iconify-icon{color:#8b5cf6;transition:all 0.3s ease}.delete-btn:hover{transform:rotate(90deg) scale(1.1);background:transparent !important}.delete-btn:hover iconify-icon{color:#ef4444}.checkbox-button:hover{background:transparent !important}.checkbox-button:hover iconify-icon{transform:scale(1.15);filter:drop-shadow(0 4px 8px rgba(139,92,246,0.3))}.filter-group{background:#f8fafc;padding:8px;border-radius:24px;border:1px solid #e2e8f0;display:inline-flex;gap:8px;box-shadow:0 1px 3px rgba(0,0,0,0.06)}.filter-btn{transition:all 0.3s cubic-bezier(0.4,0,0.2,1);font-weight:600;border-radius:20px;position:relative;overflow:hidden;background:transparent;color:#6b7280;border:none;white-space:nowrap;padding:10px 20px}.filter-btn:hover{background:rgba(139,92,246,0.1);color:#8b5cf6}.filter-btn.active{background:linear-gradient(135deg,rgba(139,92,246,0.85) 0%,rgba(168,85,247,0.85) 100%);color:white;box-shadow:0 4px 12px rgba(139,92,246,0.25)}.filter-btn:hover .filter-badge,.filter-btn.active .filter-badge{background:rgba(255,255,255,0.3);color:inherit}.filter-badge{background:rgba(139,92,246,0.1);color:#8b5cf6;border:none}.filter-btn.active .filter-badge{background:rgba(255,255,255,0.3);color:white}.counter-active{background:rgba(255,255,255,0.25) !important;color:white !important}.todo-text{outline:none;border-radius:12px;transition:all 0.3s ease}.todo-text:focus{background:linear-gradient(135deg,#faf5ff 0%,#f3e8ff 100%) !important;box-shadow:0 0 0 2px rgba(139,92,246,0.3),0 4px 12px rgba(139,92,246,0.1);outline:none;transform:translateY(-1px)}.icon-sm{width:24px;height:24px}.bold-button{background:var(--gradient-primary);font-weight:800;border-radius:12px;transition:all 0.3s cubic-bezier(0.4,0,0.2,1);box-shadow:0 4px 14px 0 rgba(139,92,246,0.4)}.bold-button:hover{transform:translateY(-3px);box-shadow:0 8px 25px 0 rgba(139,92,246,0.6)}.bold-button:active{transform:translateY(-1px)}.bold-button:disabled{transform:none;opacity:0.6;cursor:not-allowed}.bold-input{border:3px solid #e5e7eb;border-radius:12px;font-weight:600;transition:all 0.3s ease;background:white;outline:none}.bold-input:focus{border-color:#8b5cf6;box-shadow:0 0 0 3px rgba(139,92,246,0.1),var(--shadow-glow);transform:translateY(-1px);outline:none}.progress-container,.stat-card,.empty-state{background:white;border-radius:16px;box-shadow:var(--shadow-bold);border:1px solid #f3f4f6}.progress-container{padding:24px}.stat-card{padding:20px;box-shadow:0 4px 6px -1px rgba(0,0,0,0.1);transition:all 0.3s ease}.stat-card:hover{transform:translateY(-4px);box-shadow:var(--shadow-bold)}.empty-state{border-radius:20px;padding:48px 24px;text-align:center;border:2px dashed #d1d5db}.progress-bar{background:linear-gradient(90deg,#ec4899 0%,#8b5cf6 50%,#3b82f6 100%);border-radius:12px;transition:all 0.6s cubic-bezier(0.4,0,0.2,1);position:relative;overflow:hidden}.progress-bar::after{content:'';position:absolute;top:0;left:-100%;width:100%;height:100%;background:linear-gradient(90deg,transparent,rgba(255,255,255,0.4),transparent);animation:shimmer 2s infinite}@keyframes shimmer{0%{left:-100%}100%{left:100%}}@keyframes slideIn{from{opacity:0;transform:translateX(-20px)}to{opacity:1;transform:translateX(0)}}.slide-in{animation:slideIn 0.3s ease-out}.stats-footer{margin-top:80px;background:rgba(255,255,255,0.95);backdrop-filter:blur(10px);border-top:1px solid rgba(139,92,246,0.2);padding:24px;border-radius:24px 24px 0 0;box-shadow:0 -10px 25px -5px rgba(0,0,0,0.1)}.footer-stat{display:flex;flex-direction:column;align-items:center;justify-content:center;transition:all 0.3s ease;padding:12px;border-radius:12px}.footer-stat:hover{background:rgba(139,92,246,0.1);transform:translateY(-2px)}.footer-stat-value{font-size:1.75rem;font-weight:900;color:#1f2937;line-height:1}.footer-stat-label{font-size:0.75rem;font-weight:600;color:#6b7280;text-transform:uppercase;letter-spacing:0.05em;margin-top:4px}"""
        ),
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


def render_todo_item(todo: Todo, active_filter: Signal):
    """Render a single todo item with bold styling."""
    is_completed = value(todo.completed)

    show_condition = (
        active_filter.eq("all")
        | (active_filter.eq("active") & ~is_completed)
        | (active_filter.eq("completed") & is_completed)
    )

    return Div(
        # Checkbox button
        Button(
            Icon(
                "mdi:checkbox-marked" if todo.completed else "mdi:checkbox-blank-outline",
                cls="text-3xl text-purple-500",
            ),
            data_on_click=post(f"todos/{todo.id}/toggle"),
            cls="checkbox-button p-3 rounded-xl transition-all",
        ),
        # Todo text - bold contenteditable
        Div(
            todo.text,
            data_on_blur=post(f"todos/{todo.id}/edit", text="evt.target.innerText.trim()"),
            contenteditable="true",
            style="white-space: pre-wrap;",
            cls="todo-text flex-1 px-4 py-3 rounded-xl cursor-text font-semibold text-gray-800 hover:bg-gray-50",
        ),
        # Delete button
        Button(
            Icon("lucide:trash-2", cls="icon-sm"),
            data_on_click=delete(f"todos/{todo.id}"),
            cls="delete-btn p-3 rounded-xl transition-all",
        ),
        # Container attributes with visibility
        cls="todo-item slide-in flex items-center gap-3 p-2 mb-3",
        data_class_todo_completed=is_completed,
        data_todo_id=str(todo.id),
        data_show=show_condition,
    )


def render_empty_state():
    """Render bold empty state message."""
    return Div(
        Icon("lucide:sparkles", cls="text-6xl mx-auto mb-6 text-purple-400"),
        H3("No todos yet!", cls="text-2xl font-black text-gray-800 mb-3"),
        P("Add your first todo above and start conquering your day!", cls="text-lg font-medium text-gray-600"),
        cls="empty-state",
    )


def render_filter_button(
    full_label: str,
    short_label: str,
    filter_value: str,
    count: int | Expr | Signal | None = None,
    active_filter: Signal | None = None,
):
    """Render a pill-shaped tab button."""
    return Button(
        Span(
            Span(full_label, cls="hidden sm:inline"),
            Span(short_label, cls="sm:hidden"),
        ),
        Span(
            cls="ml-2 min-w-[24px] h-6 px-1.5 flex items-center justify-center text-xs rounded-full font-bold transition-all bg-purple-200 text-purple-700",
            data_class_counter_active=active_filter == filter_value,
            data_text=count,
            data_show=count > 0,  # Show counter only when count > 0
        )
        if count is not None
        else None,  # Always include the span if count is provided
        data_on_click=active_filter.set(filter_value),
        cls="filter-btn px-6 py-3 text-sm font-semibold rounded-full transition-all duration-200 flex items-center justify-center",
        data_class_active=active_filter == filter_value,
    )


# ============================================================================
#  Main Page
# ============================================================================


@rt("/")
def home():
    """Bold todo app home page."""
    # Calculate actual values from Python data
    completed = sum(1 for todo in todos_store if todo.completed)
    total = len(todos_store)
    initial_progress = round((completed / total * 100) if total > 0 else 0)

    return Div(
        # Only signals for UI state and counts - NOT the actual todo data
        (todo_text := Signal("todo_text", "")),
        (active_filter := Signal("active_filter", "all")),
        (total_count := Signal("total_count", total)),
        (completed_count := Signal("completed_count", completed)),
        (active_count := Signal("active_count", total - completed)),
        # Computed signals for derived state and validation
        (
            progress_percent := Signal(
                "progress_percent", js("Math.round($completed_count / Math.max($total_count, 1) * 100)")
            )
        ),
        (
            todo_error := Signal(
                "todo_error",
                js("$todo_text.length === 0 ? '' : $todo_text.length > 200 ? 'Too long (max 200 chars)' : ''"),
            )
        ),
        (can_add_todo := Signal("can_add_todo", js("$todo_text.trim().length > 0 && !$todo_error"))),
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
                            cls="h-6 bg-gradient-to-r from-pink-400/60 via-purple-400/60 to-blue-400/60 rounded-full transition-all duration-700 ease-out",
                            style=f"width: {initial_progress}%",
                            data_attr_style="width: " + progress_percent + "%",
                        ),
                        cls="w-full bg-gray-200/50 rounded-full h-6 overflow-hidden shadow-inner",
                    ),
                    Div(
                        Span(cls="text-sm font-medium text-gray-600", data_text=(progress_percent + "% complete")),
                        Span(
                            cls="text-sm font-medium text-gray-500",
                            data_text=f("{c} of {t} done", c=completed_count, t=total_count),
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
                                    placeholder="What challenge will you conquer today?",
                                    autofocus=True,
                                    rows="1",
                                    cls="bold-input flex-1 px-6 py-4 text-lg font-semibold resize-none overflow-hidden",
                                    style="field-sizing: content; min-height: 3.5rem; max-height: 10rem;",
                                    data_bind=todo_text,
                                    # Enter submits (but not Shift+Enter for newlines)
                                    data_on_keydown=js(
                                        "if(evt.key === 'Enter' && !evt.shiftKey) { evt.preventDefault(); if($can_add_todo) { @post('todos/add', {todo_text: $todo_text}); } }"
                                    ),
                                ),
                                Button(
                                    Icon("lucide:plus", cls="text-lg mr-2"),
                                    "Add",
                                    type="button",
                                    cls="bold-button px-6 py-4 text-lg font-bold text-white flex items-center",
                                    data_on_click=post("/todos/add", todo_text=todo_text),
                                    data_attr_disabled=~can_add_todo,
                                ),
                                cls="flex gap-4",
                            ),
                            # Character count
                            Div(
                                Span(
                                    cls="text-red-500 text-sm font-medium",
                                    data_text=todo_error,
                                    data_show=todo_error,
                                ),
                                Span(
                                    cls="text-sm font-medium ml-auto text-gray-500",
                                    data_text=todo_text.length + "/200",
                                    # Color based on length thresholds
                                    data_attr_class=switch(
                                        [
                                            (todo_text.length > 200, "text-red-500"),
                                            (todo_text.length > 150, "text-orange-500"),
                                        ]
                                    ),
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
                            render_filter_button("All Quests", "All", "all", total_count, active_filter),
                            render_filter_button("Active Battles", "Active", "active", active_count, active_filter),
                            render_filter_button("Conquered", "Done", "completed", completed_count, active_filter),
                            cls="filter-group",
                        ),
                        cls="flex justify-center mb-6",
                    ),
                    # Todo list container
                    Div(
                        # Render all todos - visibility controlled by filter in each item
                        *[render_todo_item(todo, active_filter) for todo in todos_store],
                        # Empty state - show when no todos exist
                        render_empty_state() if not todos_store else None,
                        id="todo-list",
                        cls="min-h-[200px]",
                    ),
                    # Clear completed button
                    Div(
                        Button(
                            Icon("lucide:trash", cls="text-xl mr-3"),
                            "Clear Conquered",
                            data_on_click=js('confirm("Remove all conquered todos?")')
                            & delete("todos/clear-completed"),
                            data_show=completed_count > 0,
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
        # Stats Footer - Appears at bottom of content
        Div(
            Div(
                Div(
                    Div(
                        Span(cls="footer-stat-value", data_text=completed_count),
                        Span("Completed", cls="footer-stat-label"),
                        cls="footer-stat",
                    ),
                    Div(
                        Span(cls="footer-stat-value", data_text=active_count),
                        Span("Active", cls="footer-stat-label"),
                        cls="footer-stat",
                    ),
                    Div(
                        Span(cls="footer-stat-value", data_text=total_count),
                        Span("Total", cls="footer-stat-label"),
                        cls="footer-stat",
                    ),
                    Div(
                        Span(cls="footer-stat-value", data_text=progress_percent + "%"),
                        Span("Progress", cls="footer-stat-label"),
                        cls="footer-stat",
                    ),
                    cls="grid grid-cols-2 md:grid-cols-4 gap-4 max-w-4xl mx-auto",
                ),
                cls="max-w-6xl mx-auto",
            ),
            cls="stats-footer",
        ),
        # All keyword arguments must go at the end
        cls="min-h-screen",
    )


# ============================================================================
#  SSE Endpoints
# ============================================================================


@rt("/todos/add", methods=["POST"])
@sse
def add_todo(req, todo_text: str = "", active_filter: Signal = None):
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

    yield elements(
        render_todo_item(new_todo, active_filter),
        "#todo-list",  # Target the todo list container
        "append",
    )

    # Update only counts, not the full todos array
    completed = sum(1 for t in todos_store if t.completed)
    total = len(todos_store)
    yield signals(
        total_count=total,
        completed_count=completed,
        active_count=total - completed,
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
            # Create a dummy Signal since we're just updating structure, not filter logic
            yield elements(
                render_todo_item(todo, Signal("active_filter", "all")), f'[data-todo-id="{todo_id}"]', "outer"
            )

            # Update only counts
            completed = sum(1 for t in todos_store if t.completed)
            total = len(todos_store)
            yield signals(
                completed_count=completed,
                active_count=total - completed,
            )
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
            # No signal updates needed - text change doesn't affect counts
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

    # Update counts
    total = len(todos_store)
    yield signals(
        total_count=total,
        completed_count=0,  # We just cleared all completed
        active_count=total,  # All remaining are active
    )


@rt("/todos/{todo_id}", methods=["DELETE"])
@sse
def delete_todo(req, todo_id: str):
    """Delete a single todo - surgical removal."""
    global todos_store
    todo_id = int(todo_id)

    # Check if it was completed before removing
    any(t.id == todo_id and t.completed for t in todos_store)

    # Remove from store
    todos_store = [t for t in todos_store if t.id != todo_id]

    # Surgical removal
    yield elements("", f'[data-todo-id="{todo_id}"]', "outer")

    # Update counts
    completed = sum(1 for t in todos_store if t.completed)
    total = len(todos_store)
    yield signals(
        total_count=total,
        completed_count=completed,
        active_count=total - completed,
    )

    # Show empty state if no todos left
    if not todos_store:
        yield elements(render_empty_state(), "#todo-list", "inner")


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
