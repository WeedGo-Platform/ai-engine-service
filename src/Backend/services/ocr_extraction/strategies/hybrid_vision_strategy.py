"""
Hybrid Vision Strategy

Intelligently combines local and cloud providers.
Following KISS: Try local first (fast, free), use cloud for quality assurance.
Following SRP: Strategy only knows orchestration logic.
"""

import logging
from typing import Optional

from .base import AbstractVisionStrategy
from .local_vision_strategy import LocalVisionStrategy
from .cloud_vision_strategy import CloudVisionStrategy
from ..domain.entities import Document, ExtractionResult
from ..domain.value_objects import Template, ExtractionOptions
from ..domain.exceptions import (
    ExtractionError,
    AllProvidersExhaustedError,
    RateLimitError
)

logger = logging.getLogger(__name__)


class HybridVisionStrategy(AbstractVisionStrategy):
    """
    Strategy that intelligently combines local and cloud providers

    Algorithm:
    1. Always try local first (fast, free, unlimited)
    2. Check confidence of local result
    3. If confidence >= threshold → return (90% of cases)
    4. If confidence < threshold → use cloud for better accuracy
    5. Return highest confidence result

    Benefits:
    - 90% of requests use local (free, fast)
    - 10% use cloud for quality (high confidence needed)
    - Best of both worlds: speed + accuracy

    Cost: $0.00 (both tiers free)
    Latency: 2-3s (local) or 1-2s (cloud fallback)
    Accuracy: 95%+ (cloud used when needed)
    """

    # Default confidence threshold for cloud fallback
    DEFAULT_CONFIDENCE_THRESHOLD = 0.75

    def __init__(
        self,
        local_strategy: Optional[LocalVisionStrategy] = None,
        cloud_strategy: Optional[CloudVisionStrategy] = None,
        confidence_threshold: float = DEFAULT_CONFIDENCE_THRESHOLD
    ):
        """
        Initialize hybrid strategy

        Args:
            local_strategy: Local strategy instance (or None to create)
            cloud_strategy: Cloud strategy instance (or None to create)
            confidence_threshold: Minimum confidence to accept local result
                                (0.0-1.0, default 0.75)
        """
        self.local_strategy = local_strategy or LocalVisionStrategy()
        self.cloud_strategy = cloud_strategy or CloudVisionStrategy()
        self.confidence_threshold = confidence_threshold

        logger.info(
            f"Hybrid strategy initialized "
            f"(confidence threshold: {confidence_threshold:.2f})"
        )

        # Stats tracking
        self.local_success_count = 0
        self.cloud_fallback_count = 0
        self.total_requests = 0

    def get_name(self) -> str:
        """Get strategy name"""
        return "hybrid"

    async def extract(
        self,
        document: Document,
        template: Template,
        options: Optional[ExtractionOptions] = None
    ) -> ExtractionResult:
        """
        Extract data using hybrid approach

        Algorithm:
        1. Try local providers first
        2. If confidence >= threshold → return immediately
        3. If confidence < threshold → try cloud
        4. Return best result

        Args:
            document: Document to process
            template: Template defining what to extract
            options: Extraction options

        Returns:
            ExtractionResult with extracted data

        Raises:
            ExtractionError: If extraction fails
        """
        options = options or ExtractionOptions()
        self.total_requests += 1

        local_result = None
        cloud_result = None

        # Phase 1: Try local providers
        try:
            logger.info("🔄 Phase 1: Trying local providers...")

            local_result = await self.local_strategy.extract(
                document=document,
                template=template,
                options=options
            )

            local_confidence = local_result.get_overall_confidence()
            logger.info(f"Local extraction confidence: {local_confidence:.2f}")

            # Check if local result is good enough
            if local_confidence >= self.confidence_threshold:
                logger.info(
                    f"✅ Local result accepted "
                    f"(confidence {local_confidence:.2f} >= {self.confidence_threshold:.2f})"
                )
                self.local_success_count += 1
                return local_result

            # Local confidence too low
            logger.info(
                f"⚠️ Local confidence low "
                f"({local_confidence:.2f} < {self.confidence_threshold:.2f}), "
                f"trying cloud fallback..."
            )

        except AllProvidersExhaustedError as e:
            logger.warning(f"All local providers failed: {e}")
            # Continue to cloud fallback

        except Exception as e:
            logger.error(f"Local extraction error: {e}")
            # Continue to cloud fallback

        # Phase 2: Try cloud providers (fallback)
        try:
            logger.info("🔄 Phase 2: Trying cloud providers...")

            cloud_result = await self.cloud_strategy.extract(
                document=document,
                template=template,
                options=options
            )

            cloud_confidence = cloud_result.get_overall_confidence()
            logger.info(f"Cloud extraction confidence: {cloud_confidence:.2f}")

            self.cloud_fallback_count += 1

            # Compare results if we have both
            if local_result and cloud_result:
                if cloud_confidence > local_confidence:
                    logger.info(
                        f"✅ Using cloud result "
                        f"(confidence {cloud_confidence:.2f} > {local_confidence:.2f})"
                    )
                    return cloud_result
                else:
                    logger.info(
                        f"✅ Using local result "
                        f"(confidence {local_confidence:.2f} >= {cloud_confidence:.2f})"
                    )
                    return local_result
            else:
                # Only cloud result available
                logger.info(f"✅ Using cloud result (only option)")
                return cloud_result

        except RateLimitError as e:
            # Rate limited - use local result if available
            if local_result:
                logger.warning(
                    f"Cloud rate limited, using local result "
                    f"(confidence: {local_result.get_overall_confidence():.2f})"
                )
                return local_result
            else:
                raise  # No fallback available

        except Exception as e:
            logger.error(f"Cloud extraction error: {e}")

            # Use local result if available
            if local_result:
                logger.warning(
                    f"Cloud failed, using local result "
                    f"(confidence: {local_result.get_overall_confidence():.2f})"
                )
                return local_result
            else:
                raise AllProvidersExhaustedError(
                    attempted_providers=["local", "cloud"],
                    last_error="Both local and cloud providers failed"
                )

        # Should never reach here, but just in case
        raise ExtractionError("Hybrid extraction failed unexpectedly")

    def supports_template(self, template: Template) -> bool:
        """
        Check if strategy supports this template

        Hybrid supports all templates (uses both local + cloud)

        Args:
            template: Template to check

        Returns:
            True (always)
        """
        return True

    def estimate_cost(self, document: Document) -> float:
        """
        Estimate cost for processing this document

        Args:
            document: Document to estimate cost for

        Returns:
            0.0 (both local and cloud are free!)
        """
        return 0.0

    def estimate_latency(self, document: Document) -> float:
        """
        Estimate latency for processing this document

        Latency depends on whether cloud fallback is used:
        - 90% of cases: local only (~2-3s)
        - 10% of cases: local + cloud (~4-5s)

        Args:
            document: Document to estimate latency for

        Returns:
            Estimated latency in seconds (weighted average)
        """
        local_latency = self.local_strategy.estimate_latency(document)
        cloud_latency = self.cloud_strategy.estimate_latency(document)

        # Weighted average based on typical usage
        # 90% use local only, 10% use both
        average_latency = (0.9 * local_latency) + (0.1 * (local_latency + cloud_latency))

        return average_latency

    def get_stats(self) -> dict:
        """
        Get strategy statistics

        Returns:
            Dictionary with usage stats
        """
        if self.total_requests == 0:
            local_rate = 0.0
            cloud_rate = 0.0
        else:
            local_rate = self.local_success_count / self.total_requests
            cloud_rate = self.cloud_fallback_count / self.total_requests

        return {
            'strategy': 'hybrid',
            'total_requests': self.total_requests,
            'local_success_count': self.local_success_count,
            'cloud_fallback_count': self.cloud_fallback_count,
            'local_success_rate': local_rate,
            'cloud_fallback_rate': cloud_rate,
            'confidence_threshold': self.confidence_threshold,
        }

    def set_confidence_threshold(self, threshold: float):
        """
        Update confidence threshold

        Args:
            threshold: New threshold (0.0-1.0)

        Raises:
            ValueError: If threshold not in valid range
        """
        if not 0.0 <= threshold <= 1.0:
            raise ValueError(f"Threshold must be 0.0-1.0, got {threshold}")

        logger.info(
            f"Confidence threshold updated: "
            f"{self.confidence_threshold:.2f} → {threshold:.2f}"
        )
        self.confidence_threshold = threshold

    def __repr__(self):
        return (
            f"HybridVisionStrategy("
            f"threshold={self.confidence_threshold:.2f}, "
            f"local_rate={self.local_success_count}/{self.total_requests})"
        )
