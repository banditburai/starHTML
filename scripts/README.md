# Release Scripts

## `release.sh`

Automated release script for StarHTML that handles version bumping and PyPI deployment.

### Usage

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

### What it does

1. **Validates environment**: Checks that you're in a git repo with a clean working directory
2. **Bumps version**: Uses `bump-my-version` to update version in `pyproject.toml`
3. **Creates git tag**: Automatically commits the version change and creates a git tag
4. **Pushes to GitHub**: Pushes both the commit and the tag to GitHub
5. **Triggers automation**: GitHub Actions will automatically:
   - Create a GitHub release with changelog
   - Build the package
   - Publish to PyPI

### Prerequisites

- Clean git working directory (all changes committed)
- `uv` installed with dev dependencies
- Push access to the GitHub repository 