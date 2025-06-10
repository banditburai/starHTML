"""Tests for StarHTML js module functionality"""

from starhtml.js import (
    HighlightJS,
    KatexMarkdownJS,
    MarkdownJS,
    MermaidJS,
    SortableJS,
    dark_media,
    light_media,
    marked_imp,
    npmcdn,
    proc_dstar_js,
)


class TestMediaUtilities:
    def test_light_media(self):
        """Test light_media function"""
        css = "body { background: white; }"
        result = light_media(css)
        assert result.tag == "style"
        # Should contain light media query
        style_content = result.children[0] if result.children else ""
        assert "prefers-color-scheme: light" in str(style_content)
        assert "body { background: white; }" in str(style_content)

    def test_dark_media(self):
        """Test dark_media function"""
        css = "body { background: black; }"
        result = dark_media(css)
        assert result.tag == "style"
        # Should contain dark media query
        style_content = result.children[0] if result.children else ""
        assert "prefers-color-scheme:  dark" in str(style_content)
        assert "body { background: black; }" in str(style_content)


class TestMarkdownJS:
    def test_markdown_js_basic(self):
        """Test basic MarkdownJS creation"""
        result = MarkdownJS()
        assert result.tag == "script"
        assert result.attrs.get("type") == "module"

        # Should contain expected JavaScript components
        script_content = result.children[0] if result.children else ""
        script_str = str(script_content)
        assert "proc_dstar" in script_str
        assert "marked" in script_str
        assert ".marked" in script_str  # default selector

    def test_markdown_js_custom_selector(self):
        """Test MarkdownJS with custom selector"""
        result = MarkdownJS(sel=".custom-markdown")
        script_content = result.children[0] if result.children else ""
        script_str = str(script_content)
        assert ".custom-markdown" in script_str


class TestKatexMarkdownJS:
    def test_katex_markdown_js_basic(self):
        """Test basic KatexMarkdownJS creation"""
        result = KatexMarkdownJS()
        # Should return tuple of script and css
        assert isinstance(result, tuple)
        assert len(result) == 2

        script, css = result
        assert script.tag == "script"
        assert css.tag == "link"
        assert css.attrs.get("rel") == "stylesheet"
        assert "katex" in css.attrs.get("href", "")

    def test_katex_markdown_js_custom_delimiters(self):
        """Test KatexMarkdownJS with custom delimiters"""
        result = KatexMarkdownJS(inline_delim="\\(", display_delim="\\[")
        script, css = result
        assert script.tag == "script"
        # Note: Testing implementation details would be fragile,
        # just verify it produces valid script

    def test_katex_markdown_js_custom_envs(self):
        """Test KatexMarkdownJS with custom math environments"""
        result = KatexMarkdownJS(math_envs=["align", "equation"])
        script, css = result
        assert script.tag == "script"
        assert css.tag == "link"


class TestHighlightJS:
    def test_highlight_js_basic(self):
        """Test basic HighlightJS creation"""
        result = HighlightJS()
        assert isinstance(result, list)
        assert len(result) > 5  # Should return multiple elements

        # Check that we have CSS files for themes
        css_elements = [el for el in result if hasattr(el, "tag") and el.tag == "link"]
        assert len(css_elements) >= 2  # Should have light and dark themes

        # Check that we have script elements
        script_elements = [el for el in result if hasattr(el, "tag") and el.tag == "script"]
        assert len(script_elements) >= 2  # Should have multiple scripts

    def test_highlight_js_single_language(self):
        """Test HighlightJS with single language"""
        result = HighlightJS(langs="javascript")
        assert isinstance(result, list)
        # Should still work with single language
        script_elements = [el for el in result if hasattr(el, "tag") and el.tag == "script"]
        assert len(script_elements) >= 2

    def test_highlight_js_multiple_languages(self):
        """Test HighlightJS with multiple languages"""
        result = HighlightJS(langs=["python", "javascript", "css"])
        assert isinstance(result, list)
        # Should have more elements for multiple languages
        script_elements = [el for el in result if hasattr(el, "tag") and el.tag == "script"]
        assert len(script_elements) >= 4  # Base scripts + language scripts

    def test_highlight_js_custom_themes(self):
        """Test HighlightJS with custom themes"""
        result = HighlightJS(light="github", dark="monokai-sublime")
        css_elements = [el for el in result if hasattr(el, "tag") and el.tag == "link"]
        assert len(css_elements) >= 2

        # Check that theme names appear in hrefs
        hrefs = [el.attrs.get("href", "") for el in css_elements]
        assert any("github" in href for href in hrefs)
        assert any("monokai-sublime" in href for href in hrefs)


class TestSortableJS:
    def test_sortable_js_basic(self):
        """Test basic SortableJS creation"""
        result = SortableJS()
        assert result.tag == "script"
        assert result.attrs.get("type") == "module"

        script_content = result.children[0] if result.children else ""
        script_str = str(script_content)
        assert "Sortable" in script_str
        assert "proc_dstar" in script_str
        assert ".sortable" in script_str  # default selector

    def test_sortable_js_custom_selector(self):
        """Test SortableJS with custom selector"""
        result = SortableJS(sel=".custom-sortable")
        script_content = result.children[0] if result.children else ""
        script_str = str(script_content)
        assert ".custom-sortable" in script_str

    def test_sortable_js_custom_ghost_class(self):
        """Test SortableJS with custom ghost class"""
        result = SortableJS(ghost_class="my-ghost-class")
        script_content = result.children[0] if result.children else ""
        script_str = str(script_content)
        assert "my-ghost-class" in script_str


class TestMermaidJS:
    def test_mermaid_js_basic(self):
        """Test basic MermaidJS creation"""
        result = MermaidJS()
        assert result.tag == "script"
        assert result.attrs.get("type") == "module"

        script_content = result.children[0] if result.children else ""
        script_str = str(script_content)
        assert "mermaid" in script_str
        assert "proc_dstar" in script_str
        assert ".language-mermaid" in script_str  # default selector

    def test_mermaid_js_custom_selector(self):
        """Test MermaidJS with custom selector"""
        result = MermaidJS(sel=".mermaid-diagram")
        script_content = result.children[0] if result.children else ""
        script_str = str(script_content)
        assert ".mermaid-diagram" in script_str

    def test_mermaid_js_custom_theme(self):
        """Test MermaidJS with custom theme"""
        result = MermaidJS(theme="dark")
        script_content = result.children[0] if result.children else ""
        script_str = str(script_content)
        assert "dark" in script_str
        # Should contain theme configuration
        assert "theme:" in script_str


class TestConstants:
    def test_marked_imp_constant(self):
        """Test marked_imp constant"""
        assert isinstance(marked_imp, str)
        assert "marked" in marked_imp
        assert "cdn.jsdelivr.net" in marked_imp

    def test_npmcdn_constant(self):
        """Test npmcdn constant"""
        assert isinstance(npmcdn, str)
        assert "cdn.jsdelivr.net" in npmcdn

    def test_proc_dstar_js_constant(self):
        """Test proc_dstar_js constant"""
        assert isinstance(proc_dstar_js, str)
        assert "proc_dstar" in proc_dstar_js
        assert "DOMContentLoaded" in proc_dstar_js
