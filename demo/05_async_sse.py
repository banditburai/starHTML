"""Demo: Async SSE handlers for non-blocking operations"""

import asyncio
import time

from starhtml import *

app, rt = star_app(
    title="Async SSE Demo",
    hdrs=[
        Script(src="https://cdn.jsdelivr.net/npm/@tailwindcss/browser@4"),
    ],
)


@rt("/")
def home():
    return Div(
        H1("Async SSE Demo", cls="text-3xl font-bold mb-6"),
        P("Demonstrating async SSE handlers for non-blocking operations", cls="text-lg mb-8"),
        # Sync vs Async comparison
        Div(
            H2("Sync vs Async SSE Handlers", cls="text-2xl font-semibold mb-4"),
            Div(
                Button(
                    "Test Sync Handler (blocks)",
                    ds_on_click("@get('/sync-sse')"),
                    cls="bg-red-500 text-white px-4 py-2 rounded hover:bg-red-600",
                ),
                Button(
                    "Test Async Handler (non-blocking)",
                    ds_on_click("@get('/async-sse')"),
                    cls="bg-green-500 text-white px-4 py-2 rounded hover:bg-green-600 ml-4",
                ),
                cls="mb-4",
            ),
            Div(P("Status: ", ds_text("$status"), cls="font-semibold"), cls="mb-4"),
            Div(id="result", cls="p-4 bg-gray-100 rounded min-h-[100px]"),
            cls="mb-8",
        ),
        # Multiple async operations
        Div(
            H2("Multiple Async Operations", cls="text-2xl font-semibold mb-4"),
            Button(
                "Fetch Multiple APIs",
                ds_on_click("@get('/multi-async')"),
                cls="bg-blue-500 text-white px-4 py-2 rounded hover:bg-blue-600 mb-4",
            ),
            Div(
                P("API 1: ", ds_text("$api1_status"), cls="mb-2"),
                P("API 2: ", ds_text("$api2_status"), cls="mb-2"),
                P("API 3: ", ds_text("$api3_status"), cls="mb-2"),
                cls="mb-4",
            ),
            Div(id="multi-result", cls="p-4 bg-gray-100 rounded min-h-[100px]"),
        ),
        ds_signals(
            status="Ready",
            api1_status="Not started",
            api2_status="Not started",
            api3_status="Not started",
        ),
        cls="max-w-4xl mx-auto p-8",
    )


# Simulate slow API call
def slow_sync_operation(seconds=2):
    """Simulates a slow blocking operation"""
    time.sleep(seconds)
    return {"data": f"Sync result after {seconds}s", "timestamp": time.time()}


async def slow_async_operation(seconds=2):
    """Simulates a slow async operation"""
    await asyncio.sleep(seconds)
    return {"data": f"Async result after {seconds}s", "timestamp": time.time()}


@rt("/sync-sse")
@sse
def sync_handler(req):
    """Synchronous SSE handler - blocks the thread"""
    yield signals(status="Starting sync operation...")

    # This blocks the thread!
    result = slow_sync_operation(2)

    yield elements(
        Div(
            P("✅ Sync operation complete!", cls="font-semibold text-red-600"),
            P(f"Result: {result['data']}"),
            P("Note: This blocked the server thread for 2 seconds!"),
            id="result",
        )
    )

    yield signals(status="Sync complete")


@rt("/async-sse")
@sse
async def async_handler(req):
    """Asynchronous SSE handler - non-blocking"""
    yield signals(status="Starting async operation...")

    # This doesn't block - other requests can be handled!
    result = await slow_async_operation(2)

    yield elements(
        Div(
            P("✅ Async operation complete!", cls="font-semibold text-green-600"),
            P(f"Result: {result['data']}"),
            P("Note: This did NOT block the server - other requests could be handled!"),
            id="result",
        )
    )

    yield signals(status="Async complete")


@rt("/multi-async")
@sse
async def multi_async_handler(req):
    """Handle multiple async operations concurrently"""
    yield signals(api1_status="Starting...", api2_status="Starting...", api3_status="Starting...")

    # Update status for all APIs
    yield signals(api1_status="Fetching API 1...")
    yield signals(api2_status="Fetching API 2...")
    yield signals(api3_status="Fetching API 3...")

    # Simulate concurrent API calls
    start_time = asyncio.get_event_loop().time()

    # Create tasks that run concurrently
    task1 = asyncio.create_task(slow_async_operation(1))
    task2 = asyncio.create_task(slow_async_operation(1.5))
    task3 = asyncio.create_task(slow_async_operation(0.5))

    # Wait for all to complete
    results = await asyncio.gather(task1, task2, task3)

    total_time = asyncio.get_event_loop().time() - start_time

    yield signals(api1_status="✅ Complete", api2_status="✅ Complete", api3_status="✅ Complete")

    yield elements(
        Div(
            P("✅ All APIs fetched concurrently!", cls="font-semibold text-blue-600"),
            P(f"Total time: {total_time:.2f}s (not 3s!)"),
            P("Results:"),
            Ul(
                Li(f"API 1: {results[0]['data']}"),
                Li(f"API 2: {results[1]['data']}"),
                Li(f"API 3: {results[2]['data']}"),
            ),
            id="multi-result",
        )
    )


if __name__ == "__main__":
    print("Async SSE Demo running on http://localhost:5001")
    serve(port=5001)
