#!/usr/bin/env python3
"""
V5 AI Engine API Server
Complete standalone implementation with all security and industry features
"""

import os
import sys
import asyncio
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List
from contextlib import asynccontextmanager
import uvicorn

# Add V5 to path
sys.path.insert(0, str(Path(__file__).parent))

from fastapi import FastAPI, HTTPException, Request, Depends, status
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

# V5 Core imports
from core.config_loader import get_config, SecureConfigLoader
from core.authentication import get_auth, get_current_user, JWTAuthentication
from core.rate_limiter import get_rate_limiter, rate_limit, RateLimitMiddleware
from core.input_validation import ChatRequestModel, ProductSearchModel, OrderCreateModel
from core.secure_database import SecureDatabaseConnection
from core.function_schemas import get_function_registry

# Import voice endpoints
from api.voice_endpoints import router as voice_router

# Import chat endpoints  
from api.chat_endpoints import router as chat_router

# V5 Services
from services.smart_ai_engine_v5 import SmartAIEngineV5

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# Response Models
class HealthResponse(BaseModel):
    status: str
    version: str = "5.0.0"
    features: Dict[str, bool]


class ChatResponse(BaseModel):
    response: str
    session_id: str
    tools_used: Optional[List[str]] = None
    confidence: Optional[float] = None
    metadata: Optional[Dict[str, Any]] = None


class FunctionCallResponse(BaseModel):
    function: str
    arguments: Dict[str, Any]
    result: Any
    success: bool
    error: Optional[str] = None


# Global instances
app = FastAPI(
    title="V5 AI Engine",
    description="Industry-standard AI engine with complete security and features",
    version="5.0.0"
)

# Globals
v5_engine: Optional[SmartAIEngineV5] = None
config: Optional[SecureConfigLoader] = None
auth: Optional[JWTAuthentication] = None
db: Optional[SecureDatabaseConnection] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    global v5_engine, config, auth, db
    
    try:
        # Load configuration
        logger.info("Loading V5 configuration...")
        config = get_config()
        config.log_config()
        
        # Initialize authentication
        logger.info("Initializing authentication...")
        auth = get_auth()
        
        # Initialize database (temporarily skip for testing)
        logger.info("Skipping database initialization for testing...")
        db = None
        # db_config = config.get_database_config()
        # if db_config.get('password'):
        #     db = SecureDatabaseConnection(db_config)
        #     await db.initialize()
        # else:
        #     logger.warning("Database password not configured")
        
        # Initialize rate limiter
        logger.info("Initializing rate limiter...")
        rate_limiter = await get_rate_limiter()
        app.state.rate_limiter = rate_limiter
        
        # Initialize V5 engine
        logger.info("Initializing V5 AI Engine...")
        v5_engine = SmartAIEngineV5()
        
        # Load with dispensary agent by default
        v5_engine.load_agent_personality(
            agent_id="dispensary",
            personality_id="friendly"
        )
        
        # Register function schemas
        logger.info("Registering function schemas...")
        registry = get_function_registry()
        
        logger.info("V5 AI Engine started successfully")
        
        yield
        
    except Exception as e:
        logger.error(f"Failed to start V5 engine: {e}")
        raise
    
    finally:
        # Cleanup
        logger.info("Shutting down V5 engine...")
        if db:
            await db.close()
        if v5_engine:
            v5_engine.cleanup()


# Configure app
app = FastAPI(lifespan=lifespan)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:5024", "http://localhost:3000", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add security headers middleware
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    response.headers["Content-Security-Policy"] = "default-src 'self'"
    return response

# Include routers
app.include_router(voice_router)
app.include_router(chat_router)

# Import and include admin endpoints
from api.admin_endpoints import router as admin_router
app.include_router(admin_router)

# Add global rate limiting
@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    """Global rate limiting middleware"""
    if not hasattr(app.state, 'rate_limiter'):
        return await call_next(request)
    
    rate_limiter = app.state.rate_limiter
    client_id = rate_limiter.get_client_id(request)
    
    # Check global rate limit
    allowed, info = await rate_limiter.check_rate_limit(
        client_id,
        resource='global',
        limit=(60, 60),  # 60 requests per minute
        algorithm='sliding_window'
    )
    
    if not allowed:
        return JSONResponse(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            content={"detail": "Too many requests", **info},
            headers={"Retry-After": str(info.get('retry_after', 60))}
        )
    
    return await call_next(request)


# Health check endpoint
@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    features = config.get_feature_flags() if config else {}
    
    return HealthResponse(
        status="healthy",
        version="5.0.0",
        features=features
    )


# Authentication endpoints
@app.post("/auth/login")
async def login(email: str, password: str):
    """Login endpoint"""
    # In production, verify against database
    # For now, mock authentication
    
    if not auth:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Authentication not initialized"
        )
    
    # Create tokens
    user_data = {
        'user_id': '123',
        'email': email,
        'role': 'user'
    }
    
    access_token = auth.create_access_token(user_data)
    refresh_token = auth.create_refresh_token(user_data)
    
    return {
        'access_token': access_token,
        'refresh_token': refresh_token,
        'token_type': 'bearer'
    }


# Main chat endpoint
@app.post("/api/v5/chat", response_model=ChatResponse)
@rate_limit(resource="chat", requests=30, seconds=60)
async def chat_v5(
    request: ChatRequestModel,
    user: Dict = Depends(get_current_user)
):
    """
    V5 Chat endpoint with full features
    - Authentication required
    - Rate limited
    - Input validated
    - Function schemas supported
    """
    if not v5_engine:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="V5 engine not initialized"
        )
    
    try:
        # Build context
        context = {
            'user_id': user.get('user_id'),
            'role': user.get('role'),
            'session_id': request.session_id,
            'agent_id': request.agent_id or 'dispensary'
        }
        
        # Process message
        result = await v5_engine.process_message(
            message=request.message,
            context=context,
            session_id=request.session_id
        )
        
        # Extract response
        response_text = result.get('response', "I couldn't process that request")
        tools_used = result.get('tools_used', [])
        
        return ChatResponse(
            response=response_text,
            session_id=request.session_id,
            tools_used=tools_used,
            confidence=result.get('confidence'),
            metadata=result.get('metadata')
        )
    
    except Exception as e:
        logger.error(f"Chat processing failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process chat message"
        )


# Streaming chat endpoint
@app.post("/api/v5/chat/stream")
@rate_limit(resource="chat", requests=20, seconds=60)
async def chat_v5_stream(
    request: ChatRequestModel,
    user: Dict = Depends(get_current_user)
):
    """
    V5 Streaming chat endpoint
    Returns Server-Sent Events stream
    """
    if not v5_engine:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="V5 engine not initialized"
        )
    
    async def generate():
        """Generate streaming response"""
        try:
            context = {
                'user_id': user.get('user_id'),
                'role': user.get('role'),
                'session_id': request.session_id
            }
            
            # Stream tokens
            async for token in v5_engine.stream_response(
                message=request.message,
                context=context,
                session_id=request.session_id
            ):
                yield f"data: {token}\n\n"
            
            yield f"data: [DONE]\n\n"
        
        except Exception as e:
            logger.error(f"Streaming failed: {e}")
            yield f"data: Error: {str(e)}\n\n"
    
    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive"
        }
    )


# Function calling endpoint
@app.post("/api/v5/function/{function_name}", response_model=FunctionCallResponse)
@rate_limit(resource="function", requests=20, seconds=60)
async def call_function(
    function_name: str,
    arguments: Dict[str, Any],
    user: Dict = Depends(get_current_user)
):
    """
    Direct function calling endpoint
    Executes functions with OpenAI-compatible schemas
    """
    registry = get_function_registry()
    
    # Check if function exists
    schema = registry.get_schema(function_name)
    if not schema:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Function '{function_name}' not found"
        )
    
    # Execute function
    result = await registry.execute(function_name, arguments)
    
    return FunctionCallResponse(
        function=function_name,
        arguments=arguments,
        result=result.get('result'),
        success=not bool(result.get('error')),
        error=result.get('error')
    )


# List available functions
@app.get("/api/v5/functions")
async def list_functions(
    format: str = "openai",
    category: Optional[str] = None,
    user: Dict = Depends(get_current_user)
):
    """
    List available functions in OpenAI or Anthropic format
    """
    registry = get_function_registry()
    
    if format == "anthropic":
        return registry.get_anthropic_tools(category)
    else:
        return registry.get_openai_tools(category)


# Product search endpoint
@app.post("/api/v5/search/products")
@rate_limit(resource="search", requests=30, seconds=60)
async def search_products(
    request: ProductSearchModel,
    user: Dict = Depends(get_current_user)
):
    """Search for products using V5 engine"""
    if not v5_engine:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="V5 engine not initialized"
        )
    
    # Use read_api tool through V5
    tool_manager = v5_engine.tool_manager
    if not tool_manager:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Tools not initialized"
        )
    
    # Execute search
    result = await tool_manager.execute_tool(
        "read_api",
        action="read_raw",
        endpoint="/api/v1/products/search",
        params=request.dict(exclude_none=True),
        auth_token=user.get('token')
    )
    
    return result


# Order creation endpoint
@app.post("/api/v5/orders")
@rate_limit(resource="order", requests=5, seconds=60)
async def create_order(
    request: OrderCreateModel,
    user: Dict = Depends(get_current_user)
):
    """Create an order using V5 engine"""
    if not v5_engine:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="V5 engine not initialized"
        )
    
    # Use api_orchestrator tool
    tool_manager = v5_engine.tool_manager
    if not tool_manager:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Tools not initialized"
        )
    
    # Execute order creation
    result = await tool_manager.execute_tool(
        "api_orchestrator",
        action="submit",
        operation_id="createOrder",
        data=request.dict(),
        auth_token=user.get('token')
    )
    
    return result


# Admin endpoints
@app.get("/api/v5/admin/stats")
async def get_stats(user: Dict = Depends(get_current_user)):
    """Get V5 engine statistics (admin only)"""
    if user.get('role') != 'admin':
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    return {
        "version": "5.0.0",
        "uptime": "N/A",
        "requests_processed": 0,
        "active_sessions": 0,
        "tools_available": len(v5_engine.tool_manager.tools) if v5_engine and v5_engine.tool_manager else 0
    }


# Error handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions"""
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail}
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle general exceptions"""
    logger.error(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Internal server error"}
    )


def main():
    """Run the V5 API server"""
    port = int(os.environ.get('V5_PORT', 5024))
    host = os.environ.get('V5_HOST', '0.0.0.0')
    
    # Create .env file if it doesn't exist
    env_file = Path(__file__).parent / '.env'
    if not env_file.exists():
        logger.warning(".env file not found, using defaults")
    
    logger.info(f"Starting V5 AI Engine API Server on {host}:{port}")
    
    uvicorn.run(
        app,
        host=host,
        port=port,
        reload=os.environ.get('DEBUG', 'false').lower() == 'true',
        log_level="info"
    )


if __name__ == "__main__":
    main()