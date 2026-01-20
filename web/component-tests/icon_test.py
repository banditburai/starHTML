"""Icon Component Visual Test - Testing layout stability and class support"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from starhtml import *

app, rt = star_app(
    title="Icon Component Test",
    hdrs=[
        Script(src="https://cdn.jsdelivr.net/npm/@tailwindcss/browser@4"),
        Style("""
            body {
                background: white;
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
                -webkit-font-smoothing: antialiased;
            }
            .test-section {
                border: 1px solid #e5e7eb;
                background: #f9fafb;
                padding: 1.5rem;
                margin-bottom: 1.5rem;
                border-radius: 0.5rem;
            }
            .test-row {
                display: flex;
                align-items: center;
                gap: 1rem;
                padding: 0.75rem;
                background: white;
                border-radius: 0.375rem;
                margin-bottom: 0.5rem;
            }
            .code-sample {
                font-family: 'Courier New', monospace;
                font-size: 0.875rem;
                background: #1f2937;
                color: #e5e7eb;
                padding: 0.5rem 0.75rem;
                border-radius: 0.375rem;
                overflow-x: auto;
            }
            .icon-border {
                border: 1px dashed #d1d5db;
                padding: 0.25rem;
                display: inline-block;
            }
        """),
        iconify_script(),
    ],
)


@rt("/")
def home():
    return Div(
        (reload_trigger := Signal("reload_trigger", False)),
        # Header
        Div(
            H1("Icon Component", cls="text-5xl font-bold text-black"),
            P("Visual test suite for layout stability and class support", cls="text-lg text-gray-600 mt-4"),
            cls="mb-12",
        ),
        # Reload test section
        Div(
            H2("Layout Shift Test", cls="text-2xl font-bold text-black mb-4"),
            P("Watch the icons - they should stay stable and never shift during page load.", cls="text-gray-600 mb-4"),
            Div(
                Span("Text before icon", cls="text-gray-700"),
                Icon("lucide:home", cls="mx-2 text-blue-500 size-5"),
                Span("Text after icon should not jump", cls="text-gray-700"),
                cls="test-row",
            ),
            P(
                "The icons have reserved space in HTML before JavaScript loads, preventing layout shift.",
                cls="text-sm text-gray-500 mt-2",
            ),
            cls="test-section",
        ),
        # Test 1: Default behavior
        Div(
            H2("Test 1: Default Size (1rem)", cls="text-2xl font-bold text-black mb-4"),
            Div(
                Div(
                    Icon("lucide:home"),
                    Span("Default icon (1rem)", cls="ml-2 text-gray-700"),
                ),
                Pre('Icon("lucide:home")', cls="code-sample mt-2"),
                cls="test-row",
            ),
            Div(
                Div(
                    Icon("lucide:star"),
                    Icon("lucide:heart"),
                    Icon("lucide:search"),
                    Span("Multiple default icons inline", cls="ml-2 text-gray-700"),
                ),
                Pre('Icon("lucide:star"), Icon("lucide:heart"), Icon("lucide:search")', cls="code-sample mt-2"),
                cls="test-row",
            ),
            cls="test-section",
        ),
        # Test 2: Explicit sizes
        Div(
            H2("Test 2: Explicit Size Parameter", cls="text-2xl font-bold text-black mb-4"),
            P("Use the size parameter for different icon sizes", cls="text-gray-600 mb-4"),
            Div(
                Div(
                    Div(Icon("lucide:home", size="0.75rem"), cls="icon-border"),
                    Span("size='0.75rem'", cls="text-gray-700"),
                ),
                Pre('Icon("lucide:home", size="0.75rem")', cls="code-sample mt-2"),
                cls="test-row",
            ),
            Div(
                Div(
                    Div(Icon("lucide:star", size=16), cls="icon-border"),
                    Span("size=16 (16px)", cls="text-gray-700"),
                ),
                Pre('Icon("lucide:star", size=16)', cls="code-sample mt-2"),
                cls="test-row",
            ),
            Div(
                Div(
                    Div(Icon("lucide:heart", size="1.5rem"), cls="icon-border"),
                    Span("size='1.5rem'", cls="text-gray-700"),
                ),
                Pre('Icon("lucide:heart", size="1.5rem")', cls="code-sample mt-2"),
                cls="test-row",
            ),
            Div(
                Div(
                    Div(Icon("lucide:zap", size="2rem"), cls="icon-border"),
                    Span("size='2rem'", cls="text-gray-700"),
                ),
                Pre('Icon("lucide:zap", size="2rem")', cls="code-sample mt-2"),
                cls="test-row",
            ),
            Div(
                Div(
                    Div(Icon("lucide:circle", size=48), cls="icon-border"),
                    Span("size=48 (48px)", cls="text-gray-700"),
                ),
                Pre('Icon("lucide:circle", size=48)', cls="code-sample mt-2"),
                cls="test-row",
            ),
            cls="test-section",
        ),
        # Test 3: Width/Height parameters
        Div(
            H2("Test 3: Width/Height Parameters", cls="text-2xl font-bold text-black mb-4"),
            Div(
                Div(
                    Div(Icon("lucide:square", width=24, height=24), cls="icon-border"),
                    Span("width=24, height=24", cls="text-gray-700"),
                ),
                Pre('Icon("lucide:square", width=24, height=24)', cls="code-sample mt-2"),
                cls="test-row",
            ),
            Div(
                Div(
                    Div(Icon("lucide:rectangle-horizontal", width=48, height=24), cls="icon-border"),
                    Span("width=48, height=24 (rectangular)", cls="text-gray-700"),
                ),
                Pre('Icon("lucide:rectangle-horizontal", width=48, height=24)', cls="code-sample mt-2"),
                cls="test-row",
            ),
            cls="test-section",
        ),
        # Test 4: Color classes
        Div(
            H2("Test 4: Color Classes", cls="text-2xl font-bold text-black mb-4"),
            P("Color classes should be inherited by the icon SVG", cls="text-gray-600 mb-4"),
            Div(
                Div(
                    Icon("lucide:home", size="1.5rem", cls="text-red-500"),
                    Icon("lucide:star", size="1.5rem", cls="text-orange-500"),
                    Icon("lucide:heart", size="1.5rem", cls="text-pink-500"),
                    Icon("lucide:zap", size="1.5rem", cls="text-yellow-500"),
                    Icon("lucide:leaf", size="1.5rem", cls="text-green-500"),
                    Icon("lucide:droplet", size="1.5rem", cls="text-blue-500"),
                    Icon("lucide:cloud", size="1.5rem", cls="text-indigo-500"),
                    Icon("lucide:moon", size="1.5rem", cls="text-purple-500"),
                    Icon("lucide:circle", size="1.5rem", cls="text-gray-500"),
                ),
                Pre('Icon("lucide:home", size="1.5rem", cls="text-red-500")', cls="code-sample mt-2"),
                cls="test-row",
            ),
            cls="test-section",
        ),
        # Test 5: Spacing classes
        Div(
            H2("Test 5: Spacing Classes", cls="text-2xl font-bold text-black mb-4"),
            Div(
                Div(
                    Icon("lucide:arrow-left", cls="mr-2"),
                    Span("Icon with mr-2", cls="text-gray-700"),
                ),
                Pre('Icon("lucide:arrow-left", cls="mr-2")', cls="code-sample mt-2"),
                cls="test-row",
            ),
            Div(
                Div(
                    Span("Icon with ml-4", cls="text-gray-700"),
                    Icon("lucide:arrow-right", cls="ml-4"),
                ),
                Pre('Icon("lucide:arrow-right", cls="ml-4")', cls="code-sample mt-2"),
                cls="test-row",
            ),
            Div(
                Div(
                    Icon("lucide:circle", cls="mx-3"),
                    Span("Icon with mx-3", cls="text-gray-700"),
                    Icon("lucide:circle", cls="mx-3"),
                ),
                Pre('Icon("lucide:circle", cls="mx-3")', cls="code-sample mt-2"),
                cls="test-row",
            ),
            cls="test-section",
        ),
        # Test 6: Combined size parameters with classes
        Div(
            H2("Test 6: Combined Size Parameters with Classes", cls="text-2xl font-bold text-black mb-4"),
            P("Size parameters work alongside spacing and color classes", cls="text-gray-600 mb-4"),
            Div(
                Div(
                    Icon("lucide:home", size="1.25rem", cls="mr-2 text-blue-600"),
                    Span("Size + Spacing + Color", cls="text-gray-700"),
                ),
                Pre('Icon("lucide:home", size="1.25rem", cls="mr-2 text-blue-600")', cls="code-sample mt-2"),
                cls="test-row",
            ),
            Div(
                Div(
                    Icon("lucide:star", width="2rem", height="2rem", cls="ml-3 text-amber-500"),
                    Span("Width/Height + Spacing + Color", cls="text-gray-700"),
                ),
                Pre(
                    'Icon("lucide:star", width="2rem", height="2rem", cls="ml-3 text-amber-500")',
                    cls="code-sample mt-2",
                ),
                cls="test-row",
            ),
            cls="test-section",
        ),
        # Test 7: Button examples
        Div(
            H2("Test 7: Buttons with Icons", cls="text-2xl font-bold text-black mb-4"),
            Div(
                Button(
                    Icon("lucide:home", cls="mr-2"),
                    "Home",
                    cls="px-4 py-2 bg-black text-white font-medium hover:bg-gray-800 transition-colors",
                ),
                Pre('Button(Icon("lucide:home", cls="mr-2"), "Home", ...)', cls="code-sample mt-2"),
                cls="test-row",
            ),
            Div(
                Button(
                    Icon("lucide:download", size=16, cls="mr-2"),
                    "Download",
                    cls="px-4 py-2 border border-gray-300 text-black font-medium hover:border-gray-500 transition-colors",
                ),
                Pre('Button(Icon("lucide:download", size=16, cls="mr-2"), "Download", ...)', cls="code-sample mt-2"),
                cls="test-row",
            ),
            Div(
                Button(
                    Icon("lucide:settings", size="1.25rem"),
                    cls="p-2 bg-gray-100 hover:bg-gray-200 transition-colors rounded",
                ),
                Pre('Button(Icon("lucide:settings", size="1.25rem"), ...)', cls="code-sample mt-2"),
                cls="test-row",
            ),
            cls="test-section",
        ),
        # Test 8: Flex containers
        Div(
            H2("Test 8: Flex Containers", cls="text-2xl font-bold text-black mb-4"),
            P("Icons should not shrink in flex layouts (flex-shrink: 0)", cls="text-gray-600 mb-4"),
            Div(
                Div(
                    Icon("lucide:alert-circle", cls="text-red-500 mr-2"),
                    Span(
                        "This is a very long error message that should wrap but the icon should maintain its size and not shrink",
                        cls="text-gray-700",
                    ),
                    cls="flex items-center bg-red-50 border border-red-200 p-3 rounded",
                    style="max-width: 400px;",
                ),
                Pre('Div(Icon(...), Span(...), cls="flex items-center")', cls="code-sample mt-2"),
                cls="test-row",
            ),
            cls="test-section",
        ),
        # Test 9: Unstable mode
        Div(
            H2("Test 9: Unstable Mode (stable=False)", cls="text-2xl font-bold text-black mb-4"),
            P("Bare iconify-icon without wrapper - may have layout shift", cls="text-gray-600 mb-4"),
            Div(
                Div(
                    Icon("lucide:home", stable=False, cls="text-gray-500"),
                    Span("Unstable icon (no wrapper)", cls="ml-2 text-gray-700"),
                ),
                Pre('Icon("lucide:home", stable=False, cls="text-gray-500")', cls="code-sample mt-2"),
                cls="test-row",
            ),
            cls="test-section",
        ),
        cls="max-w-4xl mx-auto px-6 py-12",
    )


serve(port=5004)
