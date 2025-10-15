"""
LLM7.io Provider - Anonymous Free Access

LLM7.io provides free anonymous access to 30+ LLM models:
- NO account required
- NO API key needed
- 40 requests/minute
- OpenAI-compatible API
- Perfect for instant testing

Docs: https://api.llm7.io/v1
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


class LLM7Provider(BaseProvider):
    """
    LLM7.io provider with anonymous access

    Free tier limits:
    - 40 requests/minute
    - No daily limit
    - No account required
    - No authentication needed

    Features:
    - 30+ models available
    - OpenAI-compatible API
    - Instant access
    - Good for prototyping
    """

    def __init__(self, model_name: str = "gpt-4o-mini"):
        """
        Initialize LLM7 provider

        Args:
            model_name: Model to use (gpt-4o-mini, gpt-4o, claude-3-5-sonnet, etc.)
        """
        # Get model from environment or use provided default
        model_name = os.getenv("LLM7_MODEL", model_name)
        
        config = ProviderConfig(
            name=f"LLM7 ({model_name})",
            enabled=True,  # No API key required - anonymous access
            cost_per_1m_input_tokens=0.0,  # Free tier
            cost_per_1m_output_tokens=0.0,
            avg_latency_seconds=2.5,
            supports_reasoning=model_name.startswith("claude") or model_name.startswith("gpt-4"),
            supports_streaming=True,
            supports_tools=False,
            is_free=True,
            requests_per_minute=40,  # Conservative estimate
            requests_per_day=57600,  # 40 req/min * 60 * 24
            api_key=None,  # No auth required
            base_url="https://llm7.io/v1",
            model_name=model_name,
            health_check_url="https://llm7.io/v1/models"
        )

        super().__init__(config)

        self.base_url = config.base_url
        self.model = config.model_name

        logger.info(f"LLM7 provider initialized with model: {model_name} (NO AUTH REQUIRED)")
        
        if os.getenv("LLM7_MODEL"):
            logger.info(f"LLM7 provider using custom model from env: {model_name}")

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
        Generate completion using LLM7

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
        # Build request payload (OpenAI-compatible)
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

        # NO AUTHORIZATION HEADER NEEDED!
        headers = {
            "Content-Type": "application/json"
        }

        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    json=payload,
                    headers=headers
                )

                # Check for rate limiting
                if response.status_code == 429:
                    retry_after = response.headers.get("Retry-After", "60")
                    raise RateLimitError(
                        f"LLM7 rate limit exceeded (40/min). Retry after {retry_after}s"
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
                        f"LLM7 API error ({response.status_code}): {error_msg}"
                    )

                data = response.json()

                if stream:
                    # Streaming not implemented in this version
                    raise ProviderError("Streaming not yet implemented for LLM7")

                # Extract completion
                choice = data["choices"][0]
                message = choice["message"]
                content = message.get("content", "")
                tool_calls = message.get("tool_calls")

                # Extract usage stats
                usage = data.get("usage", {})
                tokens_input = usage.get("prompt_tokens", 0)
                tokens_output = usage.get("completion_tokens", 0)

                # Calculate cost (free = $0)
                cost = 0.0

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
                    content=content or "",
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
                        "provider": "llm7.io",
                        "anonymous": True
                    }
                )

        except httpx.TimeoutException:
            raise ProviderError("LLM7 request timed out after 60s")
        except httpx.HTTPError as e:
            raise ProviderError(f"LLM7 HTTP error: {e}")
        except Exception as e:
            raise ProviderError(f"LLM7 completion failed: {e}")

    async def check_health(self) -> bool:
        """
        Check if LLM7 is healthy

        Returns:
            True if healthy, False otherwise
        """
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(self.config.health_check_url)
                return response.status_code == 200

        except Exception as e:
            logger.warning(f"LLM7 health check failed: {e}")
            return False

    def get_available_models(self) -> List[Dict]:
        """
        Get list of available LLM7 models

        Returns:
            List of supported models with metadata
        """
        return [
            {
                "name": "gpt-4o-mini",
                "default": True,
                "description": "GPT-4o Mini - Fast, efficient (default)"
            },
            {
                "name": "gpt-4o",
                "default": False,
                "description": "GPT-4o - Most capable OpenAI model"
            },
            {
                "name": "claude-3-5-sonnet-20241022",
                "default": False,
                "description": "Claude 3.5 Sonnet - Anthropic's best"
            },
            {
                "name": "claude-3-5-haiku-20241022",
                "default": False,
                "description": "Claude 3.5 Haiku - Fast Anthropic model"
            },
            {
                "name": "gemini-2.0-flash-exp",
                "default": False,
                "description": "Gemini 2.0 Flash - Google's latest"
            }
        ]

    def set_model(self, model_name: str) -> None:
        """
        Change the LLM7 model

        Args:
            model_name: Name of the model to use
        """
        self.model = model_name
        self.config.model_name = model_name
        logger.info(f"LLM7 provider switched to model: {model_name}")

    def __repr__(self):
        status = "✓" if self.is_healthy else "✗"
        return (
            f"{status} LLM7.io ({self.model}) - anonymous "
            f"({self.stats.requests_made} reqs, ${self.stats.total_cost:.4f})"
        )


# Convenience constructors for popular models
class LLM7GPT4Mini(LLM7Provider):
    """LLM7 with GPT-4o-mini (fast & efficient)"""
    def __init__(self):
        super().__init__(model_name="gpt-4o-mini")


class LLM7GPT4(LLM7Provider):
    """LLM7 with GPT-4o (most capable)"""
    def __init__(self):
        super().__init__(model_name="gpt-4o")


class LLM7Claude(LLM7Provider):
    """LLM7 with Claude 3.5 Sonnet"""
    def __init__(self):
        super().__init__(model_name="claude-3.5-sonnet")
