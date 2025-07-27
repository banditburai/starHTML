"""External JavaScript library wrappers and integrations"""

import re

from fastcore.utils import *

from starhtml.xtend import *

from .tags import Link, Script

__all__ = [
    "DatastarProc",
    "marked_imp",
    "npmcdn",
    "light_media",
    "dark_media",
    "MarkdownJS",
    "KatexMarkdownJS",
    "HighlightJS",
    "SortableJS",
    "MermaidJS",
]

# ============================================================================
# Core Dynamic Content Processor
# ============================================================================
""" Developer includes processor once, then uses components efficiently
head = Fragment(
    DatastarProc(),  # Required once per page
    *HighlightJS(langs=['python'])
)

# Components work efficiently
body = Fragment(
    MarkdownJS('.content'),
    MermaidJS('.diagrams')
)
"""
# Datastar-compatible element processor using MutationObserver for dynamic content
_proc_dstar_js = """
window.proc_dstar = function(selector, callback) {
    const processNode = (node) => {
        if (node.nodeType === 1) { // Element nodes only
            if (node.matches && node.matches(selector)) {
                callback(node);
            }
            if (node.querySelectorAll) {
                node.querySelectorAll(selector).forEach(callback);
            }
        }
    };

    // Process existing elements
    document.querySelectorAll(selector).forEach(callback);

    // Watch for dynamically added content using MutationObserver
    const observer = new MutationObserver((mutations) => {
        mutations.forEach((mutation) => {
            if (mutation.type === 'childList') {
                mutation.addedNodes.forEach(processNode);
            }
        });
    });

    observer.observe(document.body, { childList: true, subtree: true });
};
"""


def DatastarProc():
    "Core MutationObserver-based processor for dynamic content. Include once per page."
    return Script(_proc_dstar_js, id="datastar-processor")


# ============================================================================
# Style and Utility Helpers
# ============================================================================


def light_media(
    css: str,  # CSS to be included in the light media query
):
    return Style(f"@media (prefers-color-scheme: light) {{{css}}}")


def dark_media(
    css: str,  # CSS to be included in the dark media query
):
    return Style(f"@media (prefers-color-scheme:  dark) {{{css}}}")


marked_imp = """import { marked } from "https://cdn.jsdelivr.net/npm/marked/lib/marked.esm.js";
"""
npmcdn = "https://cdn.jsdelivr.net/npm/"

# ============================================================================
# External Library Components
# ============================================================================


def MarkdownJS(
    sel=".marked",  # CSS selector for markdown elements
):
    "Implements browser-based markdown rendering. Requires DatastarProc()."
    src = f"proc_dstar('{sel}', e => e.innerHTML = marked.parse(e.textContent));"
    return Script(marked_imp + src, type="module")


def KatexMarkdownJS(
    sel=".marked",  # CSS selector for markdown elements
    inline_delim="$",  # Delimiter for inline math
    display_delim="$$",  # Delimiter for long math
    math_envs=None,  # List of environments to render as display math
):
    "Implements KaTeX math rendering in markdown. Requires DatastarProc()."
    math_envs = math_envs or ["equation", "align", "gather", "multline"]
    env_list = "[" + ",".join(f"'{env}'" for env in math_envs) + "]"
    fn = Path(__file__).parent / "static" / "js" / "external" / "katex.js"
    try:
        scr = ScriptX(
            fn,
            display_delim=re.escape(display_delim),
            inline_delim=re.escape(inline_delim),
            sel=sel,
            env_list=env_list,
            type="module",
        )
    except FileNotFoundError:
        print(f"Warning: KatexMarkdownJS could not find file: {fn}")
        scr = Script(f"/* KatexMarkdownJS Error: Could not load {fn} */")
    css = Link(rel="stylesheet", href=npmcdn + "katex@0.16.11/dist/katex.min.css")
    return scr, css


def HighlightJS(
    sel='pre code:not([data-highlighted="yes"])',  # CSS selector for code elements
    langs: str | list | tuple = "python",  # Language(s) to highlight
    light="atom-one-light",  # Light theme
    dark="atom-one-dark",  # Dark theme
):
    "Implements browser-based syntax highlighting. Requires DatastarProc()."
    src = f"""
// Initialize highlight.js with copy plugin
hljs.addPlugin(new CopyButtonPlugin());

// Function to highlight a single element
const highlightElement = (el) => {{
    if (el.dataset.highlighted === 'yes') return;
    hljs.highlightElement(el);
    el.dataset.highlighted = 'yes';
}};

// Use Datastar-compatible processor for dynamic content
proc_dstar('{sel}', highlightElement);
"""
    hjs = "highlightjs", "cdn-release", "build"
    hjc = "arronhunt", "highlightjs-copy", "dist"
    if isinstance(langs, str):
        langs = [langs]
    langjs = [jsd(*hjs, f"languages/{lang}.min.js") for lang in langs]
    return [
        jsd(*hjs, f"styles/{dark}.css", typ="css", media="(prefers-color-scheme: dark)"),
        jsd(*hjs, f"styles/{light}.css", typ="css", media="(prefers-color-scheme: light)"),
        jsd(*hjs, "highlight.min.js"),
        jsd(*hjc, "highlightjs-copy.min.js"),
        jsd(*hjc, "highlightjs-copy.min.css", typ="css"),
        *langjs,
        Script(src, type="module"),
    ]


def SortableJS(
    sel=".sortable",  # CSS selector for sortable elements
    ghost_class="blue-background-class",  # When an element is being dragged, this is the class used to distinguish it from the rest
):
    "Implements drag-and-drop sorting. Requires DatastarProc()."
    src = f"""
import {{Sortable}} from 'https://cdn.jsdelivr.net/npm/sortablejs/+esm';
proc_dstar('{sel}', el => Sortable.create(el, {{ghostClass: '{ghost_class}'}}));
"""
    return Script(src, type="module")


def MermaidJS(
    sel=".language-mermaid",  # CSS selector for mermaid elements
    theme="base",  # Mermaid theme to use
):
    "Implements browser-based Mermaid diagram rendering. Requires DatastarProc()."
    src = f"""
import mermaid from 'https://cdn.jsdelivr.net/npm/mermaid@11/dist/mermaid.esm.min.mjs';

mermaid.initialize({{
    startOnLoad: false,
    theme: '{theme}',
    securityLevel: 'loose',
    flowchart: {{ useMaxWidth: false, useMaxHeight: false }}
}});

function renderMermaidDiagrams(element, index) {{
    try {{
        const graphDefinition = element.textContent;
        const graphId = `mermaid-diagram-${{index}}`;
        mermaid.render(graphId, graphDefinition)
            .then(({{svg, bindFunctions}}) => {{
                element.innerHTML = svg;
                bindFunctions?.(element);
            }})
            .catch(error => {{
                console.error(`Error rendering Mermaid diagram ${{index}}:`, error);
                element.innerHTML = `<p>Error rendering diagram: ${{error.message}}</p>`;
            }});
    }} catch (error) {{
        console.error(`Error processing Mermaid diagram ${{index}}:`, error);
    }}
}}

proc_dstar('{sel}', (el, idx) => renderMermaidDiagrams(el, idx));
"""
    return Script(src, type="module")
