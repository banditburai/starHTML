"""Live Updates & Auto-Targeting - Real-time SSE patterns"""

import asyncio
from datetime import datetime

from starhtml import *

app, rt = star_app(
    title="Live Updates",
    hdrs=[
        Script(src="https://cdn.jsdelivr.net/npm/@tailwindcss/browser@4"),
        Style("""
            body { background: white; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; -webkit-font-smoothing: antialiased; }
            @keyframes slideIn { from { transform: translateX(100%); opacity: 0; } to { transform: translateX(0); opacity: 1; } }
            @keyframes fadeOut { to { opacity: 0; transform: scale(0.9); } }
            .notification-enter { animation: slideIn 0.3s ease-out; }
            .notification-exit { animation: fadeOut 0.2s ease-out forwards; }
            @keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.5; } }
            .status-checking { animation: pulse 1.5s ease-in-out infinite; }
        """),
    ],
    iconify=True,
    compression=False,
)


@rt("/")
def home():
    return Div(
        # Include the active notifications signal
        active_notifications,
        # Main container
        Div(
            # Header
            Div(
                H1("04", cls="text-8xl font-black text-gray-100 leading-none"),
                H1("Live Updates", cls="text-5xl md:text-6xl font-bold text-black mt-2"),
                P("Real-time SSE patterns and auto-targeting", cls="text-lg text-gray-600 mt-4"),
                cls="mb-16",
            ),
            # === 1. NOTIFICATION SYSTEM ===
            Div(
                H3("Notification System", cls="text-2xl font-bold text-black mb-6"),
                # Controls
                Div(
                    Button(
                        Icon("material-symbols:check-circle", width="20", height="20"),
                        "Success",
                        data_on_click=get("notify/success"),
                        cls="px-4 py-2 bg-green-600 text-white font-medium hover:bg-green-700 transition-colors w-32 flex items-center justify-center gap-2",
                    ),
                    Button(
                        Icon("material-symbols:warning", width="20", height="20"),
                        "Warning",
                        data_on_click=get("notify/warning"),
                        cls="px-4 py-2 bg-amber-600 text-white font-medium hover:bg-amber-700 transition-colors w-32 mx-2 flex items-center justify-center gap-2",
                    ),
                    Button(
                        Icon("material-symbols:error", width="20", height="20"),
                        "Error",
                        data_on_click=get("notify/error"),
                        cls="px-4 py-2 bg-red-600 text-white font-medium hover:bg-red-700 transition-colors w-32 flex items-center justify-center gap-2",
                    ),
                    cls="mb-4 flex",
                ),
                # Notification container - SSE will auto-target this
                Div(id="notifications", cls="space-y-2 min-h-[100px]"),
                P("Notifications auto-dismiss after 3 seconds", cls="text-sm text-gray-500 mt-4"),
                cls="mb-12 p-8 bg-white border border-gray-200",
            ),
            # === 2. STATUS DASHBOARD ===
            Div(
                H3("Status Dashboard", cls="text-2xl font-bold text-black mb-6"),
                # Controls
                Div(
                    Button(
                        "Check All Systems",
                        data_on_click=get("check-status"),
                        cls="px-4 py-2 bg-black text-white font-medium hover:bg-gray-800 transition-colors",
                    ),
                    cls="mb-6",
                ),
                # Status grid - each will be auto-targeted by ID
                Div(
                    # Database status
                    Div(
                        Icon("material-symbols:database", width="24", height="24", cls="text-gray-400"),
                        Div(
                            Span("Database", cls="font-semibold"),
                            Span("Ready", id="db-status", cls="text-gray-500 text-sm"),
                            cls="flex-1 flex flex-col",
                        ),
                        id="status-db",
                        cls="flex items-center gap-3 p-4 bg-gray-50 border border-gray-200",
                    ),
                    # API status
                    Div(
                        Icon("material-symbols:api", width="24", height="24", cls="text-gray-400"),
                        Div(
                            Span("API Server", cls="font-semibold"),
                            Span("Ready", id="api-status", cls="text-gray-500 text-sm"),
                            cls="flex-1 flex flex-col",
                        ),
                        id="status-api",
                        cls="flex items-center gap-3 p-4 bg-gray-50 border border-gray-200",
                    ),
                    # Cache status
                    Div(
                        Icon("material-symbols:memory", width="24", height="24", cls="text-gray-400"),
                        Div(
                            Span("Cache", cls="font-semibold"),
                            Span("Ready", id="cache-status", cls="text-gray-500 text-sm"),
                            cls="flex-1 flex flex-col",
                        ),
                        id="status-cache",
                        cls="flex items-center gap-3 p-4 bg-gray-50 border border-gray-200",
                    ),
                    cls="grid grid-cols-1 md:grid-cols-3 gap-4",
                ),
                cls="mb-12 p-8 bg-gray-50",
            ),
            # === 3. ACTIVITY FEED ===
            Div(
                H3("Activity Feed", cls="text-2xl font-bold text-black mb-6"),
                # Controls
                Div(
                    Button(
                        "Simulate User Activity",
                        data_on_click=get("activity"),
                        cls="px-4 py-2 bg-black text-white font-medium hover:bg-gray-800 transition-colors mr-2",
                    ),
                    Button(
                        "Clear Feed",
                        data_on_click=get("clear-feed"),
                        cls="px-4 py-2 border border-gray-300 text-black font-medium hover:border-gray-500 transition-colors",
                    ),
                    cls="mb-6",
                ),
                # Activity feed container - prepend strategy for newest first
                Div(
                    Div(
                        "Click 'Simulate User Activity' to see live updates here", cls="text-gray-500 text-center py-8"
                    ),
                    id="activity-feed",
                    cls="space-y-2 max-h-96 overflow-y-auto p-4 bg-white border border-gray-200",
                ),
                P("New activities appear at the top (prepend strategy)", cls="text-sm text-gray-500 mt-4"),
                cls="mb-12 p-8 bg-white border border-gray-200",
            ),
            # === 4. PROGRESS TRACKING ===
            Div(
                H3("Progress Tracking", cls="text-2xl font-bold text-black mb-6"),
                # Controls
                Div(
                    Button(
                        "Start Process",
                        data_on_click=get("process"),
                        cls="px-4 py-2 bg-black text-white font-medium hover:bg-gray-800 transition-colors",
                    ),
                    cls="mb-6",
                ),
                # Progress container - will be replaced entirely
                Div(
                    Div("Ready to start...", cls="text-gray-500"),
                    id="progress-container",
                    cls="p-6 bg-gray-50 border border-gray-200",
                ),
                cls="mb-12 p-8 bg-white border border-gray-200",
            ),
        ),
        cls="max-w-5xl mx-auto px-8 sm:px-12 lg:px-16 py-16 sm:py-20 md:py-24 bg-white min-h-screen overflow-y-auto",
    )


# === SSE ENDPOINTS ===

notification_counter = 0
active_notifications = Signal("active_notifications", set())  # Track all active notifications


@rt("/notify/success")
@sse
async def send_success_notification(req):
    """Send a success notification"""
    async for result in send_notification_helper("success", "Operation completed successfully!"):
        yield result


@rt("/notify/warning")
@sse
async def send_warning_notification(req):
    """Send a warning notification"""
    async for result in send_notification_helper("warning", "This action requires attention"):
        yield result


@rt("/notify/error")
@sse
async def send_error_notification(req):
    """Send an error notification"""
    async for result in send_notification_helper("error", "Something went wrong!"):
        yield result


async def send_notification_helper(type: str, message: str):
    """Helper function to send notifications"""
    global notification_counter
    notification_counter += 1
    notification_id = f"notif-{notification_counter}"

    # Add to active notifications signal
    current_set = active_notifications.value.copy()
    current_set.add(notification_id)
    active_notifications.value = current_set

    # Icon mapping
    icon_map = {"success": "check-circle", "warning": "warning", "error": "error", "info": "info"}

    # Color mapping
    colors = {
        "success": "bg-green-50 border-green-200 text-green-900",
        "warning": "bg-amber-50 border-amber-200 text-amber-900",
        "error": "bg-red-50 border-red-200 text-red-900",
        "info": "bg-blue-50 border-blue-200 text-blue-900",
    }

    selected_color = colors.get(type, colors["info"])
    selected_icon = icon_map.get(type, "info")

    # Create notification element
    notification = Div(
        Icon(f"material-symbols:{selected_icon}", width="20", height="20", cls="flex-shrink-0"),
        Span(message, cls="flex-1"),
        Button("×", data_on_click=get(f"dismiss-notification/{notification_id}"), cls="ml-2 text-xl hover:opacity-70"),
        id=notification_id,
        cls=f"flex items-center gap-3 p-4 border {selected_color} notification-enter",
    )

    # Auto-target #notifications with append strategy
    yield elements(notification, "#notifications", "append")

    # Add JavaScript to auto-dismiss after 3 seconds
    dismiss_script = Script(f"""
        setTimeout(() => {{
            const notif = document.getElementById('{notification_id}');
            if (notif) {{
                // Trigger the dismiss endpoint
                fetch('/dismiss-notification/{notification_id}');
                // Fade out and remove
                notif.classList.add('notification-exit');
                setTimeout(() => notif.remove(), 200);
            }}
        }}, 3000);
    """)

    # Send the dismiss script
    yield elements(dismiss_script, "body", "append")


@rt("/dismiss-notification/{notification_id}")
@sse
async def dismiss_notification(req, notification_id: str):
    """Dismiss a notification immediately"""
    # Remove from active set if present
    if notification_id in active_notifications.value:
        current_set = active_notifications.value.copy()
        current_set.remove(notification_id)
        active_notifications.value = current_set

    # Remove notification by replacing with empty content
    yield elements("", f"#{notification_id}")


@rt("/clear-feed")
@sse
async def clear_feed(req):
    """Clear the activity feed"""
    # Replace feed content with placeholder, preserving the ID
    yield elements(
        Div(
            Div("Click 'Simulate User Activity' to see live updates here", cls="text-gray-500 text-center py-8"),
            id="activity-feed",
            cls="space-y-2 max-h-96 overflow-y-auto p-4 bg-white border border-gray-200",
        ),
        "#activity-feed",
    )


@rt("/check-status")
@sse
async def check_system_status(req):
    """Check various system statuses with staggered updates"""

    # Immediately show checking state for all systems
    yield elements(
        Div(
            Icon("material-symbols:database", width="24", height="24", cls="text-gray-400"),
            Div(
                Span("Database", cls="font-semibold"),
                Span("Checking...", cls="text-gray-500 text-sm"),
                cls="flex-1 flex flex-col",
            ),
            id="status-db",
            cls="flex items-center gap-3 p-4 bg-gray-50 border border-gray-200",
        ),
        "#status-db",
    )

    yield elements(
        Div(
            Icon("material-symbols:api", width="24", height="24", cls="text-gray-400"),
            Div(
                Span("API Server", cls="font-semibold"),
                Span("Checking...", cls="text-gray-500 text-sm"),
                cls="flex-1 flex flex-col",
            ),
            id="status-api",
            cls="flex items-center gap-3 p-4 bg-gray-50 border border-gray-200",
        ),
        "#status-api",
    )

    yield elements(
        Div(
            Icon("material-symbols:memory", width="24", height="24", cls="text-gray-400"),
            Div(
                Span("Cache", cls="font-semibold"),
                Span("Checking...", cls="text-gray-500 text-sm"),
                cls="flex-1 flex flex-col",
            ),
            id="status-cache",
            cls="flex items-center gap-3 p-4 bg-gray-50 border border-gray-200",
        ),
        "#status-cache",
    )

    # Check database (fastest)
    await asyncio.sleep(0.5)
    yield elements(
        Div(
            Icon("material-symbols:database", width="24", height="24", cls="text-green-600"),
            Div(
                Span("Database", cls="font-semibold"),
                Span("Connected • 12ms", cls="text-green-600 text-sm"),
                cls="flex-1 flex flex-col",
            ),
            id="status-db",
            cls="flex items-center gap-3 p-4 bg-green-50 border border-green-200",
        ),
        "#status-db",
    )

    # Check API (medium)
    await asyncio.sleep(0.8)
    yield elements(
        Div(
            Icon("material-symbols:api", width="24", height="24", cls="text-green-600"),
            Div(
                Span("API Server", cls="font-semibold"),
                Span("Online • 98% uptime", cls="text-green-600 text-sm"),
                cls="flex-1 flex flex-col",
            ),
            id="status-api",
            cls="flex items-center gap-3 p-4 bg-green-50 border border-green-200",
        ),
        "#status-api",
    )

    # Check cache (slowest, might fail)
    await asyncio.sleep(1.2)
    import random

    if random.random() > 0.9:  # 10% success rate
        yield elements(
            Div(
                Icon("material-symbols:memory", width="24", height="24", cls="text-green-600"),
                Div(
                    Span("Cache", cls="font-semibold"),
                    Span("Active • 89% hit rate", cls="text-green-600 text-sm"),
                    cls="flex-1 flex flex-col",
                ),
                id="status-cache",
                cls="flex items-center gap-3 p-4 bg-green-50 border border-green-200",
            ),
            "#status-cache",
        )
    else:
        yield elements(
            Div(
                Icon("material-symbols:memory", width="24", height="24", cls="text-amber-600"),
                Div(
                    Span("Cache", cls="font-semibold"),
                    Span("Degraded • Rebuilding...", cls="text-amber-600 text-sm"),
                    cls="flex-1 flex flex-col",
                ),
                id="status-cache",
                cls="flex items-center gap-3 p-4 bg-amber-50 border border-amber-200",
            ),
            "#status-cache",
        )


activity_counter = 0


@rt("/activity")
@sse
async def simulate_activity(req):
    """Generate activity feed items"""
    global activity_counter

    # Small random delay to prevent concurrent request conflicts
    import random

    await asyncio.sleep(random.uniform(0.1, 0.3))

    activities = [
        ("User logged in", "account-circle", "blue"),
        ("File uploaded", "upload-file", "green"),
        ("Settings changed", "settings", "gray"),
        ("Comment posted", "chat-bubble", "purple"),
        ("Task completed", "task-alt", "green"),
        ("Error occurred", "warning", "red"),
    ]

    # Generate 3 random activities with delays
    import random

    for i in range(3):
        activity_counter += 1
        activity = random.choice(activities)

        timestamp = datetime.now().strftime("%H:%M:%S")

        # Create activity item
        item = Div(
            Icon(f"material-symbols:{activity[1]}", width="20", height="20", cls=f"text-{activity[2]}-600"),
            Div(
                Span(activity[0], cls="font-medium"),
                Span(timestamp, cls="text-gray-500 text-sm ml-2"),
                cls="flex-1 flex flex-col",
            ),
            id=f"activity-{activity_counter}",
            cls="flex items-center gap-3 p-3 bg-white border-b border-gray-100 hover:bg-gray-50 transition-colors",
        )

        # Prepend to feed (newest first)
        yield elements(item, "#activity-feed", "prepend")

        if i < 2:  # Don't wait after last item
            await asyncio.sleep(0.3)


@rt("/process")
@sse
async def run_process(req):
    """Simulate a multi-step process with progress updates"""

    steps = [
        "Initializing...",
        "Connecting to server...",
        "Authenticating...",
        "Loading data...",
        "Processing records...",
        "Finalizing...",
        "Complete!",
    ]

    for i, step in enumerate(steps):
        progress = int((i / (len(steps) - 1)) * 100)

        # Update entire progress container
        content = Div(
            Div(step, cls="font-medium mb-2"),
            Div(
                Div(cls="h-2 bg-black transition-all duration-300", style=f"width: {progress}%"),
                cls="w-full bg-gray-200 h-2",
            ),
            Span(f"{progress}%", cls="text-sm text-gray-600 mt-2"),
            id="progress-container",
            cls="space-y-2 p-6 bg-gray-50 border border-gray-200",
        )

        # Replace entire container
        yield elements(content, "#progress-container")

        if i < len(steps) - 1:
            await asyncio.sleep(0.8)

    # Final success state
    await asyncio.sleep(0.5)
    yield elements(
        Div(
            Div(
                Icon("material-symbols:check-circle", width="32", height="32", cls="text-green-600"),
                Span("Process completed successfully!", cls="text-green-600 font-medium ml-3"),
                cls="flex items-center justify-center",
            ),
            id="progress-container",
            cls="text-center p-6 bg-gray-50 border border-gray-200",
        ),
        "#progress-container",
    )


if __name__ == "__main__":
    serve(port=5014)
