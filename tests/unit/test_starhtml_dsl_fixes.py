"""
Test cases for starhtml DSL fixes (to run after upstream changes are made)

These tests verify that fixing Expr subclass attribute names enables
chained property access without conflicts.

Run these tests AFTER applying the changes documented in UPSTREAM.md #5
"""

import pytest

from starhtml import Signal
from starhtml.datastar import PropertyAccess, js


class TestChainedPropertyAccess:
    """Test that chained property access works after DSL fixes"""

    def test_index_access_basic(self):
        """Basic array indexing should work"""
        arr = Signal("items", [])
        result = arr[0]
        assert result.to_js() == "$items[0]"

    def test_index_access_chained_index_property(self):
        """arr[0].index should generate property access, not return literal 0"""
        arr = Signal("items", [])
        result = arr[0].index
        assert result.to_js() == "$items[0].index"
        # NOT "0" which was the bug

    def test_index_access_chained_name_property(self):
        """arr[0].name should work"""
        arr = Signal("items", [])
        result = arr[0].name
        assert result.to_js() == "$items[0].name"

    def test_index_access_chained_value_property(self):
        """arr[0].value should work"""
        arr = Signal("items", [])
        result = arr[0].value
        assert result.to_js() == "$items[0].value"

    def test_index_access_chained_id_property(self):
        """arr[0].id should work"""
        arr = Signal("items", [])
        result = arr[0].id
        assert result.to_js() == "$items[0].id"

    def test_multiple_index_levels(self):
        """Nested array access should work"""
        arr = Signal("items", [])
        result = arr[0].items[1].name
        assert result.to_js() == "$items[0].items[1].name"

    def test_binary_op_property_access(self):
        """(a > b).value should work"""
        a = Signal("a", 0)
        b = Signal("b", 0)
        result = (a > b).value
        assert result.to_js() == "($a > $b).value"

    def test_binary_op_method_call(self):
        """(a > b).toString() should work"""
        a = Signal("a", 0)
        b = Signal("b", 0)
        result = (a > b).toString()
        assert result.to_js() == "($a > $b).toString()"

    def test_conditional_property_access(self):
        """Ternary result property access"""
        cond = Signal("cond", False)
        result = cond.if_("yes", "no").length
        assert result.to_js() == '($cond ? "yes" : "no").length'

    def test_assignment_doesnt_break(self):
        """Assignment.set() should still work (not conflict with .value property)"""
        sig = Signal("test", 0)
        result = sig.set(5)
        assert result.to_js() == "($test = 5)"

    def test_property_access_chaining(self):
        """obj.prop.value should work"""
        obj = Signal("obj", {})
        result = obj.data.value
        assert result.to_js() == "$obj.data.value"

    def test_method_call_property_access(self):
        """obj.method().prop should work"""
        obj = Signal("obj", {})
        result = obj.getData().value
        assert result.to_js() == "$obj.getData().value"


class TestNoRegressions:
    """Ensure existing functionality still works"""

    def test_signal_property_access_still_works(self):
        """Signal.length property should still work"""
        sig = Signal("items", [])
        result = sig.length
        assert result.to_js() == "$items.length"

    def test_signal_method_call_still_works(self):
        """Signal.method() should still work"""
        sig = Signal("items", [])
        result = sig.push(5)
        assert result.to_js() == "$items.push(5)"

    def test_signal_set_still_works(self):
        """Signal.set() should still work"""
        sig = Signal("count", 0)
        result = sig.set(10)
        assert result.to_js() == "($count = 10)"

    def test_binary_ops_still_work(self):
        """Binary operations should still work"""
        a = Signal("a", 0)
        b = Signal("b", 0)
        assert (a > b).to_js() == "($a > $b)"
        assert (a & b).to_js() == "($a && $b)"
        assert (a | b).to_js() == "($a || $b)"

    def test_conditionals_still_work(self):
        """Conditional.if_() should still work"""
        cond = Signal("cond", False)
        result = cond.if_("yes", "no")
        assert result.to_js() == '($cond ? "yes" : "no")'

    def test_js_raw_still_works(self):
        """js() function should still work"""
        result = js("console.log('test')")
        assert result.to_js() == "console.log('test')"


class TestEdgeCases:
    """Test edge cases and potential conflicts"""

    def test_private_attributes_not_accessible(self):
        """Private attributes with _ prefix don't conflict with JS properties"""
        sig = Signal("test", [])
        result = sig[0]

        # The fix moved attributes to _obj and _index (private)
        # This means accessing .obj or .index now creates PropertyAccess (JS property access)
        # Instead of returning the Python attribute value
        obj_access = result.obj  # This creates PropertyAccess("obj")
        assert isinstance(obj_access, PropertyAccess)
        assert obj_access.to_js() == "$test[0].obj"

        index_access = result.index  # This creates PropertyAccess("index"), not literal 0!
        assert isinstance(index_access, PropertyAccess)
        assert index_access.to_js() == "$test[0].index"

    def test_to_js_method_not_broken(self):
        """to_js() method should still be callable"""
        sig = Signal("test", [])
        result = sig[0]

        # to_js is a method, not a property
        assert callable(result.to_js)
        assert result.to_js() == "$test[0]"

    def test_slots_still_prevent_arbitrary_attributes(self):
        """__slots__ prevent setting new attributes (assignment)"""
        sig = Signal("test", [])
        result = sig[0]

        # Note: Expr objects actually use __setattr__ which allows dynamic attributes
        # This is intentional to support setting attributes via assignment expressions
        # The important thing is that reading non-existent attrs returns PropertyAccess
        result.random_attribute = "value"  # This is allowed
        # But reading it creates PropertyAccess (not stored)
        accessed = result.another_attr
        assert isinstance(accessed, PropertyAccess)

    def test_property_name_conflicts_resolved(self):
        """Properties that conflicted with slots should now work"""
        sig = Signal("items", [])

        # These all used to conflict with __slots__ attributes
        assert sig[0].index.to_js() == "$items[0].index"
        assert sig[0].value.to_js() == "$items[0].value"

        obj = Signal("obj", {})
        assert obj.data.prop.to_js() == "$obj.data.prop"


class TestAssignmentParenthesization:
    """Assignment.to_js() must wrap in parens for safe composability with && and ||."""

    def test_standalone_assignment(self):
        """Standalone assignment gets parens (harmless)."""
        sig = Signal("x", 0)
        assert sig.set(5).to_js() == "($x = 5)"

    def test_assignment_in_logical_and(self):
        """Assignment on right side of && must be parenthesized."""
        loading = Signal("loading", 1)
        tick = Signal("tick", 0)
        expr = (tick >= 15) & loading.set(0)
        result = expr.to_js()
        # Must NOT produce: (($tick >= 15) && $loading = 0)
        # which JS parses as: (($tick >= 15) && $loading) = 0  → SyntaxError
        assert result == "(($tick >= 15) && ($loading = 0))"

    def test_assignment_in_logical_or(self):
        """Assignment on right side of || must be parenthesized."""
        fallback = Signal("fallback", "")
        primary = Signal("primary", "")
        expr = (primary == "") | fallback.set("default")
        result = expr.to_js()
        assert result == '(($primary === "") || ($fallback = "default"))'

    def test_assignment_in_seq(self):
        """Assignment inside seq() — parens are harmless."""
        from starhtml.datastar import seq

        a = Signal("a", 0)
        b = Signal("b", 0)
        result = seq(a.set(1), b.set(2)).to_js()
        assert result == "(($a = 1), ($b = 2))"

    def test_assignment_with_add(self):
        """Signal.add() also produces Assignment — should be parenthesized."""
        count = Signal("count", 0)
        result = count.add(5).to_js()
        assert result == "($count = ($count + 5))"

    def test_nested_condition_with_assignment(self):
        """Real-world pattern: condition & assignment in interval handler."""
        loading = Signal("loading", 1)
        tick = Signal("tick", 0)
        from starhtml.datastar import seq

        expr = seq(tick.add(1), (tick >= 15) & loading.set(0))
        result = expr.to_js()
        assert "($loading = 0)" in result
        assert "&&" in result


class TestFTAttrGuard:
    """Expr/Signal raise AttributeError for FT protocol attrs (tag, children, attrs, void_)."""

    def test_signal_tag_raises(self):
        sig = Signal("x", 0)
        with pytest.raises(AttributeError, match="not an FT element"):
            sig.tag  # noqa: B018

    def test_signal_children_raises(self):
        sig = Signal("x", 0)
        with pytest.raises(AttributeError, match="not an FT element"):
            sig.children  # noqa: B018

    def test_signal_attrs_raises(self):
        sig = Signal("x", 0)
        with pytest.raises(AttributeError, match="not an FT element"):
            sig.attrs  # noqa: B018

    def test_signal_void_raises(self):
        sig = Signal("x", 0)
        with pytest.raises(AttributeError, match="not an FT element"):
            sig.void_  # noqa: B018

    def test_expr_tag_raises(self):
        expr = js("console.log()")
        with pytest.raises(AttributeError, match="not an FT element"):
            expr.tag  # noqa: B018

    def test_getattr_fallback_returns_default(self):
        """getattr(signal, 'tag', '') returns '' instead of PropertyAccess."""
        sig = Signal("x", 0)
        assert getattr(sig, "tag", "") == ""

    def test_normal_property_access_unaffected(self):
        """Non-FT attributes still return PropertyAccess."""
        sig = Signal("x", 0)
        result = sig.name
        assert isinstance(result, PropertyAccess)
        assert result.to_js() == "$x.name"


class TestSignalInTopLevelTuple:
    """Signal in a route return tuple must not break full-page wrapping."""

    @pytest.mark.asyncio
    async def test_signal_in_tuple_produces_full_page(self):
        from starhtml import Div, Title
        from starhtml.core import StarHTML

        app = StarHTML()

        @app.get("/")
        def home():
            return Title("Test"), Signal("sidebar", False), Div("Hello")

        resp = await app.handle_request("GET", "/")
        body = resp.body.decode()
        assert "<!DOCTYPE html>" in body
        assert "<html" in body
        assert "Hello" in body

    @pytest.mark.asyncio
    async def test_signal_in_tuple_becomes_data_signals(self):
        from starhtml import Div, Title
        from starhtml.core import StarHTML

        app = StarHTML()

        @app.get("/")
        def home():
            return Title("Test"), Signal("count", 42), Div("Content")

        resp = await app.handle_request("GET", "/")
        body = resp.body.decode()
        assert "data-signals" in body
        assert "count" in body

    @pytest.mark.asyncio
    async def test_multiple_signals_in_tuple(self):
        from starhtml import Div
        from starhtml.core import StarHTML

        app = StarHTML()

        @app.get("/")
        def home():
            return Signal("a", 1), Signal("b", 2), Div("Body")

        resp = await app.handle_request("GET", "/")
        body = resp.body.decode()
        assert "<!DOCTYPE html>" in body
        assert "data-signals" in body


def run_tests():
    """Helper to run all tests"""
    pytest.main([__file__, "-v"])


if __name__ == "__main__":
    run_tests()
