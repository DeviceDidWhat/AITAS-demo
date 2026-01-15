"""Intelligent test runner with result analysis"""
import os
import subprocess
import re
from typing import Dict, Any, Optional, List


class TestRunner:
    """Run tests intelligently and analyze results"""

    def __init__(self, inference_engine=None):
        """
        Initialize test runner

        Args:
            inference_engine: Ollama inference engine for test analysis
        """
        self.inference_engine = inference_engine

    def run_tests(self, test_framework: Optional[str] = None,
                  target: Optional[str] = None, verbose: bool = True) -> Dict[str, Any]:
        """
        Run tests intelligently

        Args:
            test_framework: pytest, jest, unittest, etc. (auto-detect if None)
            target: Specific test file or function
            verbose: Show detailed output

        Returns:
            Dict with test results and analysis
        """
        try:
            # Auto-detect test framework if not specified
            if not test_framework:
                test_framework = self._detect_test_framework()

            if not test_framework:
                return {
                    "success": False,
                    "error": "Could not detect test framework. Please specify one."
                }

            # Build test command
            command = self._build_test_command(test_framework, target, verbose)

            # Execute tests
            print(f"\n[DEBUG] Running test command: {command}")
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )

            # Parse test results
            test_results = self._parse_test_output(
                result.stdout, result.stderr, test_framework
            )

            # Analyze failures if LLM available
            if self.inference_engine and not test_results['all_passed']:
                analysis = self._analyze_failures(test_results, test_framework)
                test_results['failure_analysis'] = analysis

            test_results.update({
                "success": result.returncode == 0,
                "command": command,
                "test_framework": test_framework,
                "exit_code": result.returncode
            })

            return test_results

        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "error": "Test execution timeout (5 minutes)"
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Test execution failed: {str(e)}"
            }

    def _detect_test_framework(self) -> Optional[str]:
        """Auto-detect test framework from project files"""

        # Check for common test framework indicators
        indicators = {
            'pytest': ['pytest.ini', 'pyproject.toml', 'setup.cfg', 'tests/test_*.py'],
            'unittest': ['tests/test_*.py', 'test_*.py'],
            'jest': ['jest.config.js', 'jest.config.ts', 'package.json'],
            'mocha': ['mocha.opts', '.mocharc.json'],
            'junit': ['pom.xml', 'build.gradle'],
            'rspec': ['spec/', '.rspec'],
            'go test': ['*_test.go'],
        }

        for framework, files in indicators.items():
            for pattern in files:
                # Check if file/directory exists
                if '*' in pattern:
                    # Use glob pattern check
                    import glob
                    if glob.glob(pattern):
                        return framework
                else:
                    if os.path.exists(pattern):
                        return framework

        # Check package.json for test scripts
        if os.path.exists('package.json'):
            try:
                import json
                with open('package.json', 'r') as f:
                    package = json.load(f)
                    test_script = package.get('scripts', {}).get('test', '')
                    if 'jest' in test_script:
                        return 'jest'
                    elif 'mocha' in test_script:
                        return 'mocha'
            except:
                pass

        return None

    def _build_test_command(self, framework: str, target: Optional[str], verbose: bool) -> str:
        """Build test command based on framework"""

        commands = {
            'pytest': f"pytest {'-v' if verbose else ''} {target or ''}",
            'unittest': f"python -m unittest {'-v' if verbose else ''} {target or 'discover'}",
            'jest': f"npm test -- {target or ''} {'--verbose' if verbose else ''}",
            'mocha': f"mocha {target or 'test/**/*.js'} {'--reporter spec' if verbose else ''}",
            'go test': f"go test {'-v' if verbose else ''} {target or './...'}",
            'cargo test': f"cargo test {target or ''} {'--' if verbose else ''}",
            'npm test': f"npm test {target or ''}",
            'yarn test': f"yarn test {target or ''}",
        }

        return commands.get(framework, f"{framework} {target or ''}")

    def _parse_test_output(self, stdout: str, stderr: str, framework: str) -> Dict[str, Any]:
        """Parse test output to extract results"""

        combined_output = stdout + stderr

        results = {
            "total_tests": 0,
            "passed": 0,
            "failed": 0,
            "skipped": 0,
            "errors": 0,
            "all_passed": False,
            "failures": [],
            "output": stdout,
            "error_output": stderr
        }

        # Framework-specific parsing
        if framework == 'pytest':
            results.update(self._parse_pytest(combined_output))
        elif framework == 'jest':
            results.update(self._parse_jest(combined_output))
        elif framework == 'unittest':
            results.update(self._parse_unittest(combined_output))
        elif framework == 'go test':
            results.update(self._parse_go_test(combined_output))

        results['all_passed'] = (results['failed'] == 0 and results['errors'] == 0)

        return results

    def _parse_pytest(self, output: str) -> Dict[str, Any]:
        """Parse pytest output"""
        results = {}

        # Match pattern: "5 passed, 2 failed, 1 skipped in 1.23s"
        summary = re.search(
            r'(\d+)\s+passed(?:,\s+(\d+)\s+failed)?(?:,\s+(\d+)\s+skipped)?',
            output
        )

        if summary:
            results['passed'] = int(summary.group(1))
            results['failed'] = int(summary.group(2) or 0)
            results['skipped'] = int(summary.group(3) or 0)
            results['total_tests'] = results['passed'] + results['failed'] + results['skipped']

        # Extract failure details
        failures = re.findall(r'FAILED (.*?) - (.*?)(?:\n|$)', output)
        results['failures'] = [
            {"test": test, "reason": reason} for test, reason in failures
        ]

        return results

    def _parse_jest(self, output: str) -> Dict[str, Any]:
        """Parse jest output"""
        results = {}

        # Match pattern: "Tests: 2 failed, 5 passed, 7 total"
        summary = re.search(
            r'Tests:\s+(?:(\d+)\s+failed,\s+)?(\d+)\s+passed,\s+(\d+)\s+total',
            output
        )

        if summary:
            results['failed'] = int(summary.group(1) or 0)
            results['passed'] = int(summary.group(2))
            results['total_tests'] = int(summary.group(3))

        return results

    def _parse_unittest(self, output: str) -> Dict[str, Any]:
        """Parse unittest output"""
        results = {}

        # Match pattern: "Ran 10 tests in 0.123s" and "FAILED (failures=2)"
        ran = re.search(r'Ran (\d+) test', output)
        if ran:
            results['total_tests'] = int(ran.group(1))

        failed = re.search(r'FAILED \(failures=(\d+)\)', output)
        if failed:
            results['failed'] = int(failed.group(1))
            results['passed'] = results['total_tests'] - results['failed']
        elif 'OK' in output:
            results['passed'] = results.get('total_tests', 0)
            results['failed'] = 0

        return results

    def _parse_go_test(self, output: str) -> Dict[str, Any]:
        """Parse go test output"""
        results = {}

        # Count PASS and FAIL lines
        passed = len(re.findall(r'^PASS', output, re.MULTILINE))
        failed = len(re.findall(r'^FAIL', output, re.MULTILINE))

        results['passed'] = passed
        results['failed'] = failed
        results['total_tests'] = passed + failed

        return results

    def _analyze_failures(self, test_results: Dict[str, Any], framework: str) -> str:
        """Analyze test failures using LLM"""
        if not self.inference_engine:
            return "LLM not available for failure analysis"

        failures = test_results.get('failures', [])
        if not failures:
            return "No failures to analyze"

        # Build prompt for failure analysis
        prompt = f"""You are a testing expert. Analyze these test failures and suggest fixes.

Test Framework: {framework}
Total Tests: {test_results.get('total_tests', 0)}
Passed: {test_results.get('passed', 0)}
Failed: {test_results.get('failed', 0)}

Failed Tests:
"""

        for i, failure in enumerate(failures[:5], 1):  # Limit to 5 failures
            prompt += f"\n{i}. Test: {failure.get('test', 'Unknown')}\n"
            prompt += f"   Reason: {failure.get('reason', 'Unknown')}\n"

        if test_results.get('error_output'):
            prompt += f"\nError Output:\n{test_results['error_output'][:1000]}\n"

        prompt += """
For each failure, provide:
1. Root cause
2. Suggested fix
3. How to prevent in the future

Analysis:"""

        try:
            analysis = self.inference_engine.generate_response(prompt)
            return analysis
        except Exception as e:
            return f"Analysis failed: {str(e)}"
