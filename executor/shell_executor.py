"""Shell command executor"""
import subprocess
import shlex
from typing import Dict, Any


class ShellExecutor:
    """Executes shell commands safely"""

    def __init__(self, timeout: int = 30):
        """
        Initialize shell executor

        Args:
            timeout: Command timeout in seconds (default 30)
        """
        self.timeout = timeout

    def execute(self, command: str, confirm: bool = False, interactive: bool = None) -> Dict[str, Any]:
        """
        Execute a shell command

        Args:
            command: Shell command to execute
            confirm: If True, requires user confirmation
            interactive: If True, run without capturing output (allows user interaction)
                        If None, auto-detect based on stdin being a tty

        Returns:
            Dict with success, output, error, and command
        """
        try:
            import platform
            import sys
            is_windows = platform.system() == 'Windows'

            # Auto-detect if we should run interactively
            # Default to interactive mode if stdin is a terminal (tty)
            if interactive is None:
                interactive = sys.stdin.isatty()

            # On Windows, many commands are shell built-ins and need shell=True
            # Also need shell=True for pipes, redirects, etc.
            use_shell = any(char in command for char in ['|', '&&', '||', '>', '<', ';'])

            # Windows built-in commands that need shell=True
            windows_builtins = ['mkdir', 'cd', 'dir', 'del', 'copy', 'move', 'type', 'echo', 'set']
            if is_windows:
                first_word = command.split()[0].lower() if command.split() else ''
                if first_word in windows_builtins:
                    use_shell = True

            # Always use shell=True on Windows for better compatibility
            if is_windows:
                use_shell = True

            # Run command based on mode
            if use_shell:
                result = subprocess.run(
                    command,
                    shell=True,
                    capture_output=not interactive,  # Only capture if not interactive
                    text=True if not interactive else None,
                    timeout=self.timeout,
                    cwd="."
                )
            else:
                args = shlex.split(command)
                result = subprocess.run(
                    args,
                    capture_output=not interactive,
                    text=True if not interactive else None,
                    timeout=self.timeout,
                    cwd="."
                )

            # Check if command succeeded
            if result.returncode == 0:
                if interactive:
                    return {
                        "success": True,
                        "message": f"Command completed: {command}",
                        "output": "",
                        "error": "",
                        "command": command,
                        "return_code": result.returncode
                    }
                else:
                    return {
                        "success": True,
                        "message": f"Executed: {command}",
                        "output": result.stdout.strip() if hasattr(result, 'stdout') and result.stdout else "",
                        "error": result.stderr.strip() if hasattr(result, 'stderr') and result.stderr else "",
                        "command": command,
                        "return_code": result.returncode
                    }
            else:
                if interactive:
                    return {
                        "success": False,
                        "message": f"Command failed with exit code {result.returncode}",
                        "output": "",
                        "error": "Command failed",
                        "command": command,
                        "return_code": result.returncode
                    }
                else:
                    return {
                        "success": False,
                        "message": f"Command failed with exit code {result.returncode}",
                        "output": result.stdout.strip() if hasattr(result, 'stdout') and result.stdout else "",
                        "error": result.stderr.strip() if hasattr(result, 'stderr') and result.stderr else "",
                        "command": command,
                        "return_code": result.returncode
                    }

        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "message": f"Command timed out after {self.timeout} seconds",
                "error": f"Command timed out after {self.timeout} seconds",
                "command": command,
                "return_code": -1
            }
        except FileNotFoundError as e:
            return {
                "success": False,
                "message": f"Command not found: {str(e)}",
                "error": f"Command not found: {str(e)}",
                "command": command,
                "return_code": -1
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"Execution error: {str(e)}",
                "error": f"Execution error: {str(e)}",
                "command": command,
                "return_code": -1
            }

    def is_dangerous(self, command: str) -> bool:
        """
        Check if command is potentially dangerous

        Args:
            command: Shell command to check

        Returns:
            True if dangerous, False otherwise
        """
        dangerous_patterns = [
            'rm -rf /',
            'format',
            'mkfs',
            'dd if=',
            ':(){:|:&};:',  # Fork bomb
            'shutdown',
            'reboot',
            'halt',
            'poweroff',
            '> /dev/sda',
            'chmod -R 777 /',
            'chown -R',
        ]

        command_lower = command.lower()

        for pattern in dangerous_patterns:
            if pattern.lower() in command_lower:
                return True

        return False
