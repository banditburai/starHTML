#!/usr/bin/env python3
"""StarHTML syntax validator using AST analysis"""

import ast
import sys
from pathlib import Path
from typing import List, Tuple, Set

class StarHTMLValidator(ast.NodeVisitor):
    """Validates StarHTML syntax patterns"""
    
    def __init__(self, filename: str):
        self.filename = filename
        self.errors: List[Tuple[int, str]] = []
        self.warnings: List[Tuple[int, str]] = []
        self.imports: Set[str] = set()
        self.has_star_import = False
        self.has_star_app = False
        self.route_decorator_name = None
        self.used_components: Set[str] = set()
        
    def visit_ImportFrom(self, node):
        """Track imports from starhtml"""
        if node.module == 'starhtml':
            if any(alias.name == '*' for alias in node.names):
                self.has_star_import = True
            else:
                for alias in node.names:
                    self.imports.add(alias.name)
        self.generic_visit(node)
        
    def visit_Assign(self, node):
        """Check for star_app pattern"""
        if (isinstance(node.value, ast.Call) and 
            isinstance(node.value.func, ast.Name) and 
            node.value.func.id == 'star_app'):
            
            if len(node.targets) == 1 and isinstance(node.targets[0], ast.Tuple):
                elts = node.targets[0].elts
                if len(elts) == 2:
                    self.has_star_app = True
                    if isinstance(elts[1], ast.Name):
                        self.route_decorator_name = elts[1].id
                else:
                    self.errors.append((node.lineno, 
                        "star_app() should be unpacked as: app, rt = star_app()"))
            else:
                self.errors.append((node.lineno, 
                    "star_app() should be unpacked as: app, rt = star_app()"))
                    
        self.generic_visit(node)
        
    def visit_FunctionDef(self, node):
        """Check decorator patterns"""
        sse_idx = None
        rt_idx = None
        
        for i, decorator in enumerate(node.decorator_list):
            if isinstance(decorator, ast.Name):
                if decorator.id == 'sse':
                    sse_idx = i
            elif isinstance(decorator, ast.Call):
                if isinstance(decorator.func, ast.Name):
                    if decorator.func.id == self.route_decorator_name:
                        rt_idx = i
                    elif decorator.func.id == 'rt':
                        rt_idx = i
                        if self.route_decorator_name and self.route_decorator_name != 'rt':
                            self.warnings.append((decorator.lineno,
                                f"Using @rt but route decorator is {self.route_decorator_name}"))
                elif isinstance(decorator.func, ast.Attribute):
                    if decorator.func.attr == 'route':
                        self.errors.append((decorator.lineno,
                            f"Use @{self.route_decorator_name or 'rt'}() instead of @app.route()"))
                            
        # Check decorator ordering
        if sse_idx is not None and rt_idx is not None and sse_idx < rt_idx:
            self.errors.append((node.decorator_list[sse_idx].lineno,
                "@sse should come after route decorator"))
                
        self.generic_visit(node)
        
    def visit_Call(self, node):
        """Track component usage and check patterns"""
        if isinstance(node.func, ast.Name):
            name = node.func.id
            # Check for capitalized components
            if name in ['Div', 'Button', 'P', 'H1', 'H2', 'H3', 'Script', 'Style', 
                       'Form', 'Input', 'Label', 'Span', 'A', 'Img', 'Link']:
                self.used_components.add(name)
                
            # Check for lowercase HTML functions
            elif name in ['div', 'button', 'p', 'h1', 'h2', 'h3', 'script', 'style',
                         'form', 'input', 'label', 'span', 'a', 'img', 'link']:
                self.errors.append((node.lineno,
                    f"Use capitalized {name.capitalize()}() instead of {name}()"))
                    
        self.generic_visit(node)
        
    def validate(self, tree):
        """Run validation and check for missing imports"""
        self.visit(tree)
        
        # Check basic requirements
        if not self.has_star_import and 'star_app' not in self.imports:
            self.errors.append((0, "Missing import: from starhtml import star_app"))
            
        if not self.has_star_app:
            self.warnings.append((0, "No star_app() initialization found"))
            
        # Check for potentially missing imports
        special_components = {'Script', 'Style', 'Form', 'Hidden', 'CheckboxX'}
        for comp in self.used_components & special_components:
            if not self.has_star_import and comp not in self.imports:
                self.warnings.append((0, f"Potentially missing import for {comp}"))
                
        return self.errors, self.warnings

def validate_file(filepath: Path) -> Tuple[List[str], List[str]]:
    """Validate a single Python file"""
    # Skip test files that don't need star_app
    if filepath.name.startswith('test_') and not 'star_app' in filepath.read_text():
        return [], []
        
    try:
        with open(filepath, 'r') as f:
            content = f.read()
            
        # Skip files that are clearly not StarHTML apps
        if '__name__ == "__main__"' not in content and 'serve(' not in content:
            return [], []
            
        tree = ast.parse(content, filename=str(filepath))
            
        validator = StarHTMLValidator(str(filepath))
        errors, warnings = validator.validate(tree)
        
        error_msgs = [f"{filepath}:{line}: ERROR: {msg}" for line, msg in errors]
        warning_msgs = [f"{filepath}:{line}: WARNING: {msg}" for line, msg in warnings]
        
        return error_msgs, warning_msgs
        
    except SyntaxError as e:
        return [f"{filepath}:{e.lineno}: SYNTAX ERROR: {e.msg}"], []
    except Exception as e:
        return [f"{filepath}: ERROR: {str(e)}"], []

def main():
    """Run validator on specified files or directories"""
    if len(sys.argv) < 2:
        print("Usage: starhtml-validate <file_or_directory> ...")
        sys.exit(1)
        
    all_errors = []
    all_warnings = []
    
    for arg in sys.argv[1:]:
        path = Path(arg)
        if path.is_file() and path.suffix == '.py':
            errors, warnings = validate_file(path)
            all_errors.extend(errors)
            all_warnings.extend(warnings)
        elif path.is_dir():
            for py_file in path.rglob('*.py'):
                # Skip hidden directories and __pycache__
                if not any(part.startswith('.') or part == '__pycache__' for part in py_file.parts):
                    errors, warnings = validate_file(py_file)
                    all_errors.extend(errors)
                    all_warnings.extend(warnings)
                    
    # Print results
    for warning in all_warnings:
        print(warning)
    for error in all_errors:
        print(error)
        
    if all_errors:
        sys.exit(1)
    else:
        print(f"✓ Validated {len(sys.argv)-1} paths with {len(all_warnings)} warnings")

if __name__ == "__main__":
    main()