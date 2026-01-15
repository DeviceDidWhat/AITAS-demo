"""Session manager for maintaining conversation history and context"""
from typing import List, Dict, Any, Optional
from datetime import datetime
import json


class SessionManager:
    """Manage conversation history and session context"""

    def __init__(self, max_history: int = 10):
        """
        Initialize session manager

        Args:
            max_history: Maximum number of conversation turns to keep
        """
        self.max_history = max_history
        self.conversation_history: List[Dict[str, Any]] = []
        self.session_context: Dict[str, Any] = {
            "current_file": None,
            "current_error": None,
            "debugging_session": False,
            "test_mode": False,
            "language": None,
            "project_files": [],
        }
        self.session_start = datetime.now()

    def add_user_message(self, message: str) -> None:
        """Add user message to history"""
        self.conversation_history.append({
            "role": "user",
            "content": message,
            "timestamp": datetime.now().isoformat()
        })
        self._trim_history()

    def add_assistant_message(self, message: str, command: Optional[Dict[str, Any]] = None) -> None:
        """Add assistant message to history"""
        entry = {
            "role": "assistant",
            "content": message,
            "timestamp": datetime.now().isoformat()
        }
        if command:
            entry["command"] = command

        self.conversation_history.append(entry)
        self._trim_history()

    def add_system_message(self, message: str) -> None:
        """Add system message (errors, results) to history"""
        self.conversation_history.append({
            "role": "system",
            "content": message,
            "timestamp": datetime.now().isoformat()
        })
        self._trim_history()

    def get_conversation_history(self, last_n: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Get conversation history

        Args:
            last_n: Get last N turns (None for all)

        Returns:
            List of conversation messages
        """
        if last_n:
            return self.conversation_history[-last_n:]
        return self.conversation_history

    def get_context_string(self, include_last_n: int = 5) -> str:
        """
        Get conversation history as formatted string for LLM context

        Args:
            include_last_n: Number of recent turns to include

        Returns:
            Formatted conversation history
        """
        history = self.get_conversation_history(last_n=include_last_n)

        if not history:
            return ""

        context = "Recent Conversation:\n"
        for entry in history:
            role = entry["role"].capitalize()
            content = entry["content"]

            if entry["role"] == "assistant" and "command" in entry:
                command = entry.get("command", {})
                context += f"{role}: {content}\nExecuted: {json.dumps(command)}\n"
            else:
                context += f"{role}: {content}\n"

            context += "\n"

        return context

    def update_context(self, key: str, value: Any) -> None:
        """Update session context"""
        self.session_context[key] = value

    def get_context(self, key: str) -> Any:
        """Get value from session context"""
        return self.session_context.get(key)

    def set_current_file(self, file_path: str) -> None:
        """Set currently active file"""
        self.session_context["current_file"] = file_path
        if file_path not in self.session_context["project_files"]:
            self.session_context["project_files"].append(file_path)

    def get_current_file(self) -> Optional[str]:
        """Get currently active file"""
        return self.session_context.get("current_file")

    def start_debugging_session(self, error: str, file: Optional[str] = None) -> None:
        """Start a debugging session"""
        self.session_context["debugging_session"] = True
        self.session_context["current_error"] = error
        if file:
            self.set_current_file(file)

    def end_debugging_session(self) -> None:
        """End debugging session"""
        self.session_context["debugging_session"] = False
        self.session_context["current_error"] = None

    def is_debugging(self) -> bool:
        """Check if in debugging session"""
        return self.session_context.get("debugging_session", False)

    def set_language(self, language: str) -> None:
        """Set primary programming language for session"""
        self.session_context["language"] = language

    def get_language(self) -> Optional[str]:
        """Get primary programming language"""
        return self.session_context.get("language")

    def get_session_summary(self) -> Dict[str, Any]:
        """Get summary of current session"""
        duration = datetime.now() - self.session_start

        return {
            "duration_seconds": duration.total_seconds(),
            "total_messages": len(self.conversation_history),
            "current_file": self.get_current_file(),
            "is_debugging": self.is_debugging(),
            "language": self.get_language(),
            "files_accessed": len(self.session_context["project_files"]),
            "context": self.session_context
        }

    def clear_history(self) -> None:
        """Clear conversation history"""
        self.conversation_history.clear()

    def reset_session(self) -> None:
        """Reset entire session"""
        self.conversation_history.clear()
        self.session_context = {
            "current_file": None,
            "current_error": None,
            "debugging_session": False,
            "test_mode": False,
            "language": None,
            "project_files": [],
        }
        self.session_start = datetime.now()

    def _trim_history(self) -> None:
        """Trim history to max_history length"""
        if len(self.conversation_history) > self.max_history:
            self.conversation_history = self.conversation_history[-self.max_history:]

    def should_use_context(self) -> bool:
        """Determine if context should be included in next prompt"""
        # Use context if:
        # 1. We have conversation history
        # 2. We're in a debugging session
        # 3. We have a current file set
        return (
            len(self.conversation_history) > 0 or
            self.is_debugging() or
            self.get_current_file() is not None
        )

    def get_enhanced_prompt_context(self) -> str:
        """Get enhanced context for prompt including session state"""
        if not self.should_use_context():
            return ""

        context_parts = []

        # Add current file context
        if self.get_current_file():
            context_parts.append(f"Current File: {self.get_current_file()}")

        # Add debugging context
        if self.is_debugging():
            context_parts.append(f"Debugging Session Active")
            if self.session_context.get("current_error"):
                context_parts.append(f"Current Error: {self.session_context['current_error']}")

        # Add language context
        if self.get_language():
            context_parts.append(f"Language: {self.get_language()}")

        # Add conversation history
        history = self.get_context_string(include_last_n=3)
        if history:
            context_parts.append(history)

        if context_parts:
            return "Session Context:\n" + "\n".join(context_parts) + "\n\n"

        return ""
