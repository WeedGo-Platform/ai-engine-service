"""
Base Provider Interface

All LLM providers must implement this interface.
"""

import time
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Dict, List, Optional, AsyncGenerator, Union
import logging

from ..types import (
    ProviderConfig,
    ProviderStats,
    ProviderHealth,
    CompletionResult,
    ProviderError,
    RateLimitError
)

logger = logging.getLogger(__name__)


class BaseProvider(ABC):
    """Base class for all LLM providers"""

    def __init__(self, config: ProviderConfig):
        self.config = config
        self.stats = ProviderStats()
        self.health = ProviderHealth()

        logger.info(f"Initialized provider: {config.name}")

    @property
    def name(self) -> str:
        """Get provider name"""
        return self.config.name

    @property
    def is_enabled(self) -> bool:
        """Check if provider is enabled"""
        return self.config.enabled

    @property
    def is_healthy(self) -> bool:
        """Check if provider is healthy"""
        return self.health.is_healthy

    @abstractmethod
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
        Generate completion

        Args:
            messages: List of message dicts with 'role' and 'content'
            temperature: Sampling temperature (0.0-2.0)
            max_tokens: Maximum tokens to generate
            stream: Whether to stream the response
            tools: Optional list of tool definitions for function calling
            **kwargs: Additional provider-specific parameters

        Returns:
            CompletionResult or AsyncGenerator for streaming

        Raises:
            ProviderError: If request fails
            RateLimitError: If rate limit exceeded
        """
        pass

    @abstractmethod
    async def check_health(self) -> bool:
        """
        Check provider health

        Returns:
            True if healthy, False otherwise
        """
        pass

    def estimate_cost(self, tokens_input: int, tokens_output: int) -> float:
        """
        Estimate cost for token usage

        Args:
            tokens_input: Number of input tokens
            tokens_output: Number of output tokens

        Returns:
            Estimated cost in USD
        """
        input_cost = (tokens_input / 1_000_000) * self.config.cost_per_1m_input_tokens
        output_cost = (tokens_output / 1_000_000) * self.config.cost_per_1m_output_tokens
        return input_cost + output_cost

    def record_success(
        self,
        latency: float,
        tokens_input: int,
        tokens_output: int
    ):
        """
        Record successful request

        Args:
            latency: Request latency in seconds
            tokens_input: Input tokens used
            tokens_output: Output tokens generated
        """
        self.stats.requests_made += 1
        self.stats.tokens_input += tokens_input
        self.stats.tokens_output += tokens_output
        self.stats.total_latency += latency
        self.stats.last_used = datetime.now()

        cost = self.estimate_cost(tokens_input, tokens_output)
        self.stats.total_cost += cost

        # Update health
        self.health.is_healthy = True
        self.health.consecutive_failures = 0
        self.health.last_success = datetime.now()

        logger.debug(
            f"{self.name}: Success in {latency:.2f}s, "
            f"{tokens_input}→{tokens_output} tokens, ${cost:.6f}"
        )

    def record_failure(self, error: Exception):
        """
        Record failed request

        Args:
            error: The exception that occurred
        """
        self.stats.errors += 1
        self.stats.last_error = datetime.now()
        self.stats.last_error_message = str(error)

        # Update health
        self.health.consecutive_failures += 1
        self.health.last_failure = datetime.now()
        self.health.last_failure_reason = str(error)

        # Mark unhealthy after 3 consecutive failures
        if self.health.consecutive_failures >= 3:
            self.health.is_healthy = False
            logger.warning(
                f"{self.name}: Marked unhealthy after "
                f"{self.health.consecutive_failures} failures"
            )

        logger.error(f"{self.name}: Request failed - {error}")

    async def complete_with_retry(
        self,
        messages: List[Dict],
        retries: int = 2,
        **kwargs
    ) -> CompletionResult:
        """
        Complete with automatic retry on failure

        Args:
            messages: Chat messages
            retries: Number of retries
            **kwargs: Additional parameters

        Returns:
            CompletionResult

        Raises:
            ProviderError: If all retries exhausted
        """
        last_error = None

        for attempt in range(retries + 1):
            try:
                start_time = time.time()
                result = await self.complete(messages, **kwargs)
                latency = time.time() - start_time

                if isinstance(result, CompletionResult):
                    self.record_success(
                        latency,
                        result.tokens_input,
                        result.tokens_output
                    )
                    return result
                else:
                    # Streaming not supported in retry mode
                    raise ProviderError("Streaming not supported with retry")

            except RateLimitError:
                # Don't retry on rate limit errors
                raise

            except Exception as e:
                last_error = e
                self.record_failure(e)

                if attempt < retries:
                    wait_time = 2 ** attempt  # Exponential backoff
                    logger.info(
                        f"{self.name}: Retry {attempt + 1}/{retries} "
                        f"after {wait_time}s"
                    )
                    await asyncio.sleep(wait_time)
                continue

        # All retries exhausted
        raise ProviderError(f"All retries exhausted: {last_error}")

    def get_stats_summary(self) -> Dict:
        """
        Get provider statistics summary

        Returns:
            Dict with provider stats
        """
        return {
            "name": self.name,
            "enabled": self.is_enabled,
            "healthy": self.is_healthy,
            "requests": self.stats.requests_made,
            "errors": self.stats.errors,
            "error_rate": f"{self.stats.error_rate * 100:.2f}%",
            "tokens_input": self.stats.tokens_input,
            "tokens_output": self.stats.tokens_output,
            "total_cost": f"${self.stats.total_cost:.4f}",
            "avg_latency": f"{self.stats.avg_latency:.2f}s",
            "last_used": self.stats.last_used.isoformat() if self.stats.last_used else None,
            "consecutive_failures": self.health.consecutive_failures
        }

    def __repr__(self):
        status = "✓" if self.is_healthy else "✗"
        return (
            f"{status} {self.name} "
            f"({self.stats.requests_made} reqs, "
            f"${self.stats.total_cost:.4f})"
        )


# Import asyncio here to avoid circular imports
import asyncio
