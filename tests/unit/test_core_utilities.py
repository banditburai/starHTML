"""Comprehensive tests for StarHTML core utilities.

This module consolidates tests for core utility functions including:
- String and URI utilities
- Date/time handling
- Form processing
- Type conversion utilities
- Cookie handling
- Response creation
"""

import os
import tempfile
from datetime import datetime

import pytest
from starlette.applications import Starlette

from starhtml.realtime import EventStream
from starhtml.server import (
    Client,
    JSONResponse,
    Redirect,
    cookie,
)
from starhtml.utils import (
    HttpHeader,
    _fix_anno,
    _formitem,
    _mk_list,
    decode_uri,
    flat_tuple,
    flat_xt,
    form2dict,
    get_key,
    parsed_date,
    qp,
    snake2hyphens,
    unqid,
    uri,
)


class TestDateUtilities:
    """Test date and time parsing utilities."""

    def test_parsed_date_iso_format(self):
        """Test parsed_date with ISO format."""
        date_str = "2023-12-25T10:30:00Z"
        result = parsed_date(date_str)
        assert isinstance(result, datetime)
        assert result.year == 2023
        assert result.month == 12
        assert result.day == 25
        assert result.hour == 10
        assert result.minute == 30

    def test_parsed_date_simple_date(self):
        """Test parsed_date with simple date."""
        date_str = "2023-01-15"
        result = parsed_date(date_str)
        assert isinstance(result, datetime)
        assert result.year == 2023
        assert result.month == 1
        assert result.day == 15

    def test_parsed_date_with_timezone(self):
        """Test parsed_date with timezone info."""
        date_str = "2023-12-25T10:30:00+00:00"
        result = parsed_date(date_str)
        assert isinstance(result, datetime)
        assert result.tzinfo is not None

    def test_parsed_date_invalid(self):
        """Test parsed_date with invalid date string."""
        with pytest.raises(ValueError):
            parsed_date("not-a-date")


class TestStringUtilities:
    """Test string manipulation utilities."""

    def test_snake2hyphens(self):
        """Test snake_case to hyphen-case conversion."""
        # Function converts to camelCase then to hyphenated words
        assert snake2hyphens("hello_world") == "Hello-World"
        assert snake2hyphens("test_case_name") == "Test-Case-Name"
        assert snake2hyphens("no_change") == "No-Change"

    def test_unqid(self):
        """Test unique ID generation."""
        id1 = unqid()
        id2 = unqid()
        assert isinstance(id1, str)
        assert isinstance(id2, str)
        assert id1 != id2
        assert len(id1) > 0

    def test_unqid_format(self):
        """Test unique ID format."""
        # unqid doesn't take parameters, returns URL-safe ID starting with _
        uid = unqid()
        assert uid.startswith("_")
        assert len(uid) > 1


class TestURIUtilities:
    """Test URI encoding/decoding utilities."""

    def test_uri_encoding(self):
        """Test URI encoding."""
        # uri takes an arg and optional kwargs
        assert uri("hello world") == "hello%20world/"
        assert uri("test@example.com") == "test%40example.com/"
        assert uri("path", foo="bar") == "path/foo=bar"

    def test_decode_uri(self):
        """Test URI decoding."""
        # decode_uri returns (path, query_dict) tuple
        path, params = decode_uri("hello%20world")
        assert path == "hello world"
        assert params == {}

        path, params = decode_uri("path/foo=bar&baz=qux")
        assert path == "path"
        assert "foo" in params

    def test_uri_roundtrip(self):
        """Test encoding and decoding roundtrip."""
        original = "test path"
        encoded = uri(original, param="value")
        path, params = decode_uri(encoded)
        assert path == original
        assert params.get("param") == "value"


class TestListUtilities:
    """Test list manipulation utilities."""

    def test_mk_list(self):
        """Test making lists from various inputs."""
        # _mk_list takes type and value parameters
        assert _mk_list(str, "single") == ["single"]
        assert _mk_list(str, ["a", "b"]) == ["a", "b"]
        assert _mk_list(int, "5") == [5]
        assert _mk_list(int, ["1", "2", "3"]) == [1, 2, 3]

    def test_flat_tuple(self):
        """Test flattening tuples."""
        assert flat_tuple((1, 2, 3)) == (1, 2, 3)
        assert flat_tuple([(1, 2), 3]) == (1, 2, 3)
        assert flat_tuple([]) == ()
        assert flat_tuple("single") == ("single",)


class TestFormUtilities:
    """Test form handling utilities."""

    def test_form2dict_simple(self):
        """Test converting simple form data to dict."""
        form_data = {"name": "John", "age": "30"}
        result = form2dict(form_data)
        assert result == {"name": "John", "age": "30"}

    def test_form2dict_multi_values(self):
        """Test form2dict with multiple values."""
        form_data = {"tags": ["python", "web", "testing"]}
        result = form2dict(form_data)
        assert result["tags"] == ["python", "web", "testing"]

    def test_formitem(self):
        """Test form item processing."""
        # _formitem takes form and key parameters
        form_dict = {"name": "John", "tags": ["a", "b"]}
        assert _formitem(form_dict, "name") == "John"
        assert _formitem(form_dict, "tags") == ["a", "b"]
        assert _formitem(form_dict, "missing") is None


class TestTypeUtilities:
    """Test type conversion and annotation utilities."""

    def test_fix_anno_basic(self):
        """Test fixing type annotations."""
        # _fix_anno takes annotation and value
        assert _fix_anno(str, "test") == "test"
        assert _fix_anno(int, "5") == 5
        assert _fix_anno(bool, "true")


class TestQueryParameters:
    """Test query parameter handling."""

    def test_qp_basic(self):
        """Test basic query parameter creation."""
        # qp takes path and keyword arguments
        result = qp("/path")
        assert result == "/path"

        result = qp("/path", key="value")
        assert result == "/path?key=value"

    def test_qp_multiple_params(self):
        """Test query parameters with multiple values."""
        result = qp("/path", name="John", age=30)
        assert "name=John" in result
        assert "age=30" in result

    def test_qp_path_substitution(self):
        """Test path parameter substitution."""
        result = qp("/users/{id}", id=123)
        assert result == "/users/123"


class TestCookieHandling:
    """Test cookie creation and manipulation."""

    def test_cookie_basic(self):
        """Test basic cookie creation."""
        # cookie returns HttpHeader object
        c = cookie("session", "abc123")
        assert isinstance(c, HttpHeader)
        assert c.k == "set-cookie"

    def test_cookie_with_options(self):
        """Test cookie with various options."""
        c = cookie("session", "abc123", max_age=3600, httponly=True, secure=True)
        assert isinstance(c, HttpHeader)
        # Cookie options are encoded in the value string
        assert "abc123" in c.v
        assert "Max-Age=3600" in c.v

    def test_cookie_path_domain(self):
        """Test cookie with path and domain."""
        c = cookie("session", "abc123", path="/app", domain=".example.com")
        assert "Path=/app" in c.v
        assert "Domain=.example.com" in c.v


class TestResponseTypes:
    """Test various response type creation."""

    def test_redirect_basic(self):
        """Test basic redirect creation."""
        # Redirect is a custom class with __response__ method
        r = Redirect("/home")
        assert hasattr(r, "loc")
        assert r.loc == "/home"
        assert hasattr(r, "__response__")

    def test_redirect_response_method(self):
        """Test redirect __response__ method."""
        r = Redirect("/home")
        # Would need a mock request to test __response__
        assert callable(getattr(r, "__response__", None))

    def test_json_response(self):
        """Test JSON response creation."""
        data = {"message": "Hello", "status": "ok"}
        r = JSONResponse(data)
        # JSONResponse is a Starlette response type
        assert hasattr(r, "headers")

    def test_event_stream(self):
        """Test Server-Sent Events stream creation."""

        async def events():
            yield "data: test\n\n"

        stream = EventStream(events())
        # EventStream sets specific headers
        assert hasattr(stream, "headers")


class TestKeyManagement:
    """Test session key management."""

    def test_get_key_from_file(self):
        """Test reading key from file."""
        # get_key uses a different signature
        import os

        with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
            f.write("test-secret-key")
            fname = f.name

        # get_key takes key and filename params
        key = get_key(fname=fname)
        assert key == "test-secret-key"
        os.unlink(fname)

    def test_get_key_generated(self):
        """Test key generation when file doesn't exist."""
        key = get_key(fname="test_nonexistent.key")
        assert isinstance(key, str)
        assert len(key) > 0
        # Clean up
        if os.path.exists("test_nonexistent.key"):
            os.unlink("test_nonexistent.key")


class TestClientUtility:
    """Test HTTP client utility."""

    def test_client_creation(self):
        """Test client creation."""
        # Client requires an app parameter
        app = Starlette()
        c = Client(app)
        assert c is not None


class TestUtilityHelpers:
    """Test various utility helper functions."""

    def test_flat_xt_simple(self):
        """Test flattening XML trees."""
        # flat_xt returns tuples
        result = flat_xt("text")
        assert result == ("text",)

        # List case
        result = flat_xt(["a", "b", "c"])
        assert result == ("a", "b", "c")

        # Nested list
        result = flat_xt(["a", ["b", "c"]])
        assert result == ("a", "b", "c")

    def test_flat_xt_empty(self):
        """Test flat_xt with empty input."""
        result = flat_xt([])
        assert result == ()


class TestFormProcessing:
    """Test advanced form processing."""

    def test_form2dict_nested(self):
        """Test form2dict with nested data."""
        form_data = {"user.name": "John", "user.email": "john@example.com", "tags[]": ["python", "web"]}
        result = form2dict(form_data)
        assert "user.name" in result
        assert result["tags[]"] == ["python", "web"]

    def test_form2dict_empty(self):
        """Test form2dict with empty data."""
        result = form2dict({})
        assert result == {}


class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_uri_empty_string(self):
        """Test URI encoding of empty string."""
        assert uri("") == "/"

    def test_decode_uri_basic(self):
        """Test basic URI decoding."""
        # decode_uri returns tuple
        path, params = decode_uri("test")
        assert path == "test"
        assert params == {}

    def test_snake2hyphens_edge_cases(self):
        """Test snake2hyphens edge cases."""
        # Empty string returns empty
        assert snake2hyphens("") == ""
        # Single underscore
        assert snake2hyphens("test") == "Test"

    def test_mk_list_multiple_types(self):
        """Test _mk_list with different types."""
        # String values
        result = _mk_list(str, ["a", "b", "c"])
        assert result == ["a", "b", "c"]

        # Type conversion
        result = _mk_list(int, ["1", "2", "3"])
        assert result == [1, 2, 3]
