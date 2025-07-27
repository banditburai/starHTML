# StarHTML Test Suite

This directory contains the test suite for StarHTML, organized by test type and purpose.

## Directory Structure

```
tests/
├── unit/                          # Pure unit tests (isolated, fast)
│   ├── test_core_utilities.py     # Core utility functions
│   ├── test_datastar_comprehensive.py  # Datastar attributes & SSE
│   ├── test_handlers.py           # JavaScript handler generation
│   ├── test_html_comprehensive.py # HTML module functionality
│   ├── test_html_elements.py      # HTML/SVG element creation
│   ├── test_server_missing_coverage.py # Server module coverage
│   ├── test_starapp_comprehensive.py # StarApp module functionality
│   ├── test_tags_comprehensive.py # Tags module functionality
│   └── test_xtend_comprehensive.py # Xtend module functionality
├── integration/                   # Tests requiring multiple components
│   ├── test_auth.py               # Authentication flow integration
│   ├── test_core_functionality.py # Complete HTML generation scenarios
│   ├── test_error_handling.py     # Error scenarios & graceful degradation
│   ├── test_error_handling_additional.py # Additional error cases
│   ├── test_external.py           # External library integrations
│   ├── test_file_handling.py      # File upload/download functionality
│   ├── test_live_reload.py        # Live reload development feature
│   ├── test_performance.py        # Performance benchmarks & scalability
│   ├── test_security.py           # Security features (XSS, CSRF, injection)
│   ├── test_server_functionality.py # HTTP server features & routing
│   ├── test_sse_comprehensive.py  # Server-sent events functionality
│   └── test_websocket_simple.py   # WebSocket functionality
├── browser/                       # Browser-based tests
│   ├── benchmark_handlers.html
│   ├── benchmark_handlers.js
│   └── test_attribute_selector.html
├── fixtures/                      # Shared test fixtures and utilities
│   ├── conftest.py               # Pytest configuration
│   ├── mock_datastar.py          # Mock browser environment
│   └── performance_utils.py      # Performance testing utilities
└── validation/                    # Validation and production readiness tests
    └── README.md
```

## Current Test Coverage

### Well-Tested Areas ✅
- Core HTML/SVG element creation and attribute handling
- Datastar attributes and transformations
- SSE (Server-Sent Events) functionality
- OAuth provider implementations (Google, GitHub, Discord, etc.)
- Error handling and security features
- HTTP server functionality and routing
- Performance characteristics

### Test Coverage Status ✅
- **Core modules**: All major modules have comprehensive test coverage (70%+ achieved)
- **WebSocket functionality**: Basic WebSocket tests implemented
- **External library integrations**: Tests for external.py (KaTeX, HTMX, etc.)
- **Authentication**: Auth flow and middleware tested
- **File upload/download**: File handling tests implemented
- **Live reload functionality**: Development feature tests added
- **Server functionality**: Comprehensive server tests with 91% coverage
- **Error handling**: Robust error scenario testing

### Recently Completed ✅
- **Module coverage improved**: All modules now meet 70%+ coverage target

### Running Tests

```bash
# Run all tests
uv run pytest

# Run specific test file
uv run pytest tests/unit/test_datastar_comprehensive.py -v

# Run specific test class
uv run pytest tests/unit/test_handlers.py::TestEventHandling -v

# Run with coverage
uv run pytest --cov=starhtml tests/
```

## Test Organization

### Unit Tests
Focused, isolated tests for individual functions and classes. Fast execution, no external dependencies.

### Integration Tests  
Tests that verify multiple components work together correctly. May use TestClient or require app context.

### JavaScript Handler Tests
Tests for JavaScript plugin functionality using mock browser environments. These test the logic of client-side handlers.

### Browser Tests
Actual browser-based tests including HTML test pages and performance benchmarks.

## Writing New Tests

When adding new tests:
1. **Unit tests** go in `unit/` - isolated, fast, no external dependencies
2. **Integration tests** go in `integration/` - test multiple components together
3. **JavaScript handler tests** go in `js_handlers/` - test client-side logic with mocks
4. **Browser tests** go in `browser/` - actual browser-based testing
5. Use descriptive test class names and include docstrings
6. Follow existing patterns for consistency

## Test Conventions

- Test files must start with `test_`
- Test classes should be named `Test<Feature>`
- Test methods must start with `test_`
- Use pytest fixtures for shared setup
- Mock external dependencies in unit tests