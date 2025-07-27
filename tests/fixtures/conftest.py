"""Shared test fixtures and configuration for StarHTML tests."""

import asyncio
import sys
from pathlib import Path

import pytest
from starlette.testclient import TestClient

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from starhtml import star_app
from starhtml.realtime import elements, signals, sse


@pytest.fixture
def app():
    """Create a test StarHTML app."""
    app, rt = star_app()
    return app, rt


@pytest.fixture
def client(app):
    """Create a test client."""
    app_instance, _ = app
    return TestClient(app_instance)


@pytest.fixture
def sample_components():
    """Common component fixtures."""
    from starhtml import H1, A, Button, Div, Form, Input, P

    return {"Div": Div, "H1": H1, "Button": Button, "Form": Form, "Input": Input, "P": P, "A": A}


@pytest.fixture
def datastar_components():
    """Datastar-specific component fixtures."""

    return {"sse": sse, "signals": signals, "elements": elements}


@pytest.fixture
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def mock_request():
    """Create a mock request object for testing."""
    from starlette.datastructures import Headers

    class MockRequest:
        def __init__(self):
            self.headers = Headers({"accept": "text/html,application/xhtml+xml", "user-agent": "Mozilla/5.0 (Test)"})
            self.method = "GET"
            self.url = "http://testserver/"
            self.query_params = {}

    return MockRequest()


@pytest.fixture
def temp_demo_file(tmp_path):
    """Create a temporary demo file for testing."""

    def _create_demo(content):
        demo_file = tmp_path / "test_demo.py"
        demo_file.write_text(content)
        return demo_file

    return _create_demo
