"""
Payment Status Value Object

Represents the lifecycle status of a payment transaction.
Encapsulates business rules for status transitions.
"""

from enum import Enum
from typing import Set


class PaymentStatus(str, Enum):
    """
    Payment transaction status with business rules.

    Status Flow:
        pending → processing → completed
                           ↓
                        failed

    Refund Flow:
        completed → refunded

    Void Flow:
        pending/processing → voided
    """

    PENDING = 'pending'         # Payment initiated, not yet submitted to processor
    PROCESSING = 'processing'   # Submitted to payment processor, awaiting response
    COMPLETED = 'completed'     # Successfully processed and funds captured
    FAILED = 'failed'          # Payment failed (declined, error, etc.)
    REFUNDED = 'refunded'      # Fully refunded
    VOIDED = 'voided'          # Cancelled before completion

    def is_final(self) -> bool:
        """
        Check if status is final (cannot transition to another status).

        Returns:
            True if status is final

        Examples:
            >>> PaymentStatus.COMPLETED.is_final()
            True
            >>> PaymentStatus.PENDING.is_final()
            False
        """
        return self in [
            PaymentStatus.COMPLETED,
            PaymentStatus.FAILED,
            PaymentStatus.REFUNDED,
            PaymentStatus.VOIDED
        ]

    def can_transition_to(self, new_status: 'PaymentStatus') -> bool:
        """
        Check if transition to new status is allowed.

        Business Rules:
        - pending → processing, failed, voided
        - processing → completed, failed, voided
        - completed → refunded
        - failed → (no transitions)
        - refunded → (no transitions)
        - voided → (no transitions)

        Args:
            new_status: Target status

        Returns:
            True if transition is allowed

        Examples:
            >>> PaymentStatus.PENDING.can_transition_to(PaymentStatus.PROCESSING)
            True
            >>> PaymentStatus.COMPLETED.can_transition_to(PaymentStatus.PENDING)
            False
        """
        valid_transitions: dict[PaymentStatus, Set[PaymentStatus]] = {
            PaymentStatus.PENDING: {
                PaymentStatus.PROCESSING,
                PaymentStatus.FAILED,
                PaymentStatus.VOIDED
            },
            PaymentStatus.PROCESSING: {
                PaymentStatus.COMPLETED,
                PaymentStatus.FAILED,
                PaymentStatus.VOIDED
            },
            PaymentStatus.COMPLETED: {
                PaymentStatus.REFUNDED
            },
            PaymentStatus.FAILED: set(),      # No transitions from failed
            PaymentStatus.REFUNDED: set(),    # No transitions from refunded
            PaymentStatus.VOIDED: set()       # No transitions from voided
        }

        return new_status in valid_transitions.get(self, set())

    def can_refund(self) -> bool:
        """
        Check if transaction in this status can be refunded.

        Returns:
            True if refunds are allowed

        Examples:
            >>> PaymentStatus.COMPLETED.can_refund()
            True
            >>> PaymentStatus.PENDING.can_refund()
            False
        """
        return self == PaymentStatus.COMPLETED

    def can_void(self) -> bool:
        """
        Check if transaction in this status can be voided.

        Voiding is different from refunding - it cancels a transaction
        before it's completed, typically before funds are captured.

        Returns:
            True if voiding is allowed

        Examples:
            >>> PaymentStatus.PENDING.can_void()
            True
            >>> PaymentStatus.COMPLETED.can_void()
            False
        """
        return self in [PaymentStatus.PENDING, PaymentStatus.PROCESSING]

    def can_capture(self) -> bool:
        """
        Check if transaction can be captured.

        Capturing applies to pre-authorized transactions.

        Returns:
            True if capture is allowed

        Examples:
            >>> PaymentStatus.PROCESSING.can_capture()
            True
            >>> PaymentStatus.COMPLETED.can_capture()
            False
        """
        return self in [PaymentStatus.PENDING, PaymentStatus.PROCESSING]

    def is_successful(self) -> bool:
        """
        Check if status represents a successful payment.

        Returns:
            True if payment was successful

        Examples:
            >>> PaymentStatus.COMPLETED.is_successful()
            True
            >>> PaymentStatus.FAILED.is_successful()
            False
        """
        return self in [PaymentStatus.COMPLETED, PaymentStatus.REFUNDED]

    def is_in_progress(self) -> bool:
        """
        Check if payment is still in progress.

        Returns:
            True if payment is being processed

        Examples:
            >>> PaymentStatus.PROCESSING.is_in_progress()
            True
            >>> PaymentStatus.COMPLETED.is_in_progress()
            False
        """
        return self in [PaymentStatus.PENDING, PaymentStatus.PROCESSING]

    def requires_action(self) -> bool:
        """
        Check if status requires action (not final and not in progress).

        This could indicate a stuck transaction that needs investigation.

        Returns:
            True if action may be required

        Examples:
            >>> PaymentStatus.FAILED.requires_action()
            False
            >>> PaymentStatus.PROCESSING.requires_action()
            False
        """
        # Currently, all statuses either are final or in progress
        # This method is here for future extensibility
        return False

    def __str__(self) -> str:
        """Human-readable string representation."""
        return self.value.capitalize()

    def __repr__(self) -> str:
        """Developer-friendly representation."""
        return f"PaymentStatus.{self.name}"

    @classmethod
    def from_string(cls, status: str) -> 'PaymentStatus':
        """
        Create PaymentStatus from string.

        Args:
            status: Status string (case-insensitive)

        Returns:
            PaymentStatus enum

        Raises:
            ValueError: If status is invalid

        Examples:
            >>> PaymentStatus.from_string('completed')
            PaymentStatus.COMPLETED
            >>> PaymentStatus.from_string('PENDING')
            PaymentStatus.PENDING
        """
        try:
            return cls(status.lower())
        except ValueError:
            valid_statuses = [s.value for s in cls]
            raise ValueError(
                f"Invalid payment status: '{status}'. Must be one of: {valid_statuses}"
            )

    @classmethod
    def all_statuses(cls) -> list['PaymentStatus']:
        """
        Get all possible statuses.

        Returns:
            List of all PaymentStatus values

        Examples:
            >>> statuses = PaymentStatus.all_statuses()
            >>> len(statuses)
            6
        """
        return list(cls)

    @classmethod
    def final_statuses(cls) -> list['PaymentStatus']:
        """
        Get all final statuses.

        Returns:
            List of final PaymentStatus values

        Examples:
            >>> final = PaymentStatus.final_statuses()
            >>> PaymentStatus.COMPLETED in final
            True
            >>> PaymentStatus.PENDING in final
            False
        """
        return [status for status in cls if status.is_final()]

    def to_dict(self) -> dict:
        """
        Convert to dictionary for serialization.

        Returns:
            Dictionary representation

        Examples:
            >>> PaymentStatus.COMPLETED.to_dict()
            {'status': 'completed', 'is_final': True, 'is_successful': True}
        """
        return {
            'status': self.value,
            'is_final': self.is_final(),
            'is_successful': self.is_successful(),
            'is_in_progress': self.is_in_progress()
        }
