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


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
