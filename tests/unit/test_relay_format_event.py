"""Tests for format_event and the SSE event dataclasses in starhtml.realtime.

Covers: SignalEvent, ElementEvent, ScriptEvent dataclass construction and defaults,
format_event dispatch for each event type, mode variants, FT objects, auto_remove
behavior, error handling, and edge cases.
"""

import pytest

from starhtml import Div, P, Span
from starhtml.realtime import (
    ElementEvent,
    ScriptEvent,
    SignalEvent,
    format_event,
)


class TestSignalEvent:
    """Tests for format_event with SignalEvent."""

    def test_basic_signals(self):
        result = format_event(SignalEvent({"status": "ok", "count": 42}))
        expected = "\n".join(
            [
                "event: datastar-patch-signals",
                'data: signals {"status": "ok", "count": 42}',
                "",
                "",
            ]
        )
        assert result == expected

    def test_empty_signals_dict(self):
        result = format_event(SignalEvent({}))
        expected = "\n".join(
            [
                "event: datastar-patch-signals",
                "data: signals {}",
                "",
                "",
            ]
        )
        assert result == expected

    def test_nested_signals(self):
        signals = {"user": {"name": "Alice", "age": 30}, "items": [1, 2, 3]}
        result = format_event(SignalEvent(signals))
        assert "event: datastar-patch-signals" in result
        assert '"user": {"name": "Alice", "age": 30}' in result
        assert '"items": [1, 2, 3]' in result

    def test_boolean_and_null_signals(self):
        result = format_event(SignalEvent({"a": True, "b": False, "c": None}))
        assert "true" in result
        assert "false" in result
        assert "null" in result

    def test_signal_with_special_characters(self):
        result = format_event(SignalEvent({"msg": 'hello <world> & "friends"'}))
        assert "event: datastar-patch-signals" in result
        assert "data: signals " in result
        # JSON-encoded, so quotes are escaped in the JSON string
        assert 'hello <world> & \\"friends\\"' in result

    def test_signal_with_newline_in_value(self):
        """Newlines within signal values are JSON-escaped by the serializer."""
        result = format_event(SignalEvent({"text": "line1\nline2"}))
        assert "event: datastar-patch-signals" in result
        # JSON serializer produces \\n, not a literal newline in the data line
        assert "line1\\nline2" in result

    def test_signal_event_ends_with_double_newline(self):
        result = format_event(SignalEvent({"x": 1}))
        assert result.endswith("\n\n")


class TestElementEvent:
    """Tests for format_event with ElementEvent."""

    def test_html_string_with_default_mode(self):
        """Default mode is 'outer', so no mode line should appear in the output."""
        result = format_event(ElementEvent("<p>hello</p>", "#target"))
        expected = "\n".join(
            [
                "event: datastar-patch-elements",
                "data: selector #target",
                "data: elements &lt;p&gt;hello&lt;/p&gt;",
                "",
                "",
            ]
        )
        assert result == expected

    def test_outer_mode_omits_mode_line(self):
        """'outer' is the SSE-level default mode, so no mode line is emitted."""
        result = format_event(ElementEvent("<p>x</p>", "#t", "outer"))
        assert "data: mode" not in result
        assert "data: selector #t" in result

    def test_inner_mode(self):
        result = format_event(ElementEvent("<span>x</span>", "#box", "inner"))
        assert "data: mode inner" in result

    def test_replace_mode(self):
        result = format_event(ElementEvent("<p>x</p>", "#a", "replace"))
        assert "data: mode replace" in result

    def test_prepend_mode(self):
        result = format_event(ElementEvent("<p>x</p>", "#a", "prepend"))
        assert "data: mode prepend" in result

    def test_append_mode(self):
        result = format_event(ElementEvent("<p>x</p>", "#a", "append"))
        assert "data: mode append" in result

    def test_before_mode(self):
        result = format_event(ElementEvent("<p>x</p>", "#a", "before"))
        assert "data: mode before" in result

    def test_after_mode(self):
        result = format_event(ElementEvent("<p>x</p>", "#a", "after"))
        assert "data: mode after" in result

    def test_remove_mode(self):
        result = format_event(ElementEvent("<p>x</p>", "#a", "remove"))
        assert "data: mode remove" in result

    def test_ft_object(self):
        """FT objects are serialized to HTML by to_xml before formatting."""
        result = format_event(ElementEvent(Div("content", id="main"), "#wrapper", "outer"))
        assert "event: datastar-patch-elements" in result
        assert "data: selector #wrapper" in result
        assert '<div id="main">content</div>' in result

    def test_ft_object_nested(self):
        element = Div(P("paragraph"), Span("text"), id="outer")
        result = format_event(ElementEvent(element, "#root", "outer"))
        assert "event: datastar-patch-elements" in result
        assert "<p>paragraph</p>" in result
        assert "<span>text</span>" in result

    def test_selector_with_class(self):
        result = format_event(ElementEvent("<p>x</p>", ".my-class", "inner"))
        assert "data: selector .my-class" in result

    def test_selector_with_attribute(self):
        result = format_event(ElementEvent("<p>x</p>", "[data-id]", "inner"))
        assert "data: selector [data-id]" in result

    def test_element_event_ends_with_double_newline(self):
        result = format_event(ElementEvent("<p>x</p>", "#t"))
        assert result.endswith("\n\n")

    def test_element_event_starts_with_event_type(self):
        result = format_event(ElementEvent("<p>x</p>", "#t"))
        assert result.startswith("event: datastar-patch-elements\n")


class TestScriptEvent:
    """Tests for format_event with ScriptEvent."""

    def test_auto_remove_true_by_default(self):
        result = format_event(ScriptEvent("alert('hi')"))
        assert 'data-effect="el.remove()"' in result

    def test_auto_remove_true_explicit(self):
        result = format_event(ScriptEvent("console.log(1)", auto_remove=True))
        assert 'data-effect="el.remove()"' in result

    def test_auto_remove_false(self):
        result = format_event(ScriptEvent("console.log(1)", auto_remove=False))
        assert "data-effect" not in result

    def test_script_appended_to_body(self):
        """ScriptEvent always targets body with append mode."""
        result = format_event(ScriptEvent("alert(1)"))
        assert "data: mode append" in result
        assert "data: selector body" in result

    def test_script_wrapped_in_script_tag(self):
        result = format_event(ScriptEvent("alert(1)"))
        assert "<script" in result
        assert "alert(1)" in result
        assert "</script>" in result

    def test_script_auto_remove_true_format(self):
        result = format_event(ScriptEvent("alert(1)"))
        expected = "\n".join(
            [
                "event: datastar-patch-elements",
                "data: mode append",
                "data: selector body",
                'data: elements <script data-effect="el.remove()">alert(1)</script>',
                "",
                "",
            ]
        )
        assert result == expected

    def test_script_auto_remove_false_format(self):
        result = format_event(ScriptEvent("alert(1)", auto_remove=False))
        expected = "\n".join(
            [
                "event: datastar-patch-elements",
                "data: mode append",
                "data: selector body",
                "data: elements <script>alert(1)</script>",
                "",
                "",
            ]
        )
        assert result == expected

    def test_empty_script(self):
        result = format_event(ScriptEvent(""))
        assert "<script" in result
        assert "</script>" in result
        assert "event: datastar-patch-elements" in result

    def test_script_event_ends_with_double_newline(self):
        result = format_event(ScriptEvent("x"))
        assert result.endswith("\n\n")


class TestFormatEventDispatch:
    """Tests for format_event type dispatch and error handling."""

    def test_unknown_type_raises_type_error(self):
        with pytest.raises(TypeError, match="Unknown event type"):
            format_event("not an event")

    def test_unknown_type_int_raises_type_error(self):
        with pytest.raises(TypeError, match="Unknown event type"):
            format_event(42)

    def test_unknown_type_dict_raises_type_error(self):
        with pytest.raises(TypeError, match="Unknown event type"):
            format_event({"signals": {}})

    def test_unknown_type_none_raises_type_error(self):
        with pytest.raises(TypeError, match="Unknown event type"):
            format_event(None)


class TestEventDataclassDefaults:
    """Tests for dataclass construction and default field values."""

    def test_element_event_default_mode_is_outer(self):
        event = ElementEvent("<p>x</p>", "#t")
        assert event.mode == "outer"

    def test_element_event_explicit_mode(self):
        event = ElementEvent("<p>x</p>", "#t", "append")
        assert event.mode == "append"

    def test_script_event_default_auto_remove_is_true(self):
        event = ScriptEvent("x")
        assert event.auto_remove is True

    def test_script_event_explicit_auto_remove_false(self):
        event = ScriptEvent("x", auto_remove=False)
        assert event.auto_remove is False

    def test_signal_event_requires_signals(self):
        with pytest.raises(TypeError):
            SignalEvent()

    def test_signal_event_stores_dict(self):
        d = {"a": 1, "b": "two"}
        event = SignalEvent(d)
        assert event.signals is d

    def test_element_event_stores_fields(self):
        event = ElementEvent("<div/>", ".cls", "prepend")
        assert event.element == "<div/>"
        assert event.selector == ".cls"
        assert event.mode == "prepend"

    def test_script_event_stores_fields(self):
        event = ScriptEvent("code()", auto_remove=False)
        assert event.script == "code()"
        assert event.auto_remove is False
