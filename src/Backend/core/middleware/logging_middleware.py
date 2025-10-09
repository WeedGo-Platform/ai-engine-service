"""
Enhanced Logging Middleware with Correlation IDs and Performance Metrics
"""

import time
import uuid
import logging
from typing import Callable
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
import contextvars
from datetime import datetime
from elasticsearch import Elasticsearch

# Context variable to store correlation ID for the current request
correlation_id_ctx = contextvars.ContextVar('correlation_id', default=None)

logger = logging.getLogger(__name__)


class ElasticsearchHandler(logging.Handler):
    """
    Custom Elasticsearch logging handler compatible with Elasticsearch 9.x
    """
    def __init__(self, es_hosts, es_index_name, es_additional_fields=None):
        super().__init__()
        self.es_client = Elasticsearch(es_hosts)
        self.es_index_name = es_index_name
        self.es_additional_fields = es_additional_fields or {}

    def emit(self, record):
        """
        Send log record to Elasticsearch
        """
        # Prevent infinite recursion by ignoring elasticsearch and urllib3 logs
        if record.name.startswith('elastic') or record.name.startswith('urllib3'):
            return

        try:
            # Build the document to index
            log_document = {
                '@timestamp': datetime.utcnow().isoformat(),
                'level': record.levelname,
                'logger': record.name,
                'message': record.getMessage(),
                'correlation_id': getattr(record, 'correlation_id', 'no-correlation-id'),
                'module': record.module,
                'function': record.funcName,
                'line': record.lineno,
                'thread': record.thread,
                'thread_name': record.threadName,
            }

            # Add additional fields from record extra
            for key, value in record.__dict__.items():
                if key not in ['name', 'msg', 'args', 'created', 'filename', 'funcName',
                              'levelname', 'lineno', 'module', 'msecs', 'message',
                              'pathname', 'process', 'processName', 'relativeCreated',
                              'thread', 'threadName', 'exc_info', 'exc_text', 'stack_info',
                              'correlation_id']:
                    log_document[key] = value

            # Add configured additional fields
            log_document.update(self.es_additional_fields)

            # Add exception info if present
            if record.exc_info:
                log_document['exception'] = self.format(record)

            # Index the document
            self.es_client.index(
                index=f"{self.es_index_name}-{datetime.utcnow().strftime('%Y.%m.%d')}",
                document=log_document
            )
        except Exception as e:
            # Don't let logging errors crash the application
            print(f"Failed to send log to Elasticsearch: {e}")


class CorrelationIdFilter(logging.Filter):
    """
    Logging filter that adds correlation ID to all log records
    """
    def filter(self, record):
        record.correlation_id = correlation_id_ctx.get() or 'no-correlation-id'
        return True


class PerformanceLoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware that adds correlation IDs and logs performance metrics for each request
    """

    def __init__(self, app, log_body: bool = False, slow_request_threshold: float = 1.0):
        super().__init__(app)
        self.log_body = log_body
        self.slow_request_threshold = slow_request_threshold

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Generate or extract correlation ID
        correlation_id = request.headers.get('X-Correlation-ID') or str(uuid.uuid4())
        correlation_id_ctx.set(correlation_id)

        # Extract session ID if available
        session_id = request.headers.get('X-Session-ID', 'no-session')
        user_id = request.headers.get('X-User-ID', 'anonymous')

        # Start performance timer
        start_time = time.time()

        # Log incoming request
        logger.info(
            f"Request started",
            extra={
                'correlation_id': correlation_id,
                'session_id': session_id,
                'user_id': user_id,
                'method': request.method,
                'path': request.url.path,
                'query_params': str(request.query_params),
                'client_host': request.client.host if request.client else 'unknown',
                'user_agent': request.headers.get('user-agent', 'unknown'),
            }
        )

        # Log request body for debugging (optional, be careful with sensitive data)
        if self.log_body and request.method in ['POST', 'PUT', 'PATCH']:
            try:
                # Note: This consumes the body, so we need to be careful
                # In production, you might want to skip this or only log for specific endpoints
                pass
            except Exception as e:
                logger.warning(f"Failed to log request body: {e}")

        # Process request
        try:
            response = await call_next(request)

            # Calculate request duration
            duration_ms = (time.time() - start_time) * 1000

            # Determine log level based on response status and duration
            log_level = logging.INFO
            if response.status_code >= 500:
                log_level = logging.ERROR
            elif response.status_code >= 400:
                log_level = logging.WARNING
            elif duration_ms > self.slow_request_threshold * 1000:
                log_level = logging.WARNING

            # Log response with performance metrics
            logger.log(
                log_level,
                f"Request completed",
                extra={
                    'correlation_id': correlation_id,
                    'session_id': session_id,
                    'user_id': user_id,
                    'method': request.method,
                    'path': request.url.path,
                    'status_code': response.status_code,
                    'duration_ms': round(duration_ms, 2),
                    'slow_request': duration_ms > self.slow_request_threshold * 1000,
                }
            )

            # Add correlation ID to response headers
            response.headers['X-Correlation-ID'] = correlation_id

            return response

        except Exception as e:
            # Calculate duration even for errors
            duration_ms = (time.time() - start_time) * 1000

            # Log error with full context
            logger.error(
                f"Request failed with exception: {str(e)}",
                extra={
                    'correlation_id': correlation_id,
                    'session_id': session_id,
                    'user_id': user_id,
                    'method': request.method,
                    'path': request.url.path,
                    'duration_ms': round(duration_ms, 2),
                    'exception_type': type(e).__name__,
                },
                exc_info=True
            )

            # Re-raise the exception to be handled by error handlers
            raise


class MetricsLogger:
    """
    Utility class for logging performance metrics in business logic
    """

    @staticmethod
    def log_operation(operation: str, duration_ms: float, success: bool = True, **kwargs):
        """
        Log a business operation with performance metrics

        Args:
            operation: Name of the operation (e.g., "database_query", "ai_generation")
            duration_ms: Duration in milliseconds
            success: Whether the operation succeeded
            **kwargs: Additional context to include in logs
        """
        correlation_id = correlation_id_ctx.get()

        log_data = {
            'correlation_id': correlation_id,
            'operation': operation,
            'duration_ms': round(duration_ms, 2),
            'success': success,
            **kwargs
        }

        if success:
            logger.info(f"Operation '{operation}' completed", extra=log_data)
        else:
            logger.warning(f"Operation '{operation}' failed", extra=log_data)

    @staticmethod
    def log_ai_metrics(model: str, tokens: int, tokens_per_sec: float, duration_ms: float, **kwargs):
        """
        Log AI-specific metrics

        Args:
            model: Model name
            tokens: Number of tokens generated
            tokens_per_sec: Generation speed
            duration_ms: Total duration
            **kwargs: Additional context
        """
        correlation_id = correlation_id_ctx.get()

        logger.info(
            f"AI generation completed",
            extra={
                'correlation_id': correlation_id,
                'operation': 'ai_generation',
                'model': model,
                'tokens': tokens,
                'tokens_per_sec': round(tokens_per_sec, 2),
                'duration_ms': round(duration_ms, 2),
                **kwargs
            }
        )

    @staticmethod
    def log_database_query(query_type: str, duration_ms: float, rows_affected: int = None, **kwargs):
        """
        Log database query metrics

        Args:
            query_type: Type of query (SELECT, INSERT, UPDATE, etc.)
            duration_ms: Query duration
            rows_affected: Number of rows affected
            **kwargs: Additional context
        """
        correlation_id = correlation_id_ctx.get()

        log_data = {
            'correlation_id': correlation_id,
            'operation': 'database_query',
            'query_type': query_type,
            'duration_ms': round(duration_ms, 2),
        }

        if rows_affected is not None:
            log_data['rows_affected'] = rows_affected

        log_data.update(kwargs)

        logger.info(f"Database query completed", extra=log_data)


def get_correlation_id() -> str:
    """
    Get the current correlation ID from context

    Returns:
        Current correlation ID or 'no-correlation-id' if not set
    """
    return correlation_id_ctx.get() or 'no-correlation-id'


def setup_logging_with_correlation_id():
    """
    Setup logging configuration with correlation ID filter and Elasticsearch handler
    """
    # Add correlation ID filter to all handlers
    correlation_filter = CorrelationIdFilter()

    # Update logging format to include correlation_id
    log_format = '%(asctime)s - [%(correlation_id)s] - %(name)s - %(levelname)s - %(message)s'

    # Configure root logger
    logging.basicConfig(
        level=logging.INFO,
        format=log_format,
        force=True  # Override existing configuration
    )

    # Add filter to root logger handlers
    root_logger = logging.getLogger()
    for handler in root_logger.handlers:
        handler.addFilter(correlation_filter)
        handler.setFormatter(logging.Formatter(log_format))

    # Elasticsearch handler disabled - uncomment to enable
    # import os
    # if os.getenv('ENABLE_ELASTICSEARCH_LOGGING', 'false').lower() == 'true':
    #     try:
    #         test_es = Elasticsearch(['http://localhost:9200'], request_timeout=2)
    #         if test_es.ping():
    #             es_handler = ElasticsearchHandler(
    #                 es_hosts=['http://localhost:9200'],
    #                 es_index_name="ai-engine-logs",
    #                 es_additional_fields={
    #                     'service': 'ai-engine',
    #                     'environment': 'development'
    #                 }
    #             )
    #             es_handler.addFilter(correlation_filter)
    #             root_logger.addHandler(es_handler)
    #             logger.info("Elasticsearch logging handler configured successfully")
    #         else:
    #             logger.info("Elasticsearch is not available - skipping ES logging handler")
    #     except Exception as e:
    #         logger.info(f"Elasticsearch is not available - skipping ES logging handler: {e}")
    # else:
    #     logger.info("Elasticsearch logging disabled")
    logger.info("Elasticsearch logging disabled")

    logger.info("Logging configured with correlation ID support")
