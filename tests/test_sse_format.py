"""Test SSE format matches Datastar v1 RC specification"""

from starhtml.datastar import format_fragment_event, format_signal_event, fragments, signals


def test_signal_sse_format():
    """Test that signal SSE events use correct v1 RC format."""
    signals = {"status": "test", "count": 42}
    output = format_signal_event(signals)

    expected_lines = [
        "event: datastar-merge-signals",
        "retry: 1000",
        'data: signals {"status": "test", "count": 42}',
        "",
        "",
    ]
    expected = "\n".join(expected_lines)

    assert output == expected


def test_fragment_sse_format():
    """Test that fragment SSE events use correct v1 RC format."""
    html = "<div>Test content</div>"
    output = format_fragment_event([html], "#target", "morph")

    expected_lines = [
        "event: datastar-merge-fragments",
        "retry: 1000",
        "data: selector #target",
        "data: mergeMode morph",
        "data: fragments <div>Test content</div>",
        "",
        "",
    ]
    expected = "\n".join(expected_lines)

    assert output == expected


def test_fragment_sse_format_no_selector():
    """Test fragment SSE format when no selector provided."""
    html = "<p>No selector</p>"
    output = format_fragment_event([html], merge_mode="append")

    expected_lines = [
        "event: datastar-merge-fragments",
        "retry: 1000",
        "data: mergeMode append",
        "data: fragments <p>No selector</p>",
        "",
        "",
    ]
    expected = "\n".join(expected_lines)

    assert output == expected


def test_signal_helper():
    """Test signal helper function."""
    result = signals(status="test", count=123)

    assert result[0] == "signals"
    assert result[1] == {"status": "test", "count": 123}


def test_fragment_helper():
    """Test fragment helper function."""
    result = fragments("content", "#target", "morph")

    assert result[0] == "fragments"
    assert result[1] == ("content", "#target", "morph")


def test_fragment_helper_defaults():
    """Test fragment helper with default parameters."""
    result = fragments("content")

    assert result[0] == "fragments"
    assert result[1] == ("content", None, "morph")


def test_multiple_fragments():
    """Test handling multiple fragments."""
    fragments = ["<div>First</div>", "<div>Second</div>"]
    output = format_fragment_event(fragments, "#target", "append")

    expected_lines = [
        "event: datastar-merge-fragments",
        "retry: 1000",
        "data: selector #target",
        "data: mergeMode append",
        "data: fragments <div>First</div><div>Second</div>",
        "",
        "",
    ]
    expected = "\n".join(expected_lines)

    assert output == expected


def test_complex_signals():
    """Test complex signal data types."""
    signals = {"user": {"name": "John", "age": 30}, "items": [1, 2, 3], "active": True, "count": 0}
    output = format_signal_event(signals)

    # Should contain the event type and data prefix
    assert "event: datastar-merge-signals" in output
    assert "data: signals " in output
    assert '"user": {"name": "John", "age": 30}' in output
    assert '"items": [1, 2, 3]' in output
    assert '"active": true' in output
