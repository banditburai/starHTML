"""Test explicit wrapper functions for ds_signals."""

import json
import unittest

from starhtml.datastar import ds_signals, js, value


class TestDSSignalsWrappers(unittest.TestCase):
    """Test the value() and js() wrapper functions for ds_signals."""

    def test_value_string_literal(self):
        """Test value() wrapper for simple string literals."""
        result = ds_signals(tab=value("preview"))
        self.assertEqual(result.attrs["data-signals-tab"], '"preview"')

    def test_value_multiline_string(self):
        """Test value() wrapper properly handles multiline strings."""
        code = """def hello():
    print("Hello, World!")
    return 42"""
        result = ds_signals(content=value(code))
        # Should be JSON-encoded for JavaScript execution
        expected = json.dumps(code)
        self.assertEqual(result.attrs["data-signals-content"], expected)

    def test_value_string_with_quotes(self):
        """Test value() wrapper handles strings with quotes."""
        result = ds_signals(message=value('She said "Hello"'))
        # Should be JSON-encoded for JavaScript execution
        expected = json.dumps('She said "Hello"')
        self.assertEqual(result.attrs["data-signals-message"], expected)

    def test_value_dollar_strings_are_literals(self):
        """Test value() treats dollar-prefixed strings as literals, not expressions."""
        # This removes the confusing $ prefix detection
        result = ds_signals(price=value("$10.99 special"))
        # Should be JSON-encoded for JavaScript execution
        expected = json.dumps("$10.99 special")
        self.assertEqual(result.attrs["data-signals-price"], expected)

    def test_js_datastar_signal(self):
        """Test js() wrapper for Datastar signal references."""
        # Use js() explicitly for Datastar signals
        result = ds_signals(computed=js("$count + 1"))
        self.assertEqual(result.attrs["data-signals-computed"], "$count + 1")

    def test_js_property_access(self):
        """Test js() wrapper for property access expressions."""
        result = ds_signals(name=js("user.firstName"))
        self.assertEqual(result.attrs["data-signals-name"], "user.firstName")

    def test_js_complex_expression(self):
        """Test js() wrapper for complex expressions."""
        expression = "$items.filter(i => i.active).length > 0"
        result = ds_signals(hasActive=js(expression))
        self.assertEqual(result.attrs["data-signals-hasActive"], expression)

    def test_auto_wrap_primitives(self):
        """Test that primitives are auto-wrapped as literals."""
        result = ds_signals(count=42, active=True, inactive=False, data=None)
        self.assertEqual(result.attrs["data-signals-count"], "42")
        self.assertEqual(result.attrs["data-signals-active"], "true")
        self.assertEqual(result.attrs["data-signals-inactive"], "false")
        self.assertEqual(result.attrs["data-signals-data"], "null")

    def test_complex_types_need_wrapper(self):
        """Test that lists and dicts need explicit value() wrapper."""
        result = ds_signals(items=value([1, 2, 3]), config=value({"theme": "dark", "lang": "en"}))
        self.assertEqual(result.attrs["data-signals-items"], "[1, 2, 3]")
        self.assertEqual(result.attrs["data-signals-config"], '{"theme": "dark", "lang": "en"}')

    def test_mixed_wrappers(self):
        """Test mixing value(), js(), and auto-wrapped primitives."""
        multiline = """function test() {
    return "hello";
}"""
        result = ds_signals(
            # Explicit value wrapper for strings
            code=value(multiline),
            label=value("Total: $"),
            currency=value("USD"),
            # Explicit js wrapper
            amount=js("$price * $quantity"),
            userName=js("$user.name || 'Anonymous'"),
            # Auto-wrapped primitives (unambiguous)
            taxRate=0.08,
            includeTax=True,
        )

        # Check value-wrapped strings are JSON-encoded
        self.assertEqual(result.attrs["data-signals-code"], json.dumps(multiline))
        self.assertEqual(result.attrs["data-signals-label"], '"Total: $"')
        self.assertEqual(result.attrs["data-signals-currency"], '"USD"')

        # Check js-wrapped values are unchanged
        self.assertEqual(result.attrs["data-signals-amount"], "$price * $quantity")
        self.assertEqual(result.attrs["data-signals-userName"], "$user.name || 'Anonymous'")

        # Check auto-wrapped primitives
        self.assertEqual(result.attrs["data-signals-taxRate"], "0.08")
        self.assertEqual(result.attrs["data-signals-includeTax"], "true")

    def test_no_dollar_prefix_confusion(self):
        """Test that $ prefix has no special meaning - must use js() for expressions."""
        # Strings must use value() wrapper explicitly
        result = ds_signals(
            signal=value("$activeTab"),  # String literal with value()
            computed=value("$items.length"),  # String literal with value()
            template=value("`Hello ${name}`"),  # String literal with value()
        )
        # All should be JSON-encoded string literals
        self.assertEqual(result.attrs["data-signals-signal"], '"$activeTab"')
        self.assertEqual(result.attrs["data-signals-computed"], '"$items.length"')
        self.assertEqual(result.attrs["data-signals-template"], '"`Hello ${name}`"')

        # To make them expressions, must use js() explicitly
        result2 = ds_signals(signal=js("$activeTab"), computed=js("$items.length"), template=js("`Hello ${name}`"))
        # Now they're expressions
        self.assertEqual(result2.attrs["data-signals-signal"], "$activeTab")
        self.assertEqual(result2.attrs["data-signals-computed"], "$items.length")
        self.assertEqual(result2.attrs["data-signals-template"], "`Hello ${name}`")

    def test_strings_require_explicit_wrapper(self):
        """Test that bare strings without wrapper raise TypeError."""
        with self.assertRaises(TypeError) as ctx:
            ds_signals(bad="plain string")
        self.assertIn("Strings must use explicit", str(ctx.exception))

    def test_empty_string(self):
        """Test empty strings are handled correctly."""
        result = ds_signals(
            empty1=value(""),
            empty2=value(""),  # Must use explicit wrapper
        )
        self.assertEqual(result.attrs["data-signals-empty1"], '""')
        self.assertEqual(result.attrs["data-signals-empty2"], '""')

    def test_unicode_and_special_chars(self):
        """Test Unicode and special characters are handled."""
        special = "Hello 👋 \t\r\n\\ \"quotes\" 'apostrophe'"
        result = ds_signals(text=value(special))
        # Should be JSON-encoded for JavaScript execution
        expected = json.dumps(special)
        self.assertEqual(result.attrs["data-signals-text"], expected)

    def test_very_long_multiline_content(self):
        """Test handling of realistic multiline code content."""
        code = """from starhtml import *
from starhtml.datastar import value, js, ds_signals

def create_tabs(tabs_data):
    \"\"\"Create a tabbed interface with Datastar signals.\"\"\"
    
    # Initialize with default tab
    default_tab = tabs_data[0]["id"]
    
    return Div(
        # Set up signals for tab state
        ds_signals(
            activeTab=value(default_tab),
            tabCount=len(tabs_data)
        ),
        
        # Tab headers
        Div(
            *[
                Button(
                    tab["label"],
                    ds_on_click(expr(f"$activeTab = '{tab['id']}'")),
                    ds_class(active=js(f"$activeTab === '{tab['id']}'"))
                )
                for tab in tabs_data
            ],
            cls="tab-headers"
        ),
        
        # Tab content
        Div(
            *[
                Div(
                    tab["content"],
                    ds_show(expr(f"$activeTab === '{tab['id']}'")),
                    cls="tab-panel"
                )
                for tab in tabs_data
            ],
            cls="tab-content"
        )
    )"""

        result = ds_signals(example_code=value(code))
        # Should be JSON-encoded for JavaScript execution
        expected = json.dumps(code)
        self.assertEqual(result.attrs["data-signals-example_code"], expected)

    def test_dynamic_signal_names(self):
        """Test that dynamic signal names work with individual attributes."""
        signal_name = "tabs_1"
        result = ds_signals(**{signal_name: value("account")})
        # Individual attributes handle dynamic names perfectly
        self.assertEqual(result.attrs["data-signals-tabs_1"], '"account"')

        # Multiple dynamic names
        result2 = ds_signals(**{"user_id": 123, "session_token": value("xyz789")})
        self.assertEqual(result2.attrs["data-signals-user_id"], "123")
        self.assertEqual(result2.attrs["data-signals-session_token"], '"xyz789"')

    def test_json_object_format_basic(self):
        """Test JSON object format when dict is passed as first argument."""
        result = ds_signals({"name": value("Alice"), "age": 25, "active": True})
        expected_json = '{"name": "Alice", "age": 25, "active": true}'
        self.assertEqual(result.attrs["data-signals"], expected_json)

    def test_json_object_format_with_js(self):
        """Test JSON object format with JavaScript expressions."""
        result = ds_signals({"count": 0, "doubled": js("$count * 2")})
        expected_json = '{"count": 0, "doubled": "$count * 2"}'
        self.assertEqual(result.attrs["data-signals"], expected_json)

    def test_json_object_format_bulk_data(self):
        """Test JSON object format for bulk initialization."""
        user_data = {
            "user_id": 123,
            "username": value("alice"),
            "email": value("alice@example.com"),
            "role": value("admin"),
            "active": True,
            "login_count": 0,
        }
        result = ds_signals(user_data)
        expected_json = '{"user_id": 123, "username": "alice", "email": "alice@example.com", "role": "admin", "active": true, "login_count": 0}'
        self.assertEqual(result.attrs["data-signals"], expected_json)

    def test_json_vs_individual_format_choice(self):
        """Test that format is determined by whether first arg is dict."""
        # Dict as first arg -> JSON format
        json_result = ds_signals({"name": value("Bob"), "score": 42})
        self.assertIn("data-signals", json_result.attrs)
        self.assertNotIn("data-signals-name", json_result.attrs)

        # Kwargs -> Individual attributes
        attr_result = ds_signals(name=value("Bob"), score=42)
        self.assertIn("data-signals-name", attr_result.attrs)
        self.assertIn("data-signals-score", attr_result.attrs)
        self.assertNotIn("data-signals", attr_result.attrs)

        # Dict unpacking -> Individual attributes (not JSON)
        unpacked_result = ds_signals(**{"name": value("Bob"), "score": 42})
        self.assertIn("data-signals-name", unpacked_result.attrs)
        self.assertIn("data-signals-score", unpacked_result.attrs)
        self.assertNotIn("data-signals", unpacked_result.attrs)

    def test_json_format_with_complex_values(self):
        """Test JSON format handles complex values properly."""
        result = ds_signals(
            {
                "items": value([1, 2, 3]),
                "config": value({"theme": "dark", "lang": "en"}),
                "multiline": value("line1\nline2\nline3"),
                "special": value('Hello 👋 "quotes"'),
            }
        )
        # Parse the JSON to verify structure
        import json as json_module

        parsed = json_module.loads(result.attrs["data-signals"])
        self.assertEqual(parsed["items"], [1, 2, 3])
        self.assertEqual(parsed["config"], {"theme": "dark", "lang": "en"})
        self.assertEqual(parsed["multiline"], "line1\nline2\nline3")
        self.assertEqual(parsed["special"], 'Hello 👋 "quotes"')


if __name__ == "__main__":
    unittest.main()
