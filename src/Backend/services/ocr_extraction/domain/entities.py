"""
Domain Entities for OCR Extraction System

Entities have identity and lifecycle.
Following DDD: Entities are compared by ID, not by value.
"""

from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID, uuid4
from typing import Dict, Any, Optional, List
from pathlib import Path

from .enums import TemplateType, ConfidenceLevel
from .value_objects import Template


@dataclass
class Document:
    """
    Document entity with identity

    Represents an image/document to be processed.
    Has lifecycle and state.

    Can be initialized from:
    - file_path: Path to file on disk
    - image_bytes: Raw image bytes (for API uploads, base64 decoding)
    """
    id: UUID = field(default_factory=uuid4)
    file_path: str = ""
    image_bytes: Optional[bytes] = None
    content_type: str = ""  # image/png, application/pdf
    size_bytes: int = 0
    width: Optional[int] = None
    height: Optional[int] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    processed: bool = False
    processed_at: Optional[datetime] = None

    def __post_init__(self):
        """Initialize document"""
        if self.file_path and self.file_path != "dummy.jpg":
            self._validate_file()
        elif self.image_bytes:
            self._validate_bytes()

    def _validate_file(self):
        """Validate file exists and get metadata"""
        path = Path(self.file_path)

        if not path.exists():
            from .exceptions import DocumentNotFoundError
            raise DocumentNotFoundError(self.file_path)

        # Get file size
        self.size_bytes = path.stat().st_size

        # Infer content type from extension
        ext = path.suffix.lower()
        content_type_map = {
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.png': 'image/png',
            '.gif': 'image/gif',
            '.bmp': 'image/bmp',
            '.webp': 'image/webp',
            '.pdf': 'application/pdf',
        }
        self.content_type = content_type_map.get(ext, 'application/octet-stream')

        # Get image dimensions if image
        if self.content_type.startswith('image/'):
            try:
                from PIL import Image
                with Image.open(self.file_path) as img:
                    self.width, self.height = img.size
            except Exception:
                pass  # Dimensions not critical

    def _validate_bytes(self):
        """Validate and process image bytes"""
        if not self.image_bytes:
            from .exceptions import ValidationError
            raise ValidationError("image_bytes", "Image bytes cannot be empty")

        # Get size
        self.size_bytes = len(self.image_bytes)

        # Try to determine content type and dimensions from bytes
        try:
            from PIL import Image
            import io

            with Image.open(io.BytesIO(self.image_bytes)) as img:
                self.width, self.height = img.size

                # Determine format
                format_to_mime = {
                    'JPEG': 'image/jpeg',
                    'PNG': 'image/png',
                    'GIF': 'image/gif',
                    'BMP': 'image/bmp',
                    'WEBP': 'image/webp',
                }
                self.content_type = format_to_mime.get(img.format, 'image/jpeg')

        except Exception as e:
            # If we can't open as image, assume it's jpeg (most common)
            self.content_type = 'image/jpeg'

    def get_bytes(self) -> bytes:
        """
        Get document bytes (from file or direct bytes)

        Returns:
            Raw document bytes

        Raises:
            FileNotFoundError: If file_path is set but file doesn't exist
        """
        if self.image_bytes:
            return self.image_bytes
        elif self.file_path:
            path = Path(self.file_path)
            if not path.exists():
                from .exceptions import DocumentNotFoundError
                raise DocumentNotFoundError(self.file_path)
            return path.read_bytes()
        else:
            from .exceptions import ValidationError
            raise ValidationError("document", "Document has neither file_path nor image_bytes")

    def mark_as_processed(self):
        """Mark document as processed"""
        self.processed = True
        self.processed_at = datetime.utcnow()

    @property
    def size_mb(self) -> float:
        """Get size in megabytes"""
        return self.size_bytes / (1024 * 1024)

    @property
    def is_image(self) -> bool:
        """Check if document is an image"""
        return self.content_type.startswith('image/')

    @property
    def is_pdf(self) -> bool:
        """Check if document is a PDF"""
        return self.content_type == 'application/pdf'


@dataclass
class ExtractionResult:
    """
    Extraction result entity with identity

    Represents the outcome of an extraction operation.
    Has identity and lifecycle.
    """
    id: UUID = field(default_factory=uuid4)
    document_id: UUID = field(default_factory=uuid4)
    template_type: TemplateType = TemplateType.CUSTOM
    template_name: str = ""

    # Extracted data
    extracted_data: Dict[str, Any] = field(default_factory=dict)
    raw_ocr_text: Optional[str] = None

    # Metadata
    provider_used: str = ""
    strategy_used: str = ""
    model_used: str = ""
    confidence_scores: Dict[str, float] = field(default_factory=dict)

    # Performance
    latency_ms: float = 0.0
    tokens_used: int = 0
    cost: float = 0.0

    # Timestamps
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    # Validation
    validation_passed: bool = True
    validation_errors: List[str] = field(default_factory=list)
    validation_warnings: List[str] = field(default_factory=list)

    # Quality indicators
    requires_manual_review: bool = False
    review_reason: Optional[str] = None

    def get_overall_confidence(self) -> float:
        """
        Calculate overall confidence score
        
        Only averages confidence scores for fields that were actually extracted (non-zero).
        This prevents empty optional fields from dragging down the overall confidence.

        Returns:
            Float between 0.0 and 1.0
        """
        if not self.confidence_scores:
            return 0.0

        # Only count fields with non-zero confidence (actually extracted)
        non_zero_scores = [score for score in self.confidence_scores.values() if score > 0.0]
        
        if not non_zero_scores:
            return 0.0

        # Average of extracted field confidences only
        return sum(non_zero_scores) / len(non_zero_scores)

    def get_confidence_level(self) -> ConfidenceLevel:
        """
        Get categorical confidence level

        Returns:
            ConfidenceLevel enum
        """
        conf = self.get_overall_confidence()

        if conf >= 0.95:
            return ConfidenceLevel.VERY_HIGH
        elif conf >= 0.80:
            return ConfidenceLevel.HIGH
        elif conf >= 0.65:
            return ConfidenceLevel.MEDIUM
        elif conf >= 0.50:
            return ConfidenceLevel.LOW
        else:
            return ConfidenceLevel.VERY_LOW

    def is_high_quality(self) -> bool:
        """
        Check if extraction is high quality

        Returns:
            True if extraction meets quality criteria
        """
        return (
            self.validation_passed and
            self.get_overall_confidence() >= 0.80 and
            not self.validation_errors and
            not self.requires_manual_review
        )

    def is_acceptable(self) -> bool:
        """
        Check if extraction is acceptable (may need review)

        Returns:
            True if extraction is usable
        """
        return (
            self.validation_passed and
            self.get_overall_confidence() >= 0.50 and
            len(self.validation_errors) == 0
        )

    def flag_for_review(self, reason: str):
        """
        Flag result for manual review

        Args:
            reason: Why manual review is needed
        """
        self.requires_manual_review = True
        self.review_reason = reason
        self.updated_at = datetime.utcnow()

    def add_validation_error(self, error: str):
        """Add a validation error"""
        if error not in self.validation_errors:
            self.validation_errors.append(error)
        self.validation_passed = False
        self.updated_at = datetime.utcnow()

    def add_validation_warning(self, warning: str):
        """Add a validation warning"""
        if warning not in self.validation_warnings:
            self.validation_warnings.append(warning)
        self.updated_at = datetime.utcnow()

    def update_confidence(self, field_name: str, confidence: float):
        """Update confidence score for a field"""
        self.confidence_scores[field_name] = confidence
        self.updated_at = datetime.utcnow()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            'id': str(self.id),
            'document_id': str(self.document_id),
            'template_type': self.template_type.value,
            'template_name': self.template_name,
            'extracted_data': self.extracted_data,
            'raw_ocr_text': self.raw_ocr_text,
            'provider_used': self.provider_used,
            'strategy_used': self.strategy_used,
            'model_used': self.model_used,
            'confidence_scores': self.confidence_scores,
            'overall_confidence': self.get_overall_confidence(),
            'confidence_level': self.get_confidence_level().value,
            'latency_ms': self.latency_ms,
            'tokens_used': self.tokens_used,
            'cost': self.cost,
            'validation_passed': self.validation_passed,
            'validation_errors': self.validation_errors,
            'validation_warnings': self.validation_warnings,
            'is_high_quality': self.is_high_quality(),
            'is_acceptable': self.is_acceptable(),
            'requires_manual_review': self.requires_manual_review,
            'review_reason': self.review_reason,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
        }


@dataclass
class AvailableModel:
    """
    Represents a discovered model available for use

    This entity is discovered at runtime by scanning the models directory.
    """
    id: UUID = field(default_factory=uuid4)
    name: str = ""
    provider_type: str = ""  # 'ollama', 'huggingface', 'paddleocr'
    model_path: str = ""
    size_mb: float = 0.0
    discovered_at: datetime = field(default_factory=datetime.utcnow)
    is_loaded: bool = False
    last_used: Optional[datetime] = None

    @property
    def is_ollama_model(self) -> bool:
        """Check if this is an Ollama model"""
        return self.provider_type == 'ollama'

    @property
    def is_huggingface_model(self) -> bool:
        """Check if this is a Hugging Face model"""
        return self.provider_type == 'huggingface'

    @property
    def is_paddleocr_model(self) -> bool:
        """Check if this is a PaddleOCR model"""
        return self.provider_type == 'paddleocr'

    def mark_used(self):
        """Mark model as used"""
        self.last_used = datetime.utcnow()
