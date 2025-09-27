"""
Request/Response Validation Middleware for AGI API
Provides comprehensive validation, sanitization, and security checks
"""

import re
import logging
import json
from typing import Dict, Any, List, Optional, Union
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field, validator, ValidationError
from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
import hashlib
import bleach

from agi.security import get_content_filter
from agi.security.content_filter import FilterAction

logger = logging.getLogger(__name__)


class ContentType(Enum):
    """Content types for validation"""
    TEXT = "text"
    JSON = "json"
    CODE = "code"
    URL = "url"
    EMAIL = "email"


class ValidationRule:
    """Validation rules for different content types"""

    @staticmethod
    def validate_text(text: str, max_length: int = 10000) -> str:
        """Validate and sanitize text input"""
        if not text or not text.strip():
            raise ValueError("Text cannot be empty")

        if len(text) > max_length:
            raise ValueError(f"Text exceeds maximum length of {max_length}")

        # Sanitize HTML/scripts
        cleaned = bleach.clean(text, tags=[], strip=True)

        # Remove control characters except newlines and tabs
        cleaned = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', cleaned)

        return cleaned.strip()

    @staticmethod
    def validate_json(data: Union[str, Dict]) -> Dict[str, Any]:
        """Validate JSON data"""
        if isinstance(data, str):
            try:
                parsed = json.loads(data)
            except json.JSONDecodeError as e:
                raise ValueError(f"Invalid JSON: {e}")
        else:
            parsed = data

        if not isinstance(parsed, dict):
            raise ValueError("JSON must be an object")

        return parsed

    @staticmethod
    def validate_code(code: str, language: Optional[str] = None) -> str:
        """Validate code input"""
        if not code or not code.strip():
            raise ValueError("Code cannot be empty")

        # Check for common injection patterns
        dangerous_patterns = [
            r'exec\s*\(',
            r'eval\s*\(',
            r'__import__\s*\(',
            r'subprocess\.',
            r'os\.',
            r'sys\.',
        ]

        for pattern in dangerous_patterns:
            if re.search(pattern, code, re.IGNORECASE):
                logger.warning(f"Potentially dangerous code pattern detected: {pattern}")
                # Don't block, just log for now

        return code.strip()

    @staticmethod
    def validate_url(url: str) -> str:
        """Validate URL"""
        url_pattern = re.compile(
            r'^https?://'  # http:// or https://
            r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain...
            r'localhost|'  # localhost...
            r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
            r'(?::\d+)?'  # optional port
            r'(?:/?|[/?]\S+)$', re.IGNORECASE
        )

        if not url_pattern.match(url):
            raise ValueError("Invalid URL format")

        # Check for local/private IPs
        private_ip_patterns = [
            r'^https?://localhost',
            r'^https?://127\.',
            r'^https?://10\.',
            r'^https?://172\.(1[6-9]|2[0-9]|3[01])\.',
            r'^https?://192\.168\.'
        ]

        for pattern in private_ip_patterns:
            if re.match(pattern, url, re.IGNORECASE):
                raise ValueError("URLs to private/local addresses are not allowed")

        return url

    @staticmethod
    def validate_email(email: str) -> str:
        """Validate email address"""
        email_pattern = re.compile(
            r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        )

        if not email_pattern.match(email):
            raise ValueError("Invalid email format")

        return email.lower()


class RequestValidator(BaseModel):
    """Base request validator"""

    class Config:
        str_strip_whitespace = True
        max_anystr_length = 10000

    @validator('*', pre=True)
    def empty_str_to_none(cls, v):
        """Convert empty strings to None"""
        if v == '':
            return None
        return v


class ChatRequestValidator(RequestValidator):
    """Chat request validation"""
    message: str = Field(..., min_length=1, max_length=5000)
    session_id: Optional[str] = Field(None, max_length=100)
    temperature: Optional[float] = Field(0.7, ge=0.0, le=2.0)
    max_tokens: Optional[int] = Field(2048, ge=1, le=8192)
    stream: Optional[bool] = Field(False)

    @validator('message')
    def validate_message(cls, v):
        """Validate message content"""
        return ValidationRule.validate_text(v, max_length=5000)


class ToolRequestValidator(RequestValidator):
    """Tool execution request validation"""
    tool_name: str = Field(..., min_length=1, max_length=100)
    parameters: Dict[str, Any] = Field(default_factory=dict)

    @validator('tool_name')
    def validate_tool_name(cls, v):
        """Validate tool name"""
        if not re.match(r'^[a-zA-Z0-9_]+$', v):
            raise ValueError("Tool name must contain only alphanumeric characters and underscores")
        return v


class ResponseSanitizer:
    """Sanitize and validate responses"""

    @staticmethod
    def sanitize_response(response: Any) -> Any:
        """Sanitize response data"""
        if isinstance(response, str):
            # Remove any potential sensitive data patterns
            response = ResponseSanitizer._remove_sensitive_data(response)
        elif isinstance(response, dict):
            response = ResponseSanitizer._sanitize_dict(response)
        elif isinstance(response, list):
            response = [ResponseSanitizer.sanitize_response(item) for item in response]

        return response

    @staticmethod
    def _remove_sensitive_data(text: str) -> str:
        """Remove sensitive data patterns from text"""
        # Remove potential API keys
        text = re.sub(r'[a-zA-Z0-9]{32,}', '[REDACTED]', text)

        # Remove credit card numbers
        text = re.sub(r'\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b', '[CREDIT_CARD]', text)

        # Remove SSN
        text = re.sub(r'\b\d{3}-\d{2}-\d{4}\b', '[SSN]', text)

        # Remove email addresses in certain contexts
        # (keep if it's the main content, redact if it looks like leaked data)
        if text.count('@') > 3:  # Multiple emails might be leaked data
            text = re.sub(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', '[EMAIL]', text)

        return text

    @staticmethod
    def _sanitize_dict(data: Dict[str, Any]) -> Dict[str, Any]:
        """Sanitize dictionary recursively"""
        sanitized = {}
        sensitive_keys = ['password', 'token', 'secret', 'key', 'api_key', 'auth', 'credential']

        for key, value in data.items():
            # Redact sensitive keys
            if any(sensitive in key.lower() for sensitive in sensitive_keys):
                sanitized[key] = '[REDACTED]'
            else:
                sanitized[key] = ResponseSanitizer.sanitize_response(value)

        return sanitized


class ValidationMiddleware(BaseHTTPMiddleware):
    """Request/Response validation middleware"""

    def __init__(self, app):
        super().__init__(app)
        self.content_filter = None
        self.request_validators = {
            "/api/v1/chat": ChatRequestValidator,
            "/api/v1/tools/execute": ToolRequestValidator,
        }

    async def dispatch(self, request: Request, call_next):
        """Process request with validation"""
        # Skip validation for certain paths
        skip_paths = ["/docs", "/redoc", "/openapi.json", "/health"]
        if any(request.url.path.startswith(path) for path in skip_paths):
            return await call_next(request)

        try:
            # Validate request
            if request.method in ["POST", "PUT", "PATCH"]:
                await self._validate_request(request)

            # Process request
            response = await call_next(request)

            # Validate response
            if response.status_code == 200:
                response = await self._validate_response(response)

            return response

        except ValidationError as e:
            logger.warning(f"Validation error: {e}")
            return JSONResponse(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                content={
                    "error": "Validation Error",
                    "details": e.errors()
                }
            )

        except ValueError as e:
            logger.warning(f"Value error: {e}")
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={
                    "error": "Bad Request",
                    "message": str(e)
                }
            )

    async def _validate_request(self, request: Request):
        """Validate incoming request"""
        # Check Content-Type
        content_type = request.headers.get("Content-Type", "")
        if "application/json" not in content_type:
            raise ValueError("Content-Type must be application/json")

        # Get request body
        body = await request.body()
        if not body:
            raise ValueError("Request body cannot be empty")

        # Parse JSON
        try:
            data = json.loads(body)
        except json.JSONDecodeError:
            raise ValueError("Invalid JSON in request body")

        # Store parsed body for later use
        request.state.json = data

        # Check request size
        if len(body) > 1_000_000:  # 1MB limit
            raise ValueError("Request body too large")

        # Apply specific validators based on path
        path = request.url.path
        if path in self.request_validators:
            validator_class = self.request_validators[path]
            try:
                validated = validator_class(**data)
                request.state.validated = validated
            except ValidationError as e:
                raise e

        # Content filtering
        if not self.content_filter:
            try:
                self.content_filter = await get_content_filter()
            except:
                logger.debug("Content filter not available")

        if self.content_filter and isinstance(data, dict):
            # Check message content
            message = data.get("message") or data.get("content") or data.get("text")
            if message:
                filter_result = await self.content_filter.filter_content(message)
                if not filter_result.safe:
                    raise ValueError(f"Content blocked: {', '.join(filter_result.warnings)}")

    async def _validate_response(self, response):
        """Validate and sanitize response"""
        # Read response body
        body = b""
        async for chunk in response.body_iterator:
            body += chunk

        try:
            # Parse JSON response
            data = json.loads(body)

            # Sanitize response
            sanitized = ResponseSanitizer.sanitize_response(data)

            # Create new response with sanitized data
            return JSONResponse(
                content=sanitized,
                status_code=response.status_code,
                headers=dict(response.headers)
            )

        except json.JSONDecodeError:
            # Not JSON, return as-is
            return response

        except Exception as e:
            logger.error(f"Response validation error: {e}")
            return response


class InputSanitizer:
    """Additional input sanitization utilities"""

    @staticmethod
    def sanitize_filename(filename: str) -> str:
        """Sanitize filename for safe storage"""
        # Remove path traversal attempts
        filename = filename.replace("../", "").replace("..\\", "")

        # Keep only safe characters
        filename = re.sub(r'[^a-zA-Z0-9._-]', '_', filename)

        # Limit length
        if len(filename) > 255:
            name, ext = filename.rsplit('.', 1) if '.' in filename else (filename, '')
            filename = name[:250] + '.' + ext if ext else name[:255]

        return filename

    @staticmethod
    def sanitize_sql_identifier(identifier: str) -> str:
        """Sanitize SQL identifiers (table/column names)"""
        # Only allow alphanumeric and underscore
        sanitized = re.sub(r'[^a-zA-Z0-9_]', '', identifier)

        # Cannot start with number
        if sanitized and sanitized[0].isdigit():
            sanitized = '_' + sanitized

        if not sanitized:
            raise ValueError("Invalid SQL identifier")

        return sanitized

    @staticmethod
    def validate_uuid(uuid_str: str) -> str:
        """Validate UUID format"""
        uuid_pattern = re.compile(
            r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$',
            re.IGNORECASE
        )

        if not uuid_pattern.match(uuid_str):
            raise ValueError("Invalid UUID format")

        return uuid_str.lower()