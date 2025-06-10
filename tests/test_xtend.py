"""Tests for StarHTML xtend module functionality"""

import tempfile
from pathlib import Path
from unittest.mock import Mock

import pytest

from starhtml.xtend import (
    AX,
    A,
    CheckboxX,
    DatastarOn,
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
    with_sid,
)


class TestAnchorComponents:
    def test_a_basic(self):
        """Test basic A tag creation"""
        result = A("Click me")
        assert result.tag == "a"
        assert result.attrs["href"] == "#"
        assert "Click me" in result.children

    def test_a_with_get(self):
        """Test A tag with get parameter"""
        result = A("Submit", get="/submit")
        assert result.attrs["data-on-click"] == "@get('/submit')"

    def test_ax_basic(self):
        """Test AX tag creation"""
        result = AX("Click me")
        assert result.tag == "a"
        assert result.attrs["href"] == "#"
        assert "Click me" in result.children

    def test_ax_with_get(self):
        """Test AX tag with get parameter"""
        result = AX("Submit", get="/submit")
        assert result.attrs["data-on-click"] == "@get('/submit')"


class TestFormComponents:
    def test_form_basic(self):
        """Test basic Form creation"""
        result = Form("Content")
        assert result.tag == "form"
        assert result.attrs["enctype"] == "multipart/form-data"

    def test_hidden_basic(self):
        """Test Hidden input creation"""
        result = Hidden(value="secret")
        assert result.tag == "input"
        assert result.attrs["type"] == "hidden"
        assert result.attrs["value"] == "secret"

    def test_checkbox_x_basic(self):
        """Test CheckboxX creation"""
        hidden, checkbox = CheckboxX(name="agree")
        assert hidden.attrs["name"] == "agree"
        assert hidden.attrs["type"] == "hidden"
        assert checkbox.attrs["name"] == "agree"
        assert checkbox.attrs["type"] == "checkbox"

    def test_checkbox_x_with_label(self):
        """Test CheckboxX with label"""
        hidden, checkbox_with_label = CheckboxX(name="agree", label="I agree")
        assert checkbox_with_label.tag == "label"
        assert "I agree" in checkbox_with_label.children

    def test_checkbox_x_checked(self):
        """Test CheckboxX when checked"""
        hidden, checkbox = CheckboxX(name="agree", checked=True)
        assert checkbox.attrs.get("checked")


class TestScriptAndStyle:
    def test_script_basic(self):
        """Test Script tag creation"""
        result = Script('console.log("hello")')
        assert result.tag == "script"

    def test_style_basic(self):
        """Test Style tag creation"""
        result = Style("body { color: red; }")
        assert result.tag == "style"

    def test_script_x(self):
        """Test ScriptX reading from file"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".js", delete=False) as f:
            f.write('console.log("test");')
            temp_path = f.name

        try:
            result = ScriptX(temp_path)
            assert result.tag == "script"
        finally:
            Path(temp_path).unlink()

    def test_style_x(self):
        """Test StyleX reading from file"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".css", delete=False) as f:
            f.write("body { color: var(--tpl-main-color); }")
            temp_path = f.name

        try:
            result = StyleX(temp_path, main_color="blue")
            assert result.tag == "style"
        finally:
            Path(temp_path).unlink()


class TestStringUtilities:
    def test_double_braces(self):
        """Test double_braces function"""
        assert double_braces("{ color: red; }") == "{{ color: red; }}"
        assert double_braces("margin: 0;") == "margin: 0;"

    def test_undouble_braces(self):
        """Test undouble_braces function"""
        assert undouble_braces("{{ color: red; }}") == "{ color: red; }"
        assert undouble_braces("margin: 0;") == "margin: 0;"

    def test_loose_format(self):
        """Test loose_format function"""
        template = "Hello {name}, { color: red; }"
        result = loose_format(template, name="World")
        assert "Hello World" in result
        assert "{ color: red; }" in result

    def test_loose_format_no_kwargs(self):
        """Test loose_format with no kwargs"""
        template = "Hello {name}"
        result = loose_format(template)
        assert result == template

    def test_replace_css_vars(self):
        """Test replace_css_vars function"""
        css = "color: var(--tpl-main-color); background: var(--tpl-bg-color);"
        result = replace_css_vars(css, main_color="blue", bg_color="white")
        assert "color: blue;" in result
        assert "background: white;" in result

    def test_replace_css_vars_no_kwargs(self):
        """Test replace_css_vars with no kwargs"""
        css = "color: var(--tpl-main-color);"
        result = replace_css_vars(css)
        assert result == css


class TestUtilityComponents:
    def test_nbsp(self):
        """Test Nbsp function"""
        result = Nbsp()
        assert str(result) == "&nbsp;"

    def test_run_js(self):
        """Test run_js function"""
        result = run_js("console.log({message});", message="hello")
        assert result.tag == "script"
        # The run_js function formats the script content
        script_content = result.children[0] if result.children else ""
        assert '"hello"' in str(script_content)

    def test_datastar_on(self):
        """Test DatastarOn function"""
        result = DatastarOn("click", 'console.log("clicked");')
        assert result.tag == "script"
        assert "datastar:click" in str(result)

    def test_jsd_script(self):
        """Test jsd function for script"""
        result = jsd("jquery", "jquery", "dist", "jquery.min.js", ver="3.6.0")
        assert result.tag == "script"
        assert "cdn.jsdelivr.net" in result.attrs["src"]
        assert "jquery@3.6.0" in result.attrs["src"]

    def test_jsd_css(self):
        """Test jsd function for CSS"""
        result = jsd("bootstrap", "bootstrap", "dist/css", "bootstrap.min.css", typ="css")
        assert result.tag == "link"
        assert result.attrs["rel"] == "stylesheet"

    def test_jsd_url_only(self):
        """Test jsd function returning URL only"""
        result = jsd("jquery", "jquery", "dist", "jquery.min.js", typ="url")
        assert isinstance(result, str)
        assert "cdn.jsdelivr.net" in result

    def test_fragment(self):
        """Test Fragment component"""
        result = Fragment("content1", "content2")
        assert result.tag == ""
        assert result.void_
        assert len(result.children) == 2


class TestSocialComponents:
    def test_socials_basic(self):
        """Test Socials function"""
        result = Socials(title="Test Page", site_name="Test Site", description="Test description", image="/test.png")
        assert isinstance(result, tuple)
        assert len(result) > 10  # Should have multiple meta tags

        # Check that we have OG tags
        og_tags = [tag for tag in result if tag.attrs.get("property", "").startswith("og:")]
        assert len(og_tags) > 0

        # Check that we have Twitter tags
        twitter_tags = [tag for tag in result if tag.attrs.get("name", "").startswith("twitter:")]
        assert len(twitter_tags) > 0

    def test_socials_with_optional_params(self):
        """Test Socials with optional parameters"""
        result = Socials(
            title="Test Page",
            site_name="Test Site",
            description="Test description",
            image="/test.png",
            twitter_site="@testsite",
            creator="@creator",
        )
        # Should have additional twitter tags
        twitter_site_tags = [tag for tag in result if tag.attrs.get("name") == "twitter:site"]
        assert len(twitter_site_tags) == 1

    def test_youtube_embed_basic(self):
        """Test YouTubeEmbed function"""
        result = YouTubeEmbed("dQw4w9WgXcQ")
        assert result.tag == "div"
        # Should contain an iframe
        iframe = next((child for child in result.children if hasattr(child, "tag") and child.tag == "iframe"), None)
        assert iframe is not None
        assert "youtube.com/embed" in iframe.attrs["src"]

    def test_youtube_embed_with_params(self):
        """Test YouTubeEmbed with parameters"""
        result = YouTubeEmbed("dQw4w9WgXcQ", start_time=30, no_controls=True)
        iframe = next((child for child in result.children if hasattr(child, "tag") and child.tag == "iframe"), None)
        assert "start=30" in iframe.attrs["src"]
        assert "controls=0" in iframe.attrs["src"]

    def test_youtube_embed_invalid_id(self):
        """Test YouTubeEmbed with invalid video ID"""
        with pytest.raises(ValueError):
            YouTubeEmbed("")

        with pytest.raises(ValueError):
            YouTubeEmbed(123)  # Non-string

    def test_favicon(self):
        """Test Favicon function"""
        light_icon, dark_icon = Favicon("/light.ico", "/dark.ico")
        assert light_icon.tag == "link"
        assert dark_icon.tag == "link"
        assert light_icon.attrs["href"] == "/light.ico"
        assert dark_icon.attrs["href"] == "/dark.ico"
        assert "light" in light_icon.attrs["media"]
        assert "dark" in dark_icon.attrs["media"]


class TestWithSid:
    def test_with_sid(self):
        """Test with_sid function"""
        # Create a mock app object
        app = Mock()
        app.route = Mock()

        # Call with_sid
        with_sid(app, "/destination", "/path")

        # Verify route was called
        app.route.assert_called_once_with("/path")
