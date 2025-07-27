"""Comprehensive tests for external library integrations.

This module tests:
- DatastarProc MutationObserver functionality
- MarkdownJS rendering
- KatexMarkdownJS math rendering
- HighlightJS syntax highlighting
- SortableJS drag-and-drop
- MermaidJS diagram rendering
- Utility functions
"""

from pathlib import Path
from unittest.mock import MagicMock, patch

from starhtml import Code, Div, Pre, Script, star_app
from starhtml.external import (
    DatastarProc,
    HighlightJS,
    KatexMarkdownJS,
    MarkdownJS,
    MermaidJS,
    SortableJS,
    dark_media,
    light_media,
    marked_imp,
    npmcdn,
)


class TestDatastarProc:
    """Test the DatastarProc MutationObserver functionality."""

    def test_datastar_proc_creates_script(self):
        """Test DatastarProc creates the processor script."""
        proc = DatastarProc()

        # Should return a Script element
        assert hasattr(proc, "tag")
        assert proc.tag == "script"

        # Should have the processor ID
        assert proc.attrs.get("id") == "datastar-processor"

        # Should contain the proc_dstar function
        script_content = str(proc.children[0]) if proc.children else ""
        assert "window.proc_dstar" in script_content
        assert "MutationObserver" in script_content
        assert "processNode" in script_content

    def test_datastar_proc_mutation_observer_logic(self):
        """Test the MutationObserver logic in DatastarProc."""
        proc = DatastarProc()
        script_content = str(proc.children[0])

        # Verify key functionality
        assert "document.querySelectorAll(selector).forEach(callback)" in script_content
        assert "observer.observe(document.body" in script_content
        assert "childList: true, subtree: true" in script_content

        # Should handle both existing and dynamically added elements
        assert "processNode" in script_content
        assert "node.matches(selector)" in script_content


class TestMarkdownComponents:
    """Test Markdown rendering components."""

    def test_markdown_js_basic(self):
        """Test basic MarkdownJS component."""
        md = MarkdownJS()

        # Should return a Script element
        assert hasattr(md, "tag")
        assert md.tag == "script"
        assert md.attrs.get("type") == "module"

        # Should contain marked import and processor
        script_content = str(md.children[0])
        assert marked_imp in script_content
        assert "proc_dstar('.marked'" in script_content
        assert "marked.parse(e.textContent)" in script_content

    def test_markdown_js_custom_selector(self):
        """Test MarkdownJS with custom selector."""
        md = MarkdownJS(sel=".my-markdown")
        script_content = str(md.children[0])

        assert "proc_dstar('.my-markdown'" in script_content

    def test_katex_markdown_js(self):
        """Test KatexMarkdownJS math rendering."""
        # Mock the file read since katex.js might not exist in test env
        with patch("starhtml.external.Path.exists", return_value=True):
            with patch("starhtml.xtend.ScriptX", return_value=Script("/* KaTeX script */")):
                katex_components = KatexMarkdownJS()

        # Should return tuple of (script, css)
        assert len(katex_components) == 2
        script, css = katex_components

        # Check script
        assert hasattr(script, "tag")
        assert script.tag == "script"

        # Check CSS link
        assert hasattr(css, "tag")
        assert css.tag == "link"
        assert css.attrs.get("rel") == "stylesheet"
        assert "katex" in css.attrs.get("href", "")

    def test_katex_markdown_js_custom_delimiters(self):
        """Test KatexMarkdownJS with custom delimiters."""
        with patch("starhtml.external.Path") as mock_path:
            # Mock the file path
            mock_path.return_value = MagicMock()
            mock_path.return_value.__truediv__.return_value = MagicMock()

            with patch("starhtml.external.ScriptX") as mock_scriptx:
                mock_scriptx.return_value = Script("/* KaTeX script */")

                KatexMarkdownJS(
                    sel=".math-content", inline_delim="\\(", display_delim="\\[", math_envs=["equation", "align"]
                )

                # Verify ScriptX was called with escaped delimiters
                mock_scriptx.assert_called_once()
                call_kwargs = mock_scriptx.call_args[1]
                assert call_kwargs["inline_delim"] == r"\\\("
                assert call_kwargs["display_delim"] == r"\\\["
                assert call_kwargs["sel"] == ".math-content"

    def test_katex_markdown_js_file_not_found(self):
        """Test KatexMarkdownJS when katex.js file is missing."""
        with patch("starhtml.external.Path") as mock_path:
            mock_path.return_value.parent = Path(__file__).parent
            with patch("starhtml.xtend.ScriptX", side_effect=FileNotFoundError):
                katex_components = KatexMarkdownJS()

                script, css = katex_components
                script_content = str(script.children[0])
                assert "Error: Could not load" in script_content


class TestHighlightJS:
    """Test syntax highlighting functionality."""

    def test_highlight_js_basic(self):
        """Test basic HighlightJS setup."""
        components = HighlightJS()

        # Should return list of components
        assert isinstance(components, list)
        assert len(components) > 5  # CSS files, JS files, script

        # Find the main script
        main_script = None
        for comp in components:
            if hasattr(comp, "tag") and comp.tag == "script" and comp.attrs.get("type") == "module":
                main_script = comp
                break

        assert main_script is not None
        script_content = str(main_script.children[0])

        # Check functionality
        assert "hljs.addPlugin(new CopyButtonPlugin())" in script_content
        assert "highlightElement" in script_content
        assert "proc_dstar('pre code" in script_content
        assert "dataset.highlighted" in script_content

    def test_highlight_js_multiple_languages(self):
        """Test HighlightJS with multiple languages."""
        components = HighlightJS(langs=["python", "javascript", "sql"])

        # Should have language files
        js_components = [c for c in components if hasattr(c, "tag") and c.tag == "script"]
        js_srcs = [c.attrs.get("src", "") for c in js_components]

        # Check for language files
        assert any("python.min.js" in src for src in js_srcs)
        assert any("javascript.min.js" in src for src in js_srcs)
        assert any("sql.min.js" in src for src in js_srcs)

    def test_highlight_js_themes(self):
        """Test HighlightJS with custom themes."""
        components = HighlightJS(light="github", dark="monokai")

        # Find CSS components
        css_components = [c for c in components if hasattr(c, "tag") and c.tag == "link"]

        # Check for theme files
        light_css = None
        dark_css = None
        for css in css_components:
            href = css.attrs.get("href", "")
            css.attrs.get("media", "")
            if "github" in href:
                light_css = css
            elif "monokai" in href:
                dark_css = css

        assert light_css is not None
        assert dark_css is not None
        assert "prefers-color-scheme: light" in light_css.attrs.get("media", "")
        assert "prefers-color-scheme: dark" in dark_css.attrs.get("media", "")


class TestSortableJS:
    """Test drag-and-drop functionality."""

    def test_sortable_js_basic(self):
        """Test basic SortableJS setup."""
        sortable = SortableJS()

        assert hasattr(sortable, "tag")
        assert sortable.tag == "script"
        assert sortable.attrs.get("type") == "module"

        script_content = str(sortable.children[0])
        assert "import {Sortable}" in script_content
        assert "proc_dstar('.sortable'" in script_content
        assert "Sortable.create(el" in script_content
        assert "ghostClass" in script_content

    def test_sortable_js_custom_options(self):
        """Test SortableJS with custom options."""
        sortable = SortableJS(sel=".my-list", ghost_class="dragging")

        script_content = str(sortable.children[0])
        assert "proc_dstar('.my-list'" in script_content
        assert "ghostClass: 'dragging'" in script_content


class TestMermaidJS:
    """Test Mermaid diagram rendering."""

    def test_mermaid_js_basic(self):
        """Test basic MermaidJS setup."""
        mermaid = MermaidJS()

        assert hasattr(mermaid, "tag")
        assert mermaid.tag == "script"
        assert mermaid.attrs.get("type") == "module"

        script_content = str(mermaid.children[0])
        assert "import mermaid" in script_content
        assert "mermaid.initialize" in script_content
        assert "proc_dstar('.language-mermaid'" in script_content
        assert "renderMermaidDiagrams" in script_content

    def test_mermaid_js_custom_options(self):
        """Test MermaidJS with custom options."""
        mermaid = MermaidJS(sel=".mermaid-diagram", theme="dark")

        script_content = str(mermaid.children[0])
        assert "proc_dstar('.mermaid-diagram'" in script_content
        assert "theme: 'dark'" in script_content
        assert "securityLevel: 'loose'" in script_content

    def test_mermaid_error_handling(self):
        """Test MermaidJS error handling code."""
        mermaid = MermaidJS()
        script_content = str(mermaid.children[0])

        # Should have error handling
        assert "catch(error" in script_content
        assert "Error rendering diagram" in script_content
        assert "bindFunctions?" in script_content  # Optional chaining


class TestUtilityFunctions:
    """Test utility functions and helpers."""

    def test_light_media_helper(self):
        """Test light_media CSS helper."""
        css = "body { background: white; }"
        result = light_media(css)

        assert hasattr(result, "tag")
        assert result.tag == "style"

        style_content = str(result.children[0])
        assert "@media (prefers-color-scheme: light)" in style_content
        assert css in style_content

    def test_dark_media_helper(self):
        """Test dark_media CSS helper."""
        css = "body { background: black; }"
        result = dark_media(css)

        assert hasattr(result, "tag")
        assert result.tag == "style"

        style_content = str(result.children[0])
        assert "@media (prefers-color-scheme:  dark)" in style_content
        assert css in style_content

    def test_constants(self):
        """Test module constants."""
        # marked_imp should be the ES6 import statement
        assert "import { marked }" in marked_imp
        assert "marked.esm.js" in marked_imp

        # npmcdn should be the CDN URL
        assert npmcdn == "https://cdn.jsdelivr.net/npm/"


class TestIntegrationScenarios:
    """Test real-world integration scenarios."""

    def test_complete_markdown_page_setup(self):
        """Test setting up a complete page with markdown and highlighting."""
        app, rt = star_app()

        @rt("/")
        def index():
            return Div(
                # Include processors once
                DatastarProc(),
                *HighlightJS(langs=["python", "javascript"]),
                MarkdownJS(),
                # Content that will be processed
                Div("# Hello World\n\nThis is **markdown**!", cls="marked"),
                Pre(Code("def hello():\n    print('Hello!')", cls="language-python")),
                id="content",
            )

        from starlette.testclient import TestClient

        client = TestClient(app)
        response = client.get("/")

        assert response.status_code == 200
        html = response.text

        # Should have the processor
        assert "window.proc_dstar" in html
        assert "datastar-processor" in html

        # Should have markdown processor
        assert "marked.parse" in html

        # Should have highlight.js
        assert "hljs" in html
        assert "highlightElement" in html

    def test_dynamic_content_scenario(self):
        """Test components work with dynamically added content."""
        # Create components
        proc = DatastarProc()
        md = MarkdownJS(sel=".dynamic-md")

        # The DatastarProc should set up MutationObserver
        proc_script = str(proc.children[0])
        assert "MutationObserver" in proc_script
        assert "mutation.addedNodes" in proc_script

        # The MarkdownJS should use proc_dstar
        md_script = str(md.children[0])
        assert "proc_dstar('.dynamic-md'" in md_script

        # This combination means dynamically added .dynamic-md elements
        # will automatically be processed for markdown
