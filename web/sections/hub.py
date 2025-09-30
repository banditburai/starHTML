#!/usr/bin/env python3
"""Sections Development Hub - All sections in one server."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from starhtml import *
from starhtml.handlers import split_handler

try:
    from . import SECTIONS
except ImportError:
    import importlib.util

    init_path = Path(__file__).parent / "__init__.py"
    spec = importlib.util.spec_from_file_location("sections_init", init_path)
    sections_init = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(sections_init)
    SECTIONS = sections_init.SECTIONS


def _info_box(title, items):
    return Div(
        H3(title, cls="text-lg font-bold text-black mb-4"),
        Div(
            *[
                Div(
                    Icon(icon, width="20", height="20", cls=f"{color} mr-3 flex-shrink-0"),
                    P(text, cls="text-sm text-gray-600"),
                    cls=f"flex items-start{' mb-3' if i < len(items) - 1 else ''}",
                )
                for i, (icon, color, text) in enumerate(items)
            ]
        ),
        cls="p-6 bg-gray-50 border border-gray-200 rounded-lg",
    )


def section_card(section, index):
    return Div(
        A(href=section.route, cls="absolute inset-0 z-20", aria_label=f"View {section.title}"),
        Span(f"{index:02d}", cls="absolute top-4 right-6 text-6xl font-black text-gray-100 z-10"),
        Div(
            H3(section.title, cls="text-xl font-bold text-black mb-2"),
            P(section.description, cls="text-sm text-gray-600 leading-relaxed h-10 overflow-hidden"),
            cls="relative z-10",
        ),
        Div(
            Code(section.route, cls="text-xs font-mono text-gray-500"),
            Span("View →", cls="text-sm font-medium text-black"),
            cls="flex items-center justify-between mt-6 relative z-10",
        ),
        cls="relative block p-6 bg-white border-2 border-gray-200 rounded-lg hover:border-gray-300 transition-all group overflow-hidden h-44 cursor-pointer",
    )


app, rt = star_app(
    title="Sections Development Hub",
    hdrs=[
        Script(src="https://cdn.jsdelivr.net/npm/@tailwindcss/browser@4"),
        Script(src="https://cdn.jsdelivr.net/npm/motion@11.11.13/dist/motion.js"),
        split_handler(signal="code_split", persist=False, responsive=True),
        Style("""
            body {
                background: white;
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
                -webkit-font-smoothing: antialiased;
                -moz-osx-font-smoothing: grayscale;
            }
            
            ::selection {
                background: #000;
                color: #fff;
            }
            
            .section-card::before {
                content: '';
                position: absolute;
                inset: 0;
                background: linear-gradient(135deg, transparent 40%, rgba(0,0,0,0.02));
                opacity: 0;
                transition: opacity 0.3s ease;
            }
            
            .section-card:hover::before {
                opacity: 1;
            }
        """),
    ],
    live=True,
    iconify=True,
    compression=False,
    clipboard=True,
)


@rt("/")
def hub_home():
    return Div(
        Div(
            H1("HUB", cls="text-9xl font-black text-gray-100 leading-none select-none"),
            cls="max-w-7xl mx-auto px-6 py-16",
        ),
        Div(
            Div(
                H2("Available Sections", cls="text-2xl font-bold text-black mb-8"),
                Div(
                    *[section_card(s, i + 1) for i, s in enumerate(SECTIONS)],
                    cls="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mb-16",
                ),
                cls="mb-12",
            ),
            Div(
                _info_box(
                    "How It Works",
                    [
                        ("tabler:server", "text-blue-600", "All sections run within this single hub server"),
                        ("tabler:route", "text-green-600", "Each section has its own route namespace"),
                        ("tabler:api", "text-purple-600", "SSE routes and interactive features work seamlessly"),
                    ],
                ),
                Div(
                    H3("Development Tips", cls="text-lg font-bold text-black mb-4"),
                    Ul(
                        Li("Sections auto-reload when you modify their files", cls="text-sm text-gray-600 mb-2"),
                        Li("Use browser DevTools to inspect reactive signals", cls="text-sm text-gray-600 mb-2"),
                        Li("Each section can run standalone or embedded here", cls="text-sm text-gray-600"),
                        cls="list-disc list-inside",
                    ),
                    cls="p-6 bg-gray-50 border border-gray-200 rounded-lg",
                ),
                cls="grid grid-cols-1 md:grid-cols-2 gap-6",
            ),
            cls="max-w-7xl mx-auto px-6 pb-16",
        ),
        cls="min-h-screen bg-white",
    )


def section_wrapper(content):
    back_button = A(
        Icon("tabler:arrow-left", width="18", height="18", cls="mr-2"),
        "Back to Hub",
        href="/",
        cls="inline-flex items-center px-4 py-2 text-sm font-medium text-gray-600 hover:text-black transition-colors",
    )
    return Div(
        Div(Div(back_button, cls="max-w-7xl mx-auto px-6 py-4"), cls="bg-white border-b border-gray-200 mb-8"),
        Div(content, cls="max-w-7xl mx-auto px-6"),
        cls="min-h-screen bg-white",
    )


for section in SECTIONS:

    def create_route(s):
        @rt(s.route)
        def section_page():
            func = s.load_function()
            content = func(embedded=True) if s.needs_embedded_headers else func()
            return section_wrapper(content)

        return section_page

    create_route(section)

    try:
        module = section.load_module()
        if module and hasattr(module, "section_router"):
            module.section_router.to_app(app)
            print(f"  ✓ Registered API routes for {section.title}")
    except Exception:
        pass


if __name__ == "__main__":
    print("\n" + "=" * 50)
    print("🚀 Sections Development Hub")
    print("=" * 50)
    print("Visit: http://localhost:5089/")
    print("Embedded sections available:")

    for section in SECTIONS:
        print(f"  • {section.title} → http://localhost:5089{section.route}")

    print("=" * 50 + "\n")
    serve(port=5089)
