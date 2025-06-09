#!/usr/bin/env python3
"""Automated test runner with watch mode for StarHTML."""

import subprocess
import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def run_tests(watch=False, coverage=False, parallel=False, specific=None, verbose=False):
    """Run tests with various options."""
    cmd = ["uv", "run", "pytest"]
    
    if watch:
        # Use pytest-watch for auto-rerun
        cmd = ["uv", "run", "ptw", "--"]
        if not verbose:
            cmd.append("-q")
    
    if verbose:
        cmd.append("-vv")
    elif not watch:
        cmd.append("-v")
    
    if coverage and not watch:  # Coverage doesn't work well with watch mode
        cmd.extend(["--cov=src/starhtml", "--cov-report=term-missing"])
    
    if parallel and not watch:  # Parallel doesn't work well with watch mode
        cmd.extend(["-n", "auto"])  # Use all available CPUs
    
    if specific:
        cmd.append(specific)
    
    # Add color output
    cmd.append("--color=yes")
    
    print(f"Running: {' '.join(cmd)}")
    return subprocess.run(cmd).returncode


def run_quick_check():
    """Run a quick subset of tests for rapid feedback."""
    print("Running quick test check...")
    cmd = [
        "uv", "run", "pytest", 
        "-v",
        "--tb=short",
        "--maxfail=1",
        "-k", "not slow",
        "--color=yes"
    ]
    return subprocess.run(cmd).returncode


def run_demo_tests():
    """Run tests for demo files."""
    print("Testing demo files...")
    cmd = [
        "uv", "run", "pytest",
        "tests/test_demos.py",
        "-v",
        "--color=yes"
    ]
    return subprocess.run(cmd).returncode


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Run StarHTML tests")
    parser.add_argument("--watch", "-w", action="store_true", 
                       help="Watch mode - auto-rerun on file changes")
    parser.add_argument("--coverage", "-c", action="store_true", 
                       help="Generate coverage report")
    parser.add_argument("--parallel", "-p", action="store_true", 
                       help="Run tests in parallel")
    parser.add_argument("--quick", "-q", action="store_true",
                       help="Run quick test check (no slow tests)")
    parser.add_argument("--demos", "-d", action="store_true",
                       help="Run demo file tests")
    parser.add_argument("--verbose", "-v", action="store_true",
                       help="Verbose output")
    parser.add_argument("test", nargs="?", 
                       help="Specific test file or pattern")
    
    args = parser.parse_args()
    
    if args.quick:
        return run_quick_check()
    elif args.demos:
        return run_demo_tests()
    else:
        return run_tests(
            watch=args.watch, 
            coverage=args.coverage, 
            parallel=args.parallel,
            specific=args.test,
            verbose=args.verbose
        )


if __name__ == "__main__":
    sys.exit(main())