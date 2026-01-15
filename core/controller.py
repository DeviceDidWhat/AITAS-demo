"""Main controller orchestrating the entire flow"""
from typing import Dict, Any, Optional
from translator.simple_parser import SimpleCommandParser
from translator.intent_extractor import IntentExtractor
from executor.file_ops import FileOperations
from executor.directory_ops import DirectoryOperations
from executor.shell_executor import ShellExecutor
from security.command_filter import CommandFilter


class Controller:
    """Main orchestrator for AITAS"""

    def __init__(self, inference_engine=None, config: Dict[str, Any] = None, use_llm: bool = False):
        """
        Initialize controller

        Args:
            inference_engine: Optional LLM inference engine (Ollama)
            config: Configuration dict
            use_llm: If True, use LLM. If False, use rule-based parser
        """
        self.use_llm = use_llm and inference_engine is not None
        self.inference_engine = inference_engine
        self.parser = SimpleCommandParser()
        self.intent_extractor = IntentExtractor()
        self.file_ops = FileOperations()
        self.dir_ops = DirectoryOperations()
        self.shell_executor = ShellExecutor()

        # Security
        if config:
            security_config = config.get("security", {})
            self.command_filter = CommandFilter(
                allowed_operations=security_config.get("allowed_operations"),
                dangerous_patterns=security_config.get("dangerous_commands")
            )
        else:
            self.command_filter = CommandFilter()

        self.config = config or {}

    def process_input(self, user_input: str) -> Dict[str, Any]:
        """
        Process user input through the entire pipeline
        Returns: Result dict with action, status, and data
        """
        try:
            print(f"\n[DEBUG] Processing input: {user_input}")

            # Step 1: Parse command (LLM or rule-based)
            if self.use_llm:
                # Use LLM (Ollama)
                json_response = self.inference_engine.parse_to_json(user_input)
                print(f"[DEBUG] LLM response: {json_response}")
                command = self.intent_extractor.extract(json_response)
                command_dict = self.intent_extractor.to_dict(command)
                print(f"[DEBUG] Extracted command: {command_dict}")
            else:
                # Use fast rule-based parser
                command_dict = self.parser.parse(user_input)
                print(f"[DEBUG] Parsed command: {command_dict}")

            # Step 2: Security check
            security_check = self.command_filter.validate_command(command_dict)
            print(f"[DEBUG] Security check: {security_check}")
            if not security_check["safe"]:
                return {
                    "success": False,
                    "error": "Security check failed",
                    "reason": security_check.get("reason"),
                    "command": command_dict
                }

            # Step 3: Execute command
            result = self._execute_command(command_dict)
            print(f"[DEBUG] Execution result: {result}")

            final_result = {
                "success": result.get("success", False),
                "command": command_dict,
                "result": result
            }
            print(f"[DEBUG] Final result being returned: {final_result}")
            return final_result

        except Exception as e:
            import traceback
            print(f"\n[DEBUG ERROR in process_input] Exception: {type(e).__name__}: {str(e)}")
            traceback.print_exc()
            return {
                "success": False,
                "error": str(e),
                "command": None
            }

    def _execute_command(self, command: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the validated command"""
        try:
            action = command.get("action")
            print(f"\n[DEBUG] Executing action: {action}")
            print(f"[DEBUG] Full command: {command}")

            if action == "mkdir":
                result = self.dir_ops.make_directory(command["target"])
                print(f"[DEBUG] mkdir result: {result}")
                return result

            elif action == "write":
                result = self.file_ops.write_file(
                    command["file"],
                    command.get("content", "")
                )
                print(f"[DEBUG] write result: {result}")
                return result

            elif action == "read":
                result = self.file_ops.read_file(command["file"])
                print(f"[DEBUG] read result: {result}")
                return result

            elif action == "list":
                result = self.dir_ops.list_directory(command.get("target", "."))
                print(f"[DEBUG] list result: {result}")
                return result

            elif action == "shell":
                print(f"[DEBUG] About to execute shell command: {command['command']}")
                result = self.shell_executor.execute(command["command"])
                print(f"[DEBUG] shell result: {result}")
                return result

            else:
                return {
                    "success": False,
                    "error": f"Unknown action: {action}"
                }
        except Exception as e:
            import traceback
            print(f"\n[DEBUG ERROR] Exception caught: {type(e).__name__}")
            print(f"[DEBUG ERROR] Exception message: {str(e)}")
            print(f"[DEBUG ERROR] Traceback:")
            traceback.print_exc()
            return {
                "success": False,
                "error": f"Execution error: {str(e)}",
                "details": str(type(e).__name__)
            }
