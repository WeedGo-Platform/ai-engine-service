"""
Payment Processing Context Entities

Refactored for store-level providers and simplified architecture.
"""

# New simplified entities (DDD refactor)
from .payment_transaction import PaymentTransaction
from .payment_refund import PaymentRefund

# Legacy imports (from old payment_transaction.py.old - to be migrated)
# These are kept for backward compatibility during migration
try:
    from .payment_transaction import (
        Refund,
        PaymentInitiated,
        PaymentAuthorized,
        PaymentCaptured,
        PaymentFailed as LegacyPaymentFailed,
        PaymentCancelled,
        RefundIssued,
        RefundCompleted
    )
    _legacy_available = True
except ImportError:
    _legacy_available = False

__all__ = [
    # New DDD entities
    'PaymentTransaction',
    'PaymentRefund',
]

# Add legacy exports if available
if _legacy_available:
    __all__.extend([
        'Refund',
        'PaymentInitiated',
        'PaymentAuthorized',
        'PaymentCaptured',
        'LegacyPaymentFailed',
        'PaymentCancelled',
        'RefundIssued',
        'RefundCompleted'
    ])
