"""
Payment Provider Exceptions

External provider integration errors.
"""

from typing import Optional, Dict, Any
from uuid import UUID


class ProviderError(Exception):
    """Base exception for payment provider errors."""

    def __init__(
        self,
        message: str,
        provider_name: Optional[str] = None,
        error_code: Optional[str] = None,
        provider_response: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize provider error.

        Args:
            message: Human-readable error message
            provider_name: Name of the payment provider (Clover, Moneris, Interac)
            error_code: Provider-specific error code
            provider_response: Raw provider response for debugging
        """
        self.message = message
        self.provider_name = provider_name
        self.error_code = error_code or self.__class__.__name__
        self.provider_response = provider_response
        super().__init__(self.message)

    def __str__(self) -> str:
        if self.provider_name:
            return f"[{self.provider_name}] {self.message}"
        return f"[{self.error_code}] {self.message}"


class ProviderConnectionError(ProviderError):
    """
    Raised when unable to connect to payment provider.

    This is a transient error - retry may succeed.
    """

    def __init__(
        self,
        provider_name: str,
        message: str = "Unable to connect to payment provider",
        original_error: Optional[Exception] = None
    ):
        self.original_error = original_error
        super().__init__(
            message,
            provider_name=provider_name,
            error_code="PROVIDER_CONNECTION_ERROR"
        )


class ProviderTimeoutError(ProviderError):
    """
    Raised when provider request times out.

    This is a transient error - retry may succeed.
    """

    def __init__(self, provider_name: str, timeout_seconds: Optional[float] = None):
        message = f"Payment provider request timed out"
        if timeout_seconds:
            message += f" after {timeout_seconds}s"

        self.timeout_seconds = timeout_seconds
        super().__init__(
            message,
            provider_name=provider_name,
            error_code="PROVIDER_TIMEOUT"
        )


class ProviderAuthenticationError(ProviderError):
    """
    Raised when provider authentication fails.

    This indicates invalid credentials or expired tokens.
    """

    def __init__(
        self,
        provider_name: str,
        message: str = "Authentication failed with payment provider",
        credential_type: Optional[str] = None
    ):
        self.credential_type = credential_type
        super().__init__(
            message,
            provider_name=provider_name,
            error_code="PROVIDER_AUTHENTICATION_ERROR"
        )


class ProviderConfigurationError(ProviderError):
    """
    Raised when provider configuration is invalid.

    Example: Missing required credentials, invalid webhook URL.
    """

    def __init__(
        self,
        provider_name: str,
        message: str,
        missing_fields: Optional[list] = None
    ):
        self.missing_fields = missing_fields or []
        super().__init__(
            message,
            provider_name=provider_name,
            error_code="PROVIDER_CONFIGURATION_ERROR"
        )


class ProviderResponseError(ProviderError):
    """
    Raised when provider returns unexpected/invalid response.

    Example: Malformed JSON, missing required fields.
    """

    def __init__(
        self,
        provider_name: str,
        message: str = "Invalid response from payment provider",
        response_data: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message,
            provider_name=provider_name,
            error_code="PROVIDER_RESPONSE_ERROR",
            provider_response=response_data
        )


class ProviderRateLimitError(ProviderError):
    """
    Raised when provider rate limit is exceeded.

    This is a transient error - retry after delay may succeed.
    """

    def __init__(
        self,
        provider_name: str,
        retry_after_seconds: Optional[int] = None
    ):
        message = "Payment provider rate limit exceeded"
        if retry_after_seconds:
            message += f". Retry after {retry_after_seconds}s"

        self.retry_after_seconds = retry_after_seconds
        super().__init__(
            message,
            provider_name=provider_name,
            error_code="PROVIDER_RATE_LIMIT"
        )


class ProviderNotSupportedError(ProviderError):
    """
    Raised when attempting unsupported operation for provider.

    Example: Trying to do e-Transfer with Clover (not supported).
    """

    def __init__(self, provider_name: str, operation: str):
        message = f"Operation '{operation}' not supported by {provider_name}"
        self.operation = operation
        super().__init__(
            message,
            provider_name=provider_name,
            error_code="PROVIDER_NOT_SUPPORTED"
        )


class CloverError(ProviderError):
    """Clover-specific errors."""

    def __init__(
        self,
        message: str,
        error_code: Optional[str] = None,
        provider_response: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message,
            provider_name="Clover",
            error_code=error_code or "CLOVER_ERROR",
            provider_response=provider_response
        )


class CloverOAuthError(CloverError):
    """Clover OAuth flow errors."""

    def __init__(self, message: str, oauth_error: Optional[str] = None):
        self.oauth_error = oauth_error
        super().__init__(message, error_code="CLOVER_OAUTH_ERROR")


class MonerisError(ProviderError):
    """Moneris-specific errors."""

    def __init__(
        self,
        message: str,
        error_code: Optional[str] = None,
        provider_response: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message,
            provider_name="Moneris",
            error_code=error_code or "MONERIS_ERROR",
            provider_response=provider_response
        )


class InteracError(ProviderError):
    """Interac-specific errors."""

    def __init__(
        self,
        message: str,
        error_code: Optional[str] = None,
        provider_response: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message,
            provider_name="Interac",
            error_code=error_code or "INTERAC_ERROR",
            provider_response=provider_response
        )


class WebhookVerificationError(ProviderError):
    """
    Raised when webhook signature verification fails.

    This indicates potentially malicious webhook or configuration issue.
    """

    def __init__(
        self,
        provider_name: str,
        message: str = "Webhook signature verification failed"
    ):
        super().__init__(
            message,
            provider_name=provider_name,
            error_code="WEBHOOK_VERIFICATION_FAILED"
        )


class ProviderMaintenanceError(ProviderError):
    """
    Raised when provider is under maintenance.

    This is a transient error - retry later may succeed.
    """

    def __init__(self, provider_name: str, estimated_restoration: Optional[str] = None):
        message = f"{provider_name} is currently under maintenance"
        if estimated_restoration:
            message += f". Estimated restoration: {estimated_restoration}"

        self.estimated_restoration = estimated_restoration
        super().__init__(
            message,
            provider_name=provider_name,
            error_code="PROVIDER_MAINTENANCE"
        )
