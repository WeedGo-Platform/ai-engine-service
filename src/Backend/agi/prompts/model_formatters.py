"""
Model-specific Prompt Formatters for AGI System
Handles formatting prompts for different LLM architectures
"""

from typing import List, Dict, Any, Optional
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class ModelFamily(Enum):
    """Model family types for prompt formatting"""
    LLAMA = "llama"
    MISTRAL = "mistral"
    QWEN = "qwen"
    PHI = "phi"
    DEEPSEEK = "deepseek"
    TINYLLAMA = "tinyllama"
    UNKNOWN = "unknown"


class PromptFormatter:
    """Base class for model-specific prompt formatting"""

    def __init__(self, model_name: str):
        """
        Initialize prompt formatter

        Args:
            model_name: Name of the model
        """
        self.model_name = model_name.lower()
        self.model_family = self._detect_model_family()
        logger.info(f"Initialized formatter for {model_name} (family: {self.model_family.value})")

    def _detect_model_family(self) -> ModelFamily:
        """Detect model family from model name"""
        if "llama" in self.model_name:
            if "tinyllama" in self.model_name:
                return ModelFamily.TINYLLAMA
            return ModelFamily.LLAMA
        elif "mistral" in self.model_name:
            return ModelFamily.MISTRAL
        elif "qwen" in self.model_name or "qwq" in self.model_name:
            return ModelFamily.QWEN
        elif "phi" in self.model_name:
            return ModelFamily.PHI
        elif "deepseek" in self.model_name:
            return ModelFamily.DEEPSEEK
        else:
            return ModelFamily.UNKNOWN

    def format_prompt(
        self,
        messages: List[Dict[str, str]],
        system_prompt: Optional[str] = None
    ) -> str:
        """
        Format messages into model-specific prompt

        Args:
            messages: List of message dicts with 'role' and 'content'
            system_prompt: Optional system prompt to prepend

        Returns:
            Formatted prompt string
        """
        if self.model_family == ModelFamily.LLAMA:
            return self._format_llama_prompt(messages, system_prompt)
        elif self.model_family == ModelFamily.TINYLLAMA:
            return self._format_tinyllama_prompt(messages, system_prompt)
        elif self.model_family == ModelFamily.MISTRAL:
            return self._format_mistral_prompt(messages, system_prompt)
        elif self.model_family == ModelFamily.QWEN:
            return self._format_qwen_prompt(messages, system_prompt)
        elif self.model_family == ModelFamily.PHI:
            return self._format_phi_prompt(messages, system_prompt)
        elif self.model_family == ModelFamily.DEEPSEEK:
            return self._format_deepseek_prompt(messages, system_prompt)
        else:
            return self._format_generic_prompt(messages, system_prompt)

    def _format_llama_prompt(
        self,
        messages: List[Dict[str, str]],
        system_prompt: Optional[str] = None
    ) -> str:
        """Format prompt for Llama models"""
        prompt = ""

        # Add system prompt if provided
        if system_prompt:
            prompt = f"<|begin_of_text|><|start_header_id|>system<|end_header_id|>\n\n{system_prompt}<|eot_id|>"

        # Add conversation messages
        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")

            if role == "system" and not system_prompt:
                prompt += f"<|start_header_id|>system<|end_header_id|>\n\n{content}<|eot_id|>"
            elif role == "user":
                prompt += f"<|start_header_id|>user<|end_header_id|>\n\n{content}<|eot_id|>"
            elif role == "assistant":
                prompt += f"<|start_header_id|>assistant<|end_header_id|>\n\n{content}<|eot_id|>"

        # Add final assistant header for completion
        prompt += "<|start_header_id|>assistant<|end_header_id|>\n\n"

        return prompt

    def _format_tinyllama_prompt(
        self,
        messages: List[Dict[str, str]],
        system_prompt: Optional[str] = None
    ) -> str:
        """Format prompt for TinyLlama models"""
        prompt = ""

        # TinyLlama uses a simpler format
        if system_prompt:
            prompt = f"<|system|>\n{system_prompt}</s>\n"

        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")

            if role == "system" and not system_prompt:
                prompt += f"<|system|>\n{content}</s>\n"
            elif role == "user":
                prompt += f"<|user|>\n{content}</s>\n"
            elif role == "assistant":
                prompt += f"<|assistant|>\n{content}</s>\n"

        # Add assistant tag for completion
        prompt += "<|assistant|>\n"

        return prompt

    def _format_mistral_prompt(
        self,
        messages: List[Dict[str, str]],
        system_prompt: Optional[str] = None
    ) -> str:
        """Format prompt for Mistral models"""
        prompt = ""

        # Mistral uses [INST] format
        if system_prompt:
            prompt = f"[INST] {system_prompt}\n\n"
        else:
            prompt = "[INST] "

        for i, msg in enumerate(messages):
            role = msg.get("role", "user")
            content = msg.get("content", "")

            if role == "user":
                if i > 0:
                    prompt += f" [INST] {content} [/INST]"
                else:
                    prompt += f"{content} [/INST]"
            elif role == "assistant":
                prompt += f" {content}</s>"

        return prompt

    def _format_qwen_prompt(
        self,
        messages: List[Dict[str, str]],
        system_prompt: Optional[str] = None
    ) -> str:
        """Format prompt for Qwen models"""
        prompt = ""

        # Qwen uses special tokens
        if system_prompt:
            prompt = f"<|im_start|>system\n{system_prompt}<|im_end|>\n"

        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")

            if role == "system" and not system_prompt:
                prompt += f"<|im_start|>system\n{content}<|im_end|>\n"
            elif role == "user":
                prompt += f"<|im_start|>user\n{content}<|im_end|>\n"
            elif role == "assistant":
                prompt += f"<|im_start|>assistant\n{content}<|im_end|>\n"

        # Add assistant start token
        prompt += "<|im_start|>assistant\n"

        return prompt

    def _format_phi_prompt(
        self,
        messages: List[Dict[str, str]],
        system_prompt: Optional[str] = None
    ) -> str:
        """Format prompt for Phi models"""
        prompt = ""

        # Phi uses similar format to ChatGPT
        if system_prompt:
            prompt = f"System: {system_prompt}\n\n"

        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")

            if role == "system" and not system_prompt:
                prompt += f"System: {content}\n\n"
            elif role == "user":
                prompt += f"User: {content}\n\n"
            elif role == "assistant":
                prompt += f"Assistant: {content}\n\n"

        # Add assistant prefix
        prompt += "Assistant: "

        return prompt

    def _format_deepseek_prompt(
        self,
        messages: List[Dict[str, str]],
        system_prompt: Optional[str] = None
    ) -> str:
        """Format prompt for DeepSeek models"""
        prompt = ""

        # DeepSeek Coder uses special tokens for code
        if system_prompt:
            prompt = f"<|begin▁of▁sentence|>{system_prompt}\n\n"

        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")

            if role == "system" and not system_prompt:
                prompt += f"### System:\n{content}\n\n"
            elif role == "user":
                prompt += f"### User:\n{content}\n\n"
            elif role == "assistant":
                prompt += f"### Assistant:\n{content}\n\n"

        # Add assistant prefix
        prompt += "### Assistant:\n"

        return prompt

    def _format_generic_prompt(
        self,
        messages: List[Dict[str, str]],
        system_prompt: Optional[str] = None
    ) -> str:
        """Generic prompt formatting for unknown models"""
        prompt = ""

        if system_prompt:
            prompt = f"System: {system_prompt}\n\n"

        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")

            if role == "system" and not system_prompt:
                prompt += f"System: {content}\n\n"
            elif role == "user":
                prompt += f"User: {content}\n\n"
            elif role == "assistant":
                prompt += f"Assistant: {content}\n\n"

        prompt += "Assistant: "

        return prompt

    def extract_response(self, full_output: str) -> str:
        """
        Extract the actual response from model output

        Args:
            full_output: Full model output including any formatting

        Returns:
            Cleaned response text
        """
        # Remove common stop tokens
        stop_tokens = [
            "</s>", "<|im_end|>", "<|eot_id|>", "[/INST]",
            "<|end|>", "<|endoftext|>", "### User:", "User:"
        ]

        response = full_output
        for token in stop_tokens:
            if token in response:
                response = response.split(token)[0]

        return response.strip()


# Singleton formatter cache
_formatters: Dict[str, PromptFormatter] = {}


def get_formatter(model_name: str) -> PromptFormatter:
    """
    Get or create a prompt formatter for a model

    Args:
        model_name: Name of the model

    Returns:
        PromptFormatter instance
    """
    if model_name not in _formatters:
        _formatters[model_name] = PromptFormatter(model_name)
    return _formatters[model_name]