"""
ChatConversation Aggregate Root - BASIC CHAT ONLY (NO AGI)
Following DDD Architecture Document Section 2.13
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List, Dict, Any
from uuid import UUID, uuid4

from ....shared.domain_base import AggregateRoot, DomainEvent, BusinessRuleViolation
from ..value_objects.chat_types import (
    ConversationStatus,
    MessageRole,
    MessageType,
    SatisfactionRating,
    MessageContent,
    ParticipantInfo,
    ConversationSummary,
    QuickReply
)


# Domain Events
class ConversationStarted(DomainEvent):
    conversation_id: UUID
    customer_id: str
    started_at: datetime


class MessageReceived(DomainEvent):
    conversation_id: UUID
    message_id: UUID
    sender_role: MessageRole
    message_text: str
    received_at: datetime


class AgentAssigned(DomainEvent):
    conversation_id: UUID
    agent_id: str
    agent_name: str
    assigned_at: datetime


class ConversationResolved(DomainEvent):
    conversation_id: UUID
    resolved_by: str
    resolved_at: datetime


class ConversationClosed(DomainEvent):
    conversation_id: UUID
    closed_at: datetime
    duration_minutes: int


class SatisfactionProvided(DomainEvent):
    conversation_id: UUID
    rating: SatisfactionRating
    rated_at: datetime


@dataclass
class ChatMessage:
    """Individual chat message entity"""
    id: UUID = field(default_factory=uuid4)
    content: MessageContent = None
    sender: ParticipantInfo = None

    # Timestamps
    sent_at: datetime = field(default_factory=datetime.utcnow)
    delivered_at: Optional[datetime] = None
    read_at: Optional[datetime] = None

    # Quick replies (for agent messages)
    quick_replies: List[QuickReply] = field(default_factory=list)

    # Metadata
    metadata: Dict[str, Any] = field(default_factory=dict)

    def mark_delivered(self):
        """Mark message as delivered"""
        if not self.delivered_at:
            self.delivered_at = datetime.utcnow()

    def mark_read(self):
        """Mark message as read"""
        if not self.read_at:
            self.read_at = datetime.utcnow()
            if not self.delivered_at:
                self.delivered_at = self.read_at

    def is_from_customer(self) -> bool:
        """Check if message is from customer"""
        return self.sender.is_customer()

    def is_from_agent(self) -> bool:
        """Check if message is from agent"""
        return self.sender.is_agent()


@dataclass
class ChatConversation(AggregateRoot):
    """
    ChatConversation Aggregate Root - Basic customer support chat
    INTENTIONALLY SIMPLE - NO AGI FEATURES
    As defined in DDD_ARCHITECTURE_REFACTORING.md Section 2.13
    """
    # Identifiers
    customer_id: str = ""
    store_id: UUID = field(default_factory=uuid4)
    tenant_id: UUID = field(default_factory=uuid4)

    # Status
    status: ConversationStatus = ConversationStatus.ACTIVE

    # Participants
    customer: Optional[ParticipantInfo] = None
    assigned_agent: Optional[ParticipantInfo] = None

    # Messages
    messages: List[ChatMessage] = field(default_factory=list)

    # Topic/subject
    subject: Optional[str] = None
    category: Optional[str] = None  # order_inquiry, product_question, complaint, etc.

    # Satisfaction
    satisfaction_rating: Optional[SatisfactionRating] = None
    satisfaction_comment: Optional[str] = None

    # Timestamps
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    first_response_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None
    closed_at: Optional[datetime] = None

    # Metadata
    metadata: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def create(
        cls,
        customer_id: str,
        store_id: UUID,
        tenant_id: UUID,
        customer_name: str,
        initial_message: str,
        subject: Optional[str] = None
    ) -> 'ChatConversation':
        """Factory method to create new conversation"""
        if not customer_id:
            raise BusinessRuleViolation("Customer ID is required")

        if not initial_message:
            raise BusinessRuleViolation("Initial message is required")

        # Create customer participant
        customer = ParticipantInfo(
            participant_id=customer_id,
            participant_role=MessageRole.CUSTOMER,
            display_name=customer_name
        )

        # Create conversation
        conversation = cls(
            customer_id=customer_id,
            store_id=store_id,
            tenant_id=tenant_id,
            customer=customer,
            subject=subject or "Customer Inquiry",
            status=ConversationStatus.WAITING
        )

        # Add initial message
        content = MessageContent(text=initial_message)
        conversation.add_message(content, customer)

        # Raise creation event
        conversation.add_domain_event(ConversationStarted(
            conversation_id=conversation.id,
            customer_id=customer_id,
            started_at=conversation.created_at
        ))

        return conversation

    def add_message(
        self,
        content: MessageContent,
        sender: ParticipantInfo,
        quick_replies: Optional[List[QuickReply]] = None
    ) -> UUID:
        """Add message to conversation"""
        if self.status == ConversationStatus.CLOSED:
            raise BusinessRuleViolation("Cannot add messages to closed conversation")

        message = ChatMessage(
            content=content,
            sender=sender,
            quick_replies=quick_replies or []
        )

        self.messages.append(message)
        self.updated_at = datetime.utcnow()

        # Track first agent response
        if sender.is_agent() and not self.first_response_at:
            self.first_response_at = message.sent_at

        # Update status
        if self.status == ConversationStatus.WAITING and sender.is_agent():
            self.status = ConversationStatus.ACTIVE

        # Raise event
        self.add_domain_event(MessageReceived(
            conversation_id=self.id,
            message_id=message.id,
            sender_role=sender.participant_role,
            message_text=content.text,
            received_at=message.sent_at
        ))

        self.mark_as_modified()
        return message.id

    def assign_agent(
        self,
        agent_id: str,
        agent_name: str,
        agent_email: Optional[str] = None,
        department: Optional[str] = None
    ):
        """Assign support agent to conversation"""
        if self.assigned_agent:
            raise BusinessRuleViolation("Conversation already has an assigned agent")

        agent = ParticipantInfo(
            participant_id=agent_id,
            participant_role=MessageRole.AGENT,
            display_name=agent_name,
            email=agent_email,
            department=department
        )

        self.assigned_agent = agent
        self.status = ConversationStatus.ACTIVE

        # Raise event
        self.add_domain_event(AgentAssigned(
            conversation_id=self.id,
            agent_id=agent_id,
            agent_name=agent_name,
            assigned_at=datetime.utcnow()
        ))

        self.mark_as_modified()

    def resolve(self, resolved_by: str):
        """Mark conversation as resolved"""
        if self.status == ConversationStatus.RESOLVED:
            raise BusinessRuleViolation("Conversation already resolved")

        if self.status == ConversationStatus.CLOSED:
            raise BusinessRuleViolation("Cannot resolve closed conversation")

        self.status = ConversationStatus.RESOLVED
        self.resolved_at = datetime.utcnow()

        # Raise event
        self.add_domain_event(ConversationResolved(
            conversation_id=self.id,
            resolved_by=resolved_by,
            resolved_at=self.resolved_at
        ))

        self.mark_as_modified()

    def close(self):
        """Close the conversation"""
        if self.status == ConversationStatus.CLOSED:
            raise BusinessRuleViolation("Conversation already closed")

        self.status = ConversationStatus.CLOSED
        self.closed_at = datetime.utcnow()

        # Calculate duration
        duration = (self.closed_at - self.created_at).total_seconds() / 60

        # Raise event
        self.add_domain_event(ConversationClosed(
            conversation_id=self.id,
            closed_at=self.closed_at,
            duration_minutes=int(duration)
        ))

        self.mark_as_modified()

    def add_satisfaction_rating(
        self,
        rating: SatisfactionRating,
        comment: Optional[str] = None
    ):
        """Add customer satisfaction rating"""
        if self.satisfaction_rating:
            raise BusinessRuleViolation("Conversation already has satisfaction rating")

        if self.status not in [ConversationStatus.RESOLVED, ConversationStatus.CLOSED]:
            raise BusinessRuleViolation("Can only rate resolved or closed conversations")

        self.satisfaction_rating = rating
        self.satisfaction_comment = comment

        # Raise event
        self.add_domain_event(SatisfactionProvided(
            conversation_id=self.id,
            rating=rating,
            rated_at=datetime.utcnow()
        ))

        self.mark_as_modified()

    def mark_message_read(self, message_id: UUID):
        """Mark specific message as read"""
        message = self.get_message(message_id)
        if not message:
            raise BusinessRuleViolation(f"Message {message_id} not found")

        message.mark_read()
        self.mark_as_modified()

    def get_message(self, message_id: UUID) -> Optional[ChatMessage]:
        """Get message by ID"""
        return next((m for m in self.messages if m.id == message_id), None)

    def get_customer_messages(self) -> List[ChatMessage]:
        """Get all customer messages"""
        return [m for m in self.messages if m.is_from_customer()]

    def get_agent_messages(self) -> List[ChatMessage]:
        """Get all agent messages"""
        return [m for m in self.messages if m.is_from_agent()]

    def get_unread_messages(self) -> List[ChatMessage]:
        """Get unread messages"""
        return [m for m in self.messages if not m.read_at]

    def get_duration_minutes(self) -> int:
        """Get conversation duration in minutes"""
        end_time = self.closed_at or datetime.utcnow()
        duration = (end_time - self.created_at).total_seconds() / 60
        return int(duration)

    def get_response_time_minutes(self) -> Optional[int]:
        """Get time to first response in minutes"""
        if not self.first_response_at:
            return None

        duration = (self.first_response_at - self.created_at).total_seconds() / 60
        return int(duration)

    def get_summary(self) -> ConversationSummary:
        """Get conversation summary"""
        customer_messages = len(self.get_customer_messages())
        agent_messages = len(self.get_agent_messages())

        resolution_time = None
        if self.resolved_at:
            resolution_time = int((self.resolved_at - self.created_at).total_seconds() / 60)

        return ConversationSummary(
            total_messages=len(self.messages),
            customer_messages=customer_messages,
            agent_messages=agent_messages,
            duration_minutes=self.get_duration_minutes(),
            satisfaction_rating=self.satisfaction_rating,
            satisfaction_comment=self.satisfaction_comment,
            was_resolved=(self.status == ConversationStatus.RESOLVED),
            resolution_time_minutes=resolution_time
        )

    def validate(self) -> List[str]:
        """Validate chat conversation"""
        errors = []

        if not self.customer_id:
            errors.append("Customer ID is required")

        if not self.store_id:
            errors.append("Store ID is required")

        if not self.tenant_id:
            errors.append("Tenant ID is required")

        if not self.customer:
            errors.append("Customer participant is required")

        if len(self.messages) == 0:
            errors.append("Conversation must have at least one message")

        return errors
