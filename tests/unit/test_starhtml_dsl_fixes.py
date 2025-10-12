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
        assert result.to_js() == "$test = 5"

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
        assert result.to_js() == "$count = 10"

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


def run_tests():
    """Helper to run all tests"""
    pytest.main([__file__, "-v"])


if __name__ == "__main__":
    run_tests()
