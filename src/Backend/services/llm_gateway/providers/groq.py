"""
Groq Provider - Llama 3.3 70B (Free Tier)

Groq provides ultra-fast LLM inference with free tier:
- 14,400 requests/day (10 req/min)
- 100 requests/minute burst
- ~0.5s average latency (10x faster than typical)
- OpenAI-compatible API

Docs: https://console.groq.com/docs/quickstart
"""

import os
import httpx
import logging
from typing import Dict, List, Optional, Union, AsyncGenerator

from ..types import (
    ProviderConfig,
    CompletionResult,
    ProviderError,
    RateLimitError
)
from .base import BaseProvider

logger = logging.getLogger(__name__)


class GroqProvider(BaseProvider):
    """
    Groq provider using Llama 3.3 70B model

    Free tier limits:
    - 14,400 requests/day
    - 100 requests/minute (burst)
    - 10 requests/minute (sustained)
    - 6,000 tokens/minute

    Features:
    - Ultra-fast inference (~0.5s)
    - High quality 70B parameter model
    - OpenAI-compatible API
    - Streaming support
    - Tool calling support
    """

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize Groq provider

        Args:
            api_key: Groq API key (or set GROQ_API_KEY env var)
        """
        # Get API key from environment if not provided
        api_key = api_key or os.getenv("GROQ_API_KEY")
        
        # Get model from environment or use default
        model_name = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")

        config = ProviderConfig(
            name="Groq (Llama 3.3 70B)",
            enabled=bool(api_key),  # Only enable if API key is set
            cost_per_1m_input_tokens=0.0,  # Free tier
            cost_per_1m_output_tokens=0.0,
            avg_latency_seconds=0.5,  # Super fast!
            supports_reasoning=False,  # Fast general-purpose, not specialized reasoning
            supports_streaming=True,
            supports_tools=True,  # Groq supports function calling
            is_free=True,
            requests_per_minute=100,  # Burst capacity
            requests_per_day=14400,
            tokens_per_month=None,  # No monthly token limit, just rate limits
            api_key=api_key,
            base_url="https://api.groq.com/openai/v1",
            model_name=model_name,
            health_check_url="https://api.groq.com/openai/v1/models"
        )

        super().__init__(config)

        self.api_key = api_key
        self.base_url = config.base_url
        self.model = config.model_name

        if not self.api_key:
            logger.warning(
                "Groq API key not set. "
                "Set GROQ_API_KEY environment variable to enable."
            )
        
        if os.getenv("GROQ_MODEL"):
            logger.info(f"Groq provider initialized with custom model from env: {model_name}")

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
        Generate completion using Groq

        Args:
            messages: Chat messages in OpenAI format
            temperature: Sampling temperature (0.0-2.0)
            max_tokens: Maximum tokens to generate
            stream: Whether to stream the response
            tools: Tool definitions for function calling
            **kwargs: Additional parameters

        Returns:
            CompletionResult or AsyncGenerator for streaming

        Raises:
            ProviderError: If request fails
            RateLimitError: If rate limit exceeded
        """
        if not self.api_key:
            raise ProviderError("Groq API key not configured")

        # Build request payload
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": stream
        }

        # Add tools if provided
        if tools:
            payload["tools"] = tools
            payload["tool_choice"] = "auto"

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    json=payload,
                    headers=headers
                )

                # Check for rate limiting
                if response.status_code == 429:
                    retry_after = response.headers.get("Retry-After", "60")
                    raise RateLimitError(
                        f"Groq rate limit exceeded. Retry after {retry_after}s"
                    )

                # Check for other errors
                if response.status_code != 200:
                    error_msg = response.text
                    try:
                        error_data = response.json()
                        error_msg = error_data.get("error", {}).get("message", error_msg)
                    except:
                        pass

                    raise ProviderError(
                        f"Groq API error ({response.status_code}): {error_msg}"
                    )

                data = response.json()

                if stream:
                    # Streaming not implemented in this version
                    raise ProviderError("Streaming not yet implemented for Groq")

                # Extract completion
                choice = data["choices"][0]
                message = choice["message"]
                content = message.get("content", "")
                tool_calls = message.get("tool_calls")

                # Extract usage stats
                usage = data.get("usage", {})
                tokens_input = usage.get("prompt_tokens", 0)
                tokens_output = usage.get("completion_tokens", 0)

                # Calculate cost (free tier = $0)
                cost = self.estimate_cost(tokens_input, tokens_output)

                # Parse tool calls if present
                parsed_tool_calls = None
                if tool_calls:
                    parsed_tool_calls = [
                        {
                            "id": tc.get("id"),
                            "type": tc.get("type"),
                            "function": {
                                "name": tc["function"]["name"],
                                "arguments": tc["function"]["arguments"]
                            }
                        }
                        for tc in tool_calls
                    ]

                return CompletionResult(
                    content=content or "",  # May be empty if tool calls present
                    provider=self.name,
                    model=self.model,
                    selection_reason="",  # Will be filled by router
                    latency=0.0,  # Will be measured by base class
                    tokens_input=tokens_input,
                    tokens_output=tokens_output,
                    cost=cost,
                    cached=False,
                    tool_calls=parsed_tool_calls,
                    finish_reason=choice.get("finish_reason"),
                    metadata={
                        "model": data.get("model"),
                        "id": data.get("id"),
                        "created": data.get("created")
                    }
                )

        except httpx.TimeoutException:
            raise ProviderError("Groq request timed out after 30s")
        except httpx.HTTPError as e:
            raise ProviderError(f"Groq HTTP error: {e}")
        except Exception as e:
            raise ProviderError(f"Groq completion failed: {e}")

    async def check_health(self) -> bool:
        """
        Check if Groq is healthy

        Returns:
            True if healthy, False otherwise
        """
        if not self.api_key:
            return False

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    self.config.health_check_url,
                    headers={"Authorization": f"Bearer {self.api_key}"}
                )

                return response.status_code == 200

        except Exception as e:
            logger.warning(f"Groq health check failed: {e}")
            return False

    def get_available_models(self) -> List[Dict]:
        """
        Get list of available Groq models

        Returns:
            List of supported models with metadata
        """
        return [
            {
                "name": "llama-3.3-70b-versatile",
                "default": True,
                "description": "Llama 3.3 70B - Ultra-fast, versatile (default)"
            },
            {
                "name": "llama-3.1-70b-versatile",
                "default": False,
                "description": "Llama 3.1 70B - Versatile, high quality"
            },
            {
                "name": "llama-3.1-8b-instant",
                "default": False,
                "description": "Llama 3.1 8B - Instant, efficient"
            },
            {
                "name": "mixtral-8x7b-32768",
                "default": False,
                "description": "Mixtral 8x7B - Large context window"
            },
            {
                "name": "gemma2-9b-it",
                "default": False,
                "description": "Gemma 2 9B - Instruction tuned"
            }
        ]

    def set_model(self, model_name: str) -> None:
        """
        Change the Groq model

        Args:
            model_name: Name of the Groq model to use
        """
        self.model = model_name
        self.config.model_name = model_name
        logger.info(f"Groq provider switched to model: {model_name}")

    def __repr__(self):
        status = "✓" if self.is_healthy else "✗"
        enabled = "enabled" if self.config.enabled else "disabled"
        return (
            f"{status} Groq (Llama 3.3 70B) - {enabled} "
            f"({self.stats.requests_made} reqs, ${self.stats.total_cost:.4f})"
        )
