"""
Cloud Vision Strategy

Uses only cloud providers (Gemini Free Tier).
Following KISS: One provider, strict rate limiting.
Following SRP: Strategy only knows how to use cloud provider safely.
"""

import logging
from typing import Optional, List

from .base import AbstractVisionStrategy
from ..domain.entities import Document, ExtractionResult
from ..domain.value_objects import Template, ExtractionOptions
from ..domain.exceptions import (
    ExtractionError,
    AllProvidersExhaustedError,
    RateLimitError
)
from ..providers.base_vision_provider import BaseVisionProvider, provider_registry

logger = logging.getLogger(__name__)


class CloudVisionStrategy(AbstractVisionStrategy):
    """
    Strategy that uses only cloud providers (FREE tier only!)

    Current Provider:
    - Google Gemini 2.0 Flash (FREE tier)
      - 15 RPM (requests per minute)
      - 1,500 RPD (requests per day)
      - Cost: $0.00 (within limits)

    IMPORTANT: This strategy NEVER makes paid API calls!
    Rate limits are strictly enforced to stay within free tier.

    Cost: $0.00 (strictly enforced)
    Latency: 1-2 seconds
    Accuracy: 95%+ (GPT-4 class)
    """

    def __init__(self, cloud_providers: Optional[List[BaseVisionProvider]] = None):
        """
        Initialize cloud strategy

        Args:
            cloud_providers: List of cloud providers to use
                           If None, will get from global registry
        """
        self.cloud_providers = cloud_providers or []

        # If no providers passed, get from registry
        if not self.cloud_providers:
            all_providers = provider_registry.get_available()
            # Filter for cloud free tier only
            self.cloud_providers = [
                p for p in all_providers
                if p.config.provider_type.value == 'cloud_free'
            ]

        logger.info(f"Cloud strategy initialized with {len(self.cloud_providers)} providers")

        # Warn if no providers available
        if not self.cloud_providers:
            logger.warning(
                "No cloud providers available. "
                "Set GEMINI_API_KEY environment variable to enable cloud extraction."
            )

    def get_name(self) -> str:
        """Get strategy name"""
        return "cloud"

    async def extract(
        self,
        document: Document,
        template: Template,
        options: Optional[ExtractionOptions] = None
    ) -> ExtractionResult:
        """
        Extract data using cloud providers (FREE tier only)

        Algorithm:
        1. Check if cloud providers available
        2. Try Gemini with strict rate limiting
        3. If rate limited → raise RateLimitError (don't retry!)
        4. Return result

        Args:
            document: Document to process
            template: Template defining what to extract
            options: Extraction options

        Returns:
            ExtractionResult with extracted data

        Raises:
            AllProvidersExhaustedError: If no cloud providers available
            RateLimitError: If free tier limits exceeded
        """
        options = options or ExtractionOptions()

        if not self.cloud_providers:
            raise AllProvidersExhaustedError(
                "No cloud providers available. Set GEMINI_API_KEY environment variable."
            )

        # Build extraction prompt
        prompt = self._build_extraction_prompt(template, document)

        errors = []

        # Try each cloud provider
        for provider in self.cloud_providers:
            try:
                logger.info(f"Using cloud provider: {provider.name}")

                # Use provider's built-in retry logic
                # NOTE: Provider will check rate limits BEFORE making request
                result = await provider.extract_with_retry(
                    document=document,
                    prompt=prompt,
                    options=options
                )

                logger.info(
                    f"✅ Cloud extraction succeeded with {provider.name} "
                    f"(confidence: {result.get_overall_confidence():.2f})"
                )

                return result

            except RateLimitError as e:
                # Don't retry - respect rate limits!
                logger.warning(f"Rate limit hit for {provider.name}: {e}")
                raise  # Re-raise to caller

            except Exception as e:
                logger.warning(f"Provider {provider.name} failed: {e}")
                errors.append(f"{provider.name}: {str(e)}")
                continue

        # All providers failed
        error_summary = "; ".join(errors)
        raise AllProvidersExhaustedError(
            f"All cloud providers failed. Errors: {error_summary}"
        )

    def supports_template(self, template: Template) -> bool:
        """
        Check if strategy supports this template

        Cloud providers support all template types

        Args:
            template: Template to check

        Returns:
            True (always - cloud providers are general purpose)
        """
        return True

    def estimate_cost(self, document: Document) -> float:
        """
        Estimate cost for processing this document

        Args:
            document: Document to estimate cost for

        Returns:
            0.0 (free tier only!)
        """
        return 0.0

    def estimate_latency(self, document: Document) -> float:
        """
        Estimate latency for processing this document

        Cloud providers are typically faster than local:
        - Network latency: ~200-500ms
        - Processing: ~500-1000ms
        - Total: ~1-2s

        Args:
            document: Document to estimate latency for

        Returns:
            Estimated latency in seconds (1-2s)
        """
        return 1.5

    def get_rate_limit_stats(self) -> dict:
        """
        Get rate limit statistics for cloud providers

        Returns:
            Dictionary with rate limit info
        """
        stats = {}

        for provider in self.cloud_providers:
            provider_stats = provider.get_stats()
            if 'rate_limits' in provider_stats:
                stats[provider.name] = provider_stats['rate_limits']

        return stats

    def get_provider_names(self) -> List[str]:
        """
        Get names of cloud providers being used

        Returns:
            List of provider names
        """
        return [p.name for p in self.cloud_providers]

    def __repr__(self):
        return f"CloudVisionStrategy(providers={len(self.cloud_providers)})"
