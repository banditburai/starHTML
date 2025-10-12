"""Tests for setTimeout, clearTimeout, and resetTimeout functions."""

import pytest

from starhtml import Signal
from starhtml.datastar import clear_timeout, reset_timeout, set_timeout


class TestSetTimeout:
    """Test set_timeout() function."""

    def test_basic_timeout(self):
        """Fire-and-forget timeout."""
        copied = Signal("copied", False)
        result = set_timeout(copied.set(False), 2000)
        assert result.to_js() == "setTimeout(() => { $copied = false }, 2000)"

    def test_timeout_with_signal_delay(self):
        """Timeout with Signal as delay value."""
        action = Signal("action", False)
        delay = Signal("delay", 1000)
        result = set_timeout(action.set(True), delay)
        assert result.to_js() == "setTimeout(() => { $action = true }, $delay)"

    def test_timeout_with_store(self):
        """Timeout with stored timer ID."""
        open_state = Signal("open", False)
        timer = Signal("timer", None)
        result = set_timeout(open_state.set(True), 700, store=timer)
        assert result.to_js() == "$timer = setTimeout(() => { $open = true }, 700)"

    def test_timeout_with_window_store(self):
        """Timeout stored as window property."""
        selected = Signal("selected", 0)
        timer = Signal("timer", None)
        result = set_timeout(selected.set(0), 50, store=timer, window=True)
        assert result.to_js() == "window._timer = setTimeout(() => { $selected = 0 }, 50)"

    def test_timeout_with_multiple_actions_list(self):
        """Timeout with multiple actions as list."""
        step = Signal("step", 0)
        progress = Signal("progress", 0)
        result = set_timeout([step.set(2), progress.set(40)], 1000)
        assert result.to_js() == "setTimeout(() => { $step = 2; $progress = 40 }, 1000)"

    def test_timeout_extracts_signal_id(self):
        """set_timeout auto-extracts Signal.id for store parameter."""
        action = Signal("action", False)
        timer = Signal("my_timer", None)
        result = set_timeout(action.set(True), 500, store=timer)
        assert "$my_timer = setTimeout" in result.to_js()

    def test_timeout_with_string_timer_id(self):
        """set_timeout accepts string timer ID (backward compat)."""
        action = Signal("action", False)
        result = set_timeout(action.set(True), 500, store="custom_timer")
        assert "$custom_timer = setTimeout" in result.to_js()


class TestClearTimeout:
    """Test clear_timeout() function."""

    def test_clear_basic(self):
        """Clear timeout without actions."""
        timer = Signal("timer", None)
        result = clear_timeout(timer)
        assert result.to_js() == "clearTimeout($timer)"

    def test_clear_with_window(self):
        """Clear window timeout."""
        timer = Signal("timer", None)
        result = clear_timeout(timer, window=True)
        assert result.to_js() == "clearTimeout(window._timer)"

    def test_clear_with_single_action(self):
        """Clear timeout and execute single action."""
        timer = Signal("timer", None)
        open_state = Signal("open", False)
        result = clear_timeout(timer, open_state.set(False))
        assert result.to_js() == "clearTimeout($timer); $open = false"

    def test_clear_with_multiple_actions(self):
        """Clear timeout and execute multiple actions."""
        timer = Signal("timer", None)
        open_state = Signal("open", False)
        loading = Signal("loading", False)
        result = clear_timeout(timer, open_state.set(False), loading.set(False))
        assert result.to_js() == "clearTimeout($timer); $open = false; $loading = false"

    def test_clear_window_with_actions(self):
        """Clear window timeout with actions."""
        timer = Signal("timer", None)
        state = Signal("state", "")
        result = clear_timeout(timer, state.set("cancelled"), window=True)
        assert result.to_js() == 'clearTimeout(window._timer); $state = "cancelled"'

    def test_clear_extracts_signal_id(self):
        """clear_timeout auto-extracts Signal.id."""
        timer = Signal("my_timer", None)
        result = clear_timeout(timer)
        assert result.to_js() == "clearTimeout($my_timer)"


class TestResetTimeout:
    """Test reset_timeout() function."""

    def test_reset_basic(self):
        """Reset timeout with single action."""
        timer = Signal("timer", None)
        open_state = Signal("open", False)
        result = reset_timeout(timer, 700, open_state.set(True))
        assert result.to_js() == "clearTimeout($timer); $timer = setTimeout(() => { $open = true }, 700)"

    def test_reset_with_signal_delay(self):
        """Reset timeout with Signal delay."""
        timer = Signal("timer", None)
        delay = Signal("delay", 500)
        action = Signal("action", False)
        result = reset_timeout(timer, delay, action.set(True))
        assert result.to_js() == "clearTimeout($timer); $timer = setTimeout(() => { $action = true }, $delay)"

    def test_reset_with_window(self):
        """Reset window timeout."""
        timer = Signal("timer", None)
        selected = Signal("selected", 0)
        result = reset_timeout(timer, 50, selected.set(0), window=True)
        assert result.to_js() == "clearTimeout(window._timer); window._timer = setTimeout(() => { $selected = 0 }, 50)"

    def test_reset_with_multiple_actions(self):
        """Reset timeout with multiple actions."""
        timer = Signal("timer", None)
        step = Signal("step", 0)
        progress = Signal("progress", 0)
        result = reset_timeout(timer, 1000, step.set(2), progress.set(40))
        assert result.to_js() == "clearTimeout($timer); $timer = setTimeout(() => { $step = 2; $progress = 40 }, 1000)"

    def test_reset_debounce_pattern(self):
        """Reset timeout for debouncing (common use case)."""
        timer = Signal("search_timer", None)
        search = Signal("search", "")
        results = Signal("results", [])

        # Simulates: on every keystroke, cancel previous search and schedule new one
        result = reset_timeout(timer, 300, results.set(search + " results"))

        js = result.to_js()
        assert "clearTimeout($search_timer)" in js
        assert "$search_timer = setTimeout" in js
        assert "$results = `${$search} results`" in js
        assert "}, 300)" in js

    def test_reset_extracts_signal_id(self):
        """reset_timeout auto-extracts Signal.id."""
        timer = Signal("my_timer", None)
        action = Signal("action", False)
        result = reset_timeout(timer, 1000, action.set(True))
        assert "$my_timer = setTimeout" in result.to_js()


class TestTimerIntegration:
    """Test timeout functions work together."""

    def test_tooltip_pattern(self):
        """Tooltip hover delay pattern."""
        timer = Signal("tooltip_timer", None)
        open_state = Signal("tooltip_open", False)

        # On hover: reset timeout to show tooltip after delay
        show = reset_timeout(timer, 700, open_state.set(True))

        # On leave: clear timeout and hide immediately
        hide = clear_timeout(timer, open_state.set(False))

        assert "clearTimeout($tooltip_timer)" in show.to_js()
        assert "$tooltip_open = true" in show.to_js()
        assert "clearTimeout($tooltip_timer)" in hide.to_js()
        assert "$tooltip_open = false" in hide.to_js()

    def test_auto_hide_pattern(self):
        """Auto-hide notification pattern."""
        copied = Signal("copied", False)

        # Show immediately, then auto-hide after delay
        show = copied.set(True)
        auto_hide = set_timeout(copied.set(False), 2000)

        assert show.to_js() == "$copied = true"
        assert auto_hide.to_js() == "setTimeout(() => { $copied = false }, 2000)"

    def test_search_debounce_pattern(self):
        """Search debounce with window persistence."""
        timer = Signal("search_timer", None)
        _search = Signal("search", "")
        selected = Signal("selected", 0)

        # On search change: debounce selection reset
        debounced = reset_timeout(timer, 50, selected.set(0), window=True)

        js = debounced.to_js()
        assert "window._search_timer" in js
        assert "$selected = 0" in js

    def test_multi_step_wizard_pattern(self):
        """Multi-step wizard with timed progression."""
        step = Signal("step", 1)
        timer = Signal("step_timer", None)

        # Auto-advance to next step after delay
        advance = set_timeout(step.set(2), 3000, store=timer)

        # Cancel auto-advance on manual navigation
        cancel = clear_timeout(timer)

        assert "$step_timer = setTimeout" in advance.to_js()
        assert "$step = 2" in advance.to_js()
        assert "clearTimeout($step_timer)" in cancel.to_js()


class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_timeout_with_zero_delay(self):
        """Timeout with 0ms delay (immediate execution)."""
        action = Signal("action", False)
        result = set_timeout(action.set(True), 0)
        assert result.to_js() == "setTimeout(() => { $action = true }, 0)"

    def test_empty_actions_clear(self):
        """clear_timeout with no actions is valid."""
        timer = Signal("timer", None)
        result = clear_timeout(timer)
        assert result.to_js() == "clearTimeout($timer)"

    def test_signal_id_extraction_robustness(self):
        """Timer functions handle Signal.id extraction consistently."""
        timer = Signal("my_special_timer", None)
        action = Signal("action", False)

        set_result = set_timeout(action.set(True), 100, store=timer)
        clear_result = clear_timeout(timer)
        reset_result = reset_timeout(timer, 100, action.set(True))

        assert "$my_special_timer" in set_result.to_js()
        assert "$my_special_timer" in clear_result.to_js()
        assert "$my_special_timer" in reset_result.to_js()

    def test_window_persistence_pattern(self):
        """Window storage persists across DOM updates."""
        timer = Signal("global_timer", None)
        count = Signal("count", 0)

        # Window-stored timer survives element replacement
        window_timeout = set_timeout(count.set(0), 1000, store=timer, window=True)
        window_clear = clear_timeout(timer, window=True)

        assert "window._global_timer" in window_timeout.to_js()
        assert "window._global_timer" in window_clear.to_js()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
