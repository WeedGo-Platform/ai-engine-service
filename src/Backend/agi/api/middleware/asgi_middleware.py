"""
ASGI-based middleware implementations that properly handle streaming responses
Replaces BaseHTTPMiddleware to avoid content-length issues
"""

import logging
import json
import traceback
import time
from typing import Dict, Any, Optional, Callable
from datetime import datetime, timezone
from starlette.types import ASGIApp, Receive, Scope, Send
from starlette.datastructures import Headers
from starlette.responses import Response

from agi.security import get_audit_logger
from agi.security.audit_logger import AuditEventType, AuditSeverity
from agi.security.content_filter import get_content_filter, FilterAction

logger = logging.getLogger(__name__)


class ASGIErrorHandlerMiddleware:
    """
    ASGI-based error handling middleware that properly handles streaming
    """

    def __init__(self, app: ASGIApp):
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        # Track if response has started
        response_started = False

        async def wrapped_send(message: dict) -> None:
            nonlocal response_started

            if message["type"] == "http.response.start":
                response_started = True

            await send(message)

        try:
            await self.app(scope, receive, wrapped_send)
        except Exception as e:
            if not response_started:
                # Can still send error response
                await self._send_error_response(e, scope, send)
            else:
                # Response already started, log error
                logger.error(f"Error after response started: {e}")
                raise

    async def _send_error_response(self, error: Exception, scope: Scope, send: Send) -> None:
        """Send error response"""
        status_code = getattr(error, "status_code", 500)
        error_detail = str(error) if status_code < 500 else "Internal server error"

        # Log error
        logger.error(f"Request error: {error}", exc_info=True)

        # Audit log
        try:
            audit_logger = await get_audit_logger()
            from agi.security.audit_logger import AuditEvent
            await audit_logger.log_event(
                AuditEvent(
                    event_type=AuditEventType.SYSTEM_ERROR,
                    severity=AuditSeverity.ERROR if status_code >= 500 else AuditSeverity.WARNING,
                    error_message=str(error),
                    metadata={
                        "error": str(error),
                        "path": scope.get("path", ""),
                        "method": scope.get("method", ""),
                        "status_code": status_code
                    }
                )
            )
        except:
            logger.error("Failed to log audit event", exc_info=True)

        # Send error response
        response_body = json.dumps({
            "error": error_detail,
            "status_code": status_code,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }).encode("utf-8")

        # Get CORS headers
        headers = self._get_cors_headers(scope)
        headers.extend([
            [b"content-type", b"application/json"],
            [b"content-length", str(len(response_body)).encode()]
        ])

        await send({
            "type": "http.response.start",
            "status": status_code,
            "headers": headers,
        })

        await send({
            "type": "http.response.body",
            "body": response_body,
        })

    def _get_cors_headers(self, scope: Scope) -> list:
        """Get CORS headers for error responses"""
        headers_dict = dict(scope.get("headers", []))
        origin = headers_dict.get(b"origin", b"").decode()

        # List of allowed origins (matching main_server.py CORS config)
        allowed_origins = [
            "http://localhost:3000",
            "http://localhost:3001",
            "http://localhost:3002",
            "http://localhost:3003",
            "http://localhost:3004",
            "http://localhost:3005",
            "http://localhost:3006",
            "http://localhost:3007",
            "http://localhost:5024",
            "http://localhost:5173",
            "http://localhost:5174"
        ]

        cors_headers = []
        if origin in allowed_origins:
            cors_headers = [
                [b"access-control-allow-origin", origin.encode()],
                [b"access-control-allow-credentials", b"true"],
                [b"access-control-allow-methods", b"GET, POST, PUT, DELETE, OPTIONS, PATCH"],
                [b"access-control-allow-headers", b"*"],
                [b"access-control-expose-headers", b"*"],
            ]

        return cors_headers


class ASGIValidationMiddleware:
    """
    ASGI-based validation middleware that properly handles streaming
    """

    def __init__(self, app: ASGIApp):
        self.app = app
        self.content_filter = None
        self.max_request_size = 10 * 1024 * 1024  # 10MB

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        # Initialize content filter if needed
        if not self.content_filter:
            try:
                self.content_filter = await get_content_filter()
            except:
                logger.debug("Content filter not available")

        # Check request size from headers
        headers = Headers(scope=scope)
        content_length = headers.get("content-length")

        if content_length and int(content_length) > self.max_request_size:
            await self._send_error_response(
                "Request too large",
                413,
                scope,
                send
            )
            return

        # For API endpoints that need content filtering
        if self._should_filter_content(scope["path"]):
            # Buffer request body for filtering
            body = await self._read_body(receive)

            if body and self.content_filter:
                try:
                    # Parse JSON body
                    data = json.loads(body)

                    # Check message content
                    message = data.get("message") or data.get("content") or data.get("text")
                    if message:
                        filter_result = await self.content_filter.filter_content(message)
                        if not filter_result.safe:
                            await self._send_error_response(
                                f"Content blocked: {', '.join(filter_result.warnings)}",
                                400,
                                scope,
                                send
                            )
                            return
                except json.JSONDecodeError:
                    pass  # Not JSON, skip content filtering
                except Exception as e:
                    logger.error(f"Content filtering error: {e}")

            # Create new receive that returns buffered body
            async def new_receive():
                return {
                    "type": "http.request",
                    "body": body,
                    "more_body": False,
                }

            await self.app(scope, new_receive, send)
        else:
            # Pass through for non-filtered endpoints
            await self.app(scope, receive, send)

    def _should_filter_content(self, path: str) -> bool:
        """Check if path should have content filtering"""
        filtered_paths = ["/api/agi/chat", "/api/agi/agents"]
        return any(path.startswith(p) for p in filtered_paths)

    async def _read_body(self, receive: Receive) -> bytes:
        """Read request body"""
        body = b""
        while True:
            message = await receive()
            if message["type"] == "http.request":
                body += message.get("body", b"")
                if not message.get("more_body", False):
                    break
        return body

    async def _send_error_response(self, error_msg: str, status_code: int, scope: Scope, send: Send) -> None:
        """Send error response"""
        response_body = json.dumps({
            "error": error_msg,
            "status_code": status_code,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }).encode("utf-8")

        # Get CORS headers
        headers = self._get_cors_headers(scope)
        headers.extend([
            [b"content-type", b"application/json"],
            [b"content-length", str(len(response_body)).encode()]
        ])

        await send({
            "type": "http.response.start",
            "status": status_code,
            "headers": headers,
        })

        await send({
            "type": "http.response.body",
            "body": response_body,
        })

    def _get_cors_headers(self, scope: Scope) -> list:
        """Get CORS headers for error responses"""
        headers_dict = dict(scope.get("headers", []))
        origin = headers_dict.get(b"origin", b"").decode()

        # List of allowed origins (matching main_server.py CORS config)
        allowed_origins = [
            "http://localhost:3000",
            "http://localhost:3001",
            "http://localhost:3002",
            "http://localhost:3003",
            "http://localhost:3004",
            "http://localhost:3005",
            "http://localhost:3006",
            "http://localhost:3007",
            "http://localhost:5024",
            "http://localhost:5173",
            "http://localhost:5174"
        ]

        cors_headers = []
        if origin in allowed_origins:
            cors_headers = [
                [b"access-control-allow-origin", origin.encode()],
                [b"access-control-allow-credentials", b"true"],
                [b"access-control-allow-methods", b"GET, POST, PUT, DELETE, OPTIONS, PATCH"],
                [b"access-control-allow-headers", b"*"],
                [b"access-control-expose-headers", b"*"],
            ]

        return cors_headers


class ASGILoggingMiddleware:
    """
    ASGI-based request/response logging middleware
    """

    def __init__(self, app: ASGIApp):
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        start_time = time.time()
        path = scope.get("path", "")
        method = scope.get("method", "")

        # Track response status
        status_code = 500

        async def wrapped_send(message: dict) -> None:
            nonlocal status_code

            if message["type"] == "http.response.start":
                status_code = message.get("status", 500)

            await send(message)

        try:
            await self.app(scope, receive, wrapped_send)
        finally:
            # Log request
            duration = time.time() - start_time
            logger.info(
                f"{method} {path} - {status_code} - {duration:.3f}s"
            )