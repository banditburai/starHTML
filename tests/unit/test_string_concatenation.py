"""Tests for string concatenation with signals and expressions."""

from starhtml.datastar import Signal, js, value


class TestStringConcatenation:
    """Test suite for string concatenation with signals and expressions."""

    def test_signal_plus_string(self):
        """Test signal + string concatenation."""
        signal = Signal("counter")
        result = signal + " items"
        assert result.to_js() == "`${$counter} items`"

    def test_string_plus_signal(self):
        """Test string + signal concatenation."""
        signal = Signal("name")
        result = "Hello, " + signal
        assert result.to_js() == "`Hello, ${$name}`"

    def test_expression_plus_string(self):
        """Test expression + string concatenation."""
        expr = js("Math.round($value)")
        result = expr + "%"
        assert result.to_js() == "`${Math.round($value)}%`"

    def test_string_plus_expression(self):
        """Test string + expression concatenation."""
        expr = Signal("progress").round()
        result = "Progress: " + expr + "%"
        assert result.to_js() == "`Progress: ${Math.round($progress)}%`"

    def test_chain_concatenation(self):
        """Test chained concatenation."""
        signal = Signal("count")
        result = "(" + signal + " of " + js("$total") + ")"
        assert result.to_js() == "`(${$count} of ${$total})`"

    def test_with_value_fallback(self):
        """Test concatenation with value() fallback."""
        signal = Signal("velocity")
        result = "(" + (signal | value(0)).round() + " px/s)"
        assert result.to_js() == "`(${Math.round(($velocity || 0))} px/s)`"

    def test_conditional_concatenation(self):
        """Test concatenation with conditional expression."""
        signal = Signal("status")
        expr = (signal == "loading").if_("Loading...", "Ready")
        result = "Status: " + expr
        # Conditional adds parentheses around the condition for safety
        assert result.to_js() == '`Status: ${(($status === "loading") ? "Loading..." : "Ready")}`'

    def test_multiple_signals(self):
        """Test concatenation with multiple signals."""
        first = Signal("first_name")
        last = Signal("last_name")
        result = first + " " + last
        assert result.to_js() == "`${$first_name} ${$last_name}`"

    def test_complex_expression_concatenation(self):
        """Test concatenation with complex expressions."""
        signal = Signal("value")
        expr = (signal * 100).round(2)
        result = expr + "% complete"
        assert result.to_js() == "`${(Math.round((($value * 100) * 100)) / 100)}% complete`"

    def test_nested_template_literal(self):
        """Test that existing template literals are handled correctly."""
        # If already a template literal, should append correctly
        existing = js("`Current: ${$value}`")
        result = existing + " (updated)"
        assert result.to_js() == "`${`Current: ${$value}`} (updated)`"

    def test_empty_string_concatenation(self):
        """Test concatenation with empty strings."""
        signal = Signal("message")
        result = "" + signal + ""
        assert result.to_js() == "`${$message}`"

    def test_signal_to_signal_concatenation(self):
        """Test signal + signal concatenation."""
        sig1 = Signal("part1")
        sig2 = Signal("part2")
        # Signal + Signal is treated as arithmetic addition by default
        result = sig1 + sig2
        assert result.to_js() == "($part1 + $part2)"

        # For string concatenation between signals, use explicit string concatenation
        # e.g., sig1 + " " + sig2 to get template literal

    def test_expression_to_expression_concatenation(self):
        """Test expression + expression concatenation."""
        expr1 = js("$count + 1")
        expr2 = js("$total")
        result = expr1 + " / " + expr2
        assert result.to_js() == "`${$count + 1} / ${$total}`"

    def test_real_world_example(self):
        """Test a real-world concatenation example from the demo."""
        # Simulating: '(' + round(scroll.velocity | value(0)) + ' px/s)'
        velocity = js("$velocity")  # scroll.velocity would be js("$velocity")
        result = "(" + (velocity | value(0)).round() + " px/s)"
        assert result.to_js() == "`(${Math.round(($velocity || 0))} px/s)`"

    def test_invalid_concatenation(self):
        """Test that invalid concatenation returns NotImplemented."""
        signal = Signal("test")
        result = signal.__add__(123)  # Invalid: can't concatenate with number
        assert result == NotImplemented

        result = signal.__radd__(123)  # Invalid: can't concatenate with number
        assert result == NotImplemented
