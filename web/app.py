#!/usr/bin/env python3
"""StarHTML API Documentation - Interactive Documentation (Home Route)"""

import os
from importlib.metadata import version
from pathlib import Path

from demos import app as demos_app
from demos import setup_demos
from head import hdrs
from sections import SECTIONS
from sections import sections as s
from shared import get_source_code, support_dropdown
from starhtml import *
from starhtml.plugins import clipboard, position, scroll, split

VERSION = version("starhtml")

app, rt = star_app(
    title="StarHTML — Python-First Hypermedia Framework",
    middleware=[compression()],
    hdrs=hdrs,
    static_path=str(Path(__file__).parent),
    canonical=False,
    htmlkw={"lang": "en"},
)

app.register(
    scroll,
    position,
    split(name="code_split", responsive=True, responsive_breakpoint=768),
    clipboard,
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
        demos_cta_section(),
    ]


def demos_cta_section():
    return Div(
        Div(
            H2(
                "See It In Action",
                Icon("vaadin:asterisk", cls="ml-2 text-4xl md:text-5xl lg:text-6xl rainbow-sync"),
                cls="text-5xl sm:text-6xl md:text-7xl lg:text-8xl font-black text-black mb-4 flex items-baseline",
            ),
            P("Explore interactive examples.", cls="text-lg md:text-xl text-gray-600 mb-8 sm:mb-12"),
            A(
                Icon("vaadin:asterisk", width="20", height="20", cls="mr-2 text-white"),
                "Browse Live Demos",
                href="/demos",
                cls="inline-flex items-center px-6 py-3 text-base font-semibold text-white rounded-lg rainbow-sync-bg hover:scale-105 transition-transform",
            ),
            cls="w-full px-6 sm:px-8 lg:px-12",
        ),
        cls="pt-12 sm:pt-16 lg:pt-20 pb-24 sm:pb-32 lg:pb-40 bg-white border-t border-gray-200",
    )


def raw_api_markdown_content():
    api_md_path = Path(__file__).parent / "API.md"
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
        Span(f"v{VERSION}", cls="text-xs font-mono text-gray-400 ml-2"),
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
        Div(cls="h-16"),
    )


def philosophy_tab_button(tab_id, icon, label, active_tab, loaded_tabs):
    if tab_id == "python":
        click_action = active_tab.set(tab_id)
    else:
        click_action = f"{active_tab.set(tab_id)}; if (!$loaded_tabs.includes('{tab_id}')) {{ @get('/api/philosophy-tabs/{tab_id}') }}"

    return Button(
        Icon(f"tabler:{icon}", width="20", height="20", cls="mr-2"),
        label,
        data_on_click=click_action,
        data_attr_class=(active_tab == tab_id).if_(
            "flex items-center px-4 py-3 bg-black text-white font-semibold rounded-t-lg",
            "flex items-center px-4 py-3 bg-gray-100 text-gray-700 hover:bg-gray-200 rounded-t-lg transition-colors",
        ),
    )


def philosophy_tabs(active_tab, loaded_tabs):
    return Div(
        philosophy_tab_button("python", "brand-python", "Python First", active_tab, loaded_tabs),
        philosophy_tab_button("types", "shield-check", "Type Safety", active_tab, loaded_tabs),
        philosophy_tab_button("explicit", "eye", "Explicit", active_tab, loaded_tabs),
        philosophy_tab_button("composable", "puzzle", "Composable", active_tab, loaded_tabs),
        cls="flex flex-wrap gap-2",
    )


def philosophy_tab_content(active_tab):
    return Div(
        Div(s.python_first_section(), id="tab-python", data_show=active_tab == "python", style="display: none"),
        Div(id="tab-types", data_show=active_tab == "types", style="display: none"),
        Div(id="tab-explicit", data_show=active_tab == "explicit", style="display: none"),
        Div(id="tab-composable", data_show=active_tab == "composable", style="display: none"),
        cls="bg-white border-2 border-gray-200 rounded-b-lg rounded-tr-lg p-4 sm:p-8 min-h-[400px]",
    )


def core_philosophy_section():
    active_tab = Signal("philosophy_tab", "python")
    loaded_tabs = Signal("loaded_tabs", [])
    return Section(
        active_tab,
        loaded_tabs,
        Div(
            H2("Core Philosophy", cls="text-5xl md:text-6xl font-black text-black mb-8"),
            P("Four principles that make StarHTML powerful yet simple", cls="text-xl text-gray-600 mb-12"),
            philosophy_tabs(active_tab, loaded_tabs),
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
    yield signals({"loaded_tabs": ["types"]}, merge="append")


@rt("/api/philosophy-tabs/explicit")
@sse
def load_explicit_tab(req):
    yield elements(s.explicit_section(), "#tab-explicit", "inner")
    yield signals({"loaded_tabs": ["explicit"]}, merge="append")


@rt("/api/philosophy-tabs/composable")
@sse
def load_composable_tab(req):
    yield elements(s.composable_section(), "#tab-composable", "inner")
    yield signals({"loaded_tabs": ["composable"]}, merge="append")


@rt("/sitemap.xml")
async def sitemap(req):
    from starlette.responses import Response as StarletteResponse

    urls = [
        "https://starhtml.com/",
        "https://starhtml.com/demos/",
    ]
    xml = '<?xml version="1.0" encoding="UTF-8"?>\n'
    xml += '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
    for url in urls:
        xml += f"  <url><loc>{url}</loc></url>\n"
    xml += "</urlset>"
    return StarletteResponse(content=xml, media_type="application/xml")


app.route("/api/source-code/{filename:path}")(get_source_code)

for section in SECTIONS:
    try:
        module = section.load_module()
        if module and hasattr(module, "section_router"):
            module.section_router.to_app(app)
            print(f"  ✓ Registered API routes for {section.title}")
    except Exception as e:
        print(f"  ✗ Failed to register API routes for {section.title}: {e}")

os.environ["STARHTML_DEMOS_MOUNTED"] = "1"
setup_demos()
app.mount("/demos", demos_app)

if __name__ == "__main__":
    serve(port=5009)
