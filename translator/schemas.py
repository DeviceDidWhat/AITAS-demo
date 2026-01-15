"""JSON schemas for validating command structures"""
from pydantic import BaseModel, Field
from typing import Optional, Literal


class MkdirCommand(BaseModel):
    """Create directory command"""
    action: Literal["mkdir"]
    target: str = Field(..., description="Directory name or path to create")


class WriteCommand(BaseModel):
    """Write file command"""
    action: Literal["write"]
    file: str = Field(..., description="File path to write")
    content: str = Field(default="", description="Content to write to file")


class ReadCommand(BaseModel):
    """Read file command"""
    action: Literal["read"]
    file: str = Field(..., description="File path to read")


class ListCommand(BaseModel):
    """List directory contents command"""
    action: Literal["list"]
    target: str = Field(default=".", description="Directory to list")


class ShellCommand(BaseModel):
    """Shell command execution"""
    action: Literal["shell"]
    command: str = Field(..., description="Shell command to execute")


class CommandAction(BaseModel):
    """Base command action - polymorphic"""
    action: str

    @classmethod
    def parse_command(cls, data: dict):
        """Parse JSON dict to appropriate command model"""
        action = data.get("action", "")

        if action == "mkdir":
            return MkdirCommand(**data)
        elif action == "write":
            return WriteCommand(**data)
        elif action == "read":
            return ReadCommand(**data)
        elif action == "list":
            return ListCommand(**data)
        elif action == "shell":
            return ShellCommand(**data)
        else:
            raise ValueError(f"Unknown action: {action}")


# JSON Schema definitions for validation
MKDIR_SCHEMA = {
    "type": "object",
    "properties": {
        "action": {"type": "string", "const": "mkdir"},
        "target": {"type": "string"}
    },
    "required": ["action", "target"]
}

WRITE_SCHEMA = {
    "type": "object",
    "properties": {
        "action": {"type": "string", "const": "write"},
        "file": {"type": "string"},
        "content": {"type": "string"}
    },
    "required": ["action", "file"]
}

READ_SCHEMA = {
    "type": "object",
    "properties": {
        "action": {"type": "string", "const": "read"},
        "file": {"type": "string"}
    },
    "required": ["action", "file"]
}

LIST_SCHEMA = {
    "type": "object",
    "properties": {
        "action": {"type": "string", "const": "list"},
        "target": {"type": "string"}
    },
    "required": ["action", "target"]
}
