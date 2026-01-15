"""Directory operations executor"""
import os
from pathlib import Path
from typing import Dict, Any, List


class DirectoryOperations:
    """Handles directory operations"""

    def __init__(self, base_path: str = "."):
        self.base_path = Path(base_path).resolve()

    def make_directory(self, dir_path: str) -> Dict[str, Any]:
        """
        Create a directory
        Returns: Status dict with success/error
        """
        try:
            full_path = self.base_path / dir_path

            # Create directory
            full_path.mkdir(parents=True, exist_ok=True)

            return {
                "success": True,
                "message": f"Directory created: {dir_path}",
                "path": str(full_path)
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"Failed to create directory: {dir_path}"
            }

    def list_directory(self, dir_path: str = ".") -> Dict[str, Any]:
        """
        List contents of a directory
        Returns: Status dict with file list or error
        """
        try:
            full_path = self.base_path / dir_path

            if not full_path.exists():
                return {
                    "success": False,
                    "error": "Directory not found",
                    "message": f"Directory does not exist: {dir_path}"
                }

            if not full_path.is_dir():
                return {
                    "success": False,
                    "error": "Not a directory",
                    "message": f"Path is not a directory: {dir_path}"
                }

            # List contents
            items = []
            for item in full_path.iterdir():
                item_type = "dir" if item.is_dir() else "file"
                items.append({
                    "name": item.name,
                    "type": item_type,
                    "path": str(item.relative_to(self.base_path))
                })

            return {
                "success": True,
                "message": f"Listed directory: {dir_path}",
                "items": items,
                "count": len(items)
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"Failed to list directory: {dir_path}"
            }
