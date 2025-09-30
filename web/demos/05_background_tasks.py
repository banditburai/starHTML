"""Async Patterns & Coordination - Concurrent APIs, background streaming, and task queues"""

import asyncio
import random
import time
from datetime import datetime

from starhtml import *

app, rt = star_app(
    title="Async Patterns",
    hdrs=[
        Script(src="https://cdn.jsdelivr.net/npm/@tailwindcss/browser@4"),
        Style("""
            body { background: white; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; -webkit-font-smoothing: antialiased; }
            @keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.5; } }
            .loading { animation: pulse 1.5s ease-in-out infinite; }
            @keyframes slideIn { from { transform: translateY(20px); opacity: 0; } to { transform: translateY(0); opacity: 1; } }
            .slide-in { animation: slideIn 0.3s ease-out; }
            .dependency-line {
                position: relative;
                border-left: 2px dashed #e5e7eb;
                margin-left: 1rem;
                padding-left: 1rem;
            }
        """),
    ],
    iconify=True,
    compression=False,
)


@rt("/")
def home():
    return Div(
        # Main container
        Div(
            # Header
            Div(
                H1("05", cls="text-8xl font-black text-gray-100 leading-none"),
                H1("Async Patterns", cls="text-5xl md:text-6xl font-bold text-black mt-2"),
                P("Concurrent APIs, background streaming, and task coordination", cls="text-lg text-gray-600 mt-4"),
                cls="mb-16",
            ),
            # === 1. CONCURRENT API COORDINATION ===
            Div(
                H3("Concurrent API Coordination", cls="text-2xl font-bold text-black mb-6"),
                P("Multiple APIs with dependencies, race conditions, and error handling", cls="text-gray-600 mb-6"),
                # Controls
                Div(
                    Button(
                        "Start API Chain",
                        data_on_click=get("api-chain"),
                        cls="px-4 py-2 bg-black text-white font-medium hover:bg-gray-800 transition-colors",
                    ),
                    Button(
                        "Simulate API Race",
                        data_on_click=get("api-race"),
                        cls="px-4 py-2 bg-purple-600 text-white font-medium hover:bg-purple-700 transition-colors",
                    ),
                    Button(
                        "Reset",
                        data_on_click=get("api-reset"),
                        cls="px-4 py-2 border border-gray-300 text-black font-medium hover:border-gray-500 transition-colors",
                    ),
                    cls="mb-6 flex flex-wrap gap-3",
                ),
                # API Coordination Display
                Div(
                    # Chain execution flow
                    Div(
                        H4("Dependency Chain", cls="font-semibold mb-4"),
                        Div(
                            # Step 1: Auth
                            Div(
                                Icon("material-symbols:security", width="20", height="20", cls="text-gray-400"),
                                Span("1. Authentication", cls="ml-2 font-medium flex-1"),
                                Div("Ready", id="auth-status", cls="text-sm text-gray-500"),
                                id="auth-step",
                                cls="flex items-center p-3 bg-gray-50 border border-gray-200 mb-2",
                            ),
                            # Step 2: User Data (depends on auth)
                            Div(
                                Icon("material-symbols:person", width="20", height="20", cls="text-gray-400"),
                                Span("2. User Profile", cls="ml-2 font-medium flex-1"),
                                Div("Waiting for auth", id="profile-status", cls="text-sm text-gray-500"),
                                id="profile-step",
                                cls="flex items-center p-3 bg-gray-50 border border-gray-200 mb-2 ml-6",
                            ),
                            # Step 3: Permissions (depends on profile)
                            Div(
                                Icon(
                                    "material-symbols:admin-panel-settings",
                                    width="20",
                                    height="20",
                                    cls="text-gray-400",
                                ),
                                Span("3. Permissions", cls="ml-2 font-medium flex-1"),
                                Div("Waiting for profile", id="permissions-status", cls="text-sm text-gray-500"),
                                id="permissions-step",
                                cls="flex items-center p-3 bg-gray-50 border border-gray-200 ml-12",
                            ),
                            cls="space-y-1",
                        ),
                        cls="flex-1",
                    ),
                    # Race condition display
                    Div(
                        H4("API Race Results", cls="font-semibold mb-4"),
                        P(
                            "Simulates 5 concurrent API calls with random delays (0.3-2.0s) and 80% success rate.",
                            cls="text-xs text-gray-600 mb-2",
                        ),
                        P("✓ = successful response, ✗ = failed response", cls="text-xs text-gray-500 mb-4"),
                        Div(
                            P(
                                "Click 'Simulate API Race' to see concurrent calls",
                                cls="text-gray-500 text-center py-8",
                            ),
                            id="race-results",
                            cls="p-4 bg-gray-50 border border-gray-200 min-h-[200px]",
                        ),
                        cls="flex-1 lg:ml-6 mt-6 lg:mt-0",
                    ),
                    cls="flex flex-col lg:flex-row gap-6",
                ),
                cls="mb-12 p-8 bg-white border border-gray-200",
            ),
            # === 2. BACKGROUND DATA STREAMING ===
            Div(
                H3("Background Data Streaming", cls="text-2xl font-bold text-black mb-6"),
                P("Continuous data streams, real-time metrics, and live updates", cls="text-gray-600 mb-6"),
                # Controls
                Div(
                    Button(
                        "Start Data Stream",
                        data_on_click=get("stream-start"),
                        cls="px-4 py-2 bg-blue-600 text-white font-medium hover:bg-blue-700 transition-colors",
                    ),
                    Button(
                        "Stop Stream",
                        data_on_click=get("stream-stop"),
                        cls="px-4 py-2 bg-red-600 text-white font-medium hover:bg-red-700 transition-colors",
                    ),
                    Div(
                        Span("Stream Status:", cls="text-sm text-gray-600 mr-2"),
                        Span("Idle", id="stream-status", cls="px-2 py-1 text-xs bg-gray-100 text-gray-600 rounded"),
                        cls="flex items-center",
                    ),
                    cls="mb-6 flex flex-wrap gap-3 items-center",
                ),
                # Streaming Data Display
                Div(
                    # Live metrics
                    Div(
                        H4("Live Metrics", cls="font-semibold mb-4"),
                        Div(
                            # Metric labels (fixed width)
                            Div(
                                Div("CPU Usage", cls="text-sm font-medium text-gray-700 mb-3"),
                                Div("Memory", cls="text-sm font-medium text-gray-700 mb-3"),
                                Div("Network", cls="text-sm font-medium text-gray-700"),
                                cls="w-20 flex-shrink-0",
                            ),
                            # Progress bars (flexible width)
                            Div(
                                # CPU metric
                                Div(
                                    Div("0%", id="cpu-value", cls="text-xs text-gray-600 mb-1"),
                                    Div(
                                        Div(
                                            id="cpu-bar",
                                            cls="h-2 bg-blue-500 transition-all duration-500",
                                            style="width: 0%",
                                        ),
                                        cls="w-full bg-gray-200 h-2 rounded",
                                    ),
                                    cls="mb-3",
                                ),
                                # Memory metric
                                Div(
                                    Div("0%", id="memory-value", cls="text-xs text-gray-600 mb-1"),
                                    Div(
                                        Div(
                                            id="memory-bar",
                                            cls="h-2 bg-green-500 transition-all duration-500",
                                            style="width: 0%",
                                        ),
                                        cls="w-full bg-gray-200 h-2 rounded",
                                    ),
                                    cls="mb-3",
                                ),
                                # Network metric
                                Div(
                                    Div("0 KB/s", id="network-value", cls="text-xs text-gray-600 mb-1"),
                                    Div(
                                        Div(
                                            id="network-bar",
                                            cls="h-2 bg-purple-500 transition-all duration-500",
                                            style="width: 0%",
                                        ),
                                        cls="w-full bg-gray-200 h-2 rounded",
                                    ),
                                ),
                                cls="flex-1",
                            ),
                            cls="flex gap-4",
                        ),
                        cls="flex-1",
                    ),
                    # Live data feed
                    Div(
                        H4("Data Feed", cls="font-semibold mb-4"),
                        Div(
                            P("Start streaming to see live data", cls="text-gray-500 text-center py-8"),
                            id="data-feed",
                            cls="p-4 bg-gray-50 border border-gray-200 max-h-[300px] overflow-y-auto",
                        ),
                        cls="flex-1 lg:ml-6 mt-6 lg:mt-0",
                    ),
                    cls="flex flex-col lg:flex-row gap-6",
                ),
                cls="mb-12 p-8 bg-gray-50",
            ),
            # === 3. TASK QUEUE & WORKER PATTERNS ===
            Div(
                H3("Task Queue & Workers", cls="text-2xl font-bold text-black mb-6"),
                P("Job queuing, worker coordination, error handling, and retry patterns", cls="text-gray-600 mb-6"),
                # Controls
                Div(
                    Button(
                        "Add Jobs to Queue",
                        data_on_click=get("queue-add"),
                        cls="px-4 py-2 bg-green-600 text-white font-medium hover:bg-green-700 transition-colors",
                    ),
                    Button(
                        "Start Workers",
                        data_on_click=get("workers-start"),
                        cls="px-4 py-2 bg-orange-600 text-white font-medium hover:bg-orange-700 transition-colors",
                    ),
                    Button(
                        "Stop Workers",
                        data_on_click=get("workers-stop"),
                        cls="px-4 py-2 bg-red-600 text-white font-medium hover:bg-red-700 transition-colors",
                    ),
                    Button(
                        "Clear Queue",
                        data_on_click=get("queue-clear"),
                        cls="px-4 py-2 border border-gray-300 text-black font-medium hover:border-gray-500 transition-colors",
                    ),
                    cls="mb-6 flex flex-wrap gap-3",
                ),
                # Task Queue Display
                Div(
                    # Queue status
                    Div(
                        H4("Queue Status", cls="font-semibold mb-4"),
                        Div(
                            Div(
                                Span("Pending Jobs:", cls="text-sm font-medium text-gray-700"),
                                Span(
                                    "0",
                                    id="pending-count",
                                    cls="ml-2 px-2 py-1 bg-yellow-100 text-yellow-800 text-xs rounded",
                                ),
                                cls="flex items-center justify-between mb-2",
                            ),
                            Div(
                                Span("Active Workers:", cls="text-sm font-medium text-gray-700"),
                                Span(
                                    "0",
                                    id="worker-count",
                                    cls="ml-2 px-2 py-1 bg-blue-100 text-blue-800 text-xs rounded",
                                ),
                                cls="flex items-center justify-between mb-2",
                            ),
                            Div(
                                Span("Completed:", cls="text-sm font-medium text-gray-700"),
                                Span(
                                    "0",
                                    id="completed-count",
                                    cls="ml-2 px-2 py-1 bg-green-100 text-green-800 text-xs rounded",
                                ),
                                cls="flex items-center justify-between mb-2",
                            ),
                            Div(
                                Span("Failed:", cls="text-sm font-medium text-gray-700"),
                                Span(
                                    "0", id="failed-count", cls="ml-2 px-2 py-1 bg-red-100 text-red-800 text-xs rounded"
                                ),
                                cls="flex items-center justify-between",
                            ),
                            cls="p-4 bg-white border border-gray-200",
                        ),
                        cls="flex-1",
                    ),
                    # Job list table
                    Div(
                        H4("Job Processing", cls="font-semibold mb-4"),
                        Div(
                            Table(
                                Thead(
                                    Tr(
                                        Th(
                                            "Job ID",
                                            cls="text-left text-xs font-medium text-gray-500 uppercase tracking-wider py-2 px-3",
                                        ),
                                        Th(
                                            "Type",
                                            cls="text-left text-xs font-medium text-gray-500 uppercase tracking-wider py-2 px-3",
                                        ),
                                        Th(
                                            "Status",
                                            cls="text-left text-xs font-medium text-gray-500 uppercase tracking-wider py-2 px-3",
                                        ),
                                        Th(
                                            "Progress",
                                            cls="text-left text-xs font-medium text-gray-500 uppercase tracking-wider py-2 px-3",
                                        ),
                                        cls="border-b border-gray-200",
                                    )
                                ),
                                Tbody(
                                    Tr(
                                        Td("No jobs in queue", colspan="4", cls="text-center text-gray-500 py-8"),
                                        cls="border-b border-gray-100",
                                    ),
                                    id="job-table-body",
                                ),
                                cls="min-w-full",
                            ),
                            id="job-list",
                            cls="bg-white border border-gray-200 max-h-[300px] overflow-y-auto overflow-x-auto",
                        ),
                        cls="flex-1 lg:ml-6 mt-6 lg:mt-0",
                    ),
                    cls="flex flex-col lg:flex-row gap-6",
                ),
                cls="mb-12 p-8 bg-white border border-gray-200",
            ),
        ),
        cls="max-w-6xl mx-auto px-8 sm:px-12 lg:px-16 py-16 sm:py-20 md:py-24 bg-white min-h-screen overflow-y-auto",
    )


# === GLOBAL STATE ===
# Stream state
streaming_active = False
stream_task = None

# Queue state
job_queue = []
workers_active = False
worker_tasks = []
completed_jobs = 0
failed_jobs = 0


# === API COORDINATION ENDPOINTS ===


@rt("/api-chain")
@sse
async def api_chain(req):
    """Demonstrate API dependency chain"""

    # Step 1: Authentication
    yield elements(
        Div(
            Icon("material-symbols:security", width="20", height="20", cls="text-blue-600"),
            Span("1. Authentication", cls="ml-2 font-medium"),
            Div("Authenticating...", id="auth-status", cls="ml-auto text-sm text-blue-600 loading"),
            id="auth-step",
            cls="flex items-center p-3 bg-blue-50 border border-blue-200 mb-2",
        ),
        "#auth-step",
    )

    await asyncio.sleep(1.5)

    # Auth success
    yield elements(
        Div(
            Icon("material-symbols:security", width="20", height="20", cls="text-green-600"),
            Span("1. Authentication", cls="ml-2 font-medium"),
            Div("✓ Token acquired", id="auth-status", cls="ml-auto text-sm text-green-600"),
            id="auth-step",
            cls="flex items-center p-3 bg-green-50 border border-green-200 mb-2",
        ),
        "#auth-step",
    )

    # Step 2: User Profile (now that auth is done)
    yield elements(
        Div(
            Icon("material-symbols:person", width="20", height="20", cls="text-blue-600"),
            Span("2. User Profile", cls="ml-2 font-medium"),
            Div("Loading profile...", id="profile-status", cls="ml-auto text-sm text-blue-600 loading"),
            id="profile-step",
            cls="flex items-center p-3 bg-blue-50 border border-blue-200 mb-2 ml-6",
        ),
        "#profile-step",
    )

    await asyncio.sleep(1.2)

    # Profile success
    yield elements(
        Div(
            Icon("material-symbols:person", width="20", height="20", cls="text-green-600"),
            Span("2. User Profile", cls="ml-2 font-medium"),
            Div("✓ Profile loaded", id="profile-status", cls="ml-auto text-sm text-green-600"),
            id="profile-step",
            cls="flex items-center p-3 bg-green-50 border border-green-200 mb-2 ml-6",
        ),
        "#profile-step",
    )

    # Step 3: Permissions (depends on profile)
    yield elements(
        Div(
            Icon("material-symbols:admin-panel-settings", width="20", height="20", cls="text-blue-600"),
            Span("3. Permissions", cls="ml-2 font-medium"),
            Div("Checking permissions...", id="permissions-status", cls="ml-auto text-sm text-blue-600 loading"),
            id="permissions-step",
            cls="flex items-center p-3 bg-blue-50 border border-blue-200 ml-12",
        ),
        "#permissions-step",
    )

    await asyncio.sleep(1.0)

    # Permissions success
    yield elements(
        Div(
            Icon("material-symbols:admin-panel-settings", width="20", height="20", cls="text-green-600"),
            Span("3. Permissions", cls="ml-2 font-medium"),
            Div("✓ Admin access", id="permissions-status", cls="ml-auto text-sm text-green-600"),
            id="permissions-step",
            cls="flex items-center p-3 bg-green-50 border border-green-200 ml-12",
        ),
        "#permissions-step",
    )


@rt("/api-race")
@sse
async def api_race(req):
    """Demonstrate concurrent API race conditions"""

    # Clear previous results
    yield elements(
        Div(
            P("Starting 5 concurrent API calls...", cls="text-center text-gray-600 mb-4"),
            id="race-results",
            cls="p-4 bg-gray-50 border border-gray-200 min-h-[200px]",
        ),
        "#race-results",
    )

    # Start 5 concurrent API calls
    async def api_call(call_id, delay):
        await asyncio.sleep(delay)
        return {
            "id": call_id,
            "delay": delay,
            "timestamp": datetime.now().strftime("%H:%M:%S.%f")[:-3],
            "success": random.random() > 0.2,  # 80% success rate
        }

    # Create 5 concurrent calls with random delays
    calls = [api_call(f"API-{i + 1}", random.uniform(0.3, 2.0)) for i in range(5)]

    results = []
    for coro in asyncio.as_completed(calls):
        result = await coro
        results.append(result)

        # Update display with each completed call
        result_items = []
        for r in results:
            icon = "✓" if r["success"] else "✗"
            color = "text-green-600" if r["success"] else "text-red-600"
            result_items.append(
                Div(
                    Span(f"{icon} {r['id']}", cls=f"font-mono {color}"),
                    Span(f"({r['delay']:.2f}s)", cls="text-gray-500 text-sm ml-2"),
                    Span(r["timestamp"], cls="text-gray-400 text-xs ml-auto"),
                    cls="flex items-center justify-between p-2 bg-white border border-gray-100 mb-1 slide-in",
                )
            )

        yield elements(
            Div(
                P(f"Race progress: {len(results)}/5 completed", cls="text-center text-gray-600 mb-4"),
                Div(*result_items, cls="space-y-1"),
                id="race-results",
                cls="p-4 bg-gray-50 border border-gray-200 min-h-[200px]",
            ),
            "#race-results",
        )

    # Final summary
    successful = sum(1 for r in results if r["success"])
    yield elements(
        Div(
            P(f"Race complete! {successful}/5 successful", cls="text-center text-gray-800 font-medium mb-4"),
            Div(
                *[
                    Div(
                        Span(
                            f"{'✓' if r['success'] else '✗'} {r['id']}",
                            cls=f"font-mono {'text-green-600' if r['success'] else 'text-red-600'}",
                        ),
                        Span(f"({r['delay']:.2f}s)", cls="text-gray-500 text-sm ml-2"),
                        Span(r["timestamp"], cls="text-gray-400 text-xs ml-auto"),
                        cls="flex items-center justify-between p-2 bg-white border border-gray-100 mb-1",
                    )
                    for r in results
                ],
                cls="space-y-1",
            ),
            id="race-results",
            cls="p-4 bg-gray-50 border border-gray-200 min-h-[200px]",
        ),
        "#race-results",
    )


@rt("/api-reset")
@sse
async def api_reset(req):
    """Reset API coordination demo"""

    # Reset auth step
    yield elements(
        Div(
            Icon("material-symbols:security", width="20", height="20", cls="text-gray-400"),
            Span("1. Authentication", cls="ml-2 font-medium"),
            Div("Ready", id="auth-status", cls="ml-auto text-sm text-gray-500"),
            id="auth-step",
            cls="flex items-center p-3 bg-gray-50 border border-gray-200 mb-2",
        ),
        "#auth-step",
    )

    # Reset profile step
    yield elements(
        Div(
            Icon("material-symbols:person", width="20", height="20", cls="text-gray-400"),
            Span("2. User Profile", cls="ml-2 font-medium"),
            Div("Waiting for auth", id="profile-status", cls="ml-auto text-sm text-gray-500"),
            id="profile-step",
            cls="flex items-center p-3 bg-gray-50 border border-gray-200 mb-2 ml-6",
        ),
        "#profile-step",
    )

    # Reset permissions step
    yield elements(
        Div(
            Icon("material-symbols:admin-panel-settings", width="20", height="20", cls="text-gray-400"),
            Span("3. Permissions", cls="ml-2 font-medium"),
            Div("Waiting for profile", id="permissions-status", cls="ml-auto text-sm text-gray-500"),
            id="permissions-step",
            cls="flex items-center p-3 bg-gray-50 border border-gray-200 ml-12",
        ),
        "#permissions-step",
    )

    # Reset race results
    yield elements(
        Div(
            P("Click 'Simulate API Race' to see concurrent calls", cls="text-gray-500 text-center py-8"),
            id="race-results",
            cls="p-4 bg-gray-50 border border-gray-200 min-h-[200px]",
        ),
        "#race-results",
    )


# === STREAMING ENDPOINTS ===


@rt("/stream-start")
@sse
async def stream_start(req):
    """Start background data streaming"""
    global streaming_active, stream_task

    if streaming_active:
        return

    streaming_active = True

    # Update status
    yield elements(
        Span("Active", id="stream-status", cls="px-2 py-1 text-xs bg-green-100 text-green-600 rounded"),
        "#stream-status",
    )

    # Clear data feed
    yield elements(
        Div(
            P("Stream started - receiving data...", cls="text-green-600 text-center py-4"),
            id="data-feed",
            cls="p-4 bg-gray-50 border border-gray-200 max-h-[300px] overflow-y-auto",
        ),
        "#data-feed",
    )

    # Start streaming loop
    data_points = []
    while streaming_active:
        # Generate random metrics
        cpu = random.randint(10, 90)
        memory = random.randint(20, 85)
        network = random.randint(50, 500)

        # Update metrics bars with ID preservation
        yield elements(Div(f"{cpu}%", id="cpu-value", cls="text-xs text-gray-600"), "#cpu-value")
        yield elements(
            Div(id="cpu-bar", cls="h-2 bg-blue-500 transition-all duration-500", style=f"width: {cpu}%"), "#cpu-bar"
        )

        yield elements(Div(f"{memory}%", id="memory-value", cls="text-xs text-gray-600"), "#memory-value")
        yield elements(
            Div(id="memory-bar", cls="h-2 bg-green-500 transition-all duration-500", style=f"width: {memory}%"),
            "#memory-bar",
        )

        yield elements(Div(f"{network} KB/s", id="network-value", cls="text-xs text-gray-600"), "#network-value")
        yield elements(
            Div(
                id="network-bar",
                cls="h-2 bg-purple-500 transition-all duration-500",
                style=f"width: {min(network / 5, 100)}%",
            ),
            "#network-bar",
        )

        # Add data point to feed
        timestamp = datetime.now().strftime("%H:%M:%S")
        data_points.append({"time": timestamp, "cpu": cpu, "memory": memory, "network": network})

        # Keep only last 10 points
        if len(data_points) > 10:
            data_points.pop(0)

        # Update data feed
        feed_items = []
        for point in reversed(data_points):  # Show newest first
            feed_items.append(
                Div(
                    Span(point["time"], cls="font-mono text-xs text-gray-500"),
                    Span(f"CPU: {point['cpu']}%", cls="text-xs text-blue-600 ml-3"),
                    Span(f"MEM: {point['memory']}%", cls="text-xs text-green-600 ml-2"),
                    Span(f"NET: {point['network']} KB/s", cls="text-xs text-purple-600 ml-2"),
                    cls="p-2 bg-white border-b border-gray-100 text-sm slide-in",
                )
            )

        yield elements(
            Div(*feed_items, id="data-feed", cls="p-4 bg-gray-50 border border-gray-200 max-h-[300px] overflow-y-auto"),
            "#data-feed",
        )

        await asyncio.sleep(0.8)


@rt("/stream-stop")
@sse
async def stream_stop(req):
    """Stop background data streaming"""
    global streaming_active

    streaming_active = False

    # Update status
    yield elements(
        Span("Stopped", id="stream-status", cls="px-2 py-1 text-xs bg-red-100 text-red-600 rounded"), "#stream-status"
    )

    # Reset metrics
    yield elements(Div("0%", cls="text-xs text-gray-600"), "#cpu-value")
    yield elements(Div(cls="h-2 bg-blue-500 transition-all duration-500", style="width: 0%"), "#cpu-bar")

    yield elements(Div("0%", cls="text-xs text-gray-600"), "#memory-value")
    yield elements(Div(cls="h-2 bg-green-500 transition-all duration-500", style="width: 0%"), "#memory-bar")

    yield elements(Div("0 KB/s", cls="text-xs text-gray-600"), "#network-value")
    yield elements(Div(cls="h-2 bg-purple-500 transition-all duration-500", style="width: 0%"), "#network-bar")


# === TASK QUEUE ENDPOINTS ===


@rt("/queue-add")
@sse
async def queue_add(req):
    """Add jobs to the queue"""
    global job_queue

    # Add 5 random jobs
    new_jobs = []
    for i in range(5):
        job_id = f"job-{int(time.time())}-{i + 1}"
        job_type = random.choice(["process_image", "send_email", "generate_report", "backup_data", "sync_files"])
        new_jobs.append(
            {
                "id": job_id,
                "type": job_type,
                "status": "pending",
                "created": datetime.now().strftime("%H:%M:%S"),
                "retries": 0,
                "progress": 0,
            }
        )

    job_queue.extend(new_jobs)

    # Update pending count
    yield elements(
        Span(
            str(len([j for j in job_queue if j["status"] == "pending"])),
            id="pending-count",
            cls="ml-2 px-2 py-1 bg-yellow-100 text-yellow-800 text-xs rounded",
        ),
        "#pending-count",
    )

    # Update job table
    job_rows = []
    for job in job_queue[-10:]:  # Show last 10 jobs
        status_colors = {
            "pending": "bg-yellow-100 text-yellow-800",
            "processing": "bg-blue-100 text-blue-800",
            "completed": "bg-green-100 text-green-800",
            "failed": "bg-red-100 text-red-800",
        }

        job_rows.append(
            Tr(
                Td(job["id"], cls="py-2 px-3 text-xs font-mono"),
                Td(job["type"], cls="py-2 px-3 text-sm"),
                Td(
                    Span(job["status"], cls=f"text-xs px-2 py-1 rounded {status_colors[job['status']]}"),
                    cls="py-2 px-3",
                ),
                Td(f"{job.get('progress', 0)}%", cls="py-2 px-3 text-sm"),  # Progress column
                cls="border-b border-gray-100",
            )
        )

    yield elements(
        Tbody(
            *job_rows
            if job_rows
            else [
                Tr(
                    Td("No jobs in queue", colspan="4", cls="text-center text-gray-500 py-8"),
                    cls="border-b border-gray-100",
                )
            ],
            id="job-table-body",
        ),
        "#job-table-body",
    )


@rt("/workers-start")
@sse
async def workers_start(req):
    """Start processing jobs with live progress updates"""
    global workers_active, completed_jobs, failed_jobs

    if workers_active or not job_queue:
        return

    workers_active = True
    worker_count = 3

    # Update worker count
    yield elements(
        Span(str(worker_count), id="worker-count", cls="ml-2 px-2 py-1 bg-blue-100 text-blue-800 text-xs rounded"),
        "#worker-count",
    )

    # Process up to 3 jobs in parallel
    while workers_active and any(j["status"] == "pending" for j in job_queue):
        # Find up to 3 pending jobs to process in parallel
        pending_jobs = [j for j in job_queue if j["status"] == "pending"]
        if not pending_jobs:
            break

        # Take up to 3 jobs for parallel processing
        jobs_to_process = pending_jobs[:worker_count]

        # Start all selected jobs
        for job in jobs_to_process:
            job["status"] = "processing"
            job["progress"] = 0

        # Update table to show processing status
        def update_job_table():
            job_rows = []
            for j in job_queue[-10:]:
                status_colors = {
                    "pending": "bg-yellow-100 text-yellow-800",
                    "processing": "bg-blue-100 text-blue-800",
                    "completed": "bg-green-100 text-green-800",
                    "failed": "bg-red-100 text-red-800",
                }

                job_rows.append(
                    Tr(
                        Td(j["id"], cls="py-2 px-3 text-xs font-mono"),
                        Td(j["type"], cls="py-2 px-3 text-sm"),
                        Td(
                            Span(j["status"], cls=f"text-xs px-2 py-1 rounded {status_colors[j['status']]}"),
                            cls="py-2 px-3",
                        ),
                        Td(f"{j.get('progress', 0)}%", cls="py-2 px-3 text-sm"),
                        cls="border-b border-gray-100",
                    )
                )
            return job_rows

        # Show jobs starting to process
        yield elements(Tbody(*update_job_table(), id="job-table-body"), "#job-table-body")

        # Process all jobs in parallel with progress updates
        for progress in [25, 50, 75, 100]:
            await asyncio.sleep(0.6)  # Simulate work

            # Update progress for all processing jobs
            for job in jobs_to_process:
                if job["status"] == "processing":
                    job["progress"] = progress

            # Update table with new progress
            yield elements(Tbody(*update_job_table(), id="job-table-body"), "#job-table-body")

        # Complete all jobs (85% success rate each)
        jobs_completed = 0
        jobs_failed = 0

        for job in jobs_to_process:
            if random.random() > 0.15:
                job["status"] = "completed"
                jobs_completed += 1
            else:
                job["status"] = "failed"
                job["progress"] = 0
                jobs_failed += 1

        # Update counters
        completed_jobs += jobs_completed
        failed_jobs += jobs_failed

        if jobs_completed > 0:
            yield elements(
                Span(
                    str(completed_jobs),
                    id="completed-count",
                    cls="ml-2 px-2 py-1 bg-green-100 text-green-800 text-xs rounded",
                ),
                "#completed-count",
            )

        if jobs_failed > 0:
            yield elements(
                Span(str(failed_jobs), id="failed-count", cls="ml-2 px-2 py-1 bg-red-100 text-red-800 text-xs rounded"),
                "#failed-count",
            )

        # Update pending count
        pending_count = len([j for j in job_queue if j["status"] == "pending"])
        yield elements(
            Span(
                str(pending_count),
                id="pending-count",
                cls="ml-2 px-2 py-1 bg-yellow-100 text-yellow-800 text-xs rounded",
            ),
            "#pending-count",
        )

        # Final table update for this job
        yield elements(Tbody(*update_job_table(), id="job-table-body"), "#job-table-body")

        # Small delay before next job
        await asyncio.sleep(0.5)

    # All jobs processed - stop workers
    workers_active = False
    yield elements(
        Span("0", id="worker-count", cls="ml-2 px-2 py-1 bg-blue-100 text-blue-800 text-xs rounded"), "#worker-count"
    )


@rt("/workers-stop")
@sse
async def workers_stop(req):
    """Stop worker processes"""
    global workers_active

    workers_active = False

    # Update worker count
    yield elements(
        Span("0", id="worker-count", cls="ml-2 px-2 py-1 bg-blue-100 text-blue-800 text-xs rounded"), "#worker-count"
    )


@rt("/queue-clear")
@sse
async def queue_clear(req):
    """Clear the job queue"""
    global job_queue, completed_jobs, failed_jobs

    job_queue.clear()
    completed_jobs = 0
    failed_jobs = 0

    # Reset all counts
    yield elements(
        Span("0", id="pending-count", cls="ml-2 px-2 py-1 bg-yellow-100 text-yellow-800 text-xs rounded"),
        "#pending-count",
    )
    yield elements(
        Span("0", id="completed-count", cls="ml-2 px-2 py-1 bg-green-100 text-green-800 text-xs rounded"),
        "#completed-count",
    )
    yield elements(
        Span("0", id="failed-count", cls="ml-2 px-2 py-1 bg-red-100 text-red-800 text-xs rounded"), "#failed-count"
    )

    # Clear job table
    yield elements(
        Tbody(
            Tr(
                Td("No jobs in queue", colspan="4", cls="text-center text-gray-500 py-8"),
                cls="border-b border-gray-100",
            ),
            id="job-table-body",
        ),
        "#job-table-body",
    )


if __name__ == "__main__":
    serve(port=5015)
