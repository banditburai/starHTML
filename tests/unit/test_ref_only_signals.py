"""Test _ref_only Signal behavior."""

import unittest

from starhtml import Div, P, Span
from starhtml.datastar import Signal


class TestRefOnlySignals(unittest.TestCase):
    """Test the _ref_only flag for signals that should not appear in data-signals."""

    def test_regular_signal(self):
        """Test regular signal is included in data-signals."""
        div = Div(
            (test1 := Signal("test1", "initial value")),
            P("Signal value: ", Span(data_text="$test1")),
        )
        html = str(div)
        self.assertIn("data-signals", html)
        self.assertIn('test1: "initial value"', html)

    def test_ref_only_signal_with_initial_value(self):
        """Test _ref_only signal with initial value should not appear in data-signals."""
        div = Div(
            (test2 := Signal("test2", "ref only value", _ref_only=True)),
            P("Signal value: ", Span(data_text="$test2")),
        )
        html = str(div)
        self.assertNotIn("data-signals", html)

    def test_ref_only_signal_no_initial_value(self):
        """Test _ref_only signal without initial value should not appear in data-signals."""
        div = Div(
            (test3 := Signal("test3", None, _ref_only=True)),
            P("Signal value: ", Span(data_text="$test3")),
        )
        html = str(div)
        self.assertNotIn("data-signals", html)

    def test_multiple_signals_mixed(self):
        """Test mixed regular and _ref_only signals."""
        div = Div(
            (included := Signal("included", "value")),
            (excluded := Signal("excluded", "value", _ref_only=True)),
            P("Content"),
        )
        html = str(div)
        self.assertIn("data-signals", html)
        self.assertIn('included: "value"', html)
        self.assertNotIn("excluded:", html)

    def test_ref_only_in_data_signals_kwarg(self):
        """Test _ref_only signals passed via data_signals kwarg are excluded."""
        div = Div(
            P("Content"),
            data_signals=[
                Signal("normal", "value"),
                Signal("ref_only", "excluded", _ref_only=True),
            ],
        )
        html = str(div)
        self.assertIn("data-signals", html)
        self.assertIn('normal: "value"', html)
        self.assertNotIn("ref_only", html)

    def test_all_ref_only_signals(self):
        """Test when all signals are _ref_only, no data-signals attribute should be added."""
        div = Div(
            (ref1 := Signal("ref1", None, _ref_only=True)),
            (ref2 := Signal("ref2", "value", _ref_only=True)),
            P("Content"),
        )
        html = str(div)
        self.assertNotIn("data-signals", html)


if __name__ == "__main__":
    unittest.main()
