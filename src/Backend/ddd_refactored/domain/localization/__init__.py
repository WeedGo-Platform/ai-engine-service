"""
Localization Bounded Context

This context handles:
- Multi-language translations
- Localized text management
- Translation workflow (draft, review, publish)
- Fallback to source language
- Pluralization support
"""

from .entities import (
    Translation,
    TranslationCreated,
    TranslationUpdated,
    TranslationPublished
)

from .value_objects import (
    LanguageCode,
    TranslationStatus,
    LocalizedText,
    TranslationKey
)

__all__ = [
    'Translation',
    'TranslationCreated',
    'TranslationUpdated',
    'TranslationPublished',
    'LanguageCode',
    'TranslationStatus',
    'LocalizedText',
    'TranslationKey'
]
