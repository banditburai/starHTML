"""Comprehensive behavioral tests for datastar kwargs processing.

These tests verify the BEHAVIOR of kwargs processing, not implementation details.
They test that flattened syntax (data_class_hover_blue="$active") and dict syntax
(data_class={"hover_blue": "$active"}) both produce valid Datastar attributes.

Key principles:
- Test behavior, not implementation
- Focus on what works from a user perspective
- Avoid asserting exact JavaScript output strings where possible
"""

from fastcore.xml import NotStr

from starhtml.datastar import Signal, js, process_datastar_kwargs


class TestFlattenedSyntaxBehavior:
    """Test that flattened syntax produces valid Datastar attributes."""

    def test_flattened_class_normalizes_key_correctly(self):
        """data_class_hover_blue_500 should normalize to data-class:* format (RC6 colon syntax)."""
        kwargs = {"data_class_hover_blue_500": "active"}
        processed, _ = process_datastar_kwargs(kwargs)

        assert "data-class:hover-blue-500" in processed

    def test_flattened_class_with_signal_collects_signal(self):
        """Using a Signal in flattened data_class should collect that signal."""
        selected = Signal("selected", False)
        kwargs = {"data_class_active": selected}
        _, signals = process_datastar_kwargs(kwargs)

        assert selected in signals
        assert len(signals) == 1

    def test_flattened_class_with_expression_generates_javascript(self):
        """Signal expressions should generate JavaScript code."""
        selected = Signal("selected", False)
        kwargs = {"data_class_active": ~selected}
        processed, signals = process_datastar_kwargs(kwargs)

        value = str(processed["data-class:active"])  # RC6 colon syntax
        assert "$selected" in value or "selected" in value
        assert selected in signals

    def test_flattened_class_preserves_string_values(self):
        """Plain string values should not be JSON-encoded."""
        kwargs = {"data_class_active": "bg-blue-500"}
        processed, _ = process_datastar_kwargs(kwargs)

        # Should NOT wrap in quotes
        assert processed["data-class:active"] == "bg-blue-500"

    def test_flattened_class_preserves_js_expressions(self):
        """JavaScript expression strings starting with $ should pass through."""
        kwargs = {"data_class_active": "$isActive"}
        processed, _ = process_datastar_kwargs(kwargs)

        assert processed["data-class:active"] == "$isActive"

    def test_flattened_style_normalizes_key_correctly(self):
        """data_style_background_color should normalize to data-style:background-color (RC6 colon syntax)."""
        kwargs = {"data_style_background_color": "red"}
        processed, _ = process_datastar_kwargs(kwargs)

        assert "data-style:background-color" in processed

    def test_flattened_style_preserves_string_values(self):
        """Style string values should not be JSON-encoded."""
        kwargs = {"data_style_color": "red"}
        processed, _ = process_datastar_kwargs(kwargs)

        assert processed["data-style:color"] == "red"

    def test_flattened_style_with_signal_works(self):
        """Using Signals in flattened data_style should work."""
        color = Signal("color", "blue")
        kwargs = {"data_style_color": color}
        processed, signals = process_datastar_kwargs(kwargs)

        assert "data-style:color" in processed
        assert color in signals

    def test_flattened_attr_normalizes_key_correctly(self):
        """data_attr_disabled should normalize to data-attr:disabled (RC6 colon syntax)."""
        kwargs = {"data_attr_disabled": "true"}
        processed, _ = process_datastar_kwargs(kwargs)

        assert "data-attr:disabled" in processed

    def test_flattened_attr_with_signal_collects_signal(self):
        """Using Signals in flattened data_attr should collect the signal."""
        disabled = Signal("disabled", False)
        kwargs = {"data_attr_disabled": disabled}
        _, signals = process_datastar_kwargs(kwargs)

        assert disabled in signals

    def test_multiple_flattened_attributes_all_process(self):
        """Multiple flattened attributes should all be processed."""
        active = Signal("active", False)
        loading = Signal("loading", False)

        kwargs = {
            "data_class_bg_blue": active,
            "data_style_color": "red",
            "data_attr_title": "Test",
        }
        processed, signals = process_datastar_kwargs(kwargs)

        assert "data-class:bg-blue" in processed
        assert "data-style:color" in processed
        assert "data-attr:title" in processed
        assert active in signals


class TestDictSyntaxBehavior:
    """Test that dict syntax produces valid Datastar attributes."""

    def test_dict_class_creates_data_class_attribute(self):
        """data_class dict should create a data-class attribute."""
        kwargs = {"data_class": {"active": "bg-blue"}}
        processed, _ = process_datastar_kwargs(kwargs)

        assert "data-class" in processed
        assert isinstance(processed["data-class"], str | NotStr)

    def test_dict_class_with_signal_works(self):
        """data_class dict can contain Signals."""
        selected = Signal("selected", False)
        kwargs = {"data_class": {"active": selected}}
        processed, _ = process_datastar_kwargs(kwargs)

        assert "data-class" in processed
        # Dict syntax produces a JS object, not individual keys

    def test_dict_style_creates_data_style_attribute(self):
        """data_style dict should create a data-style attribute."""
        kwargs = {"data_style": {"color": "red"}}
        processed, _ = process_datastar_kwargs(kwargs)

        assert "data-style" in processed

    def test_dict_attr_creates_data_attr_attribute(self):
        """data_attr dict should create a data-attr attribute."""
        kwargs = {"data_attr": {"title": "Test"}}
        processed, _ = process_datastar_kwargs(kwargs)

        assert "data-attr" in processed


class TestKeyNormalization:
    """Test that keys are normalized correctly."""

    def test_underscores_become_hyphens_in_class_keys(self):
        """data_class_hover_blue_500 → data-class:hover-blue-500."""
        kwargs = {"data_class_hover_blue_500": "active"}
        processed, _ = process_datastar_kwargs(kwargs)

        assert "data-class:hover-blue-500" in processed
        assert "data_class_hover_blue_500" not in processed

    def test_underscores_become_hyphens_in_style_keys(self):
        """data_style_background_color → data-style:background-color (RC6 colon syntax)."""
        kwargs = {"data_style_background_color": "red"}
        processed, _ = process_datastar_kwargs(kwargs)

        assert "data-style:background-color" in processed

    def test_underscores_become_hyphens_in_attr_keys(self):
        """data_attr_aria_label → data-attr:aria-label (RC6 colon syntax)."""
        kwargs = {"data_attr_aria_label": "Help"}
        processed, _ = process_datastar_kwargs(kwargs)

        assert "data-attr:aria-label" in processed

    def test_data_computed_preserves_case_after_prefix(self):
        """data_computed_fullName should preserve the camelCase part (RC6 colon syntax)."""
        kwargs = {"data_computed_fullName": js("$first + $last")}
        processed, _ = process_datastar_kwargs(kwargs)

        # The prefix becomes data-computed:, and the name part is preserved
        assert "data-computed:fullName" in processed


class TestSignalCollection:
    """Test that Signals are collected correctly from expressions."""

    def test_simple_signal_is_collected(self):
        """A bare Signal should be collected."""
        count = Signal("count", 0)
        kwargs = {"data_class_visible": count}
        _, signals = process_datastar_kwargs(kwargs)

        assert count in signals

    def test_signal_in_expression_is_collected(self):
        """Signals inside expressions should be collected."""
        count = Signal("count", 0)
        kwargs = {"data_show": count > 5}
        _, signals = process_datastar_kwargs(kwargs)

        assert count in signals

    def test_multiple_signals_are_all_collected(self):
        """All signals in different attrs should be collected."""
        active = Signal("active", False)
        count = Signal("count", 0)
        loading = Signal("loading", False)

        kwargs = {
            "data_class_active": active,
            "data_show": count > 0,
            "data_bind": loading,
        }
        _, signals = process_datastar_kwargs(kwargs)

        assert active in signals
        assert count in signals
        assert loading in signals
        assert len(signals) == 3

    def test_string_values_dont_create_signals(self):
        """String values like '$active' should not create Signal objects."""
        kwargs = {"data_class_active": "$active"}
        _, signals = process_datastar_kwargs(kwargs)

        assert len(signals) == 0


class TestSpecialDataAttributes:
    """Test special Datastar attributes like data_bind, data_ref."""

    def test_data_bind_uses_signal_id(self):
        """data_bind with a Signal should use the signal's id, not full JS."""
        username = Signal("username", "")
        kwargs = {"data_bind": username}
        processed, _ = process_datastar_kwargs(kwargs)

        assert processed["data-bind"] == "username"

    def test_data_ref_uses_signal_id(self):
        """data_ref with a Signal should use the signal's id."""
        my_ref = Signal("my_ref", None)
        kwargs = {"data_ref": my_ref}
        processed, _ = process_datastar_kwargs(kwargs)

        assert processed["data-ref"] == "my_ref"

    def test_data_indicator_uses_signal_id(self):
        """data_indicator with a Signal should use the signal's id."""
        loading = Signal("loading", False)
        kwargs = {"data_indicator": loading}
        processed, _ = process_datastar_kwargs(kwargs)

        assert processed["data-indicator"] == "loading"

    def test_data_class_expr_not_dict_generates_javascript(self):
        """data_class with an Expr (not dict) should generate JavaScript."""
        active = Signal("active", False)
        kwargs = {"data_class": active}
        processed, _ = process_datastar_kwargs(kwargs)

        # When data_class is an Expr, it goes to data-class attribute
        assert "data-class" in processed


class TestEventModifiers:
    """Test that event modifiers work correctly."""

    def test_event_with_prevent_modifier(self):
        """Event with prevent modifier should add __prevent to key."""
        kwargs = {"data_on_click": ("doSomething()", {"prevent": True})}
        processed, _ = process_datastar_kwargs(kwargs)

        # Should have prevent in the key
        found_key = [k for k in processed if "prevent" in k]
        assert len(found_key) == 1

    def test_event_with_debounce_modifier(self):
        """Event with debounce should add __debounce to key."""
        kwargs = {"data_on_input": ("search()", {"debounce": "300ms"})}
        processed, _ = process_datastar_kwargs(kwargs)

        found_key = [k for k in processed if "debounce" in k]
        assert len(found_key) == 1


class TestNonDatastarAttributes:
    """Test that non-Datastar attributes pass through unchanged."""

    def test_regular_html_attributes_passthrough(self):
        """Regular HTML attributes should not be modified."""
        kwargs = {
            "id": "my-element",
            "class": "container",
            "aria_label": "Help",
            "data_class_active": "$active",
        }
        processed, _ = process_datastar_kwargs(kwargs)

        assert processed["id"] == "my-element"
        assert processed["class"] == "container"
        assert processed["aria_label"] == "Help"
        assert "data-class:active" in processed

    def test_mixed_datastar_and_regular_attrs(self):
        """Mix of Datastar and regular attrs should all process correctly."""
        count = Signal("count", 0)
        kwargs = {
            "id": "counter",
            "data_bind": count,
            "class": "btn",
            "data_class_active": count > 0,
        }
        processed, signals = process_datastar_kwargs(kwargs)

        assert processed["id"] == "counter"
        assert processed["class"] == "btn"
        assert "data-bind" in processed
        assert "data-class:active" in processed
        assert count in signals


class TestRealWorldUseCases:
    """Test realistic usage patterns."""

    def test_interactive_button(self):
        """Button with multiple reactive states."""
        loading = Signal("loading", False)
        disabled = Signal("disabled", False)

        kwargs = {
            "data_class_opacity_50": loading,
            "data_class_cursor_not_allowed": disabled,
            "data_attr_disabled": disabled | loading,
            "data_on_click": ("submit()", {"prevent": True}),
        }
        processed, signals = process_datastar_kwargs(kwargs)

        # All attributes should be present (RC6 colon syntax)
        assert "data-class:opacity-50" in processed
        assert "data-class:cursor-not-allowed" in processed
        assert "data-attr:disabled" in processed

        # Both signals should be collected
        assert loading in signals
        assert disabled in signals

    def test_form_input_with_validation(self):
        """Form input with validation states."""
        error = Signal("error", "")
        value = Signal("value", "")

        kwargs = {
            "data_bind": value,
            "data_class_border_red": error,
            "data_style_border_color": "$error ? 'red' : 'gray'",
        }
        processed, signals = process_datastar_kwargs(kwargs)

        assert processed["data-bind"] == "value"
        assert "data-class:border-red" in processed
        assert "data-style:border-color" in processed
        assert value in signals
        assert error in signals

    def test_conditional_visibility(self):
        """Element with conditional visibility."""
        show = Signal("show", True)
        count = Signal("count", 0)

        kwargs = {
            "data_show": show,
            "data_class_hidden": ~show,
            "data_text": count,
        }
        processed, signals = process_datastar_kwargs(kwargs)

        assert "data-show" in processed
        assert "data-class:hidden" in processed
        assert "data-text" in processed
        assert show in signals
        assert count in signals


class TestEdgeCases:
    """Test edge cases and special values."""

    def test_empty_string_values(self):
        """Empty strings should be preserved."""
        kwargs = {"data_class_hidden": ""}
        processed, _ = process_datastar_kwargs(kwargs)

        assert processed["data-class:hidden"] == ""

    def test_numeric_values_convert_to_notstr(self):
        """Numeric values should be wrapped in NotStr."""
        kwargs = {"data_style_opacity": 0.5}
        processed, _ = process_datastar_kwargs(kwargs)

        assert "data-style:opacity" in processed
        assert isinstance(processed["data-style:opacity"], NotStr)

    def test_boolean_values_work(self):
        """Boolean values should be handled."""
        kwargs = {"data_class_active": True}
        processed, _ = process_datastar_kwargs(kwargs)

        assert "data-class:active" in processed

    def test_list_values_for_event_handlers(self):
        """List values should work for event handlers."""
        action1 = js("console.log('a')")
        action2 = js("console.log('b')")
        kwargs = {"data_on_click": [action1, action2]}
        processed, _ = process_datastar_kwargs(kwargs)

        assert "data-on:click" in processed


class TestConsistency:
    """Test consistency and correctness of the processing."""

    def test_flattened_and_dict_both_produce_output(self):
        """Both flattened and dict syntax should produce valid output."""
        selected = Signal("selected", False)

        # Flattened
        kwargs1 = {"data_class_active": selected}
        processed1, signals1 = process_datastar_kwargs(kwargs1)

        # Dict
        kwargs2 = {"data_class": {"active": selected}}
        processed2, signals2 = process_datastar_kwargs(kwargs2)

        # Both should have output
        assert len(processed1) > 0
        assert len(processed2) > 0

        # Flattened should collect the signal
        assert selected in signals1

    def test_string_values_not_json_encoded(self):
        """Plain string CSS classes should not be JSON-encoded."""
        kwargs = {"data_class_active": "bg-blue-500"}
        processed, _ = process_datastar_kwargs(kwargs)

        # Should be plain string, not JSON string with quotes
        value = processed["data-class:active"]
        assert value == "bg-blue-500"
        assert not value.startswith('"')

    def test_signal_expressions_generate_javascript(self):
        """Signal expressions should compile to JavaScript."""
        count = Signal("count", 0)
        kwargs = {"data_show": count > 5}
        processed, _ = process_datastar_kwargs(kwargs)

        # The value should contain JavaScript-like syntax
        value = str(processed["data-show"])
        assert "$count" in value or "count" in value
        assert ">" in value

    def test_processed_values_are_notstr_where_needed(self):
        """JavaScript expressions should be wrapped in NotStr."""
        count = Signal("count", 0)
        kwargs = {"data_show": count > 0}
        processed, _ = process_datastar_kwargs(kwargs)

        assert isinstance(processed["data-show"], NotStr)


class TestDictWrappingFix:
    """Test that dicts in data_* attributes are NOT wrapped in parens."""

    def test_data_class_dict_no_parens(self):
        """data_class dict should produce object literal WITHOUT parens."""
        active = Signal("active", False)
        kwargs = {"data_class": {"text-muted": ~active}}
        processed, signals = process_datastar_kwargs(kwargs)

        value = str(processed["data-class"])
        assert not value.startswith("(")
        assert not value.endswith(")")
        assert "text-muted" in value
        assert active in signals

    def test_data_style_dict_no_parens(self):
        """data_style dict should produce object literal WITHOUT parens."""
        width = Signal("width", 100)
        kwargs = {"data_style": {"width": width + "px"}}
        processed, signals = process_datastar_kwargs(kwargs)

        value = str(processed["data-style"])
        assert not value.startswith("(")
        assert not value.endswith(")")
        assert width in signals

    def test_data_attr_dict_no_parens(self):
        """data_attr dict should produce object literal WITHOUT parens."""
        disabled = Signal("disabled", False)
        kwargs = {"data_attr": {"disabled": disabled}}
        processed, signals = process_datastar_kwargs(kwargs)

        value = str(processed["data-attr"])
        assert not value.startswith("(")
        assert not value.endswith(")")
        assert disabled in signals

    def test_non_data_dict_has_parens(self):
        """Non-data-* dicts should STILL have parens for backward compatibility."""
        sig = Signal("test", "value")
        kwargs = {"custom_attr": {"key": sig}}
        processed, signals = process_datastar_kwargs(kwargs)

        value = str(processed["custom-attr"])
        assert value.startswith("(")
        assert value.endswith(")")
        assert sig in signals

    def test_data_class_dict_with_hyphenated_keys(self):
        """data_class dict handles hyphenated class names correctly."""
        selected = Signal("selected", True)
        kwargs = {"data_class": {"text-muted-foreground": ~selected, "bg-primary": selected}}
        processed, signals = process_datastar_kwargs(kwargs)

        value = str(processed["data-class"])
        assert "text-muted-foreground" in value
        assert "bg-primary" in value
        assert not value.startswith("(")
        assert selected in signals

    def test_data_style_dict_with_multiple_properties(self):
        """data_style dict with multiple CSS properties."""
        width = Signal("width", 100)
        height = Signal("height", 50)
        kwargs = {"data_style": {"width": width + "px", "height": height + "px"}}
        processed, signals = process_datastar_kwargs(kwargs)

        value = str(processed["data-style"])
        assert "width" in value
        assert "height" in value
        assert not value.startswith("(")
        assert width in signals
        assert height in signals

    def test_data_attr_dict_with_mixed_values(self):
        """data_attr dict with signals and static values."""
        disabled = Signal("disabled", False)
        kwargs = {"data_attr": {"disabled": disabled, "aria-label": "Click me"}}
        processed, signals = process_datastar_kwargs(kwargs)

        value = str(processed["data-attr"])
        assert "disabled" in value
        assert "aria-label" in value
        assert not value.startswith("(")
        assert disabled in signals

    def test_dict_signals_are_collected(self):
        """Signals nested in dicts should be collected."""
        active = Signal("active", True)
        disabled = Signal("disabled", False)
        kwargs = {"data_class": {"active": active, "disabled": ~disabled}}
        _, signals = process_datastar_kwargs(kwargs)

        assert active in signals
        assert disabled in signals
        assert len(signals) == 2


class TestAdditiveClassBehavior:
    """Test that cls + data_attr_cls merge into data-attr:class correctly (RC6 colon syntax)."""

    def test_cls_and_data_attr_cls_merge(self):
        """When both cls and data_attr_cls are present, they merge into data-attr:class."""
        active = Signal("active", True)
        kwargs = {"cls": "base-class", "data_attr_cls": active}
        processed, signals = process_datastar_kwargs(kwargs)

        # Should NOT have separate cls and data-attr:cls
        assert "cls" not in processed
        assert "data-attr:cls" not in processed

        # Should have merged data-attr:class
        assert "data-attr:class" in processed

        # Value should be a template literal combining both
        value = str(processed["data-attr:class"])
        assert "base-class" in value
        assert "$active" in value

        # Signal should be collected
        assert active in signals

    def test_cls_and_data_attr_cls_merge_with_expression(self):
        """Complex expressions in data_attr_cls should merge correctly."""
        active = Signal("active", True)
        loading = Signal("loading", False)
        kwargs = {"cls": "btn btn-primary", "data_attr_cls": active.if_("active", "inactive")}
        processed, signals = process_datastar_kwargs(kwargs)

        assert "data-attr:class" in processed
        value = str(processed["data-attr:class"])
        assert "btn btn-primary" in value

        assert active in signals

    def test_cls_only_passes_through(self):
        """When only cls is present (no data_attr_cls), it should pass through."""
        kwargs = {"cls": "static-class"}
        processed, _ = process_datastar_kwargs(kwargs)

        assert processed["cls"] == "static-class"
        assert "data-attr:class" not in processed

    def test_data_attr_cls_only_stays_as_is(self):
        """When only data_attr_cls is present (no cls), it stays as data-attr:cls."""
        active = Signal("active", True)
        kwargs = {"data_attr_cls": active}
        processed, signals = process_datastar_kwargs(kwargs)

        # Should have data-attr:cls (RC6 syntax)
        assert "data-attr:cls" in processed
        # Should NOT merge since no static cls
        assert "data-attr:class" not in processed

        assert active in signals

    def test_merged_class_preserves_ternary_expression(self):
        """Ternary expressions should have balanced parentheses."""
        active = Signal("active", True)
        kwargs = {"cls": "base", "data_attr_cls": active.if_("yes", "no")}
        processed, _ = process_datastar_kwargs(kwargs)

        value = str(processed["data-attr:class"])
        # Should be a valid template literal with base class
        assert value.startswith("`")
        assert "base" in value
        # Parentheses must be balanced (the bug was stripping opening paren)
        assert value.count("(") == value.count(")")

    def test_merge_produces_template_literal(self):
        """Merged result should be a JavaScript template literal."""
        mode = Signal("mode", "light")
        kwargs = {"cls": "theme", "data_attr_cls": mode}
        processed, _ = process_datastar_kwargs(kwargs)

        value = str(processed["data-attr:class"])
        # Should be a template literal: `theme ${$mode}`
        assert value.startswith("`")
        assert value.endswith("`")
        assert "${" in value
