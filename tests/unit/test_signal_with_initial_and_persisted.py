"""Tests for Signal.with_initial() and Signal.persisted() methods."""

import pytest

from starhtml.datastar import Signal, js


class TestWithInitial:
    """Test Signal.with_initial() method for SSR hydration."""

    def test_with_initial_replaces_initial_value(self):
        """Test that with_initial replaces the initial value."""
        original = Signal("count", 0)
        updated = original.with_initial(42)

        assert original._initial == 0
        assert updated._initial == 42

    def test_with_initial_preserves_name(self):
        """Test that name is preserved across with_initial."""
        original = Signal("user_email", "default@example.com")
        updated = original.with_initial("new@example.com")

        assert original._name == "user_email"
        assert updated._name == "user_email"
        assert updated._name == original._name

    def test_with_initial_preserves_type(self):
        """Test that inferred or explicit type is preserved."""
        # String type inference
        original_str = Signal("name", "Alice")
        updated_str = original_str.with_initial("Bob")
        assert updated_str.type_ is str

        # Int type inference
        original_int = Signal("count", 10)
        updated_int = original_int.with_initial(20)
        assert updated_int.type_ is int

        # Bool type inference
        original_bool = Signal("active", True)
        updated_bool = original_bool.with_initial(False)
        assert updated_bool.type_ is bool

        # Explicit type specification
        original_explicit = Signal("value", 0, type_=float)
        updated_explicit = original_explicit.with_initial(3.14)
        assert updated_explicit.type_ is float

    def test_with_initial_preserves_namespace(self):
        """Test that namespace and derived _id are preserved."""
        original = Signal("dark_mode", False, namespace="theme")
        updated = original.with_initial(True)

        assert original._namespace == "theme"
        assert updated._namespace == "theme"
        assert original._id == "theme_dark_mode"
        assert updated._id == "theme_dark_mode"
        assert original._id == updated._id

    def test_with_initial_preserves_ifmissing_true(self):
        """Test that ifmissing=True is preserved."""
        original = Signal("setting", 100, ifmissing=True)
        updated = original.with_initial(200)

        assert original._ifmissing is True
        assert updated._ifmissing is True
        # Verify it affects to_dict behavior
        assert original.to_dict() == {}
        assert updated.to_dict() == {}

    def test_with_initial_preserves_ifmissing_false(self):
        """Test that ifmissing=False is preserved."""
        original = Signal("config", {"key": "value"}, ifmissing=False)
        updated = original.with_initial({"key": "new_value"})

        assert original._ifmissing is False
        assert updated._ifmissing is False
        # Verify it affects to_dict behavior
        assert original.to_dict() == {"config": {"key": "value"}}
        assert updated.to_dict() == {"config": {"key": "new_value"}}

    def test_with_initial_preserves_ref_only_true(self):
        """Test that _ref_only=True is preserved."""
        original = Signal("error_msg", "", _ref_only=True)
        updated = original.with_initial("New error")

        assert original._ref_only is True
        assert updated._ref_only is True
        # Verify get_signal_attr respects _ref_only
        assert original.get_signal_attr() is None
        assert updated.get_signal_attr() is None

    def test_with_initial_preserves_ref_only_false(self):
        """Test that _ref_only=False is preserved."""
        original = Signal("count", 5, _ref_only=False)
        updated = original.with_initial(10)

        assert original._ref_only is False
        assert updated._ref_only is False
        # Verify get_signal_attr returns attribute
        assert original.get_signal_attr() is not None
        assert updated.get_signal_attr() is not None

    def test_with_initial_on_computed_raises_valueerror(self):
        """Test that with_initial raises ValueError on computed signals."""
        base = Signal("base", 5)
        computed = Signal("doubled", base * 2)

        assert computed._is_computed is True

        with pytest.raises(ValueError) as exc_info:
            computed.with_initial(20)

        assert "Cannot call with_initial on computed signal" in str(exc_info.value)
        assert "doubled" in str(exc_info.value)
        assert "derive their value from an expression" in str(exc_info.value)

    def test_with_initial_on_js_computed_raises_valueerror(self):
        """Test that with_initial raises ValueError on js() expressions."""
        computed = Signal("user_name", js("$user.name || 'Anonymous'"))

        assert computed._is_computed is True

        with pytest.raises(ValueError) as exc_info:
            computed.with_initial("John")

        assert "Cannot call with_initial on computed signal" in str(exc_info.value)

    def test_with_initial_returns_new_instance(self):
        """Test that with_initial returns a distinct instance."""
        original = Signal("count", 0)
        updated = original.with_initial(42)

        assert original is not updated
        assert isinstance(updated, Signal)

    def test_with_initial_resets_constraint_attrs(self):
        """Test that validation/constraint attributes start clean on new instance."""
        original = Signal("email", "test@example.com")
        # Simulate constraint attrs being set (as validate() does)
        original._constraint_attrs = {"some_key": "some_value"}

        updated = original.with_initial("new@example.com")

        # New instance starts with empty constraint attrs
        assert updated._constraint_attrs == {}
        # Original is unchanged
        assert original._constraint_attrs == {"some_key": "some_value"}

    def test_with_initial_new_value_rendered_in_signal_attr(self):
        """Test that new initial value appears in get_signal_attr() output."""
        original = Signal("theme", "light", ifmissing=True)
        updated = original.with_initial("dark")

        # Check original
        orig_attr_name, orig_attr_val = original.get_signal_attr()
        assert orig_attr_name == "data-signals:theme__ifmissing"
        assert orig_attr_val == "light"

        # Check updated
        upd_attr_name, upd_attr_val = updated.get_signal_attr()
        assert upd_attr_name == "data-signals:theme__ifmissing"
        assert upd_attr_val == "dark"

    def test_with_initial_none_value(self):
        """Test with_initial with None as new value."""
        original = Signal("optional", "something")
        updated = original.with_initial(None)

        assert updated._initial is None
        # None initial values don't produce signal attrs
        assert updated.get_signal_attr() is None

    def test_with_initial_complex_types(self):
        """Test with_initial with lists and dicts."""
        original_list = Signal("items", [1, 2, 3])
        updated_list = original_list.with_initial([4, 5, 6])
        assert updated_list._initial == [4, 5, 6]

        original_dict = Signal("config", {"a": 1})
        updated_dict = original_dict.with_initial({"b": 2})
        assert updated_dict._initial == {"b": 2}

    def test_with_initial_js_string_literal(self):
        """Test with_initial with string that looks like JS but is treated as literal."""
        original = Signal("code", "const x = 1;")
        updated = original.with_initial("const y = 2;")

        assert updated._initial == "const y = 2;"
        assert updated._is_computed is False


class TestPersisted:
    """Test Signal.persisted() method for dict-based hydration."""

    def test_persisted_hydrates_from_dict(self):
        """Test that persisted looks up signal name in dict and uses that value."""
        signal = Signal("user_id", 0)
        persisted_dict = {"user_id": 123}

        hydrated = signal.persisted(persisted_dict)

        assert signal._initial == 0
        assert hydrated._initial == 123

    def test_persisted_fallback_to_original(self):
        """Test that missing key in dict uses original initial value."""
        signal = Signal("username", "default_user")
        persisted_dict = {"other_key": "other_value"}

        hydrated = signal.persisted(persisted_dict)

        assert hydrated._initial == "default_user"

    def test_persisted_with_empty_dict(self):
        """Test that empty dict results in original initial value."""
        signal = Signal("count", 42)
        hydrated = signal.persisted({})

        assert hydrated._initial == 42

    def test_persisted_none_in_dict_is_used(self):
        """Test that None value in dict is used (not treated as missing)."""
        signal = Signal("optional", "default")
        persisted_dict = {"optional": None}

        hydrated = signal.persisted(persisted_dict)

        assert hydrated._initial is None

    def test_persisted_zero_value_in_dict_is_used(self):
        """Test that falsy values (0, False) in dict are used."""
        signal_int = Signal("count", 10)
        persisted_dict_int = {"count": 0}
        hydrated_int = signal_int.persisted(persisted_dict_int)
        assert hydrated_int._initial == 0

        signal_bool = Signal("active", True)
        persisted_dict_bool = {"active": False}
        hydrated_bool = signal_bool.persisted(persisted_dict_bool)
        assert hydrated_bool._initial is False

    def test_persisted_preserves_all_other_fields(self):
        """Test that persisted preserves name, type, namespace, ifmissing, _ref_only."""
        original = Signal("setting", "original", ifmissing=False, type_=str, namespace="app", _ref_only=True)
        persisted_dict = {"setting": "hydrated"}

        hydrated = original.persisted(persisted_dict)

        # Check all fields
        assert hydrated._name == "setting"
        assert hydrated.type_ is str
        assert hydrated._namespace == "app"
        assert hydrated._ifmissing is False
        assert hydrated._ref_only is True
        assert hydrated._initial == "hydrated"
        assert hydrated._id == "app_setting"

    def test_persisted_on_computed_raises_valueerror(self):
        """Test that persisted raises ValueError on computed signals (via with_initial)."""
        base = Signal("count", 5)
        computed = Signal("doubled", base * 2)
        persisted_dict = {"doubled": 10}

        with pytest.raises(ValueError) as exc_info:
            computed.persisted(persisted_dict)

        assert "Cannot call with_initial on computed signal" in str(exc_info.value)

    def test_persisted_with_namespaced_signal(self):
        """Test that persisted uses _name (unprefixed) as dict key, not _id."""
        # Namespaced signals have _id = "namespace_name"
        # but persisted() should lookup by _name only
        signal = Signal("left_open", False, namespace="drawer")
        assert signal._name == "left_open"
        assert signal._id == "drawer_left_open"

        # Dict keyed by _name, not _id
        persisted_dict = {"left_open": True}

        hydrated = signal.persisted(persisted_dict)

        assert hydrated._initial is True
        assert hydrated._namespace == "drawer"
        assert hydrated._id == "drawer_left_open"

    def test_persisted_with_namespaced_signal_missing_uses_original(self):
        """Test that missing namespaced key uses original initial."""
        signal = Signal("setting", "default", namespace="app")

        # Dict doesn't have the key
        persisted_dict = {}

        hydrated = signal.persisted(persisted_dict)

        assert hydrated._initial == "default"

    def test_persisted_returns_new_instance(self):
        """Test that persisted returns a new Signal instance."""
        original = Signal("count", 0)
        hydrated = original.persisted({"count": 10})

        assert original is not hydrated
        assert isinstance(hydrated, Signal)

    def test_persisted_with_complex_types(self):
        """Test persisted with lists and dicts."""
        original_list = Signal("items", [])
        hydrated_list = original_list.persisted({"items": [1, 2, 3]})
        assert hydrated_list._initial == [1, 2, 3]

        original_dict = Signal("config", {})
        hydrated_dict = original_dict.persisted({"config": {"theme": "dark"}})
        assert hydrated_dict._initial == {"theme": "dark"}

    def test_persisted_is_sugar_over_with_initial(self):
        """Test that persisted(dict) is equivalent to with_initial(dict.get(...))."""
        signal = Signal("value", 100)
        persisted_dict = {"value": 200}

        # Using persisted
        via_persisted = signal.persisted(persisted_dict)

        # Using with_initial directly
        via_with_initial = signal.with_initial(persisted_dict.get("value", signal._initial))

        assert via_persisted._initial == via_with_initial._initial
        assert via_persisted._name == via_with_initial._name
        assert via_persisted._namespace == via_with_initial._namespace

    def test_persisted_multiple_signals_from_session(self):
        """Test real-world scenario: hydrating multiple signals from session dict."""
        # Simulating a drawer state persisted in session
        session_state = {
            "left_open": True,
            "right_open": False,
            "width": 250,
        }

        left = Signal("left_open", False, namespace="drawer")
        right = Signal("right_open", False, namespace="drawer")
        width = Signal("width", 200, namespace="drawer")

        # Hydrate all from session
        left_hydrated = left.persisted(session_state)
        right_hydrated = right.persisted(session_state)
        width_hydrated = width.persisted(session_state)

        assert left_hydrated._initial is True
        assert right_hydrated._initial is False
        assert width_hydrated._initial == 250

    def test_persisted_extra_keys_in_dict_ignored(self):
        """Test that extra keys in dict don't affect signal hydration."""
        signal = Signal("user_id", 0)
        persisted_dict = {
            "user_id": 42,
            "extra_key": "extra_value",
            "another_key": 999,
        }

        hydrated = signal.persisted(persisted_dict)

        assert hydrated._initial == 42


class TestWithInitialAndPersistedIntegration:
    """Integration tests combining both methods."""

    def test_with_initial_then_persisted(self):
        """Test chaining with_initial followed by persisted."""
        original = Signal("count", 0)

        # First modify initial
        updated = original.with_initial(10)

        # Then hydrate from dict
        persisted_dict = {"count": 42}
        hydrated = updated.persisted(persisted_dict)

        assert original._initial == 0
        assert updated._initial == 10
        assert hydrated._initial == 42

    def test_persisted_then_with_initial(self):
        """Test chaining persisted followed by with_initial."""
        original = Signal("value", 0)
        persisted_dict = {"value": 100}

        # First hydrate from dict
        hydrated = original.persisted(persisted_dict)
        assert hydrated._initial == 100

        # Then further modify
        modified = hydrated.with_initial(200)
        assert modified._initial == 200

    def test_multiple_persisted_calls_independent(self):
        """Test that calling persisted multiple times is independent."""
        signal = Signal("state", "initial")

        dict1 = {"state": "from_dict1"}
        hydrated1 = signal.persisted(dict1)

        dict2 = {"state": "from_dict2"}
        hydrated2 = signal.persisted(dict2)

        # Both should be independent
        assert hydrated1._initial == "from_dict1"
        assert hydrated2._initial == "from_dict2"
        assert signal._initial == "initial"

    def test_validation_workflow_with_persisted(self):
        """Test real-world validation workflow with persisted hydration."""
        # Original signal with no initial (to validate against)
        email = Signal("email", "")

        # User submits form; we get their current value from request
        form_data = {"email": "user@example.com"}
        hydrated = email.persisted(form_data)

        # Then we apply validation rules (which sets _constraint_attrs)
        hydrated.validate(lambda sig: sig.length > 0, event="input")

        # The new instance's constraint attrs should now be set
        assert len(hydrated._constraint_attrs) > 0
        # But the original should be unaffected
        assert len(email._constraint_attrs) == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
