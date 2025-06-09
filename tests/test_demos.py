"""Test that all demo files can be imported and run without errors."""

import importlib.util
import sys
from pathlib import Path

import pytest

DEMO_DIR = Path(__file__).parent.parent / "demo"


def get_demo_files():
    """Get all Python demo files."""
    demo_files = []
    for f in DEMO_DIR.glob("*.py"):
        # Skip test files and helper files
        if not f.name.startswith(("test_", "_", ".")):
            demo_files.append(f)
    return sorted(demo_files)


@pytest.mark.parametrize("demo_file", get_demo_files(), ids=lambda f: f.name)
def test_demo_imports(demo_file):
    """Test that demo file can be imported without errors."""
    # Create a module name from the file
    module_name = f"demo_test_{demo_file.stem}"

    # Load the module
    spec = importlib.util.spec_from_file_location(module_name, demo_file)
    if spec is None:
        pytest.fail(f"Could not load spec for {demo_file}")

    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module

    try:
        # This will raise if there are import errors
        spec.loader.exec_module(module)
    except Exception as e:
        pytest.fail(f"Failed to import {demo_file.name}: {e}")
    finally:
        # Clean up
        if module_name in sys.modules:
            del sys.modules[module_name]


@pytest.mark.parametrize("demo_file", get_demo_files(), ids=lambda f: f.name)
def test_demo_app_creation(demo_file):
    """Test that demo apps can be created if they define app creation functions."""
    if any(keyword in demo_file.name for keyword in ["server", "docs", "demo"]):
        module_name = f"demo_app_test_{demo_file.stem}"

        spec = importlib.util.spec_from_file_location(module_name, demo_file)
        if spec is None:
            pytest.skip(f"Could not load spec for {demo_file}")

        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module

        try:
            spec.loader.exec_module(module)

            # Check for common app creation patterns
            if hasattr(module, "app"):
                assert module.app is not None, f"{demo_file.name} has None app"

            if hasattr(module, "create_app"):
                app = module.create_app()
                assert app is not None, f"{demo_file.name} create_app returned None"

            # Check for route definitions
            if hasattr(module, "rt"):
                assert module.rt is not None, f"{demo_file.name} has None rt"

        except Exception as e:
            pytest.fail(f"Failed to create app from {demo_file.name}: {e}")
        finally:
            # Clean up
            if module_name in sys.modules:
                del sys.modules[module_name]
    else:
        pytest.skip(f"Skipping {demo_file.name} - not an app demo")


def test_demo_directory_structure():
    """Test that demo directory has expected structure."""
    assert DEMO_DIR.exists(), "Demo directory does not exist"
    assert DEMO_DIR.is_dir(), "Demo path is not a directory"

    demo_files = list(DEMO_DIR.glob("*.py"))
    assert len(demo_files) > 0, "No Python files found in demo directory"

    # Check for some expected demo patterns
    demo_names = [f.name for f in demo_files]

    # Should have numbered demos
    numbered_demos = [name for name in demo_names if name[0].isdigit()]
    assert len(numbered_demos) > 0, "No numbered demo files found (e.g., 01_basic.py)"

    # Should have some docs demos
    docs_demos = [name for name in demo_names if "docs" in name.lower()]
    assert len(docs_demos) > 0, "No documentation demo files found"


@pytest.mark.slow
def test_demo_syntax():
    """Test that demo files follow consistent patterns."""
    for demo_file in get_demo_files():
        content = demo_file.read_text()

        # Check for proper imports
        if "from starhtml import" not in content:
            pytest.fail(f"{demo_file.name} does not import from starhtml")

        # Check for if __name__ == "__main__": pattern for runnable demos
        if "server" in demo_file.name or demo_file.name.startswith(("0", "1", "2")):
            if 'if __name__ == "__main__":' not in content:
                pytest.fail(f"{demo_file.name} appears to be runnable but lacks main guard")

        # Check for docstrings
        lines = content.strip().split("\n")
        if lines and not (lines[0].startswith('"""') or lines[0].startswith("#")):
            pytest.fail(f"{demo_file.name} should start with a docstring or comment")
