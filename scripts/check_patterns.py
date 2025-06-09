#!/usr/bin/env python3
"""Check for consistent patterns across StarHTML files"""

import re
import sys
from pathlib import Path
from typing import List, Dict, Set
from collections import defaultdict

class PatternChecker:
    """Check for consistent patterns in StarHTML code"""
    
    def __init__(self):
        self.patterns = {
            # Check for consistent initialization
            'star_app_pattern': re.compile(r'app,\s*rt\s*=\s*star_app\('),
            'wrong_app_init': re.compile(r'app\s*=\s*StarHTML\('),
            
            # Check for route decorators
            'rt_decorator': re.compile(r'@rt\([\'"]'),
            'app_route': re.compile(r'@app\.route\('),
            
            # Check for SSE patterns
            'sse_decorator': re.compile(r'@sse'),
            'correct_sse_pattern': re.compile(r'@rt\([^)]+\)\s*\n\s*@sse'),
            'wrong_sse_pattern': re.compile(r'@sse\s*\n\s*@rt\('),
            
            # Check for component patterns
            'lowercase_tags': re.compile(r'\b(div|span|button|p|h[1-6]|script|style|form|input|label)\('),
            
            # Check for datastar patterns
            'ds_prefix': re.compile(r'\bds_\w+\s*='),
            'data_prefix': re.compile(r'\bdata_\w+\s*='),
            
            # Check serve patterns
            'serve_with_args': re.compile(r'serve\([^)]+\)'),
            'serve_no_args': re.compile(r'serve\(\s*\)'),
        }
        
    def check_file(self, filepath: Path) -> Dict[str, List[str]]:
        """Check patterns in a single file"""
        issues = defaultdict(list)
        
        try:
            content = filepath.read_text()
            
            # Skip non-app files
            if filepath.name.startswith('test_') and 'star_app' not in content:
                return dict(issues)
            if '__name__ == "__main__"' not in content and 'serve(' not in content:
                return dict(issues)
            
            lines = content.split('\n')
            
            # Check patterns
            if self.patterns['wrong_app_init'].search(content):
                issues['error'].append("Uses StarHTML() instead of star_app()")
                
            if self.patterns['app_route'].search(content):
                issues['error'].append("Uses @app.route() instead of @rt()")
                
            if self.patterns['wrong_sse_pattern'].search(content):
                issues['error'].append("@sse decorator before @rt (should be after)")
                
            # Check for lowercase HTML functions
            lowercase_matches = self.patterns['lowercase_tags'].findall(content)
            if lowercase_matches:
                unique_tags = set(lowercase_matches)
                issues['warning'].append(f"Uses lowercase tags: {', '.join(unique_tags)}")
                
            # Check datastar attribute consistency
            has_ds = bool(self.patterns['ds_prefix'].search(content))
            has_data = bool(self.patterns['data_prefix'].search(content))
            if has_ds and has_data:
                issues['warning'].append("Mixed ds_ and data_ prefixes (prefer ds_)")
                
            # Check serve patterns
            if self.patterns['serve_with_args'].search(content):
                serve_matches = self.patterns['serve_with_args'].findall(content)
                for match in serve_matches:
                    if 'host=' in match or 'port=' in match:
                        issues['info'].append(f"Custom serve configuration: {match}")
                        
        except Exception as e:
            issues['error'].append(f"Failed to read file: {str(e)}")
            
        return dict(issues)

def main():
    """Check patterns in specified files or directories"""
    if len(sys.argv) < 2:
        print("Usage: check-patterns <file_or_directory> ...")
        sys.exit(1)
    
    checker = PatternChecker()
    total_issues = 0
    
    for arg in sys.argv[1:]:
        path = Path(arg)
        files_to_check = []
        
        if path.is_file() and path.suffix == '.py':
            files_to_check.append(path)
        elif path.is_dir():
            files_to_check.extend(path.rglob('*.py'))
            
        for filepath in files_to_check:
            # Skip hidden directories and __pycache__
            if any(part.startswith('.') or part == '__pycache__' for part in filepath.parts):
                continue
                
            issues = checker.check_file(filepath)
            
            if issues:
                for level, messages in issues.items():
                    for msg in messages:
                        print(f"{filepath}: {level.upper()}: {msg}")
                        if level in ('error', 'warning'):
                            total_issues += 1
    
    if total_issues == 0:
        print("✓ No pattern issues found")
    else:
        print(f"\n⚠️  Found {total_issues} pattern issues")
        sys.exit(1)

if __name__ == "__main__":
    main()