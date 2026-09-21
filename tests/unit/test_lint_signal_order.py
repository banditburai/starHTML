"""check_signal_order: a signal read on an earlier element than its declaration is a Datastar footgun."""

from starhtml import Div, Input, Signal, Span
from starhtml.lint import check_signal_order


def test_reader_before_declaring_sibling_is_reported():
    s = Signal("count", 5)
    issues = check_signal_order(Div(Span(data_text=s), Div(s)))
    assert [(i.signal, i.reader_tag, i.declaring_tag) for i in issues] == [("count", "span", "div")]
    assert "before <div> declares it" in str(issues[0])


def test_declaration_first_is_clean():
    s = Signal("count", 5)
    assert check_signal_order(Div(s, Span(data_text=s), Input(data_bind=s))) == []
    assert check_signal_order(Div(Div(s), Span(data_text=s))) == []  # earlier sibling declares


def test_same_element_is_covered_by_the_hoist():
    s = Signal("count", 5)
    assert check_signal_order(Div(s, data_text=s)) == []
    assert check_signal_order(Span(data_text=s, data_signals=[s])) == []


def test_undeclared_reads_are_not_reported():
    # Declared by a layout, persisted, or patched later: nothing in this tree declares it, so no verdict.
    assert check_signal_order(Div(Span(data_text="$outer"))) == []


def test_object_form_and_computed_declarations_count():
    s = Signal("count", 5, ifmissing=False)  # plain data-signals object (server-authoritative reset)
    assert check_signal_order(Div(Span(data_text=s), Div(s))) != []
    assert check_signal_order(Div(Div(s), Span(data_text=s))) == []
    total = Signal("total", s * 2)
    assert check_signal_order(Div(Span(data_text=total), Div(s, total))) != []
    assert check_signal_order(Div(Div(s, total), Span(data_text=total))) == []


def test_starelements_locals_are_ignored():
    assert check_signal_order(Div(Span(data_text="$$count"), Div(data_signals={"count": 1}))) == []


def test_member_access_reads_the_root_signal():
    assert check_signal_order(Div(Span(data_text="$count.toFixed(2)"), Div(Signal("count", 5)))) != []
    assert check_signal_order(Div(Span(data_text="$user.name"), Div(Signal("user", {"name": "a"})))) != []


def test_bare_signal_path_values_are_reads():
    x = Signal("x")  # initial None: data_bind emits no declaration of its own
    assert check_signal_order(Div(Input(data_bind=x), Div(Signal("x", 5)))) != []
    assert check_signal_order(Div(Div(Signal("x", 5)), Input(data_bind=x))) == []


def test_nested_object_values_declare_nothing():
    assert check_signal_order(Div(Span(data_text="$b"), Div(data_signals={"a": {"b": 1}}))) == []
    assert check_signal_order(Div(Span(data_text="$a"), Div(data_signals={"a": {"b": 1}}))) != []


def test_string_literals_are_not_reads():
    assert check_signal_order(Div(Span(data_text="'price: $count'"), Div(Signal("count", 5)))) == []


def test_raw_data_signals_string_values_are_literals():
    # StarHTML escapes `$` in data-signals string values (\u0024), so they are never expression reads.
    assert check_signal_order(Div(Div(data_signals={"a": "$b"}), Div(Signal("b", 1)))) == []
