"""
Domain Enums for OCR Extraction System

Defines enumeration types used throughout the OCR extraction domain.
Following DDD: These are part of the ubiquitous language.
"""

from enum import Enum


class TemplateType(str, Enum):
    """
    Types of extraction templates supported

    Each template type represents a different document category
    with specific extraction requirements.
    """
    ACCESSORY = "accessory"
    ORDER = "order"
    INVOICE = "invoice"
    RECEIPT = "receipt"
    PRODUCT_LABEL = "product_label"
    FORM = "form"
    CUSTOM = "custom"


class FieldType(str, Enum):
    """
    Types of fields that can be extracted from documents

    Determines how data should be parsed and validated.
    """
    TEXT = "text"              # Plain text string
    NUMBER = "number"          # Numeric value (int or float)
    PRICE = "price"            # Currency amount
    DATE = "date"              # Date or datetime
    IMAGE_URL = "image_url"    # URL to image
    BARCODE = "barcode"        # Barcode/UPC/EAN
    CATEGORY = "category"      # Classification/category
    TABLE = "table"            # Structured table data
    BOOLEAN = "boolean"        # True/False value
    EMAIL = "email"            # Email address
    PHONE = "phone"            # Phone number
    ADDRESS = "address"        # Physical address


class ProviderType(str, Enum):
    """
    Types of vision providers

    Determines deployment model and cost structure.
    """
    LOCAL_OLLAMA = "local_ollama"        # Ollama-hosted models
    LOCAL_HUGGINGFACE = "local_huggingface"  # Direct HF transformers
    CLOUD_FREE = "cloud_free"            # Free cloud APIs (Gemini)
    CLOUD_PAID = "cloud_paid"            # Paid cloud APIs (not used)


class StrategyType(str, Enum):
    """
    Extraction strategy types

    Determines how extraction is performed.
    """
    LOCAL = "local"      # Local models only
    CLOUD = "cloud"      # Cloud APIs only
    HYBRID = "hybrid"    # Smart combination of local + cloud
    AUTO = "auto"        # Automatic selection


class ConfidenceLevel(str, Enum):
    """
    Confidence level categories

    Simplifies confidence interpretation.
    """
    VERY_HIGH = "very_high"  # >= 0.95
    HIGH = "high"            # >= 0.80
    MEDIUM = "medium"        # >= 0.65
    LOW = "low"              # >= 0.50
    VERY_LOW = "very_low"    # < 0.50


class ValidationSeverity(str, Enum):
    """
    Validation error severity levels

    Determines how validation failures should be handled.
    """
    ERROR = "error"      # Critical error, extraction unusable
    WARNING = "warning"  # Issue but data may still be usable
    INFO = "info"        # Informational message
