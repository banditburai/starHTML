"""Test data_signals attribute and signal initialization in new API."""

import unittest

from starhtml import Div, P
from starhtml.datastar import Signal, build_data_signals, f, js


class TestDataSignalsAttribute(unittest.TestCase):
    """Test the data_signals attribute for signal initialization."""

    def test_signal_with_string_literal(self):
        """Test Signal initialization with string literals."""
        sig = Signal("tab", "preview")
        self.assertEqual(sig.name, "tab")
        self.assertEqual(sig.value, "preview")
        # When used in data_signals, it creates proper initialization
        div = Div(data_signals=[sig])
        html = str(div)
        self.assertIn("data-signals", html)
        self.assertIn('tab: "preview"', html)

    def test_signal_with_multiline_string(self):
        """Test Signal properly handles multiline strings."""
        code = """def hello():
    print("Hello, World!")
    return 42"""
        sig = Signal("content", code)
        self.assertEqual(sig.value, code)
        # When used in data_signals, it's properly JSON-encoded
        div = Div(data_signals=[sig])
        html = str(div)
        self.assertIn("data-signals", html)
        # Check that multiline string is properly escaped in HTML
        self.assertIn("def hello", html)

    def test_signal_with_quotes(self):
        """Test Signal handles strings with quotes."""
        text = 'She said "Hello"'
        sig = Signal("message", text)
        self.assertEqual(sig.value, text)
        # When used in data_signals
        div = Div(data_signals=[sig])
        html = str(div)
        self.assertIn("data-signals", html)

    def test_signal_with_dollar_prefix(self):
        """Test Signal with dollar-prefixed strings as literals."""
        sig = Signal("price", "$10.99 special")
        self.assertEqual(sig.value, "$10.99 special")
        # When used in data_signals
        div = Div(data_signals=[sig])
        html = str(div)
        self.assertIn("data-signals", html)
        self.assertIn("$10.99 special", html)

    def test_signal_with_js_expression(self):
        """Test Signal with JavaScript expressions using js()."""
        # Signals can have js expressions as initial values
        sig = Signal("computed", js("$count + 1"))
        # The js() expression is stored as the value
        # js() expressions create PropertyAccess objects
        self.assertEqual(type(sig.value).__name__, "PropertyAccess")
        # When stringified, they show as $signal_name.value
        self.assertIn("$computed", str(sig.value))

    def test_signal_property_access(self):
        """Test Signal with property access expressions."""
        sig = Signal("name", js("user.firstName"))
        # js() expressions create PropertyAccess objects
        self.assertEqual(type(sig.value).__name__, "PropertyAccess")
        # When stringified, they show as $signal_name.value
        self.assertIn("$name", str(sig.value))

    def test_signal_complex_expression(self):
        """Test Signal with complex JavaScript expressions."""
        expression = "$items.filter(i => i.active).length > 0"
        sig = Signal("has_active", js(expression))
        # js() expressions create PropertyAccess objects
        self.assertEqual(type(sig.value).__name__, "PropertyAccess")
        # When stringified, they show as $signal_name.value
        self.assertIn("$has_active", str(sig.value))

    def test_signal_with_primitives(self):
        """Test Signal with primitive types."""
        count_sig = Signal("count", 42)
        active_sig = Signal("active", True)
        inactive_sig = Signal("inactive", False)
        data_sig = Signal("data", None)

        self.assertEqual(count_sig.value, 42)
        self.assertEqual(active_sig.value, True)
        self.assertEqual(inactive_sig.value, False)
        self.assertEqual(data_sig.value, None)

        # When used in data_signals
        div = Div(data_signals=[count_sig, active_sig, inactive_sig, data_sig])
        html = str(div)
        self.assertIn("count: 42", html)
        self.assertIn("active: true", html)
        self.assertIn("inactive: false", html)
        self.assertIn("data: null", html)

    def test_signal_with_complex_types(self):
        """Test Signal with lists and dicts."""
        items_sig = Signal("items", [1, 2, 3])
        config_sig = Signal("config", {"theme": "dark", "lang": "en"})

        self.assertEqual(items_sig.value, [1, 2, 3])
        self.assertEqual(config_sig.value, {"theme": "dark", "lang": "en"})

        # When used in data_signals
        div = Div(data_signals=[items_sig, config_sig])
        html = str(div)
        self.assertIn("items:[1,2,3]", html.replace(" ", ""))
        self.assertIn('"theme": "dark"', html)

    def test_mixed_signal_types(self):
        """Test mixing different signal value types via data_signals kwarg."""
        multiline = """function test() {
    return "hello";
}"""
        signals = [
            Signal("code", multiline),
            Signal("label", "Total: $"),
            Signal("currency", "USD"),
            Signal("amount", js("$price * $quantity")),  # Computed - excluded from data-signals
            Signal("user_name", js("$user.name || 'Anonymous'")),  # Computed - excluded from data-signals
            Signal("tax_rate", 0.08),
            Signal("include_tax", True),
        ]

        div = Div(data_signals=signals)
        html = str(div)

        # Non-computed signals appear in data-signals
        self.assertIn("code:", html)
        self.assertIn('label: "Total: $"', html)
        self.assertIn('currency: "USD"', html)
        self.assertIn("tax_rate: 0.08", html)
        self.assertIn("include_tax: true", html)

        # Computed signals (with js()) are NOT included in data-signals when passed via kwarg
        # They return {} from to_dict() and must be passed as children to create data-computed-* attributes
        self.assertNotIn("$price * $quantity", html)
        self.assertNotIn("$user.name", html)

    def test_computed_signals_as_children(self):
        """Test computed signals create data-computed-* attributes when passed as children."""
        # The correct pattern for computed signals: pass as children (walrus pattern)
        div = Div(
            (price := Signal("price", 10)),
            (quantity := Signal("quantity", 5)),
            (amount := Signal("amount", price * quantity)),  # Computed from other signals
            (user_name := Signal("user_name", js("$user.name || 'Anonymous'"))),  # JS expression
            "Content",
        )

        html = str(div)

        # Non-computed signals appear in data-signals
        self.assertIn("price: 10", html)
        self.assertIn("quantity: 5", html)

        # Computed signals create data-computed-* attributes
        self.assertIn("data-computed-amount", html)
        self.assertIn("$price * $quantity", html)
        self.assertIn("data-computed-user_name", html)
        self.assertTrue("$user.name || 'Anonymous'" in html or "$user.name || &#39;Anonymous&#39;" in html)

        # Computed signals do NOT appear in data-signals
        self.assertNotIn("amount:", html.split("data-computed")[0])  # Check only data-signals portion

    def test_string_vs_js_expression(self):
        """Test distinction between string literals and JS expressions."""
        # String literals are just strings
        string_signals = [
            Signal("signal", "$activeTab"),  # String literal
            Signal("computed", "$items.length"),  # String literal
            Signal("template", "`Hello ${name}`"),  # String literal
        ]

        div1 = Div(data_signals=string_signals)
        html1 = str(div1)
        # These are string values, not expressions
        self.assertIn('signal: "$activeTab"', html1)

        # JS expressions with js() create computed signals
        # When passed via data_signals kwarg, computed signals are excluded
        js_signals = [
            Signal("signal", js("$activeTab")),  # Computed - excluded
            Signal("computed", js("$items.length")),  # Computed - excluded
            Signal("template", js("`Hello ${name}`")),  # Computed - excluded
        ]

        div2 = Div(data_signals=js_signals)
        html2 = str(div2)
        # Computed signals don't appear when passed via kwarg
        self.assertNotIn("signal:", html2)
        self.assertNotIn("computed:", html2)

        # For computed signals to work, use walrus pattern (children)
        div3 = Div(
            (sig := Signal("signal", js("$activeTab"))),
            "Content",
        )
        html3 = str(div3)
        # Computed signals as children create data-computed-* attributes
        self.assertIn("data-computed-signal", html3)
        self.assertIn("$activeTab", html3)

    def test_signal_name_validation(self):
        """Test that Signal names must be valid identifiers."""
        # Valid names
        sig1 = Signal("valid_name", 0)
        sig2 = Signal("user_123", "test")

        # Invalid names would raise error (camelCase not allowed)
        with self.assertRaises(ValueError) as ctx:
            Signal("camelCase", 0)
        self.assertIn("snake_case", str(ctx.exception))

    def test_empty_string_signal(self):
        """Test empty strings are handled correctly."""
        empty1 = Signal("empty1", "")
        empty2 = Signal("empty2", "")

        self.assertEqual(empty1.value, "")
        self.assertEqual(empty2.value, "")

        div = Div(data_signals=[empty1, empty2])
        html = str(div)
        self.assertIn('empty1: ""', html)
        self.assertIn('empty2: ""', html)

    def test_unicode_and_special_chars(self):
        """Test Unicode and special characters are handled."""
        special = "Hello 👋 \t\r\n\\ \"quotes\" 'apostrophe'"
        sig = Signal("text", special)
        self.assertEqual(sig.value, special)

        div = Div(data_signals=[sig])
        html = str(div)
        # Check it's properly escaped in HTML
        self.assertIn("Hello", html)
        # Unicode characters may be escaped in HTML output
        self.assertTrue("👋" in html or "\\ud83d\\udc4b" in html)

    def test_data_signals_dict_format(self):
        """Test dict format for data_signals attribute."""
        # Test using dict format for data_signals
        signals_dict = {"name": "Alice", "age": 25, "active": True, "computed": js("$age * 2")}

        div = Div(data_signals=signals_dict)
        html = str(div)
        self.assertIn("data-signals", html)
        self.assertIn('name: "Alice"', html)
        self.assertIn("age: 25", html)
        self.assertIn("active: true", html)

    def test_walrus_operator_collection(self):
        """Test that signals created with walrus operator are auto-collected."""
        # This pattern is used in actual components
        div = Div(
            (counter := Signal("counter", 0)),
            (step := Signal("step", 1)),
            "Click to increment",
            data_on_click=counter.set(counter + step),
        )

        html = str(div)
        # Signals should be auto-collected into data-signals
        self.assertIn("data-signals", html)
        self.assertIn("counter: 0", html)
        self.assertIn("step: 1", html)

    def test_build_data_signals_function(self):
        """Test build_data_signals helper function."""
        # Test with dict
        result = build_data_signals({"name": "Alice", "age": 25, "active": True})
        # build_data_signals returns a NotStr (raw JS object)
        self.assertIn('name: "Alice"', str(result))
        self.assertIn("age: 25", str(result))
        self.assertIn("active: true", str(result))

    def test_signals_list_vs_dict(self):
        """Test data_signals accepts both list of Signals and dict."""
        # List format - only non-computed signals appear
        signals_list = [
            Signal("count", 0),
            Signal("doubled", js("$count * 2")),  # Computed - excluded
        ]
        div1 = Div(data_signals=signals_list)
        html1 = str(div1)
        self.assertIn("count: 0", html1)
        # Computed signals passed via kwarg don't appear
        self.assertNotIn("doubled", html1)

        # Dict format - dict values with js() are included (different from Signal objects)
        signals_dict = {
            "count": 0,
            "doubled": js("$count * 2"),  # js() value in dict IS included
        }
        div2 = Div(data_signals=signals_dict)
        html2 = str(div2)
        self.assertIn("count: 0", html2)
        self.assertIn("doubled: $count * 2", html2)  # Dict format includes js() values

    def test_signal_auto_collection(self):
        """Test that Signals are automatically collected from children."""
        # Mimicking the walrus pattern used in demos
        container = Div(
            (user_id := Signal("user_id", 123)),
            (username := Signal("username", "alice")),
            (email := Signal("email", "alice@example.com")),
            (role := Signal("role", "admin")),
            (active := Signal("active", True)),
            (login_count := Signal("login_count", 0)),
            P("User info loaded"),
        )

        html = str(container)
        # All signals should be collected
        self.assertIn("user_id: 123", html)
        self.assertIn('username: "alice"', html)
        self.assertIn('email: "alice@example.com"', html)
        self.assertIn('role: "admin"', html)
        self.assertIn("active: true", html)
        self.assertIn("login_count: 0", html)

    def test_signal_operations(self):
        """Test Signal arithmetic and logical operations."""
        counter = Signal("counter", 10)
        step = Signal("step", 2)

        # Arithmetic operations create JS expressions
        add_expr = counter + step
        self.assertEqual(str(add_expr), "($counter + $step)")

        sub_expr = counter - 5
        self.assertEqual(str(sub_expr), "($counter - 5)")

        mul_expr = counter * 2
        self.assertEqual(str(mul_expr), "($counter * 2)")

        # Comparison operations
        gt_expr = counter > 5
        self.assertEqual(str(gt_expr), "($counter > 5)")

        eq_expr = counter == 10
        self.assertEqual(str(eq_expr), "($counter === 10)")

        # Logical operations
        and_expr = (counter > 0) & (step > 0)
        self.assertEqual(str(and_expr), "(($counter > 0) && ($step > 0))")

    def test_f_template_function(self):
        """Test f() function for template literals."""
        # f() creates reactive template literals
        name = Signal("name", "Alice")
        count = Signal("count", 5)

        # Using f() for reactive templates
        template = f("Hello {name}, you have {count} messages!", name=name, count=count)
        expected = "`Hello ${$name}, you have ${$count} messages!`"
        self.assertEqual(str(template), expected)

        # f() with conditional
        plural = f("{count} {item}", count=count, item=(count == 1).if_("item", "items"))
        self.assertIn("${$count}", str(plural))
        self.assertIn("$count === 1", str(plural))


if __name__ == "__main__":
    unittest.main()
