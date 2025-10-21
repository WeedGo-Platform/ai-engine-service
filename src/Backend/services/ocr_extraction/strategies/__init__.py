"""
OCR Extraction Strategies

Provides different extraction algorithms following Strategy Pattern.

Available Strategies:
- LocalVisionStrategy: Use local models only (Ollama, HuggingFace)
- CloudVisionStrategy: Use cloud APIs only (Gemini free tier)
- HybridVisionStrategy: Smart combination (local first, cloud fallback)

Usage:
    from services.ocr_extraction.strategies import (
        LocalVisionStrategy,
        CloudVisionStrategy,
        HybridVisionStrategy,
        StrategySelector
    )

    # Auto-select best strategy
    selector = StrategySelector([
        LocalVisionStrategy(),
        CloudVisionStrategy(),
        HybridVisionStrategy()
    ])

    strategy = selector.select(template, options)
    result = await strategy.extract(document, template, options)
"""

from .base import AbstractVisionStrategy, StrategySelector
from .local_vision_strategy import LocalVisionStrategy
from .cloud_vision_strategy import CloudVisionStrategy
from .hybrid_vision_strategy import HybridVisionStrategy

__all__ = [
    # Base classes
    'AbstractVisionStrategy',
    'StrategySelector',

    # Concrete strategies
    'LocalVisionStrategy',
    'CloudVisionStrategy',
    'HybridVisionStrategy',
]
