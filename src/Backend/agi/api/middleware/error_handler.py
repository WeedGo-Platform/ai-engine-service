"""
Error Handling Middleware for AGI API
Provides comprehensive error handling, recovery, and circuit breaker patterns
"""

import logging
import traceback
import asyncio
from typing import Dict, Any, Optional, Callable
from datetime import datetime, timedelta
from enum import Enum
from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from dataclasses import dataclass, field
import json

from agi.core.database import get_db_manager
from agi.security import get_audit_logger
from agi.security.audit_logger import AuditEventType, AuditSeverity

logger = logging.getLogger(__name__)


class ErrorType(Enum):
    """Types of errors for categorization"""
    VALIDATION = "validation_error"
    AUTHENTICATION = "authentication_error"
    AUTHORIZATION = "authorization_error"
    RATE_LIMIT = "rate_limit_error"
    DATABASE = "database_error"
    MODEL = "model_error"
    TOOL = "tool_error"
    NETWORK = "network_error"
    TIMEOUT = "timeout_error"
    INTERNAL = "internal_error"
    UNKNOWN = "unknown_error"


class ServiceStatus(Enum):
    """Service health status"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    CIRCUIT_OPEN = "circuit_open"


@dataclass
class ErrorContext:
    """Context for error handling"""
    request_id: str
    path: str
    method: str
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    error_type: ErrorType = ErrorType.UNKNOWN
    error_message: str = ""
    stack_trace: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.utcnow)
    recovery_attempted: bool = False
    recovery_successful: bool = False


class CircuitBreaker:
    """Circuit breaker pattern for fault tolerance"""

    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: int = 60,
        expected_exception: type = Exception
    ):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception
        self.failure_count = 0
        self.last_failure_time = None
        self.state = ServiceStatus.HEALTHY

    def call(self, func: Callable, *args, **kwargs):
        """Execute function with circuit breaker protection"""
        if self.state == ServiceStatus.CIRCUIT_OPEN:
            if self._should_attempt_reset():
                self.state = ServiceStatus.DEGRADED
            else:
                raise Exception("Circuit breaker is open")

        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
        except self.expected_exception as e:
            self._on_failure()
            raise e

    async def async_call(self, func: Callable, *args, **kwargs):
        """Execute async function with circuit breaker protection"""
        if self.state == ServiceStatus.CIRCUIT_OPEN:
            if self._should_attempt_reset():
                self.state = ServiceStatus.DEGRADED
            else:
                raise Exception("Circuit breaker is open")

        try:
            result = await func(*args, **kwargs)
            self._on_success()
            return result
        except self.expected_exception as e:
            self._on_failure()
            raise e

    def _on_success(self):
        """Reset failure count on successful call"""
        self.failure_count = 0
        self.state = ServiceStatus.HEALTHY

    def _on_failure(self):
        """Increment failure count and open circuit if threshold reached"""
        self.failure_count += 1
        self.last_failure_time = datetime.utcnow()

        if self.failure_count >= self.failure_threshold:
            self.state = ServiceStatus.CIRCUIT_OPEN
            logger.warning(f"Circuit breaker opened after {self.failure_count} failures")

    def _should_attempt_reset(self) -> bool:
        """Check if circuit should attempt reset"""
        if self.last_failure_time:
            time_since_failure = (datetime.utcnow() - self.last_failure_time).seconds
            return time_since_failure >= self.recovery_timeout
        return False


class ErrorRecoveryStrategy:
    """Strategies for error recovery"""

    @staticmethod
    async def retry_with_backoff(
        func: Callable,
        max_retries: int = 3,
        initial_delay: float = 1.0,
        backoff_factor: float = 2.0
    ):
        """Retry function with exponential backoff"""
        delay = initial_delay

        for attempt in range(max_retries):
            try:
                return await func()
            except Exception as e:
                if attempt == max_retries - 1:
                    raise e

                logger.info(f"Retry attempt {attempt + 1} after {delay}s delay")
                await asyncio.sleep(delay)
                delay *= backoff_factor

    @staticmethod
    async def fallback_response(error: Exception, context: ErrorContext) -> Dict[str, Any]:
        """Generate fallback response for errors"""
        return {
            "error": True,
            "message": "Service temporarily unavailable. Please try again later.",
            "request_id": context.request_id,
            "timestamp": context.timestamp.isoformat(),
            "fallback": True
        }

    @staticmethod
    async def cache_fallback(key: str) -> Optional[Any]:
        """Try to return cached response as fallback"""
        try:
            db_manager = await get_db_manager()
            cached = await db_manager.fetchone(
                "SELECT response FROM agi.response_cache WHERE key = $1 AND expires_at > NOW()",
                key
            )
            if cached:
                return json.loads(cached['response'])
        except Exception as e:
            logger.debug(f"Cache fallback failed: {e}")
        return None


class ErrorHandlerMiddleware(BaseHTTPMiddleware):
    """Main error handling middleware"""

    def __init__(self, app, circuit_breakers: Optional[Dict[str, CircuitBreaker]] = None):
        super().__init__(app)
        self.circuit_breakers = circuit_breakers or {}
        self.recovery_strategy = ErrorRecoveryStrategy()

    async def dispatch(self, request: Request, call_next):
        """Process request with error handling"""
        request_id = request.headers.get("X-Request-ID", str(datetime.utcnow().timestamp()))
        context = ErrorContext(
            request_id=request_id,
            path=str(request.url.path),
            method=request.method
        )

        try:
            # Add request ID to request state
            request.state.request_id = request_id

            # Process request
            response = await call_next(request)

            # Log successful request
            if response.status_code < 400:
                logger.debug(f"Request {request_id} completed successfully")

            return response

        except HTTPException as e:
            # Handle HTTP exceptions
            context.error_type = self._classify_http_error(e.status_code)
            context.error_message = e.detail
            return await self._handle_error(e, context, e.status_code)

        except asyncio.TimeoutError:
            # Handle timeout errors
            context.error_type = ErrorType.TIMEOUT
            context.error_message = "Request timeout"
            error = HTTPException(
                status_code=status.HTTP_504_GATEWAY_TIMEOUT,
                detail="Request processing timeout"
            )
            return await self._handle_error(error, context, status.HTTP_504_GATEWAY_TIMEOUT)

        except Exception as e:
            # Handle unexpected errors
            context.error_type = self._classify_error(e)
            context.error_message = str(e)
            context.stack_trace = traceback.format_exc()

            # Log error
            logger.error(f"Unhandled error in request {request_id}: {e}")
            logger.debug(context.stack_trace)

            # Attempt recovery
            if context.error_type in [ErrorType.DATABASE, ErrorType.NETWORK]:
                try:
                    context.recovery_attempted = True
                    # Try cache fallback
                    cache_key = f"{context.path}:{context.method}"
                    cached_response = await self.recovery_strategy.cache_fallback(cache_key)
                    if cached_response:
                        context.recovery_successful = True
                        return JSONResponse(
                            status_code=status.HTTP_206_PARTIAL_CONTENT,
                            content=cached_response
                        )
                except Exception as recovery_error:
                    logger.error(f"Recovery failed: {recovery_error}")

            # Return error response
            return await self._handle_error(
                Exception(str(e)),
                context,
                status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    async def _handle_error(
        self,
        error: Exception,
        context: ErrorContext,
        status_code: int
    ) -> JSONResponse:
        """Handle error and return appropriate response"""
        # Log to audit log
        try:
            audit_logger = await get_audit_logger()
            await audit_logger.log_event(
                event_type=AuditEventType.ACCESS_DENIED if status_code == 403 else AuditEventType.ACCESS_GRANTED,
                user_id=context.user_id,
                severity=AuditSeverity.ERROR if status_code >= 500 else AuditSeverity.WARNING,
                details={
                    "request_id": context.request_id,
                    "path": context.path,
                    "method": context.method,
                    "error_type": context.error_type.value,
                    "error_message": context.error_message,
                    "recovery_attempted": context.recovery_attempted,
                    "recovery_successful": context.recovery_successful
                }
            )
        except Exception as log_error:
            logger.error(f"Failed to log error to audit: {log_error}")

        # Prepare error response
        error_response = {
            "error": True,
            "message": self._get_user_friendly_message(context.error_type),
            "detail": context.error_message if status_code < 500 else "Internal server error",
            "request_id": context.request_id,
            "timestamp": context.timestamp.isoformat(),
            "type": context.error_type.value
        }

        # Add debug info in development
        if logger.level == logging.DEBUG and context.stack_trace:
            error_response["debug"] = {
                "stack_trace": context.stack_trace,
                "path": context.path,
                "method": context.method
            }

        return JSONResponse(
            status_code=status_code,
            content=error_response
        )

    def _classify_error(self, error: Exception) -> ErrorType:
        """Classify error type from exception"""
        error_str = str(error).lower()

        if "database" in error_str or "connection" in error_str:
            return ErrorType.DATABASE
        elif "model" in error_str or "llama" in error_str:
            return ErrorType.MODEL
        elif "tool" in error_str:
            return ErrorType.TOOL
        elif "network" in error_str or "timeout" in error_str:
            return ErrorType.NETWORK
        elif "validation" in error_str:
            return ErrorType.VALIDATION
        else:
            return ErrorType.UNKNOWN

    def _classify_http_error(self, status_code: int) -> ErrorType:
        """Classify error type from HTTP status code"""
        if status_code == 401:
            return ErrorType.AUTHENTICATION
        elif status_code == 403:
            return ErrorType.AUTHORIZATION
        elif status_code == 429:
            return ErrorType.RATE_LIMIT
        elif status_code in [400, 422]:
            return ErrorType.VALIDATION
        elif status_code >= 500:
            return ErrorType.INTERNAL
        else:
            return ErrorType.UNKNOWN

    def _get_user_friendly_message(self, error_type: ErrorType) -> str:
        """Get user-friendly error message"""
        messages = {
            ErrorType.VALIDATION: "Invalid request. Please check your input.",
            ErrorType.AUTHENTICATION: "Authentication required. Please log in.",
            ErrorType.AUTHORIZATION: "You don't have permission to access this resource.",
            ErrorType.RATE_LIMIT: "Too many requests. Please slow down.",
            ErrorType.DATABASE: "Database temporarily unavailable. Please try again.",
            ErrorType.MODEL: "AI model temporarily unavailable. Please try again.",
            ErrorType.TOOL: "Tool execution failed. Please try again.",
            ErrorType.NETWORK: "Network error. Please check your connection.",
            ErrorType.TIMEOUT: "Request took too long. Please try again.",
            ErrorType.INTERNAL: "Internal server error. Our team has been notified.",
            ErrorType.UNKNOWN: "An unexpected error occurred. Please try again."
        }
        return messages.get(error_type, messages[ErrorType.UNKNOWN])


# Global circuit breakers for critical services
circuit_breakers = {
    "database": CircuitBreaker(failure_threshold=3, recovery_timeout=30),
    "model": CircuitBreaker(failure_threshold=5, recovery_timeout=60),
    "external_api": CircuitBreaker(failure_threshold=10, recovery_timeout=120)
}


def get_circuit_breaker(service: str) -> Optional[CircuitBreaker]:
    """Get circuit breaker for a service"""
    return circuit_breakers.get(service)