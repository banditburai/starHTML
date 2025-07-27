"""Shared test utilities and assertions for starhtml test suite."""

import re
from typing import Any
from xml.etree import ElementTree as ET

import pytest

# Common test data fixtures
COMMON_FORM_DATA = {"username": "testuser", "email": "test@example.com", "password": "secret123"}

COMMON_ATTRIBUTES = {"cls": "btn btn-primary", "data_value": "123", "hx_post": "/submit", "ds_show": "visible"}


class HTMLAssertions:
    """Common HTML assertion helpers."""

    @staticmethod
    def assert_has_attribute(html: str, attr_name: str, attr_value: str | None = None) -> None:
        """Assert that an HTML element has a specific attribute with optional value check."""
        # Parse as XML for more reliable attribute checking
        if not html.strip().startswith("<"):
            pytest.fail(f"Invalid HTML: {html}")

        # Handle self-closing tags
        if html.strip().endswith("/>"):
            # Already self-closing
            root = ET.fromstring(html)
        else:
            # Try parsing as-is first
            try:
                root = ET.fromstring(html)
            except ET.ParseError:
                # If it fails, it might be a non-self-closing single tag like <input>
                # Try making it self-closing
                if not html.strip().endswith(">"):
                    pytest.fail(f"Invalid HTML: {html}")
                tag_html = html.strip()[:-1] + "/>"
                try:
                    root = ET.fromstring(tag_html)
                except ET.ParseError:
                    pytest.fail(f"Could not parse HTML: {html}")

        # Check for attribute
        if attr_value is not None:
            actual_value = root.get(attr_name)
            assert actual_value == attr_value, f"Expected {attr_name}='{attr_value}', got '{actual_value}'"
        else:
            assert attr_name in root.attrib, f"Attribute '{attr_name}' not found in element"

    @staticmethod
    def assert_has_content(html: str, content: str) -> None:
        """Assert that an HTML element contains specific text content."""
        # Remove tags to get text content
        text = re.sub(r"<[^>]+>", "", html)
        assert content in text, f"Content '{content}' not found in '{text}'"

    @staticmethod
    def assert_element_structure(
        html: str, tag_name: str, attributes: dict[str, str] | None = None, content: str | None = None
    ) -> None:
        """Assert complete element structure including tag, attributes, and content."""
        # Basic tag check
        assert html.strip().startswith(f"<{tag_name}"), f"Expected {tag_name} element"

        # Check attributes if provided
        if attributes:
            for attr, value in attributes.items():
                HTMLAssertions.assert_has_attribute(html, attr, value)

        # Check content if provided
        if content is not None:
            HTMLAssertions.assert_has_content(html, content)

    @staticmethod
    def assert_valid_html_document(html: str) -> None:
        """Assert that the HTML is a valid document structure."""
        assert "<!DOCTYPE html>" in html or "<!doctype html>" in html.lower()
        assert "<html" in html
        assert "<head>" in html
        assert "<body>" in html
        assert "</html>" in html


class FormTestHelpers:
    """Helpers for form-related tests."""

    @staticmethod
    def create_test_form(fields: list[dict[str, Any]], **form_attrs) -> str:
        """Create a test form with given fields."""
        from starhtml.tags import Form, Input, Label

        children = []
        for field in fields:
            if field.get("label"):
                children.append(Label(field["label"], fr=field.get("name", "")))

            field_attrs = {k: v for k, v in field.items() if k not in ["label"]}
            children.append(Input(**field_attrs))

        return str(Form(*children, **form_attrs))

    @staticmethod
    def assert_form_has_fields(form_html: str, field_names: list[str]) -> None:
        """Assert that a form contains all specified input fields."""
        for field_name in field_names:
            assert f'name="{field_name}"' in form_html, f"Field '{field_name}' not found in form"


class DatastarTestHelpers:
    """Helpers for Datastar-specific tests."""

    @staticmethod
    def assert_has_datastar_attribute(html: str, ds_attr: str, value: str | None = None) -> None:
        """Assert that an element has a specific Datastar attribute."""
        attr_name = f"data-{ds_attr.replace('_', '-')}"
        HTMLAssertions.assert_has_attribute(html, attr_name, value)

    @staticmethod
    def create_datastar_element(tag: str, content: str = "", **ds_attrs) -> str:
        """Create an element with Datastar attributes."""
        from starhtml.html import create_element

        element = create_element(tag, content, **ds_attrs)
        return str(element)


class SSETestHelpers:
    """Helpers for SSE-related tests."""

    @staticmethod
    def assert_valid_sse_format(sse_content: str) -> None:
        """Assert that content follows valid SSE format."""
        lines = sse_content.strip().split("\n")

        # Check for event type
        assert any(line.startswith("event:") for line in lines), "SSE must have an event type"

        # Check for data
        assert any(line.startswith("data:") for line in lines), "SSE must have data"

        # Check for double newline at end
        assert sse_content.endswith("\n\n"), "SSE must end with double newline"

    @staticmethod
    def parse_sse_data(sse_content: str) -> dict[str, Any]:
        """Parse SSE content into structured data."""
        import json

        lines = sse_content.strip().split("\n")

        event_type = None
        data_lines = []

        for line in lines:
            if line.startswith("event:"):
                event_type = line[6:].strip()
            elif line.startswith("data:"):
                data_lines.append(line[5:].strip())

        # Join data lines and parse as JSON
        data_str = "\n".join(data_lines)
        try:
            data = json.loads(data_str)
        except json.JSONDecodeError:
            data = data_str

        return {"event": event_type, "data": data}


# Pytest fixtures for common test data
@pytest.fixture
def sample_form_fields():
    """Provide sample form field definitions."""
    return [
        {"type": "text", "name": "username", "label": "Username", "required": True},
        {"type": "email", "name": "email", "label": "Email", "required": True},
        {"type": "password", "name": "password", "label": "Password", "required": True},
    ]


@pytest.fixture
def sample_datastar_attrs():
    """Provide sample Datastar attributes."""
    return {"ds_show": "isVisible", "ds_text": "message", "ds_on_click": "handleClick", "ds_bind": "inputValue"}


@pytest.fixture
def html_assertions():
    """Provide HTML assertion helpers."""
    return HTMLAssertions()


@pytest.fixture
def form_helpers():
    """Provide form test helpers."""
    return FormTestHelpers()


@pytest.fixture
def datastar_helpers():
    """Provide Datastar test helpers."""
    return DatastarTestHelpers()


@pytest.fixture
def sse_helpers():
    """Provide SSE test helpers."""
    return SSETestHelpers()
