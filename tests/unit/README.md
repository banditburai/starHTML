# StarHTML Unit Tests

This directory contains consolidated unit tests for the StarHTML framework.

## Test Files

### test_core_utilities.py
Tests for core utility functions:
- String and URI utilities
- Date/time parsing
- Form processing and data conversion
- Cookie handling
- Response types (Redirect, JSONResponse, EventStream)
- Key management

### test_datastar_comprehensive.py
Comprehensive tests for Datastar integration:
- Direct attribute syntax (ds_show, ds_bind, etc.)
- SSE components (signals, elements)
- Event handling and modifiers
- Utility functions (JSON handling, formatting)
- Edge cases and special characters

### test_handlers.py
Tests for JavaScript handler generation:
- Event handling patterns
- DOM manipulation
- Async operations
- Error handling in handlers

### test_html_comprehensive.py
Comprehensive tests for HTML module functionality:
- HTML element generation
- Attribute handling
- Form processing
- Template rendering

### test_html_elements.py
Tests for HTML/SVG elements:
- Basic HTML element creation
- SVG elements and transformations
- Form helpers (find_inputs, fill_form)
- Attribute mapping
- Complete HTML document structure
- Edge cases and special elements

### test_server_missing_coverage.py
Targeted tests for server.py missing coverage:
- APIRouter functionality
- Route function handling
- Serve function
- Cookie handling
- ResponseRenderer
- Request-response pipeline

### test_starapp_comprehensive.py
Comprehensive tests for starapp.py module:
- star_app function and app factory
- Database integration and table creation
- Default headers generation (def_hdrs)
- Beforeware and MiddlewareBase classes
- Helper functions and constants

### test_tags_comprehensive.py
Comprehensive tests for tags.py module:
- HTML tag factory functions
- SVG tag factory functions and specialized SVG components
- PathFT class and path building methods
- transformd utility function
- Dynamic tag generation via __getattr__
- ft_svg base factory function

### test_xtend_comprehensive.py
Comprehensive tests for xtend.py module:
- Extension functionality
- Integration patterns
- Utility functions

## Running Tests

```bash
# Run all unit tests
uv run pytest tests/unit/ -v

# Run specific test file
uv run pytest tests/unit/test_datastar_attrs.py -v

# Run specific test class
uv run pytest tests/unit/test_event_handlers.py::TestThrottlingTransformation -v

# Run with coverage
uv run pytest tests/unit/ --cov=starhtml --cov-report=html
```

## Test Organization

Tests are organized by functionality rather than by source file, making it easier to:
- Find related tests
- Avoid duplication
- Maintain comprehensive coverage
- Add new tests in the appropriate location

Each test file contains multiple test classes grouping related functionality, with descriptive docstrings explaining what each test verifies.