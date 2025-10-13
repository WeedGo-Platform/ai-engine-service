"""
LLM Router - Intelligent Multi-Provider Orchestration

Routes requests to the best available LLM provider based on:
- Cost optimization (free tiers prioritized)
- Rate limit tracking (prevent quota exhaustion)
- Health monitoring (automatic failover)
- Task requirements (reasoning vs speed)
- Latency optimization (fastest provider for task)
"""

import asyncio
import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime

from .types import (
    RequestContext,
    CompletionResult,
    ProviderConfig,
    TaskType,
    AllProvidersExhaustedError
)
from .providers.base import BaseProvider

logger = logging.getLogger(__name__)


class LLMRouter:
    """
    Intelligent LLM provider router with automatic failover

    Features:
    - Multi-factor provider scoring
    - Automatic failover when providers exhausted
    - Cost tracking and optimization
    - Rate limit enforcement
    - Health monitoring

    Usage:
        router = LLMRouter()
        router.register_provider(openrouter_provider)
        router.register_provider(groq_provider)

        result = await router.complete(
            messages=[{"role": "user", "content": "Hello"}],
            context=RequestContext(task_type=TaskType.CHAT, estimated_tokens=100)
        )
    """

    def __init__(self):
        """Initialize the LLM router"""
        self.providers: Dict[str, BaseProvider] = {}
        self.total_requests = 0
        self.total_cost = 0.0
        self.request_history: List[Dict] = []

        logger.info("LLMRouter initialized")

    def register_provider(self, provider: BaseProvider) -> None:
        """
        Register a provider with the router

        Args:
            provider: Provider instance to register
        """
        if not provider.is_enabled:
            logger.warning(f"Skipping disabled provider: {provider.name}")
            return

        self.providers[provider.name] = provider
        logger.info(f"Registered provider: {provider.name}")

    def unregister_provider(self, provider_name: str) -> None:
        """
        Unregister a provider from the router

        Args:
            provider_name: Name of provider to remove
        """
        if provider_name in self.providers:
            del self.providers[provider_name]
            logger.info(f"Unregistered provider: {provider_name}")

    async def complete(
        self,
        messages: List[Dict],
        context: RequestContext,
        max_retries: int = 3
    ) -> CompletionResult:
        """
        Generate completion using best available provider

        Args:
            messages: Chat messages in OpenAI format
            context: Request context with task requirements
            max_retries: Maximum number of providers to try

        Returns:
            CompletionResult with response and metadata

        Raises:
            AllProvidersExhaustedError: If all providers fail
        """
        if not self.providers:
            raise AllProvidersExhaustedError("No providers registered")

        self.total_requests += 1
        attempted_providers = []

        for attempt in range(max_retries):
            try:
                # Score and select best provider
                provider, selection_reason = await self._select_provider(
                    context,
                    exclude=attempted_providers
                )

                if not provider:
                    raise AllProvidersExhaustedError(
                        f"No available providers (tried {len(attempted_providers)})"
                    )

                attempted_providers.append(provider.name)

                logger.info(
                    f"Attempt {attempt + 1}/{max_retries}: "
                    f"Selected {provider.name} - {selection_reason}"
                )

                # Generate completion
                result = await provider.complete_with_retry(
                    messages=messages,
                    temperature=context.temperature,
                    max_tokens=context.max_tokens,
                    stream=context.requires_streaming,
                    tools=context.tools
                )

                # Update router statistics
                self.total_cost += result.cost
                self._record_request(provider.name, result, selection_reason)

                logger.info(
                    f"✓ Success: {provider.name} - "
                    f"{result.tokens_input}→{result.tokens_output} tokens, "
                    f"${result.cost:.6f}, {result.latency:.2f}s"
                )

                return result

            except Exception as e:
                logger.warning(
                    f"Provider {provider.name if provider else 'unknown'} failed: {e}"
                )

                if attempt == max_retries - 1:
                    # Last attempt failed
                    raise AllProvidersExhaustedError(
                        f"All providers exhausted after {max_retries} attempts: "
                        f"Tried {', '.join(attempted_providers)}"
                    )

                # Continue to next provider
                continue

        raise AllProvidersExhaustedError("Maximum retries exceeded")

    async def _select_provider(
        self,
        context: RequestContext,
        exclude: Optional[List[str]] = None
    ) -> Tuple[Optional[BaseProvider], str]:
        """
        Select best provider based on scoring algorithm

        Args:
            context: Request context
            exclude: List of provider names to exclude

        Returns:
            Tuple of (provider, selection_reason)
        """
        exclude = exclude or []
        scored_providers = []

        # Score all available providers
        for provider in self.providers.values():
            if provider.name in exclude:
                continue

            score, reason = self._score_provider(provider, context)
            scored_providers.append((score, reason, provider))

        if not scored_providers:
            return None, "No providers available"

        # Sort by score (highest first)
        scored_providers.sort(reverse=True, key=lambda x: x[0])

        # Select best provider with non-zero score
        for score, reason, provider in scored_providers:
            if score > 0:
                return provider, f"score={score:.1f} ({reason})"

        # No providers with positive score
        return None, "All providers exhausted or rate limited"

    def _score_provider(
        self,
        provider: BaseProvider,
        context: RequestContext
    ) -> Tuple[float, str]:
        """
        Score a provider based on multiple factors

        Scoring algorithm:
        - Cost (0-30 points): Free tiers prioritized
        - Health (±30 points): Recent error tracking
        - Latency (0-10 points): Faster is better
        - Task Match (0-15 points): Reasoning/speed requirements
        - Environment (0-20 points): Dev vs production preference
        - Capabilities (0-10 points): Tools, streaming support

        Args:
            provider: Provider to score
            context: Request context

        Returns:
            Tuple of (score, reason_string)
        """
        score = 50.0  # Base score
        reasons = []

        # Factor 1: Cost (0-30 points)
        if provider.config.is_free:
            score += 30
            reasons.append("FREE")
        else:
            # Penalize paid providers
            cost = provider.config.cost_per_1m_input_tokens
            penalty = min(30, cost * 10)  # Scale penalty by cost
            score -= penalty
            reasons.append(f"PAID(${cost:.2f}/1M)")

        # Factor 2: Health (±30 points)
        if provider.is_healthy:
            score += 10
        else:
            score -= 30
            reasons.append("UNHEALTHY")
            return (0, ", ".join(reasons))  # Immediately disqualify unhealthy

        # Factor 3: Latency (0-10 points)
        latency = provider.config.avg_latency_seconds
        if latency < 1.0:
            score += 10
            reasons.append("FAST")
        elif latency < 2.0:
            score += 5
        elif latency > 4.0:
            score -= 5
            reasons.append("SLOW")

        # Factor 4: Task suitability (0-15 points)
        if context.requires_reasoning and provider.config.supports_reasoning:
            score += 15
            reasons.append("REASONING")

        if context.requires_speed and latency < 1.0:
            score += 15
            reasons.append("SPEED_OPT")

        # Factor 5: Environment preference (0-20 points)
        if not context.is_production and "Local" in provider.name:
            score += 20
            reasons.append("DEV_PREFERRED")

        # Factor 6: Capabilities (0-10 points)
        if context.requires_tools and provider.config.supports_tools:
            score += 10
            reasons.append("TOOLS")

        if context.requires_streaming and provider.config.supports_streaming:
            score += 5
            reasons.append("STREAMING")

        # Factor 7: Rate limits (binary - 0 or disqualify)
        # Note: Rate limit checking will be added in storage module
        # For now, we assume providers track their own limits

        reason_str = ", ".join(reasons) if reasons else "AVAILABLE"
        return (score, reason_str)

    def _record_request(
        self,
        provider_name: str,
        result: CompletionResult,
        selection_reason: str
    ) -> None:
        """
        Record request for analytics

        Args:
            provider_name: Name of provider used
            result: Completion result
            selection_reason: Why this provider was selected
        """
        record = {
            "timestamp": datetime.now(),
            "provider": provider_name,
            "model": result.model,
            "tokens_input": result.tokens_input,
            "tokens_output": result.tokens_output,
            "cost": result.cost,
            "latency": result.latency,
            "selection_reason": selection_reason,
            "cached": result.cached
        }

        # Keep last 1000 requests
        self.request_history.append(record)
        if len(self.request_history) > 1000:
            self.request_history.pop(0)

    def get_stats(self) -> Dict:
        """
        Get router statistics

        Returns:
            Dictionary with router stats and per-provider breakdown
        """
        stats = {
            "total_requests": self.total_requests,
            "total_cost": round(self.total_cost, 4),
            "providers_registered": len(self.providers),
            "providers": {}
        }

        # Add per-provider stats
        for name, provider in self.providers.items():
            stats["providers"][name] = provider.get_stats_summary()

        # Add request distribution
        if self.request_history:
            provider_counts = {}
            for record in self.request_history:
                provider = record["provider"]
                provider_counts[provider] = provider_counts.get(provider, 0) + 1

            stats["request_distribution"] = provider_counts

        return stats

    def get_provider(self, name: str) -> Optional[BaseProvider]:
        """
        Get provider by name

        Args:
            name: Provider name

        Returns:
            Provider instance or None
        """
        return self.providers.get(name)

    def list_providers(self) -> List[str]:
        """
        List all registered provider names

        Returns:
            List of provider names
        """
        return list(self.providers.keys())

    async def health_check(self) -> Dict:
        """
        Check health of all providers

        Returns:
            Dictionary with health status per provider
        """
        health_status = {}

        for name, provider in self.providers.items():
            try:
                is_healthy = await provider.check_health()
                health_status[name] = {
                    "healthy": is_healthy,
                    "enabled": provider.is_enabled,
                    "consecutive_failures": provider.health.consecutive_failures,
                    "last_check": datetime.now().isoformat()
                }
            except Exception as e:
                health_status[name] = {
                    "healthy": False,
                    "enabled": provider.is_enabled,
                    "error": str(e),
                    "last_check": datetime.now().isoformat()
                }

        return health_status

    def __repr__(self):
        return (
            f"LLMRouter("
            f"providers={len(self.providers)}, "
            f"requests={self.total_requests}, "
            f"cost=${self.total_cost:.4f})"
        )
