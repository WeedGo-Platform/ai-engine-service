"""
Localization Value Objects
Following DDD Architecture Document Section 2.14
"""

from dataclasses import dataclass
from enum import Enum
from typing import Optional, Dict

from ....shared.domain_base import ValueObject


class LanguageCode(str, Enum):
    """Supported language codes (ISO 639-1)"""
    ENGLISH = "en"
    FRENCH = "fr"
    SPANISH = "es"
    PORTUGUESE = "pt"
    CHINESE = "zh"


class TranslationStatus(str, Enum):
    """Translation status"""
    DRAFT = "draft"
    PENDING_REVIEW = "pending_review"
    APPROVED = "approved"
    PUBLISHED = "published"
    DEPRECATED = "deprecated"


@dataclass(frozen=True)
class LocalizedText(ValueObject):
    """
    Localized text for a specific language
    """
    language_code: LanguageCode
    text: str

    # Optional pluralization
    text_plural: Optional[str] = None

    def __post_init__(self):
        """Validate localized text"""
        if not self.text:
            raise ValueError("Text cannot be empty")

        if len(self.text) > 10000:
            raise ValueError("Text too long (max 10000 characters)")

    def get_text_for_count(self, count: int) -> str:
        """Get appropriate text based on count (handles pluralization)"""
        if count == 1 or not self.text_plural:
            return self.text
        return self.text_plural


@dataclass(frozen=True)
class TranslationKey(ValueObject):
    """
    Unique key for translations
    """
    namespace: str  # e.g., "product", "ui", "email"
    key: str  # e.g., "add_to_cart", "welcome_message"

    def __post_init__(self):
        """Validate translation key"""
        if not self.namespace:
            raise ValueError("Namespace is required")

        if not self.key:
            raise ValueError("Key is required")

        # Validate format (lowercase, underscores only)
        if not self.namespace.replace('_', '').isalnum():
            raise ValueError("Namespace must be alphanumeric with underscores")

        if not self.key.replace('_', '').isalnum():
            raise ValueError("Key must be alphanumeric with underscores")

    def get_full_key(self) -> str:
        """Get full key in dot notation"""
        return f"{self.namespace}.{self.key}"

    def __str__(self) -> str:
        return self.get_full_key()
