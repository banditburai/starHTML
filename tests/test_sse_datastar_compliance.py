"""Test SSE compliance with Datastar RC.11 format expectations."""

import json

from starlette.testclient import TestClient

from starhtml import Div, P, star_app
from starhtml.datastar import format_fragment_event, format_signal_event, fragments, signals, sse


def test_sse_event_names():
    """Test that we use the correct Datastar event names."""
    # According to the RC.11 code, these are the event names:
    # ge="datastar-merge-fragments"
    # ye="datastar-merge-signals"

    # Test signal event name
    output = format_signal_event({"test": 1})
    assert "event: datastar-merge-signals" in output

    # Test fragment event name
    output = format_fragment_event(Div("test"))
    assert "event: datastar-merge-fragments" in output

def test_sse_signal_format():
    """Test signal merge format matches Datastar expectations."""
    # From RC.11: data: signals {JSON}
    signals = {"count": 42, "active": True}
    output = format_signal_event(signals)

    lines = output.strip().split('\n')
    data_line = next(line for line in lines if line.startswith("data: signals "))
    json_str = data_line[len("data: signals "):]

    # Should be valid JSON
    parsed = json.loads(json_str)
    assert parsed == signals

def test_sse_fragment_format():
    """Test fragment merge format matches Datastar expectations."""
    # From RC.11:
    # data: selector #id
    # data: mergeMode morph
    # data: fragments <html>

    fragment = Div(P("Test"), id="test")
    output = format_fragment_event(fragment, "#target", "morph")

    lines = output.strip().split('\n')

    # Check for required data lines
    assert any(line == "data: selector #target" for line in lines)
    assert any(line == "data: mergeMode morph" for line in lines)
    assert any(line.startswith("data: fragments ") for line in lines)

    # Fragment should be on single line (newlines escaped)
    fragment_line = next(line for line in lines if line.startswith("data: fragments "))
    assert "\n" not in fragment_line  # No raw newlines

def test_sse_merge_modes():
    """Test all supported merge modes."""
    # From the code: je="morph", bt="inner", Et="outer", St="prepend", Tt="append", xt="before", At="after"
    modes = ["morph", "inner", "outer", "prepend", "append", "before", "after"]

    for mode in modes:
        output = format_fragment_event(Div("test"), "#target", mode)
        assert f"data: mergeMode {mode}" in output

def test_sse_retry_header():
    """Test that retry duration is included."""
    # Check signals
    output = format_signal_event({})
    assert "retry: 1000" in output

    # Check fragments
    output = format_fragment_event(Div())
    assert "retry: 1000" in output

def test_sse_with_app():
    """Test SSE with actual app endpoints."""
    app, rt = star_app()

    @rt('/sse-test')
    @sse
    def sse_test():
        yield signals(count=1, message="Hello")
        yield fragments(Div(P("Updated")), "#content")

    client = TestClient(app)

    # Test the SSE endpoint
    with client.stream("GET", "/sse-test") as response:
        assert response.status_code == 200
        assert response.headers["content-type"] == "text/event-stream"

        # Read the SSE stream
        content = b""
        for chunk in response.iter_bytes():
            content += chunk

        text = content.decode('utf-8')

        # Check both events are present
        assert "event: datastar-merge-signals" in text
        assert "event: datastar-merge-fragments" in text
        assert "data: signals" in text
        assert "data: selector #content" in text

def test_sse_special_characters_in_fragments():
    """Test that special characters are properly handled in fragments."""
    # Test HTML special chars
    fragment = Div(
        P("Test < > & \" '"),
        P("Line1\nLine2"),  # Newlines
        P("Unicode: 🚀")
    )

    output = format_fragment_event(fragment)

    # Get the fragments line
    lines = output.strip().split('\n')
    fragment_line = next(line for line in lines if line.startswith("data: fragments "))
    html = fragment_line[len("data: fragments "):]

    # Check escaping
    assert "&lt;" in html  # < escaped
    assert "&gt;" in html  # > escaped
    assert "&amp;" in html # & escaped
    assert "&#10;" in html # newline escaped
    assert "🚀" in html    # Unicode preserved

    # Should not contain raw newlines
    assert "\n" not in html

def test_sse_empty_selector():
    """Test fragment merge without selector."""
    output = format_fragment_event(Div("test"))

    lines = output.strip().split('\n')

    # Should not have selector line
    assert not any(line.startswith("data: selector") for line in lines)
    # Should still have mergeMode
    assert any(line.startswith("data: mergeMode") for line in lines)

def test_sse_datastar_headers():
    """Test that SSE responses include proper headers."""
    from starhtml.datastar import SSE_HEADERS

    assert SSE_HEADERS['Content-Type'] == 'text/event-stream'
    assert SSE_HEADERS['Cache-Control'] == 'no-cache'
    assert SSE_HEADERS['Connection'] == 'keep-alive'
