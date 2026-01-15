"""Code parser utilities with AST support for Python"""
import ast
import os
from typing import Dict, Any, List, Optional


class CodeParser:
    """Parse and analyze code structure"""

    @staticmethod
    def parse_python(file_path: str) -> Dict[str, Any]:
        """
        Parse Python file and extract structure

        Args:
            file_path: Path to Python file

        Returns:
            Dict with code structure information
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                code = f.read()

            tree = ast.parse(code, filename=file_path)

            structure = {
                "success": True,
                "file": file_path,
                "language": "Python",
                "functions": [],
                "classes": [],
                "imports": [],
                "variables": [],
                "docstring": ast.get_docstring(tree),
                "total_lines": len(code.split('\n'))
            }

            # Extract functions
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    func_info = {
                        "name": node.name,
                        "line": node.lineno,
                        "args": [arg.arg for arg in node.args.args],
                        "docstring": ast.get_docstring(node),
                        "is_async": isinstance(node, ast.AsyncFunctionDef),
                        "decorators": [CodeParser._get_decorator_name(dec) for dec in node.decorator_list]
                    }
                    structure["functions"].append(func_info)

                elif isinstance(node, ast.ClassDef):
                    class_info = {
                        "name": node.name,
                        "line": node.lineno,
                        "methods": [],
                        "docstring": ast.get_docstring(node),
                        "bases": [CodeParser._get_name(base) for base in node.bases]
                    }

                    # Extract methods
                    for item in node.body:
                        if isinstance(item, ast.FunctionDef):
                            class_info["methods"].append({
                                "name": item.name,
                                "line": item.lineno,
                                "args": [arg.arg for arg in item.args.args]
                            })

                    structure["classes"].append(class_info)

                elif isinstance(node, ast.Import):
                    for alias in node.names:
                        structure["imports"].append({
                            "type": "import",
                            "module": alias.name,
                            "alias": alias.asname,
                            "line": node.lineno
                        })

                elif isinstance(node, ast.ImportFrom):
                    for alias in node.names:
                        structure["imports"].append({
                            "type": "from_import",
                            "module": node.module,
                            "name": alias.name,
                            "alias": alias.asname,
                            "line": node.lineno
                        })

            return structure

        except SyntaxError as e:
            return {
                "success": False,
                "error": "Syntax error in Python code",
                "details": str(e),
                "line": e.lineno,
                "offset": e.offset
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to parse Python file: {str(e)}"
            }

    @staticmethod
    def _get_name(node) -> str:
        """Get name from AST node"""
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            return f"{CodeParser._get_name(node.value)}.{node.attr}"
        else:
            return str(node)

    @staticmethod
    def _get_decorator_name(node) -> str:
        """Get decorator name from AST node"""
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Call):
            return CodeParser._get_decorator_name(node.func)
        elif isinstance(node, ast.Attribute):
            return node.attr
        return str(node)

    @staticmethod
    def find_function(file_path: str, function_name: str) -> Optional[Dict[str, Any]]:
        """Find a specific function in a Python file"""
        structure = CodeParser.parse_python(file_path)
        if not structure.get("success"):
            return None

        for func in structure.get("functions", []):
            if func["name"] == function_name:
                return func

        # Check in classes
        for cls in structure.get("classes", []):
            for method in cls.get("methods", []):
                if method["name"] == function_name:
                    return {**method, "class": cls["name"]}

        return None

    @staticmethod
    def find_class(file_path: str, class_name: str) -> Optional[Dict[str, Any]]:
        """Find a specific class in a Python file"""
        structure = CodeParser.parse_python(file_path)
        if not structure.get("success"):
            return None

        for cls in structure.get("classes", []):
            if cls["name"] == class_name:
                return cls

        return None

    @staticmethod
    def get_code_at_line(file_path: str, line: int, context_lines: int = 5) -> Optional[str]:
        """Get code at specific line with context"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()

            start = max(0, line - context_lines - 1)
            end = min(len(lines), line + context_lines)

            context = ""
            for i in range(start, end):
                marker = ">>> " if i == line - 1 else "    "
                context += f"{marker}{i + 1}: {lines[i]}"

            return context

        except Exception:
            return None

    @staticmethod
    def analyze_complexity(file_path: str) -> Dict[str, Any]:
        """Analyze code complexity (basic metrics)"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                code = f.read()

            tree = ast.parse(code)

            metrics = {
                "success": True,
                "file": file_path,
                "total_lines": len(code.split('\n')),
                "code_lines": 0,
                "comment_lines": 0,
                "blank_lines": 0,
                "function_count": 0,
                "class_count": 0,
                "max_nesting_depth": 0,
                "complexity_score": 0
            }

            # Count lines
            lines = code.split('\n')
            for line in lines:
                stripped = line.strip()
                if not stripped:
                    metrics["blank_lines"] += 1
                elif stripped.startswith('#'):
                    metrics["comment_lines"] += 1
                else:
                    metrics["code_lines"] += 1

            # Count functions and classes
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    metrics["function_count"] += 1
                    # Simple complexity: count control flow statements
                    complexity = CodeParser._calculate_complexity(node)
                    metrics["complexity_score"] += complexity

                elif isinstance(node, ast.ClassDef):
                    metrics["class_count"] += 1

            # Calculate average complexity
            if metrics["function_count"] > 0:
                metrics["avg_function_complexity"] = metrics["complexity_score"] / metrics["function_count"]
            else:
                metrics["avg_function_complexity"] = 0

            return metrics

        except Exception as e:
            return {
                "success": False,
                "error": f"Complexity analysis failed: {str(e)}"
            }

    @staticmethod
    def _calculate_complexity(node) -> int:
        """Calculate cyclomatic complexity for a function"""
        complexity = 1  # Base complexity

        for child in ast.walk(node):
            # Add complexity for control flow statements
            if isinstance(child, (ast.If, ast.While, ast.For, ast.ExceptHandler)):
                complexity += 1
            elif isinstance(child, ast.BoolOp):
                complexity += len(child.values) - 1

        return complexity

    @staticmethod
    def extract_dependencies(file_path: str) -> Dict[str, Any]:
        """Extract all dependencies from a Python file"""
        structure = CodeParser.parse_python(file_path)

        if not structure.get("success"):
            return structure

        dependencies = {
            "success": True,
            "file": file_path,
            "standard_library": [],
            "third_party": [],
            "local": []
        }

        # Common standard library modules
        stdlib_modules = {
            'os', 'sys', 'json', 'datetime', 'time', 're', 'math',
            'random', 'collections', 'itertools', 'functools', 'typing',
            'pathlib', 'subprocess', 'shutil', 'tempfile', 'glob',
            'argparse', 'logging', 'unittest', 'asyncio', 'threading'
        }

        for imp in structure.get("imports", []):
            module = imp.get("module", "").split('.')[0]

            if module in stdlib_modules:
                dependencies["standard_library"].append(imp)
            elif module.startswith('.'):
                dependencies["local"].append(imp)
            else:
                dependencies["third_party"].append(imp)

        return dependencies

    @staticmethod
    def detect_language(file_path: str) -> str:
        """Detect programming language from file extension"""
        ext_map = {
            '.py': 'Python',
            '.js': 'JavaScript',
            '.ts': 'TypeScript',
            '.jsx': 'React/JSX',
            '.tsx': 'React/TSX',
            '.java': 'Java',
            '.cpp': 'C++',
            '.c': 'C',
            '.cs': 'C#',
            '.go': 'Go',
            '.rs': 'Rust',
            '.rb': 'Ruby',
            '.php': 'PHP',
        }

        ext = os.path.splitext(file_path)[1].lower()
        return ext_map.get(ext, 'Unknown')
