#!/usr/bin/env python3
"""
V5 AI Engine API Server
Complete standalone implementation with all security and industry features
"""

import os
import sys
import asyncio
import logging
import time
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
from api.voice_websocket import router as voice_ws_router

# Import unified chat system
from api.chat_integration import register_unified_chat_routes

# Import authentication endpoints
from api.customer_auth import router as customer_auth_router
from api.auth_otp import router as otp_auth_router
from api.auth_context import router as context_auth_router

# Import tenant and store endpoints
from api.tenant_endpoints import router as tenant_router
from api.store_endpoints import router as store_router
from api.store_hours_endpoints import router as store_hours_router
from api.store_inventory_endpoints import router as store_inventory_router
from api.payment_settings_endpoints import router as payment_settings_router
from api.payment_provider_endpoints import router as payment_provider_router

# Import kiosk endpoints
try:
    from api.kiosk_endpoints import router as kiosk_router
    KIOSK_ENABLED = True
except ImportError as e:
    print(f"ERROR: Failed to import kiosk endpoints: {e}")
    KIOSK_ENABLED = False
    kiosk_router = None
from api.client_payment_endpoints import router as client_payment_router
from api.store_payment_endpoints import router as store_payment_router
from api.payment_session_endpoints import router as payment_session_router
from api.admin_auth import router as admin_auth_router
from api.admin_device_endpoints import router as admin_device_router

# Configure logging with correlation ID support
from core.middleware.logging_middleware import (
    setup_logging_with_correlation_id,
    PerformanceLoggingMiddleware,
    MetricsLogger,
    get_correlation_id
)

# Setup enhanced logging
setup_logging_with_correlation_id()
logger = logging.getLogger(__name__)

# Import hardware endpoints
try:
    from api.hardware_endpoints import router as hardware_router
    HARDWARE_ENABLED = True
except ImportError:
    logger.warning("Hardware endpoints not available")
    HARDWARE_ENABLED = False

# Import accessories endpoints
try:
    from api.accessories_endpoints import router as accessories_router
    ACCESSORIES_ENABLED = True
    logger.info("Accessories endpoints loaded successfully")
except ImportError as e:
    logger.warning(f"Accessories endpoints not available: {e}")
    ACCESSORIES_ENABLED = False

# Import communication endpoints
try:
    from api.communication_endpoints import router as communication_router
    COMMUNICATION_ENABLED = True
    logger.info("Communication endpoints loaded successfully")
except ImportError as e:
    logger.warning(f"Communication endpoints not available: {e}")
    COMMUNICATION_ENABLED = False

# V5 Services
from services.smart_ai_engine_v5 import SmartAIEngineV5
from services.context.simple_hybrid_manager import SimpleHybridContextManager


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
            'password': os.getenv('DB_PASSWORD', 'weedgo123')
        }
        context_manager = SimpleHybridContextManager(db_config=db_config)
        await context_manager.initialize()
        app.state.context_manager = context_manager

        # Bridge context_manager to agent_pool for conversation memory
        logger.info("Bridging context manager to agent pool...")
        if v5_engine.agent_pool:
            v5_engine.agent_pool.set_context_manager(context_manager)
            logger.info("✅ Context manager successfully bridged to agent pool")

            # Initialize unified chat system with database-backed storage
            logger.info("Initializing unified chat system...")
            try:
                from api.chat_integration import initialize_unified_chat_system
                chat_service = await initialize_unified_chat_system()
                app.state.chat_service = chat_service
                logger.info("✅ Unified chat system initialized with database storage and cleanup")
            except Exception as e:
                logger.error(f"❌ Failed to initialize unified chat system: {e}", exc_info=True)
                logger.warning("Continuing without unified chat system")
        else:
            logger.warning("⚠️ Agent pool not initialized, context manager not bridged")

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

        # Try to load persisted model configuration from database
        from api.admin_endpoints import get_system_setting

        persisted_config = await get_system_setting("ai_model", "active_model_config")
        model_loaded = False

        if persisted_config and persisted_config.get("model"):
            # Load persisted model from database
            logger.info(f"Found persisted model configuration: {persisted_config['model']}")
            try:
                success = v5_engine.load_model(
                    model_name=persisted_config["model"],
                    agent_id=persisted_config.get("agent"),
                    personality_id=persisted_config.get("personality")
                )
                if success:
                    logger.info(f"✅ Successfully loaded persisted model: {persisted_config['model']} with {persisted_config.get('agent')}/{persisted_config.get('personality')} configuration")
                    model_loaded = True
                else:
                    logger.warning("Failed to load persisted model, falling back to auto-detect")
            except Exception as e:
                logger.warning(f"Error loading persisted model: {e}, falling back to auto-detect")
        else:
            logger.info("No persisted model configuration found in database")

        # Fall back to auto-detect smallest model if no persisted config or loading failed
        if not model_loaded:
            if smallest_model:
                logger.info(f"Auto-detecting and loading smallest model: {smallest_model} ({smallest_size / (1024**3):.2f} GB)")
                # Load model with dispensary agent and marcel personality (default)
                success = v5_engine.load_model(
                    model_name=smallest_model,
                    agent_id="dispensary",
                    personality_id="marcel"
                )
                if success:
                    logger.info(f"✅ Successfully loaded {smallest_model} with dispensary/marcel configuration")
                else:
                    logger.warning(f"Failed to load default model configuration")
            else:
                logger.warning("No models available to auto-load")
        
        logger.info(f"V5 Engine ready with {len(v5_engine.available_models)} models available")

        # Register function schemas
        logger.info("Registering function schemas...")
        registry = get_function_registry()

        # Tool implementations are now registered via ToolManager (see tool_manager.py)
        # Smart product search tool with LLM-based entity extraction is available
        if hasattr(v5_engine, 'tool_manager') and v5_engine.tool_manager:
            logger.info(f"Tool manager initialized with {len(v5_engine.tool_manager.list_tools())} tools")
        else:
            logger.warning("ToolManager not available in v5_engine")
        
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
    title="WeedGo AI Engine API",
    description="""## 🚀 WeedGo AI Platform API Documentation

### Available Services:
- **🤖 AGI**: Advanced AI chat, learning, and automation
- **🛍️ Commerce**: Products, orders, cart, and inventory
- **👥 Customer**: Authentication, profiles, and preferences
- **🏪 Store**: Store management, hours, and settings
- **💳 Payments**: Payment processing and transactions
- **🎙️ Voice**: Voice recognition and transcription
- **📊 Analytics**: Business intelligence and reporting
- **⚙️ Admin**: System administration and monitoring

### Quick Start:
1. Authenticate using `/api/auth/login` or API key
2. Use the search/filter box to find endpoints (enabled below)
3. Test endpoints directly from this interface
""",
    version="5.0.0",
    openapi_tags=[
        {"name": "🤖 AGI - Chat", "description": "AI chat and conversation endpoints"},
        {"name": "🧠 AGI - Dashboard", "description": "AI system monitoring and management"},
        {"name": "🔐 AGI - Authentication", "description": "AGI authentication and API keys"},
        {"name": "🛍️ Products", "description": "Product catalog and search"},
        {"name": "🛒 Cart", "description": "Shopping cart management"},
        {"name": "📦 Orders", "description": "Order processing and history"},
        {"name": "👤 Customers", "description": "Customer profiles and authentication"},
        {"name": "🏪 Stores", "description": "Store configuration and management"},
        {"name": "💰 Payments", "description": "Payment processing and methods"},
        {"name": "🎙️ Voice", "description": "Voice input and transcription"},
        {"name": "📊 Analytics", "description": "Business analytics and reporting"},
        {"name": "⚙️ Admin", "description": "System administration"},
        {"name": "🖥️ Kiosk", "description": "Self-service kiosk interface"},
        {"name": "📍 Inventory", "description": "Inventory and stock management"},
        {"name": "🔧 Hardware", "description": "Hardware detection and management"}
    ],
    swagger_ui_parameters={
        "syntaxHighlight": True,  # Enable syntax highlighting
        "tryItOutEnabled": True,  # Enable try it out by default
        "docExpansion": "list",  # Show endpoint list by default
        "filter": True,  # Enable search/filter box
        "showExtensions": True,
        "showCommonExtensions": True,
        "tagsSorter": "alpha",  # Sort tags alphabetically
        "operationsSorter": "alpha",  # Sort operations alphabetically
        "persistAuthorization": True,  # Remember auth between reloads
        "displayOperationId": False,
        "deepLinking": True,  # Enable deep linking to specific endpoints
        "displayRequestDuration": True,  # Show request duration
        "supportedSubmitMethods": ["get", "post", "put", "delete", "patch", "head", "options"],
        "validatorUrl": None,  # Disable external validator
        "withCredentials": False,  # Disable sending cookies to external sources
        "requestInterceptor": None,  # No external interceptors
        "responseInterceptor": None  # No external interceptors
    },
    docs_url="/docs",
    redoc_url="/redoc",
    swagger_ui_init_oauth=None,  # Disable OAuth init
    swagger_ui_oauth2_redirect_url=None,  # No OAuth redirect
    swagger_js_url=None,  # Use bundled JS (no external CDN)
    swagger_css_url=None,  # Use bundled CSS (no external CDN)
    swagger_favicon_url=None  # Use default favicon (no external CDN)
)

# Add performance logging middleware (before CORS to capture all requests)
app.add_middleware(
    PerformanceLoggingMiddleware,
    log_body=False,  # Set to True for debugging (be careful with sensitive data)
    slow_request_threshold=2.0  # Log warning for requests taking more than 2 seconds
)

# Add CORS middleware - allow localhost on any port
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:3001",  # Pot Palace template port
        "http://localhost:3002",  # Modern template port
        "http://localhost:3003",
        "http://localhost:3004",
        "http://localhost:3005",
        "http://localhost:3006",
        "http://localhost:3007",  # Headless template
        "http://localhost:5024",
        "http://localhost:5173",
        "http://localhost:5174"
    ],  # Allow all commerce app ports
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=["*"],
    expose_headers=["*"],
    max_age=3600,
)

# Add ASGI-based middleware for AGI streaming support
try:
    from agi.api.middleware.asgi_middleware import (
        ASGILoggingMiddleware,
        ASGIValidationMiddleware,
        ASGIErrorHandlerMiddleware
    )
    app.add_middleware(ASGILoggingMiddleware)
    app.add_middleware(ASGIValidationMiddleware)
    app.add_middleware(ASGIErrorHandlerMiddleware)
    logger.info("ASGI middleware for streaming support loaded successfully")
except Exception as e:
    logger.warning(f"Failed to load ASGI middleware: {e}")

# Add security headers middleware with relaxed CSP for Swagger UI
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)

    # Skip security headers for OPTIONS requests to avoid CORS conflicts
    if request.method == "OPTIONS":
        return response

    # Skip CSP for docs and redoc endpoints
    if request.url.path in ["/docs", "/redoc", "/openapi.json"]:
        # Allow Swagger UI to work properly
        response.headers["Content-Security-Policy"] = (
            "default-src 'self' 'unsafe-inline' 'unsafe-eval' data: blob:; "
            "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
            "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://cdn.jsdelivr.net; "
            "img-src 'self' data: blob: https://fastapi.tiangolo.com; "
            "font-src 'self' data:; "
            "connect-src 'self' http://localhost:*"
        )
    else:
        # Relaxed CSP for API endpoints to allow localhost connections
        response.headers["Content-Security-Policy"] = "default-src 'self' http://localhost:*"

    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "SAMEORIGIN"  # Changed from DENY to allow same-origin
    response.headers["X-XSS-Protection"] = "1; mode=block"
    # Remove HSTS for local development
    # response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    return response

# Auth redirect endpoints for frontend compatibility
@app.get("/api/v1/auth/")
async def auth_redirect():
    """Redirect to available auth endpoints"""
    return {
        "message": "Authentication endpoints available",
        "endpoints": {
            "customer": "/api/v1/auth/customer",
            "admin": "/api/v1/auth/admin",
            "otp": "/api/v1/auth/otp"
        }
    }

@app.post("/api/v1/auth/login")
async def auth_login_redirect():
    """Redirect login to appropriate endpoint"""
    return HTTPException(
        status_code=307,
        detail="Please use /api/v1/auth/admin/login or /api/v1/auth/customer/login"
    )

# Include routers
app.include_router(customer_auth_router)  # Customer authentication endpoints
app.include_router(otp_auth_router)   # OTP authentication endpoints
app.include_router(admin_auth_router)  # Admin authentication endpoints
app.include_router(context_auth_router)  # Context switching authentication
app.include_router(voice_router)
app.include_router(voice_ws_router)  # WebSocket endpoints for continuous voice listening

# Register unified chat routes (database-backed with Redis caching)
try:
    register_unified_chat_routes(app)
    logger.info("✅ Unified chat routes registered successfully")
except Exception as e:
    logger.error(f"❌ Failed to register unified chat routes: {e}", exc_info=True)

app.include_router(tenant_router)  # Tenant management endpoints

# File upload endpoints
try:
    from api.file_upload import router as file_upload_router
    app.include_router(file_upload_router)
    logger.info("File upload endpoints loaded successfully")
except Exception as e:
    logger.warning(f"Failed to load file upload endpoints: {e}")

# User management endpoints
try:
    from api.user_endpoints import router as user_router
    app.include_router(user_router)
    logger.info("User endpoints loaded successfully")
except Exception as e:
    logger.warning(f"Failed to load user endpoints: {e}")

# User Payment Methods
try:
    from api.user_payment_endpoints import router as user_payment_router
    app.include_router(user_payment_router)
    logger.info("User payment methods endpoints loaded successfully")
except Exception as e:
    logger.warning(f"Failed to load user payment methods endpoints: {e}")

app.include_router(store_hours_router)  # Store hours management endpoints (must be before store_router)
app.include_router(store_router)   # Store management endpoints (includes inventory stats)
app.include_router(store_inventory_router)  # Store inventory endpoints
app.include_router(payment_settings_router)  # Payment settings endpoints
app.include_router(payment_provider_router)  # Payment provider management endpoints
app.include_router(client_payment_router)  # Client payment endpoints
app.include_router(store_payment_router)  # Store payment terminal and device endpoints
app.include_router(payment_session_router)  # Payment session endpoints for Clover integration

# Kiosk endpoints
if KIOSK_ENABLED and kiosk_router:
    app.include_router(kiosk_router)  # Self-serve kiosk endpoints
    logger.info("Kiosk endpoints registered successfully")
else:
    logger.error("Kiosk endpoints not loaded - router is None or disabled")

# Import and include admin endpoints (unified admin + model management)
from api.admin_endpoints import router as admin_router
from api.analytics_endpoints import router as analytics_router
app.include_router(admin_router)
app.include_router(admin_device_router)  # Admin device management endpoints
app.include_router(analytics_router)

# Import and include AGI endpoints
try:
    # Import the AGI dashboard routes (this is the file we have fixed)
    from agi.api.dashboard_routes import router as agi_dashboard_router

    # Mount AGI dashboard router at /api/agi prefix
    app.include_router(agi_dashboard_router, prefix="/api/agi", tags=["🧠 AGI - Dashboard"])

    logger.info("AGI Dashboard endpoints loaded successfully - all 26 endpoints available")
except Exception as e:
    logger.warning(f"Failed to load AGI endpoints: {e}")

# Agent Pool endpoints for multi-agent support
try:
    from api.agent_pool_endpoints import router as agent_pool_router
    app.include_router(agent_pool_router, tags=["Agent Pool"])
    logger.info(f"Agent Pool endpoints loaded successfully - {len(agent_pool_router.routes)} endpoints available")
except Exception as e:
    logger.warning(f"Failed to load agent pool endpoints: {e}")

# Import and include inventory endpoints
from api.inventory_endpoints import router as inventory_router
app.include_router(inventory_router)

# Include communication endpoints if available
if COMMUNICATION_ENABLED and communication_router:
    app.include_router(communication_router)
    logger.info("Communication endpoints registered successfully")

# Import and include shelf location endpoints
try:
    from api.shelf_location_endpoints import router as shelf_location_router
    app.include_router(shelf_location_router)
    logger.info("Shelf location endpoints loaded successfully")
except Exception as e:
    logger.warning(f"Failed to load shelf location endpoints: {e}")

# Import and include cart endpoints
from api.cart_endpoints import router as cart_router
from api.wishlist_endpoints import router as wishlist_router
from api.customer_endpoints import router as customer_router
from api.promotion_endpoints import router as promotion_router
from api.database_management import router as database_router

# Include POS router first (before customer router to handle /customers/search route)
try:
    from api.pos_endpoints import router as pos_router
    app.include_router(pos_router)
    logger.info("POS endpoints loaded successfully")
except Exception as e:
    logger.warning(f"Failed to load POS endpoints: {e}")

# Include new POS transaction router
try:
    from api.pos_transaction_endpoints import router as pos_transaction_router
    app.include_router(pos_transaction_router)
    logger.info("POS transaction endpoints loaded successfully")
except Exception as e:
    logger.warning(f"Failed to load POS transaction endpoints: {e}")

app.include_router(cart_router)
app.include_router(customer_router)
app.include_router(promotion_router)
app.include_router(wishlist_router)
app.include_router(database_router)

# Hardware endpoints
if HARDWARE_ENABLED:
    app.include_router(hardware_router)
    logger.info("Hardware detection endpoints enabled")

# Add accessories endpoints
if ACCESSORIES_ENABLED:
    app.include_router(accessories_router)
    logger.info("Accessories management endpoints enabled")

# Add communication endpoints
if COMMUNICATION_ENABLED:
    app.include_router(communication_router)
    logger.info("Communication management endpoints enabled")

# Import and include order endpoints
try:
    from api.order_endpoints import router as order_router
    app.include_router(order_router)
except Exception as e:
    logger.warning(f"Failed to load order endpoints: {e}")
    # Add fallback mock endpoint for orders
    @app.get("/api/orders/")
    async def mock_list_orders():
        """Mock endpoint for orders when database is not available"""
        return {
            "count": 0,
            "orders": [],
            "data": []
        }

# Import and include order tracking WebSocket
try:
    from api.order_websocket import router as order_ws_router
    app.include_router(order_ws_router)
    logger.info("Order tracking WebSocket endpoints loaded")
except Exception as e:
    logger.warning(f"Failed to load order tracking WebSocket: {e}")

# Import and include translation endpoints
try:
    from api.translation_endpoints import router as translation_router
    app.include_router(translation_router)
    logger.info("Translation endpoints loaded successfully")
except Exception as e:
    logger.warning(f"Failed to load translation endpoints: {e}")

# Import and include search endpoints
try:
    from api.search_endpoints import router as search_router
    app.include_router(search_router)
    logger.info("Search endpoints loaded successfully")
except Exception as e:
    logger.warning(f"Failed to load search endpoints: {e}")

# Import and include product details endpoints
try:
    from api.product_details_endpoints import router as product_details_router
    app.include_router(product_details_router)
    logger.info("Product details endpoints loaded successfully")
except Exception as e:
    logger.warning(f"Failed to load product details endpoints: {e}")

# Import and include supplier endpoints
try:
    from api.supplier_endpoints import router as supplier_router
    app.include_router(supplier_router)
    logger.info("Supplier endpoints loaded successfully")
except Exception as e:
    logger.warning(f"Failed to load supplier endpoints: {e}")

# Import and include user context endpoints
try:
    from api.user_context_endpoints import router as user_context_router
    app.include_router(user_context_router)
    logger.info("User context endpoints loaded successfully")
except Exception as e:
    logger.warning(f"Failed to load user context endpoints: {e}")

# Import and include voice authentication endpoints
try:
    from api.auth_voice import router as voice_auth_router
    app.include_router(voice_auth_router)
    logger.info("Voice authentication endpoints loaded successfully")
except Exception as e:
    logger.warning(f"Failed to load voice authentication endpoints: {e}")

# Import and include registration integration endpoints
try:
    from api.registration_integration import router as registration_integration_router
    app.include_router(registration_integration_router)
    logger.info("Registration integration endpoints loaded successfully")
except Exception as e:
    logger.warning(f"Failed to load registration integration endpoints: {e}")

# Import and include product endpoints
try:
    from api.product_endpoints import router as product_router
    app.include_router(product_router)
    logger.info("Product endpoints loaded successfully")
except Exception as e:
    logger.warning(f"Failed to load product endpoints: {e}")

# Import and include OCS product catalog endpoints
try:
    from api.product_catalog_ocs_endpoints import router as ocs_product_router
    app.include_router(ocs_product_router)
    logger.info("OCS product catalog endpoints loaded successfully")
except Exception as e:
    logger.warning(f"Failed to load OCS product catalog endpoints: {e}")

# Import and include review endpoints
try:
    from api.review_endpoints import router as review_router
    app.include_router(review_router)
    logger.info("Review endpoints loaded successfully")
except Exception as e:
    logger.warning(f"Failed to load review endpoints: {e}")

# Import and include delivery endpoints
try:
    from api.delivery_endpoints import router as delivery_router
    from api.customer_delivery_endpoints import router as customer_delivery_router
    app.include_router(delivery_router)
    app.include_router(customer_delivery_router)  # Customer-facing delivery endpoints
    logger.info("Delivery endpoints loaded successfully")
except Exception as e:
    logger.warning(f"Failed to load delivery endpoints: {e}")

# Import and include API gateway for frontend compatibility
try:
    from api.api_gateway import router as gateway_router
    app.include_router(gateway_router)
    logger.info("API gateway endpoints loaded successfully")
except Exception as e:
    logger.warning(f"Failed to load API gateway endpoints: {e}")

# Import and include provincial catalog upload endpoints
try:
    from api.provincial_catalog_upload_endpoints import router as provincial_upload_router
    app.include_router(provincial_upload_router, prefix="/api/admin/provincial-catalog", tags=["Provincial Catalog Upload"])
    logger.info("Provincial catalog upload endpoints loaded successfully")
except Exception as e:
    logger.warning(f"Failed to load provincial catalog upload endpoints: {e}")

# Import and include SEO/Sitemap endpoints
try:
    from api.sitemap_endpoints import router as sitemap_router
    app.include_router(sitemap_router)
    logger.info("SEO/Sitemap endpoints loaded successfully")
except Exception as e:
    logger.warning(f"Failed to load SEO/Sitemap endpoints: {e}")

# Import and include Logs endpoints
try:
    from api.logs_endpoints import router as logs_router
    app.include_router(logs_router)
    logger.info("Logs endpoints loaded successfully")
except Exception as e:
    logger.warning(f"Failed to load Logs endpoints: {e}")

# Add global rate limiting
@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    """Global rate limiting middleware"""
    # Skip rate limiting for OPTIONS requests (CORS preflight)
    if request.method == "OPTIONS":
        return await call_next(request)

    # Skip rate limiting for inventory endpoints (they have their own limits)
    if "/api/inventory" in request.url.path or "/api/store-inventory" in request.url.path:
        return await call_next(request)

    # Skip rate limiting for AGI dashboard, admin endpoints, and admin auth
    # (authenticated admins have higher trust)
    if "/api/agi" in request.url.path or "/api/database" in request.url.path or "/api/admin" in request.url.path or "/api/v1/auth/admin" in request.url.path:
        return await call_next(request)

    if not hasattr(app.state, 'rate_limiter'):
        return await call_next(request)

    rate_limiter = app.state.rate_limiter
    client_id = rate_limiter.get_client_id(request)

    # Check global rate limit (increased for better user experience)
    allowed, info = await rate_limiter.check_rate_limit(
        client_id,
        resource='global',
        limit=(300, 60),  # 300 requests per minute (5 requests/second)
        algorithm='sliding_window'
    )
    
    if not allowed:
        return JSONResponse(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            content={"detail": "Too many requests", **info},
            headers={
                "Retry-After": str(info.get('retry_after', 60)),
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Credentials": "true",
                "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
                "Access-Control-Allow-Headers": "Content-Type, Authorization"
            }
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
@rate_limit(resource="chat", requests=3000, seconds=60)
async def chat_v5(
    request: ChatRequestModel,
    req: Request
):
    """
    V5 Chat endpoint with agent pool architecture
    - Uses agent pool for fast response
    - Session-based context management
    - Rate limited
    - Input validated
    """
    try:
        # Get agent pool (primary method for chat)
        from services.agent_pool_manager import get_agent_pool
        agent_pool = get_agent_pool()

        logger.info(f"Agent pool status: {agent_pool is not None}, Sessions count: {len(agent_pool.sessions) if agent_pool else 0}")

        if not agent_pool:
            # Fallback to v5_engine if agent pool not available
            v5_engine = getattr(req.app.state, 'v5_engine', None)
            if not v5_engine:
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail="Chat service not initialized"
                )
            logger.warning("Agent pool not available, falling back to direct engine")

        # Generate session ID if not provided
        session_id = request.session_id or str(uuid.uuid4())
        user_id = request.user_id or 'anonymous'

        if agent_pool:
            # Create session in agent pool if it doesn't exist
            if session_id not in agent_pool.sessions:
                # Determine agent and personality (default to dispensary/marcel)
                agent_id = request.agent_id or 'dispensary'
                personality_id = request.personality_id or 'marcel'

                logger.info(f"Creating new session: {session_id}, agent: {agent_id}, personality: {personality_id}")

                # Create session (it's async)
                session = await agent_pool.create_session(
                    session_id=session_id,
                    agent_id=agent_id,
                    personality_id=personality_id,
                    user_id=user_id
                )

                if not session:
                    logger.error(f"Failed to create session {session_id} in agent pool")
                    raise HTTPException(
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        detail="Failed to create chat session"
                    )

                logger.info(f"Created new session {session_id} with {agent_id}/{personality_id}")
            else:
                logger.info(f"Session {session_id} already exists in agent pool")

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
            # Use agent pool for fast response if available
            if agent_pool and session_id in agent_pool.sessions:
                logger.info(f"Using agent pool for session {session_id}")

                # Track generation time
                generation_start = time.time()

                # Generate response using agent pool (with cached context)
                response_text = await agent_pool.generate_message(
                    session_id=session_id,
                    message=request.message,
                    user_id=user_id
                )

                # Log AI generation metrics
                generation_time_ms = (time.time() - generation_start) * 1000
                MetricsLogger.log_operation(
                    operation="agent_pool_generation",
                    duration_ms=generation_time_ms,
                    success=True,
                    session_id=session_id,
                    user_id=user_id,
                    message_length=len(request.message),
                    response_length=len(response_text) if response_text else 0
                )

                # Build result dict for compatibility
                result = {
                    "text": response_text,
                    "session_id": session_id,
                    "agent_pool": True
                }

                # Skip intent detection and other processing when using agent pool
                detected_intent = "general"
                confidence = 1.0
            else:
                # Fallback to direct engine if agent pool not available
                logger.warning(f"Agent pool not available for session {session_id}, using direct engine")

                # Get v5_engine
                v5_engine = getattr(req.app.state, 'v5_engine', None)
                if not v5_engine:
                    raise HTTPException(
                        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                        detail="V5 engine not initialized"
                    )

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
            
            # Handle intent result only for direct engine path
            if not (agent_pool and session_id in agent_pool.sessions):
                # Map intent to prompt type
                detected_intent = intent_result.get('intent', 'general')
                confidence = intent_result.get('confidence', 0.5)

                # Log intent detection result
                logger.info(f"Intent detected: {detected_intent} (confidence: {confidence}, method: {intent_result.get('method', 'unknown')})")
            
            # Only process intent and generate for direct engine path
            if not (agent_pool and session_id in agent_pool.sessions):
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
            
            # Extract text from the result (handle both agent pool and direct engine responses)
            response_text = ""
            if agent_pool and session_id in agent_pool.sessions:
                # Response already extracted in agent pool path
                response_text = result.get("text", "")
            elif isinstance(result, dict):
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
@rate_limit(resource="chat", requests=2000, seconds=60)
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
@rate_limit(resource="function", requests=2000, seconds=60)
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
@rate_limit(resource="history", requests=5000, seconds=60)
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
@rate_limit(resource="search", requests=3000, seconds=60)
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


# Order creation endpoint (V5 engine - disabled to avoid conflict with order_endpoints router)
# @app.post("/api/orders")
# @rate_limit(resource="order", requests=500, seconds=60)
# async def create_order(
#     request: OrderCreateModel,
#     req: Request
# ):
#     """Create an order using V5 engine"""
#     if not v5_engine:
#         raise HTTPException(
#             status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
#             detail="V5 engine not initialized"
#         )
#
#     # Use api_orchestrator tool
#     tool_manager = v5_engine.tool_manager
#     if not tool_manager:
#         raise HTTPException(
#             status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
#             detail="Tools not initialized"
#         )
#
#     # Execute order creation
#     result = await tool_manager.execute_tool(
#         "api_orchestrator",
#         action="submit",
#         operation_id="createOrder",
#         data=request.dict(),
#         auth_token=None  # No auth for testing
#     )
#
#     return result


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
    response = JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail}
    )
    # Add CORS headers to error responses
    origin = request.headers.get("origin")
    if origin in ["http://localhost:3003", "http://localhost:3004", "http://localhost:3000", "http://localhost:5024", "http://localhost:5173", "http://localhost:5174"]:
        response.headers["Access-Control-Allow-Origin"] = origin
        response.headers["Access-Control-Allow-Credentials"] = "true"
        response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS, PATCH"
        response.headers["Access-Control-Allow-Headers"] = "*"
    return response


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle general exceptions"""
    logger.error(f"Unhandled exception: {exc}")
    response = JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Internal server error"}
    )
    # Add CORS headers to error responses
    origin = request.headers.get("origin")
    if origin in ["http://localhost:3003", "http://localhost:3004", "http://localhost:3000", "http://localhost:5024", "http://localhost:5173", "http://localhost:5174"]:
        response.headers["Access-Control-Allow-Origin"] = origin
        response.headers["Access-Control-Allow-Credentials"] = "true"
        response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS, PATCH"
        response.headers["Access-Control-Allow-Headers"] = "*"
    return response


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
        app,  # Pass the app instance directly instead of module string
        host=host,
        port=port,
        reload=os.environ.get('DEBUG', 'false').lower() == 'true',
        log_level="info",
        access_log=True  # Enable access logging
    )


if __name__ == "__main__":
    main()