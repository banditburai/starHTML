#!/usr/bin/env python3
"""Auto-fix common StarHTML patterns"""

import re
import sys
from pathlib import Path

def fix_file(filepath: Path, dry_run=False):
    """Apply common fixes to a file"""
    try:
        content = filepath.read_text()
        original = content
        
        # Skip non-app files
        if filepath.name.startswith('test_') and 'star_app' not in content:
            return False
        if '__name__ == "__main__"' not in content and 'serve(' not in content:
            return False
        
        # Fix app initialization
        content = re.sub(
            r'app\s*=\s*StarHTML\([^)]*\)',
            'app, rt = star_app()',
            content
        )
        
        # Fix route decorators
        content = re.sub(
            r'@app\.route\(',
            '@rt(',
            content
        )
        
        # Fix lowercase tags (common ones)
        replacements = {
            r'\bdiv\(': 'Div(',
            r'\bspan\(': 'Span(',
            r'\bbutton\(': 'Button(',
            r'\bp\(': 'P(',
            r'\bh1\(': 'H1(',
            r'\bh2\(': 'H2(',
            r'\bh3\(': 'H3(',
            r'\bscript\(': 'Script(',
            r'\bstyle\(': 'Style(',
            r'\bform\(': 'Form(',
            r'\binput\(': 'Input(',
            r'\blabel\(': 'Label(',
            r'\ba\(': 'A(',
            r'\bimg\(': 'Img(',
            r'\blink\(': 'Link(',
        }
        
        for pattern, replacement in replacements.items():
            content = re.sub(pattern, replacement, content)
        
        # Fix data_ to ds_ prefixes
        content = re.sub(r'\bdata_on_click\b', 'ds_on_click', content)
        content = re.sub(r'\bdata_show\b', 'ds_show', content)
        content = re.sub(r'\bdata_text\b', 'ds_text', content)
        content = re.sub(r'\bdata_signal\b', 'ds_signal', content)
        content = re.sub(r'\bdata_ref\b', 'ds_ref', content)
        content = re.sub(r'\bdata_bind\b', 'ds_bind', content)
        
        # Fix decorator ordering (simple case)
        content = re.sub(
            r'@sse\s*\n(\s*)@rt\(',
            r'\1@rt(\2\n\1@sse',
            content
        )
        
        if content != original:
            if dry_run:
                print(f"Would fix: {filepath}")
                # Show diff
                import difflib
                diff = difflib.unified_diff(
                    original.splitlines(keepends=True),
                    content.splitlines(keepends=True),
                    fromfile=str(filepath),
                    tofile=str(filepath),
                    n=3
                )
                sys.stdout.writelines(diff)
                print()
            else:
                filepath.write_text(content)
                print(f"Fixed: {filepath}")
            return True
        else:
            if not dry_run:
                print(f"No changes needed: {filepath}")
            return False
            
    except Exception as e:
        print(f"Error processing {filepath}: {e}")
        return False

def main():
    """Fix StarHTML patterns in specified files or directories"""
    if len(sys.argv) < 2:
        print("Usage: fix-starhtml [--dry-run] <file_or_directory> ...")
        sys.exit(1)
    
    args = sys.argv[1:]
    dry_run = False
    
    if args[0] == '--dry-run':
        dry_run = True
        args = args[1:]
    
    fixed_count = 0
    
    for arg in args:
        path = Path(arg)
        if path.is_file() and path.suffix == '.py':
            if fix_file(path, dry_run):
                fixed_count += 1
        elif path.is_dir():
            for py_file in path.rglob('*.py'):
                # Skip hidden directories and __pycache__
                if not any(part.startswith('.') or part == '__pycache__' for part in py_file.parts):
                    if fix_file(py_file, dry_run):
                        fixed_count += 1
    
    if dry_run:
        print(f"\n{fixed_count} files would be fixed")
    else:
        print(f"\n✓ Fixed {fixed_count} files")

if __name__ == "__main__":
    main()