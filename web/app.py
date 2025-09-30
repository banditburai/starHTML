#!/usr/bin/env python3
"""StarHTML API Documentation - Interactive Documentation (Home Route)"""

import os
from pathlib import Path

from sections import sections as s
from starhtml import *
from starhtml.handlers import position_handler, split_handler

app, rt = star_app(
    title="StarHTML API Documentation",
    hdrs=[
        Script(src="https://cdn.jsdelivr.net/npm/@tailwindcss/browser@4"),
        Script(src="https://cdn.jsdelivr.net/npm/motion@11.11.13/dist/motion.js"),
        (scroll := scroll_handler()),
        position_handler(),
        split_handler(signal="code_split", responsive=True, responsive_breakpoint=768),
        Style("""
            * {
                box-sizing: border-box;
            }
            
            /* Split handler variables */
            :root {
                --split-handle-size: 8px;
                --split-handle-color: rgba(0, 0, 0, 0.15);
                --split-handle-hover-color: rgba(0, 123, 255, 0.3);
                --split-handle-active-color: rgba(0, 123, 255, 0.5);
            }
            
            body, html {
                margin: 0;
                padding: 0;
                width: 100%;
                overflow-x: hidden;
            }
            
            .docs-section {
                min-height: 100vh;
                scroll-margin-top: 80px;
            }
            
            .docs-nav-item {
                transition: all 0.3s ease;
                border-left: 3px solid transparent;
            }
            
            .docs-nav-item.active {
                border-left-color: #000;
                background: rgba(0, 0, 0, 0.05);
            }
            
            .code-example {
                background: #1a1a1a;
                border-radius: 12px;
                overflow: hidden;
                transition: transform 0.3s ease;
            }
            
            .code-example:hover {
                transform: translateY(-2px);
            }
            
            .mini-demo {
                background: white;
                border: 2px solid #f3f4f6;
                border-radius: 16px;
                transition: all 0.3s ease;
            }
            
            .mini-demo:hover {
                border-color: #d1d5db;
                box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.1);
            }
            
            .scroll-progress-container {
                position: fixed;
                top: 60px;
                left: 0;
                width: 100%;
                height: 10px;
                background: rgba(0, 0, 0, 0.1);
                z-index: 40;
            }
            
            .scroll-progress-fill {
                height: 100%;
                background-color: #fbbf24;
                transition: width 0.1s ease;
                width: 0%;
                animation: rainbow-bg 8s ease-in-out infinite;
            }
            
            .fade-in-up {
                opacity: 1;
                transform: translateY(0);
                transition: all 0.8s ease;
            }
            
            .navigation-unselectable {
                user-select: none;
                -webkit-user-select: none;
                -moz-user-select: none;
                -ms-user-select: none;
            }
            
            #markdown-content-container {
                user-select: text;
                -webkit-user-select: text;
                -moz-user-select: text;
                -ms-user-select: text;
            }
            
            @media (max-width: 640px) {
                .desktop-only { display: none !important; }
                .mobile-only { display: flex !important; }
            }
            @media (min-width: 641px) {
                .desktop-only { display: flex !important; }
                .mobile-only { display: none !important; }
            }
            
        """),
    ],
    iconify=True,
    compression=False,
    clipboard=True,
)


@rt("/")
def render_interactive_docs():
    return Div(
        (view_mode := Signal("view_mode", "human")),
        (support_open := Signal("support_open", False)),
        docs_navigation(view_mode, support_open),
        Div(
            Div(
                data_style_width=scroll.page_progress + "%",
                cls="scroll-progress-fill",
                data_scroll=True,
            ),
            cls="scroll-progress-container",
        ),
        Div(*generate_interactive_docs_sections(), data_show=view_mode == "human"),
        Div(
            raw_api_markdown_content(),
            data_show=view_mode == "agent",
            style="display: none",
            cls="fixed top-16 left-0 right-0 bottom-0 bg-white z-30 overflow-auto",
            id="markdown-content-container",
        ),
        cls="min-h-screen bg-white",
        data_on_click="""
            const clickedButton = evt.target.closest('#support_open_button');
            const clickedMenu = evt.target.closest('#support_open_menu');
            
            if (!clickedButton && !clickedMenu) {
                $support_open = false;
            }
        """,
    )


def generate_interactive_docs_sections():
    return [
        s.hero_section(),
        core_philosophy_section(),
        s.quick_reference_section(),
        # s.core_concepts_section(),
        # s.reactivity_section(),
        # s.expressions_logic_section(),
        # s.styling_section(),
    ]


def raw_api_markdown_content():
    api_md_path = Path(__file__).parent.parent / "API.md"

    try:
        content = api_md_path.read_text(encoding="utf-8")
        return Pre(
            Code(content, cls="text-sm leading-relaxed"),
            cls="h-full w-full p-6 bg-white font-mono text-gray-800 whitespace-pre-wrap overflow-auto border-0",
        )
    except Exception as e:
        return Div(
            H3("Error loading API.md", cls="text-xl font-bold text-red-600 mb-4"),
            P(f"Could not load API.md file: {str(e)}", cls="text-gray-700"),
            P("Please ensure API.md exists in the project root.", cls="text-gray-600 text-sm"),
            cls="p-8 bg-red-50 border border-red-200 rounded-lg m-6",
        )


def nav_left_section():
    return Div(
        Span("starHTML", cls="text-lg font-bold text-black"),
        Span("v0.1.26", cls="text-xs font-mono text-gray-400 ml-2"),
        cls="flex items-baseline",
    )


def nav_view_mode_button(mode, icon, label, view_mode):
    return Button(
        Icon(icon, width="18", height="18", cls="sm:mr-1.5"),
        Span(label, cls="hidden sm:inline"),
        data_on_click=view_mode.set(mode),
        data_attr_class=(view_mode == mode).if_(
            "flex items-center px-2 sm:px-3 py-1.5 text-xs font-medium rounded-md bg-gray-900 text-white",
            "flex items-center px-2 sm:px-3 py-1.5 text-xs font-medium rounded-md text-gray-500 hover:text-gray-700 hover:bg-gray-100/80 transition-all",
        ),
        title=f"{label}-friendly view",
    )


def nav_filter_buttons(view_mode):
    return Div(
        nav_view_mode_button("human", "tabler:user", "Human", view_mode),
        nav_view_mode_button("agent", "tabler:robot", "Agent", view_mode),
        cls="flex gap-1 p-1 bg-gray-50/80 rounded-lg border border-gray-200/50",
    )


def docs_navigation(view_mode, support_signal):
    return Div(
        Div(
            Div(
                nav_left_section(),
                Div(nav_filter_buttons(view_mode), support_dropdown(support_signal), cls="flex items-center gap-3"),
                cls="flex items-center justify-between w-full px-4 sm:px-6 lg:px-8 h-16",
            ),
            cls="fixed top-0 left-0 right-0 z-50 backdrop-blur-xl bg-white/80 border-b border-gray-200/50",
            data_class_navigation_unselectable=view_mode == "agent",
        ),
        Div(cls="h-16"),  # Spacer for fixed nav
    )


def philosophy_tab_button(tab_id, icon, label, active_tab):
    return Button(
        Icon(f"tabler:{icon}", width="20", height="20", cls="mr-2"),
        label,
        data_on_click=active_tab.set(tab_id),
        data_attr_class=(active_tab == tab_id).if_(
            "flex items-center px-4 py-3 bg-black text-white font-semibold rounded-t-lg",
            "flex items-center px-4 py-3 bg-gray-100 text-gray-700 hover:bg-gray-200 rounded-t-lg transition-colors",
        ),
    )


def philosophy_tabs(active_tab):
    return Div(
        philosophy_tab_button("python", "brand-python", "Python First", active_tab),
        philosophy_tab_button("types", "shield-check", "Type Safety", active_tab),
        philosophy_tab_button("explicit", "eye", "Explicit", active_tab),
        philosophy_tab_button("composable", "puzzle", "Composable", active_tab),
        cls="flex flex-wrap gap-2",
    )


def philosophy_tab_content(active_tab):
    return Div(
        # Load first tab immediately (default)
        Div(s.python_first_section(), data_show=active_tab == "python", style="display: none"),
        # Lazy load other tabs on first view
        Div(
            data_show=active_tab == "types",
            data_on_intersect=get("/api/philosophy-tabs/types").with_(once=True),
            style="display: none",
            id="tab-types",
        ),
        Div(
            data_show=active_tab == "explicit",
            data_on_intersect=get("/api/philosophy-tabs/explicit").with_(once=True),
            style="display: none",
            id="tab-explicit",
        ),
        Div(
            data_show=active_tab == "composable",
            data_on_intersect=get("/api/philosophy-tabs/composable").with_(once=True),
            style="display: none",
            id="tab-composable",
        ),
        cls="bg-white border-2 border-gray-200 rounded-b-lg rounded-tr-lg p-4 sm:p-8 min-h-[400px]",
    )


def core_philosophy_section():
    active_tab = Signal("philosophy_tab", "python")
    return Section(
        active_tab,
        Div(
            H2("Core Philosophy", cls="text-5xl md:text-6xl font-black text-black mb-8"),
            P("Four principles that make StarHTML powerful yet simple", cls="text-xl text-gray-600 mb-12"),
            philosophy_tabs(active_tab),
            philosophy_tab_content(active_tab),
            cls="fade-in-up w-full px-6 sm:px-8 lg:px-12 py-10",
        ),
        cls="docs-section py-20 bg-gray-50 border-t-2 border-gray-200",
        id="philosophy",
    )


# Philosophy tab lazy loading endpoints
@rt("/api/philosophy-tabs/types")
@sse
def load_type_safety_tab(req):
    yield elements(s.type_safety_section(), "#tab-types", "inner")


@rt("/api/philosophy-tabs/explicit")
@sse
def load_explicit_tab(req):
    yield elements(s.explicit_section(), "#tab-explicit", "inner")


@rt("/api/philosophy-tabs/composable")
@sse
def load_composable_tab(req):
    yield elements(s.composable_section(), "#tab-composable", "inner")


from shared import get_source_code, support_dropdown

app.route("/api/source-code/{filename:path}")(get_source_code)

from sections import SECTIONS

for section in SECTIONS:
    try:
        module = section.load_module()
        if module and hasattr(module, "section_router"):
            module.section_router.to_app(app)
            print(f"  ✓ Registered API routes for {section.title}")
    except Exception as e:
        print(f"  ✗ Failed to register API routes for {section.title}: {e}")

os.environ["STARHTML_DEMOS_MOUNTED"] = "1"
from starlette.routing import Mount

from demos import app as demos_app
from demos import setup_demos

setup_demos()
app.router.routes.append(Mount("/demos", demos_app))

if __name__ == "__main__":
    serve(port=5009)
