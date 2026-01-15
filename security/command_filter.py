"""Security filter for dangerous commands"""
from typing import List, Dict, Any


class CommandFilter:
    """Filters and validates commands for security"""

    def __init__(self, allowed_operations: List[str] = None, dangerous_patterns: List[str] = None):
        self.allowed_operations = allowed_operations or ["mkdir", "write", "read", "list", "shell"]
        self.dangerous_patterns = dangerous_patterns or [
            "rm", "del", "delete", "format", "shutdown", "reboot",
            "..", "/etc", "/sys", "/root", "C:\\Windows\\System32"
        ]

        # Dangerous shell command patterns
        self.dangerous_shell_patterns = [
            "rm -rf /",
            "format",
            "mkfs",
            "dd if=",
            ":(){:|:&};:",  # Fork bomb
            "shutdown",
            "reboot",
            "halt",
            "poweroff",
            "> /dev/sda",
            "chmod -R 777 /",
            "chown -R",
        ]

    def is_safe_action(self, action: str) -> bool:
        """Check if action is allowed"""
        return action in self.allowed_operations

    def is_safe_path(self, path: str) -> bool:
        """Check if path contains dangerous patterns"""
        path_lower = path.lower()

        for pattern in self.dangerous_patterns:
            if pattern.lower() in path_lower:
                return False

        return True

    def validate_command(self, command: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate a command for security
        Returns: Dict with 'safe' boolean and optional 'reason'
        """
        action = command.get("action", "")

        # Check if action is allowed
        if not self.is_safe_action(action):
            return {
                "safe": False,
                "reason": f"Action '{action}' is not allowed"
            }

        # Check paths for dangerous patterns
        if action == "mkdir":
            target = command.get("target", "")
            if not self.is_safe_path(target):
                return {
                    "safe": False,
                    "reason": f"Target path contains dangerous pattern: {target}"
                }

        elif action in ["write", "read"]:
            file_path = command.get("file", "")
            if not self.is_safe_path(file_path):
                return {
                    "safe": False,
                    "reason": f"File path contains dangerous pattern: {file_path}"
                }

        elif action == "list":
            target = command.get("target", ".")
            if not self.is_safe_path(target):
                return {
                    "safe": False,
                    "reason": f"Target path contains dangerous pattern: {target}"
                }

        elif action == "shell":
            # Check for dangerous shell commands
            shell_command = command.get("command", "")
            if self.is_dangerous_shell(shell_command):
                return {
                    "safe": False,
                    "reason": f"Dangerous shell command detected: {shell_command}",
                    "requires_confirmation": True
                }

        return {"safe": True}

    def is_dangerous_shell(self, command: str) -> bool:
        """Check if shell command is dangerous"""
        command_lower = command.lower()

        for pattern in self.dangerous_shell_patterns:
            if pattern.lower() in command_lower:
                return True

        return False
