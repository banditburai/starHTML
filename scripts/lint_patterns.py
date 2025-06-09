#!/usr/bin/env python3
"""
Lint StarHTML code for idiomatic patterns.
"""

import re
import sys
from pathlib import Path
from typing import List, Tuple

class PatternLinter:
    """Check for non-idiomatic StarHTML patterns."""
    
    def __init__(self):
        self.patterns = [
            # Check for serve() without if __name__ == "__main__"
            (
                r'^serve\(\)',
                "serve() should be called within 'if __name__ == \"__main__\"' block",
                lambda line, prev_lines: not any('if __name__' in l for l in prev_lines[-5:])
            ),
            # Check for missing port in demo files
            (
                r'serve\(\s*\)$',
                "Consider specifying port for demo: serve(port=XXXX)",
                lambda line, prev_lines: True
            ),
            # Check for signals without $ in keys
            (
                r'ds_signals\s*=\s*{\s*["\'](?!\$)',
                "Signal names in ds_signals should start with $ (e.g., {'$counter': 0})"
            ),
            # Check for old signal/fragment names
            (
                r'\b(signal|fragment)\s*\(',
                "Use 'signals()' and 'fragments()' instead of singular forms"
            ),
            # Check for missing ds_ prefix
            (
                r'\b(on_click|on_change|text|show|hide)\s*=\s*["\']',
                "Use ds_ prefix for Datastar attributes (e.g., ds_on_click)"
            ),
            # Check for incorrect SSE usage
            (
                r'@rt\s*\([^\)]+\)\s*\n\s*def\s+\w+.*:\s*\n\s*yield\s+(signals|fragments)',
                "SSE endpoints that yield should have @sse decorator",
                None,
                True  # Multi-line pattern
            ),
            # Check for incorrect star_app usage
            (
                r'^\s*app\s*=\s*star_app\s*\(',
                "Use 'app, rt = star_app(...)' to unpack both app and route decorator"
            ),
            # Check for HTML in wrong position
            (
                r'(Div|Button|P|H\d|Span)\s*\([^)]*\bid\s*=[^,)]+,[^)]*\)',
                "HTML attributes should come after all children: Div(child1, child2, id='...')"
            ),
            # Check for missing type hints in route functions
            (
                r'@rt\s*\([^\)]+\)\s*\n\s*def\s+(\w+)\s*\(\s*\):',
                "Route functions should accept request parameter: def route_name(req):"
            ),
            # Check for print statements without context
            (
                r'^\s*print\s*\(',
                "Add descriptive context to print statements for debugging"
            ),
        ]
        
    def lint_file(self, filepath: Path) -> List[Tuple[int, str]]:
        """Lint a file for patterns."""
        issues = []
        
        # Skip __pycache__ and test files
        if '__pycache__' in str(filepath) or 'test_' in filepath.name:
            return issues
        
        with open(filepath, 'r') as f:
            lines = f.readlines()
        
        # Check each pattern
        for pattern_info in self.patterns:
            if len(pattern_info) >= 4 and pattern_info[3]:  # Multi-line pattern
                # Handle multi-line patterns
                full_content = ''.join(lines)
                if re.search(pattern_info[0], full_content, re.MULTILINE | re.DOTALL):
                    # Find approximate line number
                    for i, line in enumerate(lines, 1):
                        if '@rt' in line:
                            issues.append((i, pattern_info[1]))
                            break
            else:
                # Single line patterns
                for i, line in enumerate(lines, 1):
                    pattern = pattern_info[0]
                    message = pattern_info[1]
                    
                    # Check if pattern has a condition function
                    if len(pattern_info) >= 3 and pattern_info[2]:
                        condition = pattern_info[2]
                        if re.search(pattern, line) and condition(line, lines[:i-1]):
                            issues.append((i, message))
                    else:
                        if re.search(pattern, line):
                            issues.append((i, message))
        
        # Additional checks for demo files
        if 'demo' in str(filepath):
            # Check for proper demo structure
            has_main_block = any('if __name__' in line for line in lines)
            if not has_main_block and 'serve' in ''.join(lines):
                issues.append((len(lines), "Demo files should have 'if __name__ == \"__main__\"' block"))
            
            # Check for helpful print statements
            has_print = any('print' in line and 'http' in line for line in lines)
            if has_main_block and not has_print:
                issues.append((
                    len(lines), 
                    "Demo files should print the URL when starting (e.g., print('Running on http://localhost:5001'))"
                ))
        
        return issues


def format_issue(filepath: Path, line_num: int, message: str) -> str:
    """Format an issue for display."""
    return f"  Line {line_num}: {message}"


def main():
    """Run pattern linting."""
    if len(sys.argv) < 2:
        print("Usage: python lint_patterns.py <file_or_directory>")
        sys.exit(1)
    
    linter = PatternLinter()
    target = Path(sys.argv[1])
    
    if target.is_file():
        files = [target]
    else:
        files = list(target.glob("**/*.py"))
    
    total_issues = 0
    files_with_issues = 0
    
    for filepath in sorted(files):
        # Skip certain directories
        if any(skip in str(filepath) for skip in ['__pycache__', 'scripts', '.git']):
            continue
            
        issues = linter.lint_file(filepath)
        if issues:
            files_with_issues += 1
            print(f"\n{filepath}:")
            for line, msg in sorted(issues):
                print(format_issue(filepath, line, msg))
                total_issues += 1
    
    if total_issues == 0:
        print("✅ No pattern issues found!")
    else:
        print(f"\nTotal: {total_issues} issues in {files_with_issues} files")
    
    return 1 if total_issues > 0 else 0


if __name__ == "__main__":
    sys.exit(main())