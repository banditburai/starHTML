"""Tests for the modern Datastar API (no legacy helpers)."""

from starhtml import *
from starhtml.datastar import (
    Signal,
    f_,
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
        assert f_("Hello {name}", name=js("$name")) == "`Hello ${$name}`"
        assert (
            f_(
                "rotate({rotation}deg) scale({scale})",
                rotation=js("$rotation"),
                scale=js("$scale"),
            )
            == "`rotate(${$rotation}deg) scale(${$scale})`"
        )

        result = f_(
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
        # Note: js() now minifies, so spaces are removed
        assert 'data-show="$count>0"' in html

    def test_data_show_fouc_prevention(self):
        """FOUC prevention: initially-false data_show injects display:none."""
        sig = Signal("vis", False)
        html = str(Div("x", data_show=sig))
        assert 'style="display:none"' in html

    def test_data_show_fouc_merges_with_existing_style(self):
        """FOUC prevention appends display:none to existing inline style."""
        sig = Signal("vis", False)
        html = str(Div("x", data_show=sig, style="color:red"))
        assert "color:red; display:none" in html

    def test_data_show_fouc_skipped_when_initially_true(self):
        """No display:none injected when signal is initially true."""
        sig = Signal("vis", True)
        html = str(Div("x", data_show=sig))
        assert "display:none" not in html

    def test_data_text(self):
        html = str(Div("x", data_text="Hello"))
        assert 'data-text="Hello"' in html
        html = str(Div("x", data_text=js("$message")))
        assert 'data-text="$message"' in html
        html = str(Div("x", data_text=f_("User: {name}", name=js("$name"))))
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
        # Note: js() now minifies, so spaces around operators are removed
        # RC6 uses colon syntax: data-computed:fullName
        assert res == {"data-computed:fullName": "$firstName+' '+$lastName"}


class TestSignals:
    def test_data_signals_list(self):
        res = attrs_of_kwargs(data_signals=[Signal("count", 0), Signal("name", "John"), Signal("active", True)])
        # Default ifmissing=True uses individual attributes
        assert "data-signals:count__ifmissing" in res
        assert "data-signals:name__ifmissing" in res
        assert "data-signals:active__ifmissing" in res


class TestEventHandlers:
    def test_on_click_basic(self):
        res = attrs_of_kwargs(data_on_click=("handleClick()", {}))
        # RC6 uses colon syntax: data-on:click
        assert "data-on:click" in res
        assert "handleClick()" in str(res["data-on:click"])

    def test_on_click_with_modifiers(self):
        res = attrs_of_kwargs(data_on_click=("submit()", {"once": True, "prevent": True}))
        # RC6 uses colon syntax: data-on:click
        assert "data-on:click__once__prevent" in res

    def test_on_input_with_debounce(self):
        res = attrs_of_kwargs(data_on_input=("search()", {"debounce": "500ms"}))
        # RC6 uses colon syntax: data-on:input
        assert "data-on:input__debounce.500ms" in res
        res = attrs_of_kwargs(data_on_input=("search()", {"debounce": "300ms"}))
        assert "data-on:input__debounce.300ms" in res

    def test_mixed_modifiers(self):
        res = attrs_of_kwargs(data_on_input=("search()", {"prevent": True, "debounce": "500ms"}))
        # RC6 uses colon syntax: data-on:input
        assert "data-on:input__prevent__debounce.500ms" in res

    def test_on_interval_and_intersect(self):
        # These are separate Datastar plugins, use hyphen syntax (not colon)
        # data-on-interval uses setInterval, data-on-intersect uses IntersectionObserver
        assert "data-on-interval__duration.1s" in attrs_of_kwargs(data_on_interval=("tick()", {"duration": "1s"}))
        assert "data-on-interval__duration.500ms" in attrs_of_kwargs(
            data_on_interval=("update()", {"duration": "500ms"})
        )
        assert "data-on-intersect__once__half" in attrs_of_kwargs(
            data_on_intersect=("loadMore()", {"once": True, "half": True})
        )

    def test_generic_on(self):
        res = attrs_of_kwargs(data_on_custom_event=("handleCustom()", {"once": True}))
        # RC6 uses colon syntax: data-on:custom-event
        assert "data-on:custom-event__once" in res


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
        # RC6 uses colon syntax: data-on:click
        assert "data-on:click__once__prevent" in html
        # attrs_of_simple uses hyphen syntax (test helper, not process_datastar_kwargs)
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
        # RC6 uses colon syntax: data-on:submit
        assert "data-on:submit__prevent" in html
        assert "data-bind" in html

    def test_conditional_styling(self):
        div = Div(
            "Content",
            **attrs_of_simple(
                style_background=js("$hovered").if_("#e3f2fd", "#fff").to_js(),
                style_opacity=js("$loading").if_(0.5, 1).to_js(),
                style_transform=f_("scale({scale})", scale=js("$scale")),
            ),
        )
        html = str(div)
        assert "data-style-background" in html
        assert "data-style-opacity" in html
        assert "data-style-transform" in html
        assert "`scale(${$scale})`" in html


class TestActionUrlNormalization:
    """``post()`` / ``get()`` / ``put()`` / ``delete()`` / ``patch()`` should
    force a leading slash on bare resource paths so that the browser's
    ``fetch()`` resolves the URL absolutely instead of relative to the
    current page URL.

    Background: under per-resource URL routing (e.g. ``/chat/{uuid}``),
    a Datastar action like ``post('chat/foo')`` would resolve to
    ``/chat/chat/foo`` from any sub-resource page — silently broken in
    a way that doesn't surface in tests or on landing pages. Forcing the
    leading slash at the helper level prevents the entire bug class.
    """

    def test_post_bare_resource_gets_leading_slash(self):
        # 'chat/foo' must become '/chat/foo' so it's an absolute URL.
        assert str(post("chat/foo")) == "@post('/chat/foo')"

    def test_get_bare_resource_gets_leading_slash(self):
        assert str(get("api/users")) == "@get('/api/users')"

    def test_put_bare_resource_gets_leading_slash(self):
        assert str(put("items/42")) == "@put('/items/42')"

    def test_delete_bare_resource_gets_leading_slash(self):
        assert str(delete("things/x")) == "@delete('/things/x')"

    def test_patch_bare_resource_gets_leading_slash(self):
        assert str(patch("things/x")) == "@patch('/things/x')"

    def test_already_absolute_path_unchanged(self):
        assert str(post("/chat/foo")) == "@post('/chat/foo')"
        assert str(get("/api/users")) == "@get('/api/users')"

    def test_full_https_url_unchanged(self):
        assert str(post("https://api.example.com/v1/foo")) == "@post('https://api.example.com/v1/foo')"

    def test_full_http_url_unchanged(self):
        assert str(post("http://localhost:8000/foo")) == "@post('http://localhost:8000/foo')"

    def test_websocket_url_unchanged(self):
        assert str(get("ws://localhost/socket")) == "@get('ws://localhost/socket')"
        assert str(get("wss://api.example.com/socket")) == "@get('wss://api.example.com/socket')"

    def test_explicit_relative_dot_unchanged(self):
        # Author explicitly used './' — preserve their intent.
        assert str(post("./relative")) == "@post('./relative')"

    def test_explicit_parent_relative_unchanged(self):
        assert str(post("../parent")) == "@post('../parent')"

    def test_query_only_unchanged(self):
        # Query-only refresh of the current URL — preserve.
        assert str(get("?refresh=1")) == "@get('?refresh=1')"

    def test_fragment_only_unchanged(self):
        assert str(get("#anchor")) == "@get('#anchor')"

    def test_datastar_expression_prefix_unchanged(self):
        # An '@'-prefixed value would be a Datastar expression, not a URL.
        # Defensive: preserve unchanged so the user can debug their typo.
        assert str(post("@signal")) == "@post('@signal')"

    def test_normalization_preserves_kwargs(self):
        # The kwargs path renders an options object after the URL —
        # normalization must apply BEFORE the kwargs render so the
        # options object is unaffected.
        result = str(post("chat/ui-state", contentType="json"))
        assert result.startswith("@post('/chat/ui-state'")
        assert "contentType:" in result

    def test_payload_with_expression_preserves_underscore_keys(self):
        # When an options dict contains an Expr, JSON serialization falls back
        # to manual JS object rendering. That path must preserve payload keys so
        # server query-param binding can still resolve names like project_id.
        project_id = Signal("project_id")
        result = str(get("/projects", payload={"project_id": project_id}))
        assert 'payload: ({"project_id": $project_id})' in result
        assert "project-id" not in result

    def test_fstring_with_dynamic_segment(self):
        # The most common pattern that bit zacks: f-string with a UUID.
        thread_id = "abc-123"
        assert str(post(f"chat/select-thread/{thread_id}")) == "@post('/chat/select-thread/abc-123')"


class TestForceAbsoluteUrlHelper:
    """The shared ``_force_absolute_url`` helper that powers both the
    ``post``/``get``/``put``/``delete``/``patch`` action helpers and the
    realtime ``push_state``/``replace_state`` history helpers. Direct
    helper tests so coverage is independent of the call-site flow.
    """

    def test_bare_path_gets_leading_slash(self):
        from starhtml.datastar import _force_absolute_url

        assert _force_absolute_url("foo") == "/foo"
        assert _force_absolute_url("api/v1/users") == "/api/v1/users"

    def test_already_absolute_unchanged(self):
        from starhtml.datastar import _force_absolute_url

        assert _force_absolute_url("/foo") == "/foo"
        assert _force_absolute_url("//example.com/foo") == "//example.com/foo"  # protocol-relative

    def test_explicit_relative_unchanged(self):
        from starhtml.datastar import _force_absolute_url

        assert _force_absolute_url("./foo") == "./foo"
        assert _force_absolute_url("../foo") == "../foo"

    def test_full_urls_unchanged(self):
        from starhtml.datastar import _force_absolute_url

        assert _force_absolute_url("http://x.test/foo") == "http://x.test/foo"
        assert _force_absolute_url("https://x.test/foo") == "https://x.test/foo"
        assert _force_absolute_url("ws://x.test/socket") == "ws://x.test/socket"
        assert _force_absolute_url("wss://x.test/socket") == "wss://x.test/socket"

    def test_query_and_fragment_only_unchanged(self):
        from starhtml.datastar import _force_absolute_url

        assert _force_absolute_url("?refresh=1") == "?refresh=1"
        assert _force_absolute_url("#anchor") == "#anchor"

    def test_datastar_expression_unchanged(self):
        from starhtml.datastar import _force_absolute_url

        assert _force_absolute_url("@signal") == "@signal"

    def test_empty_string_unchanged(self):
        from starhtml.datastar import _force_absolute_url

        assert _force_absolute_url("") == ""


class TestStateHelpersNormalization:
    """``push_state`` and ``replace_state`` should apply the same URL
    normalization as the action helpers, so a bare resource path doesn't
    silently push the wrong URL under per-resource routing.
    """

    def test_push_state_normalizes_bare_url(self):
        from starhtml import push_state

        result = push_state("dashboard")
        # ('elements', (script_element, selector, mode, ...))
        script_html = str(result[1][0])
        assert '"/dashboard"' in script_html
        # Plain (non-slashed) form should not appear in the JSON-encoded URL.
        assert '"dashboard"' not in script_html
        assert "history.pushState" in script_html

    def test_push_state_preserves_absolute_url(self):
        from starhtml import push_state

        result = push_state("/chat/abc")
        script_html = str(result[1][0])
        assert '"/chat/abc"' in script_html

    def test_push_state_fstring_uuid(self):
        from starhtml import push_state

        thread_id = "abc-123"
        result = push_state(f"chat/{thread_id}")
        script_html = str(result[1][0])
        assert '"/chat/abc-123"' in script_html

    def test_replace_state_normalizes_bare_url(self):
        from starhtml import replace_state

        result = replace_state("dashboard")
        script_html = str(result[1][0])
        assert '"/dashboard"' in script_html
        assert "history.replaceState" in script_html

    def test_replace_state_preserves_full_url(self):
        from starhtml import replace_state

        # Full URLs (e.g., to a different host) should not be normalized.
        result = replace_state("https://other.example/foo")
        script_html = str(result[1][0])
        assert '"https://other.example/foo"' in script_html


class TestRedirectHelper:
    """``redirect()`` should perform full-page navigation via
    ``window.location`` and apply the same URL normalization as the
    history helpers, so a bare URL doesn't navigate to the wrong place
    under per-resource routing.
    """

    def test_redirect_normalizes_bare_url(self):
        from starhtml import redirect

        result = redirect("login")
        script_html = str(result[1][0])
        assert '"/login"' in script_html
        assert "window.location" in script_html
        assert "setTimeout" in script_html  # deferred past in-flight patches

    def test_redirect_preserves_absolute_path(self):
        from starhtml import redirect

        result = redirect("/dashboard")
        script_html = str(result[1][0])
        assert '"/dashboard"' in script_html

    def test_redirect_preserves_full_https_url(self):
        from starhtml import redirect

        # The Stripe-checkout pattern: redirect to a fully-qualified
        # external URL should NOT be normalized.
        url = "https://checkout.stripe.com/c/pay/cs_test_abc123"
        result = redirect(url)
        script_html = str(result[1][0])
        assert f'"{url}"' in script_html

    def test_redirect_fstring_with_dynamic_segment(self):
        from starhtml import redirect

        thread_id = "abc-123"
        result = redirect(f"chat/{thread_id}")
        script_html = str(result[1][0])
        assert '"/chat/abc-123"' in script_html
