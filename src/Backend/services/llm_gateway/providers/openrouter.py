"""
OpenRouter Provider - DeepSeek R1 (Free Tier)

OpenRouter provides access to DeepSeek R1 reasoning model with free tier:
- 200 requests/day
- Excellent reasoning capabilities
- ~2s average latency
- OpenAI-compatible API

Docs: https://openrouter.ai/docs
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


class OpenRouterProvider(BaseProvider):
    """
    OpenRouter provider using DeepSeek R1 model

    Free tier limits:
    - 200 requests/day
    - 20 requests/minute
    - No token limits

    Features:
    - Excellent reasoning capabilities
    - OpenAI-compatible API
    - Streaming support
    """

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize OpenRouter provider

        Args:
            api_key: OpenRouter API key (or set OPENROUTER_API_KEY env var)
        """
        # Get API key from environment if not provided
        api_key = api_key or os.getenv("OPENROUTER_API_KEY")

        config = ProviderConfig(
            name="OpenRouter (DeepSeek R1)",
            enabled=bool(api_key),  # Only enable if API key is set
            cost_per_1m_input_tokens=0.0,  # Free tier
            cost_per_1m_output_tokens=0.0,
            avg_latency_seconds=2.0,
            supports_reasoning=True,
            supports_streaming=True,
            supports_tools=False,  # DeepSeek R1 free tier doesn't support tools
            is_free=True,
            requests_per_minute=20,
            requests_per_day=200,
            api_key=api_key,
            base_url="https://openrouter.ai/api/v1",
            model_name="deepseek/deepseek-r1-distill-llama-70b:free",
            health_check_url="https://openrouter.ai/api/v1/models"
        )

        super().__init__(config)

        self.api_key = api_key
        self.base_url = config.base_url
        self.model = config.model_name

        if not self.api_key:
            logger.warning(
                "OpenRouter API key not set. "
                "Set OPENROUTER_API_KEY environment variable to enable."
            )

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
        Generate completion using OpenRouter

        Args:
            messages: Chat messages in OpenAI format
            temperature: Sampling temperature (0.0-2.0)
            max_tokens: Maximum tokens to generate
            stream: Whether to stream the response
            tools: Tool definitions (not supported in free tier)
            **kwargs: Additional parameters

        Returns:
            CompletionResult or AsyncGenerator for streaming

        Raises:
            ProviderError: If request fails
            RateLimitError: If rate limit exceeded
        """
        if not self.api_key:
            raise ProviderError("OpenRouter API key not configured")

        if tools:
            logger.warning("OpenRouter free tier does not support tool calling")

        # Build request payload
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": stream
        }

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "HTTP-Referer": "https://weedgo.app",  # Optional but recommended
            "X-Title": "WeedGo AI Budtender",  # Optional but recommended
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
                        f"OpenRouter rate limit exceeded. Retry after {retry_after}s"
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
                        f"OpenRouter API error ({response.status_code}): {error_msg}"
                    )

                data = response.json()

                if stream:
                    # Streaming not implemented in this version
                    raise ProviderError("Streaming not yet implemented for OpenRouter")

                # Extract completion
                choice = data["choices"][0]
                message = choice["message"]
                content = message.get("content", "")

                # DeepSeek R1 puts response in 'reasoning' field
                reasoning = message.get("reasoning", "")
                if reasoning and not content:
                    content = reasoning
                elif reasoning and content:
                    # Both exist - combine them
                    content = f"{reasoning}\n\n{content}"

                # Extract usage stats
                usage = data.get("usage", {})
                tokens_input = usage.get("prompt_tokens", 0)
                tokens_output = usage.get("completion_tokens", 0)

                # Calculate cost (free tier = $0)
                cost = self.estimate_cost(tokens_input, tokens_output)

                return CompletionResult(
                    content=content,
                    provider=self.name,
                    model=self.model,
                    selection_reason="",  # Will be filled by router
                    latency=0.0,  # Will be measured by base class
                    tokens_input=tokens_input,
                    tokens_output=tokens_output,
                    cost=cost,
                    cached=False,
                    finish_reason=choice.get("finish_reason"),
                    metadata={
                        "model": data.get("model"),
                        "id": data.get("id")
                    }
                )

        except httpx.TimeoutException:
            raise ProviderError("OpenRouter request timed out after 60s")
        except httpx.HTTPError as e:
            raise ProviderError(f"OpenRouter HTTP error: {e}")
        except Exception as e:
            raise ProviderError(f"OpenRouter completion failed: {e}")

    async def check_health(self) -> bool:
        """
        Check if OpenRouter is healthy

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
            logger.warning(f"OpenRouter health check failed: {e}")
            return False

    def __repr__(self):
        status = "✓" if self.is_healthy else "✗"
        enabled = "enabled" if self.config.enabled else "disabled"
        return (
            f"{status} OpenRouter (DeepSeek R1) - {enabled} "
            f"({self.stats.requests_made} reqs, ${self.stats.total_cost:.4f})"
        )
