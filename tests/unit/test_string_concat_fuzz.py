"""
Comprehensive fuzz tests for string concatenation to ensure optimal JS output.
Tests all edge cases and combinations to verify no unnecessary punctuation.
"""

import random

from starhtml.datastar import Signal, match


class TestStringConcatenationFuzz:
    """Fuzz tests to ensure optimal JavaScript output."""

    def test_no_nested_template_literals(self):
        """Ensure we never generate nested template literals like ``expr`text``."""
        signal = Signal("test")

        # Test all permutations that should NOT create nested templates
        test_cases = [
            ("start " + signal + " end", "`start ${$test} end`"),
            (signal + " suffix", "`${$test} suffix`"),
            ("prefix " + signal, "`prefix ${$test}`"),
            ("a" + signal + "b" + signal + "c", "`a${$test}b${$test}c`"),
        ]

        for expr, expected in test_cases:
            result = expr.to_js()
            assert result == expected, f"Expected {expected}, got {result}"
            # Ensure no nested backticks
            assert "``" not in result, f"Found nested backticks in: {result}"
            assert "`${" not in result or result.count("`${") <= 1, f"Multiple template start sequences: {result}"

    def test_long_chain_concatenation(self):
        """Test very long chains of concatenation remain clean."""
        signal = Signal("val")

        # Build a long chain: "a" + signal + "b" + signal + "c" + signal + "d"
        result = "a" + signal + "b" + signal + "c" + signal + "d"
        expected = "`a${$val}b${$val}c${$val}d`"

        assert result.to_js() == expected
        assert result.to_js().count("`") == 2  # Only start and end backticks

    def test_expression_combinations(self):
        """Test various combinations of expressions and strings."""
        sig1 = Signal("a")
        sig2 = Signal("b")
        expr = sig1.round()

        test_cases = [
            # Different expression types
            ("Value: " + expr, "`Value: ${Math.round($a)}`"),
            (expr + " units", "`${Math.round($a)} units`"),
            (sig1 + " and " + sig2, "`${$a} and ${$b}`"),
            ("(" + expr + "/" + sig2 + ")", "`(${Math.round($a)}/${$b})`"),
            # With conditionals
            (sig1.if_("yes", "no") + " result", '`${($a ? "yes" : "no")} result`'),
            ("Status: " + sig1.if_("on", "off"), '`Status: ${($a ? "on" : "off")}`'),
        ]

        for expr_obj, expected in test_cases:
            result = expr_obj.to_js()
            assert result == expected, f"Expected {expected}, got {result}"
            self._verify_clean_output(result)

    def test_special_characters_escaping(self):
        """Test that special characters are properly escaped."""
        signal = Signal("test")

        # Test backticks in strings
        result1 = "text with `backticks` " + signal
        assert "\\`" in result1.to_js(), "Backticks should be escaped"

        # Test dollar signs
        result2 = "price $100 " + signal
        expected2 = "`price $100 ${$test}`"
        assert result2.to_js() == expected2

        # Test template literal injection attempts
        result3 = "safe ${code} " + signal
        expected3 = "`safe \\${code} ${$test}`"
        assert result3.to_js() == expected3

    def test_empty_and_edge_cases(self):
        """Test edge cases like empty strings, whitespace, etc."""
        signal = Signal("x")

        test_cases = [
            ("" + signal, "`${$x}`"),  # Empty prefix
            (signal + "", "`${$x}`"),  # Empty suffix
            (" " + signal + " ", "` ${$x} `"),  # Whitespace
            ("\n" + signal + "\t", "`\n${$x}\t`"),  # Newlines/tabs
            (signal + signal, "($x + $x)"),  # Signal + Signal = arithmetic
        ]

        for expr, expected in test_cases:
            result = expr.to_js()
            assert result == expected, f"Expected {expected}, got {result}"
            if "`" in result:
                self._verify_clean_output(result)

    def test_complex_expressions_with_operators(self):
        """Test concatenation with complex expressions involving operators."""
        a = Signal("a")
        b = Signal("b")

        # Arithmetic expressions in concatenation
        result1 = "Sum: " + (a + b) + " total"
        expected1 = "`Sum: ${($a + $b)} total`"
        assert result1.to_js() == expected1

        # Comparison expressions
        result2 = "Is greater: " + (a > b).if_("yes", "no")
        expected2 = '`Is greater: ${(($a > $b) ? "yes" : "no")}`'
        assert result2.to_js() == expected2

        # Mixed operators
        result3 = (a * 2) + " times two"
        expected3 = "`${($a * 2)} times two`"
        assert result3.to_js() == expected3

    def test_fuzz_random_combinations(self):
        """Fuzz test with random combinations."""
        signals = [Signal(f"s{i}") for i in range(5)]
        strings = ["hello", "world", " ", "123", "test"]

        for _ in range(50):  # Run 50 random tests
            # Build a random concatenation chain
            parts = []
            for _ in range(random.randint(2, 6)):
                if random.choice([True, False]):
                    parts.append(random.choice(strings))
                else:
                    parts.append(random.choice(signals))

            # Build the expression - ensure first part is an expression if starting with string
            result = parts[0]
            if isinstance(result, str) and len(parts) > 1:
                # Start with first signal to ensure we get an Expr object
                signal_indices = [i for i, p in enumerate(parts) if not isinstance(p, str)]
                if signal_indices and signal_indices[0] > 0:
                    # Swap first string with first signal
                    first_signal_idx = signal_indices[0]
                    parts[0], parts[first_signal_idx] = parts[first_signal_idx], parts[0]
                    result = parts[0]

            for part in parts[1:]:
                result = result + part

            # Skip if still just a string (no expressions added)
            if isinstance(result, str):
                continue

            js_output = result.to_js()
            self._verify_clean_output(js_output)

    def test_match_function_concatenation(self):
        """Test concatenation with match function results."""
        status = Signal("status")

        # Match result in concatenation
        result = "Status: " + match(status, ok="✓", error="✗", loading="...")
        js_output = result.to_js()

        # Should be clean template literal
        assert js_output.startswith("`Status: ")
        assert js_output.endswith("`")
        self._verify_clean_output(js_output)

    def test_performance_indicators(self):
        """Test that output doesn't contain performance-degrading patterns."""
        signal = Signal("perf")

        # Very long concatenation chain
        result = signal
        for i in range(20):
            result = result + f" step{i}"

        js_output = result.to_js()

        # Should be one clean template literal, not nested
        backtick_count = js_output.count("`")
        assert backtick_count == 2, f"Should have exactly 2 backticks, got {backtick_count} in: {js_output}"

        # Should not have excessive interpolations
        interpolation_count = js_output.count("${")
        assert interpolation_count <= 21, f"Too many interpolations: {interpolation_count}"

    def _verify_clean_output(self, js_output: str):
        """Helper to verify JS output is clean and optimal."""
        # No nested template literals
        assert "``" not in js_output, f"Found nested backticks: {js_output}"

        # If it's a template literal, should have proper structure
        if js_output.startswith("`") and js_output.endswith("`"):
            # Count backticks - should be exactly 2 (start and end)
            backtick_count = js_output.count("`")
            assert backtick_count == 2, f"Template literal should have exactly 2 backticks: {js_output}"

            # Should not have template literals inside template literals
            # Look for patterns like `...`${"..."}`
            assert "`${" not in js_output.replace(js_output[0], "", 1), f"Nested template pattern found: {js_output}"

        # No unnecessary string concatenation in template literals
        assert '`${"`' not in js_output, f"Unnecessary string literal in template: {js_output}"
        assert '`${"}`' not in js_output, f"Unnecessary string literal in template: {js_output}"


class TestOptimalOutputPattern:
    """Tests to verify we always generate the most optimal JavaScript patterns."""

    def test_optimal_single_expression(self):
        """Single expressions should not be wrapped unnecessarily."""
        signal = Signal("test")

        # Just a signal by itself should not create template literal
        assert signal.to_js() == "$test"

        # Signal with operation should be wrapped only when needed
        expr = signal.round()
        assert expr.to_js() == "Math.round($test)"

        # Only when mixed with strings should we get templates
        mixed = "Value: " + signal
        assert mixed.to_js() == "`Value: ${$test}`"

    def test_minimal_wrapping(self):
        """Expressions should only be wrapped when necessary."""
        signal = Signal("val")

        # Simple concatenation
        result = signal + " items"
        assert result.to_js() == "`${$val} items`"

        # Should not double-wrap
        result2 = "Count: " + result
        expected = "`Count: ${$val} items`"  # Should flatten, not nest
        assert result2.to_js() == expected

    def test_arithmetic_vs_concatenation(self):
        """Ensure proper distinction between arithmetic and string concatenation."""
        a = Signal("a")
        b = Signal("b")

        # Expression + Expression = arithmetic
        arithmetic = a + b
        assert arithmetic.to_js() == "($a + $b)"

        # Expression + String = template literal
        template = a + " units"
        assert template.to_js() == "`${$a} units`"

        # String + Expression = template literal
        template2 = "Total: " + a
        assert template2.to_js() == "`Total: ${$a}`"
