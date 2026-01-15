"""Extract and validate command intent from model output"""
import json
from typing import Dict, Any, Union
from .schemas import CommandAction, MkdirCommand, WriteCommand, ReadCommand, ListCommand, ShellCommand


class IntentExtractor:
    """Extracts structured command intent from JSON responses"""

    def __init__(self):
        self.supported_actions = ["mkdir", "write", "read", "list", "shell"]

    def extract(self, json_string: str) -> Union[MkdirCommand, WriteCommand, ReadCommand, ListCommand, ShellCommand]:
        """
        Extract and validate command from JSON string
        Returns: Validated command model
        Raises: ValueError if JSON is invalid or action not supported
        """
        try:
            # Parse JSON
            data = json.loads(json_string)

            # Validate action exists
            if "action" not in data:
                raise ValueError("Missing 'action' field in JSON")

            action = data["action"]

            # Check if action is supported
            if action not in self.supported_actions:
                raise ValueError(f"Unsupported action: {action}")

            # Parse to appropriate command model
            command = CommandAction.parse_command(data)
            return command

        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON: {str(e)}")
        except Exception as e:
            raise ValueError(f"Failed to extract intent: {str(e)}")

    def to_dict(self, command: Union[MkdirCommand, WriteCommand, ReadCommand, ListCommand, ShellCommand]) -> Dict[str, Any]:
        """Convert command model back to dict"""
        return command.model_dump()
