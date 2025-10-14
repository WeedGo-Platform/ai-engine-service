"""
Prometheus Metrics for AI Engine
WebSocket connections, signup flow, and API metrics
"""

from prometheus_client import Counter, Gauge, Histogram, Info
import time
from functools import wraps
from typing import Callable, Any
import logging

logger = logging.getLogger(__name__)


# =====================================================
# WebSocket Metrics
# =====================================================

# Connection counts
websocket_connections_total = Counter(
    'websocket_connections_total',
    'Total WebSocket connections',
    ['connection_type']  # user, admin, public
)

websocket_disconnections_total = Counter(
    'websocket_disconnections_total',
    'Total WebSocket disconnections',
    ['connection_type', 'reason']  # normal, error, timeout
)

websocket_active_connections = Gauge(
    'websocket_active_connections',
    'Currently active WebSocket connections',
    ['connection_type']
)

websocket_messages_sent_total = Counter(
    'websocket_messages_sent_total',
    'Total WebSocket messages sent',
    ['message_type']  # verification_code, signup_progress, admin_new_review, etc.
)

websocket_messages_received_total = Counter(
    'websocket_messages_received_total',
    'Total WebSocket messages received',
    ['connection_type']
)

websocket_message_send_errors_total = Counter(
    'websocket_message_send_errors_total',
    'Total WebSocket message send errors',
    ['error_type']
)

websocket_reconnections_total = Counter(
    'websocket_reconnections_total',
    'Total WebSocket reconnection attempts',
    ['connection_type', 'success']
)


# =====================================================
# Signup Flow Metrics
# =====================================================

signup_started_total = Counter(
    'signup_started_total',
    'Total signup flows started',
    ['verification_tier']  # auto_approved, manual_review
)

signup_completed_total = Counter(
    'signup_completed_total',
    'Total signup flows completed',
    ['verification_tier', 'outcome']  # success, failed
)

signup_step_duration_seconds = Histogram(
    'signup_step_duration_seconds',
    'Duration of each signup step',
    ['step'],  # validating_crsa, sending_code, verifying_code, creating_tenant
    buckets=[0.1, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0, 60.0]
)

signup_state_recovery_total = Counter(
    'signup_state_recovery_total',
    'Total signup state recoveries',
    ['step']  # which step was recovered from
)

verification_codes_sent_total = Counter(
    'verification_codes_sent_total',
    'Total verification codes sent',
    ['method']  # email, sms, websocket
)

verification_codes_verified_total = Counter(
    'verification_codes_verified_total',
    'Total verification code verifications',
    ['success']  # true, false
)

verification_attempts_total = Counter(
    'verification_attempts_total',
    'Total verification code attempts',
    ['attempt_number']  # 1, 2, 3
)


# =====================================================
# Admin Review Metrics
# =====================================================

admin_reviews_pending = Gauge(
    'admin_reviews_pending',
    'Currently pending admin reviews'
)

admin_review_duration_seconds = Histogram(
    'admin_review_duration_seconds',
    'Duration from submission to admin review',
    buckets=[60, 300, 900, 3600, 7200, 14400, 28800, 86400]  # 1m to 24h
)

admin_review_actions_total = Counter(
    'admin_review_actions_total',
    'Total admin review actions',
    ['action']  # approved, rejected
)


# =====================================================
# Redis Metrics
# =====================================================

redis_operations_total = Counter(
    'redis_operations_total',
    'Total Redis operations',
    ['operation', 'success']  # get, set, delete, etc.
)

redis_connection_errors_total = Counter(
    'redis_connection_errors_total',
    'Total Redis connection errors'
)

redis_operation_duration_seconds = Histogram(
    'redis_operation_duration_seconds',
    'Duration of Redis operations',
    ['operation'],
    buckets=[0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0]
)


# =====================================================
# API Metrics
# =====================================================

api_requests_total = Counter(
    'api_requests_total',
    'Total API requests',
    ['method', 'endpoint', 'status']
)

api_request_duration_seconds = Histogram(
    'api_request_duration_seconds',
    'API request duration',
    ['method', 'endpoint'],
    buckets=[0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0]
)

api_errors_total = Counter(
    'api_errors_total',
    'Total API errors',
    ['endpoint', 'error_type']
)


# =====================================================
# System Info
# =====================================================

system_info = Info('ai_engine', 'AI Engine system information')
system_info.info({
    'version': '5.0.0',
    'service': 'ai-engine',
    'environment': 'production'
})


# =====================================================
# Metric Helper Functions
# =====================================================

class MetricsContext:
    """Context manager for tracking operation duration"""

    def __init__(self, histogram: Histogram, labels: dict):
        self.histogram = histogram
        self.labels = labels
        self.start_time = None

    def __enter__(self):
        self.start_time = time.time()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        duration = time.time() - self.start_time
        self.histogram.labels(**self.labels).observe(duration)


def track_duration(histogram: Histogram, **labels):
    """Decorator to track function execution duration"""

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(*args, **kwargs) -> Any:
            start_time = time.time()
            try:
                result = await func(*args, **kwargs)
                return result
            finally:
                duration = time.time() - start_time
                histogram.labels(**labels).observe(duration)

        @wraps(func)
        def sync_wrapper(*args, **kwargs) -> Any:
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                return result
            finally:
                duration = time.time() - start_time
                histogram.labels(**labels).observe(duration)

        # Return appropriate wrapper based on function type
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator


# =====================================================
# Metrics Collection Functions
# =====================================================

def track_websocket_connection(connection_type: str):
    """Track new WebSocket connection"""
    websocket_connections_total.labels(connection_type=connection_type).inc()
    websocket_active_connections.labels(connection_type=connection_type).inc()
    logger.debug(f"Metrics: WebSocket connection ({connection_type})")


def track_websocket_disconnection(connection_type: str, reason: str = 'normal'):
    """Track WebSocket disconnection"""
    websocket_disconnections_total.labels(
        connection_type=connection_type,
        reason=reason
    ).inc()
    websocket_active_connections.labels(connection_type=connection_type).dec()
    logger.debug(f"Metrics: WebSocket disconnection ({connection_type}, {reason})")


def track_websocket_message_sent(message_type: str):
    """Track WebSocket message sent"""
    websocket_messages_sent_total.labels(message_type=message_type).inc()


def track_websocket_message_received(connection_type: str):
    """Track WebSocket message received"""
    websocket_messages_received_total.labels(connection_type=connection_type).inc()


def track_signup_started(verification_tier: str):
    """Track signup flow started"""
    signup_started_total.labels(verification_tier=verification_tier).inc()
    logger.info(f"Metrics: Signup started ({verification_tier})")


def track_signup_completed(verification_tier: str, outcome: str):
    """Track signup flow completed"""
    signup_completed_total.labels(
        verification_tier=verification_tier,
        outcome=outcome
    ).inc()
    logger.info(f"Metrics: Signup completed ({verification_tier}, {outcome})")


def track_verification_code_sent(method: str):
    """Track verification code sent"""
    verification_codes_sent_total.labels(method=method).inc()


def track_verification_code_verified(success: bool):
    """Track verification code verification"""
    verification_codes_verified_total.labels(
        success='true' if success else 'false'
    ).inc()


def track_admin_review_action(action: str):
    """Track admin review action"""
    admin_review_actions_total.labels(action=action).inc()
    logger.info(f"Metrics: Admin review action ({action})")


def update_pending_reviews_count(count: int):
    """Update pending reviews gauge"""
    admin_reviews_pending.set(count)


def track_redis_operation(operation: str, success: bool, duration: float):
    """Track Redis operation"""
    redis_operations_total.labels(
        operation=operation,
        success='true' if success else 'false'
    ).inc()
    redis_operation_duration_seconds.labels(operation=operation).observe(duration)


def track_redis_connection_error():
    """Track Redis connection error"""
    redis_connection_errors_total.inc()


def track_api_request(method: str, endpoint: str, status: int, duration: float):
    """Track API request"""
    api_requests_total.labels(
        method=method,
        endpoint=endpoint,
        status=str(status)
    ).inc()
    api_request_duration_seconds.labels(
        method=method,
        endpoint=endpoint
    ).observe(duration)


def track_api_error(endpoint: str, error_type: str):
    """Track API error"""
    api_errors_total.labels(
        endpoint=endpoint,
        error_type=error_type
    ).inc()
