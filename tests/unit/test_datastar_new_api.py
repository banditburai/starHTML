"""Tests for the new function-based Datastar API."""

import re

from starhtml import *
from starhtml.datastar import (
    # Import DatastarAttr for testing
    DatastarAttr,
    ds_attr,
    ds_bind,
    ds_class,
    ds_computed,
    # Other attributes
    ds_disabled,
    ds_ignore,
    ds_json_signals,
    ds_on,
    ds_on_click,
    ds_on_contextmenu,
    ds_on_dblclick,
    ds_on_drag,
    ds_on_dragend,
    ds_on_dragenter,
    ds_on_dragleave,
    ds_on_dragover,
    # New drag event handlers
    ds_on_dragstart,
    ds_on_drop,
    ds_on_input,
    ds_on_intersect,
    ds_on_interval,
    # New mouse event handlers
    ds_on_mousedown,
    ds_on_mouseenter,
    ds_on_mouseleave,
    ds_on_mousemove,
    ds_on_mouseout,
    ds_on_mouseover,
    ds_on_mouseup,
    ds_on_pointerdown,
    ds_on_pointerenter,
    ds_on_pointerleave,
    ds_on_pointermove,
    ds_on_pointerup,
    # Additional event handlers
    ds_on_reset,
    ds_on_select,
    ds_on_submit,
    ds_on_touchcancel,
    ds_on_touchend,
    ds_on_touchmove,
    # New touch event handlers
    ds_on_touchstart,
    ds_on_wheel,
    ds_persist,
    ds_preserve_attr,
    ds_show,
    ds_signals,
    ds_style,
    ds_text,
    equals,
    gt,
    gte,
    if_,
    lt,
    lte,
    # Helper functions
    t,
)


def attrs_of(ds_result):
    """Extract attrs dict from DatastarAttr result."""
    assert isinstance(ds_result, DatastarAttr)
    return ds_result.attrs


class TestHelperFunctions:
    """Test helper functions for expressions."""

    def test_template_function(self):
        """Test t() template function."""
        # Simple template
        assert t("Hello {$name}") == "`Hello ${$name}`"

        # Complex template
        assert t("rotate({$rotation}deg) scale({$scale})") == "`rotate(${$rotation}deg) scale(${$scale})`"

        # Multi-line template
        result = t("""Welcome {$userName}!
You have {$messageCount} messages.""")
        assert result.startswith("`")
        assert "${$userName}" in result
        assert "${$messageCount}" in result

        # Plain identifiers
        assert t("{rotation}") == "`${rotation}`"

    def test_if_function_simple(self):
        """Test if_() function with simple ternary."""
        # Simple boolean
        assert if_("$active", "green", "gray") == '$active ? "green" : "gray"'

        # With numbers
        assert if_("$loading", 0.5, 1) == "$loading ? 0.5 : 1"

        # With expressions
        assert if_("$count > 0", "block", "none") == '$count > 0 ? "block" : "none"'

    def test_if_function_pattern_matching(self):
        """Test if_() function with pattern matching."""
        result = if_("$status", success="green", error="red", _="gray")
        assert '"success"' in result
        assert '"green"' in result
        assert '"error"' in result
        assert '"red"' in result
        assert '"gray"' in result

        # Check structure
        assert result.endswith('"gray"')  # default case at end

    def test_condition_helpers(self):
        """Test condition helper functions."""
        # equals
        assert equals("$status", "active") == '$status === "active"'
        assert equals("status", "active") == '${status} === "active"'

        # gt
        assert gt("$count", 0) == "$count > 0"
        assert gt("count", 10) == "${count} > 10"

        # lt
        assert lt("$width", 600) == "$width < 600"

        # gte
        assert gte("$score", 90) == "$score >= 90"

        # lte
        assert lte("$age", 18) == "$age <= 18"


class TestCoreAttributes:
    """Test core Datastar attribute functions."""

    def test_ds_show(self):
        """Test ds_show function."""
        # Boolean value
        assert attrs_of(ds_show(True)) == {"data-show": "true"}
        assert attrs_of(ds_show(False)) == {"data-show": "false"}

        # String expression
        assert attrs_of(ds_show("$isVisible")) == {"data-show": "$isVisible"}
        assert attrs_of(ds_show("$count > 0")) == {"data-show": "$count > 0"}

    def test_ds_text(self):
        """Test ds_text function."""
        assert attrs_of(ds_text("Hello")) == {"data-text": "Hello"}
        assert attrs_of(ds_text("$message")) == {"data-text": "$message"}
        assert attrs_of(ds_text(t("User: {$name}"))) == {"data-text": "`User: ${$name}`"}

    def test_ds_bind(self):
        """Test ds_bind function."""
        # Simple binding
        assert attrs_of(ds_bind("username")) == {"data-bind": "username"}

        # With case modifier
        assert attrs_of(ds_bind("email", case="lower")) == {"data-bind-email__case.lower": True}
        assert attrs_of(ds_bind("name", case="title")) == {"data-bind-name__case.title": True}

    def test_ds_class(self):
        """Test ds_class function."""
        result = attrs_of(ds_class(active="$isActive", hidden="!$visible", loading="$pending"))
        assert result == {
            "data-class-active": "$isActive",
            "data-class-hidden": "!$visible",
            "data-class-loading": "$pending",
        }

        # Underscore to hyphen conversion
        result = attrs_of(ds_class(text_blue_700="$isPrimary"))
        assert result == {"data-class-text-blue-700": "$isPrimary"}

    def test_ds_style(self):
        """Test ds_style function."""
        result = attrs_of(ds_style(color="red", background_color="$bgColor", font_size="16px"))
        assert result == {
            "data-style-color": "red",
            "data-style-background-color": "$bgColor",
            "data-style-font-size": "16px",
        }

    def test_ds_attr(self):
        """Test ds_attr function."""
        result = attrs_of(ds_attr(title="$tooltip", data_value="$value", disabled="$isDisabled"))
        assert result == {
            "data-attr-title": "$tooltip",
            "data-attr-data-value": "$value",
            "data-attr-disabled": "$isDisabled",
        }

    def test_ds_computed(self):
        """Test ds_computed function."""
        # Basic computed
        result = attrs_of(ds_computed("fullName", "$firstName + ' ' + $lastName"))
        assert result == {"data-computed-fullName": "$firstName + ' ' + $lastName"}

        # With case modifier
        result = attrs_of(ds_computed("total", "$items.reduce((s, i) => s + i.price, 0)", case="upper"))
        assert result == {"data-computed-total__case.upper": "$items.reduce((s, i) => s + i.price, 0)"}


class TestSignalsAndPersistence:
    """Test signals and persistence functions."""

    def test_ds_signals_kwargs(self):
        """Test ds_signals with kwargs."""
        result = attrs_of(ds_signals(count=0, name="John", active=True))
        assert result == {"data-signals-count": "0", "data-signals-name": '"John"', "data-signals-active": "true"}

    def test_ds_signals_dict(self):
        """Test ds_signals with dict argument."""
        signals = {"count": 0, "name": "John"}
        result = attrs_of(ds_signals(signals))
        assert result == {"data-signals-count": "0", "data-signals-name": '"John"'}

    def test_ds_signals_with_modifiers(self):
        """Test ds_signals with ifmissing modifier."""
        result = attrs_of(ds_signals(count=0, ifmissing="warn"))
        assert "data-signals__ifmissing" in result
        assert result["data-signals__ifmissing"] == "warn"

    def test_ds_persist_all(self):
        """Test ds_persist with no arguments."""
        result = attrs_of(ds_persist())
        assert result == {"data-persist": None}

    def test_ds_persist_specific(self):
        """Test ds_persist with specific signals."""
        result = attrs_of(ds_persist("name", "email"))
        assert result == {"data-persist": "name,email"}

    def test_ds_persist_filters(self):
        """Test ds_persist with include/exclude filters."""
        # Single pattern
        result = attrs_of(ds_persist(include="user", exclude="temp"))
        data = str(result["data-persist"])
        assert '"include": "/user/"' in data
        assert '"exclude": "/temp/"' in data

        # Multiple patterns
        result = attrs_of(ds_persist(include=["user", "profile"]))
        data = str(result["data-persist"])
        assert '"/user/"' in data
        assert '"/profile/"' in data

    def test_ds_persist_regex(self):
        """Test ds_persist with regex patterns."""
        result = attrs_of(ds_persist(include=[re.compile(r"user_\d+")]))
        data = str(result["data-persist"])
        assert '"/user_\\\\d+/"' in data

    def test_ds_persist_modifiers(self):
        """Test ds_persist with modifiers."""
        # Session storage
        result = attrs_of(ds_persist(session=True))
        assert result == {"data-persist__session": None}

        # Custom key
        result = attrs_of(ds_persist(key="myapp"))
        assert result == {"data-persist-myapp": None}

        # Combined (key takes precedence over session)
        result = attrs_of(ds_persist("name", session=True, key="app-v2"))
        assert result == {"data-persist-app-v2": "name"}

    def test_ds_json_signals(self):
        """Test ds_json_signals function."""
        # Default (True)
        assert attrs_of(ds_json_signals()) == {"data-json-signals": True}

        # Explicit True
        assert attrs_of(ds_json_signals(True)) == {"data-json-signals": True}

        # False
        assert attrs_of(ds_json_signals(False)) == {"data-json-signals": "false"}

        # Terse
        assert attrs_of(ds_json_signals(terse=True)) == {"data-json-signals__terse": True}

        # Filters
        result = attrs_of(ds_json_signals(include="user", exclude="temp"))
        data = str(result["data-json-signals"])
        assert "/user/" in data
        assert "/temp/" in data
        assert "include:" in data
        assert "exclude:" in data


class TestEventHandlers:
    """Test event handler functions."""

    def test_ds_on_click_basic(self):
        """Test basic ds_on_click."""
        result = attrs_of(ds_on_click("handleClick()"))
        assert result == {"data-on-click": str(result["data-on-click"])}
        assert "handleClick()" in str(result["data-on-click"])

    def test_ds_on_click_html_modifiers(self):
        """Test ds_on_click with HTML-style modifiers."""
        result = attrs_of(ds_on_click("submit()", "once", "prevent"))
        assert "data-on-click__once.prevent" in result

    def test_ds_on_click_kwargs_modifiers(self):
        """Test ds_on_click with kwargs modifiers."""
        result = attrs_of(ds_on_click("submit()", once=True, prevent=True))
        assert "data-on-click__once.prevent" in result

    def test_ds_on_input_with_debounce(self):
        """Test ds_on_input with debounce."""
        result = attrs_of(ds_on_input("search()", debounce="500ms"))
        assert "data-on-input__debounce.500ms" in result

        # Without ms
        result = attrs_of(ds_on_input("search()", debounce="300"))
        assert "data-on-input__debounce.300ms" in result

    def test_mixed_modifiers(self):
        """Test mixed positional and keyword modifiers."""
        result = attrs_of(ds_on_input("search()", "prevent", debounce="500ms"))
        assert "data-on-input__prevent.debounce.500ms" in result

    def test_ds_on_interval(self):
        """Test ds_on_interval with duration."""
        result = attrs_of(ds_on_interval("tick()", duration="1s"))
        assert "data-on-interval__duration.1s" in result

        result = attrs_of(ds_on_interval("update()", duration="500ms"))
        assert "data-on-interval__duration.500ms" in result

    def test_ds_on_intersect(self):
        """Test ds_on_intersect with modifiers."""
        result = attrs_of(ds_on_intersect("loadMore()", "once", "half"))
        assert "data-on-intersect__once.half" in result

    def test_generic_ds_on(self):
        """Test generic ds_on for custom events."""
        result = attrs_of(ds_on("custom-event", "handleCustom()", "once"))
        assert "data-on-custom-event__once" in result

    def test_mouse_event_handlers(self):
        """Test mouse event handler generation."""
        # Basic mouse events
        result = attrs_of(ds_on_mousedown("handleMouseDown()"))
        assert "data-on-mousedown" in result
        assert "handleMouseDown()" in str(result["data-on-mousedown"])

        result = attrs_of(ds_on_mouseup("handleMouseUp()"))
        assert "data-on-mouseup" in result

        result = attrs_of(ds_on_mousemove("handleMouseMove()"))
        assert "data-on-mousemove" in result

        # Mouse enter/leave events
        result = attrs_of(ds_on_mouseenter("showTooltip()"))
        assert "data-on-mouseenter" in result

        result = attrs_of(ds_on_mouseleave("hideTooltip()"))
        assert "data-on-mouseleave" in result

        # Mouse over/out events
        result = attrs_of(ds_on_mouseover("handleOver()"))
        assert "data-on-mouseover" in result

        result = attrs_of(ds_on_mouseout("handleOut()"))
        assert "data-on-mouseout" in result

        # Special mouse events
        result = attrs_of(ds_on_contextmenu("showContextMenu()", prevent=True))
        assert "data-on-contextmenu__prevent" in result

        result = attrs_of(ds_on_dblclick("handleDoubleClick()"))
        assert "data-on-dblclick" in result

        result = attrs_of(ds_on_wheel("handleWheel()", prevent=True))
        assert "data-on-wheel__prevent" in result

    def test_touch_event_handlers(self):
        """Test touch event handler generation."""
        result = attrs_of(ds_on_touchstart("handleTouchStart()"))
        assert "data-on-touchstart" in result
        assert "handleTouchStart()" in str(result["data-on-touchstart"])

        result = attrs_of(ds_on_touchmove("handleTouchMove()"))
        assert "data-on-touchmove" in result

        result = attrs_of(ds_on_touchend("handleTouchEnd()"))
        assert "data-on-touchend" in result

        result = attrs_of(ds_on_touchcancel("handleTouchCancel()"))
        assert "data-on-touchcancel" in result

    def test_drag_event_handlers(self):
        """Test drag and drop event handlers."""
        result = attrs_of(ds_on_dragstart("handleDragStart()"))
        assert "data-on-dragstart" in result

        result = attrs_of(ds_on_drag("handleDrag()"))
        assert "data-on-drag" in result

        result = attrs_of(ds_on_dragenter("handleDragEnter()"))
        assert "data-on-dragenter" in result

        result = attrs_of(ds_on_dragover("handleDragOver()", prevent=True))
        assert "data-on-dragover__prevent" in result

        result = attrs_of(ds_on_dragleave("handleDragLeave()"))
        assert "data-on-dragleave" in result

        result = attrs_of(ds_on_drop("handleDrop()", prevent=True))
        assert "data-on-drop__prevent" in result

        result = attrs_of(ds_on_dragend("handleDragEnd()"))
        assert "data-on-dragend" in result

    def test_additional_event_handlers(self):
        """Test additional form and pointer event handlers."""
        # Additional form events
        result = attrs_of(ds_on_reset("handleReset()"))
        assert "data-on-reset" in result

        result = attrs_of(ds_on_select("handleSelect()"))
        assert "data-on-select" in result

        # Pointer events
        result = attrs_of(ds_on_pointerdown("handlePointerDown()"))
        assert "data-on-pointerdown" in result

        result = attrs_of(ds_on_pointerup("handlePointerUp()"))
        assert "data-on-pointerup" in result

        result = attrs_of(ds_on_pointermove("handlePointerMove()"))
        assert "data-on-pointermove" in result

        result = attrs_of(ds_on_pointerenter("handlePointerEnter()"))
        assert "data-on-pointerenter" in result

        result = attrs_of(ds_on_pointerleave("handlePointerLeave()"))
        assert "data-on-pointerleave" in result

    def test_new_event_handlers_with_modifiers(self):
        """Test new event handlers with various modifiers."""
        # Mouse event with multiple modifiers
        result = attrs_of(ds_on_mousedown("startDrag()", "once", prevent=True))
        assert "data-on-mousedown__once.prevent" in result

        # Touch event with debounce
        result = attrs_of(ds_on_touchmove("handleSwipe()", debounce="100ms"))
        assert "data-on-touchmove__debounce.100ms" in result

        # Drag event with stop propagation
        result = attrs_of(ds_on_drop("handleFileDrop()", "stop", prevent=True))
        assert "data-on-drop__stop.prevent" in result


class TestOtherAttributes:
    """Test other Datastar attributes."""

    def test_ds_disabled(self):
        """Test ds_disabled function."""
        assert attrs_of(ds_disabled(True)) == {"data-disabled": "true"}
        assert attrs_of(ds_disabled(False)) == {"data-disabled": "false"}
        assert attrs_of(ds_disabled("$isSubmitting")) == {"data-disabled": "$isSubmitting"}

    def test_ds_ignore(self):
        """Test ds_ignore function."""
        # Default
        assert attrs_of(ds_ignore()) == {"data-ignore": ""}

        # With self modifier
        assert attrs_of(ds_ignore("self")) == {"data-ignore__self": ""}

    def test_ds_preserve_attr(self):
        """Test ds_preserve_attr function."""
        # All attributes
        assert attrs_of(ds_preserve_attr()) == {"data-preserve-attr": "*"}

        # Specific attributes
        assert attrs_of(ds_preserve_attr("style", "class")) == {"data-preserve-attr": "style,class"}


class TestIntegration:
    """Test integration with FastHTML elements."""

    def test_element_with_new_api(self):
        """Test using new API with FastHTML elements."""
        # Create a button with multiple attributes
        btn = Button(
            "Submit",
            ds_on_click("submit()", "once", "prevent"),
            ds_class(active="$isActive", loading="$isSubmitting"),
            ds_disabled("$isSubmitting"),
        )

        html = str(btn)
        assert "data-on-click__once.prevent" in html
        assert "data-class-active" in html
        assert "data-class-loading" in html
        assert "data-disabled" in html

    def test_form_with_signals_and_persist(self):
        """Test form with signals and persistence."""
        form = Form(
            Input(ds_bind("email", case="lower"), type="email"),
            Input(ds_bind("password"), type="password"),
            Button("Login", ds_disabled("!$email || !$password")),
            ds_signals(email="", password=""),
            ds_persist("email"),
            ds_on_submit("login()", "prevent"),
        )

        html = str(form)
        assert "data-signals-email" in html
        assert "data-signals-password" in html
        assert "data-persist" in html
        assert "data-on-submit__prevent" in html
        assert "data-bind-email__case.lower" in html

    def test_conditional_styling(self):
        """Test conditional styling with new API."""
        div = Div(
            "Content",
            ds_style(
                background=if_("$hovered", "#e3f2fd", "#fff"),
                opacity=if_("$loading", 0.5, 1),
                transform=t("scale({$scale})"),
            ),
        )

        html = str(div)
        assert "data-style-background" in html
        assert "data-style-opacity" in html
        assert "data-style-transform" in html
        assert "`scale(${$scale})`" in html
