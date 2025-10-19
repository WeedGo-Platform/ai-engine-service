"""
Money Value Object

Represents monetary amounts with currency.
Immutable value object following DDD principles.
"""

from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP
from typing import Union


@dataclass(frozen=True)
class Money:
    """
    Value object representing monetary amount.

    Invariants:
    - Amount must have exactly 2 decimal places
    - Currency must be valid ISO code
    - Amount must be non-negative for transactions

    Examples:
        >>> money = Money(Decimal('19.99'), 'CAD')
        >>> money.amount
        Decimal('19.99')

        >>> money2 = Money.from_cents(1999, 'CAD')
        >>> money2.amount
        Decimal('19.99')

        >>> total = money + money2
        >>> total.amount
        Decimal('39.98')
    """

    amount: Decimal
    currency: str = 'CAD'

    def __post_init__(self):
        """Validate and normalize amount."""
        # Convert to Decimal if not already
        if not isinstance(self.amount, Decimal):
            object.__setattr__(self, 'amount', Decimal(str(self.amount)))

        # Ensure exactly 2 decimal places
        normalized_amount = self.amount.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        object.__setattr__(self, 'amount', normalized_amount)

        # Validate currency
        valid_currencies = ['CAD', 'USD']
        if self.currency not in valid_currencies:
            raise ValueError(f"Currency must be one of {valid_currencies}, got: {self.currency}")

        # Validate amount is non-negative
        if self.amount < 0:
            raise ValueError(f"Money amount cannot be negative, got: {self.amount}")

    def __add__(self, other: 'Money') -> 'Money':
        """Add two Money objects (same currency)."""
        if not isinstance(other, Money):
            raise TypeError(f"Cannot add Money with {type(other)}")

        if self.currency != other.currency:
            raise ValueError(
                f"Cannot add money with different currencies: {self.currency} and {other.currency}"
            )

        return Money(self.amount + other.amount, self.currency)

    def __sub__(self, other: 'Money') -> 'Money':
        """Subtract two Money objects (same currency)."""
        if not isinstance(other, Money):
            raise TypeError(f"Cannot subtract {type(other)} from Money")

        if self.currency != other.currency:
            raise ValueError(
                f"Cannot subtract money with different currencies: {self.currency} and {other.currency}"
            )

        result_amount = self.amount - other.amount
        if result_amount < 0:
            raise ValueError(f"Money subtraction would result in negative amount: {result_amount}")

        return Money(result_amount, self.currency)

    def __mul__(self, multiplier: Union[int, float, Decimal]) -> 'Money':
        """Multiply Money by a scalar."""
        if not isinstance(multiplier, (int, float, Decimal)):
            raise TypeError(f"Cannot multiply Money by {type(multiplier)}")

        return Money(self.amount * Decimal(str(multiplier)), self.currency)

    def __truediv__(self, divisor: Union[int, float, Decimal]) -> 'Money':
        """Divide Money by a scalar."""
        if not isinstance(divisor, (int, float, Decimal)):
            raise TypeError(f"Cannot divide Money by {type(divisor)}")

        if Decimal(str(divisor)) == 0:
            raise ValueError("Cannot divide Money by zero")

        return Money(self.amount / Decimal(str(divisor)), self.currency)

    def __eq__(self, other: object) -> bool:
        """Check equality."""
        if not isinstance(other, Money):
            return False
        return self.amount == other.amount and self.currency == other.currency

    def __lt__(self, other: 'Money') -> bool:
        """Less than comparison."""
        if not isinstance(other, Money):
            raise TypeError(f"Cannot compare Money with {type(other)}")

        if self.currency != other.currency:
            raise ValueError("Cannot compare money with different currencies")

        return self.amount < other.amount

    def __le__(self, other: 'Money') -> bool:
        """Less than or equal comparison."""
        return self == other or self < other

    def __gt__(self, other: 'Money') -> bool:
        """Greater than comparison."""
        return not self <= other

    def __ge__(self, other: 'Money') -> bool:
        """Greater than or equal comparison."""
        return not self < other

    def __str__(self) -> str:
        """String representation."""
        return f"{self.currency} ${self.amount:.2f}"

    def __repr__(self) -> str:
        """Developer-friendly representation."""
        return f"Money(amount=Decimal('{self.amount}'), currency='{self.currency}')"

    @classmethod
    def from_cents(cls, cents: int, currency: str = 'CAD') -> 'Money':
        """
        Create Money from cents (to avoid floating point issues).

        Args:
            cents: Amount in cents (e.g., 1999 for $19.99)
            currency: Currency code (default: CAD)

        Returns:
            Money object

        Examples:
            >>> Money.from_cents(1999, 'CAD')
            Money(amount=Decimal('19.99'), currency='CAD')
        """
        return cls(amount=Decimal(cents) / 100, currency=currency)

    @classmethod
    def zero(cls, currency: str = 'CAD') -> 'Money':
        """
        Create zero Money.

        Args:
            currency: Currency code (default: CAD)

        Returns:
            Money object with zero amount

        Examples:
            >>> Money.zero('CAD')
            Money(amount=Decimal('0.00'), currency='CAD')
        """
        return cls(amount=Decimal('0.00'), currency=currency)

    @property
    def cents(self) -> int:
        """
        Get amount in cents.

        Returns:
            Amount in cents as integer

        Examples:
            >>> money = Money(Decimal('19.99'), 'CAD')
            >>> money.cents
            1999
        """
        return int(self.amount * 100)

    @property
    def is_zero(self) -> bool:
        """
        Check if amount is zero.

        Returns:
            True if amount is zero

        Examples:
            >>> Money.zero().is_zero
            True
            >>> Money(Decimal('19.99'), 'CAD').is_zero
            False
        """
        return self.amount == Decimal('0.00')

    def to_dict(self) -> dict:
        """
        Convert to dictionary for serialization.

        Returns:
            Dictionary with amount and currency

        Examples:
            >>> Money(Decimal('19.99'), 'CAD').to_dict()
            {'amount': '19.99', 'currency': 'CAD'}
        """
        return {
            'amount': str(self.amount),
            'currency': self.currency
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'Money':
        """
        Create Money from dictionary.

        Args:
            data: Dictionary with 'amount' and optional 'currency'

        Returns:
            Money object

        Examples:
            >>> Money.from_dict({'amount': '19.99', 'currency': 'CAD'})
            Money(amount=Decimal('19.99'), currency='CAD')
        """
        return cls(
            amount=Decimal(str(data['amount'])),
            currency=data.get('currency', 'CAD')
        )
