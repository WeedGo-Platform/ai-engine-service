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

from fastapi import FastAPI, HTTPException, Request, Depends, status, WebSocket
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
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

# Import authentication endpoints
from api.simple_auth_endpoints import router as auth_router
from api.otp_auth_endpoints import router as otp_router

# V5 Services
from services.smart_ai_engine_v5 import SmartAIEngineV5
from services.context.simple_hybrid_manager import SimpleHybridContextManager

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
    version="5.0.0",
    # Disable external CDN for Swagger UI
    swagger_ui_parameters={
        "syntaxHighlight": False,
        "tryItOutEnabled": True,
        "docExpansion": "none",
    },
    # Use local assets only
    docs_url="/docs",
    redoc_url="/redoc"
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
        
        # Store engine in app state for access from endpoints
        app.state.v5_engine = v5_engine
        
        # Initialize context manager
        logger.info("Initializing Context Manager...")
        db_config = {
            'host': os.getenv('DB_HOST', 'localhost'),
            'port': int(os.getenv('DB_PORT', 5434)),
            'database': os.getenv('DB_NAME', 'ai_engine'),
            'user': os.getenv('DB_USER', 'weedgo'),
            'password': os.getenv('DB_PASSWORD', 'your_password_here')
        }
        context_manager = SimpleHybridContextManager(db_config=db_config)
        await context_manager.initialize()
        app.state.context_manager = context_manager
        
        # Auto-load smallest model with dispensary agent and zac personality on startup
        logger.info("Auto-loading default model configuration...")
        
        # Find the smallest model
        smallest_model = None
        smallest_size = float('inf')
        for model_name, model_path in v5_engine.available_models.items():
            try:
                size_bytes = os.path.getsize(model_path)
                if size_bytes > 0 and size_bytes < smallest_size:
                    smallest_size = size_bytes
                    smallest_model = model_name
            except:
                continue
        
        if smallest_model:
            logger.info(f"Loading smallest model: {smallest_model} ({smallest_size / (1024**3):.2f} GB)")
            # Load model with dispensary agent and zac personality
            success = v5_engine.load_model(
                model_name=smallest_model,
                agent_id="dispensary",
                personality_id="zac"
            )
            if success:
                logger.info(f"✅ Successfully loaded {smallest_model} with dispensary/zac configuration")
            else:
                logger.warning(f"Failed to load default model configuration")
        else:
            logger.warning("No models available to auto-load")
        
        logger.info(f"V5 Engine ready with {len(v5_engine.available_models)} models available")
        
        # Register function schemas
        logger.info("Registering function schemas...")
        registry = get_function_registry()
        
        # Load and register actual tool implementations
        logger.info("Loading tool implementations...")
        try:
            from services.tools.product_search_tool import ProductSearchTool
            
            # Create tool instances
            product_search_tool = ProductSearchTool()
            
            # Register tools with the v5 engine's tool manager if available
            if hasattr(v5_engine, 'tool_manager') and v5_engine.tool_manager:
                # Register product search wrapper
                v5_engine.tool_manager.register_tool(
                    "search_products",
                    lambda **kwargs: product_search_tool.search_products(**kwargs),
                    {
                        "description": "Search for cannabis products",
                        "category": "search",
                        "function_schema": registry.get_schema("search_products")
                    }
                )
                
                # Get product count for verification
                product_count = product_search_tool.get_product_count()
                logger.info(f"ProductSearchTool loaded - Database has {product_count} products")
                
                # Register trending products tool
                v5_engine.tool_manager.register_tool(
                    "get_trending_products", 
                    lambda **kwargs: product_search_tool.get_trending_products(**kwargs),
                    {
                        "description": "Get trending cannabis products",
                        "category": "search"
                    }
                )
                
                logger.info(f"Registered {len(v5_engine.tool_manager.list_tools())} tools with ToolManager")
            else:
                logger.warning("ToolManager not available in v5_engine")
                
        except Exception as e:
            logger.error(f"Failed to load tool implementations: {e}")
        
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
        
        # Close context manager
        if hasattr(app.state, 'context_manager'):
            logger.info("Closing context manager...")
            await app.state.context_manager.close()
        if v5_engine:
            v5_engine.cleanup()


# Configure app with same settings
app = FastAPI(
    lifespan=lifespan,
    title="V5 AI Engine",
    description="Industry-standard AI engine with complete security and features",
    version="5.0.0",
    # Disable external CDN for Swagger UI
    swagger_ui_parameters={
        "syntaxHighlight": False,
        "tryItOutEnabled": True,
        "docExpansion": "none",
    },
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:5024", "http://localhost:3000", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add security headers middleware with relaxed CSP for Swagger UI
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    
    # Skip CSP for docs and redoc endpoints
    if request.url.path in ["/docs", "/redoc", "/openapi.json"]:
        # Allow Swagger UI to work properly
        response.headers["Content-Security-Policy"] = (
            "default-src 'self' 'unsafe-inline' 'unsafe-eval' data: blob:; "
            "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
            "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://cdn.jsdelivr.net; "
            "img-src 'self' data: blob: https://fastapi.tiangolo.com; "
            "font-src 'self' data:; "
            "connect-src 'self'"
        )
    else:
        # Strict CSP for other endpoints
        response.headers["Content-Security-Policy"] = "default-src 'self'"
    
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    return response

# Include routers
app.include_router(auth_router)  # Authentication endpoints
app.include_router(otp_router)   # OTP authentication endpoints
app.include_router(voice_router)
app.include_router(chat_router)

# Import and include admin endpoints (unified admin + model management)
from api.admin_endpoints import router as admin_router
app.include_router(admin_router)

# Import and include inventory endpoints
from api.inventory_endpoints import router as inventory_router
app.include_router(inventory_router)

# Import and include cart endpoints
from api.cart_endpoints import router as cart_router
app.include_router(cart_router)

# Import and include order endpoints
from api.order_endpoints import router as order_router
app.include_router(order_router)

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
@app.post("/api/chat", response_model=ChatResponse)
@rate_limit(resource="chat", requests=30, seconds=60)
async def chat_v5(
    request: ChatRequestModel,
    req: Request
):
    """
    V5 Chat endpoint with full features
    - Authentication required
    - Rate limited
    - Input validated
    - Function schemas supported
    """
    try:
        # Get v5_engine and context_manager from app state
        v5_engine = getattr(req.app.state, 'v5_engine', None)
        if not v5_engine:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="V5 engine not initialized"
            )
        
        context_manager = getattr(req.app.state, 'context_manager', None)
        if not context_manager:
            logger.warning("Context manager not initialized, proceeding without context persistence")
        
        # Build context and get conversation history if available
        context = {
            'user_id': 'test-user',
            'role': 'user',
            'session_id': request.session_id,
            'agent_id': request.agent_id or 'dispensary'
        }
        
        # Get conversation context if context manager is available
        conversation_context = None
        if context_manager and request.session_id:
            try:
                # Get context and format history for prompt
                conversation_context = await context_manager.get_context(
                    request.session_id, 
                    customer_id=context.get('user_id')
                )
                
                # Get formatted history to include in prompt
                formatted_history = await context_manager.get_formatted_history(
                    request.session_id,
                    limit=10,
                    format_style='simple'
                )
                
                if formatted_history:
                    # Prepend history to the message for context
                    context['conversation_history'] = formatted_history
                    
            except Exception as e:
                logger.error(f"Failed to get conversation context: {e}")
                # Continue without context on error
        
        # Process message
        try:
            # Make sure the v5_engine has a model loaded
            if not v5_engine.current_model:
                # Try to load the default model if none is loaded
                logger.warning("No model loaded in v5_engine, attempting to load default")
                v5_engine.load_model("tinyllama_1.1b_chat_v1.0.q4_k_m")
            
            # Use the new intent detector for intelligent intent detection
            intent_result = v5_engine.detect_intent(request.message)
            
            # Ensure intent_result is a dictionary
            if not isinstance(intent_result, dict):
                logger.warning(f"Intent detector returned non-dict: {type(intent_result)}")
                intent_result = {"intent": "general", "confidence": 0.3, "method": "fallback"}
            
            # Map intent to prompt type
            detected_intent = intent_result.get('intent', 'general')
            confidence = intent_result.get('confidence', 0.5)
            
            # Log intent detection result
            logger.info(f"Intent detected: {detected_intent} (confidence: {confidence}, method: {intent_result.get('method', 'unknown')})")
            
            # Get prompt_type from intent result metadata (loaded from intent.json)
            # The prompt_type should be included in the intent configuration
            prompt_type = intent_result.get('prompt_type', None)
            
            # If prompt_type is not in the result, let V5 auto-detect
            if not prompt_type and detected_intent != 'general':
                # Try to get it from the intent detector's configuration
                if hasattr(v5_engine.intent_detector, 'intent_config'):
                    intents = v5_engine.intent_detector.intent_config.get('intents', {})
                    intent_config = intents.get(detected_intent, {})
                    prompt_type = intent_config.get('prompt_type', None)
            
            # Build prompt with context if available
            prompt_with_context = request.message
            if context.get('conversation_history'):
                prompt_with_context = f"Previous conversation:\n{context['conversation_history']}\n\nCurrent message: {request.message}"
            
            # Get tools configuration from system config
            tools_enabled = False
            if hasattr(v5_engine, 'system_config') and v5_engine.system_config:
                tools_enabled = v5_engine.system_config.get('system', {}).get('tools', {}).get('enabled', False)
            
            # Generate response using the correct method with prompt type
            result = v5_engine.generate(
                prompt=prompt_with_context,
                prompt_type=prompt_type,  # Pass the detected prompt type
                session_id=request.session_id,
                max_tokens=500,
                use_tools=tools_enabled,  # Use configuration setting
                use_context=False
            )
            
            # Ensure result is a dict
            if not isinstance(result, dict):
                result = {"text": str(result) if result else ""}
            
            # Log the raw result for debugging
            logger.info(f"Raw generate result: {result}")
            
            # Extract text from the result
            response_text = ""
            if isinstance(result, dict):
                response_text = result.get("text", "")
                if result.get("error"):
                    logger.error(f"Error from v5_engine: {result.get('error')}")
                    response_text = f"I encountered an error: {result.get('error')}"
            else:
                response_text = str(result) if result else ""
            
            if not response_text or response_text.strip() == "":
                # Try with a more explicit prompt format for TinyLlama
                formatted_prompt = f"<|system|>\nYou are a helpful cannabis dispensary assistant.\n<|user|>\n{request.message}\n<|assistant|>\n"
                result = v5_engine.generate(
                    prompt=formatted_prompt,
                    session_id=request.session_id,
                    max_tokens=500,
                    use_tools=tools_enabled,  # Use configuration setting
                    use_context=False
                )
                # Ensure result is a dict
                if not isinstance(result, dict):
                    result = {"text": str(result) if result else ""}
                logger.info(f"Retry with formatted prompt result: {result}")
                if isinstance(result, dict):
                    response_text = result.get("text", "")
                    
            if not response_text or response_text.strip() == "":
                response_text = "I'm here to help! Please ask me a question about cannabis products."
            
            # Extract additional metadata from generate result if available
            metadata = {'session_id': request.session_id}
            if isinstance(result, dict):
                metadata['tokens'] = result.get('tokens')
                metadata['tokens_per_sec'] = result.get('tokens_per_sec')
                metadata['time_ms'] = result.get('time_ms')
                metadata['prompt_template'] = result.get('prompt_template')
                metadata['model'] = result.get('model')
                
            result = {
                'response': response_text,
                'tools_used': [],
                'confidence': None,
                'metadata': metadata
            }
        except Exception as e:
            logger.error(f"Error in process_message: {e}")
            result = {
                'response': f"I apologize, but I encountered an error: {str(e)}",
                'tools_used': [],
                'confidence': None,
                'metadata': {'error': str(e)}
            }
        
        # Extract response
        response_text = result.get('response', "I couldn't process that request")
        tools_used = result.get('tools_used', [])
        
        # Save interaction to context if available
        if context_manager and request.session_id:
            try:
                await context_manager.add_interaction(
                    session_id=request.session_id,
                    user_message=request.message,
                    ai_response=response_text,
                    customer_id=context.get('user_id'),
                    metadata={
                        'intent': detected_intent if 'detected_intent' in locals() else None,
                        'confidence': confidence if 'confidence' in locals() else None,
                        'tokens': result.get('metadata', {}).get('tokens'),
                        'response_time': result.get('metadata', {}).get('time_ms')
                    }
                )
            except Exception as e:
                logger.error(f"Failed to save interaction: {e}")
                # Continue even if saving fails
        
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
@app.post("/api/chat/stream")
@rate_limit(resource="chat", requests=20, seconds=60)
async def chat_v5_stream(
    request: ChatRequestModel,
    req: Request
):
    """
    V5 Streaming chat endpoint
    Returns Server-Sent Events stream
    """
    # Get v5_engine from app state
    v5_engine = getattr(req.app.state, 'v5_engine', None)
    if not v5_engine:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="V5 engine not initialized"
        )
    
    async def generate():
        """Generate streaming response"""
        try:
            context = {
                'user_id': 'test-user',
                'role': 'user',
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
@app.post("/api/function/{function_name}", response_model=FunctionCallResponse)
@rate_limit(resource="function", requests=20, seconds=60)
async def call_function(
    function_name: str,
    arguments: Dict[str, Any],
    req: Request
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
@app.get("/api/functions")
async def list_functions(
    format: str = "openai",
    category: Optional[str] = None
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
@app.get("/api/context/stats")
async def get_context_stats(req: Request):
    """
    Get context manager statistics
    """
    try:
        context_manager = getattr(req.app.state, 'context_manager', None)
        if not context_manager:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Context manager not initialized"
            )
        
        stats = await context_manager.get_stats()
        return stats
        
    except Exception as e:
        logger.error(f"Failed to get context stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve context statistics"
        )

@app.get("/api/conversations/history/{session_id}")
@rate_limit(resource="history", requests=50, seconds=60)
async def get_conversation_history(
    session_id: str,
    req: Request,
    limit: int = 20
):
    """
    Get conversation history for a session
    """
    try:
        context_manager = getattr(req.app.state, 'context_manager', None)
        if not context_manager:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Context manager not initialized"
            )
        
        history = await context_manager.get_history(session_id, limit=limit)
        context = await context_manager.get_context(session_id)
        
        return {
            "session_id": session_id,
            "history": history,
            "context": context,
            "message_count": len(history)
        }
        
    except Exception as e:
        logger.error(f"Failed to get conversation history: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve conversation history"
        )

@app.post("/api/search/products")
@rate_limit(resource="search", requests=30, seconds=60)
async def search_products(
    request: ProductSearchModel,
    req: Request
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
        auth_token=None  # No auth for testing
    )
    
    return result


# Order creation endpoint
@app.post("/api/orders")
@rate_limit(resource="order", requests=5, seconds=60)
async def create_order(
    request: OrderCreateModel,
    req: Request
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
        auth_token=None  # No auth for testing
    )
    
    return result


# Admin endpoints
@app.get("/api/admin/stats")
async def get_stats():
    """Get V5 engine statistics (testing mode - no auth required)"""
    
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