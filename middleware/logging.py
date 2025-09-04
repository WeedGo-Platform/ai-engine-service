"""
Logging Middleware - Request/response logging
Implements structured logging with correlation IDs
"""

import time
import uuid
import logging
from typing import Callable

from fastapi import Request, Response

logger = logging.getLogger(__name__)

async def logging_middleware(request: Request, call_next: Callable) -> Response:
    """
    Middleware for logging all requests and responses
    Adds correlation ID for request tracking
    """
    
    # Generate request ID
    request_id = str(uuid.uuid4())
    request.state.request_id = request_id
    
    # Start timer
    start_time = time.time()
    
    # Log request
    logger.info(
        f"Request started",
        extra={
            "request_id": request_id,
            "method": request.method,
            "path": request.url.path,
            "query": str(request.url.query) if request.url.query else None,
            "client": request.client.host if request.client else None
        }
    )
    
    # Process request
    response = await call_next(request)
    
    # Calculate duration
    duration = time.time() - start_time
    
    # Add headers
    response.headers["X-Request-ID"] = request_id
    response.headers["X-Response-Time"] = str(duration)
    
    # Log response
    logger.info(
        f"Request completed",
        extra={
            "request_id": request_id,
            "method": request.method,
            "path": request.url.path,
            "status_code": response.status_code,
            "duration": round(duration, 3)
        }
    )
    
    return response