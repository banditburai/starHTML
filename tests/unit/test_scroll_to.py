"""Tests for scroll_to helper."""

from starhtml.datastar import el, js, scroll_to


class TestScrollToBasic:
    def test_string_selector(self):
        result = scroll_to(".my-section").to_js()
        assert 'document.querySelector(".my-section")' in result

    def test_expr_target(self):
        result = scroll_to(el.closest(".card")).to_js()
        assert 'el.closest(".card")' in result

    def test_js_target(self):
        result = scroll_to(js("evt.target")).to_js()
        assert "evt.target" in result


class TestScrollToParameters:
    def test_default_duration(self):
        result = scroll_to(".x").to_js()
        assert "d=400" in result

    def test_custom_duration(self):
        result = scroll_to(".x", duration=600).to_js()
        assert "d=600" in result

    def test_default_offset(self):
        result = scroll_to(".x").to_js()
        assert "r.top-0" in result

    def test_custom_offset(self):
        result = scroll_to(".x", offset=48).to_js()
        assert "r.top-48" in result

    def test_visibility_check_by_default(self):
        result = scroll_to(".x").to_js()
        assert "if(r.top<0||r.bottom>innerHeight)" in result

    def test_force_skips_visibility_check(self):
        result = scroll_to(".x", force=True).to_js()
        assert "if(r.top<0||r.bottom>innerHeight)" not in result


class TestScrollToFocus:
    def test_no_focus_by_default(self):
        result = scroll_to(".x").to_js()
        assert ".focus()" not in result

    def test_focus_after_animation(self):
        result = scroll_to(".x", focus=True).to_js()
        assert "else _e.focus()" in result


class TestScrollToAnimation:
    def test_cancels_previous_animation(self):
        result = scroll_to(".x").to_js()
        assert "if(window._sRaf)cancelAnimationFrame(window._sRaf)" in result

    def test_uses_request_animation_frame(self):
        result = scroll_to(".x").to_js()
        assert "window._sRaf=requestAnimationFrame(function f(t)" in result

    def test_ease_out_formula(self):
        result = scroll_to(".x").to_js()
        assert "p*(2-p)" in result

    def test_null_target_guard(self):
        """Generated JS guards against null querySelector results."""
        result = scroll_to(".x").to_js()
        assert "if(_e)" in result


class TestScrollToSelectorEscaping:
    def test_special_chars_escaped(self):
        """Selectors with $ or @ are escaped to avoid Datastar preprocessor."""
        result = scroll_to("[data-value$='test']").to_js()
        assert "\\u0024" in result
