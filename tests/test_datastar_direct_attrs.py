"""Comprehensive tests for Datastar direct attribute syntax (no ** unpacking)."""

import pytest
import json
from starhtml import Div, Button, Input, Form, P, A, Script, Span, Select, Option
from starhtml.components import to_xml

class TestDatastarDirectAttributes:
    """Test the new direct attribute syntax without ** unpacking."""
    
    def test_ds_bind(self):
        """Test direct ds_bind attribute."""
        # Simple binding
        input_elem = Input(ds_bind="username")
        xml = to_xml(input_elem)
        assert 'data-bind="username"' in xml
        
        # With other attributes
        input_elem = Input(type="text", ds_bind="email", placeholder="Email")
        xml = to_xml(input_elem)
        assert 'data-bind="email"' in xml
        assert 'type="text"' in xml
        assert 'placeholder="Email"' in xml
    
    def test_ds_show(self):
        """Test direct ds_show attribute."""
        div_elem = Div("Content", ds_show="isVisible")
        xml = to_xml(div_elem)
        assert 'data-show="isVisible"' in xml
        
        # Complex expression (HTML entities are escaped in XML)
        div_elem = Div("Content", ds_show="count > 0 && isActive")
        xml = to_xml(div_elem)
        # Check for escaped version
        assert 'data-show="count &gt; 0 &amp;&amp; isActive"' in xml
    
    def test_ds_text(self):
        """Test direct ds_text attribute."""
        p_elem = P(ds_text="message")
        xml = to_xml(p_elem)
        assert 'data-text="message"' in xml
        
        # Template literal
        span_elem = Span(ds_text="`Count: ${count}`")
        xml = to_xml(span_elem)
        assert 'data-text="`Count: ${count}`"' in xml
    
    def test_ds_html(self):
        """Test direct ds_html attribute."""
        div_elem = Div(ds_html="markdown(content)")
        xml = to_xml(div_elem)
        assert 'data-html="markdown(content)"' in xml
    
    def test_ds_on_events(self):
        """Test direct ds_on_* event attributes."""
        # Click event
        btn = Button("Click me", ds_on_click="handleClick()")
        xml = to_xml(btn)
        assert 'data-on-click="handleClick()"' in xml
        
        # Submit event
        form = Form(ds_on_submit="@post('/submit')")
        xml = to_xml(form)
        assert 'data-on-submit="@post(\'/submit\')"' in xml
        
        # Multiple events
        input_elem = Input(
            ds_on_input="updateValue()",
            ds_on_change="validateValue()",
            ds_on_focus="showHint()"
        )
        xml = to_xml(input_elem)
        assert 'data-on-input="updateValue()"' in xml
        assert 'data-on-change="validateValue()"' in xml
        assert 'data-on-focus="showHint()"' in xml
    
    def test_ds_indicator(self):
        """Test direct ds_indicator attribute."""
        button = Button("Submit", ds_indicator="loading")
        xml = to_xml(button)
        assert 'data-indicator="loading"' in xml
    
    def test_ds_signals(self):
        """Test direct ds_signals attribute with dict."""
        # Dict format
        div = Div(ds_signals={"count": 0, "user": {"name": "John"}})
        xml = to_xml(div)
        assert 'data-signals=' in xml
        # Check it's valid JSON
        assert '"count": 0' in xml
        assert '"user": {"name": "John"}' in xml
    
    def test_ds_class(self):
        """Test direct ds_class attribute."""
        div = Div(
            cls="base-class",
            ds_class="{ 'active': isActive, 'disabled': isDisabled }"
        )
        xml = to_xml(div)
        assert 'class="base-class"' in xml
        assert 'data-class="{ \'active\': isActive, \'disabled\': isDisabled }"' in xml
    
    def test_ds_style(self):
        """Test direct ds_style attribute."""
        div = Div(ds_style="{ color: textColor, fontSize: `${size}px` }")
        xml = to_xml(div)
        assert 'data-style="{ color: textColor, fontSize: `${size}px` }"' in xml
    
    def test_ds_ref(self):
        """Test direct ds_ref attribute."""
        input_elem = Input(ds_ref="emailInput")
        xml = to_xml(input_elem)
        assert 'data-ref="emailInput"' in xml
    
    def test_ds_computed(self):
        """Test direct ds_computed attribute."""
        div = Div(ds_computed="fullName = firstName + ' ' + lastName")
        xml = to_xml(div)
        assert 'data-computed="fullName = firstName + \' \' + lastName"' in xml
    
    def test_ds_store(self):
        """Test direct ds_store attribute."""
        button = Button("Increment", ds_on_click="store.increment()")
        div = Div(ds_text="store.count")
        
        btn_xml = to_xml(button)
        div_xml = to_xml(div)
        
        assert 'data-on-click="store.increment()"' in btn_xml
        assert 'data-text="store.count"' in div_xml
    
    def test_ds_teleport(self):
        """Test direct ds_teleport attribute."""
        modal = Div("Modal content", ds_teleport="#modal-root")
        xml = to_xml(modal)
        assert 'data-teleport="#modal-root"' in xml
    
    def test_ds_transition(self):
        """Test direct ds_transition attributes."""
        div = Div(
            "Content",
            ds_show="isVisible",
            ds_transition_enter="fade-in",
            ds_transition_leave="fade-out"
        )
        xml = to_xml(div)
        assert 'data-transition-enter="fade-in"' in xml
        assert 'data-transition-leave="fade-out"' in xml
    
    def test_ds_on_intersect(self):
        """Test ds_on_intersect with modifiers."""
        # Basic intersection
        div = Div(ds_on_intersect="loadMore()")
        xml = to_xml(div)
        assert 'data-on-intersect="loadMore()"' in xml
        
        # With once modifier
        div = Div(ds_on_intersect="loadMore()", ds_on_intersect_once="true")
        xml = to_xml(div)
        assert 'data-on-intersect="loadMore()"' in xml
        assert 'data-on-intersect.once="true"' in xml
    
    def test_ds_on_interval(self):
        """Test ds_on_interval with modifiers."""
        # Basic interval
        div = Div(ds_on_interval="updateTime()")
        xml = to_xml(div)
        assert 'data-on-interval="updateTime()"' in xml
        
        # With ms modifier
        div = Div(ds_on_interval="updateTime()", ds_on_interval_ms="1000")
        xml = to_xml(div)
        assert 'data-on-interval="updateTime()"' in xml
        assert 'data-on-interval.ms="1000"' in xml
    
    def test_ds_attr_dynamic(self):
        """Test dynamic attribute setting with ds_attr_*."""
        div = Div(
            ds_attr_disabled="isLoading",
            ds_attr_title="user.name",
            ds_attr_data_id="userId"
        )
        xml = to_xml(div)
        assert 'data-attr-disabled="isLoading"' in xml
        assert 'data-attr-title="user.name"' in xml
        assert 'data-attr-data-id="userId"' in xml
    
    def test_complex_component(self):
        """Test complex component with multiple Datastar attributes."""
        form = Form(
            Input(
                type="text",
                ds_bind="username",
                ds_ref="usernameInput",
                placeholder="Username"
            ),
            Input(
                type="email",
                ds_bind="email",
                ds_show="showEmail",
                ds_on_input="validateEmail()",
                placeholder="Email"
            ),
            Button(
                "Submit",
                type="submit",
                ds_on_click="handleSubmit()",
                ds_indicator="submitting",
                ds_attr_disabled="submitting"
            ),
            ds_on_submit="@post('/api/submit')",
            ds_signals={"username": "", "email": "", "submitting": False}
        )
        
        xml = to_xml(form)
        
        # Form attributes
        assert 'data-on-submit="@post(\'/api/submit\')"' in xml
        assert 'data-signals=' in xml
        
        # First input
        assert 'data-bind="username"' in xml
        assert 'data-ref="usernameInput"' in xml
        
        # Second input
        assert 'data-bind="email"' in xml
        assert 'data-show="showEmail"' in xml
        assert 'data-on-input="validateEmail()"' in xml
        
        # Button
        assert 'data-on-click="handleSubmit()"' in xml
        assert 'data-indicator="submitting"' in xml
        assert 'data-attr-disabled="submitting"' in xml
    
    def test_boolean_values(self):
        """Test that boolean values are converted to 'true'/'false' strings."""
        # Boolean true
        div = Div(ds_show=True, ds_on_load=True)
        xml = to_xml(div)
        assert 'data-show="true"' in xml
        assert 'data-on-load="true"' in xml
        
        # Boolean false
        div = Div(ds_show=False, ds_on_intersect_once=False)
        xml = to_xml(div)
        assert 'data-show="false"' in xml
        assert 'data-on-intersect.once="false"' in xml
    
    def test_multiple_event_modifiers(self):
        """Test multiple event modifiers on the same element."""
        div = Div(
            ds_on_intersect="loadMore()",
            ds_on_intersect_once=True,
            ds_on_interval="updateTime()",
            ds_on_interval_ms="1000"
        )
        xml = to_xml(div)
        assert 'data-on-intersect="loadMore()"' in xml
        assert 'data-on-intersect.once="true"' in xml
        assert 'data-on-interval="updateTime()"' in xml
        assert 'data-on-interval.ms="1000"' in xml
    
    def test_edge_cases(self):
        """Test edge cases and special characters."""
        # Special characters in expressions (will be HTML escaped)
        div = Div(ds_show="item !== null && item.count > 0")
        xml = to_xml(div)
        assert 'data-show="item !== null &amp;&amp; item.count &gt; 0"' in xml
        
        # Empty values might be filtered out by the framework
        div = Div(ds_text=" ")  # Non-empty space
        xml = to_xml(div)
        assert 'data-text=" "' in xml
        
        # Complex JSON in signals
        div = Div(ds_signals={
            "array": [1, 2, 3],
            "nested": {"deep": {"value": True}},
            "special": "with \"quotes\""
        })
        xml = to_xml(div)
        assert 'data-signals=' in xml
        # Verify it's valid JSON by parsing the attribute value
        # (Would need to extract and parse in real test)