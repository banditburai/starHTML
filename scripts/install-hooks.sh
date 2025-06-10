#!/bin/bash
# Install git hooks for automated testing

HOOKS_DIR=".git/hooks"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo "Installing git hooks for StarHTML..."

# Create pre-commit hook
cat > "$PROJECT_ROOT/$HOOKS_DIR/pre-commit" << 'EOF'
#!/bin/bash
# Pre-commit hook for StarHTML
# Runs quick tests before allowing commit

echo "🧪 Running pre-commit tests..."

# Get list of Python files being committed
PYTHON_FILES=$(git diff --cached --name-only --diff-filter=ACM | grep '\.py$')

if [ -z "$PYTHON_FILES" ]; then
    echo "No Python files to test"
    exit 0
fi

# Run autotest on changed files
echo "Testing changed files: $PYTHON_FILES"
./scripts/autotest.py $PYTHON_FILES

if [ $? -ne 0 ]; then
    echo "❌ Tests failed. Commit aborted."
    echo "Fix the failing tests or run with --no-verify to skip"
    exit 1
fi

echo "✅ All tests passed!"
exit 0
EOF

# Make hook executable
chmod +x "$PROJECT_ROOT/$HOOKS_DIR/pre-commit"

# Create pre-push hook
cat > "$PROJECT_ROOT/$HOOKS_DIR/pre-push" << 'EOF'
#!/bin/bash
# Pre-push hook for StarHTML
# Runs full test suite before push

echo "🚀 Running pre-push tests..."

# Run full test suite
./scripts/autotest.py --all

if [ $? -ne 0 ]; then
    echo "❌ Tests failed. Push aborted."
    echo "Fix the failing tests or run with --no-verify to skip"
    exit 1
fi

echo "✅ All tests passed! Pushing..."
exit 0
EOF

# Make hook executable
chmod +x "$PROJECT_ROOT/$HOOKS_DIR/pre-push"

echo "✅ Git hooks installed successfully!"
echo ""
echo "Hooks installed:"
echo "  - pre-commit: Runs quick tests on changed files"
echo "  - pre-push: Runs full test suite"
echo ""
echo "To skip hooks, use --no-verify flag:"
echo "  git commit --no-verify"
echo "  git push --no-verify"