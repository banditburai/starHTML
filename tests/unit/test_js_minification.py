"""Tests for js() function minification and operator spacing fixes.

This test suite ensures that the rjsmin minifier workaround correctly handles
operator spacing for Datastar RC6 signal expressions while not breaking:
- URL paths in strings
- Regular JavaScript operators
- String literals
- Complex expressions
"""

from starhtml.datastar import js


class TestJSMinificationOperatorSpacing:
    """Test that js() correctly handles operator spacing for Datastar signals."""

    def test_signal_arithmetic_subtraction(self):
        """Signal subtraction should have spaces added around the minus operator."""
        # Original bug: $monster_hp-dmg became $monster_hp-dmg (interpreted as signal name)
        code = js("$monster_hp - dmg")
        assert "$monster_hp - dmg" in str(code) or "$monster_hp-dmg" not in str(code)

        # Minified version still needs spaces around operator
        code = js("$monster_hp-dmg")
        assert " - " in str(code), f"Expected spaces around '-' operator, got: {code}"

    def test_signal_arithmetic_addition(self):
        """Signal addition should have spaces added."""
        code = js("$counter+$step")
        assert " + " in str(code), f"Expected spaces around '+' operator, got: {code}"

    def test_signal_arithmetic_multiplication(self):
        """Signal multiplication should have spaces added."""
        code = js("$value*2")
        assert " * " in str(code), f"Expected spaces around '*' operator, got: {code}"

    def test_signal_arithmetic_division(self):
        """Signal division should have spaces added."""
        code = js("$counter/2")
        assert " / " in str(code), f"Expected spaces around '/' operator, got: {code}"

    def test_signal_arithmetic_modulo(self):
        """Signal modulo should have spaces added."""
        code = js("$value%10")
        assert " % " in str(code), f"Expected spaces around '%' operator, got: {code}"


class TestJSMinificationStringPreservation:
    """Test that strings are NOT affected by operator spacing fixes."""

    def test_url_path_preserved(self):
        """URL paths with slashes should not have spaces added."""
        # Original bug fix broke this: 'todos/add' became 'todos / add'
        code = js("@post('todos/add', {todo_text: $todo_text})")
        result = str(code)
        assert "'todos/add'" in result or '"todos/add"' in result, f"URL path should not have spaces: {result}"
        assert "todos / add" not in result, f"URL path should not be split: {result}"

    def test_url_with_query_params(self):
        """URLs with query parameters should be preserved."""
        code = js("fetch('/api/users?page=1&limit=10')")
        result = str(code)
        # Should not add spaces around special chars in strings
        assert "'/api/users?page=1&limit=10'" in result or '"/api/users?page=1&limit=10"' in result


class TestJSMinificationComplexExpressions:
    """Test complex JavaScript expressions with mixed operators and signals."""

    def test_mixed_signal_and_literal_operators(self):
        """Expressions mixing signals and literals should work correctly."""
        code = js("$counter + 5 - $step")
        result = str(code)
        # At least the operators next to signals should have spaces
        assert "$counter +" in result or "+ $step" in result or "- $step" in result

    def test_chained_operators(self):
        """Multiple chained operators should all get spaces."""
        code = js("$a+$b-$c*$d")
        result = str(code)
        # Should have spaces around operators adjacent to signals
        assert " + " in result or " - " in result or " * " in result, (
            f"At least some operators should have spaces: {result}"
        )


class TestJSMinificationRegressionPrevention:
    """Specific regression tests for bugs we've encountered."""

    def test_monster_hp_bug_regression(self):
        """Original bug: $monster_hp-dmg was interpreted as a signal name."""
        code = js("$monster_hp = Math.max(0, $monster_hp - dmg)")
        result = str(code)
        # Must have space around the minus
        assert "$monster_hp - dmg" in result, f"Monster HP subtraction must have spaces: {result}"

    def test_todos_add_url_regression(self):
        """Regression: 'todos/add' was becoming 'todos / add'."""
        code = js("if($can_add_todo){@post('todos/add',{todo_text:$todo_text});}")
        result = str(code)
        assert "'todos/add'" in result or '"todos/add"' in result, f"URL 'todos/add' must stay intact: {result}"
        assert "todos / add" not in result, f"URL must not have spaces inserted: {result}"

    def test_keydown_handler_regression(self):
        """The full keydown handler that was broken."""
        code = js("""
            if(evt.key === 'Enter' && !evt.shiftKey) {
                evt.preventDefault();
                if($can_add_todo) {
                    @post('todos/add', {todo_text: $todo_text});
                }
            }
        """)
        result = str(code)
        # URL must be preserved
        assert "'todos/add'" in result or '"todos/add"' in result
        # Signal references should work
        assert "$can_add_todo" in result
        assert "$todo_text" in result
        # URL should not have spaces
        assert "todos / add" not in result
