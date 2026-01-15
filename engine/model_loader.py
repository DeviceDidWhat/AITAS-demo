"""Load and initialize Small Language Model (SLM)"""
import os
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
from typing import Tuple


class ModelLoader:
    """Handles loading and initialization of the language model"""

    def __init__(self, model_name: str, device: str = "cpu"):
        self.model_name = model_name
        self.device = device
        self.model = None
        self.tokenizer = None

    def load_model(self) -> Tuple[AutoModelForCausalLM, AutoTokenizer]:
        """
        Load the model and tokenizer
        Returns: Tuple of (model, tokenizer)
        """
        print(f"Loading model: {self.model_name}")
        print(f"Device: {self.device}")

        # Load tokenizer
        self.tokenizer = AutoTokenizer.from_pretrained(
            self.model_name,
            trust_remote_code=True
        )

        # Set pad token if not exists
        if self.tokenizer.pad_token is None:
            self.tokenizer.pad_token = self.tokenizer.eos_token

        # Load model
        self.model = AutoModelForCausalLM.from_pretrained(
            self.model_name,
            trust_remote_code=True,
            torch_dtype=torch.float32 if self.device == "cpu" else torch.float16,
            low_cpu_mem_usage=True
        )

        self.model.to(self.device)
        self.model.eval()

        print("Model loaded successfully!")
        return self.model, self.tokenizer

    def is_loaded(self) -> bool:
        """Check if model is loaded"""
        return self.model is not None and self.tokenizer is not None
