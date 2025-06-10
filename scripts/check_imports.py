#!/usr/bin/env python3
"""
Check StarHTML import dependencies and suggest fixes.
"""

import ast
import sys
from pathlib import Path
from typing import Set, Dict, List

# Known component mappings
COMPONENT_MAPPINGS = {
    'Button': 'components.ui.button',
    'IconifyIcon': 'components.ui.iconify',
    'Icon': 'components.ui.iconify',
    'ThemeToggle': 'components.ui.theme_toggle',
    'DocsLayout': 'components.docs.layout',
    'DocsHeader': 'components.docs.header',
    'DocsSidebar': 'components.docs.sidebar',
    'DocsBreadcrumb': 'components.docs.breadcrumb',
    'DocsFooter': 'components.docs.footer',
    'ComponentDocPage': 'components.docs.page_template',
    'PreviewCard': 'components.docs.preview_card',
    'CodeBlock': 'components.docs.code_block',
    'InstallationSection': 'components.docs.installation_section',
}

# Built-in names to ignore
BUILTINS = set(dir(__builtins__)) | {
    'app', 'rt', 'req', 'serve', 'true', 'false', 'null',
    'print', 'len', 'range', 'enumerate', 'zip', 'map', 'filter',
    'any', 'all', 'sum', 'min', 'max', 'sorted', 'reversed',
}

# StarHTML core exports (from 'starhtml import *')
STARHTML_EXPORTS = {
    'Div', 'P', 'H1', 'H2', 'H3', 'H4', 'H5', 'H6',
    'Span', 'A', 'Button', 'Input', 'Form', 'Label',
    'Table', 'Thead', 'Tbody', 'Tr', 'Th', 'Td',
    'Ul', 'Ol', 'Li', 'Pre', 'Code', 'Br', 'Hr',
    'Script', 'Style', 'Link', 'Meta', 'Title',
    'star_app', 'serve', 'rt', 'sse', 'SSE',
    'signals', 'fragments', 'Response',
    'ds_signals', 'ds_on_click', 'ds_text', 'ds_show',
}

class ImportChecker(ast.NodeVisitor):
    """Check for missing imports."""
    
    def __init__(self):
        self.imports: Dict[str, str] = {}
        self.used_names: Set[str] = set()
        self.missing_imports: Dict[str, str] = {}
        self.defined_names: Set[str] = set()
        
    def visit_ImportFrom(self, node: ast.ImportFrom):
        """Track imports."""
        if node.module:
            for alias in node.names:
                if alias.name == '*':
                    # Wildcard import
                    if node.module == 'starhtml':
                        # Add all starhtml exports
                        for name in STARHTML_EXPORTS:
                            self.imports[name] = node.module
                else:
                    self.imports[alias.asname or alias.name] = node.module
        self.generic_visit(node)
    
    def visit_Import(self, node: ast.Import):
        """Track regular imports."""
        for alias in node.names:
            self.imports[alias.asname or alias.name] = alias.name
        self.generic_visit(node)
    
    def visit_FunctionDef(self, node: ast.FunctionDef):
        """Track function definitions."""
        self.defined_names.add(node.name)
        # Track parameter names
        for arg in node.args.args:
            self.defined_names.add(arg.arg)
        self.generic_visit(node)
    
    def visit_ClassDef(self, node: ast.ClassDef):
        """Track class definitions."""
        self.defined_names.add(node.name)
        self.generic_visit(node)
    
    def visit_Assign(self, node: ast.Assign):
        """Track variable assignments."""
        for target in node.targets:
            if isinstance(target, ast.Name):
                self.defined_names.add(target.id)
            elif isinstance(target, ast.Tuple):
                for elt in target.elts:
                    if isinstance(elt, ast.Name):
                        self.defined_names.add(elt.id)
        self.generic_visit(node)
    
    def visit_Name(self, node: ast.Name):
        """Track name usage."""
        if isinstance(node.ctx, ast.Load):
            self.used_names.add(node.id)
        self.generic_visit(node)
    
    def check_missing(self):
        """Find missing imports."""
        for name in self.used_names:
            # Skip if already imported, defined locally, or is a builtin
            if (name in self.imports or 
                name in self.defined_names or 
                name in BUILTINS):
                continue
                
            # Check if it's a known component
            if name in COMPONENT_MAPPINGS:
                self.missing_imports[name] = COMPONENT_MAPPINGS[name]
                
        return self.missing_imports


def check_file(filepath: Path) -> bool:
    """Check a file for missing imports. Returns True if issues found."""
    with open(filepath, 'r') as f:
        content = f.read()
    
    try:
        tree = ast.parse(content)
        checker = ImportChecker()
        checker.visit(tree)
        missing = checker.check_missing()
        
        if missing:
            print(f"\n{filepath}:")
            print("  Missing imports detected:")
            for name, module in sorted(missing.items()):
                print(f"    {name} (from {module})")
            
            # Generate import statements
            print("\n  Add these imports:")
            imports_by_module = {}
            for name, module in missing.items():
                if module not in imports_by_module:
                    imports_by_module[module] = []
                imports_by_module[module].append(name)
            
            for module, names in sorted(imports_by_module.items()):
                print(f"    from {module} import {', '.join(sorted(names))}")
            
            return True
                
    except SyntaxError as e:
        print(f"\n{filepath}: SyntaxError on line {e.lineno}")
        return True
    
    return False


def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        print("Usage: python check_imports.py <file_or_directory>")
        sys.exit(1)
    
    target = Path(sys.argv[1])
    issues_found = False
    
    if target.is_file():
        issues_found = check_file(target)
    elif target.is_dir():
        files_checked = 0
        for filepath in sorted(target.glob("**/*.py")):
            if ('test_' not in filepath.name and 
                '__pycache__' not in str(filepath) and
                'scripts' not in str(filepath)):
                files_checked += 1
                if check_file(filepath):
                    issues_found = True
        
        if not issues_found and files_checked > 0:
            print(f"✅ All {files_checked} files have correct imports!")
    
    return 1 if issues_found else 0


if __name__ == "__main__":
    sys.exit(main())