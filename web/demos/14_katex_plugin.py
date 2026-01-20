"""Dynamic KaTeX Demo - Math rendering plugin with live updates"""

from starhtml import *
from starhtml.plugins import katex

app, rt = star_app(
    title="Dynamic KaTeX Math",
    htmlkw={"lang": "en"},
    hdrs=[
        Script(src="https://cdn.jsdelivr.net/npm/@tailwindcss/browser@4"),
        Style("""
            body { background: white; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; }
            /* Math content styling */
            .math-content { line-height: 1.8; }
            .math-content p { margin: 1em 0; word-wrap: break-word; }
            .math-content h1 { font-size: 1.5em; font-weight: bold; margin: 1em 0 0.5em; }
            .math-content h2 { font-size: 1.25em; font-weight: bold; margin: 1em 0 0.5em; }
            .math-content ul { margin: 1em 0; padding-left: 2em; }
            .math-content li { margin: 0.5em 0; }
            .math-content strong { font-weight: 600; }
            /* Reset pre wrapper styling */
            .math-content > pre[data-katex] {
                background: none;
                color: inherit;
                padding: 0;
                margin: 0;
                font-family: inherit;
                font-size: inherit;
                white-space: normal;
                overflow: visible;
            }
        """),
    ],
)
app.register(katex)

# Sample math content
SAMPLES = {
    "basics": """# Basic Math

Inline math: The quadratic formula is $x = \\frac{-b \\pm \\sqrt{b^2 - 4ac}}{2a}$.

Display math (centered):

$$E = mc^2$$

$$\\int_0^\\infty e^{-x^2} dx = \\frac{\\sqrt{\\pi}}{2}$$""",
    "calculus": """# Calculus

## Derivatives

The derivative of $f(x) = x^n$ is $f'(x) = nx^{n-1}$.

$$\\frac{d}{dx}\\left[\\sin(x)\\right] = \\cos(x)$$

## Integrals

$$\\int x^n dx = \\frac{x^{n+1}}{n+1} + C$$

$$\\int_a^b f(x) dx = F(b) - F(a)$$""",
    "matrices": """# Linear Algebra

## Vectors and Matrices

A vector: $\\vec{v} = \\begin{pmatrix} 1 \\\\ 2 \\\\ 3 \\end{pmatrix}$

A matrix multiplication:

$$\\begin{bmatrix} a & b \\\\ c & d \\end{bmatrix} \\begin{bmatrix} x \\\\ y \\end{bmatrix} = \\begin{bmatrix} ax + by \\\\ cx + dy \\end{bmatrix}$$

## Determinant

$$\\det(A) = \\begin{vmatrix} a & b \\\\ c & d \\end{vmatrix} = ad - bc$$""",
    "physics": """# Physics Equations

## Mechanics

Newton's second law: $F = ma$

Kinetic energy: $KE = \\frac{1}{2}mv^2$

$$\\vec{F} = m\\vec{a} = m\\frac{d\\vec{v}}{dt}$$

## Electromagnetism

Maxwell's equations in differential form:

$$\\nabla \\cdot \\vec{E} = \\frac{\\rho}{\\epsilon_0}$$

$$\\nabla \\times \\vec{B} = \\mu_0\\vec{J} + \\mu_0\\epsilon_0\\frac{\\partial\\vec{E}}{\\partial t}$$""",
}

DEFAULT_CUSTOM = """# My Custom Math

Try writing your own equations!

Inline: \\(a^2 + b^2 = c^2\\) (Pythagorean theorem)

Display mode:

\\[\\sum_{n=1}^{\\infty} \\frac{1}{n^2} = \\frac{\\pi^2}{6}\\]

**Tip:** Use backslash-paren for inline, backslash-bracket for display."""


def katex_content(text: str):
    """Render content with KaTeX math processing."""
    return Div(
        # Content-based ID: morphing treats as new element only when content changes
        Pre(text, data_katex=True, id=f"katex-{hash(text)}"),
        cls="math-content",
    )


@rt("/")
def home():
    return Div(
        # Signal for custom content
        (custom_math := Signal("custom_math", DEFAULT_CUSTOM)),
        # Header
        Div(
            H1("14", cls="text-8xl font-black text-gray-100 leading-none"),
            H1("KaTeX Math", cls="text-5xl md:text-6xl font-bold text-black mt-2"),
            P("Dynamic math rendering with the katex plugin", cls="text-lg text-gray-600 mt-4"),
            cls="mb-16",
        ),
        # Content selector
        Div(
            H3("Sample Equations", cls="text-2xl font-bold text-black mb-6"),
            Div(
                Button(
                    "Basics",
                    data_on_click=get("math/basics"),
                    cls="px-4 py-2 bg-black text-white font-medium hover:bg-gray-800 transition-colors",
                ),
                Button(
                    "Calculus",
                    data_on_click=get("math/calculus"),
                    cls="px-4 py-2 bg-black text-white font-medium hover:bg-gray-800 transition-colors",
                ),
                Button(
                    "Matrices",
                    data_on_click=get("math/matrices"),
                    cls="px-4 py-2 bg-black text-white font-medium hover:bg-gray-800 transition-colors",
                ),
                Button(
                    "Physics",
                    data_on_click=get("math/physics"),
                    cls="px-4 py-2 bg-black text-white font-medium hover:bg-gray-800 transition-colors",
                ),
                cls="mb-8 flex flex-wrap gap-2",
            ),
            cls="mb-8",
        ),
        # Math display
        Div(
            katex_content(SAMPLES["basics"]),
            cls="p-4 sm:p-8 bg-gray-50 border border-gray-200 rounded-lg min-h-[300px] overflow-x-auto",
            id="math-display",
        ),
        # Custom math editor with debounced auto-render
        Div(
            H3("Custom Math", cls="text-xl sm:text-2xl font-bold text-black mb-6"),
            P(
                "Edit the equations below - preview updates automatically:",
                cls="text-gray-600 mb-4 text-sm sm:text-base",
            ),
            Textarea(
                DEFAULT_CUSTOM,
                data_bind=custom_math,
                data_on_input=get("math/custom").with_(debounce=500),
                rows="12",
                cls="w-full p-3 sm:p-4 font-mono text-xs sm:text-sm border border-gray-300 rounded-lg focus:border-gray-500 focus:outline-none mb-4",
            ),
            Div(
                katex_content(DEFAULT_CUSTOM),
                cls="p-4 sm:p-8 bg-gray-50 border border-gray-200 rounded-lg min-h-[200px] overflow-x-auto",
                id="custom-math-display",
            ),
            cls="mt-8 sm:mt-12 p-4 sm:p-8 bg-white border border-gray-200 rounded-lg",
        ),
        cls="max-w-4xl mx-auto px-4 sm:px-8 lg:px-16 py-12 sm:py-16 md:py-24 bg-white min-h-screen",
    )


@rt("/math/custom")
@sse
def get_custom(custom_math: str = ""):
    """Render custom math - signal auto-extracted by StarHTML."""
    text = custom_math or DEFAULT_CUSTOM
    yield elements(katex_content(text), "#custom-math-display", "inner")


@rt("/math/{name}")
@sse
def get_math(name: str):
    """Return math content by name via SSE."""
    text = SAMPLES.get(name, SAMPLES["basics"])
    yield elements(katex_content(text), "#math-display", "inner")


if __name__ == "__main__":
    serve(port=5014)
