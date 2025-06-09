#!/bin/bash
# Quick test commands for StarHTML development

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}StarHTML Quick Test Commands${NC}"
echo "================================"

# Function to run a test command
run_test() {
    local description=$1
    local command=$2
    echo -e "\n${YELLOW}$description${NC}"
    echo "Command: $command"
    echo "--------------------------------"
    eval $command
}

case "${1:-all}" in
    "all")
        run_test "Running all tests with coverage" \
            "uv run pytest --cov=src/starhtml --cov-report=term-missing"
        ;;
    "quick")
        run_test "Running quick tests (no slow tests)" \
            "uv run pytest -v --tb=short --maxfail=1 -m 'not slow'"
        ;;
    "watch")
        run_test "Starting test watcher (auto-rerun on changes)" \
            "uv run ptw -- -v --tb=short"
        ;;
    "demos")
        run_test "Testing demo files" \
            "uv run pytest tests/test_demos.py -v"
        ;;
    "datastar")
        run_test "Running Datastar-specific tests" \
            "uv run pytest -k datastar -v"
        ;;
    "coverage")
        run_test "Generating detailed coverage report" \
            "uv run pytest --cov=src/starhtml --cov-report=html && echo 'Open htmlcov/index.html to view report'"
        ;;
    "parallel")
        run_test "Running tests in parallel" \
            "uv run pytest -n auto"
        ;;
    "failed")
        run_test "Re-running only failed tests" \
            "uv run pytest --lf -v"
        ;;
    "new")
        # For testing newly added files
        if [ -z "$2" ]; then
            echo -e "${RED}Error: Please specify a test file or pattern${NC}"
            echo "Usage: $0 new <test_file_or_pattern>"
            exit 1
        fi
        run_test "Running specific test: $2" \
            "uv run pytest $2 -vv"
        ;;
    "help"|*)
        echo -e "\n${GREEN}Available commands:${NC}"
        echo "  all      - Run all tests with coverage (default)"
        echo "  quick    - Run quick tests only (skip slow tests)"
        echo "  watch    - Start test watcher (auto-rerun on changes)"
        echo "  demos    - Test all demo files"
        echo "  datastar - Run Datastar-specific tests"
        echo "  coverage - Generate HTML coverage report"
        echo "  parallel - Run tests in parallel"
        echo "  failed   - Re-run only failed tests"
        echo "  new <pattern> - Run specific test file or pattern"
        echo ""
        echo -e "${YELLOW}Examples:${NC}"
        echo "  ./scripts/quick_test.sh"
        echo "  ./scripts/quick_test.sh quick"
        echo "  ./scripts/quick_test.sh watch"
        echo "  ./scripts/quick_test.sh new tests/test_button.py"
        echo "  ./scripts/quick_test.sh new 'test_*docs*'"
        ;;
esac