"""Tests for the slot_attrs feature in StarHTML."""

from fastcore.xml import to_xml

from starhtml import *


class TestSlotAttrsBasic:
    """Basic slot_attrs functionality tests."""

    def test_single_slot_with_conditional_class(self):
        """Test applying conditional class to a single slotted element."""
        done = Signal("done", False)
        element = Div(Label("Task", data_slot="label"), slot_label={"data_attr_class": done.if_("line-through", "")})

        html = to_xml(element)
        assert 'data-slot="label"' in html
        assert "data-attr-class=" in html
        assert "$done" in html
        assert "line-through" in html

    def test_multiple_slots_different_attrs(self):
        """Test applying different attributes to multiple slots."""
        active = Signal("active", True)
        visible = Signal("visible", True)
        element = Div(
            Label("Title", data_slot="label"),
            Span("Content", data_slot="content"),
            slot_label={"data_attr_class": active.if_("font-bold", "")},
            slot_content={"data_show": visible},
        )

        html = to_xml(element)
        assert 'data-slot="label"' in html
        assert 'data-slot="content"' in html
        assert "data-attr-class=" in html
        assert "$active" in html
        assert 'data-show="$visible"' in html

    def test_nested_elements_with_slots(self):
        """Test slot_ kwargs applies recursively to nested elements."""
        highlight = Signal("highlight", False)
        element = Div(
            Div(Span(Label("Nested", data_slot="label"))),
            slot_label={"data_attr_class": highlight.if_("bg-yellow", "")},
        )

        html = to_xml(element)
        assert 'data-slot="label"' in html
        assert "data-attr-class=" in html
        assert "$highlight" in html

    def test_multiple_elements_same_slot(self):
        """Test that all elements with the same slot name receive attributes."""
        active = Signal("active", False)
        element = Div(
            Label("First", data_slot="label"),
            Label("Second", data_slot="label"),
            slot_label={"data_attr_class": active.if_("underline", "")},
        )

        html = to_xml(element)
        count = html.count("data-attr-class=")
        assert count == 2, f"Expected 2 occurrences, found {count}"
        assert "$active" in html

    def test_slot_attrs_with_base_classes(self):
        """Test conditional class with base classes using slot_ kwargs."""
        important = Signal("important", True)
        element = Div(
            Label("Text", data_slot="label", cls="text-sm"),
            slot_label={"data_attr_class": js("'text-gray-700 ' + ($important ? 'font-bold' : '')")},
        )

        html = to_xml(element)
        assert 'cls="text-sm"' in html or 'class="text-sm"' in html
        assert "text-gray-700" in html
        assert "font-bold" in html
        assert "$important" in html


class TestSlotAttrsEdgeCases:
    """Edge cases and complex scenarios for slot_attrs."""

    def test_direct_attrs_take_precedence(self):
        """Test that direct attributes on elements take precedence over slot_ kwargs."""
        local = Signal("local", True)
        global_sig = Signal("global", False)
        element = Div(
            Label("Text", data_slot="label", data_attr_class=local.if_("text-red", "text-blue")),
            slot_label={"data_attr_class": global_sig.if_("text-green", "text-yellow")},
        )

        html = to_xml(element)
        assert "$local" in html
        assert "$global" not in html
        assert "text-red" in html
        assert "text-blue" in html
        assert "text-green" not in html

    def test_list_of_attrs_for_single_slot(self):
        """Test applying multiple attributes to a single slot."""
        active = Signal("active", True)
        enabled = Signal("enabled", True)
        element = Div(
            Button("Click", data_slot="button"),
            slot_button={
                "data_attr_class": active.if_("bg-blue-500", "bg-gray-300"),
                "data_show": enabled,
                "data_class_hover": "bg-blue-600",
            },
        )

        html = to_xml(element)
        assert "data-attr-class=" in html
        assert "$active" in html
        assert 'data-show="$enabled"' in html
        assert 'data_class_hover="bg-blue-600"' in html

    def test_nonexistent_slot_ignored(self):
        """Test that slot_ kwargs for non-existent slots are ignored."""
        active = Signal("active", True)
        never = Signal("never", False)
        element = Div(
            Label("Text", data_slot="label"),
            slot_label={"data_attr_class": active.if_("bold", "")},
            slot_nonexistent={"data_show": never},
        )

        html = to_xml(element)
        assert "data-attr-class=" in html
        assert "$active" in html
        assert "$never" not in html

    def test_empty_slot_attrs(self):
        """Test that empty slot_ kwargs doesn't break anything."""
        element = Div(Label("Text", data_slot="label"), slot_label={})

        html = to_xml(element)
        assert 'data-slot="label"' in html

    def test_none_slot_attrs(self):
        """Test that omitting slot_ kwargs is handled gracefully."""
        element = Div(
            Label("Text", data_slot="label")
            # No slot_ kwargs at all
        )

        html = to_xml(element)
        assert 'data-slot="label"' in html

    def test_slot_attrs_not_in_output(self):
        """Test that slot_ kwargs themselves don't appear in the HTML output."""
        visible = Signal("visible", True)
        element = Div(Label("Text", data_slot="label"), slot_label={"data_show": visible})

        html = to_xml(element)
        assert "slot_attrs" not in html
        assert "slot-attrs" not in html


class TestSlotAttrsWithDatastar:
    """Test slot_attrs with various Datastar attributes."""

    def test_with_data_show(self):
        """Test slot_ kwargs with data-show."""
        is_visible = Signal("is_visible", True)
        element = Div(Span("Hidden", data_slot="content"), slot_content={"data_show": is_visible})

        html = to_xml(element)
        assert 'data-show="$is_visible"' in html

    def test_with_data_bind(self):
        """Test slot_ kwargs with data-bind."""
        username = Signal("username", "")
        element = Form(Input(data_slot="input"), slot_input={"data_bind": username})

        html = to_xml(element)
        assert 'data-bind="username"' in html

    def test_with_data_class(self):
        """Test slot_ kwargs with data-class."""
        element = Div(
            Button("Submit", data_slot="button"),
            slot_button={"data_class_active": "bg-green-500", "data_class_disabled": "bg-gray-300"},
        )

        html = to_xml(element)
        assert 'data_class_active="bg-green-500"' in html
        assert 'data_class_disabled="bg-gray-300"' in html

    def test_with_custom_datastar_attr(self):
        """Test slot_ kwargs with custom attrs dict."""
        element = Div(Span("Text", data_slot="span"), slot_span={"data_custom": "value"})

        html = to_xml(element)
        assert 'data_custom="value"' in html


class TestSlotAttrsRealWorldScenarios:
    """Real-world component scenarios using slot_attrs."""

    def test_checkbox_with_label_component(self):
        """Test a realistic checkbox component with slot_ kwargs."""

        def CheckboxWithLabel(label, signal_name=None, **kwargs):
            # Extract slot_ kwargs
            slot_checkbox = kwargs.pop("slot_checkbox", {})
            slot_label = kwargs.pop("slot_label", {})
            sig = Signal(signal_name, False) if signal_name else None
            return Div(
                Input(type="checkbox", data_slot="checkbox"),
                Label(label, data_slot="label"),
                slot_checkbox=slot_checkbox,
                slot_label=slot_label,
                **kwargs,
            )

        task1 = Signal("task1", False)
        component = CheckboxWithLabel(
            "Complete task",
            signal_name="task1",
            slot_label={"data_attr_class": task1.if_("line-through text-gray-500", "")},
            slot_checkbox={"data_bind": task1},
        )

        html = to_xml(component)
        assert 'data-slot="checkbox"' in html
        assert 'data-slot="label"' in html
        assert 'data-bind="task1"' in html
        assert "line-through" in html

    def test_dropdown_component(self):
        """Test a dropdown component with slot_ kwargs."""

        def Dropdown(trigger_text, content, **kwargs):
            # Extract slot_ kwargs
            slot_trigger = kwargs.pop("slot_trigger", {})
            slot_content = kwargs.pop("slot_content", {})
            return Div(
                Button(trigger_text, data_slot="trigger"),
                Div(content, data_slot="content"),
                slot_trigger=slot_trigger,
                slot_content=slot_content,
                **kwargs,
            )

        open_sig = Signal("open", False)
        dropdown = Dropdown(
            "Options",
            "Menu items here",
            slot_trigger={"data_attr_class": open_sig.if_("rotate-180", "")},
            slot_content={"data_show": open_sig},
        )

        html = to_xml(dropdown)
        assert 'data-slot="trigger"' in html
        assert 'data-slot="content"' in html
        assert "rotate-180" in html
        assert 'data-show="$open"' in html

    def test_form_with_multiple_inputs(self):
        """Test a form with multiple inputs using slot_ kwargs."""
        form_username = Signal("form_username", "")
        form_email = Signal("form_email", "")
        loading = Signal("loading", False)
        form_valid = Signal("form_valid", False)

        form = Form(
            Input(type="text", placeholder="Username", data_slot="username"),
            Input(type="email", placeholder="Email", data_slot="email"),
            Button("Submit", data_slot="submit"),
            slot_username={"data_bind": form_username},
            slot_email={"data_bind": form_email},
            slot_submit={"data_attr_class": loading.if_("opacity-50 cursor-wait", ""), "data_show": form_valid},
        )

        html = to_xml(form)
        assert 'data-bind="form_username"' in html
        assert 'data-bind="form_email"' in html
        assert "opacity-50 cursor-wait" in html
        assert 'data-show="$form_valid"' in html


class TestSlotAttrsWithDictAttributes:
    """Test slot_attrs with plain dictionary attributes."""

    def test_dict_attributes(self):
        """Test slot_ kwargs with plain dictionary attributes."""
        element = Div(Span("Text", data_slot="span"), slot_span={"data_test": "value", "id": "my-span"})

        html = to_xml(element)
        assert 'data_test="value"' in html
        assert 'id="my-span"' in html

    def test_mixed_datastar_and_dict(self):
        """Test slot_ kwargs with mixed datastar attrs and dict attributes."""
        active = Signal("active", True)
        element = Div(
            Label("Text", data_slot="label"),
            slot_label={"data_attr_class": active.if_("bold", ""), "data_custom": "value"},
        )

        html = to_xml(element)
        assert "data-attr-class=" in html
        assert "$active" in html
        assert 'data_custom="value"' in html


class TestSlotAttrsNormalization:
    """Test underscore to kebab-case normalization in slot_attrs."""

    def test_basic_underscore_normalization(self):
        """Test that underscores in slot names are converted to kebab-case."""
        disabled_partial = Signal("disabled_partial", False)
        element = Div(
            Button("X", data_slot="toggle-group-item"), slot_toggle_group_item={"data_attr_disabled": disabled_partial}
        )

        html = to_xml(element)
        assert 'data-slot="toggle-group-item"' in html
        assert 'data-attr-disabled="$disabled_partial"' in html

    def test_multiple_underscores_normalization(self):
        """Test normalization with multiple underscores."""
        active = Signal("active", False)
        visible = Signal("visible", True)
        element = Div(
            Span("Item 1", data_slot="my-complex-slot-name"),
            Span("Item 2", data_slot="another-long-name"),
            slot_my_complex_slot_name={"data_attr_class": active.if_("highlight", "")},
            slot_another_long_name={"data_show": visible},
        )

        html = to_xml(element)
        assert 'data-slot="my-complex-slot-name"' in html
        assert 'data-slot="another-long-name"' in html
        assert "$active" in html
        assert "$visible" in html

    def test_dict_with_kebab_case_still_works(self):
        """Test that passing a dict with kebab-case keys still works."""
        disabled = Signal("disabled", False)
        element = Div(
            Button("Y", data_slot="toggle-group-item"), slot_toggle_group_item={"data_attr_disabled": disabled}
        )

        html = to_xml(element)
        assert 'data-attr-disabled="$disabled"' in html

    def test_dict_with_underscores_normalized(self):
        """Test that dict keys with underscores are also normalized."""
        disabled = Signal("disabled", False)
        element = Div(
            Button("Z", data_slot="toggle-group-item"), slot_toggle_group_item={"data_attr_disabled": disabled}
        )

        html = to_xml(element)
        assert 'data-attr-disabled="$disabled"' in html

    def test_mixed_dict_and_kwargs(self):
        """Test that both dict and kwargs can be used together."""
        menu_visible = Signal("menu_visible", True)
        open_sig = Signal("open", False)
        element = Div(
            Span("Menu", data_slot="menu-item"),
            Button("Toggle", data_slot="toggle-button"),
            slot_menu_item={"data_show": menu_visible},
            slot_toggle_button={"data_attr_class": open_sig.if_("rotate-180", "")},
        )

        html = to_xml(element)
        assert 'data-show="$menu_visible"' in html
        assert "$open" in html
        assert "rotate-180" in html

    def test_no_underscores_unchanged(self):
        """Test that slot names without underscores remain unchanged."""
        visible = Signal("visible", True)
        action = Signal("action", "")
        element = Div(
            Label("Text", data_slot="label"),
            Button("Click", data_slot="button"),
            slot_label={"data_show": visible},
            slot_button={"data_bind": action},
        )

        html = to_xml(element)
        assert 'data-show="$visible"' in html
        assert 'data-bind="action"' in html

    def test_backward_compatibility_with_kwarg_pattern(self):
        """Test that the kwarg pattern (slot_attrs=dict) still works."""
        active = Signal("active", False)
        element = Div(
            Label("Old Style", data_slot="label-item"), slot_label_item={"data_attr_class": active.if_("bold", "")}
        )

        html = to_xml(element)
        assert "$active" in html
        assert "bold" in html

    def test_real_world_component_with_normalization(self):
        """Test a realistic component using underscore normalization."""

        def ToggleGroup(items, **kwargs):
            children = []
            for i, item in enumerate(items):
                children.append(Button(item, data_slot="toggle-group-item", data_item_id=str(i)))
            # Extract slot_ kwargs
            slot_toggle_group_item = kwargs.pop("slot_toggle_group_item", {})
            return Div(*children, slot_toggle_group_item=slot_toggle_group_item, cls="toggle-group", **kwargs)

        selected = Signal("selected", False)
        disabled_items = Signal("disabled_items", False)
        component = ToggleGroup(
            ["Option 1", "Option 2", "Option 3"],
            slot_toggle_group_item={
                "data_attr_class": selected.if_("bg-blue-500 text-white", "bg-gray-200"),
                "data_attr_disabled": disabled_items,
            },
        )

        html = to_xml(component)
        assert html.count('data-slot="toggle-group-item"') == 3
        assert "$selected" in html
        assert "bg-blue-500" in html
        assert 'data-attr-disabled="$disabled_items"' in html
