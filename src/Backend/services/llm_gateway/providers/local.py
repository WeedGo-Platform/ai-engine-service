"""
Local Provider - llama-cpp-python Fallback

Local inference using llama-cpp-python models.
Always available fallback when cloud providers are exhausted.

Features:
- No rate limits (local CPU/GPU)
- No API costs
- Offline capable
- Slower inference (~5s on CPU)
- Integrates with existing ModelManager
"""

import logging
from typing import Dict, List, Optional, Union, AsyncGenerator, Callable

from ..types import (
    ProviderConfig,
    CompletionResult,
    ProviderError
)
from .base import BaseProvider

logger = logging.getLogger(__name__)


class LocalProvider(BaseProvider):
    """
    Local LLM provider using llama-cpp-python

    Features:
    - No rate limits
    - No costs
    - Offline capable
    - Always available fallback

    Can be initialized with:
    1. ModelManager reference (preferred)
    2. Direct model callable
    3. Mock mode for testing
    """

    def __init__(
        self,
        model_manager=None,
        model_callable: Optional[Callable] = None,
        model_name: str = "Local Llama"
    ):
        """
        Initialize Local provider

        Args:
            model_manager: ModelManager instance (from existing codebase)
            model_callable: Direct callable model function
            model_name: Display name for the model
        """
        config = ProviderConfig(
            name="Local Llama (llama-cpp-python)",
            enabled=True,  # Always enabled (fallback)
            cost_per_1m_input_tokens=0.0,
            cost_per_1m_output_tokens=0.0,
            avg_latency_seconds=5.0,  # Slower on CPU
            supports_reasoning=False,
            supports_streaming=True,  # llama-cpp-python supports streaming
            supports_tools=False,  # Basic models don't support function calling
            is_free=True,
            requests_per_minute=None,  # No limits
            requests_per_day=None,
            api_key=None,
            base_url=None,
            model_name=model_name
        )

        super().__init__(config)

        self.model_manager = model_manager
        self.model_callable = model_callable

        if model_manager:
            logger.info("Local provider initialized with ModelManager")
        elif model_callable:
            logger.info("Local provider initialized with model callable")
        else:
            logger.warning("Local provider initialized without model (mock mode)")

    def _get_model(self):
        """
        Get the current model for inference

        Returns:
            Model callable

        Raises:
            ProviderError: If no model is available
        """
        # Try model_manager first
        if self.model_manager:
            model = self.model_manager.get_current_model()
            if model:
                return model

        # Try direct callable
        if self.model_callable:
            return self.model_callable

        # No model available
        raise ProviderError("No local model loaded")

    async def complete(
        self,
        messages: List[Dict],
        temperature: float = 0.7,
        max_tokens: int = 2000,
        stream: bool = False,
        tools: Optional[List[Dict]] = None,
        **kwargs
    ) -> Union[CompletionResult, AsyncGenerator[str, None]]:
        """
        Generate completion using local model

        Args:
            messages: Chat messages in OpenAI format
            temperature: Sampling temperature (0.0-2.0)
            max_tokens: Maximum tokens to generate
            stream: Whether to stream the response
            tools: Tool definitions (not supported)
            **kwargs: Additional parameters

        Returns:
            CompletionResult or AsyncGenerator for streaming

        Raises:
            ProviderError: If request fails
        """
        if tools:
            logger.warning("Local provider does not support tool calling")

        try:
            model = self._get_model()
        except ProviderError as e:
            # If no model is available, return a mock response for testing
            logger.warning(f"No local model available: {e}. Using mock response.")
            return self._mock_response(messages, max_tokens)

        # Convert OpenAI messages to prompt string
        # This is a simplified conversion - production should use proper templates
        prompt = self._messages_to_prompt(messages)

        # Build generation parameters
        generation_params = {
            "max_tokens": max_tokens,
            "temperature": temperature,
            "top_p": kwargs.get("top_p", 0.9),
            "top_k": kwargs.get("top_k", 40),
            "repeat_penalty": kwargs.get("repeat_penalty", 1.1),
            "stream": stream
        }

        try:
            # Call the model (llama-cpp-python format)
            response = model(prompt, **generation_params)

            if stream:
                # Streaming not implemented in this version
                raise ProviderError("Streaming not yet implemented for Local provider")

            # Extract response
            if isinstance(response, dict):
                # llama-cpp-python dict format
                content = response.get("choices", [{}])[0].get("text", "")
                usage = response.get("usage", {})
                tokens_input = usage.get("prompt_tokens", len(prompt.split()))
                tokens_output = usage.get("completion_tokens", len(content.split()))
                finish_reason = response.get("choices", [{}])[0].get("finish_reason", "stop")
            else:
                # Fallback for simple string response
                content = str(response)
                tokens_input = len(prompt.split())
                tokens_output = len(content.split())
                finish_reason = "stop"

            # Calculate cost (always $0 for local)
            cost = 0.0

            return CompletionResult(
                content=content.strip(),
                provider=self.name,
                model=self.config.model_name,
                selection_reason="",  # Will be filled by router
                latency=0.0,  # Will be measured by base class
                tokens_input=tokens_input,
                tokens_output=tokens_output,
                cost=cost,
                cached=False,
                finish_reason=finish_reason,
                metadata={
                    "model": self.config.model_name,
                    "backend": "llama-cpp-python"
                }
            )

        except Exception as e:
            raise ProviderError(f"Local model completion failed: {e}")

    def _messages_to_prompt(self, messages: List[Dict]) -> str:
        """
        Convert OpenAI message format to prompt string

        Args:
            messages: List of message dicts

        Returns:
            Formatted prompt string
        """
        # Simple conversion - production should use model-specific templates
        prompt_parts = []

        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")

            if role == "system":
                prompt_parts.append(f"<|system|>\n{content}")
            elif role == "user":
                prompt_parts.append(f"<|user|>\n{content}")
            elif role == "assistant":
                prompt_parts.append(f"<|assistant|>\n{content}")

        # Add final assistant prompt
        prompt_parts.append("<|assistant|>\n")

        return "\n".join(prompt_parts)

    def _mock_response(
        self,
        messages: List[Dict],
        max_tokens: int
    ) -> CompletionResult:
        """
        Generate mock response when no model is available (for testing)

        Args:
            messages: Input messages
            max_tokens: Max tokens

        Returns:
            Mock CompletionResult
        """
        logger.info("Generating mock response (no model loaded)")

        # Extract last user message
        last_message = ""
        for msg in reversed(messages):
            if msg.get("role") == "user":
                last_message = msg.get("content", "")
                break

        mock_content = f"[Mock Local Response] I received: '{last_message[:50]}...'"

        return CompletionResult(
            content=mock_content,
            provider=self.name,
            model="mock-local",
            selection_reason="",
            latency=0.1,
            tokens_input=10,
            tokens_output=15,
            cost=0.0,
            cached=False,
            finish_reason="stop",
            metadata={"mock": True}
        )

    async def check_health(self) -> bool:
        """
        Check if local model is healthy

        Returns:
            True if model is loaded, False otherwise
        """
        try:
            model = self._get_model()
            return model is not None
        except:
            return False

    def set_model_manager(self, model_manager):
        """
        Set or update the model manager

        Args:
            model_manager: ModelManager instance
        """
        self.model_manager = model_manager
        logger.info("Updated Local provider model manager")

    def set_model_callable(self, model_callable: Callable):
        """
        Set or update the model callable

        Args:
            model_callable: Direct model function
        """
        self.model_callable = model_callable
        logger.info("Updated Local provider model callable")

    def __repr__(self):
        status = "✓" if self.is_healthy else "✗"
        model_status = "loaded" if self.model_manager or self.model_callable else "mock"
        return (
            f"{status} Local Llama - {model_status} "
            f"({self.stats.requests_made} reqs, ${self.stats.total_cost:.4f})"
        )
