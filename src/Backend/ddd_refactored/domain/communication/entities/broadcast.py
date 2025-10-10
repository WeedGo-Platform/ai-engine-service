"""
Broadcast Aggregate Root
Following DDD Architecture Document Section 2.11
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List, Dict, Any
from uuid import UUID, uuid4

from ....shared.domain_base import AggregateRoot, DomainEvent, BusinessRuleViolation
from ..value_objects.message_types import (
    MessageType,
    MessageStatus,
    MessagePriority,
    BroadcastStatus,
    AudienceSegment,
    MessageCategory,
    MessageContent,
    Recipient,
    DeliverySettings,
    BroadcastFilter,
    MessageTemplate
)


# Domain Events
class BroadcastCreated(DomainEvent):
    broadcast_id: UUID
    broadcast_name: str
    message_type: MessageType
    audience_segment: AudienceSegment


class BroadcastScheduled(DomainEvent):
    broadcast_id: UUID
    broadcast_name: str
    scheduled_time: datetime


class BroadcastStarted(DomainEvent):
    broadcast_id: UUID
    broadcast_name: str
    started_at: datetime
    total_recipients: int


class MessageSent(DomainEvent):
    broadcast_id: UUID
    message_id: UUID
    recipient_id: str
    message_type: MessageType
    sent_at: datetime


class MessageDelivered(DomainEvent):
    broadcast_id: UUID
    message_id: UUID
    recipient_id: str
    delivered_at: datetime


class MessageFailed(DomainEvent):
    broadcast_id: UUID
    message_id: UUID
    recipient_id: str
    failure_reason: str
    failed_at: datetime


class BroadcastCompleted(DomainEvent):
    broadcast_id: UUID
    broadcast_name: str
    completed_at: datetime
    total_sent: int
    total_delivered: int
    total_failed: int


@dataclass
class Message:
    """Individual message entity within Broadcast aggregate"""
    id: UUID = field(default_factory=uuid4)
    recipient: Recipient = None

    # Status
    status: MessageStatus = MessageStatus.PENDING

    # Delivery tracking
    sent_at: Optional[datetime] = None
    delivered_at: Optional[datetime] = None
    read_at: Optional[datetime] = None
    failed_at: Optional[datetime] = None

    # Failure details
    failure_reason: Optional[str] = None
    retry_count: int = 0

    # Provider details
    provider_message_id: Optional[str] = None  # ID from SMS/email provider

    # Metadata
    metadata: Dict[str, Any] = field(default_factory=dict)

    def mark_sent(self, provider_message_id: str):
        """Mark message as sent"""
        if self.status not in [MessageStatus.PENDING, MessageStatus.QUEUED]:
            raise BusinessRuleViolation(f"Cannot mark {self.status} message as sent")

        self.status = MessageStatus.SENT
        self.sent_at = datetime.utcnow()
        self.provider_message_id = provider_message_id

    def mark_delivered(self):
        """Mark message as delivered"""
        if self.status != MessageStatus.SENT:
            raise BusinessRuleViolation(f"Cannot mark {self.status} message as delivered")

        self.status = MessageStatus.DELIVERED
        self.delivered_at = datetime.utcnow()

    def mark_read(self):
        """Mark message as read"""
        if self.status != MessageStatus.DELIVERED:
            raise BusinessRuleViolation(f"Cannot mark {self.status} message as read")

        self.status = MessageStatus.READ
        self.read_at = datetime.utcnow()

    def mark_failed(self, reason: str):
        """Mark message as failed"""
        self.status = MessageStatus.FAILED
        self.failure_reason = reason
        self.failed_at = datetime.utcnow()
        self.retry_count += 1

    def can_retry(self, max_retries: int) -> bool:
        """Check if message can be retried"""
        return self.status == MessageStatus.FAILED and self.retry_count < max_retries


@dataclass
class Broadcast(AggregateRoot):
    """
    Broadcast Aggregate Root - Mass communication campaigns
    As defined in DDD_ARCHITECTURE_REFACTORING.md Section 2.11
    """
    # Identifiers
    store_id: UUID = field(default_factory=uuid4)
    tenant_id: UUID = field(default_factory=uuid4)
    broadcast_name: str = ""
    description: Optional[str] = None

    # Status
    status: BroadcastStatus = BroadcastStatus.DRAFT

    # Message details
    message_type: MessageType = MessageType.EMAIL
    message_category: MessageCategory = MessageCategory.PROMOTIONAL
    message_priority: MessagePriority = MessagePriority.NORMAL

    # Content
    message_content: Optional[MessageContent] = None
    template_used: Optional[str] = None  # Template name if using template

    # Audience
    audience_filter: Optional[BroadcastFilter] = None
    total_recipients: int = 0

    # Messages
    messages: List[Message] = field(default_factory=list)

    # Delivery settings
    delivery_settings: Optional[DeliverySettings] = None

    # Statistics
    total_sent: int = 0
    total_delivered: int = 0
    total_failed: int = 0
    total_read: int = 0

    # Timestamps
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    scheduled_time: Optional[datetime] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    # Created by
    created_by: Optional[UUID] = None

    # Metadata
    metadata: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def create(
        cls,
        store_id: UUID,
        tenant_id: UUID,
        broadcast_name: str,
        message_type: MessageType,
        message_category: MessageCategory,
        message_content: MessageContent,
        audience_filter: BroadcastFilter,
        created_by: Optional[UUID] = None
    ) -> 'Broadcast':
        """Factory method to create new broadcast"""
        if not broadcast_name:
            raise BusinessRuleViolation("Broadcast name is required")

        broadcast = cls(
            store_id=store_id,
            tenant_id=tenant_id,
            broadcast_name=broadcast_name,
            message_type=message_type,
            message_category=message_category,
            message_content=message_content,
            audience_filter=audience_filter,
            created_by=created_by,
            status=BroadcastStatus.DRAFT
        )

        # Raise creation event
        broadcast.add_domain_event(BroadcastCreated(
            broadcast_id=broadcast.id,
            broadcast_name=broadcast_name,
            message_type=message_type,
            audience_segment=audience_filter.audience_segment
        ))

        return broadcast

    def schedule(self, scheduled_time: datetime, delivery_settings: DeliverySettings):
        """Schedule the broadcast"""
        if self.status != BroadcastStatus.DRAFT:
            raise BusinessRuleViolation(f"Cannot schedule {self.status} broadcast")

        if scheduled_time <= datetime.utcnow():
            raise BusinessRuleViolation("Scheduled time must be in the future")

        if not self.message_content:
            raise BusinessRuleViolation("Message content is required")

        if len(self.messages) == 0:
            raise BusinessRuleViolation("No recipients added")

        self.scheduled_time = scheduled_time
        self.delivery_settings = delivery_settings
        self.status = BroadcastStatus.SCHEDULED

        # Raise event
        self.add_domain_event(BroadcastScheduled(
            broadcast_id=self.id,
            broadcast_name=self.broadcast_name,
            scheduled_time=scheduled_time
        ))

        self.mark_as_modified()

    def add_recipients(self, recipients: List[Recipient]):
        """Add recipients to broadcast"""
        if self.status not in [BroadcastStatus.DRAFT, BroadcastStatus.SCHEDULED]:
            raise BusinessRuleViolation(f"Cannot add recipients to {self.status} broadcast")

        for recipient in recipients:
            # Create message for each recipient
            message = Message(recipient=recipient)
            self.messages.append(message)

        self.total_recipients = len(self.messages)
        self.mark_as_modified()

    def start_sending(self):
        """Start sending the broadcast"""
        if self.status != BroadcastStatus.SCHEDULED:
            raise BusinessRuleViolation(f"Cannot start {self.status} broadcast")

        if len(self.messages) == 0:
            raise BusinessRuleViolation("No messages to send")

        self.status = BroadcastStatus.SENDING
        self.started_at = datetime.utcnow()

        # Raise event
        self.add_domain_event(BroadcastStarted(
            broadcast_id=self.id,
            broadcast_name=self.broadcast_name,
            started_at=self.started_at,
            total_recipients=self.total_recipients
        ))

        self.mark_as_modified()

    def mark_message_sent(
        self,
        message_id: UUID,
        provider_message_id: str
    ):
        """Mark a specific message as sent"""
        if self.status not in [BroadcastStatus.SENDING, BroadcastStatus.SENT]:
            raise BusinessRuleViolation(f"Cannot mark sent in {self.status} broadcast")

        message = self.get_message(message_id)
        if not message:
            raise BusinessRuleViolation(f"Message {message_id} not found")

        message.mark_sent(provider_message_id)
        self.total_sent += 1

        # Raise event
        self.add_domain_event(MessageSent(
            broadcast_id=self.id,
            message_id=message_id,
            recipient_id=message.recipient.recipient_id or "",
            message_type=self.message_type,
            sent_at=message.sent_at
        ))

        # Update status if all sent
        if self.total_sent == self.total_recipients:
            self.status = BroadcastStatus.SENT

        self.mark_as_modified()

    def mark_message_delivered(self, message_id: UUID):
        """Mark a specific message as delivered"""
        message = self.get_message(message_id)
        if not message:
            raise BusinessRuleViolation(f"Message {message_id} not found")

        message.mark_delivered()
        self.total_delivered += 1

        # Raise event
        self.add_domain_event(MessageDelivered(
            broadcast_id=self.id,
            message_id=message_id,
            recipient_id=message.recipient.recipient_id or "",
            delivered_at=message.delivered_at
        ))

        self.mark_as_modified()

    def mark_message_failed(
        self,
        message_id: UUID,
        failure_reason: str
    ):
        """Mark a specific message as failed"""
        message = self.get_message(message_id)
        if not message:
            raise BusinessRuleViolation(f"Message {message_id} not found")

        message.mark_failed(failure_reason)
        self.total_failed += 1

        # Raise event
        self.add_domain_event(MessageFailed(
            broadcast_id=self.id,
            message_id=message_id,
            recipient_id=message.recipient.recipient_id or "",
            failure_reason=failure_reason,
            failed_at=message.failed_at
        ))

        self.mark_as_modified()

    def complete(self):
        """Complete the broadcast"""
        if self.status not in [BroadcastStatus.SENDING, BroadcastStatus.SENT]:
            raise BusinessRuleViolation(f"Cannot complete {self.status} broadcast")

        self.status = BroadcastStatus.COMPLETED
        self.completed_at = datetime.utcnow()

        # Raise event
        self.add_domain_event(BroadcastCompleted(
            broadcast_id=self.id,
            broadcast_name=self.broadcast_name,
            completed_at=self.completed_at,
            total_sent=self.total_sent,
            total_delivered=self.total_delivered,
            total_failed=self.total_failed
        ))

        self.mark_as_modified()

    def cancel(self):
        """Cancel the broadcast"""
        if self.status not in [BroadcastStatus.DRAFT, BroadcastStatus.SCHEDULED]:
            raise BusinessRuleViolation(f"Cannot cancel {self.status} broadcast")

        self.status = BroadcastStatus.CANCELLED
        self.mark_as_modified()

    def get_message(self, message_id: UUID) -> Optional[Message]:
        """Get message by ID"""
        return next((m for m in self.messages if m.id == message_id), None)

    def get_failed_messages(self) -> List[Message]:
        """Get all failed messages"""
        return [m for m in self.messages if m.status == MessageStatus.FAILED]

    def get_retryable_messages(self) -> List[Message]:
        """Get messages that can be retried"""
        max_retries = self.delivery_settings.max_retries if self.delivery_settings else 3
        return [m for m in self.messages if m.can_retry(max_retries)]

    def get_success_rate(self) -> float:
        """Calculate success rate (delivered / sent)"""
        if self.total_sent == 0:
            return 0.0

        return (self.total_delivered / self.total_sent) * 100

    def get_delivery_rate(self) -> float:
        """Calculate delivery rate (delivered / total recipients)"""
        if self.total_recipients == 0:
            return 0.0

        return (self.total_delivered / self.total_recipients) * 100

    def is_ready_to_send(self) -> bool:
        """Check if broadcast is ready to send"""
        if self.status != BroadcastStatus.SCHEDULED:
            return False

        if not self.scheduled_time:
            return False

        return datetime.utcnow() >= self.scheduled_time

    def validate(self) -> List[str]:
        """Validate broadcast"""
        errors = []

        if not self.broadcast_name:
            errors.append("Broadcast name is required")

        if not self.store_id:
            errors.append("Store ID is required")

        if not self.tenant_id:
            errors.append("Tenant ID is required")

        if not self.message_content:
            errors.append("Message content is required")

        if not self.audience_filter:
            errors.append("Audience filter is required")

        if self.status == BroadcastStatus.SCHEDULED and not self.scheduled_time:
            errors.append("Scheduled broadcasts must have a scheduled time")

        if len(self.messages) == 0 and self.status != BroadcastStatus.DRAFT:
            errors.append("Broadcast must have recipients")

        return errors
