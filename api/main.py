#!/usr/bin/env python3
"""
WeedGo AI Engine Service - Production API
Consolidated, clean, maintainable implementation following best practices
"""

import os
import logging
from datetime import datetime
from typing import Optional, Dict, Any, List
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, validator
import uvicorn

from config import settings
from services.budtender_service import BudtenderService
from services.recognition_service import RecognitionService
from services.pricing_service import PricingService
from services.verification_service import VerificationService
from services.model_manager import ModelManager
from middleware.error_handler import error_handler_middleware
from middleware.logging import logging_middleware
from utils.monitoring import metrics_collector

# Configure logging
logging.basicConfig(
    level=settings.LOG_LEVEL,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(settings.LOG_FILE),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Lifecycle management
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle"""
    logger.info("Starting WeedGo AI Engine Service...")
    
    # Initialize services
    app.state.model_manager = ModelManager()
    app.state.budtender = BudtenderService(app.state.model_manager)
    app.state.recognition = RecognitionService()
    app.state.pricing = PricingService()
    app.state.verification = VerificationService()
    
    # Load models
    await app.state.model_manager.initialize()
    
    logger.info("AI Engine Service started successfully")
    
    yield
    
    # Cleanup
    logger.info("Shutting down AI Engine Service...")
    await app.state.model_manager.cleanup()
    logger.info("AI Engine Service stopped")

# Create FastAPI app
app = FastAPI(
    title="WeedGo AI Engine Service",
    version="2.0.0",
    description="Production-ready AI service for cannabis retail",
    lifespan=lifespan,
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# Add middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.middleware("http")(error_handler_middleware)
app.middleware("http")(logging_middleware)

# Request/Response Models
class ChatRequest(BaseModel):
    """Chat request model with validation"""
    message: str = Field(..., min_length=1, max_length=1000)
    customer_id: str = Field(..., regex="^[a-zA-Z0-9-]+$")
    language: str = Field(default="en", regex="^[a-z]{2}$")
    context: Optional[Dict[str, Any]] = None
    
    @validator('language')
    def validate_language(cls, v):
        supported = ['en', 'fr', 'es', 'pt', 'ar', 'zh']
        if v not in supported:
            raise ValueError(f"Language must be one of {supported}")
        return v

class ChatResponse(BaseModel):
    """Chat response model"""
    response: str
    suggestions: List[Dict[str, Any]]
    model_used: str
    response_time: float
    confidence: float

class RecognitionRequest(BaseModel):
    """Face recognition request"""
    image_base64: str = Field(..., min_length=100)
    store_id: str = Field(..., regex="^[a-zA-Z0-9-]+$")

class PricingRequest(BaseModel):
    """Dynamic pricing request"""
    product_id: str
    quantity: float = Field(gt=0)
    customer_type: str = Field(default="regular")
    
class VerificationRequest(BaseModel):
    """Age verification request"""
    document_base64: str = Field(..., min_length=100)
    document_type: str = Field(default="drivers_license")

class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    version: str
    models_loaded: Dict[str, bool]
    uptime: float
    timestamp: str

# Dependency injection
def get_budtender(request, app_state=Depends(lambda: app.state)) -> BudtenderService:
    """Get budtender service instance"""
    return app_state.budtender

def get_recognition(app_state=Depends(lambda: app.state)) -> RecognitionService:
    """Get recognition service instance"""
    return app_state.recognition

def get_pricing(app_state=Depends(lambda: app.state)) -> PricingService:
    """Get pricing service instance"""
    return app_state.pricing

def get_verification(app_state=Depends(lambda: app.state)) -> VerificationService:
    """Get verification service instance"""
    return app_state.verification

# API Endpoints
@app.get("/health", response_model=HealthResponse, tags=["System"])
async def health_check():
    """Health check endpoint"""
    return HealthResponse(
        status="healthy",
        version="2.0.0",
        models_loaded=app.state.model_manager.get_status(),
        uptime=(datetime.now() - app.state.start_time).total_seconds(),
        timestamp=datetime.now().isoformat()
    )

@app.post("/api/chat", response_model=ChatResponse, tags=["Budtender"])
async def chat(
    request: ChatRequest,
    budtender: BudtenderService = Depends(get_budtender)
):
    """
    Virtual budtender chat endpoint
    Supports 6 languages and intelligent model routing
    """
    try:
        result = await budtender.chat(
            message=request.message,
            customer_id=request.customer_id,
            language=request.language,
            context=request.context
        )
        
        metrics_collector.record_chat(
            customer_id=request.customer_id,
            model=result["model_used"],
            response_time=result["response_time"]
        )
        
        return ChatResponse(**result)
    except Exception as e:
        logger.error(f"Chat error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process chat request"
        )

@app.post("/api/recognize", tags=["Recognition"])
async def recognize_customer(
    request: RecognitionRequest,
    recognition: RecognitionService = Depends(get_recognition)
):
    """
    Customer face recognition endpoint
    Returns customer profile if recognized
    """
    try:
        result = await recognition.recognize(
            image_base64=request.image_base64,
            store_id=request.store_id
        )
        return result
    except Exception as e:
        logger.error(f"Recognition error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process recognition request"
        )

@app.post("/api/pricing", tags=["Pricing"])
async def dynamic_pricing(
    request: PricingRequest,
    pricing: PricingService = Depends(get_pricing)
):
    """
    Dynamic pricing optimization endpoint
    Returns optimized price based on various factors
    """
    try:
        result = await pricing.calculate(
            product_id=request.product_id,
            quantity=request.quantity,
            customer_type=request.customer_type
        )
        return result
    except Exception as e:
        logger.error(f"Pricing error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to calculate pricing"
        )

@app.post("/api/verify", tags=["Verification"])
async def verify_age(
    request: VerificationRequest,
    verification: VerificationService = Depends(get_verification)
):
    """
    Age verification endpoint
    Verifies customer is 19+ (Ontario requirement)
    """
    try:
        result = await verification.verify(
            document_base64=request.document_base64,
            document_type=request.document_type
        )
        return result
    except Exception as e:
        logger.error(f"Verification error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to verify document"
        )

@app.get("/api/models", tags=["System"])
async def get_models_status():
    """Get status of all loaded models"""
    return app.state.model_manager.get_detailed_status()

@app.post("/api/models/reload", tags=["System"])
async def reload_models():
    """Reload AI models"""
    try:
        await app.state.model_manager.reload()
        return {"status": "success", "message": "Models reloaded"}
    except Exception as e:
        logger.error(f"Model reload error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to reload models"
        )

@app.get("/metrics", tags=["Monitoring"])
async def get_metrics():
    """Get application metrics"""
    return metrics_collector.get_metrics()

# Error handlers
@app.exception_handler(ValueError)
async def value_error_handler(request, exc):
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"detail": str(exc)}
    )

@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Internal server error"}
    )

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower()
    )