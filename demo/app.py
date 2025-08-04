#!/usr/bin/env python3
"""
StarHTML Demo Hub - One entry point for all demos
Run with: uv run demo/app.py
"""

import importlib.util
from dataclasses import dataclass
from pathlib import Path

from starhtml import *

# Create the hub app - simple and clean
app, rt = star_app(
    title="StarHTML Demo Hub",
    hdrs=[
        Script(src="https://cdn.jsdelivr.net/npm/@tailwindcss/browser@4"),
    ],
)


@dataclass
class Demo:
    """Configuration for a single demo."""

    id: str
    title: str
    description: str
    file: str
    level: str
    time: str

    @property
    def file_path(self) -> Path:
        return Path(__file__).parent / self.file

    @property
    def route_path(self) -> str:
        return f"/{self.id}/"


class BackButtonMiddleware(BaseHTTPMiddleware):
    """Middleware to inject back button and convert absolute paths to relative ones."""

    async def dispatch(self, request, call_next):
        response = await call_next(request)

        # Only modify HTML responses from demo routes (pattern /XX-* where XX are digits)
        import re

        if (
            re.match(r"^/\d{2}-", request.url.path)
            and request.url.path.endswith("/")
            and response.headers.get("content-type", "").startswith("text/html")
        ):
            # Read the response body
            body = b"".join([chunk async for chunk in response.body_iterator])
            html_content = body.decode("utf-8")

            # Convert absolute paths to relative paths for proper Mount behavior
            import re

            # Convert @method('/route') to @method('route') for all HTTP methods
            http_methods = ["get", "post", "put", "patch", "delete", "head", "options"]
            for method in http_methods:
                html_content = re.sub(rf"@{method}\('/([^']+)'\)", rf"@{method}('\1')", html_content)

            # Convert other absolute paths to relative
            html_content = html_content.replace("'/api/", "'api/")
            html_content = html_content.replace('"/api/', '"api/')

            # Inject the back button after <body> tag
            back_button_html = """
                <a href="/"
                   class="fixed top-4 left-4 z-50 p-3 rounded-2xl transition-all duration-300 no-underline flex items-center justify-center group"
                   style="
                       width: 48px;
                       height: 48px;
                       background: rgba(59, 130, 246, 0.15);
                       backdrop-filter: blur(10px);
                       -webkit-backdrop-filter: blur(10px);
                       border: 1px solid rgba(255, 255, 255, 0.18);
                       box-shadow: 0 8px 32px 0 rgba(31, 38, 135, 0.37);
                   "
                   onmouseover="
                       this.style.background='rgba(59, 130, 246, 0.25)';
                       this.style.transform='scale(1.05)';
                       this.style.boxShadow='0 8px 32px 0 rgba(31, 38, 135, 0.47)';
                   "
                   onmouseout="
                       this.style.background='rgba(59, 130, 246, 0.15)';
                       this.style.transform='scale(1)';
                       this.style.boxShadow='0 8px 32px 0 rgba(31, 38, 135, 0.37)';
                   "
                   title="Back to Hub">
                    <iconify-icon icon="icon-park:back" width="24" height="24" style="color: #3b82f6;"></iconify-icon>
                </a>
            """

            if "<body>" in html_content:
                html_content = html_content.replace("<body>", f"<body>{back_button_html}")

            # Remove Content-Length header since we modified the body
            headers = dict(response.headers)
            headers.pop("content-length", None)
            headers.pop("Content-Length", None)

            # Return modified response
            return Response(
                content=html_content, status_code=response.status_code, headers=headers, media_type="text/html"
            )

        return response


# Demo metadata - ordered by learning progression
DEMOS = [
    Demo(
        "00-syntax",
        "Syntax Patterns",
        "Learn StarHTML syntax patterns and best practices",
        "00_syntax_patterns.py",
        "Foundation",
        "5 min",
    ),
    Demo(
        "01-signals",
        "Basic Signals",
        "Reactive data binding with Datastar signals",
        "01_basic_signals.py",
        "Foundation",
        "5 min",
    ),
    Demo(
        "02-sse",
        "Server-Sent Events",
        "Real-time updates with SSE elements",
        "02_sse_elements.py",
        "Foundation",
        "10 min",
    ),
    Demo(
        "03-forms",
        "Forms & Binding",
        "Form handling and data binding patterns",
        "03_forms_binding.py",
        "Foundation",
        "10 min",
    ),
    Demo(
        "04-debugging",
        "SSE Debugging",
        "Debug SSE merge elements and real-time updates",
        "04_sse_debugging.py",
        "Intermediate",
        "15 min",
    ),
    Demo(
        "05-async", "Async SSE", "Asynchronous SSE handlers and patterns", "05_async_sse.py", "Intermediate", "15 min"
    ),
    Demo(
        "06-persist",
        "Persist Handler",
        "Data persistence with localStorage and sessionStorage",
        "06_persist_handler.py",
        "Advanced",
        "20 min",
    ),
    Demo(
        "07-scroll",
        "Scroll Handler",
        "Scroll detection and position tracking",
        "07_scroll_handler.py",
        "Advanced",
        "20 min",
    ),
    Demo(
        "08-resize",
        "Resize Handler",
        "Window and element resize detection",
        "08_resize_handler.py",
        "Advanced",
        "20 min",
    ),
    Demo(
        "09-attributes",
        "New Datastar Attributes",
        "Explore data-ignore, data-on-load, and more",
        "09_new_attributes.py",
        "Advanced",
        "15 min",
    ),
    Demo(
        "10-todo",
        "Todo List CRUD",
        "Server-driven todo list with session storage and validation",
        "10_todo_list.py",
        "Advanced",
        "25 min",
    ),
    Demo(
        "11-drag",
        "Drag Handler",
        "Drag-and-drop sortable lists with reactive state management",
        "11_drag_handler.py",
        "Advanced",
        "15 min",
    ),
    Demo(
        "12-freeform-drag",
        "🎯 Freeform Drag with Zones",
        "Drag items anywhere while zones track what's over them",
        "12_freeform_drag.py",
        "Advanced",
        "15 min",
    ),
    Demo(
        "13-canvas",
        "Canvas Handler",
        "Infinite pannable/zoomable canvas with touch support",
        "13_canvas_handler.py",
        "Advanced",
        "15 min",
    ),
    Demo(
        "14-canvas-fullpage",
        "Full-Page Canvas",
        "Full viewport infinite canvas with keyboard shortcuts",
        "14_canvas_fullpage.py",
        "Advanced",
        "20 min",
    ),
    Demo(
        "15-nodegraph",
        "🔗 Composable Node Graph",
        "Build a node graph by combining canvas + drag handlers",
        "15_nodegraph_demo.py",
        "Advanced",
        "25 min",
    ),
]


def demo_card(demo: Demo) -> A:
    """Create a demo card component."""
    level_colors = {
        "Foundation": "bg-green-100 text-green-800",
        "Intermediate": "bg-blue-100 text-blue-800",
        "Advanced": "bg-purple-100 text-purple-800",
    }

    return A(
        Div(
            # Header
            Div(
                H3(demo.title, cls="text-xl font-semibold mb-2"),
                Div(
                    Span(demo.level, cls=f"px-2 py-1 rounded-full text-xs font-medium {level_colors[demo.level]}"),
                    Span(demo.time, cls="text-sm text-gray-500 ml-2"),
                    cls="flex items-center mb-3",
                ),
                cls="mb-4",
            ),
            # Description
            P(demo.description, cls="text-gray-600 mb-4 flex-grow"),
            # Footer
            Div(Span("View Demo →", cls="text-blue-600 font-medium"), cls="text-right"),
            cls="flex flex-col h-full",
        ),
        href=demo.route_path,
        cls="block p-6 border border-gray-200 rounded-lg hover:shadow-lg transition-shadow duration-300 hover:border-blue-300 h-full",
    )


def create_demo_grid(level: str) -> Div:
    """Create a grid of demo cards for a specific level."""
    demos_for_level = [demo for demo in DEMOS if demo.level == level]
    grid_cols = "grid-cols-1 md:grid-cols-2" if level != "Advanced" else "grid-cols-1 md:grid-cols-2 lg:grid-cols-3"

    return Div(*[demo_card(demo) for demo in demos_for_level], cls=f"grid {grid_cols} gap-6 mb-12")


@rt("/")
def home():
    """Demo hub homepage with navigation."""
    return Div(
        # Header
        Header(
            Div(
                H1("StarHTML Demo Hub", cls="text-4xl font-bold text-center mb-4"),
                P("Interactive examples to learn StarHTML step by step", cls="text-xl text-gray-600 text-center mb-8"),
                cls="max-w-4xl mx-auto",
            ),
            cls="bg-gradient-to-r from-blue-50 to-purple-50 py-12",
        ),
        # Main content
        Main(
            Div(
                # Learning path sections
                Div(
                    H2("🚀 Foundation", cls="text-2xl font-bold mb-6"),
                    P("Start here to learn the basics of StarHTML and reactive programming.", cls="text-gray-600 mb-8"),
                    create_demo_grid("Foundation"),
                    H2("🔧 Intermediate", cls="text-2xl font-bold mb-6"),
                    P(
                        "Build on the basics with more advanced patterns and debugging techniques.",
                        cls="text-gray-600 mb-8",
                    ),
                    create_demo_grid("Intermediate"),
                    H2("⚡ Advanced", cls="text-2xl font-bold mb-6"),
                    P("Master advanced handlers and real-time interactive patterns.", cls="text-gray-600 mb-8"),
                    create_demo_grid("Advanced"),
                    cls="max-w-6xl mx-auto",
                ),
                cls="container mx-auto px-6 py-12",
            )
        ),
        # Footer
        Footer(
            Div(
                P("StarHTML Demo Hub - Learn reactive web development", cls="text-center text-gray-500"),
                P(
                    "Run individual demos with: ",
                    Code("uv run demo/XX_demo_name.py", cls="bg-gray-100 px-2 py-1 rounded"),
                    cls="text-center text-sm text-gray-500 mt-2",
                ),
                cls="max-w-4xl mx-auto",
            ),
            cls="bg-gray-50 py-8 border-t",
        ),
        cls="min-h-screen flex flex-col",
    )


class DemoLoader:
    """Handles loading and mounting demo applications."""

    @staticmethod
    def load_demo_module(demo: Demo) -> object | None:
        """Load a demo module dynamically."""
        try:
            module_name = f"demo_{demo.id.replace('-', '_')}"
            spec = importlib.util.spec_from_file_location(module_name, demo.file_path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            return module
        except Exception as e:
            print(f"Failed to load demo {demo.id}: {e}")
            return None


def setup_demo_routes(app) -> None:
    """Mount demo applications with proper session middleware sharing."""
    loader = DemoLoader()

    for demo in DEMOS:
        module = loader.load_demo_module(demo)

        if module:
            demo_app = getattr(module, "app", None)
            if demo_app:
                # Mount the demo app at its route path
                demo_mount = Mount(demo.route_path, demo_app)
                app.router.routes.append(demo_mount)
            else:
                pass  # Demo app not found
        else:
            pass  # Failed to load demo


# Set up middleware and routes
app.add_middleware(BackButtonMiddleware)
setup_demo_routes(app)

if __name__ == "__main__":
    print("🚀 StarHTML Demo Hub")
    print("=" * 50)
    print("Visit: http://localhost:5001")
    print("All demos available in one place!")
    print("=" * 50)
    serve(port=5001)
