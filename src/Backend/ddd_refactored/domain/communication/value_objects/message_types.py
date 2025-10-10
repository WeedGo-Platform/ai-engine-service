"""
Communication Context Value Objects
Following DDD Architecture Document Section 2.11
"""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Optional, Dict, Any

from ....shared.domain_base import ValueObject


class MessageType(str, Enum):
    """Type of message"""
    SMS = "sms"
    EMAIL = "email"
    PUSH_NOTIFICATION = "push_notification"
    IN_APP = "in_app"
    WHATSAPP = "whatsapp"


class MessageStatus(str, Enum):
    """Message delivery status"""
    PENDING = "pending"
    QUEUED = "queued"
    SENT = "sent"
    DELIVERED = "delivered"
    READ = "read"
    FAILED = "failed"
    BOUNCED = "bounced"
    UNSUBSCRIBED = "unsubscribed"


class MessagePriority(str, Enum):
    """Message priority"""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


class BroadcastStatus(str, Enum):
    """Broadcast campaign status"""
    DRAFT = "draft"
    SCHEDULED = "scheduled"
    SENDING = "sending"
    SENT = "sent"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    FAILED = "failed"


class AudienceSegment(str, Enum):
    """Target audience segment"""
    ALL_CUSTOMERS = "all_customers"
    NEW_CUSTOMERS = "new_customers"
    VIP_CUSTOMERS = "vip_customers"
    INACTIVE_CUSTOMERS = "inactive_customers"
    MEDICAL_PATIENTS = "medical_patients"
    RECREATIONAL_USERS = "recreational_users"
    CUSTOM = "custom"


class MessageCategory(str, Enum):
    """Category of message"""
    TRANSACTIONAL = "transactional"  # Order confirmations, receipts
    PROMOTIONAL = "promotional"  # Sales, discounts
    INFORMATIONAL = "informational"  # Updates, news
    REMINDER = "reminder"  # Appointment, pickup reminders
    ALERT = "alert"  # Urgent notifications


@dataclass(frozen=True)
class MessageContent(ValueObject):
    """
    Message content with template support
    """
    subject: Optional[str] = None  # For email
    body: str = ""
    html_body: Optional[str] = None  # For email HTML

    # Template variables
    template_variables: Optional[Dict[str, Any]] = None

    # Media attachments
    attachment_urls: Optional[tuple[str, ...]] = None

    def __post_init__(self):
        """Validate message content"""
        if not self.body:
            raise ValueError("Message body is required")

        if len(self.body) > 10000:
            raise ValueError("Message body too long (max 10000 characters)")

        if self.subject and len(self.subject) > 500:
            raise ValueError("Subject too long (max 500 characters)")

    def render(self, variables: Optional[Dict[str, Any]] = None) -> str:
        """Render template with variables"""
        rendered_body = self.body

        # Merge template variables
        all_vars = dict(self.template_variables or {})
        if variables:
            all_vars.update(variables)

        # Simple template variable substitution
        for key, value in all_vars.items():
            placeholder = f"{{{{{key}}}}}"
            rendered_body = rendered_body.replace(placeholder, str(value))

        return rendered_body

    def has_attachments(self) -> bool:
        """Check if message has attachments"""
        return bool(self.attachment_urls)


@dataclass(frozen=True)
class Recipient(ValueObject):
    """
    Message recipient details
    """
    recipient_id: Optional[str] = None  # Customer ID

    # Contact details
    email: Optional[str] = None
    phone: Optional[str] = None
    device_token: Optional[str] = None  # For push notifications

    # Personalization
    first_name: Optional[str] = None
    last_name: Optional[str] = None

    # Preferences
    language: str = "en"
    timezone: str = "America/Toronto"

    def __post_init__(self):
        """Validate recipient"""
        # Must have at least one contact method
        if not any([self.email, self.phone, self.device_token]):
            raise ValueError("Recipient must have at least one contact method")

        # Validate email format
        if self.email:
            import re
            email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            if not re.match(email_pattern, self.email):
                raise ValueError("Invalid email format")

        # Validate phone format (Canadian numbers)
        if self.phone:
            import re
            # Remove formatting
            digits = re.sub(r'\D', '', self.phone)
            if len(digits) != 10 and len(digits) != 11:
                raise ValueError("Invalid phone number format")

    def get_full_name(self) -> str:
        """Get full name"""
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        elif self.first_name:
            return self.first_name
        elif self.last_name:
            return self.last_name
        return "Customer"

    def get_personalization_vars(self) -> Dict[str, str]:
        """Get personalization variables for templates"""
        return {
            'first_name': self.first_name or 'Customer',
            'last_name': self.last_name or '',
            'full_name': self.get_full_name()
        }


@dataclass(frozen=True)
class DeliverySettings(ValueObject):
    """
    Message delivery settings
    """
    # Scheduling
    send_immediately: bool = True
    scheduled_time: Optional[datetime] = None

    # Retry settings
    max_retries: int = 3
    retry_interval_minutes: int = 5

    # Rate limiting
    max_sends_per_minute: Optional[int] = None

    # Delivery window (for scheduled messages)
    delivery_window_start_hour: Optional[int] = None  # 0-23
    delivery_window_end_hour: Optional[int] = None  # 0-23

    def __post_init__(self):
        """Validate delivery settings"""
        if not self.send_immediately and not self.scheduled_time:
            raise ValueError("Must specify scheduled_time if not sending immediately")

        if self.scheduled_time and self.scheduled_time <= datetime.utcnow():
            raise ValueError("Scheduled time must be in the future")

        if self.max_retries < 0:
            raise ValueError("Max retries cannot be negative")

        if self.retry_interval_minutes <= 0:
            raise ValueError("Retry interval must be positive")

        if self.max_sends_per_minute and self.max_sends_per_minute <= 0:
            raise ValueError("Max sends per minute must be positive")

        if self.delivery_window_start_hour is not None:
            if self.delivery_window_start_hour < 0 or self.delivery_window_start_hour > 23:
                raise ValueError("Delivery window start hour must be 0-23")

        if self.delivery_window_end_hour is not None:
            if self.delivery_window_end_hour < 0 or self.delivery_window_end_hour > 23:
                raise ValueError("Delivery window end hour must be 0-23")

    def is_in_delivery_window(self, current_time: datetime) -> bool:
        """Check if current time is within delivery window"""
        if self.delivery_window_start_hour is None:
            return True

        hour = current_time.hour

        if self.delivery_window_end_hour > self.delivery_window_start_hour:
            # Normal window (e.g., 9am to 5pm)
            return self.delivery_window_start_hour <= hour < self.delivery_window_end_hour
        else:
            # Overnight window (e.g., 10pm to 6am)
            return hour >= self.delivery_window_start_hour or hour < self.delivery_window_end_hour


@dataclass(frozen=True)
class BroadcastFilter(ValueObject):
    """
    Filters for audience targeting
    """
    audience_segment: AudienceSegment = AudienceSegment.ALL_CUSTOMERS

    # Customer attributes
    min_order_count: Optional[int] = None
    max_order_count: Optional[int] = None
    min_total_spent: Optional[float] = None

    # Activity filters
    last_order_days_ago_min: Optional[int] = None
    last_order_days_ago_max: Optional[int] = None

    # Location filters
    cities: Optional[tuple[str, ...]] = None
    provinces: Optional[tuple[str, ...]] = None
    postal_code_prefixes: Optional[tuple[str, ...]] = None

    # Preferences
    opted_in_only: bool = True
    exclude_unsubscribed: bool = True

    def __post_init__(self):
        """Validate broadcast filter"""
        if self.min_order_count and self.min_order_count < 0:
            raise ValueError("Min order count cannot be negative")

        if self.max_order_count and self.max_order_count < 0:
            raise ValueError("Max order count cannot be negative")

        if self.min_order_count and self.max_order_count:
            if self.max_order_count < self.min_order_count:
                raise ValueError("Max order count must be >= min order count")

    def matches_segment(self, segment: str) -> bool:
        """Check if segment matches filter"""
        if self.audience_segment == AudienceSegment.ALL_CUSTOMERS:
            return True

        return self.audience_segment.value == segment


@dataclass(frozen=True)
class MessageTemplate(ValueObject):
    """
    Reusable message template
    """
    template_name: str
    template_category: MessageCategory

    # Template content
    subject_template: Optional[str] = None
    body_template: str = ""

    # Required variables
    required_variables: Optional[tuple[str, ...]] = None

    # Multi-language support
    language: str = "en"

    def __post_init__(self):
        """Validate message template"""
        if not self.template_name:
            raise ValueError("Template name is required")

        if not self.body_template:
            raise ValueError("Body template is required")

    def get_variables(self) -> set[str]:
        """Extract all template variables from body"""
        import re
        pattern = r'\{\{(\w+)\}\}'

        variables = set()
        variables.update(re.findall(pattern, self.body_template))

        if self.subject_template:
            variables.update(re.findall(pattern, self.subject_template))

        return variables

    def validate_variables(self, provided_vars: Dict[str, Any]) -> tuple[bool, list[str]]:
        """Validate that all required variables are provided"""
        if not self.required_variables:
            return True, []

        missing = []
        for var in self.required_variables:
            if var not in provided_vars:
                missing.append(var)

        return len(missing) == 0, missing
