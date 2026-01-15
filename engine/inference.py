"""Run inference on user input using the loaded model"""
import torch
from typing import Dict, Any
from .prompt_templates import format_prompt, extract_json_from_response


class InferenceEngine:
    """Handles model inference and response generation"""

    def __init__(self, model, tokenizer, config: Dict[str, Any]):
        self.model = model
        self.tokenizer = tokenizer
        self.max_length = config.get("max_length", 256)
        self.temperature = config.get("temperature", 0.1)
        self.top_p = config.get("top_p", 0.95)
        self.device = config.get("device", "cpu")

    def generate_response(self, user_input: str) -> str:
        """
        Generate response from user input
        Returns: Raw model output
        """
        # Format prompt
        prompt = format_prompt(user_input)

        print(f"[DEBUG] Prompt length: {len(prompt)} chars")

        # Tokenize
        inputs = self.tokenizer(
            prompt,
            return_tensors="pt",
            padding=True,
            truncation=True,
            max_length=512
        ).to(self.device)

        print(f"[DEBUG] Input tokens: {inputs['input_ids'].shape}")

        # Generate with optimized parameters
        with torch.no_grad():
            outputs = self.model.generate(
                inputs["input_ids"],
                attention_mask=inputs["attention_mask"],
                max_new_tokens=80,  # Reduced for faster generation
                temperature=0.7,  # Increased for faster sampling
                do_sample=False,  # Use greedy decoding for speed
                pad_token_id=self.tokenizer.pad_token_id,
                eos_token_id=self.tokenizer.eos_token_id,
                num_beams=1  # Disable beam search for speed
            )

        print(f"[DEBUG] Generated tokens: {outputs.shape}")

        # Decode
        response = self.tokenizer.decode(outputs[0], skip_special_tokens=True)

        print(f"[DEBUG] Full response length: {len(response)} chars")

        # Extract only the generated part (remove prompt)
        if prompt in response:
            response = response.replace(prompt, "").strip()

        print(f"[DEBUG] Extracted response: {response[:200]}")

        return response

    def parse_to_json(self, user_input: str) -> str:
        """
        Generate and extract JSON from model response
        Returns: JSON string
        """
        raw_response = self.generate_response(user_input)
        json_response = extract_json_from_response(raw_response)
        return json_response
