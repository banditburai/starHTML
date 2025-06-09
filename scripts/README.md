# StarHTML Scripts

This directory contains various scripts for development, validation, and release management.

## Validation Tools

### `validate_starhtml.py` - Syntax Validator

Validates StarHTML syntax patterns using AST analysis.

**Usage:**
```bash
python scripts/validate_starhtml.py demo/
python scripts/validate_starhtml.py demo/my_app.py
```

**What it checks:**
- Proper `app, rt = star_app()` initialization pattern
- Use of `@rt()` decorators instead of `@app.route()`
- Correct decorator ordering (`@sse` after `@rt`)
- Capitalized component names (e.g., `Div()` not `div()`)
- Missing imports for special components like `Script`, `Style`

**Example output:**
```
demo/bad_app.py:10: ERROR: Use @rt() instead of @app.route()
demo/bad_app.py:15: ERROR: Use capitalized Div() instead of div()
demo/bad_app.py:0: WARNING: Potentially missing import for Script
```

### `check_patterns.py` - Pattern Consistency Checker

Checks for consistent patterns across StarHTML files using regex.

**Usage:**
```bash
python scripts/check_patterns.py demo/
python scripts/check_patterns.py examples/
```

**What it checks:**
- Initialization patterns (`star_app()` vs `StarHTML()`)
- Route decorator patterns
- SSE decorator ordering
- Lowercase HTML function usage
- Mixed `ds_` and `data_` prefixes
- Custom serve configurations

**Example output:**
```
demo/app.py: ERROR: Uses StarHTML() instead of star_app()
demo/app.py: WARNING: Mixed ds_ and data_ prefixes (prefer ds_)
demo/server.py: INFO: Custom serve configuration: serve(port=8000)
```

### `fix_starhtml.py` - Auto-fixer

Automatically fixes common StarHTML pattern issues.

**Usage:**
```bash
# Dry run (shows what would be changed)
python scripts/fix_starhtml.py --dry-run demo/

# Apply fixes
python scripts/fix_starhtml.py demo/
```

**What it fixes:**
- `app = StarHTML()` → `app, rt = star_app()`
- `@app.route()` → `@rt()`
- Lowercase tags → Capitalized components
- `data_*` attributes → `ds_*` attributes
- Incorrect decorator ordering

**Example output:**
```
Fixed: demo/app.py
No changes needed: demo/server.py
✓ Fixed 1 files
```

## Integration

### Pre-commit Hook

Add to `.pre-commit-config.yaml`:

```yaml
repos:
  - repo: local
    hooks:
      - id: starhtml-validate
        name: StarHTML Syntax Validator
        entry: python scripts/validate_starhtml.py
        language: python
        files: '\.py$'
        exclude: '^(tests/|setup\.py|build/)'
```

### CI/CD (GitHub Actions)

Add to `.github/workflows/starhtml-check.yml`:

```yaml
name: StarHTML Checks

on: [push, pull_request]

jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    - uses: actions/setup-python@v4
      with:
        python-version: '3.11'
    - name: Install dependencies
      run: |
        pip install uv
        uv pip install -e .
    - name: Run validators
      run: |
        python scripts/validate_starhtml.py demo/ examples/
        python scripts/check_patterns.py demo/ examples/
```

### VS Code Integration

Add to `.vscode/tasks.json`:

```json
{
  "version": "2.0.0",
  "tasks": [
    {
      "label": "Validate StarHTML",
      "type": "shell",
      "command": "python",
      "args": ["${workspaceFolder}/scripts/validate_starhtml.py", "${file}"],
      "problemMatcher": {
        "pattern": {
          "regexp": "^(.+?):(\\d+):\\s*(ERROR|WARNING):\\s*(.+)$",
          "file": 1,
          "line": 2,
          "severity": 3,
          "message": 4
        }
      }
    }
  ]
}
```

## Common Issues and Solutions

### Issue: "Missing import for Script"
**Solution:** Add explicit import when using special components:
```python
from starhtml import Script, Style
```

### Issue: "Use @rt() instead of @app.route()"
**Solution:** Use the route decorator from `star_app()`:
```python
app, rt = star_app()

@rt('/')
def home(): ...
```

### Issue: "@sse should come after route decorator"
**Solution:** Correct decorator order:
```python
@rt('/api/data')
@sse
def get_data(): ...
```

### Issue: "Use capitalized Div() instead of div()"
**Solution:** Use StarHTML's capitalized components:
```python
# Wrong
div(p("Hello"))

# Right
Div(P("Hello"))
```

## Best Practices

1. **Always use `star_app()` pattern**
   ```python
   app, rt = star_app(title="My App")
   ```

2. **Use `@rt()` for routes**
   ```python
   @rt('/')
   def home(): ...
   ```

3. **Correct decorator ordering**
   ```python
   @rt('/api/data')
   @sse
   def get_data(): ...
   ```

4. **Use capitalized components**
   ```python
   Div(P("Hello"), Button("Click"))
   ```

5. **Prefer `ds_` prefixes**
   ```python
   Button("Click", ds_on_click="...")
   ```

## Release Scripts

### `release.sh`

Automated release script for StarHTML that handles version bumping and PyPI deployment.

**Usage:**
```bash
# Bump patch version (0.1.0 -> 0.1.1)
./scripts/release.sh patch

# Bump minor version (0.1.0 -> 0.2.0)
./scripts/release.sh minor

# Bump major version (0.1.0 -> 1.0.0)
./scripts/release.sh major

# Default is patch if no argument provided
./scripts/release.sh
```

**What it does:**

1. **Validates environment**: Checks that you're in a git repo with a clean working directory
2. **Bumps version**: Uses `bump-my-version` to update version in `pyproject.toml`
3. **Creates git tag**: Automatically commits the version change and creates a git tag
4. **Pushes to GitHub**: Pushes both the commit and the tag to GitHub
5. **Triggers automation**: GitHub Actions will automatically:
   - Create a GitHub release with changelog
   - Build the package
   - Publish to PyPI

**Prerequisites:**

- Clean git working directory (all changes committed)
- `uv` installed with dev dependencies
- Push access to the GitHub repository

## Development

To add new validation rules:

1. For AST-based checks, modify `StarHTMLValidator` in `validate_starhtml.py`
2. For pattern-based checks, add patterns to `PatternChecker` in `check_patterns.py`
3. For auto-fixes, add replacements to `fix_file()` in `fix_starhtml.py` 