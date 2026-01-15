"""Code analyzer using Ollama for intelligent code analysis"""
import os
from typing import Dict, Any, Optional


class CodeAnalyzer:
    """Analyze code for bugs, improvements, and explanations"""

    def __init__(self, inference_engine=None):
        """
        Initialize code analyzer

        Args:
            inference_engine: Ollama inference engine for code analysis
        """
        self.inference_engine = inference_engine

    def analyze(self, file_path: str, task: str) -> Dict[str, Any]:
        """
        Analyze code file based on task

        Args:
            file_path: Path to file to analyze
            task: What to analyze (find bugs, explain logic, suggest improvements, review code)

        Returns:
            Dict with success status and analysis result
        """
        try:
            # Check if file exists
            if not os.path.exists(file_path):
                return {
                    "success": False,
                    "error": f"File not found: {file_path}"
                }

            # Read file content
            with open(file_path, 'r', encoding='utf-8') as f:
                code_content = f.read()

            if not code_content.strip():
                return {
                    "success": False,
                    "error": f"File is empty: {file_path}"
                }

            # Detect language from file extension
            language = self._detect_language(file_path)

            # If no LLM available, provide basic analysis
            if not self.inference_engine:
                return self._basic_analysis(code_content, language, task)

            # Use LLM for deep analysis
            analysis_prompt = self._build_analysis_prompt(code_content, language, task, file_path)

            # Generate analysis using Ollama
            analysis_result = self.inference_engine.generate_response(analysis_prompt)

            return {
                "success": True,
                "file": file_path,
                "language": language,
                "task": task,
                "analysis": analysis_result,
                "code_preview": code_content[:500] + ("..." if len(code_content) > 500 else "")
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"Analysis failed: {str(e)}"
            }

    def _detect_language(self, file_path: str) -> str:
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
            '.swift': 'Swift',
            '.kt': 'Kotlin',
            '.sh': 'Shell',
            '.html': 'HTML',
            '.css': 'CSS',
            '.sql': 'SQL',
            '.r': 'R',
            '.m': 'MATLAB',
            '.yaml': 'YAML',
            '.yml': 'YAML',
            '.json': 'JSON',
            '.xml': 'XML',
        }

        ext = os.path.splitext(file_path)[1].lower()
        return ext_map.get(ext, 'Unknown')

    def _build_analysis_prompt(self, code: str, language: str, task: str, file_path: str) -> str:
        """Build prompt for code analysis"""

        # Add line numbers to code for easier reference
        code_lines = code.split('\n')
        numbered_code = '\n'.join([f"{i+1:4d} | {line}" for i, line in enumerate(code_lines)])

        task_instructions = {
            'find bugs': f"""Analyze this {language} code and identify potential bugs, errors, or issues.

For EACH bug found, provide:
1. **Line number**: Exact line where the bug is
2. **Bug description**: What's wrong
3. **Impact**: What could go wrong
4. **Fix**: EXACT code change needed using diff format:

   - Remove this line (old code)
   + Add this line (new code)

Example format:
Bug at line 42: Variable 'x' is undefined
Fix:
   - result = process(x)
   + x = get_default_value()
   + result = process(x)""",

            'explain logic': f"""Explain the logic and flow of this {language} code in a clear, organized way:

1. **Purpose**: What this code does (1-2 sentences)
2. **Main Flow**: Step-by-step execution flow
3. **Key Components**: Important functions/classes and their roles
4. **Notable Patterns**: Any design patterns or techniques used

Keep explanations concise and focused.""",

            'suggest improvements': f"""Review this {language} code and provide SPECIFIC, ACTIONABLE improvements.

For EACH improvement, show EXACT code changes using diff format:

1. **What to improve**: Describe the issue
2. **Why**: Benefit of the change
3. **How**: Show exact diff

Format:
Improvement: Make function more readable
At lines 15-18:
   - if x > 0:
   -     return True
   - else:
   -     return False
   + return x > 0

Focus on: performance, readability, best practices, security.""",

            'review code': f"""Perform a comprehensive code review with SPECIFIC, ACTIONABLE feedback.

Structure your review as:

1. **Summary**: Overall quality (1-2 sentences)

2. **Issues Found**: List each issue with line numbers and EXACT fixes using diff format:
   Issue at line X: Description
   Fix:
   - old code
   + new code

3. **Strengths**: What's done well

4. **Recommendations**: Prioritized list of improvements

Use diff format (- for remove, + for add) for ALL code suggestions."""
        }

        instruction = task_instructions.get(task.lower(), task_instructions['review code'])

        prompt = f"""You are an expert {language} developer. Provide SPECIFIC, ACTIONABLE analysis with EXACT code changes.

File: {file_path}
Task: {task}

{instruction}

Code with line numbers:
```{language.lower()}
{numbered_code}
```

IMPORTANT:
- Reference exact line numbers
- Show EXACT code changes using diff format (- for remove, + for add)
- Don't give vague advice - show concrete code examples
- Be specific and actionable

Your analysis:"""

        return prompt

    def _basic_analysis(self, code: str, language: str, task: str) -> Dict[str, Any]:
        """Provide basic analysis without LLM"""
        lines = code.split('\n')
        total_lines = len(lines)
        non_empty_lines = len([line for line in lines if line.strip()])

        # Basic metrics
        analysis = f"Basic {language} Code Analysis:\n\n"
        analysis += f"Total Lines: {total_lines}\n"
        analysis += f"Non-empty Lines: {non_empty_lines}\n"
        analysis += f"Empty Lines: {total_lines - non_empty_lines}\n\n"

        # Task-specific basic analysis
        if 'bug' in task.lower():
            analysis += "Note: Deep bug analysis requires LLM. Basic check:\n"
            analysis += "- Check for common issues like undefined variables\n"
            analysis += "- Look for syntax errors\n"
            analysis += "- Review error handling\n"
        elif 'explain' in task.lower():
            analysis += "Note: Code explanation requires LLM for detailed analysis.\n"
            analysis += f"This {language} file has {total_lines} lines of code.\n"
        else:
            analysis += f"Note: Detailed {task} requires LLM.\n"
            analysis += "Basic suggestions:\n"
            analysis += "- Add comments for complex logic\n"
            analysis += "- Keep functions small and focused\n"
            analysis += "- Follow language-specific best practices\n"

        return {
            "success": True,
            "language": language,
            "task": task,
            "analysis": analysis,
            "note": "LLM not available - showing basic analysis only"
        }

    def explain_snippet(self, code_snippet: str, language: str) -> Dict[str, Any]:
        """Explain a specific code snippet"""
        try:
            if not self.inference_engine:
                return {
                    "success": False,
                    "error": "LLM required for code explanation"
                }

            prompt = f"""You are an expert {language} developer. Explain this code snippet clearly and concisely.

Language: {language}

Code:
```{language.lower()}
{code_snippet}
```

Provide:
1. What this code does
2. How it works
3. Any important details or gotchas

Explanation:"""

            explanation = self.inference_engine.generate_response(prompt)

            return {
                "success": True,
                "language": language,
                "code_snippet": code_snippet,
                "explanation": explanation
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"Explanation failed: {str(e)}"
            }
