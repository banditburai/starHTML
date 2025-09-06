"""Test that DatastarAttr implements the mapping protocol for unpacking."""

from starhtml.datastar import (
    DatastarAttr,
    ds_attr,
    ds_bind,
    ds_class,
    ds_disabled,
    ds_show,
    ds_style,
    ds_text,
)


class TestDatastarAttrMapping:
    """Test that DatastarAttr can be unpacked with **."""

    def test_datastar_attr_is_mapping(self):
        """Test that DatastarAttr implements the mapping protocol."""
        attr = DatastarAttr({"test-key": "test-value"})

        # Test mapping methods
        assert list(attr.keys()) == ["test-key"]
        assert len(attr) == 1
        assert list(attr) == ["test-key"]
        assert attr["test-key"] == "test-value"

        # Test unpacking
        unpacked = {**attr}
        assert unpacked == {"test-key": "test-value"}

        # Test dict() constructor
        as_dict = dict(attr)
        assert as_dict == {"test-key": "test-value"}

    def test_ds_disabled_unpacking(self):
        """Test ds_disabled can be unpacked directly."""
        # Without unpacking operator should fail previously, but work now
        result = {**ds_disabled("$condition")}
        assert result == {"data-attr-disabled": "$condition"}

        # Boolean value
        result = {**ds_disabled(True)}
        assert result == {"data-attr-disabled": "true"}

    def test_multiple_ds_functions_unpacking(self):
        """Test combining multiple ds_* functions with unpacking."""
        combined = {**ds_disabled("!$isActive"), **ds_class(**{"opacity-50": "$isDisabled"}), **ds_show("$isVisible")}

        assert "data-attr-disabled" in combined
        assert "data-class-opacity-50" in combined
        assert "data-show" in combined

    def test_ds_class_unpacking(self):
        """Test ds_class unpacking with various inputs."""
        # Regular classes
        result = {**ds_class(**{"text-blue": "$isBlue", "font-bold": "$isBold"})}
        assert "data-class-text-blue" in result
        assert "data-class-font-bold" in result

        # With slashes (uses dictionary format)
        result = {**ds_class(**{"border-primary/60": "$isPrimary"})}
        assert "data-class" in result
        assert "border-primary/60" in result["data-class"]

    def test_all_ds_functions_unpackable(self):
        """Test that all ds_* functions return unpackable results."""
        # Test functions that take positional args
        positional_funcs = [
            (ds_show, "$visible"),
            (ds_text, "$message"),
            (ds_bind, "inputValue"),
            (ds_disabled, "$isDisabled"),
        ]

        for func, arg in positional_funcs:
            result = func(arg)
            # Should be able to unpack without error
            unpacked = {**result}
            assert isinstance(unpacked, dict)
            assert len(unpacked) > 0

        # Test functions that take keyword args
        result = ds_style(color="$textColor")
        unpacked = {**result}
        assert isinstance(unpacked, dict)

        result = ds_attr(title="$tooltip")
        unpacked = {**result}
        assert isinstance(unpacked, dict)

    def test_backward_compatibility(self):
        """Test that .attrs still works for backward compatibility."""
        attr = ds_disabled("$condition")

        # Old way with .attrs
        old_way = attr.attrs
        assert old_way == {"data-attr-disabled": "$condition"}

        # New way with unpacking
        new_way = {**attr}
        assert new_way == {"data-attr-disabled": "$condition"}

        # Both should be identical
        assert old_way == new_way

    def test_empty_datastar_attr(self):
        """Test edge case with empty attributes."""
        attr = DatastarAttr({})

        assert len(attr) == 0
        assert list(attr.keys()) == []
        assert {**attr} == {}
        assert dict(attr) == {}

    def test_multiple_attributes(self):
        """Test DatastarAttr with multiple attributes."""
        attr = DatastarAttr({"data-show": "$visible", "data-text": "$message", "data-class-active": "$isActive"})

        assert len(attr) == 3
        assert set(attr.keys()) == {"data-show", "data-text", "data-class-active"}

        unpacked = {**attr}
        assert unpacked["data-show"] == "$visible"
        assert unpacked["data-text"] == "$message"
        assert unpacked["data-class-active"] == "$isActive"
