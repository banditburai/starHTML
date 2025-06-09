#!/usr/bin/env python3
"""
Automated testing helper for StarHTML development.
Provides intelligent test running based on what files have changed.
"""

import subprocess
import sys
import os
from pathlib import Path
import argparse
import time
from datetime import datetime

# ANSI color codes
GREEN = '\033[92m'
YELLOW = '\033[93m'
RED = '\033[91m'
BLUE = '\033[94m'
RESET = '\033[0m'
BOLD = '\033[1m'


class TestRunner:
    def __init__(self, verbose=False):
        self.verbose = verbose
        self.project_root = Path(__file__).parent.parent
        self.last_run_time = None
        
    def log(self, message, color=None):
        """Print colored log message."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        color_code = color or ""
        print(f"{color_code}[{timestamp}] {message}{RESET}")
    
    def run_command(self, cmd, description=None):
        """Run a command and return success status."""
        if description:
            self.log(f"🧪 {description}", BLUE)
        
        if self.verbose:
            self.log(f"$ {' '.join(cmd)}", YELLOW)
        
        start_time = time.time()
        result = subprocess.run(cmd, cwd=self.project_root)
        elapsed = time.time() - start_time
        
        if result.returncode == 0:
            self.log(f"✅ Passed in {elapsed:.1f}s", GREEN)
        else:
            self.log(f"❌ Failed in {elapsed:.1f}s", RED)
            
        return result.returncode == 0
    
    def get_related_tests(self, file_path):
        """Determine which tests to run based on changed file."""
        file_path = Path(file_path)
        tests = []
        
        # If it's a test file, run it
        if file_path.name.startswith("test_"):
            tests.append(str(file_path))
            return tests
        
        # If it's in src/starhtml, find related tests
        if "src/starhtml" in str(file_path):
            component_name = file_path.stem
            
            # Look for specific test files
            test_patterns = [
                f"test_{component_name}.py",
                f"test_*{component_name}*.py",
                f"*{component_name}*test*.py"
            ]
            
            tests_dir = self.project_root / "tests"
            for pattern in test_patterns:
                matching_tests = list(tests_dir.glob(pattern))
                tests.extend(str(t) for t in matching_tests)
            
            # If component-specific tests found, use them
            if tests:
                return tests
            
            # Otherwise, run tests that might import this module
            if component_name == "datastar":
                tests.append("-k datastar")
            elif component_name == "components":
                tests.append("-k component")
            elif component_name == "core":
                # Core changes affect everything, run quick tests
                tests.append("-m 'not slow'")
        
        # If it's a demo file, run demo tests
        if "demo/" in str(file_path):
            tests.append("tests/test_demos.py")
            # Also run specific test for this demo if pattern matches
            demo_name = file_path.stem
            tests.append(f"-k {demo_name}")
        
        # If no specific tests found, run quick test suite
        if not tests:
            tests.append("-m 'not slow'")
            
        return tests
    
    def run_quick_tests(self):
        """Run a quick subset of tests."""
        cmd = [
            "uv", "run", "pytest",
            "-v", "--tb=short",
            "--maxfail=3",
            "-m", "not slow",
            "--color=yes"
        ]
        return self.run_command(cmd, "Running quick tests")
    
    def run_all_tests(self):
        """Run full test suite with coverage."""
        cmd = [
            "uv", "run", "pytest",
            "-v",
            "--cov=src/starhtml",
            "--cov-report=term-missing",
            "--color=yes"
        ]
        return self.run_command(cmd, "Running all tests with coverage")
    
    def run_specific_tests(self, test_specs):
        """Run specific tests."""
        cmd = ["uv", "run", "pytest", "-v", "--tb=short", "--color=yes"]
        cmd.extend(test_specs)
        
        desc = f"Running tests: {' '.join(test_specs)}"
        return self.run_command(cmd, desc)
    
    def run_failed_tests(self):
        """Re-run only failed tests."""
        cmd = [
            "uv", "run", "pytest",
            "--lf", "-v",
            "--tb=short",
            "--color=yes"
        ]
        return self.run_command(cmd, "Re-running failed tests")
    
    def run_watch_mode(self):
        """Start test watcher."""
        self.log("👀 Starting test watcher (Ctrl+C to stop)", BLUE)
        cmd = [
            "uv", "run", "ptw", "--",
            "-v", "--tb=short",
            "-m", "not slow",
            "--color=yes"
        ]
        subprocess.run(cmd, cwd=self.project_root)
    
    def check_imports(self):
        """Quick import check for all modules."""
        self.log("🔍 Checking imports...", BLUE)
        
        # Try importing main modules
        test_imports = [
            "from starhtml import star_app",
            "from starhtml import Div, H1, Button",
            "from starhtml.datastar import sse, signals",
        ]
        
        for import_stmt in test_imports:
            try:
                exec(import_stmt)
                self.log(f"✅ {import_stmt}", GREEN)
            except Exception as e:
                self.log(f"❌ {import_stmt}: {e}", RED)
                return False
                
        return True
    
    def run_demo_validation(self):
        """Validate all demo files."""
        cmd = [
            "uv", "run", "pytest",
            "tests/test_demos.py",
            "-v",
            "--color=yes"
        ]
        return self.run_command(cmd, "Validating demo files")
    
    def suggest_next_steps(self, success):
        """Suggest next steps based on test results."""
        print("\n" + "="*50)
        if success:
            self.log("🎉 All tests passed!", GREEN)
            print("\nNext steps:")
            print("  1. Run full test suite: ./scripts/autotest.py --all")
            print("  2. Check coverage: ./scripts/autotest.py --coverage")
            print("  3. Start watcher: ./scripts/autotest.py --watch")
        else:
            self.log("💡 Some tests failed", YELLOW)
            print("\nNext steps:")
            print("  1. Fix failing tests")
            print("  2. Re-run failed: ./scripts/autotest.py --failed")
            print("  3. Run specific test: ./scripts/autotest.py <test_file>")


def main():
    parser = argparse.ArgumentParser(
        description="Intelligent test runner for StarHTML",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                    # Run quick tests
  %(prog)s --all              # Run all tests with coverage  
  %(prog)s --watch            # Start test watcher
  %(prog)s --failed           # Re-run failed tests
  %(prog)s src/starhtml/button.py  # Run tests related to button.py
  %(prog)s tests/test_button.py    # Run specific test file
  %(prog)s --demos            # Validate all demo files
"""
    )
    
    parser.add_argument("files", nargs="*", 
                       help="Specific files to test (auto-detects related tests)")
    parser.add_argument("--all", "-a", action="store_true",
                       help="Run all tests with coverage")
    parser.add_argument("--watch", "-w", action="store_true",
                       help="Start test watcher")
    parser.add_argument("--failed", "-f", action="store_true",
                       help="Re-run only failed tests")
    parser.add_argument("--quick", "-q", action="store_true",
                       help="Run quick tests only (default)")
    parser.add_argument("--demos", "-d", action="store_true",
                       help="Validate demo files")
    parser.add_argument("--coverage", "-c", action="store_true",
                       help="Generate HTML coverage report")
    parser.add_argument("--verbose", "-v", action="store_true",
                       help="Verbose output")
    
    args = parser.parse_args()
    runner = TestRunner(verbose=args.verbose)
    
    # Always start with import check
    if not runner.check_imports():
        runner.log("⚠️  Import errors detected - fix these first!", RED)
        return 1
    
    success = True
    
    if args.watch:
        runner.run_watch_mode()
    elif args.all:
        success = runner.run_all_tests()
    elif args.failed:
        success = runner.run_failed_tests()
    elif args.demos:
        success = runner.run_demo_validation()
    elif args.coverage:
        cmd = [
            "uv", "run", "pytest",
            "--cov=src/starhtml",
            "--cov-report=html",
            "--cov-report=term",
            "--color=yes"
        ]
        success = runner.run_command(cmd, "Generating coverage report")
        if success:
            runner.log("📊 Coverage report: htmlcov/index.html", BLUE)
            # Try to open in browser
            import webbrowser
            webbrowser.open(f"file://{runner.project_root}/htmlcov/index.html")
    elif args.files:
        # Run tests for specific files
        all_tests = []
        for file in args.files:
            tests = runner.get_related_tests(file)
            all_tests.extend(tests)
        
        # Remove duplicates while preserving order
        unique_tests = list(dict.fromkeys(all_tests))
        success = runner.run_specific_tests(unique_tests)
    else:
        # Default: run quick tests
        success = runner.run_quick_tests()
    
    if not args.watch:
        runner.suggest_next_steps(success)
    
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())