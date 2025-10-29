"""
Unified Messaging Service with Multi-Provider Failover
Follows Circuit Breaker and Strategy patterns for resilience
"""

import logging
import asyncio
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from enum import Enum
import os

from .base_channel import (
    ICommunicationChannel,
    ChannelType,
    ChannelConfig,
    Recipient,
    Message,
    DeliveryResult,
    DeliveryStatus,
    ProviderHealth,
    ProviderStatus
)

# Provider imports
from .aws_ses_provider import AWSSESProvider
from .aws_sns_provider import AWSSNSProvider
from .email_service import EmailService
from .sms_service import SMSService
from .console_sms_provider import ConsoleSMSProvider
from .smtp_email_provider import SMTPEmailProvider

logger = logging.getLogger(__name__)


class ProviderPriority(Enum):
    """Provider priority levels"""
    PRIMARY = 1
    SECONDARY = 2
    TERTIARY = 3
    FALLBACK = 4


class CircuitBreakerState(Enum):
    """Circuit breaker states"""
    CLOSED = "closed"  # Normal operation
    OPEN = "open"      # Failing, don't try
    HALF_OPEN = "half_open"  # Testing if recovered


class CircuitBreaker:
    """
    Circuit breaker for provider health management
    Prevents cascading failures
    """

    def __init__(
        self,
        failure_threshold: int = 5,
        success_threshold: int = 2,
        timeout_seconds: int = 60
    ):
        self.failure_threshold = failure_threshold
        self.success_threshold = success_threshold
        self.timeout_seconds = timeout_seconds

        self.failure_count = 0
        self.success_count = 0
        self.state = CircuitBreakerState.CLOSED
        self.last_failure_time: Optional[datetime] = None

    def record_success(self):
        """Record successful operation"""
        self.failure_count = 0

        if self.state == CircuitBreakerState.HALF_OPEN:
            self.success_count += 1
            if self.success_count >= self.success_threshold:
                self.state = CircuitBreakerState.CLOSED
                self.success_count = 0
                logger.info("Circuit breaker closed - provider recovered")

    def record_failure(self):
        """Record failed operation"""
        self.failure_count += 1
        self.last_failure_time = datetime.now()
        self.success_count = 0

        if self.failure_count >= self.failure_threshold:
            self.state = CircuitBreakerState.OPEN
            logger.warning(f"Circuit breaker opened after {self.failure_count} failures")

    def can_attempt(self) -> bool:
        """Check if operation can be attempted"""
        if self.state == CircuitBreakerState.CLOSED:
            return True

        if self.state == CircuitBreakerState.OPEN:
            if self.last_failure_time:
                time_since_failure = (datetime.now() - self.last_failure_time).total_seconds()
                if time_since_failure >= self.timeout_seconds:
                    self.state = CircuitBreakerState.HALF_OPEN
                    logger.info("Circuit breaker half-open - testing provider")
                    return True
            return False

        # HALF_OPEN state
        return True

    @property
    def is_healthy(self) -> bool:
        """Check if provider is healthy"""
        return self.state in (CircuitBreakerState.CLOSED, CircuitBreakerState.HALF_OPEN)


class UnifiedMessagingService:
    """
    Unified messaging service with multi-provider failover
    Supports email and SMS with automatic provider selection
    """

    def __init__(self, db_pool: Optional[Any] = None):
        self.db_pool = db_pool

        # Email providers (in priority order)
        self.email_providers: List[Tuple[ICommunicationChannel, ProviderPriority, CircuitBreaker]] = []

        # SMS providers (in priority order)
        self.sms_providers: List[Tuple[ICommunicationChannel, ProviderPriority, CircuitBreaker]] = []

        # Initialize providers
        self._initialize_providers()

    def _initialize_providers(self):
        """Initialize all messaging providers"""
        # Email providers
        self._init_email_providers()

        # SMS providers
        self._init_sms_providers()

    def _init_email_providers(self):
        """Initialize email providers in priority order"""
        # 1. AWS SES (Primary) - Best cost/performance
        if os.getenv('AWS_ACCESS_KEY_ID') or os.getenv('AWS_REGION'):
            try:
                ses_config = ChannelConfig(
                    enabled=True,
                    rate_limit=14,  # SES limit is 14 emails/sec by default
                    cost_per_message=0.0001,  # $0.10 per 1000 emails
                    timeout=30
                )
                ses_provider = AWSSESProvider(ses_config)
                circuit_breaker = CircuitBreaker(failure_threshold=5, timeout_seconds=300)
                self.email_providers.append((ses_provider, ProviderPriority.PRIMARY, circuit_breaker))
                logger.info("AWS SES initialized as PRIMARY email provider")
            except Exception as e:
                logger.warning(f"Failed to initialize AWS SES: {e}")

        # 2. SendGrid (Secondary) - Reliable fallback
        if os.getenv('SENDGRID_API_KEY'):
            try:
                sendgrid_config = ChannelConfig(
                    enabled=True,
                    rate_limit=10,
                    cost_per_message=0.0,  # Free tier (100/day)
                    api_key=os.getenv('SENDGRID_API_KEY'),
                    timeout=30,
                    retry_attempts=0  # Don't retry SendGrid - fail fast
                )
                sendgrid_provider = EmailService(sendgrid_config, provider="sendgrid")
                circuit_breaker = CircuitBreaker(failure_threshold=1, timeout_seconds=300)  # Fail after 1 attempt
                self.email_providers.append((sendgrid_provider, ProviderPriority.SECONDARY, circuit_breaker))
                logger.info("SendGrid initialized as SECONDARY email provider")
            except Exception as e:
                logger.warning(f"Failed to initialize SendGrid: {e}")

        # 3. Gmail SMTP (Tertiary) - Last resort fallback
        if os.getenv('SMTP_USER') and os.getenv('SMTP_PASSWORD'):
            try:
                smtp_config = ChannelConfig(
                    enabled=True,
                    rate_limit=1,  # Conservative rate for SMTP (1 email/sec)
                    cost_per_message=0.0,  # Free
                    timeout=30
                )
                smtp_provider = SMTPEmailProvider(smtp_config)
                circuit_breaker = CircuitBreaker(failure_threshold=3, timeout_seconds=180)
                self.email_providers.append((smtp_provider, ProviderPriority.TERTIARY, circuit_breaker))
                logger.info("SMTP initialized as TERTIARY email provider")
            except Exception as e:
                logger.warning(f"Failed to initialize SMTP: {e}")

    def _init_sms_providers(self):
        """Initialize SMS providers in priority order"""
        # 1. AWS SNS (Primary) - Best cost for high volume
        if os.getenv('AWS_ACCESS_KEY_ID') or os.getenv('AWS_REGION'):
            try:
                sns_config = ChannelConfig(
                    enabled=True,
                    rate_limit=10,  # Conservative SMS rate
                    cost_per_message=0.00645,  # US/Canada rate
                    timeout=30
                )
                sns_provider = AWSSNSProvider(sns_config)
                circuit_breaker = CircuitBreaker(failure_threshold=5, timeout_seconds=300)
                self.sms_providers.append((sns_provider, ProviderPriority.PRIMARY, circuit_breaker))
                logger.info("AWS SNS initialized as PRIMARY SMS provider")
            except Exception as e:
                logger.warning(f"Failed to initialize AWS SNS: {e}")

        # 2. Twilio (Secondary) - Reliable fallback
        if os.getenv('TWILIO_ACCOUNT_SID') and os.getenv('TWILIO_AUTH_TOKEN'):
            try:
                twilio_config = ChannelConfig(
                    enabled=True,
                    rate_limit=5,
                    cost_per_message=0.0075,  # Twilio US rate
                    api_key=os.getenv('TWILIO_ACCOUNT_SID'),
                    api_secret=os.getenv('TWILIO_AUTH_TOKEN'),
                    timeout=30
                )
                twilio_provider = SMSService(twilio_config)
                circuit_breaker = CircuitBreaker(failure_threshold=3, timeout_seconds=180)
                self.sms_providers.append((twilio_provider, ProviderPriority.SECONDARY, circuit_breaker))
                logger.info("Twilio initialized as SECONDARY SMS provider")
            except Exception as e:
                logger.warning(f"Failed to initialize Twilio: {e}")

        # 3. Console Provider (Fallback) - Development/Testing
        # Always available as last resort for development environments
        try:
            console_config = ChannelConfig(
                enabled=True,
                rate_limit=100,  # No real limit for console
                cost_per_message=0.0,
                timeout=5
            )
            console_provider = ConsoleSMSProvider(console_config)
            circuit_breaker = CircuitBreaker(failure_threshold=999, timeout_seconds=1)
            self.sms_providers.append((console_provider, ProviderPriority.FALLBACK, circuit_breaker))
            logger.info("Console SMS initialized as FALLBACK provider (development mode)")
        except Exception as e:
            logger.warning(f"Failed to initialize Console SMS: {e}")

    async def send_email(
        self,
        to: str,
        subject: str,
        html_content: str,
        text_content: Optional[str] = None,
        from_email: Optional[str] = None,
        from_name: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> DeliveryResult:
        """
        Send email with automatic provider failover
        Tries providers in priority order until successful
        """
        recipient = Recipient(
            id=to,
            email=to,
            metadata=metadata
        )

        message = Message(
            subject=subject,
            content=html_content,
            sender_email=from_email,
            sender_name=from_name,
            metadata=metadata,
            template_variables={'text_content': text_content} if text_content else None
        )

        return await self._send_with_failover(
            recipient,
            message,
            self.email_providers,
            "email"
        )

    async def send_sms(
        self,
        to: str,
        message_body: str,
        from_number: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> DeliveryResult:
        """
        Send SMS with automatic provider failover
        Tries providers in priority order until successful
        """
        recipient = Recipient(
            id=to,
            phone=to,
            metadata=metadata
        )

        message = Message(
            content=message_body,
            sender_phone=from_number,
            metadata=metadata
        )

        return await self._send_with_failover(
            recipient,
            message,
            self.sms_providers,
            "sms"
        )

    async def _send_with_failover(
        self,
        recipient: Recipient,
        message: Message,
        providers: List[Tuple[ICommunicationChannel, ProviderPriority, CircuitBreaker]],
        channel_type: str
    ) -> DeliveryResult:
        """
        Send message with automatic failover through provider chain
        Strategy: Try PRIMARY → wait 2s → try SECONDARY once → TERTIARY (only on network errors)
        """
        if not providers:
            return DeliveryResult(
                message_id=f"no-provider-{datetime.now().timestamp()}",
                recipient_id=recipient.id,
                status=DeliveryStatus.FAILED,
                channel=ChannelType.EMAIL if channel_type == "email" else ChannelType.SMS,
                error_message=f"No {channel_type} providers configured",
                sent_at=datetime.now()
            )

        errors = []
        sorted_providers = sorted(providers, key=lambda x: x[1].value)
        
        # Try each provider in priority order
        for idx, (provider, priority, circuit_breaker) in enumerate(sorted_providers):
            # Check circuit breaker
            if not circuit_breaker.can_attempt():
                logger.warning(f"Skipping provider {provider.__class__.__name__} - circuit breaker open")
                continue

            # Add delay between providers (2 seconds after PRIMARY fails)
            if idx > 0:
                await asyncio.sleep(2.0)
                logger.info(f"Waiting 2 seconds before trying {provider.__class__.__name__}")

            try:
                # Attempt to send
                logger.info(f"Attempting to send via {provider.__class__.__name__} ({priority.name})")
                result = await provider.send_single(recipient, message)

                if result.status == DeliveryStatus.SENT:
                    # Success!
                    circuit_breaker.record_success()
                    logger.info(f"✅ Message sent via {provider.__class__.__name__} ({priority.name})")
                    return result
                else:
                    # Provider returned failure
                    circuit_breaker.record_failure()
                    error_msg = result.error_message or "Unknown error"
                    errors.append(f"{provider.__class__.__name__}: {error_msg}")
                    logger.warning(f"❌ Provider {provider.__class__.__name__} failed: {error_msg}")
                    
                    # Check if it's a network error (retryable with next provider)
                    is_network_error = any([
                        'timeout' in error_msg.lower(),
                        'connection' in error_msg.lower(),
                        'network' in error_msg.lower(),
                        '5' in error_msg and error_msg.index('5') < 3,  # 5xx errors
                    ])
                    
                    # Stop failover chain if not a network error and we've tried PRIMARY and SECONDARY
                    if not is_network_error and priority.value >= ProviderPriority.SECONDARY.value:
                        logger.info(f"Stopping failover - non-network error from {priority.name} provider")
                        break

            except Exception as e:
                # Provider threw exception
                circuit_breaker.record_failure()
                error_msg = str(e)
                errors.append(f"{provider.__class__.__name__}: {error_msg}")
                logger.error(f"❌ Provider {provider.__class__.__name__} exception: {e}")
                
                # Check if it's a network error
                is_network_error = any([
                    'timeout' in error_msg.lower(),
                    'connection' in error_msg.lower(),
                    'network' in error_msg.lower(),
                    'timed out' in error_msg.lower(),
                ])
                
                # Stop failover chain if not a network error and we've tried PRIMARY and SECONDARY
                if not is_network_error and priority.value >= ProviderPriority.SECONDARY.value:
                    logger.info(f"Stopping failover - non-network exception from {priority.name} provider")
                    break

        # All providers failed
        return DeliveryResult(
            message_id=f"all-failed-{datetime.now().timestamp()}",
            recipient_id=recipient.id,
            status=DeliveryStatus.FAILED,
            channel=ChannelType.EMAIL if channel_type == "email" else ChannelType.SMS,
            error_message=f"All providers failed: {'; '.join(errors)}",
            sent_at=datetime.now(),
            metadata={'attempted_providers': len(errors), 'errors': errors}
        )

    async def get_provider_health(self) -> Dict[str, Any]:
        """Get health status of all providers"""
        health = {
            'email_providers': [],
            'sms_providers': []
        }

        for provider, priority, circuit_breaker in self.email_providers:
            health['email_providers'].append({
                'name': provider.__class__.__name__,
                'priority': priority.name,
                'circuit_breaker': circuit_breaker.state.value,
                'is_healthy': circuit_breaker.is_healthy,
                'failure_count': circuit_breaker.failure_count
            })

        for provider, priority, circuit_breaker in self.sms_providers:
            health['sms_providers'].append({
                'name': provider.__class__.__name__,
                'priority': priority.name,
                'circuit_breaker': circuit_breaker.state.value,
                'is_healthy': circuit_breaker.is_healthy,
                'failure_count': circuit_breaker.failure_count
            })

        return health
