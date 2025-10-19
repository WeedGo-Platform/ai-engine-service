"""
Payment Processing Exceptions

Domain and provider-specific exceptions for payment processing.
"""

from .payment_errors import (
    PaymentError,
    InvalidTransactionStateError,
    InsufficientFundsError,
    RefundAmountExceededError,
    DuplicateTransactionError,
    TransactionNotFoundError,
    PaymentMethodNotFoundError,
    InvalidPaymentMethodError,
    PaymentDeclinedError,
    RefundNotAllowedError,
    VoidNotAllowedError,
    InvalidAmountError,
    CurrencyMismatchError,
    StoreNotConfiguredError,
    ProviderNotActiveError,
)

from .provider_errors import (
    ProviderError,
    ProviderConnectionError,
    ProviderTimeoutError,
    ProviderAuthenticationError,
    ProviderConfigurationError,
    ProviderResponseError,
    ProviderRateLimitError,
    ProviderNotSupportedError,
    CloverError,
    CloverOAuthError,
    MonerisError,
    InteracError,
    WebhookVerificationError,
    ProviderMaintenanceError,
)

__all__ = [
    # Payment domain errors
    'PaymentError',
    'InvalidTransactionStateError',
    'InsufficientFundsError',
    'RefundAmountExceededError',
    'DuplicateTransactionError',
    'TransactionNotFoundError',
    'PaymentMethodNotFoundError',
    'InvalidPaymentMethodError',
    'PaymentDeclinedError',
    'RefundNotAllowedError',
    'VoidNotAllowedError',
    'InvalidAmountError',
    'CurrencyMismatchError',
    'StoreNotConfiguredError',
    'ProviderNotActiveError',

    # Provider errors
    'ProviderError',
    'ProviderConnectionError',
    'ProviderTimeoutError',
    'ProviderAuthenticationError',
    'ProviderConfigurationError',
    'ProviderResponseError',
    'ProviderRateLimitError',
    'ProviderNotSupportedError',
    'CloverError',
    'CloverOAuthError',
    'MonerisError',
    'InteracError',
    'WebhookVerificationError',
    'ProviderMaintenanceError',
]
