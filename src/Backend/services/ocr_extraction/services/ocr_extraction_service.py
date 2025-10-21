"""
OCR Extraction Service

Main orchestrator for OCR extraction system.
Following SRP: Only responsible for orchestration.
Following DDD: This is the Application Service layer.
"""

import logging
import os
from typing import Optional, List
from pathlib import Path

from ..domain.entities import Document, ExtractionResult
from ..domain.value_objects import Template, ExtractionOptions, VisionProviderConfig
from ..domain.enums import ProviderType, FieldType
from ..domain.exceptions import (
    ExtractionError,
    ProviderUnavailableError,
    AllProvidersExhaustedError
)

from .model_discovery import ModelDiscoveryService
from .validation_service import ValidationService

from ..providers.base_vision_provider import provider_registry
from ..providers.ollama_provider import OllamaVisionProvider
from ..providers.huggingface_provider import HuggingFaceVisionProvider
from ..providers.gemini_provider import GeminiVisionProvider

from ..strategies import (
    LocalVisionStrategy,
    CloudVisionStrategy,
    HybridVisionStrategy,
    StrategySelector
)

logger = logging.getLogger(__name__)


class OCRExtractionService:
    """
    Main service for OCR extraction

    This is the primary interface for the entire OCR system.
    Handles:
    - Auto-discovery of available models
    - Provider initialization
    - Strategy selection
    - Extraction orchestration
    - Validation

    Usage:
        service = OCRExtractionService()
        await service.initialize()

        result = await service.extract(
            document=document,
            template=ACCESSORY_TEMPLATE,
            options=ExtractionOptions()
        )
    """

    def __init__(self):
        """Initialize OCR extraction service"""
        self.discovery_service = ModelDiscoveryService()
        self.validation_service = ValidationService()
        self.strategy_selector = StrategySelector()

        self.is_initialized = False
        self.discovery_result = None

        logger.info("OCR Extraction Service created")

    async def initialize(self):
        """
        Initialize service

        Discovers available models and initializes providers.
        This is called automatically on first extract() if not called manually.
        """
        if self.is_initialized:
            logger.info("Service already initialized, skipping")
            return

        logger.info("🔍 Initializing OCR Extraction Service...")

        # Step 1: Discover available models
        logger.info("Step 1: Discovering available models...")
        self.discovery_result = self.discovery_service.discover_all()

        if not self.discovery_result.models_found:
            logger.warning(
                "⚠️ No models found! Please install Ollama or download HF models. "
                "Set GEMINI_API_KEY for cloud fallback."
            )
        else:
            logger.info(
                f"✅ Found {len(self.discovery_result.models_found)} models: "
                f"{', '.join([m.name for m in self.discovery_result.models_found])}"
            )

        # Step 2: Initialize providers
        logger.info("Step 2: Initializing providers...")
        await self._initialize_providers()

        # Step 3: Initialize strategies
        logger.info("Step 3: Initializing strategies...")
        self._initialize_strategies()

        self.is_initialized = True
        logger.info("✅ OCR Extraction Service initialized successfully!")

    async def _initialize_providers(self):
        """
        Initialize providers based on discovered models

        Creates provider instances and registers them.
        """
        if not self.discovery_result:
            return

        # Filter models by provider type
        ollama_models = [m for m in self.discovery_result.models_found if m.is_ollama_model]
        huggingface_models = [m for m in self.discovery_result.models_found if m.is_huggingface_model or m.is_paddleocr_model]

        # Initialize Ollama providers
        for model in ollama_models:
            try:
                config = VisionProviderConfig(
                    name=f"ollama_{model.name}",
                    provider_type=ProviderType.LOCAL_OLLAMA,
                    model_name=model.name
                )

                provider = OllamaVisionProvider(
                    config=config,
                    model=model,
                    ollama_url="http://localhost:11434"
                )

                # Register provider
                provider_registry.register(provider)

                # Initialize provider to make it available
                await provider.initialize()
                logger.info(f"  ✅ Registered and initialized Ollama provider: {model.name}")

            except Exception as e:
                logger.warning(f"  ⚠️ Failed to initialize Ollama provider {model.name}: {e}")

        # Initialize Hugging Face providers
        for model in huggingface_models:
            try:
                config = VisionProviderConfig(
                    name=f"hf_{model.name}",
                    provider_type=ProviderType.LOCAL_HUGGINGFACE,
                    model_name=model.name
                )

                provider = HuggingFaceVisionProvider(
                    config=config,
                    model=model
                )

                # Register provider
                provider_registry.register(provider)

                # Initialize provider to make it available
                await provider.initialize()
                logger.info(f"  ✅ Registered and initialized Hugging Face provider: {model.name}")

            except Exception as e:
                logger.warning(f"  ⚠️ Failed to initialize HF provider {model.name}: {e}")

        # Initialize Gemini provider if API key available
        if self.discovery_result.gemini_api_key:
            try:
                from ..domain.entities import AvailableModel

                # Create virtual model for Gemini
                gemini_model = AvailableModel(
                    name="gemini-2.0-flash-exp",
                    provider_type=ProviderType.CLOUD_FREE,
                    model_path="",  # Cloud API, no local path
                    size_mb=0  # Cloud model
                )

                config = VisionProviderConfig(
                    name="gemini_flash",
                    provider_type=ProviderType.CLOUD_FREE,
                    model_name="gemini-2.0-flash-exp"
                )

                provider = GeminiVisionProvider(
                    config=config,
                    model=gemini_model,
                    api_key=self.discovery_result.gemini_api_key
                )

                # Register provider
                provider_registry.register(provider)

                # Initialize provider to make it available
                await provider.initialize()
                logger.info(f"  ✅ Registered and initialized Gemini provider (free tier)")

            except Exception as e:
                logger.warning(f"  ⚠️ Failed to initialize Gemini provider: {e}")

        logger.info(f"Total providers registered: {len(provider_registry.get_available())}")

    def _initialize_strategies(self):
        """
        Initialize extraction strategies

        Creates strategy instances and adds to selector.
        """
        # Get providers by type
        all_providers = provider_registry.get_available()
        local_providers = [
            p for p in all_providers
            if p.config.provider_type in [ProviderType.LOCAL_OLLAMA, ProviderType.LOCAL_HUGGINGFACE]
        ]
        cloud_providers = [
            p for p in all_providers
            if p.config.provider_type == ProviderType.CLOUD_FREE
        ]

        # Create strategies
        if local_providers:
            local_strategy = LocalVisionStrategy(local_providers)
            self.strategy_selector.add_strategy(local_strategy)
            logger.info(f"  ✅ Added LocalVisionStrategy ({len(local_providers)} providers)")

        if cloud_providers:
            cloud_strategy = CloudVisionStrategy(cloud_providers)
            self.strategy_selector.add_strategy(cloud_strategy)
            logger.info(f"  ✅ Added CloudVisionStrategy ({len(cloud_providers)} providers)")

        if local_providers and cloud_providers:
            hybrid_strategy = HybridVisionStrategy()
            self.strategy_selector.add_strategy(hybrid_strategy)
            logger.info(f"  ✅ Added HybridVisionStrategy")

        logger.info(f"Total strategies available: {len(self.strategy_selector.strategies)}")

    async def extract(
        self,
        document: Document,
        template: Template,
        options: Optional[ExtractionOptions] = None
    ) -> ExtractionResult:
        """
        Extract data from document using template

        This is the main entry point for extraction.

        Args:
            document: Document to extract from
            template: Template defining what to extract
            options: Extraction options (strategy, provider, etc.)

        Returns:
            ExtractionResult with extracted data and validation

        Raises:
            ExtractionError: If extraction fails
        """
        # Auto-initialize if needed
        if not self.is_initialized:
            await self.initialize()

        options = options or ExtractionOptions()

        logger.info(
            f"📄 Extracting from document: {document.file_path or '<bytes>'} "
            f"using template: {template.name}"
        )

        # Validate document exists (only for file-based documents)
        if document.file_path and not document.image_bytes:
            if not Path(document.file_path).exists():
                raise ExtractionError(f"Document not found: {document.file_path}")

        # Select strategy
        try:
            strategy = self.strategy_selector.select(template, options)
            logger.info(f"🎯 Selected strategy: {strategy.get_name()}")
        except ValueError as e:
            raise AllProvidersExhaustedError(
                f"No suitable strategy found: {e}. "
                "Install local models or set GEMINI_API_KEY."
            )

        # Execute extraction
        try:
            result = await strategy.extract(document, template, options)
            logger.info(
                f"✅ Extraction completed "
                f"(confidence: {result.get_overall_confidence():.2f})"
            )

        except AllProvidersExhaustedError as e:
            logger.error(f"❌ All providers failed: {e}")
            raise

        except Exception as e:
            logger.error(f"❌ Extraction failed: {e}")
            raise ExtractionError(f"Extraction failed: {e}")

        # Validate extracted data
        validation_result = self.validation_service.validate(
            extracted_data=result.extracted_data,
            template=template
        )

        # Update result with validation info
        result.validation_passed = validation_result.is_valid
        result.validation_errors = validation_result.errors + validation_result.warnings

        # Mark for manual review if validation failed or confidence low
        result.requires_manual_review = (
            not validation_result.is_valid or
            result.get_overall_confidence() < 0.70
        )

        logger.info(f"Validation: {validation_result.get_summary()}")
        if result.requires_manual_review:
            logger.warning("⚠️ Result requires manual review")

        return result

    def get_stats(self) -> dict:
        """
        Get service statistics

        Returns:
            Dictionary with stats
        """
        return {
            'initialized': self.is_initialized,
            'discovery': self.discovery_result.to_dict() if self.discovery_result else None,
            'providers': provider_registry.get_stats(),
            'strategies': self.strategy_selector.get_available_strategies(),
        }

    async def cleanup(self):
        """Cleanup resources"""
        logger.info("Cleaning up OCR Extraction Service...")
        # Providers will cleanup themselves via __del__
        self.is_initialized = False


# Convenience: Global instance
ocr_service = OCRExtractionService()
