"""
Translation Aggregate Root
Following DDD Architecture Document Section 2.14
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List, Dict, Any
from uuid import UUID

from ....shared.domain_base import AggregateRoot, DomainEvent, BusinessRuleViolation
from ..value_objects.translation_types import (
    LanguageCode,
    TranslationStatus,
    LocalizedText,
    TranslationKey
)


# Domain Events
class TranslationCreated(DomainEvent):
    translation_id: UUID
    translation_key: str
    source_language: LanguageCode


class TranslationUpdated(DomainEvent):
    translation_id: UUID
    translation_key: str
    language_code: LanguageCode
    updated_at: datetime


class TranslationPublished(DomainEvent):
    translation_id: UUID
    translation_key: str
    published_at: datetime


@dataclass
class Translation(AggregateRoot):
    """
    Translation Aggregate Root - Multi-language text management
    As defined in DDD_ARCHITECTURE_REFACTORING.md Section 2.14
    """
    # Translation key
    translation_key: Optional[TranslationKey] = None

    # Source language (usually English)
    source_language: LanguageCode = LanguageCode.ENGLISH
    source_text: str = ""

    # Translations for each language
    translations: Dict[LanguageCode, LocalizedText] = field(default_factory=dict)

    # Status
    status: TranslationStatus = TranslationStatus.DRAFT

    # Metadata
    description: Optional[str] = None  # What this translation is for
    context: Optional[str] = None  # Usage context
    max_length: Optional[int] = None  # Character limit (for UI strings)

    # Timestamps
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    published_at: Optional[datetime] = None

    # Tracking
    created_by: Optional[UUID] = None
    last_translated_by: Optional[UUID] = None

    # Metadata
    metadata: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def create(
        cls,
        translation_key: TranslationKey,
        source_text: str,
        source_language: LanguageCode = LanguageCode.ENGLISH,
        description: Optional[str] = None,
        created_by: Optional[UUID] = None
    ) -> 'Translation':
        """Factory method to create new translation"""
        if not source_text:
            raise BusinessRuleViolation("Source text is required")

        translation = cls(
            translation_key=translation_key,
            source_language=source_language,
            source_text=source_text,
            description=description,
            created_by=created_by,
            status=TranslationStatus.DRAFT
        )

        # Add source language translation
        source_localized = LocalizedText(
            language_code=source_language,
            text=source_text
        )
        translation.translations[source_language] = source_localized

        # Raise creation event
        translation.add_domain_event(TranslationCreated(
            translation_id=translation.id,
            translation_key=translation_key.get_full_key(),
            source_language=source_language
        ))

        return translation

    def add_translation(
        self,
        language_code: LanguageCode,
        text: str,
        text_plural: Optional[str] = None,
        translated_by: Optional[UUID] = None
    ):
        """Add or update translation for a language"""
        if not text:
            raise BusinessRuleViolation("Translation text cannot be empty")

        # Validate length if max_length is set
        if self.max_length and len(text) > self.max_length:
            raise BusinessRuleViolation(
                f"Translation exceeds max length of {self.max_length} characters"
            )

        localized = LocalizedText(
            language_code=language_code,
            text=text,
            text_plural=text_plural
        )

        self.translations[language_code] = localized
        self.last_translated_by = translated_by
        self.updated_at = datetime.utcnow()

        # Raise event
        self.add_domain_event(TranslationUpdated(
            translation_id=self.id,
            translation_key=self.translation_key.get_full_key(),
            language_code=language_code,
            updated_at=self.updated_at
        ))

        self.mark_as_modified()

    def remove_translation(self, language_code: LanguageCode):
        """Remove translation for a language"""
        if language_code == self.source_language:
            raise BusinessRuleViolation("Cannot remove source language translation")

        if language_code in self.translations:
            del self.translations[language_code]
            self.updated_at = datetime.utcnow()
            self.mark_as_modified()

    def publish(self):
        """Publish the translation"""
        if self.status == TranslationStatus.PUBLISHED:
            raise BusinessRuleViolation("Translation is already published")

        # Validate all required translations exist
        if len(self.translations) < 2:  # At least source + one other language
            raise BusinessRuleViolation("Must have at least one translation before publishing")

        self.status = TranslationStatus.PUBLISHED
        self.published_at = datetime.utcnow()

        # Raise event
        self.add_domain_event(TranslationPublished(
            translation_id=self.id,
            translation_key=self.translation_key.get_full_key(),
            published_at=self.published_at
        ))

        self.mark_as_modified()

    def deprecate(self):
        """Mark translation as deprecated"""
        self.status = TranslationStatus.DEPRECATED
        self.mark_as_modified()

    def get_translation(
        self,
        language_code: LanguageCode,
        fallback_to_source: bool = True
    ) -> Optional[LocalizedText]:
        """Get translation for language"""
        if language_code in self.translations:
            return self.translations[language_code]

        if fallback_to_source and self.source_language in self.translations:
            return self.translations[self.source_language]

        return None

    def get_text(
        self,
        language_code: LanguageCode,
        fallback_to_source: bool = True,
        count: Optional[int] = None
    ) -> Optional[str]:
        """Get translated text for language"""
        translation = self.get_translation(language_code, fallback_to_source)
        if not translation:
            return None

        if count is not None:
            return translation.get_text_for_count(count)

        return translation.text

    def has_translation(self, language_code: LanguageCode) -> bool:
        """Check if translation exists for language"""
        return language_code in self.translations

    def get_supported_languages(self) -> List[LanguageCode]:
        """Get list of supported languages"""
        return list(self.translations.keys())

    def get_completion_percentage(self) -> float:
        """Get translation completion percentage"""
        # Assume we want all 5 supported languages
        total_languages = len(LanguageCode)
        translated = len(self.translations)

        return (translated / total_languages) * 100

    def is_complete(self) -> bool:
        """Check if all languages are translated"""
        return len(self.translations) == len(LanguageCode)

    def validate(self) -> List[str]:
        """Validate translation"""
        errors = []

        if not self.translation_key:
            errors.append("Translation key is required")

        if not self.source_text:
            errors.append("Source text is required")

        if self.source_language not in self.translations:
            errors.append("Source language translation is missing")

        if self.max_length:
            for lang_code, localized in self.translations.items():
                if len(localized.text) > self.max_length:
                    errors.append(
                        f"{lang_code} translation exceeds max length ({self.max_length})"
                    )

        return errors
