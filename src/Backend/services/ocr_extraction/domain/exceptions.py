"""
Domain Exceptions for OCR Extraction System

Custom exceptions specific to the OCR extraction domain.
Following DDD: Domain-specific errors are part of the model.
"""


class OCRExtractionError(Exception):
    """Base exception for all OCR extraction errors"""
    pass


class ProviderError(OCRExtractionError):
    """Base exception for vision provider errors"""
    pass


class ProviderUnavailableError(ProviderError):
    """Raised when a vision provider is not available"""
    def __init__(self, provider_name: str, reason: str):
        self.provider_name = provider_name
        self.reason = reason
        super().__init__(
            f"Provider '{provider_name}' unavailable: {reason}"
        )


class ProviderTimeoutError(ProviderError):
    """Raised when a provider request times out"""
    def __init__(self, provider_name: str, timeout_seconds: float):
        self.provider_name = provider_name
        self.timeout_seconds = timeout_seconds
        super().__init__(
            f"Provider '{provider_name}' timed out after {timeout_seconds}s"
        )


class RateLimitError(ProviderError):
    """Raised when provider rate limit is exceeded"""
    def __init__(self, provider_name: str, limit_type: str, retry_after: int = None):
        self.provider_name = provider_name
        self.limit_type = limit_type
        self.retry_after = retry_after
        message = f"Provider '{provider_name}' rate limit exceeded: {limit_type}"
        if retry_after:
            message += f". Retry after {retry_after}s"
        super().__init__(message)


class AllProvidersExhaustedError(ProviderError):
    """Raised when all providers have failed or are unavailable"""
    def __init__(self, attempted_providers: list, last_error: str = None):
        self.attempted_providers = attempted_providers
        self.last_error = last_error
        message = f"All providers exhausted: {', '.join(attempted_providers)}"
        if last_error:
            message += f". Last error: {last_error}"
        super().__init__(message)


class TemplateError(OCRExtractionError):
    """Base exception for template-related errors"""
    pass


class TemplateNotFoundError(TemplateError):
    """Raised when requested template doesn't exist"""
    def __init__(self, template_name: str):
        self.template_name = template_name
        super().__init__(f"Template not found: '{template_name}'")


class InvalidTemplateError(TemplateError):
    """Raised when template definition is invalid"""
    def __init__(self, template_name: str, reason: str):
        self.template_name = template_name
        self.reason = reason
        super().__init__(
            f"Invalid template '{template_name}': {reason}"
        )


class TemplateMismatchError(TemplateError):
    """Raised when extracted data doesn't match template schema"""
    def __init__(self, template_name: str, missing_fields: list):
        self.template_name = template_name
        self.missing_fields = missing_fields
        super().__init__(
            f"Data doesn't match template '{template_name}'. "
            f"Missing required fields: {', '.join(missing_fields)}"
        )


class ValidationError(OCRExtractionError):
    """Base exception for validation errors"""
    pass


class FieldValidationError(ValidationError):
    """Raised when a field fails validation"""
    def __init__(self, field_name: str, value: any, reason: str):
        self.field_name = field_name
        self.value = value
        self.reason = reason
        super().__init__(
            f"Field '{field_name}' validation failed: {reason}. Value: {value}"
        )


class RequiredFieldMissingError(ValidationError):
    """Raised when a required field is missing"""
    def __init__(self, field_name: str, template_name: str):
        self.field_name = field_name
        self.template_name = template_name
        super().__init__(
            f"Required field '{field_name}' missing in template '{template_name}'"
        )


class DocumentError(OCRExtractionError):
    """Base exception for document-related errors"""
    pass


class DocumentNotFoundError(DocumentError):
    """Raised when document file is not found"""
    def __init__(self, file_path: str):
        self.file_path = file_path
        super().__init__(f"Document not found: {file_path}")


class InvalidDocumentError(DocumentError):
    """Raised when document is invalid or corrupted"""
    def __init__(self, file_path: str, reason: str):
        self.file_path = file_path
        self.reason = reason
        super().__init__(
            f"Invalid document '{file_path}': {reason}"
        )


class UnsupportedDocumentTypeError(DocumentError):
    """Raised when document type is not supported"""
    def __init__(self, file_path: str, content_type: str):
        self.file_path = file_path
        self.content_type = content_type
        super().__init__(
            f"Unsupported document type '{content_type}' for file: {file_path}"
        )


class ExtractionError(OCRExtractionError):
    """Base exception for extraction process errors"""
    pass


class ExtractionFailedError(ExtractionError):
    """Raised when extraction completely fails"""
    def __init__(self, document_id: str, reason: str):
        self.document_id = document_id
        self.reason = reason
        super().__init__(
            f"Extraction failed for document {document_id}: {reason}"
        )


class LowConfidenceError(ExtractionError):
    """Raised when extraction confidence is too low"""
    def __init__(self, document_id: str, confidence: float, threshold: float):
        self.document_id = document_id
        self.confidence = confidence
        self.threshold = threshold
        super().__init__(
            f"Extraction confidence ({confidence:.2%}) below threshold "
            f"({threshold:.2%}) for document {document_id}"
        )


class ImageProcessingError(OCRExtractionError):
    """Raised when image preprocessing fails"""
    def __init__(self, file_path: str, reason: str):
        self.file_path = file_path
        self.reason = reason
        super().__init__(
            f"Image processing failed for '{file_path}': {reason}"
        )
