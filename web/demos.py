#!/usr/bin/env python3
"""StarHTML Demo Hub - Standalone and Mountable"""

import importlib.util
import os
import sys
from dataclasses import dataclass
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from starlette.routing import Mount

from starhtml import *
from starhtml.handlers import position_handler, split_handler

try:
    from starlighter import StarlighterStyles
except ImportError:
    StarlighterStyles = None


app, rt = star_app(
    title="StarHTML Demo Hub",
    hdrs=[
        Script(src="https://cdn.jsdelivr.net/npm/@tailwindcss/browser@4"),
        (splitter := split_handler(signal="demo_split", responsive=True, responsive_breakpoint=768)),
        position_handler(),
        StarlighterStyles("github-light") if StarlighterStyles else None,
        Script("""
            document.addEventListener('DOMContentLoaded', () => {
                // Create overlay to prevent iframe from capturing mouse during drag
                const overlay = document.createElement('div');
                overlay.style.cssText = 'position:fixed;top:0;left:0;right:0;bottom:0;z-index:9999;display:none;';
                document.body.appendChild(overlay);
                
                // Show overlay when dragging starts
                document.addEventListener('mousedown', (e) => {
                    if (e.target.dataset.splitHandle) {
                        overlay.style.display = 'block';
                    }
                });
                
                // Hide overlay when dragging ends
                document.addEventListener('mouseup', () => {
                    overlay.style.display = 'none';
                });
            });
        """),
        Style("""
            * {
                box-sizing: border-box;
            }
            
            :root {
                --split-handle-size: 8px;
                --split-handle-color: rgba(0, 0, 0, 0.15);
                --split-handle-hover-color: rgba(0, 123, 255, 0.3);
                --split-handle-active-color: rgba(0, 123, 255, 0.5);
            }
            
            body, html {
                background: #fff;
                color: #000;
                margin: 0;
                padding: 0;
                width: 100%;
                overflow-x: hidden;
                -webkit-font-smoothing: antialiased;
                -moz-osx-font-smoothing: grayscale;
            }
            ::selection {
                background: #000;
                color: #fff;
            }
            
            /* Make navigation and UI elements non-selectable */
            nav,
            nav *,
            button,
            .view-btn-active,
            .view-btn-inactive,
            [data-split-handle],
            .split-wrapper > :not(.panel),
            .panel.left iframe {
                -webkit-user-select: none;
                -moz-user-select: none;
                -ms-user-select: none;
                user-select: none;
            }
            
            /* Only allow selection in code areas */
            .panel.right,
            [id^="code-"] pre,
            [id^="code-"] code,
            [id^="split-code-"] pre,
            [id^="split-code-"] code,
            .code-container,
            .code-container * {
                -webkit-user-select: text;
                -moz-user-select: text;
                -ms-user-select: text;
                user-select: text;
            }
            
            /* View mode buttons */
            .view-btn-active {
                background: black;
                color: white;
            }
            .view-btn-inactive {
                background: white;
                color: black;
            }
            .view-btn-inactive:hover {
                background: rgb(249 250 251);
            }
            
            .split-wrapper {
                position: absolute;
                inset: 0;
                z-index: 1;
            }
            
            [data-split] {
                z-index: 10;
                position: relative;
            }
            
            .split-wrapper .split-container {
                height: 100%;
                width: 100%;
                display: flex;
                overflow: hidden;
            }
            
            .split-wrapper .panel {
                overflow: auto;
            }
            
            .split-wrapper .panel.left {
                background: white;
            }
            
            .split-wrapper .panel.right {
                background: white;
            }
            
            
            [id^="code-"], [id^="split-code-"] {
                min-height: 100%;
                background: white;
            }
            
            [id^="code-"] *,
            [id^="split-code-"] * {
                font-family: 'SF Mono', Monaco, 'Cascadia Code', 'Roboto Mono', Consolas, 'Courier New', monospace;
            }
            
            /* Starlighter provides syntax highlighting styles via StarlighterStyles component */
                        
        """),
    ],
    iconify=True,
    compression=False,
)


@dataclass
class Demo:
    id: str
    title: str
    description: str
    file: str
    level: str

    @property
    def file_path(self) -> Path:
        return Path(__file__).parent / "demos" / self.file

    @property
    def route_path(self) -> str:
        prefix = "/demos" if os.environ.get("STARHTML_DEMOS_MOUNTED") else ""
        return f"{prefix}/demo/{self.id}/"

    @property
    def view_path(self) -> str:
        prefix = "/demos" if os.environ.get("STARHTML_DEMOS_MOUNTED") else ""
        return f"{prefix}/view/{self.id}/"

    def load_as_mount(self) -> Mount | None:
        try:
            module_name = f"demo_{self.id.replace('-', '_')}"
            spec = importlib.util.spec_from_file_location(module_name, self.file_path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

            if hasattr(module, "app"):
                mount_path = f"/demo/{self.id}"
                return Mount(mount_path, app=module.app)
            else:
                print(f"Demo {self.id} doesn't have an 'app' attribute")
                return None
        except Exception as e:
            import traceback

            print(f"Failed to load demo {self.id}: {e}")
            traceback.print_exc()
            return None


DEMOS = [
    Demo(
        "01-signals",
        "Basic Signals",
        "Reactive data binding with Datastar signals",
        "01_basic_signals.py",
        "Foundation",
    ),
    Demo(
        "02-sse",
        "Server-Sent Events",
        "Real-time updates with SSE elements",
        "02_sse_elements.py",
        "Foundation",
    ),
    Demo(
        "03-forms",
        "Forms & Binding",
        "Form handling and data binding patterns",
        "03_forms_binding.py",
        "Foundation",
    ),
    Demo(
        "04-live-updates",
        "Live Updates",
        "Real-time notifications and auto-targeting patterns",
        "04_live_updates.py",
        "Practical",
    ),
    Demo(
        "05-background",
        "Background Tasks",
        "File uploads, concurrent APIs, and async patterns",
        "05_background_tasks.py",
        "Practical",
    ),
    Demo(
        "06-attributes",
        "Control Attributes",
        "Explore data-ignore, data-on-load, and slot_attrs",
        "06_control_attributes.py",
        "Intermediate",
    ),
    Demo(
        "07-todo",
        "Todo List",
        "Server-driven todo list with session storage and validation",
        "07_todo_list.py",
        "Intermediate",
    ),
    Demo(
        "08-routing",
        "Routing Patterns",
        "Dynamic routes, parameters, and navigation",
        "08_routing_patterns.py",
        "Intermediate",
    ),
    Demo(
        "09-persist",
        "Persist Handler",
        "Data persistence with localStorage and sessionStorage",
        "09_persist_handler.py",
        "Handlers",
    ),
    Demo(
        "10-scroll",
        "Scroll Handler",
        "Scroll detection and position tracking",
        "10_scroll_handler.py",
        "Handlers",
    ),
    Demo(
        "11-resize",
        "Resize Handler",
        "Window and element resize detection",
        "11_resize_handler.py",
        "Handlers",
    ),
    Demo(
        "12-drag",
        "Drag Handler",
        "Drag-and-drop sortable lists with reactive state management",
        "12_drag_handler.py",
        "Handlers",
    ),
    Demo(
        "13-freeform-drag",
        "Freeform Drag",
        "Drag items anywhere while zones track what's over them",
        "13_freeform_drag.py",
        "Advanced",
    ),
    Demo(
        "14-canvas",
        "Canvas Handler",
        "Infinite pannable/zoomable canvas with touch support",
        "14_canvas_handler.py",
        "Advanced",
    ),
    Demo(
        "15-canvas-fullpage",
        "Full-Page Canvas",
        "Full viewport infinite canvas with keyboard shortcuts",
        "15_canvas_fullpage.py",
        "Advanced",
    ),
    Demo(
        "16-nodegraph",
        "Node Graph",
        "Build a node graph by combining canvas + drag handlers",
        "16_nodegraph_demo.py",
        "Advanced",
    ),
    Demo(
        "17-position",
        "Position Handler",
        "Clean positioning with Floating UI integration",
        "17_position_handler.py",
        "Advanced",
    ),
    Demo(
        "18-split-responsive",
        "Split Responsive",
        "Responsive split with mobile stacking",
        "18_split_responsive.py",
        "Advanced",
    ),
    Demo(
        "19-split-universal",
        "Split Universal",
        "Full universal split demo - FT Splitter with Datastar patterns",
        "19_split_universal.py",
        "Advanced",
    ),
    Demo(
        "20-toggle-patterns",
        "Advanced Toggles",
        "Complex toggle interactions and state management",
        "20_advanced_toggle_patterns.py",
        "Patterns",
    ),
    Demo(
        "21-complex-modifiers",
        "Complex Modifiers",
        "Advanced modifier combinations and patterns",
        "21_complex_modifiers.py",
        "Patterns",
    ),
    Demo(
        "22-property-chaining",
        "Property Chaining",
        "Deep property access and manipulation",
        "22_nested_property_chaining.py",
        "Patterns",
    ),
    Demo(
        "23-datastar-helpers",
        "Helper Functions",
        "Master logical operators, math functions, templates, and debugging",
        "23_datastar_helpers_showcase.py",
        "Patterns",
    ),
]


def find_demo_by_id(demo_id: str) -> Demo:
    return next((demo for demo in DEMOS if demo.id == demo_id), None)


def find_demo_by_path(path: str) -> Demo:
    return next((demo for demo in DEMOS if demo.route_path.rstrip("/") == path.rstrip("/")), None)


def demo_calendar_card(demo: Demo, index: int) -> Div:
    demo_id = demo.id.split("-", 1)[0]
    return A(
        Div(
            Div(demo_id.zfill(2), cls="text-5xl sm:text-6xl font-black text-gray-200 mb-3"),
            Div(demo.title, cls="text-sm sm:text-base font-semibold text-black leading-tight"),
        ),
        href=demo.view_path,
        cls="block p-8 sm:p-10 border-r border-b border-gray-200 hover:bg-gray-50 transition-colors group min-h-[180px] sm:min-h-[220px] flex flex-col justify-between",
    )


def demo_list_card(demo: Demo) -> Div:
    demo_id = demo.id.split("-", 1)[0]

    return A(
        Div(
            Span(
                demo_id.zfill(2),
                cls="text-4xl sm:text-5xl md:text-6xl font-black text-gray-100 w-16 sm:w-20 md:w-24 flex-shrink-0",
            ),
            Div(
                H3(demo.title, cls="text-lg sm:text-xl font-bold text-black mb-1 group-hover:underline"),
                P(demo.description, cls="text-gray-600 text-sm sm:text-base"),
                cls="flex-1 px-4 sm:px-6 md:px-8",
            ),
        ),
        href=demo.view_path,
        cls="flex items-center py-6 sm:py-8 md:py-10 border-b border-gray-200 hover:bg-white transition-colors group",
    )


def demo_foundation_card(demo: Demo) -> Div:
    demo_id = demo.id.split("-", 1)[0]

    return A(
        Div(
            Div(demo_id.zfill(2), cls="text-4xl sm:text-5xl font-black text-white/80 mb-3 relative z-10"),
            Div(demo.title, cls="text-base sm:text-lg font-semibold text-white leading-tight mb-2 relative z-10"),
            P(demo.description, cls="text-sm text-white/70 leading-relaxed relative z-10"),
            Div(cls="absolute inset-0 bg-gradient-to-br from-gray-700 to-gray-800 rounded-lg"),
            cls="relative p-6 sm:p-8 min-h-[200px] flex flex-col justify-between overflow-hidden",
        ),
        href=demo.view_path,
        cls="block border border-gray-600 rounded-lg hover:border-gray-500 hover:shadow-xl hover:-translate-y-1 transition-all duration-300 group shadow-[0_1px_0_rgba(255,255,255,0.05)_inset]",
    )


def demo_elevated_feature_card(demo: Demo) -> Div:
    demo_id = demo.id.split("-", 1)[0]

    return Div(
        A(
            # Floating number indicator
            Div(
                Span(demo_id.zfill(2), cls="text-xs font-mono text-white"),
                cls="absolute -top-2 -left-2 w-8 h-8 bg-gray-600 rounded-full flex items-center justify-center z-30",
            ),
            # Main content card
            Div(
                H3(
                    demo.title,
                    cls="text-xl sm:text-2xl font-bold text-black mb-3 group-hover:text-gray-800 transition-colors",
                ),
                P(demo.description, cls="text-gray-900 leading-relaxed mb-6"),
                Div(
                    Span("Explore", cls="text-sm font-medium text-gray-500"),
                    Span("→", cls="text-lg ml-2 group-hover:translate-x-1 transition-transform"),
                    cls="flex items-center",
                ),
                cls="p-8 bg-white rounded-xl border border-gray-200 relative z-20",
            ),
            # Dynamic shadow layers
            Div(
                cls="absolute inset-0 bg-black/5 rounded-xl transform translate-x-1 translate-y-1 z-10 group-hover:translate-x-2 group-hover:translate-y-2 transition-transform"
            ),
            Div(
                cls="absolute inset-0 bg-black/3 rounded-xl transform translate-x-2 translate-y-2 z-0 group-hover:translate-x-4 group-hover:translate-y-4 transition-transform"
            ),
            href=demo.view_path,
            cls="block group relative",
        ),
        cls="relative hover:-translate-y-2 transition-transform duration-300",
    )


def demo_minimal_card(demo: Demo) -> Div:
    demo_id = demo.id.split("-", 1)[0]

    return Div(
        A(
            Span(f"{demo_id.zfill(2)}.", cls="text-gray-400 font-mono text-sm sm:text-base"),
            Span(demo.title, cls="text-black font-semibold ml-3 sm:ml-4 group-hover:underline text-base sm:text-lg"),
            Span(" — ", cls="text-gray-300 mx-2 hidden sm:inline"),
            Span(demo.description, cls="text-gray-500 text-sm sm:text-base hidden md:inline"),
            href=demo.view_path,
            cls="flex items-baseline group py-3 flex-1",
        ),
        A(
            "view source",
            href=f"https://github.com/banditburai/starHTML/blob/refactor-to-kwarg/demo/{demo.file}",
            target="_blank",
            rel="noopener noreferrer",
            cls="text-xs text-gray-400 hover:text-gray-600 font-mono ml-2 flex-shrink-0",
        ),
        cls="flex items-baseline",
    )


def demo_card(demo: Demo) -> Div:
    demo_id = demo.id.split("-", 1)[0]
    level_styles = {
        "Foundation": "text-gray-500",
        "Practical": "text-gray-400",
        "Intermediate": "text-gray-400",
        "Handlers": "text-gray-300",
        "Advanced": "text-gray-300",
        "Patterns": "text-white",
        "Production": "text-yellow-400",
    }

    return Div(
        A(
            # Large number as visual element
            Div(
                Span(
                    demo_id.zfill(2),
                    cls="text-5xl font-black text-gray-800 group-hover:text-gray-600 transition-colors",
                ),
                cls="mb-4",
            ),
            # Bold title
            H3(demo.title, cls="text-xl font-bold text-white mb-2 group-hover:text-gray-200 transition-colors"),
            # Subtle description
            P(demo.description, cls="text-sm text-gray-500 mb-4 leading-relaxed"),
            # Minimal level indicator
            Div(
                Span(
                    demo.level.upper(),
                    cls=f"text-xs font-medium tracking-wider {level_styles.get(demo.level, 'text-gray-500')}",
                ),
                cls="flex items-center justify-between",
            ),
            href=demo.view_path,
            cls="group block p-6 bg-black border border-gray-900 hover:border-gray-700 hover:-translate-y-px transition-all duration-200",
        ),
        cls="h-full",
    )


from shared import get_source_code, support_dropdown

app.route("/api/source-code/{filename:path}")(get_source_code)


def demo_breadcrumbs(demo, base_url):
    return Div(
        A(
            Icon("tabler:home", width="18", height="18", cls="text-gray-400 group-hover:text-black"),
            href="/",
            cls="text-xs text-gray-500 hover:text-black transition-colors",
            title="Back to Docs",
        ),
        Span(" / ", cls="text-gray-300 mx-1"),
        A("Demos", href=f"{base_url}/", cls="text-xs text-gray-500 hover:text-black transition-colors"),
        Span(" / ", cls="text-gray-300 mx-1"),
        Span(f"{demo.id.split('-')[0].zfill(2)}. {demo.title}", cls="text-xs font-semibold text-black"),
        cls="flex items-center",
    )


def demo_view_buttons(view_mode):
    return Div(
        Button(
            Icon("tabler:devices", width="18", height="18"),
            data_on_click=view_mode.set("demo"),
            cls="p-1.5 rounded-md hover:bg-gray-100/80 transition-all",
            data_attr_class=(view_mode == "demo").if_(
                "p-1.5 rounded-md text-black hover:bg-gray-100/80 transition-all",
                "p-1.5 rounded-md text-gray-400 hover:text-black hover:bg-gray-100/80 transition-all",
            ),
            title="Demo View",
        ),
        Button(
            Icon("tabler:layout-columns", width="18", height="18"),
            data_on_click=view_mode.set("split"),
            cls="p-1.5 rounded-md hover:bg-gray-100/80 transition-all",
            data_attr_class=(view_mode == "split").if_(
                "p-1.5 rounded-md text-black hover:bg-gray-100/80 transition-all",
                "p-1.5 rounded-md text-gray-400 hover:text-black hover:bg-gray-100/80 transition-all",
            ),
            title="Split View",
        ),
        Button(
            Icon("tabler:code", width="18", height="18"),
            data_on_click=view_mode.set("code"),
            cls="p-1.5 rounded-md hover:bg-gray-100/80 transition-all",
            data_attr_class=(view_mode == "code").if_(
                "p-1.5 rounded-md text-black hover:bg-gray-100/80 transition-all",
                "p-1.5 rounded-md text-gray-400 hover:text-black hover:bg-gray-100/80 transition-all",
            ),
            title="Code View",
        ),
        cls="flex gap-0.5",
    )


def demo_navigation_controls(prev_demo, next_demo):
    return Div(
        (
            A(
                Icon("tabler:arrow-left", width="20", height="20", cls="text-gray-400 group-hover:text-black block"),
                href=prev_demo.view_path,
                cls="p-1.5 rounded-md hover:bg-gray-100/80 transition-all group",
                title=prev_demo.title,
            )
            if prev_demo
            else Div(
                Icon("tabler:arrow-left", width="20", height="20", cls="text-gray-300 block"),
                cls="p-1.5 opacity-30 cursor-not-allowed",
            )
        ),
        (
            A(
                Icon("tabler:arrow-right", width="20", height="20", cls="text-gray-400 group-hover:text-black block"),
                href=next_demo.view_path,
                cls="p-1.5 rounded-md hover:bg-gray-100/80 transition-all group",
                title=next_demo.title,
            )
            if next_demo
            else Div(
                Icon("tabler:arrow-right", width="20", height="20", cls="text-gray-300 block"),
                cls="p-1.5 opacity-30 cursor-not-allowed",
            )
        ),
        cls="flex items-center gap-1",
    )


def demo_navigation_bar(demo, view_mode, support_open, prev_demo, next_demo, base_url):
    return Nav(
        Div(
            Div(demo_breadcrumbs(demo, base_url), demo_view_buttons(view_mode), cls="flex items-end gap-1.5"),
            Div(
                support_dropdown(support_open),
                demo_navigation_controls(prev_demo, next_demo),
                cls="flex items-end gap-2",
            ),
            cls="flex items-end justify-between h-16 pb-3",
        ),
        cls="fixed top-0 left-0 right-0 z-50 backdrop-blur-xl bg-white/80 border-b border-gray-200/50 px-4 sm:px-6 lg:px-8",
    )


def demo_content_views(demo, view_mode):
    return Div(
        Iframe(
            src=demo.route_path, data_show=view_mode == "demo", cls="absolute inset-0 w-full h-full border-0 bg-white"
        ),
        Div(
            Div(id=f"code-{demo.id}", cls="h-full overflow-auto p-4"),
            data_show=view_mode == "code",
            cls="absolute inset-0",
        ),
        Div(
            Div(
                Iframe(src=demo.route_path, cls="panel left w-full h-full border-0 bg-white"),
                Div(data_split="demo_split:horizontal:50,50"),
                Div(Div(id=f"split-code-{demo.id}", cls="h-full overflow-auto p-4"), cls="panel right"),
                cls="split-container",
            ),
            data_show=view_mode == "split",
            cls="absolute inset-0 split-wrapper",
        ),
        Script(f"""
            document.addEventListener('DOMContentLoaded', function() {{
                fetch('/api/source-code/{demo.file}')
                    .then(r => r.text())
                    .then(html => {{
                        const codeEl = document.getElementById('code-{demo.id}');
                        const splitCodeEl = document.getElementById('split-code-{demo.id}');
                        if (codeEl) codeEl.innerHTML = html;
                        if (splitCodeEl) splitCodeEl.innerHTML = html;
                    }})
                    .catch(err => console.error('Failed to load code:', err));
            }});
        """),
        cls="fixed top-16 left-0 right-0 bottom-0",
    )


@rt("/view/{demo_id}/")
def demo_with_nav(req, demo_id: str):
    demo = find_demo_by_id(demo_id)
    if not demo:
        return Div(
            H1("Demo Not Found", cls="text-2xl font-bold text-red-600 mb-4"),
            P(f"Demo '{demo_id}' does not exist.", cls="text-gray-700"),
            A("Back to Hub", href="/", cls="text-blue-600 hover:underline"),
            cls="p-8",
        )

    demo_idx = next((i for i, d in enumerate(DEMOS) if d.id == demo.id), -1)
    prev_demo = DEMOS[demo_idx - 1] if demo_idx > 0 else None
    next_demo = DEMOS[demo_idx + 1] if demo_idx < len(DEMOS) - 1 else None

    base_url = "/demos" if os.environ.get("STARHTML_DEMOS_MOUNTED") else ""

    signal_id = demo.id.replace("-", "_")
    view_mode = Signal(f"view_{signal_id}", "demo")
    support_open = Signal(f"support_{signal_id}", False)

    return Div(
        view_mode,
        support_open,
        demo_navigation_bar(demo, view_mode, support_open, prev_demo, next_demo, base_url),
        Div(cls="h-16"),
        demo_content_views(demo, view_mode),
        Div(
            data_show=support_open,
            data_on_click=support_open.set(False),
            cls="fixed inset-0 z-[999]",
            style="background: transparent; cursor: default;",
        ),
    )


def setup_demos():
    if hasattr(app, "_demos_mounted") and app._demos_mounted:
        return

    app._demos_mounted = True

    mounted_count = 0
    for demo in DEMOS:
        mount = demo.load_as_mount()
        if mount:
            app.router.routes.append(mount)
            mounted_count += 1

    print(f"🎯 Successfully mounted {mounted_count}/{len(DEMOS)} demos")


def demos_navigation(support_open):
    return Nav(
        Div(
            Div(
                A(
                    Icon("tabler:home", width="18", height="18", cls="text-gray-400 group-hover:text-black"),
                    href="/",
                    cls="p-1.5 rounded-md hover:bg-gray-100/80 transition-all group",
                    title="Back to Docs",
                ),
                Span(" / ", cls="text-gray-300 mx-1"),
                Span("Demos", cls="text-sm font-semibold text-black"),
                cls="flex items-center",
            ),
            support_dropdown(support_open),
            cls="w-full max-w-none px-6 sm:px-8 lg:px-12 py-4 flex justify-between items-center",
        ),
        cls="bg-white border-b border-gray-100",
    )


def demos_hero():
    return Header(
        Div(
            Div(
                H1(
                    "From a single file",
                    cls="text-5xl sm:text-6xl md:text-7xl lg:text-8xl xl:text-9xl font-black text-black leading-[0.9] tracking-tight",
                ),
                H1(
                    "To a galaxy of possibilities.",
                    cls="text-5xl sm:text-6xl md:text-7xl lg:text-8xl xl:text-9xl font-black text-gray-300 leading-[1.1] tracking-tight",
                ),
                cls="mb-8 sm:mb-10",
            ),
            P(
                "The brightest way to build reactive websites in Python.",
                cls="text-lg md:text-xl lg:text-2xl text-gray-600 leading-relaxed mb-8 sm:mb-12",
            ),
            Div(
                A(
                    "Start Exploring",
                    href="#foundation",
                    cls="inline-block px-6 sm:px-8 py-3 sm:py-4 bg-black text-white font-semibold hover:bg-gray-900 transition-colors text-base sm:text-lg",
                ),
                A(
                    "Learn More",
                    href="/",
                    cls="inline-block px-6 sm:px-8 py-3 sm:py-4 border border-gray-300 text-black font-semibold hover:border-gray-500 hover:bg-gray-50 transition-colors text-base sm:text-lg",
                ),
                cls="flex gap-4",
            ),
            cls="w-full px-6 sm:px-8 lg:px-12 py-12 sm:py-16 md:py-20 lg:py-24",
        ),
        cls="bg-white",
    )


def demos_by_level(level):
    return [demo for demo in DEMOS if demo.level == level]


@rt("/")
def home():
    support_open = Signal("hub_support", False)

    return Div(
        support_open,
        demos_navigation(support_open),
        demos_hero(),
        Main(
            Div(
                Div(
                    H2(
                        "Foundation",
                        cls="text-5xl sm:text-6xl md:text-7xl lg:text-8xl font-black text-black mb-4",
                        id="foundation",
                    ),
                    P("Start here. Core concepts.", cls="text-lg md:text-xl text-gray-500 mb-8 sm:mb-12"),
                    Div(
                        *[demo_calendar_card(demo, i) for i, demo in enumerate(demos_by_level("Foundation"))],
                        cls="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-0 border border-gray-200 rounded-lg overflow-hidden",
                    ),
                    cls="w-full px-6 sm:px-8 lg:px-12",
                ),
                cls="py-12 sm:py-16 lg:py-20 bg-white",
            ),
            Div(
                Div(
                    H2(
                        "Practical",
                        cls="text-5xl sm:text-6xl md:text-7xl lg:text-8xl font-black text-gray-900 mb-4",
                        id="practical",
                    ),
                    P("Build real features.", cls="text-lg md:text-xl text-gray-500 mb-8 sm:mb-12"),
                    Div(
                        *[demo_list_card(demo) for demo in demos_by_level("Practical")],
                        cls="space-y-0 border-t border-gray-200",
                    ),
                    cls="w-full px-6 sm:px-8 lg:px-12",
                ),
                cls="py-12 sm:py-16 lg:py-20 bg-gray-50",
            ),
            Div(
                Div(
                    H2("Intermediate", cls="text-5xl sm:text-6xl md:text-7xl lg:text-8xl font-black text-white mb-4"),
                    P("Combine concepts.", cls="text-lg text-white/80 mb-8 sm:mb-12"),
                    Div(
                        *[demo_foundation_card(demo) for demo in demos_by_level("Intermediate")],
                        cls="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6",
                    ),
                    cls="w-full px-6 sm:px-8 lg:px-12",
                ),
                cls="py-12 sm:py-16 lg:py-20 bg-gradient-to-br from-gray-700 via-gray-800 to-gray-900",
            ),
            Div(
                Div(
                    H2(
                        "Handlers",
                        cls="text-5xl sm:text-6xl md:text-7xl lg:text-8xl font-black text-gray-700 mb-4",
                        id="handlers",
                    ),
                    P("Specialized event handlers.", cls="text-lg md:text-xl text-gray-500 mb-8 sm:mb-12"),
                    Div(
                        *[demo_list_card(demo) for demo in demos_by_level("Handlers")],
                        cls="space-y-0 border-t border-gray-200",
                    ),
                    cls="w-full px-6 sm:px-8 lg:px-12",
                ),
                cls="py-12 sm:py-16 lg:py-20 bg-gray-50",
            ),
            Div(
                Div(
                    H2("Advanced", cls="text-5xl sm:text-6xl md:text-7xl lg:text-8xl font-black text-black mb-4"),
                    P("Shine brilliantly with Python.", cls="text-lg md:text-xl text-gray-500 mb-8 sm:mb-12"),
                    Div(
                        *[demo_elevated_feature_card(demo) for demo in demos_by_level("Advanced")],
                        cls="grid grid-cols-1 lg:grid-cols-2 gap-12",
                    ),
                    cls="w-full px-6 sm:px-8 lg:px-12",
                ),
                cls="py-12 sm:py-16 lg:py-20 bg-white relative",
            ),
            Div(
                Div(
                    H2(
                        "Patterns",
                        cls="text-5xl sm:text-6xl md:text-7xl lg:text-8xl font-black text-gray-200 mb-4",
                        id="patterns",
                    ),
                    P("Master the platform.", cls="text-lg md:text-xl text-gray-400 mb-8 sm:mb-12"),
                    Div(
                        *[demo_minimal_card(demo) for demo in demos_by_level("Patterns")], cls="space-y-6 sm:space-y-8"
                    ),
                    cls="w-full px-6 sm:px-8 lg:px-12",
                ),
                cls="py-12 sm:py-16 lg:py-20 bg-gray-50",
            ),
            Div(
                Div(
                    H2("Production", cls="text-5xl sm:text-6xl md:text-7xl lg:text-8xl font-black text-white mb-4"),
                    P("Ship real applications with confidence.", cls="text-lg md:text-xl text-white/90 mb-8 sm:mb-12"),
                    Div(
                        *[demo_card(demo) for demo in demos_by_level("Production")],
                        cls="grid grid-cols-1 sm:grid-cols-2 gap-6",
                    ),
                    cls="w-full px-6 sm:px-8 lg:px-12",
                ),
                cls="py-12 sm:py-16 lg:py-20 bg-gradient-to-br from-gray-900 via-black to-gray-800",
            ),
        ),
        Footer(
            Div(
                Div(
                    P("StarHTML Demo Hub", cls="text-sm font-semibold text-gray-600 mb-2"),
                    P("© 2025 - Interactive Python Components", cls="text-xs text-gray-400"),
                    cls="text-center",
                ),
                cls="w-full px-6 sm:px-8 lg:px-12 py-8",
            ),
            cls="bg-white border-t border-gray-100 mt-12",
        ),
        cls="min-h-screen bg-white",
        data_on_click="""
            const clickedTrigger = evt.target.closest('#hub_support_button');
            const clickedInsideMenu = evt.target.closest('#hub_support_menu');
            
            if (!clickedTrigger && !clickedInsideMenu) {
                $hub_support = false;
            }
        """,
    )


# Module exports for external use
__all__ = ["app", "DEMOS", "Demo"]

# Always setup demos to ensure routes are available
setup_demos()

if __name__ == "__main__":
    print("Starting StarHTML Demo Hub...")
    print(f"Available demos: {len(DEMOS)}")
    serve(port=5016, reload=True)
