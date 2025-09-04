"""
Error Handler Middleware - Centralized error handling
Implements Chain of Responsibility pattern
"""

import logging
import traceback
from typing import Callable
from datetime import datetime

from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)

class ErrorHandlerMiddleware(BaseHTTPMiddleware):
    """
    Middleware for handling all application errors
    Provides consistent error responses
    """
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request and handle errors"""
        try:
            response = await call_next(request)
            return response
            
        except ValueError as e:
            # Validation errors
            logger.warning(f"Validation error: {str(e)}")
            return JSONResponse(
                status_code=400,
                content={
                    "error": "Validation Error",
                    "message": str(e),
                    "timestamp": datetime.now().isoformat()
                }
            )
            
        except PermissionError as e:
            # Authorization errors
            logger.warning(f"Permission error: {str(e)}")
            return JSONResponse(
                status_code=403,
                content={
                    "error": "Permission Denied",
                    "message": str(e),
                    "timestamp": datetime.now().isoformat()
                }
            )
            
        except FileNotFoundError as e:
            # Resource not found
            logger.warning(f"Resource not found: {str(e)}")
            return JSONResponse(
                status_code=404,
                content={
                    "error": "Not Found",
                    "message": str(e),
                    "timestamp": datetime.now().isoformat()
                }
            )
            
        except TimeoutError as e:
            # Timeout errors
            logger.error(f"Timeout error: {str(e)}")
            return JSONResponse(
                status_code=504,
                content={
                    "error": "Gateway Timeout",
                    "message": "Request processing timed out",
                    "timestamp": datetime.now().isoformat()
                }
            )
            
        except Exception as e:
            # Unexpected errors
            logger.error(
                f"Unexpected error: {str(e)}\n"
                f"Traceback: {traceback.format_exc()}"
            )
            
            # Don't expose internal errors in production
            message = str(e) if logger.level == logging.DEBUG else "Internal server error"
            
            return JSONResponse(
                status_code=500,
                content={
                    "error": "Internal Server Error",
                    "message": message,
                    "timestamp": datetime.now().isoformat()
                }
            )

async def error_handler_middleware(request: Request, call_next: Callable) -> Response:
    """Function-based middleware for error handling"""
    try:
        response = await call_next(request)
        
        # Log successful responses
        if response.status_code < 400:
            logger.debug(
                f"{request.method} {request.url.path} - {response.status_code}"
            )
        else:
            logger.warning(
                f"{request.method} {request.url.path} - {response.status_code}"
            )
        
        return response
        
    except Exception as e:
        # Log the error with full context
        logger.error(
            f"Error processing {request.method} {request.url.path}: {str(e)}",
            exc_info=True,
            extra={
                "method": request.method,
                "path": request.url.path,
                "query": str(request.url.query),
                "headers": dict(request.headers)
            }
        )
        
        # Return generic error response
        return JSONResponse(
            status_code=500,
            content={
                "error": "Internal Server Error",
                "message": "An unexpected error occurred",
                "request_id": request.headers.get("X-Request-ID", "unknown"),
                "timestamp": datetime.now().isoformat()
            }
        )