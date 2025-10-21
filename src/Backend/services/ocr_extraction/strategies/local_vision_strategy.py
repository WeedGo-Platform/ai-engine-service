"""
Local Vision Strategy

Uses only local providers (Ollama, Hugging Face).
Following KISS: Try fastest first, fallback to alternatives.
Following SRP: Strategy only knows how to orchestrate local providers.
"""

import logging
from typing import Optional, List

from .base import AbstractVisionStrategy
from ..domain.entities import Document, ExtractionResult
from ..domain.value_objects import Template, ExtractionOptions
from ..domain.exceptions import (
    ExtractionError,
    AllProvidersExhaustedError
)
from ..providers.base_vision_provider import BaseVisionProvider, provider_registry

logger = logging.getLogger(__name__)


class LocalVisionStrategy(AbstractVisionStrategy):
    """
    Strategy that uses only local providers

    Priority:
    1. Ollama (fastest: 2-3s)
    2. Hugging Face (slower: 4-6s, but more accurate for docs)

    Cost: $0.00 (completely free, unlimited)
    Latency: 2-6 seconds
    Accuracy: 85-95% (depending on model)
    """

    def __init__(self, local_providers: Optional[List[BaseVisionProvider]] = None):
        """
        Initialize local strategy

        Args:
            local_providers: List of local providers to use
                           If None, will get from global registry
        """
        self.local_providers = local_providers or []

        # If no providers passed, get from registry
        if not self.local_providers:
            all_providers = provider_registry.get_available()
            # Filter for local only
            self.local_providers = [
                p for p in all_providers
                if p.config.provider_type.value.startswith('local_')
            ]

        logger.info(f"Local strategy initialized with {len(self.local_providers)} providers")

    def get_name(self) -> str:
        """Get strategy name"""
        return "local"

    async def extract(
        self,
        document: Document,
        template: Template,
        options: Optional[ExtractionOptions] = None
    ) -> ExtractionResult:
        """
        Extract data using local providers only

        Algorithm:
        1. Sort providers by latency (fastest first)
        2. Try each provider in order
        3. Return first successful result
        4. If all fail → raise AllProvidersExhaustedError

        Args:
            document: Document to process
            template: Template defining what to extract
            options: Extraction options

        Returns:
            ExtractionResult with extracted data

        Raises:
            AllProvidersExhaustedError: If all local providers fail
        """
        options = options or ExtractionOptions()

        if not self.local_providers:
            raise AllProvidersExhaustedError(
                attempted_providers=[],
                last_error="No local providers available. Install Ollama or download HF models."
            )

        # Sort by estimated latency (fastest first)
        sorted_providers = sorted(
            self.local_providers,
            key=lambda p: self.estimate_latency(document)
        )

        # Build extraction prompt
        prompt = self._build_extraction_prompt(template, document)

        errors = []

        # Try each provider
        for provider in sorted_providers:
            try:
                logger.info(f"Trying local provider: {provider.name}")

                # Use provider's built-in retry logic
                result = await provider.extract_with_retry(
                    document=document,
                    prompt=prompt,
                    options=options
                )

                logger.info(
                    f"✅ Local extraction succeeded with {provider.name} "
                    f"(confidence: {result.get_overall_confidence():.2f})"
                )

                return result

            except Exception as e:
                logger.warning(f"Provider {provider.name} failed: {e}")
                errors.append(f"{provider.name}: {str(e)}")
                continue

        # All providers failed
        attempted_names = [p.name for p in sorted_providers]
        error_summary = "; ".join(errors)
        raise AllProvidersExhaustedError(
            attempted_providers=attempted_names,
            last_error=error_summary
        )

    def supports_template(self, template: Template) -> bool:
        """
        Check if strategy supports this template

        Local providers support all template types

        Args:
            template: Template to check

        Returns:
            True (always - local providers are general purpose)
        """
        return True

    def estimate_cost(self, document: Document) -> float:
        """
        Estimate cost for processing this document

        Args:
            document: Document to estimate cost for

        Returns:
            0.0 (local processing is free!)
        """
        return 0.0

    def estimate_latency(self, document: Document) -> float:
        """
        Estimate latency for processing this document

        Latency depends on:
        - Model size (larger = slower)
        - Device (GPU vs CPU)
        - Image size

        Args:
            document: Document to estimate latency for

        Returns:
            Estimated latency in seconds (2-6s)
        """
        if not self.local_providers:
            return 10.0  # Default if no providers

        # Use fastest provider's latency
        # Ollama: ~2-3s, HuggingFace: ~4-6s
        latencies = []

        for provider in self.local_providers:
            # Estimate based on provider type
            if 'ollama' in provider.name.lower():
                latencies.append(2.5)
            elif 'huggingface' in provider.name.lower():
                # HF varies by device
                if hasattr(provider, 'device') and provider.device == 'cuda':
                    latencies.append(4.0)
                else:
                    latencies.append(6.0)
            else:
                latencies.append(5.0)  # Default

        return min(latencies) if latencies else 5.0

    def get_provider_names(self) -> List[str]:
        """
        Get names of local providers being used

        Returns:
            List of provider names
        """
        return [p.name for p in self.local_providers]

    def __repr__(self):
        return f"LocalVisionStrategy(providers={len(self.local_providers)})"
