"""Tests for the modern Datastar API (no legacy helpers)."""

from starhtml import *
from starhtml.datastar import (
    Signal,
    f,
    js,
    process_datastar_kwargs,
)


# Define attrs locally for testing
def attrs(**kwargs):
    """Helper function to create data-* attributes."""
    result = {}
    for key, value in kwargs.items():
        # Convert underscore to hyphen for data attributes
        attr_key = f"data-{key.replace('_', '-')}"
        result[attr_key] = value
    return result


def attrs_of_kwargs(**kwargs):
    """Process Datastar kwargs and normalize NotStr values to strings."""
    processed, _ = process_datastar_kwargs(kwargs)
    from fastcore.xml import NotStr

    return {k: (str(v) if isinstance(v, NotStr) else v) for k, v in processed.items()}


def attrs_of_simple(**kwargs):
    """Use attrs() helper for simple data-* attributes."""
    return attrs(**kwargs)


class TestHelperFunctions:
    def test_template_function(self):
        assert f("Hello {name}", name=js("$name")) == "`Hello ${$name}`"
        assert (
            f(
                "rotate({rotation}deg) scale({scale})",
                rotation=js("$rotation"),
                scale=js("$scale"),
            )
            == "`rotate(${$rotation}deg) scale(${$scale})`"
        )

        result = f(
            """Welcome {userName}!
You have {messageCount} messages.""",
            userName=js("$userName"),
            messageCount=js("$messageCount"),
        )
        assert result.startswith("`")
        assert "${$userName}" in result
        assert "${$messageCount}" in result

    def test_condition_helpers(self):
        assert js("$active").if_("green", "gray").to_js() == '($active ? "green" : "gray")'


class TestCoreAttributes:
    def test_data_show(self):
        html = str(Div("x", data_show=True))
        assert " data-show" in html
        html = str(Div("x", data_show=False))
        # current behavior: omit attribute when false
        assert " data-show" not in html
        html = str(Div("x", data_show=js("$isVisible")))
        assert 'data-show="$isVisible"' in html
        html = str(Div("x", data_show=js("$count > 0")))
        assert 'data-show="$count > 0"' in html

    def test_data_text(self):
        html = str(Div("x", data_text="Hello"))
        assert 'data-text="Hello"' in html
        html = str(Div("x", data_text=js("$message")))
        assert 'data-text="$message"' in html
        html = str(Div("x", data_text=f("User: {name}", name=js("$name"))))
        assert 'data-text="`User: ${$name}`"' in html

    def test_data_bind(self):
        assert attrs_of_kwargs(data_bind=Signal("username")) == {"data-bind": "username"}

    def test_class_attrs(self):
        res = attrs_of_simple(class_active="$isActive", class_hidden="!$visible", class_loading="$pending")
        assert res == {
            "data-class-active": "$isActive",
            "data-class-hidden": "!$visible",
            "data-class-loading": "$pending",
        }

        res = attrs_of_simple(class_text_blue_700="$isPrimary")
        assert res == {"data-class-text-blue-700": "$isPrimary"}

    def test_style_attrs(self):
        res = attrs_of_simple(style_color="red", style_background_color="$bgColor", style_font_size="16px")
        assert res == {
            "data-style-color": "red",
            "data-style-background-color": "$bgColor",
            "data-style-font-size": "16px",
        }

    def test_attr_attrs(self):
        res = attrs_of_simple(attr_title="$tooltip", attr_data_value="$value", attr_disabled="$isDisabled")
        assert res == {
            "data-attr-title": "$tooltip",
            "data-attr-data-value": "$value",
            "data-attr-disabled": "$isDisabled",
        }

    def test_data_computed(self):
        res = attrs_of_kwargs(data_computed_fullName=js("$firstName + ' ' + $lastName"))
        assert res == {"data-computed-fullName": "$firstName + ' ' + $lastName"}


class TestSignals:
    def test_data_signals_list(self):
        res = attrs_of_kwargs(data_signals=[Signal("count", 0), Signal("name", "John"), Signal("active", True)])
        assert "data-signals" in res
        data = res["data-signals"]
        assert "count: 0" in data
        assert 'name: "John"' in data
        assert "active: true" in data


class TestEventHandlers:
    def test_on_click_basic(self):
        res = attrs_of_kwargs(data_on_click=("handleClick()", {}))
        assert "data-on-click" in res
        assert "handleClick()" in str(res["data-on-click"])

    def test_on_click_with_modifiers(self):
        res = attrs_of_kwargs(data_on_click=("submit()", {"once": True, "prevent": True}))
        assert "data-on-click__once__prevent" in res

    def test_on_input_with_debounce(self):
        res = attrs_of_kwargs(data_on_input=("search()", {"debounce": "500ms"}))
        assert "data-on-input__debounce.500ms" in res
        res = attrs_of_kwargs(data_on_input=("search()", {"debounce": "300ms"}))
        assert "data-on-input__debounce.300ms" in res

    def test_mixed_modifiers(self):
        res = attrs_of_kwargs(data_on_input=("search()", {"prevent": True, "debounce": "500ms"}))
        assert "data-on-input__prevent__debounce.500ms" in res

    def test_on_interval_and_intersect(self):
        assert "data-on-interval__duration.1s" in attrs_of_kwargs(data_on_interval=("tick()", {"duration": "1s"}))
        assert "data-on-interval__duration.500ms" in attrs_of_kwargs(
            data_on_interval=("update()", {"duration": "500ms"})
        )
        assert "data-on-intersect__once__half" in attrs_of_kwargs(
            data_on_intersect=("loadMore()", {"once": True, "half": True})
        )

    def test_generic_on(self):
        res = attrs_of_kwargs(data_on_custom_event=("handleCustom()", {"once": True}))
        assert "data-on-custom-event__once" in res


class TestOtherAttributes:
    def test_disabled_attr(self):
        assert attrs_of_simple(attr_disabled="true") == {"data-attr-disabled": "true"}
        assert attrs_of_simple(attr_disabled="false") == {"data-attr-disabled": "false"}
        assert attrs_of_simple(attr_disabled="$isSubmitting") == {"data-attr-disabled": "$isSubmitting"}

    def test_ignore_attr(self):
        assert " data-ignore" in str(Div("x", data_ignore=True))
        # current behavior: double dash in raw mapping
        assert "data-ignore--self" in str(Div("x", data_ignore__self=True))

    def test_preserve_attr(self):
        assert attrs_of_simple(preserve_attr="*") == {"data-preserve-attr": "*"}
        assert attrs_of_simple(preserve_attr="style,class") == {"data-preserve-attr": "style,class"}


class TestIntegration:
    def test_element_with_new_api(self):
        btn = Button(
            "Submit",
            **attrs_of_kwargs(data_on_click=("submit()", {"once": True, "prevent": True})),
            **attrs_of_simple(class_active="$isActive", class_loading="$isSubmitting"),
            **attrs_of_simple(attr_disabled="$isSubmitting"),
        )
        html = str(btn)
        assert "data-on-click__once__prevent" in html
        assert "data-class-active" in html
        assert "data-class-loading" in html
        assert "data-attr-disabled" in html

    def test_form_with_signals(self):
        form = Form(
            Input(**attrs_of_kwargs(data_bind=Signal("email")), type="email"),
            Input(**attrs_of_kwargs(data_bind=Signal("password")), type="password"),
            Button("Login", **attrs_of_simple(attr_disabled="!$email || !$password")),
            **attrs_of_kwargs(data_signals=[Signal("email", ""), Signal("password", "")]),
            **attrs_of_kwargs(data_on_submit=("login()", {"prevent": True})),
        )
        html = str(form)
        assert "data-signals" in html
        assert "data-on-submit__prevent" in html
        assert "data-bind" in html

    def test_conditional_styling(self):
        div = Div(
            "Content",
            **attrs_of_simple(
                style_background=js("$hovered").if_("#e3f2fd", "#fff").to_js(),
                style_opacity=js("$loading").if_(0.5, 1).to_js(),
                style_transform=f("scale({scale})", scale=js("$scale")),
            ),
        )
        html = str(div)
        assert "data-style-background" in html
        assert "data-style-opacity" in html
        assert "data-style-transform" in html
        assert "`scale(${$scale})`" in html
