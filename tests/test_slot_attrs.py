"""Tests for the slot_attrs feature in StarHTML."""

from fastcore.xml import to_xml

from starhtml.datastar import DatastarAttr, ds_bind, ds_class, ds_show, slot_attrs, toggle_class
from starhtml.tags import Button, Div, Form, Input, Label, Span


class TestSlotAttrsBasic:
    """Basic slot_attrs functionality tests."""

    def test_single_slot_with_toggle_class(self):
        """Test applying toggle_class to a single slotted element."""
        element = Div(Label("Task", data_slot="label"), slot_attrs={"label": toggle_class("done", "line-through", "")})

        html = to_xml(element)
        assert 'data-slot="label"' in html
        assert "data-attr-class=" in html
        assert "$done" in html
        assert "line-through" in html

    def test_multiple_slots_different_attrs(self):
        """Test applying different attributes to multiple slots."""
        element = Div(
            Label("Title", data_slot="label"),
            Span("Content", data_slot="content"),
            slot_attrs={"label": toggle_class("active", "font-bold", ""), "content": ds_show("$visible")},
        )

        html = to_xml(element)
        assert 'data-slot="label"' in html
        assert 'data-slot="content"' in html
        assert "data-attr-class=" in html
        assert "$active" in html
        assert 'data-show="$visible"' in html

    def test_nested_elements_with_slots(self):
        """Test slot_attrs applies recursively to nested elements."""
        element = Div(
            Div(Span(Label("Nested", data_slot="label"))),
            slot_attrs={"label": toggle_class("highlight", "bg-yellow", "")},
        )

        html = to_xml(element)
        assert 'data-slot="label"' in html
        assert "data-attr-class=" in html
        assert "$highlight" in html

    def test_multiple_elements_same_slot(self):
        """Test that all elements with the same slot name receive attributes."""
        element = Div(
            Label("First", data_slot="label"),
            Label("Second", data_slot="label"),
            slot_attrs={"label": toggle_class("active", "underline", "")},
        )

        html = to_xml(element)
        # Count occurrences of the attribute
        count = html.count("data-attr-class=")
        assert count == 2, f"Expected 2 occurrences, found {count}"
        assert "$active" in html

    def test_slot_attrs_with_base_classes(self):
        """Test toggle_class with base classes in slot_attrs."""
        element = Div(
            Label("Text", data_slot="label", cls="text-sm"),
            slot_attrs={"label": toggle_class("important", "font-bold", "", base="text-gray-700")},
        )

        html = to_xml(element)
        assert 'cls="text-sm"' in html or 'class="text-sm"' in html
        assert "text-gray-700" in html
        assert "font-bold" in html


class TestSlotAttrsEdgeCases:
    """Edge cases and complex scenarios for slot_attrs."""

    def test_direct_attrs_take_precedence(self):
        """Test that direct attributes on elements take precedence over slot_attrs."""
        element = Div(
            Label("Text", data_slot="label", **toggle_class("local", "text-red", "text-blue").attrs),
            slot_attrs={"label": toggle_class("global", "text-green", "text-yellow")},
        )

        html = to_xml(element)
        # Should have the local toggle_class, not the global one
        assert "$local" in html
        assert "$global" not in html
        assert "text-red" in html
        assert "text-green" not in html

    def test_list_of_attrs_for_single_slot(self):
        """Test applying multiple attributes to a single slot."""
        element = Div(
            Button("Click", data_slot="button"),
            slot_attrs={
                "button": [
                    toggle_class("active", "bg-blue-500", "bg-gray-300"),
                    ds_show("$enabled"),
                    ds_class(hover="bg-blue-600"),
                ]
            },
        )

        html = to_xml(element)
        assert "data-attr-class=" in html
        assert "$active" in html
        assert 'data-show="$enabled"' in html
        assert 'data-class-hover="bg-blue-600"' in html

    def test_nonexistent_slot_ignored(self):
        """Test that slot_attrs for non-existent slots are ignored."""
        element = Div(
            Label("Text", data_slot="label"),
            slot_attrs={"label": toggle_class("active", "bold", ""), "nonexistent": ds_show("$never")},
        )

        html = to_xml(element)
        assert "data-attr-class=" in html
        assert "$active" in html
        assert "$never" not in html

    def test_empty_slot_attrs(self):
        """Test that empty slot_attrs doesn't break anything."""
        element = Div(Label("Text", data_slot="label"), slot_attrs={})

        html = to_xml(element)
        assert 'data-slot="label"' in html
        # Should render normally without any additional attributes

    def test_none_slot_attrs(self):
        """Test that None slot_attrs is handled gracefully."""
        element = Div(Label("Text", data_slot="label"), slot_attrs=None)

        html = to_xml(element)
        assert 'data-slot="label"' in html

    def test_slot_attrs_not_in_output(self):
        """Test that slot_attrs itself doesn't appear in the HTML output."""
        element = Div(Label("Text", data_slot="label"), slot_attrs={"label": ds_show("$visible")})

        html = to_xml(element)
        assert "slot_attrs" not in html
        assert "slot-attrs" not in html


class TestSlotAttrsWithDatastar:
    """Test slot_attrs with various Datastar attributes."""

    def test_with_ds_show(self):
        """Test slot_attrs with ds_show."""
        element = Div(Span("Hidden", data_slot="content"), slot_attrs={"content": ds_show("$isVisible")})

        html = to_xml(element)
        assert 'data-show="$isVisible"' in html

    def test_with_ds_bind(self):
        """Test slot_attrs with ds_bind."""
        element = Form(Input(data_slot="input"), slot_attrs={"input": ds_bind("username")})

        html = to_xml(element)
        assert 'data-bind="username"' in html

    def test_with_ds_class(self):
        """Test slot_attrs with ds_class."""
        element = Div(
            Button("Submit", data_slot="button"),
            slot_attrs={"button": ds_class(active="bg-green-500", disabled="bg-gray-300")},
        )

        html = to_xml(element)
        assert 'data-class-active="bg-green-500"' in html
        assert 'data-class-disabled="bg-gray-300"' in html

    def test_with_custom_datastar_attr(self):
        """Test slot_attrs with custom DatastarAttr."""
        custom_attr = DatastarAttr({"data-custom": "value"})
        element = Div(Span("Text", data_slot="span"), slot_attrs={"span": custom_attr})

        html = to_xml(element)
        assert 'data-custom="value"' in html


class TestSlotAttrsRealWorldScenarios:
    """Real-world component scenarios using slot_attrs."""

    def test_checkbox_with_label_component(self):
        """Test a realistic checkbox component with slot_attrs."""

        def CheckboxWithLabel(label, signal=None, slot_attrs=None, **kwargs):
            return Div(
                Input(type="checkbox", data_slot="checkbox"),
                Label(label, data_slot="label"),
                slot_attrs=slot_attrs,
                **kwargs,
            )

        component = CheckboxWithLabel(
            label="Complete task",
            signal="task1",
            slot_attrs={"label": toggle_class("task1", "line-through text-gray-500", ""), "checkbox": ds_bind("task1")},
        )

        html = to_xml(component)
        assert 'data-slot="checkbox"' in html
        assert 'data-slot="label"' in html
        assert 'data-bind="task1"' in html
        assert "line-through" in html

    def test_dropdown_component(self):
        """Test a dropdown component with slot_attrs."""

        def Dropdown(trigger_text, content, slot_attrs=None):
            return Div(
                Button(trigger_text, data_slot="trigger"), Div(content, data_slot="content"), slot_attrs=slot_attrs
            )

        dropdown = Dropdown(
            trigger_text="Options",
            content="Menu items here",
            slot_attrs={"trigger": toggle_class("open", "rotate-180", ""), "content": ds_show("$open")},
        )

        html = to_xml(dropdown)
        assert 'data-slot="trigger"' in html
        assert 'data-slot="content"' in html
        assert "rotate-180" in html
        assert 'data-show="$open"' in html

    def test_form_with_multiple_inputs(self):
        """Test a form with multiple inputs using slot_attrs."""
        form = Form(
            Input(type="text", placeholder="Username", data_slot="username"),
            Input(type="email", placeholder="Email", data_slot="email"),
            Button("Submit", data_slot="submit"),
            slot_attrs={
                "username": ds_bind("form.username"),
                "email": ds_bind("form.email"),
                "submit": [toggle_class("loading", "opacity-50 cursor-wait", ""), ds_show("$formValid")],
            },
        )

        html = to_xml(form)
        assert 'data-bind="form.username"' in html
        assert 'data-bind="form.email"' in html
        assert "opacity-50 cursor-wait" in html
        assert 'data-show="$formValid"' in html


class TestSlotAttrsWithDictAttributes:
    """Test slot_attrs with plain dictionary attributes."""

    def test_dict_attributes(self):
        """Test slot_attrs with plain dictionary attributes."""
        element = Div(Span("Text", data_slot="span"), slot_attrs={"span": {"data-test": "value", "id": "my-span"}})

        html = to_xml(element)
        assert 'data-test="value"' in html
        assert 'id="my-span"' in html

    def test_mixed_datastar_and_dict(self):
        """Test slot_attrs with mixed DatastarAttr and dict attributes."""
        element = Div(
            Label("Text", data_slot="label"),
            slot_attrs={"label": [toggle_class("active", "bold", ""), {"data-custom": "value"}]},
        )

        html = to_xml(element)
        assert "data-attr-class=" in html
        assert "$active" in html
        assert 'data-custom="value"' in html


class TestSlotAttrsPositional:
    """Test the positional slot_attrs() helper pattern."""

    def test_positional_slot_attrs_basic(self):
        """Test using slot_attrs as a positional argument."""
        element = Div(
            slot_attrs(label=toggle_class("active", "bold", ""), input=ds_bind("name")),
            Label("Name", data_slot="label"),
            Input(data_slot="input"),
        )

        html = to_xml(element)
        assert 'data-slot="label"' in html
        assert 'data-slot="input"' in html
        assert "data-attr-class=" in html
        assert "$active" in html
        assert 'data-bind="name"' in html

    def test_positional_mixed_with_direct_attrs(self):
        """Test slot_attrs positional mixed with direct attributes."""
        element = Div(
            toggle_class("container", "bg-blue", ""),  # Direct on Div
            slot_attrs(label=toggle_class("required", "font-bold", ""), input=ds_bind("email")),
            Label("Email", data_slot="label"),
            Input(type="email", data_slot="input"),
            cls="form-group",
        )

        html = to_xml(element)
        # Container should have its own toggle_class
        assert html.count("data-attr-class=") == 2
        assert "$container" in html
        assert "$required" in html
        assert 'data-bind="email"' in html

    def test_positional_with_multiple_attrs_per_slot(self):
        """Test positional slot_attrs with arrays of attributes."""
        element = Div(
            slot_attrs(
                button=[toggle_class("loading", "opacity-50", ""), ds_show("$enabled"), ds_class(hover="bg-blue-600")]
            ),
            Button("Submit", data_slot="button"),
        )

        html = to_xml(element)
        assert "data-attr-class=" in html
        assert "$loading" in html
        assert 'data-show="$enabled"' in html
        assert 'data-class-hover="bg-blue-600"' in html

    def test_both_positional_and_kwarg_patterns(self):
        """Test that both patterns work in the same codebase."""
        # Positional pattern
        elem1 = Div(slot_attrs(label=ds_show("$visible")), Label("Positional", data_slot="label"))

        # Kwarg pattern (original)
        elem2 = Div(Label("Kwarg", data_slot="label"), slot_attrs={"label": ds_show("$visible")})

        html1 = to_xml(elem1)
        html2 = to_xml(elem2)

        # Both should produce the same slot attribute
        assert 'data-show="$visible"' in html1
        assert 'data-show="$visible"' in html2

    def test_positional_in_component_function(self):
        """Test using positional slot_attrs in a component function."""

        def FormField(label, name, field_attrs=None):
            children = [
                Label(label, data_slot="label"),
                Input(name=name, data_slot="input"),
                Span("", data_slot="error"),
            ]
            if field_attrs:
                children.insert(0, field_attrs)
            return Div(*children, cls="form-field")

        component = FormField(
            "Username", "username", field_attrs=slot_attrs(input=ds_bind("username"), error=ds_show("$usernameError"))
        )

        html = to_xml(component)
        assert 'data-bind="username"' in html
        assert 'data-show="$usernameError"' in html

    def test_positional_overwrites_kwarg(self):
        """Test that positional slot_attrs takes precedence over kwarg."""
        element = Div(
            slot_attrs(label=toggle_class("pos", "bold", "")),
            Label("Test", data_slot="label"),
            slot_attrs={"label": toggle_class("kwarg", "italic", "")},
        )

        html = to_xml(element)
        # Positional should override kwarg
        assert "$pos" in html
        assert "$kwarg" not in html
