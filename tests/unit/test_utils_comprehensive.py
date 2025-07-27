"""Comprehensive tests for starhtml.utils module to improve coverage from 68% to 90%+.

This module tests previously uncovered functionality including:
- _fill_item function (lines 175-215) for form filling logic
- _url_for function (lines 75-81) for URL generation
- reg_re_param function for regex parameter registration
- fill_form and fill_dataclass functions
- find_inputs function for searching elements
- File function for reading file content
- _from_body function for extracting body parameters
- _params, _annotations, _is_body helper functions
- _add_ids function for adding IDs to elements
- _camel_to_kebab function for name conversion
- Edge cases and error conditions
"""

import io
import tempfile
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from unittest.mock import Mock, patch

import pytest
from fastcore.xml import FT
from starlette.datastructures import FormData, UploadFile
from starlette.exceptions import HTTPException

from starhtml.utils import (
    File,
    HttpHeader,
    _add_ids,
    _annotations,
    _camel_to_kebab,
    _fill_item,
    _fix_anno,
    _form_arg,
    _formitem,
    _from_body,
    _is_body,
    _list,
    _params,
    _url_for,
    decode_uri,
    empty,
    fill_dataclass,
    fill_form,
    find_inputs,
    flat_tuple,
    flat_xt,
    form2dict,
    get_key,
    noop_body,
    parse_form,
    qp,
    reg_re_param,
    snake2hyphens,
    uri,
)


class TestFillItemFunction:
    """Test the _fill_item function which handles form filling logic."""

    def test_fill_input_text(self):
        """Test filling text input fields."""
        # Create an input element
        input_elem = FT("input", (), {"type": "text", "name": "username"})
        obj = {"username": "john_doe"}

        result = _fill_item(input_elem, obj)
        assert result.attrs["value"] == "john_doe"
        assert result.attrs["name"] == "username"

    def test_fill_input_checkbox_single(self):
        """Test filling single checkbox."""
        # Checkbox that should be checked
        checkbox = FT("input", (), {"type": "checkbox", "name": "subscribe", "value": "yes"})
        obj = {"subscribe": True}

        result = _fill_item(checkbox, obj)
        assert "checked" in result.attrs
        assert result.attrs["checked"] == "1"

        # Checkbox that should not be checked
        obj = {"subscribe": False}
        result = _fill_item(checkbox, obj)
        assert "checked" not in result.attrs

    def test_fill_input_checkbox_multiple(self):
        """Test filling checkbox with multiple values."""
        # Multiple checkboxes with same name
        checkbox1 = FT("input", (), {"type": "checkbox", "name": "skills", "value": "python"})
        checkbox2 = FT("input", (), {"type": "checkbox", "name": "skills", "value": "javascript"})
        checkbox3 = FT("input", (), {"type": "checkbox", "name": "skills", "value": "rust"})

        obj = {"skills": ["python", "rust"]}

        result1 = _fill_item(checkbox1, obj)
        assert "checked" in result1.attrs  # Python is in the list

        result2 = _fill_item(checkbox2, obj)
        assert "checked" not in result2.attrs  # JavaScript is not in the list

        result3 = _fill_item(checkbox3, obj)
        assert "checked" in result3.attrs  # Rust is in the list

    def test_fill_input_radio(self):
        """Test filling radio buttons."""
        radio1 = FT("input", (), {"type": "radio", "name": "gender", "value": "male"})
        radio2 = FT("input", (), {"type": "radio", "name": "gender", "value": "female"})

        obj = {"gender": "female"}

        result1 = _fill_item(radio1, obj)
        assert "checked" not in result1.attrs

        result2 = _fill_item(radio2, obj)
        assert "checked" in result2.attrs
        assert result2.attrs["checked"] == "1"

    def test_fill_textarea(self):
        """Test filling textarea elements."""
        textarea = FT("textarea", ("old content",), {"name": "description"})
        obj = {"description": "This is my new description"}

        result = _fill_item(textarea, obj)
        assert result.children == ("This is my new description",)
        assert result.attrs["name"] == "description"

    def test_fill_select_single(self):
        """Test filling select dropdown with single value."""
        options = [
            FT("option", ("Red",), {"value": "red"}),
            FT("option", ("Green",), {"value": "green"}),
            FT("option", ("Blue",), {"value": "blue"}),
        ]
        select = FT("select", tuple(options), {"name": "color"})
        obj = {"color": "green"}

        result = _fill_item(select, obj)
        # Check that green option is selected
        for opt in result.children:
            if opt.attrs.get("value") == "green":
                assert opt.attrs.get("selected") == "1"
            else:
                assert "selected" not in opt.attrs

    def test_fill_select_multiple(self):
        """Test filling multi-select with multiple values."""
        options = [
            FT("option", ("Python",), {"value": "python"}),
            FT("option", ("JavaScript",), {"value": "js"}),
            FT("option", ("Rust",), {"value": "rust"}),
            FT("option", ("Go",), {"value": "go"}),
        ]
        select = FT("select", tuple(options), {"name": "languages", "multiple": "true"})
        obj = {"languages": ["python", "rust"]}

        result = _fill_item(select, obj)
        # Check that python and rust are selected
        for opt in result.children:
            if opt.attrs.get("value") in ["python", "rust"]:
                assert opt.attrs.get("selected") == "1"
            else:
                assert "selected" not in opt.attrs

    def test_fill_nested_elements(self):
        """Test filling nested form elements."""
        form = FT(
            "form",
            (
                FT("input", (), {"type": "text", "name": "name"}),
                FT(
                    "div",
                    (FT("input", (), {"type": "email", "name": "email"}), FT("textarea", ("",), {"name": "message"})),
                    {},
                ),
            ),
            {},
        )

        obj = {"name": "John Doe", "email": "john@example.com", "message": "Hello World"}

        result = _fill_item(form, obj)
        # Check that nested elements are filled
        name_input = result.children[0]
        assert name_input.attrs["value"] == "John Doe"

        div = result.children[1]
        email_input = div.children[0]
        assert email_input.attrs["value"] == "john@example.com"

        textarea = div.children[1]
        assert textarea.children == ("Hello World",)

    def test_fill_skip_attribute(self):
        """Test that elements with skip attribute are not filled."""
        input_elem = FT("input", (), {"type": "text", "name": "username", "skip": "true"})
        obj = {"username": "john_doe"}

        result = _fill_item(input_elem, obj)
        assert "value" not in result.attrs

    def test_fill_non_ft_element(self):
        """Test that non-FT elements are returned unchanged."""
        non_ft = "Just a string"
        obj = {"test": "value"}

        result = _fill_item(non_ft, obj)
        assert result == "Just a string"


class TestUrlForFunction:
    """Test the _url_for function for URL generation."""

    def test_url_for_simple_route(self):
        """Test _url_for with simple route name."""
        # Mock request with url_path_for method
        req = Mock()
        req.url_path_for.return_value = "/users"

        result = _url_for(req, "users")
        assert result == "/users"
        req.url_path_for.assert_called_once_with("users")

    def test_url_for_with_path_params(self):
        """Test _url_for with path parameters."""
        req = Mock()
        req.url_path_for.return_value = "/users/123"

        # Simulate URL with encoded params
        _url_for(req, "users/id=123")
        # The function should decode the URI and pass params
        req.url_path_for.assert_called()

    def test_url_for_with_query_string(self):
        """Test _url_for preserving query string."""
        req = Mock()
        req.url_path_for.return_value = "/search"

        result = _url_for(req, "search?q=test&page=2")
        assert result == "/search?q=test&page=2"

    def test_url_for_with_callable(self):
        """Test _url_for with callable that has __routename__."""
        req = Mock()
        req.url_path_for.return_value = "/custom"

        # Mock callable with __routename__
        func = Mock()
        func.__routename__ = "custom_route"

        _url_for(req, func)
        req.url_path_for.assert_called_with("custom_route")

    def test_url_for_with_callable_no_routename(self):
        """Test _url_for with callable without __routename__."""
        req = Mock()
        req.url_path_for.return_value = "/func"

        def my_func():
            pass

        _url_for(req, my_func)
        # Should use string representation of function
        req.url_path_for.assert_called()


class TestRegReParam:
    """Test regex parameter registration."""

    @patch("starlette.convertors.register_url_convertor")
    def test_reg_re_param_basic(self, mock_register):
        """Test basic regex parameter registration."""
        reg_re_param("phone", r"\d{3}-\d{3}-\d{4}")

        mock_register.assert_called_once()
        args = mock_register.call_args[0]
        assert args[0] == "phone"
        # Check that a convertor class was registered
        convertor_class = args[1]
        assert hasattr(convertor_class, "regex")

    @patch("starlette.convertors.register_url_convertor")
    def test_reg_re_param_complex_regex(self, mock_register):
        """Test regex parameter with complex pattern."""
        reg_re_param("uuid", r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}")

        mock_register.assert_called_once()


class TestFillFormAndDataclass:
    """Test fill_form and fill_dataclass functions."""

    def test_fill_form_with_dict(self):
        """Test fill_form with dictionary object."""
        form = FT(
            "form",
            (FT("input", (), {"type": "text", "name": "name"}), FT("input", (), {"type": "email", "name": "email"})),
            {},
        )

        obj = {"name": "Alice", "email": "alice@example.com"}
        result = fill_form(form, obj)

        # Check that form was filled
        assert result.children[0].attrs["value"] == "Alice"
        assert result.children[1].attrs["value"] == "alice@example.com"

    def test_fill_form_with_dataclass(self):
        """Test fill_form with dataclass object."""

        @dataclass
        class User:
            name: str
            email: str
            age: int

        form = FT(
            "form",
            (
                FT("input", (), {"type": "text", "name": "name"}),
                FT("input", (), {"type": "email", "name": "email"}),
                FT("input", (), {"type": "number", "name": "age"}),
            ),
            {},
        )

        user = User(name="Bob", email="bob@example.com", age=30)
        result = fill_form(form, user)

        assert result.children[0].attrs["value"] == "Bob"
        assert result.children[1].attrs["value"] == "bob@example.com"
        assert result.children[2].attrs["value"] == 30

    def test_fill_form_with_object(self):
        """Test fill_form with regular object."""

        class Person:
            def __init__(self):
                self.name = "Charlie"
                self.city = "New York"

        form = FT(
            "form",
            (FT("input", (), {"type": "text", "name": "name"}), FT("input", (), {"type": "text", "name": "city"})),
            {},
        )

        person = Person()
        result = fill_form(form, person)

        assert result.children[0].attrs["value"] == "Charlie"
        assert result.children[1].attrs["value"] == "New York"

    def test_fill_dataclass(self):
        """Test fill_dataclass function."""

        @dataclass
        class Source:
            name: str
            value: int

        @dataclass
        class Dest:
            name: str
            value: int
            extra: str = "default"

        src = Source(name="test", value=42)
        dest = Dest(name="old", value=0)

        result = fill_dataclass(src, dest)
        assert result is dest  # Returns same object
        assert dest.name == "test"
        assert dest.value == 42
        assert dest.extra == "default"  # Unchanged


class TestFindInputs:
    """Test find_inputs function for searching elements."""

    def test_find_inputs_basic(self):
        """Test finding input elements."""
        form = FT(
            "form",
            (
                FT("input", (), {"type": "text", "name": "field1"}),
                FT("input", (), {"type": "email", "name": "field2"}),
                FT("button", ("Submit",), {"type": "submit"}),
            ),
            {},
        )

        inputs = find_inputs(form, "input")
        assert len(inputs) == 2
        assert all(inp.tag == "input" for inp in inputs)

    def test_find_inputs_with_attributes(self):
        """Test finding elements with specific attributes."""
        form = FT(
            "form",
            (
                FT("input", (), {"type": "text", "name": "username"}),
                FT("input", (), {"type": "password", "name": "password"}),
                FT("input", (), {"type": "email", "name": "email"}),
                FT("input", (), {"type": "submit", "value": "Login"}),
            ),
            {},
        )

        # Find only password inputs
        password_inputs = find_inputs(form, "input", type="password")
        assert len(password_inputs) == 1
        assert password_inputs[0].attrs["name"] == "password"

    def test_find_inputs_multiple_tags(self):
        """Test finding multiple tag types."""
        form = FT(
            "form",
            (
                FT("input", (), {"name": "field1"}),
                FT("textarea", ("",), {"name": "field2"}),
                FT("select", (), {"name": "field3"}),
            ),
            {},
        )

        # Find both input and textarea
        elements = find_inputs(form, ["input", "textarea"])
        assert len(elements) == 2
        assert elements[0].tag == "input"
        assert elements[1].tag == "textarea"

    def test_find_inputs_nested(self):
        """Test finding inputs in nested structure."""
        nested_div = FT("div", (FT("input", (), {"type": "text", "name": "nested2"}),), {})
        form_group = FT(
            "div", (FT("input", (), {"type": "text", "name": "nested1"}), nested_div), {"class": "form-group"}
        )
        form = FT("form", (form_group, FT("input", (), {"type": "text", "name": "top-level"})), {})

        inputs = find_inputs(form, "input")
        assert len(inputs) == 3
        names = [inp.attrs.get("name") for inp in inputs]
        assert "nested1" in names
        assert "nested2" in names
        assert "top-level" in names

    def test_find_inputs_no_matches(self):
        """Test when no elements match."""
        form = FT("form", (FT("div", ("No inputs here",), {}), FT("p", ("Just text",), {})), {})

        inputs = find_inputs(form, "input")
        assert inputs == []

    def test_find_inputs_non_ft_element(self):
        """Test find_inputs with non-FT elements."""
        # String
        assert find_inputs("not an element", "input") == []
        # None
        assert find_inputs(None, "input") == []
        # Dict (not a valid element type)
        assert find_inputs({"key": "value"}, "input") == []


class TestFileFunction:
    """Test File function for reading file content."""

    def test_file_read_content(self):
        """Test reading file content."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".txt") as f:
            f.write("Hello from file!")
            fname = f.name

        try:
            result = File(fname)
            # File returns NotStr which prevents HTML escaping
            assert str(result) == "Hello from file!"
            # NotStr from fastcore has special properties
            assert result.__class__.__name__ == "NotStr"
        finally:
            Path(fname).unlink()

    def test_file_nonexistent(self):
        """Test File with non-existent file."""
        with pytest.raises(FileNotFoundError):
            File("/path/that/does/not/exist.txt")


class TestFromBodyFunction:
    """Test _from_body function for extracting body parameters."""

    @pytest.mark.asyncio
    async def test_from_body_simple_dict(self):
        """Test _from_body with simple dict annotation."""

        # Create mock async form method
        async def mock_form():
            return FormData([("key", "value"), ("num", "42")])

        # Mock request with headers
        req = Mock()
        req.form = mock_form
        req.query_params = {}
        req.headers = Mock()
        req.headers.get = Mock(return_value="application/x-www-form-urlencoded")

        # Mock parameter with dict annotation
        param = Mock()
        param.annotation = dict

        result = await _from_body(req, param)
        assert isinstance(result, dict)
        assert result["key"] == "value"
        assert result["num"] == "42"

    @pytest.mark.asyncio
    async def test_from_body_with_dataclass(self):
        """Test _from_body with dataclass annotation."""

        @dataclass
        class UserData:
            name: str
            age: int
            active: bool = True

        async def mock_form():
            return FormData([("name", "Alice"), ("age", "25"), ("active", "false")])

        req = Mock()
        req.form = mock_form
        req.query_params = {}
        req.headers = Mock()
        req.headers.get = Mock(return_value="application/x-www-form-urlencoded")

        param = Mock()
        param.annotation = UserData

        result = await _from_body(req, param)
        assert isinstance(result, UserData)
        assert result.name == "Alice"
        assert result.age == 25
        assert result.active is False

    @pytest.mark.asyncio
    async def test_from_body_with_query_params(self):
        """Test _from_body merging form and query params."""

        async def mock_form():
            return FormData([("form_field", "form_value")])

        req = Mock()
        req.form = mock_form
        req.query_params = {"query_field": "query_value"}
        req.headers = Mock()
        req.headers.get = Mock(return_value="application/x-www-form-urlencoded")

        param = Mock()
        param.annotation = dict

        result = await _from_body(req, param)
        assert result["form_field"] == "form_value"
        assert result["query_field"] == "query_value"


class TestHelperFunctions:
    """Test various helper functions."""

    def test_params_function(self):
        """Test _params function."""

        def sample_func(a: str, b: int = 5, *args, **kwargs):
            pass

        params = _params(sample_func)
        assert "a" in params
        assert "b" in params
        assert params["b"].default == 5

    def test_annotations_regular_class(self):
        """Test _annotations with regular class."""

        @dataclass
        class MyClass:
            field1: str
            field2: int

        annos = _annotations(MyClass)
        assert annos["field1"] is str
        assert annos["field2"] is int

    def test_annotations_namedtuple(self):
        """Test _annotations with namedtuple."""
        from collections import namedtuple

        MyTuple = namedtuple("MyTuple", ["x", "y", "z"])

        annos = _annotations(MyTuple)
        assert annos == {"x": str, "y": str, "z": str}

    def test_is_body_dict(self):
        """Test _is_body with dict type."""
        assert _is_body(dict) is True

    def test_is_body_dataclass(self):
        """Test _is_body with dataclass."""

        @dataclass
        class TestClass:
            field: str

        # _is_body returns annotations dict if body type, not True
        result = _is_body(TestClass)
        assert result is not False
        assert isinstance(result, dict)
        assert "field" in result

    def test_is_body_regular_type(self):
        """Test _is_body with non-body type."""
        assert not _is_body(str)
        assert not _is_body(int)

    def test_list_function(self):
        """Test _list helper function."""
        assert _list(None) == []
        assert _list([1, 2, 3]) == [1, 2, 3]
        assert _list((1, 2, 3)) == [1, 2, 3]
        assert _list("single") == ["single"]
        assert _list(42) == [42]


class TestAddIdsFunction:
    """Test _add_ids function for adding IDs to elements."""

    def test_add_ids_single_element(self):
        """Test adding ID to single element."""
        elem = FT("div", ("content",), {})
        _add_ids(elem)
        assert hasattr(elem, "id")
        assert elem.id.startswith("_")  # unqid starts with underscore

    def test_add_ids_nested_elements(self):
        """Test adding IDs to nested elements."""
        elem = FT("div", (FT("p", ("paragraph",), {}), FT("span", ("text",), {})), {})

        _add_ids(elem)
        assert hasattr(elem, "id")
        assert hasattr(elem.children[0], "id")
        assert hasattr(elem.children[1], "id")
        # All IDs should be unique
        assert elem.id != elem.children[0].id
        assert elem.id != elem.children[1].id
        assert elem.children[0].id != elem.children[1].id

    def test_add_ids_existing_id(self):
        """Test that existing IDs are not overwritten."""
        elem = FT("div", ("content",), {"id": "my-custom-id"})
        elem.id = "my-custom-id"
        _add_ids(elem)
        assert elem.id == "my-custom-id"  # Should not change

    def test_add_ids_non_ft_element(self):
        """Test _add_ids with non-FT elements."""
        # Should not raise error
        _add_ids("not an element")
        _add_ids(None)
        _add_ids({"key": "value"})


class TestCamelToKebab:
    """Test _camel_to_kebab function."""

    def test_camel_to_kebab_basic(self):
        """Test basic camelCase conversion."""
        assert _camel_to_kebab("camelCase") == "camel-case"
        assert _camel_to_kebab("myVariableName") == "my-variable-name"

    def test_camel_to_kebab_pascal(self):
        """Test PascalCase conversion."""
        assert _camel_to_kebab("PascalCase") == "pascal-case"
        assert _camel_to_kebab("MyClassName") == "my-class-name"

    def test_camel_to_kebab_with_numbers(self):
        """Test conversion with numbers."""
        assert _camel_to_kebab("component1Name") == "component1-name"
        assert _camel_to_kebab("html5Parser") == "html5-parser"

    def test_camel_to_kebab_consecutive_caps(self):
        """Test conversion with consecutive capitals."""
        assert _camel_to_kebab("XMLHttpRequest") == "xml-http-request"
        assert _camel_to_kebab("IOError") == "io-error"

    def test_camel_to_kebab_already_kebab(self):
        """Test with already kebab-case string."""
        assert _camel_to_kebab("already-kebab-case") == "already-kebab-case"

    def test_camel_to_kebab_edge_cases(self):
        """Test edge cases."""
        assert _camel_to_kebab("") == ""
        assert _camel_to_kebab("A") == "a"
        assert _camel_to_kebab("ABC") == "abc"
        assert _camel_to_kebab("simpleword") == "simpleword"


class TestFormArgumentProcessing:
    """Test form argument processing functions."""

    def test_form_arg_none_value(self):
        """Test _form_arg with None value."""
        result = _form_arg("key", None, {"key": str})
        assert result is None

    def test_form_arg_no_annotation(self):
        """Test _form_arg without type annotation."""
        result = _form_arg("key", "value", {})
        assert result == "value"

    def test_form_arg_with_type_conversion(self):
        """Test _form_arg with type conversion."""
        # String to int
        result = _form_arg("age", "25", {"age": int})
        assert result == 25
        assert isinstance(result, int)

        # String to bool
        result = _form_arg("active", "true", {"active": bool})
        assert result is True

        # List of strings to list of ints
        result = _form_arg("numbers", ["1", "2", "3"], {"numbers": list[int]})
        assert result == [1, 2, 3]

    def test_form_arg_non_string_passthrough(self):
        """Test _form_arg with non-string values."""
        # Already correct type
        result = _form_arg("num", 42, {"num": int})
        assert result == 42

        # Complex object
        obj = {"nested": "data"}
        result = _form_arg("data", obj, {"data": dict})
        assert result is obj


class TestParseFormEdgeCases:
    """Test edge cases for parse_form function."""

    @pytest.mark.asyncio
    async def test_parse_form_empty_multipart(self):
        """Test parse_form with empty multipart form."""
        req = Mock()
        req.headers = {"Content-Type": "multipart/form-data; boundary=----test", "Content-Length": "10"}
        req.form = Mock(return_value=FormData())

        result = await parse_form(req)
        assert isinstance(result, FormData)
        assert len(result) == 0

    @pytest.mark.asyncio
    async def test_parse_form_json_content(self):
        """Test parse_form with JSON content type."""

        async def mock_json():
            return {"key": "value", "number": 42}

        req = Mock()
        req.headers = {"Content-Type": "application/json"}
        req.json = mock_json

        result = await parse_form(req)
        assert result == {"key": "value", "number": 42}

    @pytest.mark.asyncio
    async def test_parse_form_invalid_boundary(self):
        """Test parse_form with invalid multipart boundary."""
        req = Mock()
        req.headers = {"Content-Type": "multipart/form-data"}  # Missing boundary

        with pytest.raises(HTTPException) as exc_info:
            await parse_form(req)
        assert exc_info.value.status_code == 400
        assert "boundary" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_parse_form_regular_form(self):
        """Test parse_form with regular form data."""
        form_data = FormData([("field1", "value1"), ("field2", "value2")])

        async def mock_form():
            return form_data

        req = Mock()
        req.headers = {"Content-Type": "application/x-www-form-urlencoded"}
        req.form = mock_form

        result = await parse_form(req)
        assert result is form_data


class TestFixAnnoEdgeCases:
    """Test edge cases for _fix_anno function."""

    def test_fix_anno_union_types(self):
        """Test _fix_anno with Union types."""
        # Union with None (Optional)
        result = _fix_anno(str | None, "test")
        assert result == "test"

        # Union with multiple types
        result = _fix_anno(int | str, "42")
        assert result == 42  # Should convert to first non-None type

    def test_fix_anno_list_type(self):
        """Test _fix_anno with list types."""
        # List of strings
        result = _fix_anno(list[str], ["a", "b", "c"])
        assert result == ["a", "b", "c"]

        # Single value to list
        result = _fix_anno(list[int], "5")
        assert result == [5]

    def test_fix_anno_upload_file(self):
        """Test _fix_anno with UploadFile."""
        # Create a proper UploadFile with required file parameter
        file_obj = io.BytesIO(b"test content")
        upload = UploadFile(filename="test.txt", file=file_obj)
        result = _fix_anno(UploadFile, upload)
        assert result is upload  # Should return as-is

    def test_fix_anno_date_type(self):
        """Test _fix_anno with date type."""
        result = _fix_anno(date, "2023-12-25")
        assert isinstance(result, date)
        assert result.year == 2023
        assert result.month == 12
        assert result.day == 25


class TestHttpHeaderDataclass:
    """Test HttpHeader dataclass."""

    def test_http_header_creation(self):
        """Test creating HttpHeader instances."""
        header = HttpHeader(k="Content-Type", v="application/json")
        assert header.k == "Content-Type"
        assert header.v == "application/json"

    def test_http_header_equality(self):
        """Test HttpHeader equality."""
        h1 = HttpHeader("X-Custom", "value1")
        h2 = HttpHeader("X-Custom", "value1")
        h3 = HttpHeader("X-Custom", "value2")

        assert h1 == h2
        assert h1 != h3


class TestEmptyConstant:
    """Test the empty constant."""

    def test_empty_is_parameter_empty(self):
        """Test that empty is Parameter.empty."""
        from inspect import Parameter

        assert empty is Parameter.empty

    def test_empty_usage(self):
        """Test using empty in parameter checking."""

        def check_param(value=empty):
            return value is not empty

        assert check_param("value") is True
        assert check_param() is False


class TestIntegrationScenarios:
    """Integration tests combining multiple utilities."""

    def test_full_form_processing_flow(self):
        """Test complete form processing workflow."""
        # Create a complex form
        form = FT(
            "form",
            (
                FT("input", (), {"type": "text", "name": "username"}),
                FT("input", (), {"type": "email", "name": "email"}),
                FT("input", (), {"type": "checkbox", "name": "subscribe", "value": "yes"}),
                FT(
                    "select",
                    (
                        FT("option", ("Admin",), {"value": "admin"}),
                        FT("option", ("User",), {"value": "user"}),
                        FT("option", ("Guest",), {"value": "guest"}),
                    ),
                    {"name": "role"},
                ),
                FT("textarea", ("",), {"name": "bio"}),
            ),
            {"method": "post"},
        )

        # User data to fill
        @dataclass
        class UserForm:
            username: str
            email: str
            subscribe: bool
            role: str
            bio: str

        user_data = UserForm(
            username="johndoe", email="john@example.com", subscribe=True, role="user", bio="Software developer"
        )

        # Fill the form
        filled_form = fill_form(form, user_data)

        # Verify all fields are filled correctly
        assert filled_form.children[0].attrs["value"] == "johndoe"
        assert filled_form.children[1].attrs["value"] == "john@example.com"
        assert "checked" in filled_form.children[2].attrs

        # Check select option
        select = filled_form.children[3]
        for option in select.children:
            if option.attrs["value"] == "user":
                assert option.attrs.get("selected") == "1"
            else:
                assert "selected" not in option.attrs

        # Check textarea
        assert filled_form.children[4].children == ("Software developer",)

    def test_find_and_fill_workflow(self):
        """Test finding inputs and then filling them."""
        # Create nested form structure
        form = FT(
            "div",
            (
                FT(
                    "fieldset",
                    (
                        FT("legend", ("Personal Info",), {}),
                        FT("input", (), {"type": "text", "name": "first_name", "required": "true"}),
                        FT("input", (), {"type": "text", "name": "last_name", "required": "true"}),
                    ),
                    {},
                ),
                FT(
                    "fieldset",
                    (
                        FT("legend", ("Contact Info",), {}),
                        FT("input", (), {"type": "email", "name": "email", "required": "true"}),
                        FT("input", (), {"type": "tel", "name": "phone"}),
                    ),
                    {},
                ),
            ),
            {"class": "form-container"},
        )

        # Find all required inputs
        required_inputs = find_inputs(form, "input", required="true")
        assert len(required_inputs) == 3

        # Fill the form
        data = {"first_name": "Jane", "last_name": "Doe", "email": "jane@example.com", "phone": "555-1234"}

        filled_form = _fill_item(form, data)

        # Verify required fields are filled
        filled_required = find_inputs(filled_form, "input", required="true")
        assert filled_required[0].attrs["value"] == "Jane"
        assert filled_required[1].attrs["value"] == "Doe"
        assert filled_required[2].attrs["value"] == "jane@example.com"


class TestMissingCoverage:
    """Test remaining uncovered lines to reach 90%+ coverage."""

    def test_qp_false_none_values(self):
        """Test qp with False and None values in parameters."""
        # Test that False and None values are handled correctly
        result = qp("/path/{id}", id=False)
        assert result == "/path/"  # False should be removed

        result = qp("/path/{id}", id=None)
        assert result == "/path/"  # None should be removed

        # Test query params with False/None - they become empty strings in query
        result = qp("/path", active=False, deleted=None, valid=True)
        assert "valid=True" in result
        assert "active=" in result  # False becomes empty string
        assert "deleted=" in result  # None becomes empty string

    def test_qp_optional_path_params(self):
        """Test qp with optional path parameters."""
        # Test pattern with optional suffix
        result = qp("/users/{id:int}", id=123)
        assert result == "/users/123"

        # Test multiple placeholders
        result = qp("/api/{version}/users/{id}", version="v2", id=456)
        assert result == "/api/v2/users/456"

    def test_decode_uri_no_query(self):
        """Test decode_uri with no query parameters."""
        path, params = decode_uri("simple-path")
        assert path == "simple-path"
        assert params == {}

    def test_uri_function(self):
        """Test uri encoding function."""
        # Simple case
        result = uri("test arg")
        assert result == "test%20arg/"

        # With kwargs
        result = uri("path", key="value", num=42)
        assert "key=value" in result
        assert "num=42" in result

    @pytest.mark.asyncio
    async def test_parse_form_no_content_length(self):
        """Test parse_form with missing Content-Length header."""
        req = Mock()
        headers_dict = {
            "Content-Type": "multipart/form-data; boundary=test",
            "Content-Length": "0",  # Zero length
        }
        req.headers = Mock()
        req.headers.get = Mock(side_effect=lambda k, default="": headers_dict.get(k, default))

        result = await parse_form(req)
        assert isinstance(result, FormData)
        assert len(result) == 0

    def test_form2dict_already_dict(self):
        """Test form2dict when input is already a dict."""
        input_dict = {"key": "value", "num": 42}
        result = form2dict(input_dict)
        assert result == input_dict
        assert result is input_dict  # Should return same object

    def test_find_inputs_none_tags(self):
        """Test find_inputs with None as tags."""
        elem = FT("div", (FT("input", (), {"name": "test"}),), {})
        result = find_inputs(elem, None)
        assert result == []  # None tags should return empty list

    def test_formitem_dict_input(self):
        """Test _formitem with dict input."""
        form_dict = {"name": "John", "age": 30}
        assert _formitem(form_dict, "name") == "John"
        assert _formitem(form_dict, "missing") is None

    def test_snake2hyphens_function(self):
        """Test snake2hyphens conversion."""
        # The function first converts to camelCase then to hyphenated
        assert snake2hyphens("hello_world_test") == "Hello-World-Test"
        assert snake2hyphens("simple") == "Simple"

    def test_get_key_with_existing_key(self):
        """Test get_key when providing a key to write."""
        import os
        import tempfile

        with tempfile.NamedTemporaryFile(delete=False) as f:
            fname = f.name

        # Test writing a key
        test_key = "my-secret-key-123"
        result = get_key(key=test_key, fname=fname)
        assert result == test_key

        # Verify it was written
        with open(fname) as f:
            assert f.read() == test_key

        os.unlink(fname)

    def test_get_key_generate_new(self):
        """Test get_key generating a new key."""
        import os
        import tempfile

        # Use a unique filename that doesn't exist
        fname = tempfile.mktemp()

        try:
            key = get_key(fname=fname)
            assert isinstance(key, str)
            assert len(key) > 20  # Should be a decent length

            # Verify it was saved
            assert os.path.exists(fname)
            with open(fname) as f:
                assert f.read() == key
        finally:
            if os.path.exists(fname):
                os.unlink(fname)

    def test_flat_xt_with_ft_element(self):
        """Test flat_xt with FT elements."""
        elem = FT("div", ("content",), {})
        result = flat_xt(elem)
        assert result == (elem,)

        # Test with string
        result = flat_xt("string")
        assert result == ("string",)

    def test_flat_tuple_edge_cases(self):
        """Test flat_tuple with various input types."""
        # Test with generator
        gen = (x for x in [1, 2, 3])
        result = flat_tuple(gen)
        assert result == (1, 2, 3)

        # Test with range
        result = flat_tuple(range(3))
        assert result == (0, 1, 2)

        # Test with filter
        result = flat_tuple(filter(lambda x: x > 0, [-1, 0, 1, 2]))
        assert result == (1, 2)

        # Test with map
        result = flat_tuple(map(str, [1, 2, 3]))
        assert result == ("1", "2", "3")

    def test_noop_body_function(self):
        """Test noop_body function."""
        content = "test content"
        req = Mock()
        result = noop_body(content, req)
        assert result == content  # Should just return content unchanged


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
