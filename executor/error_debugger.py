"""Error debugger for analyzing and fixing errors"""
import os
import re
from typing import Dict, Any, Optional, List


class ErrorDebugger:
    """Debug errors and suggest fixes"""

    def __init__(self, inference_engine=None):
        """
        Initialize error debugger

        Args:
            inference_engine: Ollama inference engine for error analysis
        """
        self.inference_engine = inference_engine

    def debug(self, error_message: str, file_path: Optional[str] = None,
              line: Optional[int] = None, code_context: Optional[str] = None) -> Dict[str, Any]:
        """
        Debug an error and suggest fixes

        Args:
            error_message: The error message or exception
            file_path: Optional file where error occurred
            line: Optional line number
            code_context: Optional code context around error

        Returns:
            Dict with debugging analysis and fix suggestions
        """
        try:
            # Parse error message to extract useful info
            error_info = self._parse_error_message(error_message)

            # Get code context if file and line provided
            if file_path and line and not code_context:
                code_context = self._get_code_context(file_path, line)

            # If no LLM, provide basic debugging
            if not self.inference_engine:
                return self._basic_debug(error_message, error_info, code_context)

            # Use LLM for intelligent debugging
            debug_prompt = self._build_debug_prompt(
                error_message, error_info, file_path, line, code_context
            )

            # Generate debugging analysis
            debug_result = self.inference_engine.generate_response(debug_prompt)

            return {
                "success": True,
                "error_message": error_message,
                "error_type": error_info.get('type', 'Unknown'),
                "file": file_path,
                "line": line,
                "code_context": code_context,
                "analysis": debug_result,
                "parsed_info": error_info
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"Debugging failed: {str(e)}"
            }

    def _parse_error_message(self, error_message: str) -> Dict[str, Any]:
        """Parse error message to extract key information"""
        info = {
            'type': 'Unknown',
            'description': error_message,
            'file': None,
            'line': None,
            'severity': 'error'
        }

        # Common error patterns
        patterns = {
            # Python errors
            'python': {
                'type': r'(\w+Error|\w+Exception):',
                'file_line': r'File "([^"]+)", line (\d+)',
                'syntax': r'SyntaxError: (.+)',
                'name': r'NameError: name \'(\w+)\' is not defined',
                'import': r'ImportError: (.+)|ModuleNotFoundError: (.+)',
                'attribute': r'AttributeError: (.+)',
                'type_error': r'TypeError: (.+)',
                'value': r'ValueError: (.+)',
                'index': r'IndexError: (.+)',
                'key': r'KeyError: (.+)',
            },
            # JavaScript errors
            'javascript': {
                'type': r'(\w+Error):',
                'reference': r'ReferenceError: (.+)',
                'syntax': r'SyntaxError: (.+)',
                'type_error': r'TypeError: (.+)',
            },
            # Java errors
            'java': {
                'type': r'(\w+Exception):',
                'file_line': r'at .+ \((.+):(\d+)\)',
                'null_pointer': r'NullPointerException',
            }
        }

        # Try to match error type
        for lang, lang_patterns in patterns.items():
            if 'type' in lang_patterns:
                match = re.search(lang_patterns['type'], error_message)
                if match:
                    info['type'] = match.group(1)
                    info['language'] = lang
                    break

        # Try to extract file and line
        for lang, lang_patterns in patterns.items():
            if 'file_line' in lang_patterns:
                match = re.search(lang_patterns['file_line'], error_message)
                if match:
                    info['file'] = match.group(1)
                    info['line'] = int(match.group(2))
                    break

        # Categorize error severity
        critical_types = ['SyntaxError', 'ImportError', 'ModuleNotFoundError', 'IndentationError']
        if info['type'] in critical_types:
            info['severity'] = 'critical'

        return info

    def _get_code_context(self, file_path: str, line: int, context_lines: int = 5) -> str:
        """Get code context around a specific line"""
        try:
            if not os.path.exists(file_path):
                return None

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

    def _build_debug_prompt(self, error_message: str, error_info: Dict[str, Any],
                             file_path: Optional[str], line: Optional[int],
                             code_context: Optional[str]) -> str:
        """Build prompt for error debugging"""

        prompt = f"""You are an expert debugging assistant. Analyze this error and provide a fix.

Error Type: {error_info.get('type', 'Unknown')}
Severity: {error_info.get('severity', 'error')}

Error Message:
{error_message}
"""

        if file_path:
            prompt += f"\nFile: {file_path}"
        if line:
            prompt += f"\nLine: {line}"

        if code_context:
            prompt += f"\n\nCode Context:\n{code_context}"

        prompt += """

Provide a comprehensive debugging analysis:

1. **Root Cause**: What's causing this error?
2. **Explanation**: Why is this happening?
3. **Fix**: How to fix it (provide specific code if possible)
4. **Prevention**: How to prevent this in the future

Be specific and actionable. If you can provide code fixes, show the exact changes needed.

Analysis:"""

        return prompt

    def _basic_debug(self, error_message: str, error_info: Dict[str, Any],
                     code_context: Optional[str]) -> Dict[str, Any]:
        """Provide basic debugging without LLM"""

        error_type = error_info.get('type', 'Unknown')

        # Common error fixes
        common_fixes = {
            'NameError': "Variable is not defined. Check:\n1. Variable spelling\n2. Variable scope\n3. Import statements",
            'ImportError': "Module not found. Try:\n1. pip install <module>\n2. Check module name spelling\n3. Verify module is installed",
            'ModuleNotFoundError': "Module not found. Try:\n1. pip install <module>\n2. Check PYTHONPATH\n3. Verify package installation",
            'SyntaxError': "Syntax error. Check:\n1. Missing colons, brackets, or quotes\n2. Indentation\n3. Invalid syntax",
            'TypeError': "Type mismatch. Check:\n1. Function argument types\n2. Operation between incompatible types\n3. None values",
            'ValueError': "Invalid value. Check:\n1. Value format\n2. Value range\n3. Type conversion",
            'IndexError': "Index out of range. Check:\n1. List/array length\n2. Index bounds\n3. Empty collections",
            'KeyError': "Key not found. Check:\n1. Dictionary key existence\n2. Key spelling\n3. Use .get() method",
            'AttributeError': "Attribute not found. Check:\n1. Object type\n2. Attribute spelling\n3. Object initialization",
            'IndentationError': "Indentation issue. Check:\n1. Consistent spaces/tabs\n2. Indentation level\n3. Block structure",
        }

        suggestion = common_fixes.get(error_type, "No specific suggestion available. Review error message carefully.")

        analysis = f"Error Type: {error_type}\n\n"
        analysis += f"Common Fix:\n{suggestion}\n\n"

        if code_context:
            analysis += "Code Context:\n" + code_context

        return {
            "success": True,
            "error_type": error_type,
            "analysis": analysis,
            "note": "LLM not available - showing basic debugging only",
            "parsed_info": error_info
        }

    def suggest_fix(self, problem: str, file_path: str, context: Optional[str] = None) -> Dict[str, Any]:
        """Suggest a fix for a specific problem"""
        try:
            if not os.path.exists(file_path):
                return {
                    "success": False,
                    "error": f"File not found: {file_path}"
                }

            # Read file if no context provided
            if not context:
                with open(file_path, 'r', encoding='utf-8') as f:
                    context = f.read()

            # Detect language
            language = self._detect_language(file_path)

            if not self.inference_engine:
                return {
                    "success": False,
                    "error": "LLM required for fix suggestions"
                }

            prompt = f"""You are an expert {language} developer. Suggest a fix for this problem.

File: {file_path}
Problem: {problem}

Current Code:
```{language.lower()}
{context}
```

Provide:
1. The issue/problem explained
2. The fix (show exact code changes)
3. Why this fix works

Fix Suggestion:"""

            fix_suggestion = self.inference_engine.generate_response(prompt)

            return {
                "success": True,
                "file": file_path,
                "problem": problem,
                "language": language,
                "suggestion": fix_suggestion
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"Fix suggestion failed: {str(e)}"
            }

    def _detect_language(self, file_path: str) -> str:
        """Detect programming language from file extension"""
        ext_map = {
            '.py': 'Python',
            '.js': 'JavaScript',
            '.ts': 'TypeScript',
            '.java': 'Java',
            '.cpp': 'C++',
            '.c': 'C',
            '.go': 'Go',
            '.rs': 'Rust',
            '.rb': 'Ruby',
            '.php': 'PHP',
        }
        ext = os.path.splitext(file_path)[1].lower()
        return ext_map.get(ext, 'Unknown')
