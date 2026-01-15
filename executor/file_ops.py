"""File operations executor"""
import os
from pathlib import Path
from typing import Dict, Any


class FileOperations:
    """Handles file read/write operations"""

    def __init__(self, base_path: str = "."):
        self.base_path = Path(base_path).resolve()

    def write_file(self, file_path: str, content: str = "") -> Dict[str, Any]:
        """
        Write content to a file
        Returns: Status dict with success/error
        """
        try:
            full_path = self.base_path / file_path

            # Create parent directories if they don't exist
            full_path.parent.mkdir(parents=True, exist_ok=True)

            # Write file
            with open(full_path, 'w', encoding='utf-8') as f:
                f.write(content)

            return {
                "success": True,
                "message": f"File created: {file_path}",
                "path": str(full_path)
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"Failed to write file: {file_path}"
            }

    def read_file(self, file_path: str) -> Dict[str, Any]:
        """
        Read content from a file
        Returns: Status dict with content or error
        """
        try:
            full_path = self.base_path / file_path

            if not full_path.exists():
                return {
                    "success": False,
                    "error": "File not found",
                    "message": f"File does not exist: {file_path}"
                }

            with open(full_path, 'r', encoding='utf-8') as f:
                content = f.read()

            return {
                "success": True,
                "message": f"File read: {file_path}",
                "content": content,
                "path": str(full_path)
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"Failed to read file: {file_path}"
            }
