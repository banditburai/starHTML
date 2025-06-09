"""Basic external Javascript lib wrappers"""

import re
from fastcore.utils import *
from starhtml.components import *
from starhtml.xtend import *

# Datastar-compatible element processor
proc_dstar_js = """
window.proc_dstar = function(selector, callback) {
    // Process existing elements on page load
    document.addEventListener('DOMContentLoaded', () => {
        document.querySelectorAll(selector).forEach(callback);
    });
    
    // Also process any existing elements immediately if DOM is already loaded
    if (document.readyState !== 'loading') {
        document.querySelectorAll(selector).forEach(callback);
    }
};
"""

__all__ = [
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


def light_media(
    css: str,  # CSS to be included in the light media query
):
    "Render light media for day mode views"
    return Style("@media (prefers-color-scheme: light) {%s}" % css)


def dark_media(
    css: str,  # CSS to be included in the dark media query
):
    "Render dark media for night mode views"
    return Style("@media (prefers-color-scheme:  dark) {%s}" % css)


marked_imp = """import { marked } from "https://cdn.jsdelivr.net/npm/marked/lib/marked.esm.js";
"""
npmcdn = "https://cdn.jsdelivr.net/npm/"


def MarkdownJS(
    sel=".marked",  # CSS selector for markdown elements
):
    "Implements browser-based markdown rendering."
    src = "proc_dstar('%s', e => e.innerHTML = marked.parse(e.textContent));" % sel
    return Script(proc_dstar_js + marked_imp + src, type="module")


def KatexMarkdownJS(
    sel=".marked",  # CSS selector for markdown elements
    inline_delim="$",  # Delimiter for inline math
    display_delim="$$",  # Delimiter for long math
    math_envs=None,  # List of environments to render as display math
):
    math_envs = math_envs or ["equation", "align", "gather", "multline"]
    env_list = "[" + ",".join(f"'{env}'" for env in math_envs) + "]"
    fn = Path(__file__).parent / "katex.js"
    scr = ScriptX(
        fn,
        display_delim=re.escape(display_delim),
        inline_delim=re.escape(inline_delim),
        sel=sel,
        env_list=env_list,
        type="module",
    )
    css = Link(rel="stylesheet", href=npmcdn + "katex@0.16.11/dist/katex.min.css")
    return scr, css


def HighlightJS(
    sel='pre code:not([data-highlighted="yes"])',  # CSS selector for code elements. Default is industry standard, be careful before adjusting it
    langs: str | list | tuple = "python",  # Language(s) to highlight
    light="atom-one-light",  # Light theme
    dark="atom-one-dark",  # Dark theme
):
    "Implements browser-based syntax highlighting. Usage example [here](/tutorials/quickstart_for_web_devs.html#code-highlighting)."
    src = (
        """
hljs.addPlugin(new CopyButtonPlugin());
hljs.configure({'cssSelector': '%s'});
htmx.onLoad(hljs.highlightAll);"""
        % sel
    )
    hjs = "highlightjs", "cdn-release", "build"
    hjc = "arronhunt", "highlightjs-copy", "dist"
    if isinstance(langs, str):
        langs = [langs]
    langjs = [jsd(*hjs, f"languages/{lang}.min.js") for lang in langs]
    return [
        jsd(*hjs, f"styles/{dark}.css", typ="css", media="(prefers-color-scheme: dark)"),
        jsd(*hjs, f"styles/{light}.css", typ="css", media="(prefers-color-scheme: light)"),
        jsd(*hjs, f"highlight.min.js"),
        jsd(*hjc, "highlightjs-copy.min.js"),
        jsd(*hjc, "highlightjs-copy.min.css", typ="css"),
        *langjs,
        Script(src, type="module"),
    ]


def SortableJS(
    sel=".sortable",  # CSS selector for sortable elements
    ghost_class="blue-background-class",  # When an element is being dragged, this is the class used to distinguish it from the rest
):
    src = """
import {Sortable} from 'https://cdn.jsdelivr.net/npm/sortablejs/+esm';
proc_dstar('%s', el => Sortable.create(el, {ghostClass: '%s'}));
""" % (sel, ghost_class)
    return Script(proc_dstar_js + src, type="module")


def MermaidJS(
    sel=".language-mermaid",  # CSS selector for mermaid elements
    theme="base",  # Mermaid theme to use
):
    "Implements browser-based Mermaid diagram rendering."
    src = """
import mermaid from 'https://cdn.jsdelivr.net/npm/mermaid@11/dist/mermaid.esm.min.mjs';

mermaid.initialize({
    startOnLoad: false,
    theme: '%s',
    securityLevel: 'loose',
    flowchart: { useMaxWidth: false, useMaxHeight: false }
});

function renderMermaidDiagrams(element, index) {
    try {
        const graphDefinition = element.textContent;
        const graphId = `mermaid-diagram-${index}`;
        mermaid.render(graphId, graphDefinition)
            .then(({svg, bindFunctions}) => {
                element.innerHTML = svg;
                bindFunctions?.(element);
            })
            .catch(error => {
                console.error(`Error rendering Mermaid diagram ${index}:`, error);
                element.innerHTML = `<p>Error rendering diagram: ${error.message}</p>`;
            });
    } catch (error) {
        console.error(`Error processing Mermaid diagram ${index}:`, error);
    }
}

proc_dstar('%s', (el, idx) => renderMermaidDiagrams(el, idx));
""" % (theme, sel)
    return Script(proc_dstar_js + src, type="module")
