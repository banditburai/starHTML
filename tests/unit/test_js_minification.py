"""
Behavior tests for JavaScript minification in js() and Script().

Tests verify that minification works correctly without testing implementation details.
"""

from starhtml.datastar import js
from starhtml.xtend import Script


class TestJsMinification:
    """Test js() minifies JavaScript while preserving functionality"""

    def test_js_reduces_code_size(self):
        """Minification should reduce code size"""
        code = """
            const x = 1;
            const y = 2;
            return x + y;
        """
        result = js(code).to_js()
        assert len(result) < len(code)

    def test_js_removes_comments(self):
        """Comments should be removed during minification"""
        result = js("const x = 1; // comment").to_js()
        assert "//" not in result
        assert "x" in result

    def test_js_removes_multiline_comments(self):
        """Multi-line comments should be removed"""
        result = js("const x = 1; /* comment */ const y = 2;").to_js()
        assert "/*" not in result
        assert "*/" not in result
        assert "x" in result
        assert "y" in result

    def test_js_preserves_string_content(self):
        """String content must be preserved exactly"""
        result = js("const msg = 'Hello World';").to_js()
        assert "Hello World" in result

    def test_js_preserves_template_literals(self):
        """Template literal syntax must be preserved"""
        result = js("const html = `<div>Content</div>`;").to_js()
        assert "`" in result
        assert "Content" in result

    def test_js_works_with_f_strings(self):
        """js() should work with Python f-string interpolation"""
        theme = "dark"
        result = js(f"const theme = '{theme}';").to_js()
        assert "dark" in result
        assert "theme" in result

    def test_js_handles_empty_string(self):
        """Empty strings should be handled gracefully"""
        result = js("").to_js()
        assert result == ""

    def test_js_preserves_regex_literals(self):
        """Regex literals must be preserved"""
        result = js("const pattern = /test/g;").to_js()
        assert "/test/" in result
        assert "pattern" in result

    def test_js_preserves_unicode(self):
        """Unicode characters must be preserved"""
        result = js("const emoji = '🚀';").to_js()
        assert "🚀" in result


class TestScriptMinification:
    """Test Script() component minifies JavaScript"""

    def test_script_reduces_code_size(self):
        """Script should minify its content"""
        code = """
            window.init = function() {
                console.log('test');
            };
        """
        result = str(Script(code))
        # Should be smaller than unminified version
        assert len(result) < len(f"<script>{code}</script>")
        assert "init" in result
        assert "console.log" in result

    def test_script_with_empty_code(self):
        """Script with empty code should work"""
        result = str(Script(""))
        assert "<script></script>" in result

    def test_script_with_src_attribute(self):
        """Script with src attribute should not need minification"""
        result = str(Script(src="/app.js"))
        assert 'src="/app.js"' in result
        assert "<script" in result

    def test_script_preserves_functionality(self):
        """Minified script should preserve variable names and logic"""
        code = "const config = { debug: true };"
        result = str(Script(code))
        assert "config" in result
        assert "debug" in result
        assert "true" in result


class TestMinificationIntegration:
    """Test that js() and Script() work consistently"""

    def test_js_and_script_both_minify(self):
        """Both js() and Script() should minify code"""
        code = "const x = 1;  const y = 2;"
        js_result = js(code).to_js()
        script_result = str(Script(code))

        # Both should reduce size
        assert len(js_result) < len(code)
        assert len(script_result) < len(f"<script>{code}</script>")

        # Both should preserve variables
        assert "x" in js_result
        assert "y" in js_result
        assert "x" in script_result
        assert "y" in script_result
