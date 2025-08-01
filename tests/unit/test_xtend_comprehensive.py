"""Comprehensive tests for StarHTML xtend module.

This module provides tests for all xtend functionality including:
- Core component extensions (A, AX, Form, Fragment)
- Form helpers (Hidden, CheckboxX)
- Script and style helpers (Script, Style, ScriptX, StyleX, run_js, jsd)
- SEO and social media components (Socials, Favicon, YouTubeEmbed)
- String formatting utilities (loose_format, double_braces, etc.)
"""

import tempfile
from pathlib import Path

import pytest
from fastcore.xml import Safe

from starhtml.datastar import ds_bind, ds_on_submit, ds_show, ds_text
from starhtml.xtend import (
    AX,
    A,
    CheckboxX,
    Favicon,
    Form,
    Fragment,
    Hidden,
    Nbsp,
    Script,
    ScriptX,
    Socials,
    Style,
    StyleX,
    YouTubeEmbed,
    double_braces,
    jsd,
    loose_format,
    replace_css_vars,
    run_js,
    undouble_braces,
)


class TestCoreComponents:
    """Test core component extensions."""

    def test_a_link_basic(self):
        """Test basic A link creation."""
        link = A("Click me")
        html = str(link)
        assert 'href="#"' in html  # Default href
        assert "Click me" in html
        assert "<a" in html

    def test_a_link_with_get(self):
        """Test A link with get parameter."""
        link = A("Get data", get="/api/data")
        html = str(link)
        assert "data-on-click=\"@get('/api/data')\"" in html
        assert 'href="#"' in html

    def test_a_link_custom_href(self):
        """Test A link with custom href."""
        link = A("External", href="https://example.com")
        html = str(link)
        assert 'href="https://example.com"' in html

    def test_a_link_with_datastar_attrs(self):
        """Test A link with additional Datastar attributes."""
        link = A("Button", ds_show("$isVisible"), ds_text("$dynamicText"))
        html = str(link)
        assert 'data-show="$isVisible"' in html
        assert 'data-text="$dynamicText"' in html

    def test_ax_convenience_function(self):
        """Test AX convenience function."""
        link = AX("Quick link", get="/api/quick")
        html = str(link)
        assert "Quick link" in html
        assert "data-on-click=\"@get('/api/quick')\"" in html
        assert 'href="#"' in html

    def test_ax_without_get(self):
        """Test AX without get parameter."""
        link = AX("Simple link", href="/page")
        html = str(link)
        assert "Simple link" in html
        assert 'href="/page"' in html
        assert "data-on-click" not in html

    def test_form_default_enctype(self):
        """Test Form has default multipart enctype."""
        form = Form("Content")
        html = str(form)
        assert 'enctype="multipart/form-data"' in html
        assert "Content" in html
        assert "<form" in html

    def test_form_custom_enctype(self):
        """Test Form with custom enctype."""
        form = Form("Content", enctype="application/x-www-form-urlencoded")
        html = str(form)
        assert 'enctype="application/x-www-form-urlencoded"' in html

    def test_form_with_datastar_attrs(self):
        """Test Form with Datastar attributes."""
        form = Form("Form content", ds_bind("formData"), ds_on_submit("handleSubmit()"))
        html = str(form)
        assert 'data-bind="formData"' in html
        assert 'data-on-submit="handleSubmit()"' in html

    def test_fragment_empty_container(self):
        """Test Fragment creates empty container."""
        fragment = Fragment("Content 1", "Content 2")
        html = str(fragment)
        assert "Content 1" in html
        assert "Content 2" in html
        # Fragment should not have a wrapping tag
        assert html.count("<") == 0  # No opening tags
        assert html.count(">") == 0  # No closing tags


class TestFormHelpers:
    """Test form helper components."""

    def test_hidden_basic(self):
        """Test basic Hidden input."""
        hidden = Hidden("secret_value")
        html = str(hidden)
        assert 'type="hidden"' in html
        assert 'value="secret_value"' in html
        assert "<input" in html

    def test_hidden_with_id(self):
        """Test Hidden input with ID."""
        hidden = Hidden("value", id="hidden_field")
        assert hidden.attrs["id"] == "hidden_field"
        assert hidden.attrs["value"] == "value"
        assert hidden.attrs["type"] == "hidden"

    def test_hidden_with_datastar_attrs(self):
        """Test Hidden basic functionality."""
        hidden = Hidden("value")
        html = str(hidden)
        assert 'type="hidden"' in html
        assert 'value="value"' in html

    def test_checkboxx_basic(self):
        """Test basic CheckboxX."""
        checkbox = CheckboxX()
        # CheckboxX returns a tuple: (hidden, checkbox)
        assert isinstance(checkbox, tuple)
        assert len(checkbox) == 2

        hidden_html = str(checkbox[0])
        checkbox_html = str(checkbox[1])

        assert 'type="hidden"' in hidden_html
        assert 'type="checkbox"' in checkbox_html

    def test_checkboxx_checked(self):
        """Test CheckboxX with checked state."""
        checkbox = CheckboxX(checked=True)
        checkbox_html = str(checkbox[1])
        assert "checked" in checkbox_html

    def test_checkboxx_with_label(self):
        """Test CheckboxX with label."""
        checkbox = CheckboxX(label="Accept terms")
        # Should wrap checkbox in label
        checkbox_html = str(checkbox[1])
        assert "Accept terms" in checkbox_html
        assert "<label" in checkbox_html

    def test_checkboxx_with_id_and_name(self):
        """Test CheckboxX with ID and name."""
        checkbox = CheckboxX(id="terms", name="terms_accepted")
        checkbox_input = checkbox[1]
        assert checkbox_input.attrs["id"] == "terms"
        assert checkbox_input.attrs["name"] == "terms_accepted"

    def test_checkboxx_id_sets_name(self):
        """Test CheckboxX sets name from ID if name not provided."""
        checkbox = CheckboxX(id="agreement")
        checkbox_input = checkbox[1]
        assert checkbox_input.attrs["id"] == "agreement"
        assert checkbox_input.attrs["name"] == "agreement"


class TestScriptAndStyleHelpers:
    """Test script and style helper functions."""

    def test_script_basic(self):
        """Test basic Script creation."""
        script = Script("console.log('hello');")
        html = str(script)
        assert "<script" in html
        assert "console.log('hello');" in html
        # Should not escape JavaScript
        assert "&gt;" not in html  # No HTML escaping

    def test_script_with_attributes(self):
        """Test Script with attributes."""
        script = Script("console.log('test');", type="module", _async=True)
        html = str(script)
        assert 'type="module"' in html
        assert "async" in html

    def test_style_basic(self):
        """Test basic Style creation."""
        style = Style("body { color: red; }")
        html = str(style)
        assert "<style" in html
        assert "body { color: red; }" in html
        # Should not escape CSS
        assert "&gt;" not in html

    def test_style_multiple_content(self):
        """Test Style with multiple content blocks."""
        style = Style("body { color: red; }", "p { margin: 0; }")
        html = str(style)
        assert "body { color: red; }" in html
        assert "p { margin: 0; }" in html

    def test_scriptx_file_read(self):
        """Test ScriptX reads from file."""
        # Create a temporary file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".js", delete=False) as f:
            f.write("console.log('from file');")
            temp_path = f.name

        try:
            script = ScriptX(temp_path)
            html = str(script)
            assert "console.log('from file');" in html
            assert "<script" in html
        finally:
            Path(temp_path).unlink()

    def test_scriptx_file_not_found(self):
        """Test ScriptX handles missing file."""
        script = ScriptX("nonexistent.js")
        html = str(script)
        assert "ScriptX Error: Could not load nonexistent.js" in html

    def test_scriptx_with_formatting(self):
        """Test ScriptX with string formatting."""
        # Create a temporary file with template
        with tempfile.NamedTemporaryFile(mode="w", suffix=".js", delete=False) as f:
            f.write("const message = '{message}';")
            temp_path = f.name

        try:
            script = ScriptX(temp_path, message="Hello World")
            html = str(script)
            assert "const message = 'Hello World';" in html
        finally:
            Path(temp_path).unlink()

    def test_scriptx_with_attributes(self):
        """Test ScriptX with script attributes."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".js", delete=False) as f:
            f.write("console.log('test');")
            temp_path = f.name

        try:
            script = ScriptX(temp_path, type="module", defer=True)
            html = str(script)
            assert 'type="module"' in html
            assert "defer" in html
        finally:
            Path(temp_path).unlink()

    def test_stylex_file_read(self):
        """Test StyleX reads from file."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".css", delete=False) as f:
            f.write("body { color: blue; }")
            temp_path = f.name

        try:
            style = StyleX(temp_path)
            html = str(style)
            assert "body { color: blue; }" in html
            assert "<style" in html
        finally:
            Path(temp_path).unlink()

    def test_stylex_file_not_found(self):
        """Test StyleX handles missing file."""
        style = StyleX("nonexistent.css")
        html = str(style)
        assert "StyleX Error: Could not load nonexistent.css" in html

    def test_stylex_with_css_vars(self):
        """Test StyleX with CSS variable replacement."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".css", delete=False) as f:
            f.write("body { color: var(--tpl-primary); background: var(--tpl-secondary); }")
            temp_path = f.name

        try:
            style = StyleX(temp_path, primary="red", secondary="blue")
            html = str(style)
            assert "color: red;" in html
            assert "background: blue;" in html
            assert "var(--tpl-" not in html  # Variables should be replaced
        finally:
            Path(temp_path).unlink()

    def test_stylex_with_attributes(self):
        """Test StyleX with style attributes."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".css", delete=False) as f:
            f.write("body { color: black; }")
            temp_path = f.name

        try:
            style = StyleX(temp_path, type="text/css", media="screen")
            html = str(style)
            assert 'type="text/css"' in html
            assert 'media="screen"' in html
        finally:
            Path(temp_path).unlink()

    def test_run_js_basic(self):
        """Test run_js basic functionality."""
        script = run_js("console.log({message});", message="Hello")
        assert script.children[0] == 'console.log("Hello");'
        assert script.tag == "script"

    def test_run_js_with_id(self):
        """Test run_js with custom ID."""
        script = run_js("console.log('test');", id="custom_script")
        assert script.attrs["id"] == "custom_script"

    def test_run_js_auto_id(self):
        """Test run_js generates ID from caller function."""
        # This test verifies the ID generation behavior
        script = run_js("console.log('auto');")
        # Should have an ID (from test function name)
        assert "id" in script.attrs
        assert script.attrs["id"] == "test_run_js_auto_id"

    def test_run_js_json_escaping(self):
        """Test run_js properly JSON-escapes parameters."""
        script = run_js("console.log({data});", data={"key": "value"})
        assert '{"key": "value"}' in script.children[0]

    def test_jsd_script_tag(self):
        """Test jsd creates script tag."""
        script = jsd("org", "repo", "dist", "script.js")
        html = str(script)
        assert "<script" in html
        assert 'src="https://cdn.jsdelivr.net/gh/org/repo/dist/script.js"' in html

    def test_jsd_css_link(self):
        """Test jsd creates CSS link."""
        link = jsd("org", "repo", "dist", "style.css", typ="css")
        html = str(link)
        assert "<link" in html
        assert 'rel="stylesheet"' in html
        assert 'href="https://cdn.jsdelivr.net/gh/org/repo/dist/style.css"' in html

    def test_jsd_url_only(self):
        """Test jsd returns URL string."""
        url = jsd("org", "repo", "dist", "file.js", typ="url")
        assert isinstance(url, str)
        assert url == "https://cdn.jsdelivr.net/gh/org/repo/dist/file.js"

    def test_jsd_with_version(self):
        """Test jsd with version parameter."""
        script = jsd("org", "repo", "dist", "script.js", ver="1.0.0")
        html = str(script)
        assert "repo@1.0.0" in html

    def test_jsd_esm_module(self):
        """Test jsd with ESM module."""
        script = jsd("org", "repo", "dist", "module.js", esm=True)
        html = str(script)
        assert "/+esm" in html

    def test_jsd_with_attributes(self):
        """Test jsd with additional attributes."""
        script = jsd("org", "repo", "dist", "script.js", defer=True, integrity="sha256-xyz")
        html = str(script)
        assert "defer" in html
        assert 'integrity="sha256-xyz"' in html


class TestSEOComponents:
    """Test SEO and social media components."""

    def test_socials_basic(self):
        """Test basic Socials generation."""
        socials = Socials(title="Test Page", site_name="Test Site", description="Test description", image="/image.png")

        # Should return tuple of meta tags
        assert isinstance(socials, tuple)
        assert len(socials) >= 10  # Should have multiple meta tags

        # Convert to HTML and check content
        html_parts = [str(tag) for tag in socials]
        html = "\n".join(html_parts)

        assert 'property="og:title" content="Test Page"' in html
        assert 'property="og:description" content="Test description"' in html
        assert 'property="og:site_name" content="Test Site"' in html
        assert 'name="twitter:title" content="Test Page"' in html

    def test_socials_with_url(self):
        """Test Socials with custom URL."""
        socials = Socials(
            title="Test", site_name="example.com", description="Test", image="/image.png", url="https://custom.com"
        )

        html = "\n".join(str(tag) for tag in socials)
        assert 'property="og:url" content="https://custom.com"' in html
        assert "https://custom.com/image.png" in html  # Image should be absolute

    def test_socials_url_normalization(self):
        """Test Socials URL normalization."""
        socials = Socials(
            title="Test",
            site_name="example.com",  # No https://
            description="Test",
            image="/image.png",
        )

        html = "\n".join(str(tag) for tag in socials)
        assert 'content="https://example.com"' in html
        assert "https://example.com/image.png" in html

    def test_socials_with_twitter_options(self):
        """Test Socials with Twitter-specific options."""
        socials = Socials(
            title="Test",
            site_name="example.com",
            description="Test",
            image="/image.png",
            twitter_site="@site",
            creator="@creator",
            card="summary_large_image",
        )

        html = "\n".join(str(tag) for tag in socials)
        assert 'name="twitter:site" content="@site"' in html
        assert 'name="twitter:creator" content="@creator"' in html
        assert 'name="twitter:card" content="summary_large_image"' in html

    def test_socials_image_dimensions(self):
        """Test Socials with custom image dimensions."""
        socials = Socials(title="Test", site_name="example.com", description="Test", image="/image.png", w=800, h=400)

        html = "\n".join(str(tag) for tag in socials)
        assert 'property="og:image:width" content="800"' in html
        assert 'property="og:image:height" content="400"' in html

    def test_favicon_light_dark(self):
        """Test Favicon with light and dark icons."""
        favicons = Favicon("/light.ico", "/dark.ico")

        assert isinstance(favicons, tuple)
        assert len(favicons) == 2

        light_html = str(favicons[0])
        dark_html = str(favicons[1])

        assert 'href="/light.ico"' in light_html
        assert 'media="(prefers-color-scheme: light)"' in light_html
        assert 'href="/dark.ico"' in dark_html
        assert 'media="(prefers-color-scheme: dark)"' in dark_html

    def test_youtube_embed_basic(self):
        """Test basic YouTube embed."""
        embed = YouTubeEmbed("dQw4w9WgXcQ")
        html = str(embed)

        assert "<iframe" in html
        assert 'src="https://www.youtube.com/embed/dQw4w9WgXcQ"' in html
        assert 'width="560"' in html
        assert 'height="315"' in html
        assert "allowfullscreen" in html

    def test_youtube_embed_with_options(self):
        """Test YouTube embed with options."""
        embed = YouTubeEmbed(
            "dQw4w9WgXcQ", width=800, height=450, start_time=30, no_controls=True, title="Custom title"
        )
        html = str(embed)

        assert 'width="800"' in html
        assert 'height="450"' in html
        assert "start=30" in html
        assert "controls=0" in html
        assert 'title="Custom title"' in html

    def test_youtube_embed_invalid_video_id(self):
        """Test YouTube embed with invalid video ID."""
        with pytest.raises(ValueError, match="valid YouTube video ID"):
            YouTubeEmbed("")

        with pytest.raises(ValueError, match="valid YouTube video ID"):
            YouTubeEmbed(None)

    def test_youtube_embed_with_class(self):
        """Test YouTube embed with CSS class."""
        embed = YouTubeEmbed("dQw4w9WgXcQ", cls="video-wrapper")
        html = str(embed)

        assert 'class="video-wrapper"' in html
        assert "<div" in html  # Should be wrapped in div

    def test_nbsp_entity(self):
        """Test Nbsp creates non-breaking space entity."""
        nbsp = Nbsp()
        assert isinstance(nbsp, Safe)
        assert str(nbsp) == "&nbsp;"


class TestStringUtilities:
    """Test string formatting and processing utilities."""

    def test_double_braces_basic(self):
        """Test double_braces basic functionality."""
        result = double_braces("{ color: red; }")
        assert result == "{{ color: red; }}"

    def test_double_braces_with_special_chars(self):
        """Test double_braces with special characters."""
        result = double_braces("{ margin: 0; } body { padding: 0; }")
        assert "{{" in result
        assert "}}" in result

    def test_double_braces_preserves_template_vars(self):
        """Test double_braces preserves template variables."""
        result = double_braces("color: {color}; margin: { 0; }")
        # Template vars should not be doubled
        assert "{color}" in result
        # CSS braces should be doubled
        assert "{{ 0; }}" in result

    def test_undouble_braces_basic(self):
        """Test undouble_braces basic functionality."""
        result = undouble_braces("{{ color: red; }}")
        assert result == "{ color: red; }"

    def test_undouble_braces_preserves_singles(self):
        """Test undouble_braces preserves single braces."""
        result = undouble_braces("color: {color}; margin: {{ 0; }}")
        assert "{color}" in result
        assert "{ 0; }" in result

    def test_brace_roundtrip(self):
        """Test double_braces and undouble_braces roundtrip."""
        original = "{ margin: 0; } .class { padding: {spacing}; }"
        doubled = double_braces(original)
        undoubled = undouble_braces(doubled)
        assert undoubled == original

    def test_loose_format_basic(self):
        """Test loose_format basic functionality."""
        template = "Hello {name}, welcome to {site}!"
        result = loose_format(template, name="John", site="our site")
        assert result == "Hello John, welcome to our site!"

    def test_loose_format_with_css(self):
        """Test loose_format with CSS-like content."""
        template = ".class { color: {color}; margin: { 0; } }"
        result = loose_format(template, color="red")
        assert result == ".class { color: red; margin: { 0; } }"

    def test_loose_format_no_variables(self):
        """Test loose_format with no variables."""
        template = "No variables here"
        result = loose_format(template)
        assert result == template

    def test_loose_format_missing_variables(self):
        """Test loose_format with missing variables."""
        template = "Hello {name}, today is {day}"
        result = loose_format(template, name="John")
        # Missing variables should remain as placeholders
        assert "Hello John" in result
        assert "{day}" in result

    def test_replace_css_vars_basic(self):
        """Test replace_css_vars basic functionality."""
        css = "color: var(--tpl-primary); background: var(--tpl-secondary);"
        result = replace_css_vars(css, primary="red", secondary="blue")
        assert result == "color: red; background: blue;"

    def test_replace_css_vars_custom_prefix(self):
        """Test replace_css_vars with custom prefix."""
        css = "color: var(--custom_theme-color);"
        result = replace_css_vars(css, pre="custom_theme", color="green")
        assert result == "color: green;"

    def test_replace_css_vars_hyphen_underscore(self):
        """Test replace_css_vars handles hyphen to underscore conversion."""
        css = "font-size: var(--tpl-font-size);"
        result = replace_css_vars(css, font_size="16px")
        assert result == "font-size: 16px;"

    def test_replace_css_vars_no_match(self):
        """Test replace_css_vars leaves unmatched variables."""
        css = "color: var(--tpl-primary); background: var(--other-secondary);"
        result = replace_css_vars(css, primary="red")
        assert "color: red;" in result
        assert "var(--other-secondary)" in result  # Should remain unchanged

    def test_replace_css_vars_no_kwargs(self):
        """Test replace_css_vars with no replacement variables."""
        css = "color: var(--tpl-primary);"
        result = replace_css_vars(css)
        assert result == css  # Should remain unchanged


class TestEdgeCases:
    """Test edge cases and error conditions."""

    def test_empty_string_handling(self):
        """Test functions handle empty strings gracefully."""
        assert double_braces("") == ""
        assert undouble_braces("") == ""
        assert loose_format("") == ""
        assert replace_css_vars("") == ""

    def test_none_value_handling(self):
        """Test components handle None values appropriately."""
        # Most components should handle None gracefully
        hidden = Hidden(None)
        # None value should not add value attribute
        assert "value" not in hidden.attrs or hidden.attrs.get("value") is None

    def test_complex_nesting(self):
        """Test complex component nesting."""
        form = Form(
            Hidden("csrf_token", id="csrf"),
            CheckboxX(label="I agree", id="terms")[1],  # Get checkbox part
            A("Submit", get="/submit"),
        )
        html = str(form)
        assert 'type="hidden"' in html
        assert 'type="checkbox"' in html
        assert "data-on-click" in html
        assert "<form" in html

    def test_unicode_content(self):
        """Test components handle Unicode content."""
        script = Script("console.log('Hello 世界');")
        html = str(script)
        assert "世界" in html

        style = Style("/* 测试 */ body { content: '🚀'; }")
        html = str(style)
        assert "测试" in html
        assert "🚀" in html

    def test_special_character_escaping(self):
        """Test proper escaping of special characters."""
        # HTML attributes should be escaped
        link = A("Test", href='javascript:alert("xss")')
        html = str(link)
        assert "&quot;" in html or '"' in html  # Quotes should be handled

        # Script content should not be HTML escaped
        script = Script('console.log("test");')
        html = str(script)
        assert 'console.log("test");' in html
        assert "&quot;" not in html
