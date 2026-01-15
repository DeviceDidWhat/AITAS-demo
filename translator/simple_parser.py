"""Simple rule-based parser for natural language commands"""
import re
import json
from typing import Dict, Any, Optional


class SimpleCommandParser:
    """
    Fast rule-based parser that converts natural language to JSON commands
    No ML model needed - instant responses!
    """

    def parse(self, user_input: str) -> Dict[str, Any]:
        """
        Parse natural language input to command JSON
        Returns: Dict with action and parameters
        """
        user_input = user_input.lower().strip()

        # Try to match mkdir patterns
        mkdir_result = self._parse_mkdir(user_input)
        if mkdir_result:
            return mkdir_result

        # Try to match write patterns
        write_result = self._parse_write(user_input)
        if write_result:
            return write_result

        # Try to match read patterns
        read_result = self._parse_read(user_input)
        if read_result:
            return read_result

        # Try to match list patterns
        list_result = self._parse_list(user_input)
        if list_result:
            return list_result

        # Default: couldn't parse
        raise ValueError(f"Could not understand command: {user_input}")

    def _parse_mkdir(self, text: str) -> Optional[Dict[str, Any]]:
        """Parse mkdir commands"""
        patterns = [
            r"(?:create|make|mkdir)\s+(?:a\s+)?(?:folder|directory|dir)?\s*(?:called|named)?\s+['\"]?(\w+)['\"]?",
            r"(?:new|add)\s+(?:folder|directory)\s+['\"]?(\w+)['\"]?",
        ]

        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                folder_name = match.group(1)
                return {
                    "action": "mkdir",
                    "target": folder_name
                }

        return None

    def _parse_write(self, text: str) -> Optional[Dict[str, Any]]:
        """Parse write file commands"""
        patterns = [
            r"(?:create|make|write)\s+(?:a\s+)?(?:file\s+)?['\"]?([a-zA-Z0-9_./\\-]+\.\w+)['\"]?(?:\s+(?:in|to)\s+([a-zA-Z0-9_./\\-]+))?(?:\s+with\s+(.+))?",
            r"(?:write|add)\s+['\"]?([a-zA-Z0-9_./\\-]+\.\w+)['\"]?(?:\s+with\s+(.+))?",
        ]

        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                filename = match.group(1)

                # Check if there's a folder specified
                if "in " in text or "to " in text:
                    folder_match = re.search(r"(?:in|to)\s+([a-zA-Z0-9_./\\-]+)", text)
                    if folder_match:
                        folder = folder_match.group(1)
                        filename = f"{folder}/{filename}"

                # Extract content if specified
                content = ""
                if "with " in text:
                    content_match = re.search(r"with\s+(.+)", text)
                    if content_match:
                        content = content_match.group(1).strip()

                # Default content based on file type
                if not content:
                    if filename.endswith(".md"):
                        content = f"# {filename.split('/')[-1].replace('.md', '')}\n\nProject documentation"
                    elif filename.endswith(".txt"):
                        content = "Sample text content"
                    else:
                        content = ""

                return {
                    "action": "write",
                    "file": filename,
                    "content": content
                }

        return None

    def _parse_read(self, text: str) -> Optional[Dict[str, Any]]:
        """Parse read file commands"""
        patterns = [
            r"(?:read|show|display|cat|view)\s+(?:file\s+)?['\"]?([a-zA-Z0-9_./\\-]+\.\w+)['\"]?",
            r"(?:what'?s?\s+in|contents?\s+of)\s+['\"]?([a-zA-Z0-9_./\\-]+\.\w+)['\"]?",
        ]

        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                filename = match.group(1)
                return {
                    "action": "read",
                    "file": filename
                }

        return None

    def _parse_list(self, text: str) -> Optional[Dict[str, Any]]:
        """Parse list directory commands"""
        patterns = [
            r"(?:list|show|ls|dir)\s+(?:files?\s+(?:in\s+)?)?['\"]?([a-zA-Z0-9_./\\-]*)['\"]?",
            r"(?:what'?s?\s+in|show\s+me)\s+(?:the\s+)?(?:current\s+)?(?:directory|folder)",
        ]

        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                target = match.group(1) if match.lastindex >= 1 else "."
                if not target or target in ["files", "here", "this"]:
                    target = "."
                return {
                    "action": "list",
                    "target": target
                }

        # Default list current directory
        if any(word in text for word in ["list", "show", "ls", "files"]):
            return {
                "action": "list",
                "target": "."
            }

        return None

    def to_json_string(self, command: Dict[str, Any]) -> str:
        """Convert command dict to JSON string"""
        return json.dumps(command, indent=2)
