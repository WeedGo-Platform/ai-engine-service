"""
Base Vision Provider Interface

All vision providers (discovered dynamically) must implement this interface.
No hardcoded provider names - providers register themselves!

Following SRP: Provider only knows how to extract from images.
Following DDD: This is an interface in the domain layer.
"""

import time
import logging
import asyncio
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from datetime import datetime

from ..domain.entities import Document, ExtractionResult, AvailableModel
from ..domain.value_objects import ExtractionOptions, VisionProviderConfig
from ..domain.exceptions import ProviderError, ProviderUnavailableError

logger = logging.getLogger(__name__)


class BaseVisionProvider(ABC):
    """
    Abstract base class for all vision providers

    Providers are discovered at runtime - no hardcoding!
    Each provider knows how to extract from images using its model.
    """

    def __init__(self, config: VisionProviderConfig, model: AvailableModel):
        """
        Initialize provider

        Args:
            config: Provider configuration
            model: Model discovered at runtime
        """
        self.config = config
        self.model = model
        self.is_initialized = False

        # Statistics
        self.total_requests = 0
        self.total_failures = 0
        self.total_latency = 0.0
        self.total_cost = 0.0
        self.last_used = None

        logger.info(f"Provider created: {self.name} ({model.name})")

    @property
    def name(self) -> str:
        """Get provider name (from config)"""
        return self.config.name

    @property
    def is_available(self) -> bool:
        """Check if provider is available and ready"""
        return self.is_initialized

    @property
    def is_free(self) -> bool:
        """Check if provider is free to use"""
        return self.config.is_free

    @abstractmethod
    async def initialize(self):
        """
        Initialize provider (load model, check API, etc.)

        Providers load themselves lazily when first used.
        This allows fast startup - only load what's needed!
        """
        pass

    @abstractmethod
    async def extract(
        self,
        document: Document,
        prompt: str,
        options: Optional[ExtractionOptions] = None
    ) -> Dict[str, Any]:
        """
        Extract data from document

        Args:
            document: Document to process
            prompt: Extraction prompt (what to extract)
            options: Optional extraction options

        Returns:
            Dictionary with extracted data

        Raises:
            ProviderError: If extraction fails
        """
        pass

    @abstractmethod
    async def check_health(self) -> bool:
        """
        Check if provider is healthy and accessible

        Returns:
            True if healthy, False otherwise
        """
        pass

    async def extract_with_retry(
        self,
        document: Document,
        prompt: str,
        options: Optional[ExtractionOptions] = None
    ) -> ExtractionResult:
        """
        Extract with automatic retry logic

        Args:
            document: Document to process
            prompt: Extraction prompt
            options: Extraction options

        Returns:
            ExtractionResult
        """
        options = options or ExtractionOptions()

        # Ensure provider is initialized
        if not self.is_initialized:
            await self.initialize()

        last_error = None

        for attempt in range(options.max_retries):
            try:
                start_time = time.time()

                # Call provider's extract method
                data = await self.extract(document, prompt, options)

                latency_ms = (time.time() - start_time) * 1000

                # Build result
                result = ExtractionResult(
                    document_id=document.id,
                    extracted_data=data,
                    provider_used=self.name,
                    model_used=self.model.name,
                    latency_ms=latency_ms,
                    cost=self.config.cost_per_image,
                )

                # Record success
                self._record_success(latency_ms)

                return result

            except Exception as e:
                last_error = e
                logger.warning(
                    f"Provider {self.name} attempt {attempt + 1}/{options.max_retries} failed: {e}"
                )

                self._record_failure()

                if attempt < options.max_retries - 1:
                    # Wait before retry
                    await asyncio.sleep(1)
                    continue
                else:
                    # Final attempt failed
                    raise ProviderError(
                        f"Provider {self.name} failed after {options.max_retries} attempts: {last_error}"
                    )

    def _record_success(self, latency_ms: float):
        """Record successful request"""
        self.total_requests += 1
        self.total_latency += latency_ms
        self.total_cost += self.config.cost_per_image
        self.last_used = datetime.now()

        logger.debug(
            f"{self.name}: Success in {latency_ms:.0f}ms, "
            f"cost ${self.config.cost_per_image:.6f}"
        )

    def _record_failure(self):
        """Record failed request"""
        self.total_failures += 1

    def get_stats(self) -> Dict[str, Any]:
        """
        Get provider statistics

        Returns:
            Dictionary with stats
        """
        avg_latency = (
            self.total_latency / self.total_requests
            if self.total_requests > 0
            else 0.0
        )

        success_rate = (
            (self.total_requests - self.total_failures) / self.total_requests
            if self.total_requests > 0
            else 0.0
        )

        return {
            'provider': self.name,
            'model': self.model.name,
            'provider_type': self.model.provider_type,
            'is_free': self.is_free,
            'total_requests': self.total_requests,
            'total_failures': self.total_failures,
            'success_rate': success_rate,
            'avg_latency_ms': avg_latency,
            'total_cost': self.total_cost,
            'last_used': self.last_used.isoformat() if self.last_used else None,
        }

    def __repr__(self):
        return (
            f"{self.__class__.__name__}("
            f"name='{self.name}', "
            f"model='{self.model.name}', "
            f"requests={self.total_requests})"
        )


class ProviderRegistry:
    """
    Registry for dynamically discovered providers

    No hardcoded provider list - providers register themselves!
    """

    def __init__(self):
        self.providers: Dict[str, BaseVisionProvider] = {}
        logger.info("Provider registry initialized")

    def register(self, provider: BaseVisionProvider):
        """
        Register a provider

        Args:
            provider: Provider to register
        """
        self.providers[provider.name] = provider
        logger.info(f"✅ Registered provider: {provider.name}")

    def unregister(self, provider_name: str):
        """Unregister a provider"""
        if provider_name in self.providers:
            del self.providers[provider_name]
            logger.info(f"Unregistered provider: {provider_name}")

    def get(self, provider_name: str) -> Optional[BaseVisionProvider]:
        """Get provider by name"""
        return self.providers.get(provider_name)

    def get_all(self) -> list[BaseVisionProvider]:
        """Get all registered providers"""
        return list(self.providers.values())

    def get_available(self) -> list[BaseVisionProvider]:
        """Get all available (initialized) providers"""
        return [p for p in self.providers.values() if p.is_available]

    def get_free(self) -> list[BaseVisionProvider]:
        """Get all free providers"""
        return [p for p in self.providers.values() if p.is_free]

    def clear(self):
        """Clear all registered providers"""
        self.providers.clear()
        logger.info("Provider registry cleared")

    def get_stats(self) -> Dict[str, Any]:
        """Get statistics for all providers"""
        return {
            'total_providers': len(self.providers),
            'available_providers': len(self.get_available()),
            'free_providers': len(self.get_free()),
            'providers': {
                name: provider.get_stats()
                for name, provider in self.providers.items()
            }
        }

    def __len__(self):
        return len(self.providers)

    def __repr__(self):
        return f"ProviderRegistry(providers={len(self.providers)})"


# Global provider registry instance
provider_registry = ProviderRegistry()
