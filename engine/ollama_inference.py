"""Ollama-based inference engine for fast local LLM"""
import ollama
import json
from typing import Dict, Any
from .prompt_templates import SYSTEM_PROMPT_LINUX, SYSTEM_PROMPT_WINDOWS, extract_json_from_response


class OllamaInferenceEngine:
    """
    Uses Ollama for fast local LLM inference
    Much faster and easier than raw transformers
    """

    def __init__(self, model_name: str = "llama3.2:1b"):
        """
        Initialize Ollama inference engine

        Args:
            model_name: Ollama model to use (default: llama3.2:1b - smallest, fastest)
                       Other options: llama3.2:3b, phi3:mini, qwen2.5:0.5b
        """
        self.model_name = model_name

        # Detect OS and use appropriate prompt
        import platform
        os_name = platform.system()

        if os_name == 'Windows':
            self.system_prompt = SYSTEM_PROMPT_WINDOWS
        else:
            self.system_prompt = SYSTEM_PROMPT_LINUX

    def generate_response(self, user_input: str) -> str:
        """
        Generate response using Ollama

        Args:
            user_input: User's natural language command

        Returns:
            Model's response (ideally JSON)
        """
        try:
            # Create the full prompt
            prompt = f"""{self.system_prompt}

User: "{user_input}"
Output:"""

            print(f"[DEBUG] Sending to Ollama model: {self.model_name}")

            # Call Ollama
            response = ollama.generate(
                model=self.model_name,
                prompt=prompt,
                options={
                    "temperature": 0.1,  # Low temp for more deterministic output
                    "num_predict": 100,  # Max tokens to generate
                    "stop": ["\n\n", "User:"],  # Stop at these sequences
                }
            )

            # Extract the response text
            response_text = response['response'].strip()

            print(f"[DEBUG] Ollama response: {response_text}")

            return response_text

        except Exception as e:
            print(f"[ERROR] Ollama generation failed: {str(e)}")
            raise

    def parse_to_json(self, user_input: str) -> str:
        """
        Generate and extract JSON from model response

        Args:
            user_input: User's natural language command

        Returns:
            JSON string with the command
        """
        raw_response = self.generate_response(user_input)
        json_response = extract_json_from_response(raw_response)
        return json_response

    def test_connection(self) -> bool:
        """
        Test if Ollama is running and model is available

        Returns:
            True if connection successful, False otherwise
        """
        try:
            # Try to list models
            models = ollama.list()
            print(f"[DEBUG] Available models: {[m['model'] for m in models.get('models', [])]}")

            # Check if our model exists
            model_exists = any(self.model_name in m['model'] for m in models.get('models', []))

            if not model_exists:
                print(f"[WARNING] Model {self.model_name} not found. You may need to pull it.")
                print(f"[INFO] Run: ollama pull {self.model_name}")
                return False

            return True

        except Exception as e:
            print(f"[ERROR] Could not connect to Ollama: {str(e)}")
            print("[INFO] Make sure Ollama is running:")
            print("  1. Download from: https://ollama.ai")
            print("  2. Start Ollama")
            print(f"  3. Run: ollama pull {self.model_name}")
            return False
