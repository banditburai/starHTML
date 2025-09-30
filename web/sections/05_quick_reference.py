"""Quick Reference - Essential Patterns

Displays the Quick Reference section from API.md in a clean, copyable format.
"""

import re
from pathlib import Path

from starlighter import CodeBlock, StarlighterStyles

from starhtml import *
from starhtml.datastar import clipboard


def get_quick_reference_content() -> str:
    api_md_path = Path(__file__).parents[2] / "API.md"

    if not api_md_path.exists():
        return "API.md file not found."

    content = api_md_path.read_text()
    pattern = r"## Quick Reference.*?```python(.*?)```"
    match = re.search(pattern, content, re.DOTALL)

    return match.group(1).strip() if match else "Quick Reference section not found in API.md."


def quick_reference_section() -> Div:
    return Div(
        (copied := Signal("quick_copied", False)),
        StarlighterStyles("github-light"),
        Div(
            Div(
                H2(
                    Icon("tabler:lightning-bolt", width="40", height="40", cls="inline-block mr-2"),
                    "Quick Reference",
                    cls="text-4xl md:text-5xl font-black text-black",
                ),
                P("Copy-paste syntax cheat sheet for common patterns", cls="text-lg text-gray-600 mt-2"),
                cls="flex-1",
            ),
            Button(
                Icon("tabler:clipboard-copy", width="20", height="20", cls="mr-2"),
                Span(
                    data_text=copied.if_("Copied!", "Copy All"),
                    data_class_text_green_600=copied,
                ),
                data_on_click=clipboard(element="quick-ref-code", signal="quick_copied"),
                cls="flex items-center px-6 py-3 bg-black hover:bg-gray-800 text-white font-medium rounded-lg transition-all transform hover:scale-105",
            ),
            cls="flex flex-col md:flex-row items-start md:items-center justify-between gap-4 mb-8",
        ),
        Div(
            CodeBlock(get_quick_reference_content(), lang="python", id="quick-ref-code"),
            data_on_click=clipboard(element="quick-ref-code", signal="quick_copied"),
            title="Click to copy code",
            cls="cursor-pointer hover:opacity-95 transition-opacity",
        ),
        Div(
            Icon("tabler:alert-triangle", width="20", height="20", cls="text-amber-500 mr-2 flex-shrink-0"),
            Div(
                Strong("Common Gotcha: ", cls="text-gray-800"),
                'Use + for reactive strings ("Count: " + counter), not f-strings which are static!',
                cls="text-gray-700",
            ),
            cls="flex items-start p-4 bg-amber-50 border-l-4 border-amber-400 mt-6 rounded-r-lg",
        ),
        cls="fade-in-up w-full px-6 sm:px-8 lg:px-12 py-10 docs-section bg-white",
        id="quick-reference",
    )


app, rt = star_app(
    title="Quick Reference - StarHTML Documentation (Dev Mode)",
    hdrs=[
        Script(src="https://cdn.jsdelivr.net/npm/@tailwindcss/browser@4"),
        Style("""
            body {
                background: white;
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
                -webkit-font-smoothing: antialiased;
            }
            .fade-in-up {
                animation: fadeInUp 0.6s ease-out;
            }
            @keyframes fadeInUp {
                from { opacity: 0; transform: translateY(20px); }
                to { opacity: 1; transform: translateY(0); }
            }
        """),
    ],
    iconify=True,
    clipboard=True,
)


@rt("/")
def dev_home():
    return Div(
        Div("⚠️ Development Mode - Quick Reference Section", cls="bg-yellow-100 p-4 mb-4 text-center font-mono text-sm"),
        quick_reference_section(),
    )


if __name__ == "__main__":
    print("🚀 Quick Reference - Development Mode")
    print("Visit: http://localhost:5095/")
    serve(port=5095)
