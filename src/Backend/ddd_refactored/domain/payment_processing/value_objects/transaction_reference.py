"""
Transaction Reference Value Object

Generates and validates unique payment transaction references.
"""

import re
from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from uuid import uuid4


@dataclass(frozen=True)
class TransactionReference:
    """
    Value object representing a unique transaction reference.

    Format: TXN-{YYYYMMDD}-{RANDOM}
    Example: TXN-20250118-A3F9B2C1

    Invariants:
    - Must be unique across all transactions
    - Must follow the format pattern
    - Cannot be empty
    - Maximum 100 characters
    """

    value: str

    # Pattern for validation: TXN-YYYYMMDD-ALPHANUMERIC
    PATTERN = re.compile(r'^TXN-\d{8}-[A-Z0-9]{8,12}$')

    def __post_init__(self):
        """Validate transaction reference format."""
        if not self.value:
            raise ValueError("Transaction reference cannot be empty")

        if len(self.value) > 100:
            raise ValueError(f"Transaction reference too long: {len(self.value)} chars (max 100)")

        if not self.PATTERN.match(self.value):
            raise ValueError(
                f"Invalid transaction reference format: '{self.value}'. "
                f"Expected format: TXN-YYYYMMDD-ALPHANUMERIC"
            )

    def __str__(self) -> str:
        """String representation."""
        return self.value

    def __repr__(self) -> str:
        """Developer-friendly representation."""
        return f"TransactionReference('{self.value}')"

    def __hash__(self) -> int:
        """Hash for use in sets/dicts."""
        return hash(self.value)

    @classmethod
    def generate(cls, prefix: str = "TXN") -> 'TransactionReference':
        """
        Generate a new unique transaction reference.

        Format: {PREFIX}-{YYYYMMDD}-{UUID_HEX}

        Args:
            prefix: Optional prefix (default: TXN)

        Returns:
            New TransactionReference

        Examples:
            >>> ref = TransactionReference.generate()
            >>> ref.value.startswith('TXN-')
            True
            >>> len(ref.value) >= 20
            True
        """
        # Get current date in YYYYMMDD format
        date_str = datetime.now().strftime('%Y%m%d')

        # Generate random unique part from UUID (8-12 chars)
        unique_part = uuid4().hex[:12].upper()

        # Combine parts
        reference = f"{prefix}-{date_str}-{unique_part}"

        return cls(reference)

    @classmethod
    def from_string(cls, value: str) -> 'TransactionReference':
        """
        Create TransactionReference from string.

        Args:
            value: Transaction reference string

        Returns:
            TransactionReference

        Raises:
            ValueError: If format is invalid

        Examples:
            >>> ref = TransactionReference.from_string('TXN-20250118-A3F9B2C1')
            >>> ref.value
            'TXN-20250118-A3F9B2C1'
        """
        return cls(value)

    @property
    def date_part(self) -> Optional[str]:
        """
        Extract date part from reference.

        Returns:
            Date string (YYYYMMDD) or None if not in standard format

        Examples:
            >>> ref = TransactionReference.from_string('TXN-20250118-A3F9B2C1')
            >>> ref.date_part
            '20250118'
        """
        parts = self.value.split('-')
        if len(parts) >= 2:
            return parts[1]
        return None

    @property
    def unique_part(self) -> Optional[str]:
        """
        Extract unique identifier part from reference.

        Returns:
            Unique part or None if not in standard format

        Examples:
            >>> ref = TransactionReference.from_string('TXN-20250118-A3F9B2C1')
            >>> ref.unique_part
            'A3F9B2C1'
        """
        parts = self.value.split('-')
        if len(parts) >= 3:
            return parts[2]
        return None

    def to_dict(self) -> dict:
        """
        Convert to dictionary for serialization.

        Returns:
            Dictionary with reference value

        Examples:
            >>> ref = TransactionReference.from_string('TXN-20250118-A3F9B2C1')
            >>> ref.to_dict()
            {'reference': 'TXN-20250118-A3F9B2C1'}
        """
        return {'reference': self.value}

    @classmethod
    def is_valid_format(cls, value: str) -> bool:
        """
        Check if string matches valid reference format.

        Args:
            value: String to validate

        Returns:
            True if format is valid

        Examples:
            >>> TransactionReference.is_valid_format('TXN-20250118-A3F9B2C1')
            True
            >>> TransactionReference.is_valid_format('INVALID')
            False
        """
        if not value or len(value) > 100:
            return False
        return bool(cls.PATTERN.match(value))
