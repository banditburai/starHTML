"""Tests for starhtml.forms validation builders, lifecycle, and coordination."""

import pytest

from starhtml.datastar import Signal
from starhtml.forms import (
    FormAttrs,
    checked,
    email,
    form_reset,
    form_submit,
    form_validate_on_click,
    matches,
    max_length,
    min_length,
    pattern,
    required,
)

# ============================================================================
# Validation builders
# ============================================================================


class TestRequired:
    def test_default_label(self):
        sig = Signal("name", "")
        result = required(sig).to_js()
        assert "This field is required" in result

    def test_custom_label(self):
        sig = Signal("name", "")
        result = required(sig, "Name").to_js()
        assert "Name is required" in result

    def test_returns_expr(self):
        sig = Signal("name", "")
        result = required(sig)
        assert hasattr(result, "to_js")

    def test_uses_signal_reference(self):
        sig = Signal("username", "")
        result = required(sig).to_js()
        assert "$username" in result

    def test_negation_logic(self):
        """required uses ~signal (logical NOT) to detect empty."""
        sig = Signal("name", "")
        result = required(sig).to_js()
        # The output should contain a ternary with negation
        assert "!" in result or "not" in result.lower()

    def test_returns_empty_string_when_valid(self):
        """When the field is non-empty, the expr evaluates to empty string."""
        sig = Signal("name", "")
        result = required(sig).to_js()
        # The if_ with one arg uses empty string as the false branch
        assert '""' in result


class TestEmail:
    def test_required_check(self):
        sig = Signal("email", "")
        result = email(sig).to_js()
        assert "Email is required" in result

    def test_regex_check(self):
        sig = Signal("email", "")
        result = email(sig).to_js()
        assert "valid email" in result

    def test_custom_regex(self):
        sig = Signal("email", "")
        custom_re = r"^[^@]+@company\.com$"
        result = email(sig, re=custom_re).to_js()
        assert "company" in result

    def test_uses_signal_reference(self):
        sig = Signal("user_email", "")
        result = email(sig).to_js()
        assert "$user_email" in result

    def test_default_regex_pattern(self):
        """Default email regex should be present in the JS output."""
        sig = Signal("email", "")
        result = email(sig).to_js()
        # The default regex includes @
        assert "@" in result

    def test_is_switch_expression(self):
        """email() uses switch(), which creates nested ternaries."""
        sig = Signal("email", "")
        result = email(sig).to_js()
        # switch produces nested ternaries with ?
        assert "?" in result

    def test_both_messages_present(self):
        """Both the required and invalid email messages should appear."""
        sig = Signal("email", "")
        result = email(sig).to_js()
        assert "Email is required" in result
        assert "Please enter a valid email" in result


class TestMinLength:
    def test_required_check(self):
        sig = Signal("pw", "")
        result = min_length(sig, 8).to_js()
        assert "is required" in result

    def test_length_check(self):
        sig = Signal("pw", "")
        result = min_length(sig, 8).to_js()
        assert "8" in result

    def test_custom_label(self):
        sig = Signal("pw", "")
        result = min_length(sig, 8, "Password").to_js()
        assert "Password is required" in result

    def test_default_label(self):
        sig = Signal("pw", "")
        result = min_length(sig, 8).to_js()
        assert "This field is required" in result

    def test_uses_length_property(self):
        sig = Signal("pw", "")
        result = min_length(sig, 8).to_js()
        assert ".length" in result

    def test_different_min_values(self):
        sig = Signal("pw", "")
        for n in [1, 5, 12, 100]:
            result = min_length(sig, n).to_js()
            assert f"at least {n} characters" in result

    def test_uses_signal_reference(self):
        sig = Signal("password", "")
        result = min_length(sig, 6).to_js()
        assert "$password" in result


class TestMaxLength:
    def test_max_check(self):
        sig = Signal("bio", "")
        result = max_length(sig, 500).to_js()
        assert "500" in result

    def test_does_not_check_required(self):
        sig = Signal("bio", "")
        result = max_length(sig, 500).to_js()
        assert "required" not in result

    def test_message_format(self):
        sig = Signal("bio", "")
        result = max_length(sig, 200).to_js()
        assert "Must be at most 200 characters" in result

    def test_uses_length_property(self):
        sig = Signal("bio", "")
        result = max_length(sig, 500).to_js()
        assert ".length" in result

    def test_returns_empty_when_valid(self):
        sig = Signal("bio", "")
        result = max_length(sig, 500).to_js()
        assert '""' in result

    def test_uses_greater_than(self):
        """max_length checks signal.length > n."""
        sig = Signal("bio", "")
        result = max_length(sig, 500).to_js()
        assert ">" in result


class TestPattern:
    def test_required_by_default(self):
        sig = Signal("code", "")
        result = pattern(sig, r"^\d{6}$", "Invalid code").to_js()
        assert "required" in result

    def test_pattern_message(self):
        sig = Signal("code", "")
        result = pattern(sig, r"^\d{6}$", "Invalid code").to_js()
        assert "Invalid code" in result

    def test_optional_skips_required(self):
        sig = Signal("phone", "")
        result = pattern(sig, r"^\d{10}$", "Invalid phone", optional=True).to_js()
        assert "required" not in result

    def test_optional_still_validates_pattern(self):
        sig = Signal("phone", "")
        result = pattern(sig, r"^\d{10}$", "Invalid phone", optional=True).to_js()
        assert "Invalid phone" in result

    def test_regex_in_output(self):
        sig = Signal("code", "")
        result = pattern(sig, r"^\d{6}$", "Invalid code").to_js()
        # The regex pattern should appear
        assert r"^\d{6}$" in result

    def test_optional_uses_and_logic(self):
        """Optional pattern: (signal & ~regex.test(signal)) — only checks when non-empty."""
        sig = Signal("phone", "")
        result = pattern(sig, r"^\d{10}$", "Invalid phone", optional=True).to_js()
        assert "&&" in result or "&" in result

    def test_uses_test_method(self):
        sig = Signal("code", "")
        result = pattern(sig, r"^\d{6}$", "Invalid code").to_js()
        assert ".test(" in result


class TestMatches:
    def test_required_check(self):
        sig = Signal("confirm", "")
        other = Signal("password", "")
        result = matches(sig, other).to_js()
        assert "is required" in result

    def test_match_message(self):
        sig = Signal("confirm", "")
        other = Signal("password", "")
        result = matches(sig, other, "Passwords must match").to_js()
        assert "Passwords must match" in result

    def test_default_message(self):
        sig = Signal("confirm", "")
        other = Signal("password", "")
        result = matches(sig, other).to_js()
        assert "Fields must match" in result

    def test_custom_label(self):
        sig = Signal("confirm", "")
        other = Signal("password", "")
        result = matches(sig, other, label="Confirmation").to_js()
        assert "Confirmation is required" in result

    def test_references_both_signals(self):
        sig = Signal("confirm_pw", "")
        other = Signal("password", "")
        result = matches(sig, other).to_js()
        assert "$confirm_pw" in result
        assert "$password" in result

    def test_uses_inequality(self):
        sig = Signal("confirm", "")
        other = Signal("password", "")
        result = matches(sig, other).to_js()
        assert "!=" in result or "!==" in result


class TestChecked:
    def test_default_message(self):
        sig = Signal("terms", False)
        result = checked(sig).to_js()
        assert "required" in result

    def test_custom_message(self):
        sig = Signal("terms", False)
        result = checked(sig, "You must accept the terms").to_js()
        assert "accept the terms" in result

    def test_uses_signal_reference(self):
        sig = Signal("terms_accepted", False)
        result = checked(sig).to_js()
        assert "$terms_accepted" in result

    def test_returns_expr(self):
        sig = Signal("terms", False)
        result = checked(sig)
        assert hasattr(result, "to_js")

    def test_negation_logic(self):
        """checked uses ~signal, same as required."""
        sig = Signal("terms", False)
        result = checked(sig).to_js()
        assert "!" in result


# ============================================================================
# Signal._validation_expr storage
# ============================================================================


class TestSignalValidateStorage:
    def test_stores_validation_expr(self):
        sig = Signal("org", _ref_only=True)
        sig.validate(min_length, 3, "Organization")
        assert hasattr(sig, "_validation_expr")
        assert sig._validation_expr.to_js()

    def test_updates_on_revalidate(self):
        sig = Signal("org", _ref_only=True)
        sig.validate(min_length, 3)
        first = sig._validation_expr
        sig.validate(email)
        assert sig._validation_expr is not first

    def test_not_present_before_validate(self):
        sig = Signal("org", _ref_only=True)
        assert "_validation_expr" not in sig.__dict__

    def test_stores_pre_built_expr(self):
        sig = Signal("org", _ref_only=True)
        expr = min_length(sig, 3)
        sig.validate(expr)
        assert sig._validation_expr is expr


# ============================================================================
# Form submission coordination
# ============================================================================


class TestFormSubmit:
    def _make_validated_signals(self, *names):
        """Helper: create validated signals."""
        sigs = []
        for name in names:
            sig = Signal(name, _ref_only=True)
            sig.validate(required)
            sigs.append(sig)
        return sigs

    def test_returns_form_attrs(self):
        [sig] = self._make_validated_signals("name")
        result = form_submit("auth/login", sig, name="login")
        assert isinstance(result, FormAttrs)
        assert isinstance(result, dict)

    def test_required_keys(self):
        [sig] = self._make_validated_signals("name")
        result = form_submit("auth/login", sig, name="login")
        assert "data_on_submit" in result
        assert result["action"] == "auth/login"
        assert result["method"] == "post"
        assert result["novalidate"] is True

    def test_exactly_five_keys(self):
        [sig] = self._make_validated_signals("name")
        result = form_submit("test", sig, name="t")
        assert len(result) == 5  # data_on_submit, action, method, novalidate, data_signals
        assert "data_signals" in result

    def test_data_signals_includes_all_lifecycle(self):
        [sig] = self._make_validated_signals("name")
        result = form_submit("test", sig, name="t")
        names = {s._name for s in result["data_signals"]}
        assert "t_submitting" in names
        assert "t_submitted" in names
        assert "t_error" in names

    def test_auto_creates_submitting_signal(self):
        [sig] = self._make_validated_signals("name")
        result = form_submit("test", sig, name="myform")
        assert isinstance(result.submitting, Signal)
        assert result.submitting._name == "myform_submitting"

    def test_auto_creates_submitted_signal(self):
        [sig] = self._make_validated_signals("name")
        result = form_submit("test", sig, name="myform")
        assert isinstance(result.submitted, Signal)
        assert result.submitted._name == "myform_submitted"
        assert result.submitted._initial is False

    def test_auto_creates_error_signal(self):
        [sig] = self._make_validated_signals("name")
        result = form_submit("test", sig, name="myform")
        assert isinstance(result.error, Signal)
        assert result.error._name == "myform_error"

    def test_name_hyphens_to_underscores(self):
        [sig] = self._make_validated_signals("name")
        result = form_submit("test", sig, name="reg-form")
        assert result.submitting._name == "reg_form_submitting"
        assert result.submitted._name == "reg_form_submitted"
        assert result.error._name == "reg_form_error"

    def test_explicit_submitting_override(self):
        [sig] = self._make_validated_signals("name")
        my_sub = Signal("my_sub", False)
        result = form_submit("test", sig, submitting=my_sub)
        assert result.submitting is my_sub
        assert result.submitted is None  # not auto-created without name=

    def test_explicit_submitting_with_name_auto_creates_others(self):
        [sig] = self._make_validated_signals("name")
        my_sub = Signal("my_sub", False)
        result = form_submit("test", sig, name="reg", submitting=my_sub)
        assert result.submitting is my_sub
        assert isinstance(result.submitted, Signal)
        assert result.submitted._name == "reg_submitted"
        assert isinstance(result.error, Signal)
        assert result.error._name == "reg_error"

    def test_explicit_submitted_override(self):
        [sig] = self._make_validated_signals("name")
        my_done = Signal("my_done", False)
        result = form_submit("test", sig, name="t", submitted=my_done)
        assert result.submitted is my_done

    def test_explicit_error_override(self):
        [sig] = self._make_validated_signals("name")
        my_err = Signal("my_err", "")
        my_sub = Signal("my_sub", False)
        result = form_submit("test", sig, submitting=my_sub, error=my_err)
        assert result.error is my_err

    def test_raises_without_name_or_submitting(self):
        [sig] = self._make_validated_signals("name")
        with pytest.raises(ValueError, match="name="):
            form_submit("test", sig)

    def test_raises_for_unvalidated_signal(self):
        sig = Signal("name", _ref_only=True)  # no .validate() called
        with pytest.raises(ValueError, match="no validation"):
            form_submit("test", sig, name="t")

    def test_data_on_submit_is_tuple(self):
        [sig] = self._make_validated_signals("name")
        result = form_submit("test", sig, name="t")
        assert isinstance(result["data_on_submit"], tuple)
        assert len(result["data_on_submit"]) == 2

    def test_prevent_default(self):
        [sig] = self._make_validated_signals("name")
        result = form_submit("test", sig, name="t")
        _, opts = result["data_on_submit"]
        assert opts == {"prevent": True}

    def test_focus_first_error_enabled_by_default(self):
        [sig] = self._make_validated_signals("name")
        result = form_submit("test", sig, name="t")
        actions, _ = result["data_on_submit"]
        # 1 validate + 1 conditional submit + 1 focus = 3
        assert len(actions) == 3

    def test_focus_first_error_disabled(self):
        [sig] = self._make_validated_signals("name")
        result = form_submit("test", sig, name="t", focus_first_error=False)
        actions, _ = result["data_on_submit"]
        # 1 validate + 1 conditional submit = 2
        assert len(actions) == 2

    def test_multiple_fields(self):
        em, pw = self._make_validated_signals("email", "pw")
        em.validate(email)
        pw.validate(min_length, 8)
        result = form_submit("auth/register", em, pw, name="reg")
        actions, _ = result["data_on_submit"]
        # 2 validate + 1 conditional submit + 1 focus = 4
        assert len(actions) == 4

    def test_three_fields(self):
        sigs = self._make_validated_signals("a", "b", "c")
        result = form_submit("test", *sigs, name="t")
        actions, _ = result["data_on_submit"]
        # 3 validate + 1 conditional submit + 1 focus = 5
        assert len(actions) == 5

    def test_three_fields_no_focus(self):
        sigs = self._make_validated_signals("a", "b", "c")
        result = form_submit("test", *sigs, name="t", focus_first_error=False)
        actions, _ = result["data_on_submit"]
        # 3 validate + 1 conditional submit = 4
        assert len(actions) == 4

    def test_endpoint_in_action(self):
        [sig] = self._make_validated_signals("name")
        result = form_submit("my/api/endpoint", sig, name="t")
        assert result["action"] == "my/api/endpoint"

    def test_actions_contain_validation_assignments(self):
        sig = Signal("name", _ref_only=True)
        sig.validate(required)
        result = form_submit("test", sig, name="t")
        actions, _ = result["data_on_submit"]
        first_action_js = actions[0].to_js()
        assert "$name_err" in first_action_js

    def test_submit_action_contains_post(self):
        [sig] = self._make_validated_signals("name")
        result = form_submit("auth/login", sig, name="t")
        actions, _ = result["data_on_submit"]
        submit_js = actions[1].to_js()
        assert "auth/login" in submit_js

    def test_focus_action_references_aria_invalid(self):
        [sig] = self._make_validated_signals("name")
        result = form_submit("test", sig, name="t")
        actions, _ = result["data_on_submit"]
        focus_js = actions[-1].to_js()
        assert "aria-invalid" in focus_js

    def test_server_error_cleared_on_submit(self):
        [sig] = self._make_validated_signals("name")
        result = form_submit("test", sig, name="myform")
        actions, _ = result["data_on_submit"]
        submit_js = actions[1].to_js()
        assert "$myform_error" in submit_js

    def test_explicit_error_cleared_on_submit(self):
        [sig] = self._make_validated_signals("name")
        server_err = Signal("server_err", "")
        result = form_submit("test", sig, submitting=Signal("sub", False), error=server_err)
        actions, _ = result["data_on_submit"]
        submit_js = actions[1].to_js()
        assert "$server_err" in submit_js

    def test_error_list_clears_all(self):
        [sig] = self._make_validated_signals("name")
        server_err = Signal("server_err", "")
        err_type = Signal("error_type", "")
        result = form_submit("test", sig, submitting=Signal("sub", False), error=[server_err, err_type])
        actions, _ = result["data_on_submit"]
        submit_js = actions[1].to_js()
        assert "$server_err" in submit_js
        assert "$error_type" in submit_js

    def test_error_none_no_clearing(self):
        [sig] = self._make_validated_signals("name")
        result = form_submit("test", sig, submitting=Signal("sub", False), error=None)
        actions, _ = result["data_on_submit"]
        submit_js = actions[1].to_js()
        assert "test" in submit_js

    def test_spreadable_as_kwargs(self):
        """FormAttrs works with ** spreading."""
        [sig] = self._make_validated_signals("name")
        result = form_submit("test", sig, name="t")
        spread = {**result}
        assert "data_on_submit" in spread
        assert "action" in spread

    def test_reset_on_success_false_by_default(self):
        [sig] = self._make_validated_signals("name")
        result = form_submit("test", sig, name="t")
        assert "data_on_signal_patch" not in result
        assert "data_on_signal_patch_filter" not in result

    def test_reset_on_success_adds_signal_patch_handler(self):
        [sig] = self._make_validated_signals("name")
        result = form_submit("test", sig, name="t", reset_on_success=True)
        assert "data_on_signal_patch" in result
        assert result["data_on_signal_patch_filter"] == "{include: /^t_submitted$/}"

    def test_reset_on_success_guards_on_submitted(self):
        [sig] = self._make_validated_signals("name")
        result = form_submit("test", sig, name="t", reset_on_success=True)
        js = result["data_on_signal_patch"].to_js()
        assert "&&" in js
        assert "$t_submitted" in js

    def test_reset_on_success_resets_field_signals(self):
        em, pw = self._make_validated_signals("email", "pw")
        em.validate(email)
        pw.validate(min_length, 8)
        result = form_submit("test", em, pw, name="reg", reset_on_success=True)
        js = result["data_on_signal_patch"].to_js()
        assert "$email" in js
        assert "$pw" in js

    def test_reset_on_success_clears_error_signals(self):
        [sig] = self._make_validated_signals("name")
        result = form_submit("test", sig, name="t", reset_on_success=True)
        js = result["data_on_signal_patch"].to_js()
        assert "$name_err" in js

    def test_reset_on_success_without_submitted_is_noop(self):
        """When no submitted signal exists, reset_on_success has no effect."""
        [sig] = self._make_validated_signals("name")
        my_sub = Signal("sub", False)
        result = form_submit("test", sig, submitting=my_sub, reset_on_success=True)
        assert "data_on_signal_patch" not in result
        assert "data_on_signal_patch_filter" not in result


# ============================================================================
# Native POST validation
# ============================================================================


class TestFormValidateOnClick:
    def test_returns_dict_with_data_on_click(self):
        sig = Signal("name", _ref_only=True)
        sig.validate(required)
        result = form_validate_on_click(sig)
        assert isinstance(result, dict)
        assert "data_on_click" in result

    def test_exactly_one_key(self):
        sig = Signal("name", _ref_only=True)
        sig.validate(required)
        result = form_validate_on_click(sig)
        assert len(result) == 1

    def test_no_post_call(self):
        sig = Signal("name", _ref_only=True)
        sig.validate(required)
        result = form_validate_on_click(sig)
        actions = result["data_on_click"]
        all_js = " ".join(a.to_js() for a in actions)
        assert "sse(" not in all_js

    def test_validates_all_fields(self):
        s1 = Signal("name", _ref_only=True)
        s2 = Signal("email", _ref_only=True)
        s1.validate(required)
        s2.validate(email)
        result = form_validate_on_click(s1, s2)
        actions = result["data_on_click"]
        # 2 validate + 1 focus = 3
        assert len(actions) == 3

    def test_focus_first_error_enabled(self):
        sig = Signal("name", _ref_only=True)
        sig.validate(required)
        result = form_validate_on_click(sig)
        actions = result["data_on_click"]
        # 1 validate + 1 focus = 2
        assert len(actions) == 2
        focus_js = actions[-1].to_js()
        assert "aria-invalid" in focus_js

    def test_focus_first_error_disabled(self):
        sig = Signal("name", _ref_only=True)
        sig.validate(required)
        result = form_validate_on_click(sig, focus_first_error=False)
        actions = result["data_on_click"]
        # 1 validate only, no focus
        assert len(actions) == 1

    def test_validation_references_error_signal(self):
        sig = Signal("name", _ref_only=True)
        sig.validate(required)
        result = form_validate_on_click(sig)
        actions = result["data_on_click"]
        assert "$name_err" in actions[0].to_js()

    def test_raises_for_unvalidated_signal(self):
        sig = Signal("name", _ref_only=True)
        with pytest.raises(ValueError, match="no validation"):
            form_validate_on_click(sig)


# ============================================================================
# Accessibility helpers
# ============================================================================


class TestFormReset:
    def test_returns_expr(self):
        sig1 = Signal("email", "")
        sig2 = Signal("password", "")
        result = form_reset(sig1, sig2)
        assert hasattr(result, "to_js")

    def test_resets_to_initial_values(self):
        sig = Signal("count", "0")
        result = form_reset(sig).to_js()
        assert "$count" in result

    def test_multiple_signals(self):
        sigs = [Signal(f"s{i}", "") for i in range(5)]
        result = form_reset(*sigs).to_js()
        for i in range(5):
            assert f"$s{i}" in result

    def test_preserves_initial_string_values(self):
        sig = Signal("greeting", "hello")
        result = form_reset(sig).to_js()
        assert "hello" in result

    def test_preserves_initial_boolean(self):
        sig = Signal("active", False)
        result = form_reset(sig).to_js()
        assert "false" in result

    def test_preserves_initial_number(self):
        sig = Signal("count", 0)
        result = form_reset(sig).to_js()
        assert "$count" in result

    def test_mixed_initial_types(self):
        str_sig = Signal("name", "")
        bool_sig = Signal("active", False)
        num_sig = Signal("count", 0)
        result = form_reset(str_sig, bool_sig, num_sig).to_js()
        assert "$name" in result
        assert "$active" in result
        assert "$count" in result

    def test_uses_seq(self):
        """form_reset returns a seq() expression, which produces comma-separated assignments."""
        sig1 = Signal("a", "")
        sig2 = Signal("b", "")
        result = form_reset(sig1, sig2).to_js()
        assert "," in result

    def test_auto_clears_err_for_validated_signals(self):
        sig = Signal("email", "", _ref_only=True)
        sig.validate(email)
        js = form_reset(sig).to_js()
        assert "$email" in js
        assert "$email_err" in js

    def test_no_err_for_unvalidated_signals(self):
        sig = Signal("name", "")
        js = form_reset(sig).to_js()
        assert "$name" in js
        assert "err" not in js

    def test_extras_kwargs(self):
        sig = Signal("name", "")
        js = form_reset(sig, submitted=False).to_js()
        assert "$name" in js
        assert "$submitted" in js
        assert "false" in js

    def test_validated_plus_extras(self):
        sig = Signal("pw", "", _ref_only=True)
        sig.validate(min_length, 8)
        js = form_reset(sig, step=0).to_js()
        assert "$pw" in js
        assert "$pw_err" in js
        assert "$step" in js


# ============================================================================
# Signal.err property
# ============================================================================


class TestSignalErr:
    def test_returns_signal(self):
        sig = Signal("org", _ref_only=True)
        assert isinstance(sig.err, Signal)

    def test_name_is_derived(self):
        sig = Signal("org", _ref_only=True)
        assert sig.err._name == "org_err"

    def test_js_reference(self):
        sig = Signal("org", _ref_only=True)
        assert sig.err.to_js() == "$org_err"

    def test_inherits_ref_only(self):
        sig = Signal("org", _ref_only=True)
        assert sig.err._ref_only is True

    def test_inherits_ref_only_false(self):
        sig = Signal("email", "")
        assert sig.err._ref_only is False

    def test_inherits_namespace(self):
        sig = Signal("org", _ref_only=True, namespace="login")
        assert sig.err._namespace == "login"
        assert sig.err.to_js() == "$login_org_err"

    def test_cached_identity(self):
        sig = Signal("org", _ref_only=True)
        assert sig.err is sig.err

    def test_different_signals_different_errs(self):
        a = Signal("name", _ref_only=True)
        b = Signal("email", _ref_only=True)
        assert a.err is not b.err
        assert a.err._name != b.err._name

    def test_err_is_ref_only_no_data_signals(self):
        sig = Signal("org", _ref_only=True)
        assert sig.err.get_signal_attr() is None

    def test_err_usable_in_expressions(self):
        sig = Signal("org", _ref_only=True)
        js = sig.err.set("some error").to_js()
        assert "$org_err" in js

    def test_err_usable_with_if(self):
        sig = Signal("org", _ref_only=True)
        js = sig.err.if_("true").to_js()
        assert "$org_err" in js


# ============================================================================
# Signal.validate method
# ============================================================================


class TestSignalValidate:
    def test_returns_dict(self):
        sig = Signal("org", _ref_only=True)
        result = sig.validate(min_length, 3)
        assert isinstance(result, dict)

    def test_has_five_keys(self):
        sig = Signal("org", _ref_only=True)
        result = sig.validate(min_length, 3)
        assert len(result) == 5
        assert "data_bind" in result
        assert "data_on_blur" in result
        assert "data_on_input" in result
        assert "data_class_error" in result
        assert "data_attr_aria_invalid" in result

    def test_auto_calls_rule_with_self(self):
        """validate(min_length, 3) calls min_length(self, 3) internally."""
        sig = Signal("org", _ref_only=True)
        result = sig.validate(min_length, 3, "Organization")
        js = result["data_on_blur"].to_js()
        assert "Organization is required" in js
        assert "$org" in js

    def test_accepts_pre_built_expr(self):
        """validate(expr) works with a pre-built validation expression."""
        sig = Signal("org", _ref_only=True)
        result = sig.validate(min_length(sig, 3))
        js = result["data_on_blur"].to_js()
        assert "$org_err" in js

    def test_uses_derived_err_signal(self):
        sig = Signal("org", _ref_only=True)
        result = sig.validate(min_length, 3)
        js = result["data_on_blur"].to_js()
        assert "$org_err" in js

    def test_input_only_revalidates_when_error(self):
        sig = Signal("org", _ref_only=True)
        result = sig.validate(min_length, 3)
        js = result["data_on_input"].to_js()
        assert "if" in js
        assert "$org_err" in js

    def test_class_error_is_err_signal(self):
        sig = Signal("org", _ref_only=True)
        result = sig.validate(min_length, 3)
        assert result["data_class_error"] is sig.err

    def test_aria_invalid_is_boolean_conditional(self):
        sig = Signal("org", _ref_only=True)
        result = sig.validate(min_length, 3)
        js = result["data_attr_aria_invalid"].to_js()
        assert "true" in js and "false" in js

    def test_includes_data_bind(self):
        """validate() includes data_bind=self for two-way binding."""
        sig = Signal("org", _ref_only=True)
        result = sig.validate(min_length, 3)
        assert result["data_bind"] is sig

    def test_custom_event(self):
        sig = Signal("terms", _ref_only=True)
        result = sig.validate(checked, event="change")
        assert "data_on_change" in result
        assert "data_on_input" not in result

    def test_with_email_auto_call(self):
        sig = Signal("em", _ref_only=True)
        result = sig.validate(email)
        js = result["data_on_blur"].to_js()
        assert "Email is required" in js
        assert "$em_err" in js

    def test_stores_validation_expr(self):
        """validate() stores the expression for form_submit to read."""
        sig = Signal("org", _ref_only=True)
        sig.validate(min_length, 3)
        assert hasattr(sig, "_validation_expr")
        js = sig._validation_expr.to_js()
        assert "$org" in js
