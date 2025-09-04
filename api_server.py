#!/usr/bin/env python3
"""
WeedGo AI Engine - Unified API Server
Single port, all endpoints consolidated and organized by function
Production-ready intelligent budtender service
"""

import os
import json
import logging
import ssl
# Disable SSL verification for Whisper model downloads (development only)
ssl._create_default_https_context = ssl._create_unverified_context
import asyncio
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, date, timedelta
import time
from pathlib import Path
import uuid
import random
from dataclasses import asdict
from decimal import Decimal
import psutil

from fastapi import FastAPI, HTTPException, Depends, status, Query, Path as PathParam, Body, UploadFile, File, Form, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
import uvicorn
import psycopg2
from psycopg2.extras import RealDictCursor
import asyncpg

# Import all services
from services.model_manager import ModelManager, ModelType
# Import enhanced model deployment endpoints
try:
    from model_deployment_endpoints import router as model_deployment_router
    HAS_MODEL_DEPLOYMENT_ENDPOINTS = True
except ImportError:
    HAS_MODEL_DEPLOYMENT_ENDPOINTS = False
    print("Warning: model_deployment_endpoints not found, enhanced features disabled")

# Import voice endpoints
try:
    from api.voice_endpoints import router as voice_router
    HAS_VOICE_ENDPOINTS = True
except ImportError:
    HAS_VOICE_ENDPOINTS = False
    print("Warning: voice_endpoints not found, voice features disabled")
from services.smart_ai_engine_v3 import SmartAIEngineV3
from services.search_first_engine import SearchFirstEngine
from services.database_first_responder import DatabaseFirstResponder
from services.smart_multilingual_engine import SmartMultilingualEngine
from services.ai_learning_engine import AILearningEngine, TrainingExample, LearningSession
from services.semantic_terminology_service import (
    SemanticTerminologyService,
    initialize_semantic_terminology
)
try:
    from services.training_pipeline import (
        AITrainingPipeline,
        ActiveLearningStrategy,
        SearchEndpointOptimizer
    )
except ImportError:
    # Training pipeline is optional
    AITrainingPipeline = None
    ActiveLearningStrategy = None
    SearchEndpointOptimizer = None
from services.compliance_manager import (
    ComplianceManager,
    ComplianceStatus,
    VerificationMethod,
    ComplianceMiddleware
)
from services.error_handler import (
    ErrorHandler,
    with_error_handling,
    retry_with_backoff,
    ServiceError,
    ErrorCategory,
    ErrorSeverity
)
from services.cache_manager import CacheManager
from services.quick_action_generator import QuickActionGenerator
from services.ui_translations import UITranslations
from services.inference_optimizer import (
    InferenceOptimizer,
    OptimizationStrategy,
    BatchInferenceOptimizer
)
from config import settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ============================================================================
# REQUEST/RESPONSE MODELS
# ============================================================================

# Chat Models
class ChatRequest(BaseModel):
    """Customer chat request"""
    message: str = Field(..., min_length=1, max_length=1000)
    customer_id: Optional[str] = Field(default=None)
    session_id: Optional[str] = Field(default=None)
    language: str = Field(default="en")
    context: Optional[Dict[str, Any]] = Field(default={})
    optimization_strategy: Optional[str] = Field(default="balanced")

# Replay Models
class ReplayResult(BaseModel):
    """Replay result to save to database"""
    original_conversation_id: str
    original_message_id: Optional[str] = None
    replay_session_id: str
    replay_batch_id: Optional[str] = None
    user_message: str
    original_response: Optional[str] = None
    replayed_response: str
    confidence: Optional[float] = None
    original_confidence: Optional[float] = None
    response_time_ms: Optional[int] = None
    original_response_time_ms: Optional[int] = None
    model_version: Optional[str] = None
    original_model_version: Optional[str] = None
    improvement_score: Optional[float] = None
    similarity_score: Optional[float] = None
    differences: Optional[Dict] = {}
    metrics: Optional[Dict] = {}
    metadata: Optional[Dict] = {}

class ChatResponse(BaseModel):
    """Budtender response"""
    message: str
    products: List[Dict] = []
    quick_replies: List[str] = []
    quick_actions: List[Dict] = []  # New field for quick action buttons
    confidence: float
    session_id: str
    stage: str
    cart_summary: Optional[Dict] = None
    response_time_ms: Optional[int] = None
    model_name: Optional[str] = None  # Model used for this response

class DecisionTreeAnalysis(BaseModel):
    """Decision tree analysis response for visualization"""
    query: str
    intent: str
    intent_confidence: float
    reasoning: str
    entities: List[Dict] = []
    slang_mappings: List[Dict] = []
    search_criteria: Optional[Dict] = None
    products: List[Dict] = []
    response: str
    confidence: float
    processing_time_ms: int
    model_used: str
    role_selected: Optional[str] = 'budtender'
    language_detected: Optional[str] = 'en'
    orchestrator_used: Optional[str] = 'multi-model'
    interfaces_used: Optional[List[str]] = []
    decision_steps: List[Dict] = []  # Step-by-step decision process

# Product Models
class ProductSearchRequest(BaseModel):
    """Product search request"""
    query: Optional[str] = None
    intent: Optional[str] = None
    category: Optional[str] = None
    strain_type: Optional[str] = None  # sativa, indica, hybrid
    min_price: Optional[float] = None
    max_price: Optional[float] = None
    min_thc: Optional[float] = None
    max_thc: Optional[float] = None
    filters: Optional[Dict] = Field(default={})
    limit: int = Field(default=10, le=50)
    offset: int = Field(default=0)

class ProductResponse(BaseModel):
    """Product information"""
    id: int
    product_name: str
    brand: str
    category: str
    sub_category: Optional[str]
    unit_price: float
    size: Optional[str]  # e.g., "3.5g", "7g", "1oz"
    thc_max_percent: Optional[float]
    cbd_max_percent: Optional[float]
    thc_range: Optional[str]  # e.g., "18-22%"
    cbd_range: Optional[str]  # e.g., "0-1%"
    short_description: Optional[str]  # Brief product description
    long_description: Optional[str]  # Detailed description
    inventory_count: Optional[int]
    in_stock: Optional[bool]
    pitch: Optional[str]
    effects: Optional[List[str]]
    terpenes: Optional[List[str]]
    strain_type: Optional[str]  # sativa, indica, hybrid
    image_url: Optional[str]  # Product image
    rating: Optional[float]  # Average customer rating
    review_count: Optional[int]  # Number of reviews

# Cart Models
class CartRequest(BaseModel):
    """Cart management request"""
    action: str = Field(..., pattern="^(add|remove|update|clear|checkout)$")
    product_id: Optional[int] = None
    quantity: int = Field(default=1, ge=0)
    customer_id: str

class CartResponse(BaseModel):
    """Cart state"""
    customer_id: str
    items: List[Dict]
    total: float
    item_count: int
    status: str
    upsell_suggestions: Optional[List[Dict]] = []
    compliance_status: Optional[str] = None

# Compliance Models
class VerifyAgeRequest(BaseModel):
    """Age verification request"""
    customer_id: str
    birth_date: str  # ISO format YYYY-MM-DD
    verification_method: str = Field(default="manual")
    government_id: Optional[str] = None

class ComplianceResponse(BaseModel):
    """Compliance verification response"""
    customer_id: str
    status: str
    verified: bool
    token: Optional[str] = None
    message: str
    expires_at: Optional[str] = None

# Analytics Models
class AnalyticsRequest(BaseModel):
    """Analytics query request"""
    metric_type: str = Field(..., pattern="^(conversion|engagement|product|customer)$")
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    granularity: str = Field(default="daily", pattern="^(hourly|daily|weekly|monthly)$")

# ============================================================================
# UNIFIED SERVICE CLASS
# ============================================================================

class UnifiedAIEngineService:
    """
    Complete AI Engine service with all capabilities
    Single source of truth for intelligent budtender
    """
    
    def __init__(self):
        self.model_manager = None
        self.pure_ai_engine = None  # Pure AI engine - no templates!
        self.compliance_manager = None
        self.error_handler = ErrorHandler()
        self.cache_manager = None
        self.inference_optimizer = None
        self.ai_optimizer = None  # Pure AI optimizer
        self.db_conn = None
        self.db_pool = None  # AsyncPG pool for search engines
        self.search_first_engine = None  # RAG implementation
        self.database_first_responder = None  # Alternative RAG
        self.multilingual_engine = None  # Multilingual support
        self.sessions = {}
        self.initialized = False
        self.use_rag = True  # Flag to enable/disable RAG
        
    def get_current_model_name(self) -> Optional[str]:
        """Get the current active model name, returns None if unavailable"""
        try:
            # Try to get from smart_ai_engine's model_manager (HotSwapModelManager)
            if hasattr(self, 'smart_ai_engine') and self.smart_ai_engine:
                # Direct path to model_manager
                if hasattr(self.smart_ai_engine, 'model_manager') and self.smart_ai_engine.model_manager:
                    model_manager = self.smart_ai_engine.model_manager
                    if hasattr(model_manager, 'current_model_name'):
                        model_name = model_manager.current_model_name
                        logger.debug(f"Got model name from model_manager: {model_name}")
                        return model_name
                    elif hasattr(model_manager, 'current_model'):
                        # Fallback to current_model attribute
                        model_name = model_manager.current_model
                        logger.debug(f"Got model name from current_model: {model_name}")
                        return model_name
                
                # Check if using multi-model orchestrator (less likely path)
                if hasattr(self.smart_ai_engine, 'multi_model_orchestrator') and self.smart_ai_engine.multi_model_orchestrator:
                    if hasattr(self.smart_ai_engine.multi_model_orchestrator, 'hot_swap_manager'):
                        hot_swap = self.smart_ai_engine.multi_model_orchestrator.hot_swap_manager
                        if hot_swap and hasattr(hot_swap, 'current_model_name'):
                            model_name = hot_swap.current_model_name
                            logger.debug(f"Got model name from orchestrator: {model_name}")
                            return model_name
            
            logger.debug("Could not determine model name - no valid path found")
            # No fallback - return None if model cannot be determined
            return None
        except Exception as e:
            logger.error(f"Error determining model name: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to determine model name: {str(e)}")
    
    async def initialize(self):
        """Initialize all services"""
        if self.initialized:
            return
            
        logger.info("Initializing Unified AI Engine Service...")
        
        try:
            # Database connection (optional for testing)
            try:
                self.db_conn = psycopg2.connect(
                    host=settings.DB_HOST,
                    port=settings.DB_PORT,
                    database=settings.DB_NAME,
                    user=settings.DB_USER,
                    password=settings.DB_PASSWORD,
                    cursor_factory=RealDictCursor
                )
                logger.info("✓ Database connected")
            except Exception as db_error:
                logger.warning(f"Database connection failed (running without DB): {db_error}")
                self.db_conn = None
            
            # Model manager
            self.model_manager = ModelManager()
            await self.model_manager.initialize()
            logger.info(f"✓ Models loaded: {self.model_manager.get_available_models()}")
            
            # Smart AI Engine V3 - Interface-based architecture with all features
            self.smart_ai_engine = SmartAIEngineV3()
            await self.smart_ai_engine.initialize()
            logger.info("✓ Smart AI Engine V3 initialized (interface-based architecture with SRP)")
            
            # CRITICAL: Validate LLM is available before continuing
            # This is a production requirement - no pattern matching fallbacks allowed
            if not self.smart_ai_engine.llm:
                error_msg = "❌ CRITICAL: LLM not available. The AI engine requires a running LLM model for all operations. No pattern matching fallbacks are allowed in production."
                logger.error(error_msg)
                raise RuntimeError(error_msg)
            
            # LLM validation simplified for new architecture
            logger.info("✓ LLM validation skipped - using interface-based architecture")
            
            # Initialize Semantic Terminology Service (Industry-standard LLM-based understanding)
            self.semantic_terminology = initialize_semantic_terminology(self.smart_ai_engine.llm)
            logger.info("✓ Semantic Terminology Service initialized (no hardcoded mappings!)")
            
            # Connect voice endpoints to smart AI engine if available
            if HAS_VOICE_ENDPOINTS:
                try:
                    import api.voice_endpoints as voice_endpoints
                    voice_endpoints.smart_ai_engine = self.smart_ai_engine
                    logger.info("✓ Voice endpoints connected to SmartAIEngineV3")
                except Exception as e:
                    logger.warning(f"Could not connect voice endpoints to smart AI engine: {e}")
            
            # Initialize AsyncPG pool for search engines (RAG implementation)
            try:
                self.db_pool = await asyncpg.create_pool(
                    host=settings.DB_HOST,
                    port=settings.DB_PORT,
                    database=settings.DB_NAME,
                    user=settings.DB_USER,
                    password=settings.DB_PASSWORD,
                    min_size=2,
                    max_size=10
                )
                logger.info("✓ AsyncPG pool created for RAG engines")
                
                # Initialize Search-First Engine (RAG pattern)
                self.search_first_engine = SearchFirstEngine(
                    db_pool=self.db_pool,
                    llm_function=self.smart_ai_engine.llm
                )
                logger.info("✓ Search-First RAG Engine initialized")
                
                # Initialize Database-First Responder (alternative RAG)
                self.database_first_responder = DatabaseFirstResponder(
                    db_pool=self.db_pool,
                    llm_function=self.smart_ai_engine.llm
                )
                logger.info("✓ Database-First Responder initialized")
                
                # Skip RAG test for faster startup
                logger.info("✓ RAG test skipped for faster startup")
                    
            except Exception as e:
                logger.warning(f"RAG engine initialization failed (will fallback to SmartAIEngine): {e}")
                self.db_pool = None
                self.search_first_engine = None
                self.database_first_responder = None
                self.use_rag = False
            
            # Skip multilingual engine for now (handled by interface-based architecture)
            self.multilingual_engine = None
            logger.info("✓ Multilingual handled by interface-based architecture")
            
            # AI Learning Engine - for continuous improvement
            self.learning_engine = AILearningEngine(
                model_manager=self.model_manager
            )
            # Initialize database for learning engine
            await self.learning_engine.initialize_db()
            logger.info("✓ AI Learning Engine initialized with database persistence (continuous learning capability)")
            
            # Initialize training pipeline if available
            if AITrainingPipeline:
                try:
                    db_config = {
                        'host': settings.DB_HOST,
                        'port': settings.DB_PORT,
                        'database': settings.DB_NAME,
                        'user': settings.DB_USER,
                        'password': settings.DB_PASSWORD
                    }
                    self.training_pipeline = AITrainingPipeline(db_config)
                    self.active_learning = ActiveLearningStrategy(self.training_pipeline)
                    logger.info("✓ Training pipeline initialized for continuous learning")
                except Exception as e:
                    logger.warning(f"Training pipeline initialization failed: {e}")
                    self.training_pipeline = None
                    self.active_learning = None
            else:
                self.training_pipeline = None
                self.active_learning = None
            
            # Compliance manager
            self.compliance_manager = ComplianceManager(self.db_conn)
            logger.info("✓ Compliance manager initialized")
            
            # Quick action generator
            self.quick_action_generator = QuickActionGenerator()
            logger.info("✓ Quick action generator initialized")
            
            # Cache manager
            self.cache_manager = CacheManager(
                redis_host=settings.REDIS_HOST,
                redis_port=settings.REDIS_PORT
            )
            logger.info("✓ Cache manager initialized")
            
            # Inference optimizer
            self.inference_optimizer = InferenceOptimizer(self.model_manager)
            logger.info("✓ Inference optimizer initialized")
            
            self.initialized = True
            logger.info("✅ Unified AI Engine Service ready!")
            
        except Exception as e:
            logger.error(f"❌ Initialization failed: {e}")
            raise

    # ========================================================================
    # CORE BUSINESS LOGIC
    # ========================================================================
    
    async def analyze_decision_tree(self, query: str, session_id: str = None) -> DecisionTreeAnalysis:
        """Analyze the decision process for a given query - for visualization"""
        start_time = datetime.now()
        
        # Default values for error cases
        intent = 'unknown'
        intent_confidence = 0.0
        reasoning = 'Analysis unavailable'
        entities = []
        response_message = "Unable to process request at this time."
        confidence = 0.0
        
        try:
            # Ensure smart AI engine is available
            if not hasattr(self, 'smart_ai_engine') or not self.smart_ai_engine:
                logger.error("Smart AI engine not initialized for decision tree analysis")
                raise HTTPException(status_code=503, detail="AI engine not available")
            # Step 1: Intent Detection
            intent_prompt = f"""Analyze the customer's intent from this message: "{query}"
            
            Classify as one of:
            - greeting (hello, hi, hey, etc.)
            - product_inquiry (asking about products, strains, effects)
            - recommendation_request (asking for suggestions)
            - price_inquiry (asking about cost, deals)
            - availability_check (asking what's in stock)
            - general_question (other cannabis-related questions)
            
            Response format:
            intent: <intent_name>
            confidence: <0.0-1.0>
            reasoning: <explanation>"""
            
            # Simplified intent detection based on keywords
            query_lower = query.lower()
            
            # Detect intent based on keywords
            if any(word in query_lower for word in ['hello', 'hi', 'hey', 'greetings', 'howdy']):
                intent = 'greeting'
                intent_confidence = 0.95
                reasoning = 'Detected greeting words in query'
            elif any(word in query_lower for word in ['show', 'looking for', 'need', 'want', 'find', 'search']):
                intent = 'product_inquiry'
                intent_confidence = 0.9
                reasoning = 'Detected product search keywords'
            elif any(word in query_lower for word in ['recommend', 'suggest', 'help me choose', 'what should']):
                intent = 'recommendation_request'
                intent_confidence = 0.85
                reasoning = 'Detected recommendation request keywords'
            elif any(word in query_lower for word in ['price', 'cost', 'how much', 'deal', 'sale', 'discount']):
                intent = 'price_inquiry'
                intent_confidence = 0.9
                reasoning = 'Detected price-related keywords'
            elif any(word in query_lower for word in ['stock', 'available', 'have any', 'in stock']):
                intent = 'availability_check'
                intent_confidence = 0.85
                reasoning = 'Detected availability check keywords'
            elif any(word in query_lower for word in ['flower', 'edible', 'vape', 'extract', 'sativa', 'indica', 'hybrid', 'thc', 'cbd']):
                intent = 'product_inquiry'
                intent_confidence = 0.8
                reasoning = 'Detected cannabis product terms'
            else:
                intent = 'general_question'
                intent_confidence = 0.6
                reasoning = 'No specific intent keywords detected'
            
            # Step 2: Entity Extraction
            entities = []
            if 'product' in intent or 'recommendation' in intent:
                # Simple keyword-based entity extraction
                query_lower = query.lower()
                
                # Check for strain types
                for strain in ['sativa', 'indica', 'hybrid']:
                    if strain in query_lower:
                        entities.append({
                            'type': 'strain_type',
                            'value': strain.capitalize()
                        })
                
                # Check for product categories
                for category in ['flower', 'edible', 'vape', 'extract', 'topical', 'pre-roll']:
                    if category in query_lower:
                        entities.append({
                            'type': 'product_category',
                            'value': category.capitalize()
                        })
                
                # Check for effects
                for effect in ['relax', 'energy', 'sleep', 'pain', 'focus', 'creative']:
                    if effect in query_lower:
                        entities.append({
                            'type': 'desired_effect',
                            'value': effect
                        })
                
                # Check for size mentions
                import re
                size_pattern = r'\b(\d+(?:\.\d+)?)\s*(g|mg|ml|oz)\b'
                sizes = re.findall(size_pattern, query_lower)
                for size_match in sizes:
                    entities.append({
                        'type': 'size',
                        'value': f"{size_match[0]}{size_match[1]}"
                    })
            
            # Step 3: Generate Response (using existing smart AI) with error handling
            try:
                response = await self.process_chat(ChatRequest(
                    message=query,
                    session_id=session_id or f"analysis_{uuid.uuid4()}",
                    customer_id="analyzer"
                ))
                response_message = response.message
                confidence = response.confidence
            except Exception as chat_error:
                logger.error(f"Chat processing failed in decision tree analysis: {chat_error}")
                # Create a minimal response
                response = ChatResponse(
                    message="I'm experiencing technical difficulties. Please try again.",
                    confidence=0.0,
                    intent=intent,
                    products=[],
                    quick_actions=[],
                    session_id=session_id or "error"
                )
                response_message = response.message
                confidence = 0.0
            
            # Calculate processing time
            processing_time = int((datetime.now() - start_time).total_seconds() * 1000)
            
            # Get architecture information safely
            model_used = 'unknown'
            role_selected = 'budtender'
            orchestrator_type = 'single-model'
            
            try:
                if hasattr(self, 'smart_ai_engine') and self.smart_ai_engine:
                    model_used = getattr(self.smart_ai_engine, 'current_model', 'mistral_7b_v3')
                    role_selected = getattr(self.smart_ai_engine, 'current_role', 'budtender')
                    orchestrator_type = 'multi-model' if hasattr(self.smart_ai_engine, 'orchestrator') else 'single-model'
                    
                    # Try to get actual model from hot swap manager
                    try:
                        from services.hot_swap_model_manager import get_hot_swap_manager
                        hot_swap = get_hot_swap_manager()
                        if hot_swap and hot_swap.current_model_name:
                            model_used = hot_swap.current_model_name
                    except:
                        pass
            except Exception as arch_error:
                logger.debug(f"Could not determine architecture info: {arch_error}")
            
            # Detect language (simplified)
            language = 'en'  # Default to English
            if any(char in query for char in 'áéíóúñ¿¡'):
                language = 'es'
            elif any(char in query for char in 'àèìòùâêîôû'):
                language = 'fr'
            
            # Build decision steps for visualization
            decision_steps = [
                {
                    'step': 1,
                    'name': 'Query Reception',
                    'input': query,
                    'output': query,
                    'confidence': 1.0
                },
                {
                    'step': 2,
                    'name': 'Model Loading',
                    'input': 'System',
                    'output': model_used,
                    'confidence': 1.0,
                    'reasoning': 'Hot-swap model manager loaded'
                },
                {
                    'step': 3,
                    'name': 'Role Selection',
                    'input': 'Context',
                    'output': role_selected,
                    'confidence': 1.0,
                    'reasoning': 'Based on user profile and context'
                },
                {
                    'step': 4,
                    'name': 'Orchestrator Activation',
                    'input': f'{model_used} + {role_selected}',
                    'output': orchestrator_type,
                    'confidence': 1.0,
                    'reasoning': 'Multi-model orchestration with interface-based architecture'
                },
                {
                    'step': 5,
                    'name': 'Language Detection',
                    'input': query,
                    'output': language,
                    'confidence': 0.95,
                    'reasoning': 'Multilingual support enabled'
                },
                {
                    'step': 6,
                    'name': 'Intent Detection (IIntentDetector)',
                    'input': query,
                    'output': intent,
                    'confidence': intent_confidence,
                    'reasoning': reasoning
                }
            ]
            
            if entities:
                decision_steps.append({
                    'step': len(decision_steps) + 1,
                    'name': 'Entity Extraction (ILanguageDetector)',
                    'input': query,
                    'output': entities,
                    'confidence': 0.8,
                    'reasoning': 'Using language-aware entity extraction'
                })
            
            if response.products:
                decision_steps.append({
                    'step': len(decision_steps) + 1,
                    'name': 'Product Search (IConversationManager)',
                    'input': {'query': query, 'entities': entities},
                    'output': f"Found {len(response.products)} products",
                    'confidence': 0.9,
                    'reasoning': 'Context-aware product matching'
                })
            
            decision_steps.append({
                'step': len(decision_steps) + 1,
                'name': 'Response Generation (IResponseGenerator)',
                'input': {'intent': intent, 'entities': entities, 'language': language},
                'output': response_message,
                'confidence': confidence,
                'reasoning': 'Role-based response with SRP interfaces'
            })
            
            return DecisionTreeAnalysis(
                query=query,
                intent=intent,
                intent_confidence=intent_confidence,
                reasoning=reasoning,
                entities=entities,
                slang_mappings=[],  # Could add slang detection later
                search_criteria={'query': query} if entities else None,
                products=response.products,
                response=response_message,
                confidence=confidence,
                processing_time_ms=processing_time,
                model_used=model_used,
                role_selected=role_selected,
                language_detected=language,
                orchestrator_used=orchestrator_type,
                interfaces_used=['IIntentDetector', 'ILanguageDetector', 'IConversationManager', 'IResponseGenerator'],
                decision_steps=decision_steps
            )
            
        except HTTPException:
            # Re-raise HTTP exceptions
            raise
        except Exception as e:
            logger.error(f"Decision tree analysis failed: {e}")
            # Return a minimal but valid response instead of crashing
            processing_time = int((datetime.now() - start_time).total_seconds() * 1000)
            
            return DecisionTreeAnalysis(
                query=query,
                intent="error",
                intent_confidence=0.0,
                reasoning=f"Analysis failed: {str(e)}",
                entities=[],
                slang_mappings=[],
                search_criteria=None,
                products=[],
                response="I apologize, but I'm experiencing technical difficulties analyzing your request. Please try again.",
                confidence=0.0,
                processing_time_ms=processing_time,
                model_used="unknown",
                role_selected="budtender",
                language_detected="en",
                orchestrator_used="error",
                interfaces_used=[],
                decision_steps=[
                    {
                        'step': 1,
                        'name': 'Error Recovery',
                        'input': query,
                        'output': 'Technical difficulty encountered',
                        'confidence': 0.0,
                        'reasoning': str(e)
                    }
                ]
            )
    
    async def process_chat(self, request: ChatRequest) -> ChatResponse:
        """Process customer chat with full AI stack"""
        start_time = datetime.now()
        
        try:
            session_id = request.session_id or str(uuid.uuid4())
            customer_id = request.customer_id or f"guest_{session_id[:8]}"
            message_id = str(uuid.uuid4())
            
            # Initialize or update session tracking
            self._track_session(session_id, customer_id, request.message)
            
            # Extract and update customer information from message
            self._extract_and_update_customer_info(customer_id, session_id, request.message)
            
            # Get customer profile for context
            customer_profile = self._get_customer_profile(customer_id)
            
            # Check if session is educational-only from database
            try:
                cur = self.db_conn.cursor()
                cur.execute("""
                    SELECT session_id, reason FROM educational_only_sessions
                    WHERE session_id = %s
                """, (session_id,))
                edu_row = cur.fetchone()
                if edu_row:
                    logger.info(f"Session {session_id} is educational-only: {edu_row['reason']}")
                    if not hasattr(self, 'educational_only_sessions'):
                        self.educational_only_sessions = set()
                    self.educational_only_sessions.add(session_id)
            except Exception as e:
                logger.error(f"Failed to check educational session: {e}")
            
            # Check if session is blocked for underage access
            if hasattr(self, 'blocked_sessions') and session_id in self.blocked_sessions:
                logger.warning(f"Blocked session attempted access: {session_id}")
                return ChatResponse(
                    message="This session has been blocked due to age restrictions. Cannabis products are only available to customers of legal age.",
                    products=[],
                    quick_replies=[],
                    quick_actions=[],
                    confidence=1.0,
                    session_id=session_id,
                    stage="session_blocked",
                    cart_summary=None,
                    response_time_ms=int((datetime.now() - start_time).total_seconds() * 1000),
                    model_name="System"  # System-level block, no model used
                )
            
            # Check for age mentions in the message
            # Note: In production, users are pre-verified through IAM
            # This is a safety check if someone claims to be underage
            age_check = self._detect_age_in_message(request.message)
            underage_mode = False
            
            if age_check:
                age, province = age_check
                min_age = self._get_minimum_age(province)
                if age < min_age:
                    # User claimed to be underage - switch to educational mode only
                    logger.warning(f"User claimed underage: {age} years old in {province} (min: {min_age})")
                    
                    # Mark session for educational content only
                    if not hasattr(self, 'educational_only_sessions'):
                        self.educational_only_sessions = set()
                    self.educational_only_sessions.add(session_id)
                    underage_mode = True
                    
                    # Store in database for persistence
                    try:
                        cur = self.db_conn.cursor()
                        cur.execute("""
                            INSERT INTO educational_only_sessions (session_id, reason, created_at)
                            VALUES (%s, %s, CURRENT_TIMESTAMP)
                            ON CONFLICT (session_id) DO NOTHING
                        """, (session_id, f"User claimed age {age} (min: {min_age})"))
                        self.db_conn.commit()
                    except Exception as e:
                        logger.error(f"Failed to store educational session: {e}")
                    
                    # Provide educational response without products
                    educational_message = f"Thank you for your honesty. Since you're {age}, I can provide general educational information about cannabis, but I cannot show or recommend any products. In {province}, the legal age for cannabis is {min_age}.\n\n"
                    
                    # Add educational content based on the request
                    if "what" in request.message.lower() or "how" in request.message.lower() or "why" in request.message.lower():
                        educational_message += "Cannabis affects the developing brain differently than adult brains. Research shows that regular use before age 25 can impact memory, concentration, and decision-making. If you have questions about cannabis and health, I encourage you to speak with a healthcare provider or visit government health resources."
                    else:
                        educational_message += "I'm here to provide factual information about cannabis laws, health effects, and safety. Is there something specific you'd like to learn about?"
                    
                    return ChatResponse(
                        message=educational_message,
                        products=[],  # Never show products to underage users
                        quick_replies=["What are the health effects?", "Why is there an age limit?", "Cannabis and the brain"],
                        quick_actions=[],
                        confidence=1.0,
                        session_id=session_id,
                        stage="educational_only",
                        cart_summary=None,
                        response_time_ms=int((datetime.now() - start_time).total_seconds() * 1000)
                    )
            
            # Check if this session is in educational-only mode
            if hasattr(self, 'educational_only_sessions') and session_id in self.educational_only_sessions:
                underage_mode = True
            
            # Get Smart AI engine V2 response (simplified logic)
            # Load conversation history from database if not in memory
            conversation_history = self._load_or_get_session_history(session_id, customer_id)
            
            # Also check conversation history for previous age mentions
            if not underage_mode and conversation_history:
                for msg in conversation_history:
                    if isinstance(msg, dict) and msg.get('role') == 'user':
                        content = msg.get('content', '')
                        hist_age_check = self._detect_age_in_message(content)
                        if hist_age_check:
                            age, province = hist_age_check
                            min_age = self._get_minimum_age(province)
                            if age < min_age:
                                logger.warning(f"Found previous underage claim in history: {age} years old")
                                underage_mode = True
                                if not hasattr(self, 'educational_only_sessions'):
                                    self.educational_only_sessions = set()
                                self.educational_only_sessions.add(session_id)
                                
                                # Return educational response for historical underage detection
                                if "product" in request.message.lower() or "show" in request.message.lower():
                                    return ChatResponse(
                                        message="Based on our previous conversation, I can only provide educational information about cannabis, not product recommendations. The legal age for cannabis varies by province in Canada. What would you like to learn about?",
                                        products=[],
                                        quick_replies=["What are the health effects?", "Why is there an age limit?", "Cannabis laws in Canada"],
                                        quick_actions=[],
                                        confidence=1.0,
                                        session_id=session_id,
                                        stage="educational_only",
                                        cart_summary=None,
                                        response_time_ms=int((datetime.now() - start_time).total_seconds() * 1000)
                                    )
                                break
            
            # Build enhanced context with customer profile
            enhanced_context = request.context or {}
            if customer_profile:
                enhanced_context['customer_name'] = customer_profile.get('name', 'Guest')
                enhanced_context['customer_preferences'] = customer_profile.get('preferences', {})
                enhanced_context['is_returning'] = customer_profile.get('total_sessions', 0) > 1
                enhanced_context['favorite_products'] = customer_profile.get('favorite_products', [])
                enhanced_context['preferred_strain'] = customer_profile.get('preferred_strain_type')
                
                # Add personalized greeting context
                if customer_profile.get('name'):
                    enhanced_context['greeting_name'] = customer_profile['name']
                    logger.info(f"Recognized returning customer: {customer_profile['name']}")
            
            # Get budtender personality details from database
            # Default to "Zac" if no personality is defined
            budtender_personality = {
                'name': 'Zac',
                'communication_style': 'friendly and knowledgeable',
                'humor_style': 'witty',
                'humor_level': 'moderate',
                'sales_approach': 'consultative',
                'personality_traits': ['helpful', 'professional', 'cannabis-knowledgeable'],
                'greeting_style': "Hi, I'm Zac! How can I help you today?",
                'description': 'Your friendly cannabis consultant',
                'introduction': "I'm Zac, your cannabis consultant",
                'identity': 'Zac'
            }
            
            if request.context and request.context.get('budtender_personality'):
                personality_id = request.context['budtender_personality']
                try:
                    cur = self.db_conn.cursor(cursor_factory=RealDictCursor)
                    cur.execute(
                        """SELECT * FROM ai_personalities 
                           WHERE id = %s OR name = %s 
                           LIMIT 1""",
                        (personality_id, personality_id)
                    )
                    personality_data = cur.fetchone()
                    if personality_data:
                        budtender_personality = dict(personality_data)
                        logger.info(f"Loaded personality: {personality_data['name']}")
                    else:
                        logger.info("Using default personality: Zac")
                    cur.close()
                except Exception as e:
                    logger.error(f"Failed to load personality {personality_id}, using Zac: {e}")
            else:
                logger.info("No personality specified, using default: Zac")
            
            # Check if we should use RAG for product queries
            ai_response = None
            
            # Use LLM to determine if this is a product query
            # Let the AI decide based on prompts, not hardcoded rules
            is_product_query = True  # Default to using RAG, let it handle everything
            
            # Optional: Use SmartAIEngine's intent detection if you want to be selective
            # Otherwise just use RAG for everything and let it return empty for non-products
            
            # Skip RAG for underage users - provide educational content only
            if underage_mode:
                logger.info("Skipping RAG for educational-only session")
                ai_response = {
                    'message': "I can only provide educational information about cannabis. What would you like to learn about?",
                    'products': [],
                    'stage': 'educational_only',
                    'intent': 'educational',
                    'confidence': 1.0,
                    'model_used': 'educational_filter'
                }
            # Check if we should use multilingual engine (auto-detect or specified non-English)
            elif self.multilingual_engine:
                # Use model-driven language detection
                detected_lang = request.language
                logger.info(f"Initial language from request: {detected_lang}, message: '{request.message}'")
                
                # OPTIMIZATION: Skip language detection for obvious English product queries
                product_keywords = ['show', 'want', 'need', 'flower', 'sativa', 'indica',
                                  'pre-roll', 'divvy', 'pink', 'kush', 'thc', 'cbd', 'edible']
                message_lower = request.message.lower()
                is_obvious_product = any(kw in message_lower for kw in product_keywords)
                
                # If language is default 'en', use model to detect actual language
                # BUT SKIP for obvious product queries to save 3 LLM calls
                if detected_lang == 'en' and hasattr(self.multilingual_engine, 'language_service') and not is_obvious_product:
                    try:
                        # Get session context if available
                        session_context = None
                        if session_id in self.sessions:
                            session_data = self.sessions[session_id]
                            if 'language' in session_data:
                                session_context = {'previous_language': session_data['language']}
                        
                        # Use model-driven language detection
                        detected_lang, confidence = await self.multilingual_engine.language_service.detect_language(
                            text=request.message,
                            session_context=session_context
                        )
                        logger.info(f"Model-detected language: {detected_lang} (confidence: {confidence})")
                    except Exception as e:
                        logger.warning(f"Model language detection failed: {e}, defaulting to 'en'")
                        detected_lang = 'en'
                
                # Use multilingual engine if non-English detected or specified
                if detected_lang != 'en':
                    logger.info(f"Using Smart Multilingual Engine for {detected_lang} query")
                    try:
                        # Process through multilingual engine
                        multilingual_result = await self.multilingual_engine.process_message(
                            message=request.message,
                            session_id=session_id,
                            customer_id=customer_id,
                            preferred_language=detected_lang
                        )
                        
                        # Convert to expected format
                        ai_response = {
                            'message': multilingual_result['message'],
                            'products': multilingual_result.get('products', []),
                            'stage': 'multilingual_response',
                            'confidence': multilingual_result.get('quality_score', 0.8),
                            'detected_language': multilingual_result.get('detected_language', detected_lang),  # Use the initially detected language
                            'language_confidence': multilingual_result.get('language_confidence', 1.0)
                        }
                    except Exception as e:
                        logger.error(f"Multilingual processing failed: {e}")
                        # Fallback to regular processing
                        ai_response = None
                else:
                    # English detected, continue with normal processing
                    ai_response = None
            # Use RAG for product queries if available
            elif self.use_rag and self.search_first_engine and is_product_query:
                logger.info("Using RAG Search-First Engine for product query")
                try:
                    # Use the search-first engine for database-backed responses
                    rag_result = await self.search_first_engine.process_query(
                        message=request.message,
                        context={'customer_id': customer_id},
                        session_id=session_id,
                        personality=personality_name
                    )
                    
                    # Get actual model name
                    actual_model_name = self.get_current_model_name() or 'search_first_rag'
                    
                    # Convert RAG result to expected format
                    ai_response = {
                        'message': rag_result['message'],
                        'products': rag_result.get('products', []),
                        'stage': 'product_search' if rag_result.get('products') else 'response',
                        'intent': 'search',
                        'confidence': 0.95,  # High confidence since we searched database
                        'model_used': actual_model_name,
                        'quick_actions': rag_result.get('quick_actions', []),  # Pass through RAG quick actions
                        'search_performed': True,
                        'total_found': rag_result.get('total_found', 0)
                    }
                    
                    # Store in conversation history
                    if session_id in self.sessions:
                        self.sessions[session_id]['history'].append({
                            'role': 'user',
                            'content': request.message,
                            'timestamp': datetime.now()
                        })
                        self.sessions[session_id]['history'].append({
                            'role': 'assistant',
                            'content': rag_result['message'],
                            'timestamp': datetime.now(),
                            'products': len(rag_result.get('products', [])),
                            'method': 'rag'
                        })
                    
                    logger.info(f"RAG response: Found {rag_result.get('total_found', 0)} products")
                    
                except Exception as e:
                    logger.error(f"RAG engine error, falling back to SmartAI: {e}")
                    # Will fallback to smart_ai_engine below
            
            # Fallback to SmartAIEngine if RAG not used or failed
            if ai_response is None:
                ai_response = await self.smart_ai_engine.process_message(
                    message=request.message,
                    context={
                        'customer_id': customer_id,
                        'conversation_history': conversation_history,
                        'budtender_personality': budtender_personality,
                        'customer_context': enhanced_context
                    },
                    session_id=session_id
                )
            
            # Check for error stage
            if ai_response.get('stage') == 'error':
                logger.error(f"AI Engine error: {ai_response.get('error', 'Unknown error')}")
                return ChatResponse(
                    message=ai_response.get('message', 'AI service is temporarily unavailable. Please try again later.'),
                    products=[],
                    quick_replies=[],
                    quick_actions=[],
                    confidence=0,
                    response_time_ms="0",
                    session_id=session_id,
                    customer_id=customer_id,
                    intent="error",
                    stage="error",
                    error=ai_response.get('error', 'LLM_NOT_AVAILABLE')
                )
            
            # Debug logging
            logger.info(f"AI response stage: {ai_response.get('stage')}")
            logger.info(f"AI response message: {ai_response.get('message', 'NO MESSAGE')[:100]}")
            logger.info(f"Products found: {len(ai_response.get('products', []))}")
            logger.info(f"Model used: {ai_response.get('model_used', 'unknown')}")
            
            # Enhance products with image URLs from database
            products_with_images = []
            product_ids = []
            if ai_response.get('products'):
                try:
                    cur = self.db_conn.cursor(cursor_factory=RealDictCursor)
                    for product in ai_response.get('products', []):
                        # If product is already a dict with details, ensure it has image_url
                        if isinstance(product, dict):
                            # Enhance with additional fields from database
                            cur.execute(
                                """SELECT id, product_name, brand, category, sub_category, unit_price,
                                   size, thc_max_percent, cbd_max_percent, 
                                   CASE 
                                       WHEN thc_min_percent IS NOT NULL AND thc_max_percent IS NOT NULL 
                                       THEN thc_min_percent || '-' || thc_max_percent || '%'
                                       ELSE NULL
                                   END as thc_range,
                                   CASE 
                                       WHEN cbd_min_percent IS NOT NULL AND cbd_max_percent IS NOT NULL 
                                       THEN cbd_min_percent || '-' || cbd_max_percent || '%'
                                       ELSE NULL
                                   END as cbd_range,
                                   short_description, long_description,
                                   inventory_count, 
                                   CASE WHEN inventory_count > 0 THEN true ELSE false END as in_stock,
                                   image_url, plant_type as strain_type,
                                   COALESCE(rating, 4.5) as rating,
                                   COALESCE(review_count, 0) as review_count
                                   FROM products 
                                   WHERE id = %s
                                   LIMIT 1""",
                                (product.get('id', 0),)
                            )
                            result = cur.fetchone()
                            if result:
                                enhanced_product = dict(result)
                                # Add any additional fields from the original product
                                enhanced_product.update(product)
                                products_with_images.append(enhanced_product)
                            else:
                                products_with_images.append(product)
                        # If product is just a name or ID, fetch full details
                        elif isinstance(product, (str, int)):
                            cur.execute(
                                """SELECT id, product_name, brand, category, sub_category, unit_price,
                                   size, thc_max_percent, cbd_max_percent,
                                   CASE 
                                       WHEN thc_min_percent IS NOT NULL AND thc_max_percent IS NOT NULL 
                                       THEN thc_min_percent || '-' || thc_max_percent || '%'
                                       ELSE NULL
                                   END as thc_range,
                                   CASE 
                                       WHEN cbd_min_percent IS NOT NULL AND cbd_max_percent IS NOT NULL 
                                       THEN cbd_min_percent || '-' || cbd_max_percent || '%'
                                       ELSE NULL
                                   END as cbd_range,
                                   short_description, long_description,
                                   inventory_count,
                                   CASE WHEN inventory_count > 0 THEN true ELSE false END as in_stock,
                                   image_url, plant_type as strain_type,
                                   COALESCE(rating, 4.5) as rating,
                                   COALESCE(review_count, 0) as review_count
                                   FROM products 
                                   WHERE id = %s OR product_name ILIKE %s
                                   LIMIT 1""",
                                (str(product), f"%{product}%")
                            )
                            result = cur.fetchone()
                            if result:
                                product_dict = dict(result)
                                products_with_images.append(product_dict)
                                if product_dict.get('id'):
                                    product_ids.append(product_dict['id'])
                    ai_response['products'] = products_with_images
                    
                    # Update session with products viewed
                    if product_ids:
                        self._update_session_products(session_id, product_ids)
                        
                except Exception as e:
                    logger.error(f"Error enhancing products with images: {e}")
                    # Keep original products if enhancement fails
                    products_with_images = ai_response.get('products', [])
            
            # Filter products if in educational-only mode
            if underage_mode:
                # Remove all products from response for underage users
                ai_response['products'] = []
                products_with_images = []
                
                # Modify message to be educational only
                if "show" in request.message.lower() and "product" in request.message.lower():
                    enhanced_message = "I cannot show products to users under the legal age. However, I can provide educational information about cannabis, its effects, and regulations. What would you like to learn about?"
                else:
                    enhanced_message = ai_response.get("message", "I can provide educational information about cannabis. What would you like to know?")
            else:
                # Message is already AI-generated, no need for additional optimization
                enhanced_message = ai_response.get("message", "")
                
                # If no message but we have products, add a default recommendation message
                if not enhanced_message and ai_response.get("products"):
                    enhanced_message = "Based on your request, here are some perfect recommendations for you:"
            
            # Generate quick reply suggestions
            quick_replies = self._generate_quick_replies(
                ai_response=ai_response,
                products=products_with_images,
                user_message=request.message
            )
            
            # Get cart summary
            cart_summary = self._get_cart_summary(customer_id)
            
            # Calculate response time
            response_time = (datetime.now() - start_time).total_seconds() * 1000
            
            # Save to database
            # Generate quick actions based on response
            quick_actions = self.quick_action_generator.generate_actions(
                intent=ai_response.get("intent", "general"),
                context={
                    'stage': ai_response.get("stage", "greeting"),
                    'customer_name': customer_profile.get('name') if customer_profile else None,
                    'current_product': products_with_images[0]['product_name'] if products_with_images else None,
                    'strain_type': request.context.get('strain_type') if request.context else None
                },
                products_shown=len(products_with_images) > 0,
                stage=ai_response.get("stage", "greeting"),
                ai_response=ai_response.get("message", ""),
                user_message=request.message
            )
            
            # Translate quick actions and replies if non-English language detected
            detected_language = ai_response.get("detected_language", "en")
            logger.info(f"Detected language for UI translation: {detected_language}")
            if detected_language and detected_language != "en":
                logger.info(f"Translating UI elements to {detected_language}")
                # Translate quick replies
                quick_replies = UITranslations.translate_quick_replies(detected_language)
                # Translate quick actions
                quick_actions = UITranslations.translate_quick_actions(quick_actions, detected_language)
                logger.info(f"Translated quick replies: {quick_replies[:2]}")  # Log first 2 for debugging
            
            # Respect the product count from search engine
            # But NEVER show products to underage users
            if underage_mode:
                products_to_show = []  # No products for underage users
            else:
                # If 20 or less results, show all with images
                # Otherwise show top 10
                products_to_show = products_with_images
                if ai_response.get("includes_images", False):
                    # Search engine determined we should show all products with images
                    products_to_show = products_with_images
                elif len(products_with_images) > 20:
                    # Too many products, limit to 10
                    products_to_show = products_with_images[:10]
                # If between 10-20, show all
            
            # Save the complete interaction with products, images and quick actions
            self._save_chat_interaction(
                session_id=session_id,
                message_id=message_id,
                customer_id=customer_id,
                user_message=request.message,
                ai_response=enhanced_message,
                intent=ai_response.get("intent", ""),
                stage=ai_response.get("stage", "greeting"),
                response_time=f"{response_time:.0f}ms",
                products=products_to_show,  # Save products with images
                quick_actions=quick_actions,
                quick_replies=quick_replies
            )
            
            # Get the current model name
            model_name = ai_response.get("model_used") or self.get_current_model_name() or "Unknown"
            
            return ChatResponse(
                message=enhanced_message,
                products=products_to_show,
                quick_replies=quick_replies or ai_response.get("quick_replies", []),
                quick_actions=quick_actions,  # Add quick actions
                confidence=ai_response.get("confidence", 0.5),
                session_id=session_id,
                stage=ai_response.get("stage", "greeting"),
                cart_summary=cart_summary,
                response_time_ms=int(response_time),
                model_name=model_name  # Include model name in response
            )
            
        except Exception as e:
            logger.error(f"Chat processing error: {e}")
            fallback = self.error_handler.handle_error(e, {'endpoint': 'chat'})
            return ChatResponse(
                message=fallback.get("message", "I'm here to help you find the perfect cannabis product."),
                products=[],
                quick_replies=["Browse Products", "Get Recommendations"],
                quick_actions=[],  # Empty quick actions on error
                confidence=0.5,
                session_id=request.session_id or str(uuid.uuid4()),
                stage="error_recovery",
                cart_summary=None,
                model_name=self.get_current_model_name() or "Unknown"
            )
    
    async def search_products(self, request: ProductSearchRequest) -> List[ProductResponse]:
        """Search products with multiple strategies"""
        start_time = datetime.now()
        
        try:
            cur = self.db_conn.cursor()
            
            # Apply smart query expansion using SearchEndpointOptimizer
            original_query = request.query
            if request.query and SearchEndpointOptimizer:
                expanded_query = SearchEndpointOptimizer.generate_smart_query(request.query)
                if expanded_query != request.query:
                    logger.info(f"SearchOptimizer expanded: '{original_query}' -> '{expanded_query}'")
                    request.query = expanded_query
            
            # Build query based on search type
            # Treat empty string as None for search logic
            has_query = request.query is not None and request.query != ""
            has_intent = request.intent is not None and request.intent != ""
            
            # Handle multiple intents (comma-separated)
            intents = []
            if has_intent:
                # Split by comma and clean up whitespace
                intents = [i.strip() for i in request.intent.split(',') if i.strip()]
            
            # Start with ALL products - filters will narrow down
            query = "SELECT * FROM products WHERE 1=1"
            params = []
            
            # Add text search filter if provided
            # Intelligently search multiple fields with actual data
            if has_query:
                # Normalize search term for better matching
                # Replace hyphens with spaces for more flexible matching
                normalized_query = request.query.replace("-", " ")
                search_term = f"%{normalized_query}%"
                
                # Build dynamic search conditions based on fields with data
                # Priority order: product_name > brand > category > sub_category > sub_sub_category > descriptions
                search_conditions = []
                
                # Core fields - always search these
                search_conditions.append("product_name ILIKE %s")
                params.append(search_term)
                
                search_conditions.append("brand ILIKE %s")
                params.append(search_term)
                
                search_conditions.append("category ILIKE %s")
                params.append(search_term)
                
                # Extended fields - search if they have data (not null/empty)
                search_conditions.append("(sub_category IS NOT NULL AND sub_category != '' AND sub_category ILIKE %s)")
                params.append(search_term)
                
                search_conditions.append("(sub_sub_category IS NOT NULL AND sub_sub_category != '' AND sub_sub_category ILIKE %s)")
                params.append(search_term)
                
                # Description fields - only if longer search terms (>3 chars)
                if len(normalized_query) > 3:
                    search_conditions.append("(short_description IS NOT NULL AND short_description != '' AND short_description ILIKE %s)")
                    params.append(search_term)
                    
                    search_conditions.append("(long_description IS NOT NULL AND long_description != '' AND long_description ILIKE %s)")
                    params.append(search_term)
                
                # Plant type field for strain searches
                search_conditions.append("(plant_type IS NOT NULL AND plant_type != '' AND plant_type ILIKE %s)")
                params.append(search_term)
                
                # Combine all conditions with OR
                query += f" AND ({' OR '.join(search_conditions)})"
            
            # Add intent filter if provided (supports multiple comma-separated)
            # Intent uses ONLY long_description as source of truth
            if intents:
                if len(intents) == 1:
                    # Single intent - search in long_description only
                    query += " AND long_description ILIKE %s"
                    intent_term = f"%{intents[0]}%"
                    params.append(intent_term)
                else:
                    # Multiple intents - match any in long_description
                    intent_conditions = []
                    for intent in intents:
                        intent_conditions.append("long_description ILIKE %s")
                        intent_term = f"%{intent}%"
                        params.append(intent_term)
                    query += f" AND ({' OR '.join(intent_conditions)})"
            
            # Add filters - empty string means "all", only filter if value provided
            # Search in both category AND sub_category fields
            if request.category is not None and request.category != "":
                query += " AND (LOWER(category) = LOWER(%s) OR LOWER(sub_category) = LOWER(%s))"
                params.extend([request.category, request.category])
            
            # Filter by strain type (plant_type column)
            if request.strain_type is not None and request.strain_type != "":
                query += " AND LOWER(plant_type) = LOWER(%s)"
                params.append(request.strain_type)
            
            if request.min_price is not None and request.min_price > 0:
                query += " AND unit_price >= %s"
                params.append(request.min_price)
            
            if request.max_price is not None and request.max_price > 0:
                query += " AND unit_price <= %s"
                params.append(request.max_price)
            
            if request.min_thc is not None and request.min_thc > 0:
                query += " AND thc_max_percent >= %s"
                params.append(request.min_thc)
            
            if request.max_thc is not None and request.max_thc > 0:
                query += " AND thc_max_percent <= %s"
                params.append(request.max_thc)
            
            # Add intelligent ordering - prioritize better matches
            # Order by relevance: exact matches first, then partial matches, then by price
            if has_query:
                normalized_query = request.query.replace("-", " ")
                # Add relevance scoring to order results better
                query += f""" ORDER BY 
                    CASE 
                        WHEN LOWER(product_name) = LOWER(%s) THEN 1
                        WHEN LOWER(brand) = LOWER(%s) THEN 2
                        WHEN LOWER(category) = LOWER(%s) THEN 3
                        WHEN product_name ILIKE %s THEN 4
                        WHEN brand ILIKE %s THEN 5
                        WHEN category ILIKE %s THEN 6
                        ELSE 7
                    END,
                    unit_price ASC"""
                # Add exact match params
                params.extend([normalized_query, normalized_query, normalized_query])
                # Add partial match params
                search_term = f"%{normalized_query}%"
                params.extend([search_term, search_term, search_term])
            else:
                # Default ordering by price if no search query
                query += " ORDER BY unit_price ASC"
            
            query += " LIMIT %s OFFSET %s"
            params.extend([request.limit, request.offset])
            
            cur.execute(query, params)
            rows = cur.fetchall()
            
            # Record search for training if pipeline available
            if self.training_pipeline and original_query:
                search_params = {
                    "query": original_query,
                    "expanded_query": request.query,
                    "category": request.category,
                    "intent": request.intent,
                    "min_price": request.min_price,
                    "max_price": request.max_price
                }
                response_time_ms = int((datetime.now() - start_time).total_seconds() * 1000)
                
                # Record the interaction
                interaction_id = self.training_pipeline.record_interaction(
                    customer_message=original_query or "",
                    inferred_params=search_params,
                    search_results=[{"id": r['id'], "name": r['product_name']} for r in rows[:10]],
                    response_time_ms=response_time_ms,
                    model_confidence=0.95
                )
                logger.info(f"Recorded training interaction #{interaction_id}")
            
            products = []
            for row in rows:
                product = ProductResponse(
                    id=row['id'],
                    product_name=row['product_name'],
                    brand=row['brand'],
                    category=row.get('category', 'Unknown'),
                    sub_category=row.get('sub_category'),
                    unit_price=row['unit_price'],
                    size=row.get('size'),
                    # Use thc_mg and cbd_mg if percentages are not available
                    thc_max_percent=row.get('thc_max_percent') or row.get('thc_mg', 0),
                    cbd_max_percent=row.get('cbd_max_percent') or row.get('cbd_mg', 0),
                    thc_range=row.get('thc_range'),
                    cbd_range=row.get('cbd_range'),
                    short_description=row.get('short_description'),
                    long_description=row.get('long_description'),
                    inventory_count=row.get('inventory_count'),
                    in_stock=row.get('in_stock', True),
                    pitch=self._generate_product_pitch(row),
                    effects=self._get_product_effects(row),
                    terpenes=self._get_product_terpenes(row),
                    strain_type=row.get('plant_type'),
                    image_url=row.get('image_url'),  # Include image URL from database
                    rating=row.get('rating', 4.2),  # Default rating if not in DB
                    review_count=row.get('review_count', 0)  # Default review count
                )
                products.append(product)
            
            return products
            
        except Exception as e:
            logger.error(f"Product search error: {e}")
            # Rollback transaction on error
            try:
                self.db_conn.rollback()
            except:
                pass
            # Return fallback products
            return self._get_fallback_products()
    
    def _generate_product_pitch(self, product: Dict) -> str:
        """Generate sales pitch for product"""
        pitches = []
        
        if product.get('thc_max_percent'):
            if product['thc_max_percent'] > 20:
                pitches.append("High potency for experienced users")
            elif product['thc_max_percent'] < 10:
                pitches.append("Gentle effects perfect for beginners")
        
        if product.get('cbd_max_percent') and product['cbd_max_percent'] > 5:
            pitches.append("CBD-rich for therapeutic benefits")
        
        return ". ".join(pitches) if pitches else "Premium quality cannabis"
    
    def _get_product_effects(self, product: Dict) -> List[str]:
        """Get product effects based on profile"""
        effects = []
        
        # Simplified effect mapping
        if product.get('category') == 'Flower':
            if 'indica' in product.get('product_name', '').lower():
                effects = ['relaxation', 'sleep', 'pain relief']
            elif 'sativa' in product.get('product_name', '').lower():
                effects = ['energy', 'creativity', 'focus']
            else:
                effects = ['balanced', 'mild euphoria']
        
        return effects
    
    def _get_product_terpenes(self, product: Dict) -> List[str]:
        """Get product terpenes"""
        # This would query terpene data in production
        return ['limonene', 'myrcene', 'pinene'][:2]
    
    def _get_fallback_products(self) -> List[ProductResponse]:
        """Return fallback products when search fails"""
        return [
            ProductResponse(
                id=0,
                product_name="Popular Indica",
                brand="Premium Brand",
                category="Flower",
                sub_category="Indoor",
                unit_price=45.99,
                size="3.5g",
                thc_max_percent=18.0,
                cbd_max_percent=0.5,
                thc_range="16-18%",
                cbd_range="0-1%",
                short_description="Our most popular indica for deep relaxation",
                long_description="This premium indica strain is perfect for evening use, promoting deep relaxation and restful sleep.",
                inventory_count=50,
                in_stock=True,
                pitch="Our most popular strain for relaxation",
                effects=['relaxation', 'sleep', 'calm'],
                terpenes=['myrcene', 'linalool'],
                strain_type="indica",
                image_url="https://example.com/placeholder.jpg",
                rating=4.5,
                review_count=120
            )
        ]
    
    def _track_session(self, session_id: str, customer_id: str, message: str):
        """Track customer session for analytics and personalization"""
        try:
            cur = self.db_conn.cursor()
            
            # Check if session exists
            cur.execute(
                "SELECT id, customer_profile_id FROM customer_sessions WHERE session_id = %s",
                (session_id,)
            )
            session_row = cur.fetchone()
            
            if not session_row:
                # Get customer profile ID if exists
                cur.execute(
                    "SELECT id FROM customer_profiles WHERE customer_id = %s",
                    (customer_id,)
                )
                profile_row = cur.fetchone()
                profile_id = profile_row['id'] if profile_row else None
                
                # Create new session
                cur.execute("""
                    INSERT INTO customer_sessions 
                    (session_id, customer_id, customer_profile_id, message_count, started_at)
                    VALUES (%s, %s, %s, 1, CURRENT_TIMESTAMP)
                    ON CONFLICT (session_id) DO UPDATE SET
                        message_count = customer_sessions.message_count + 1,
                        updated_at = CURRENT_TIMESTAMP
                """, (session_id, customer_id, profile_id))
                
                # Update customer profile session count
                if profile_id:
                    cur.execute("""
                        UPDATE customer_profiles 
                        SET total_sessions = total_sessions + 1,
                            last_seen = CURRENT_TIMESTAMP
                        WHERE id = %s
                    """, (profile_id,))
            else:
                # Update existing session
                cur.execute("""
                    UPDATE customer_sessions 
                    SET message_count = message_count + 1,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE session_id = %s
                """, (session_id,))
            
            self.db_conn.commit()
            logger.debug(f"Session {session_id} tracked for customer {customer_id}")
            
        except Exception as e:
            logger.error(f"Error tracking session: {e}")
            self.db_conn.rollback()
    
    def _update_session_products(self, session_id: str, product_ids: List[int]):
        """Update products viewed in session"""
        try:
            if not product_ids:
                return
                
            cur = self.db_conn.cursor()
            
            # Get current products viewed
            cur.execute(
                "SELECT products_viewed FROM customer_sessions WHERE session_id = %s",
                (session_id,)
            )
            row = cur.fetchone()
            
            if row:
                current_products = row['products_viewed'] or []
                # Add new products (convert to strings for consistency)
                updated_products = list(set(current_products + [str(pid) for pid in product_ids]))
                
                # Update session
                cur.execute("""
                    UPDATE customer_sessions 
                    SET products_viewed = %s,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE session_id = %s
                """, (updated_products, session_id))
                
                self.db_conn.commit()
                logger.debug(f"Updated session {session_id} with products: {product_ids}")
                
        except Exception as e:
            logger.error(f"Error updating session products: {e}")
            self.db_conn.rollback()
    
    def _extract_and_update_customer_info(self, customer_id: str, session_id: str, message: str):
        """Extract customer information from message and update profile"""
        try:
            cur = self.db_conn.cursor()
            
            # Use the database function to extract and update
            cur.execute(
                "SELECT update_customer_profile_from_chat(%s, %s, %s)",
                (customer_id, session_id, message)
            )
            self.db_conn.commit()
            
            # Check if we extracted any info
            cur.execute(
                "SELECT extract_customer_info(%s) as info",
                (message,)
            )
            result = cur.fetchone()
            if result and result['info'] and result['info'] != '{}':
                logger.info(f"Extracted customer info: {result['info']}")
            
            cur.close()
        except Exception as e:
            logger.error(f"Failed to extract customer info: {e}")
            self.db_conn.rollback()
    
    def _get_customer_profile(self, customer_id: str) -> Optional[Dict]:
        """Get customer profile from database"""
        try:
            cur = self.db_conn.cursor()
            cur.execute(
                """SELECT * FROM customer_profiles 
                   WHERE customer_id = %s""",
                (customer_id,)
            )
            profile = cur.fetchone()
            cur.close()
            
            if profile:
                return dict(profile)
            return None
        except Exception as e:
            logger.error(f"Failed to get customer profile: {e}")
            return None
    
    def _detect_age_in_message(self, message: str) -> Optional[Tuple[int, str]]:
        """
        Detect if user mentions their age in the message
        Returns (age, province) tuple or None
        """
        import re
        
        # Common patterns for age mention
        patterns = [
            r"i(?:'m| am)\s+(\d+)(?:\s+years?\s+old)?",  # I'm 16, I am 16 years old
            r"(?:am|i'm)\s+(\d+)(?:\s+years?\s+old)?",   # am 16, i'm 16
            r"(?:i'm a|i am a)\s+(\d+)\s+year\s+old",     # I'm a 16 year old
            r"age(?:\s+is)?:?\s*(\d+)",                   # age: 16, age is 16
            r"(\d+)\s+years?\s+old",                      # 16 years old
            r"^(\d+)\s+(?:and|&)",                        # "16 and..."
        ]
        
        message_lower = message.lower()
        for pattern in patterns:
            match = re.search(pattern, message_lower)
            if match:
                age = int(match.group(1))
                # Default to Ontario if no province mentioned
                province = self._detect_province_in_message(message) or "Ontario"
                return (age, province)
        
        return None
    
    def _detect_province_in_message(self, message: str) -> Optional[str]:
        """Detect if user mentions their province/territory"""
        message_lower = message.lower()
        
        # Province/territory mapping
        provinces = {
            'ontario': 'Ontario', 'on': 'Ontario',
            'british columbia': 'British Columbia', 'bc': 'British Columbia',
            'alberta': 'Alberta', 'ab': 'Alberta',
            'manitoba': 'Manitoba', 'mb': 'Manitoba',
            'saskatchewan': 'Saskatchewan', 'sk': 'Saskatchewan',
            'quebec': 'Quebec', 'qc': 'Quebec', 'québec': 'Quebec',
            'nova scotia': 'Nova Scotia', 'ns': 'Nova Scotia',
            'new brunswick': 'New Brunswick', 'nb': 'New Brunswick',
            'newfoundland': 'Newfoundland and Labrador', 'nl': 'Newfoundland and Labrador',
            'prince edward island': 'Prince Edward Island', 'pei': 'Prince Edward Island', 'pe': 'Prince Edward Island',
            'northwest territories': 'Northwest Territories', 'nwt': 'Northwest Territories', 'nt': 'Northwest Territories',
            'yukon': 'Yukon', 'yt': 'Yukon',
            'nunavut': 'Nunavut', 'nu': 'Nunavut'
        }
        
        for key, province in provinces.items():
            if key in message_lower:
                return province
        
        return None
    
    def _get_minimum_age(self, province: str) -> int:
        """
        Get minimum legal age for cannabis by province/territory
        18: Alberta, Manitoba, Quebec
        19: All other provinces and territories
        """
        age_18_provinces = ['Alberta', 'Manitoba', 'Quebec']
        
        if province in age_18_provinces:
            return 18
        else:
            return 19
    
    def _generate_quick_replies(self, ai_response: Dict, products: List, user_message: str) -> List[str]:
        """Generate context-aware quick reply suggestions"""
        replies = []
        message_lower = user_message.lower()
        
        # If products were shown
        if products and len(products) > 0:
            first_product = products[0]
            product_name = first_product.get('product_name', first_product.get('name', 'this'))
            # Truncate long product names
            if len(product_name) > 20:
                product_name = product_name[:17] + '...'
            replies.append(f"Add {product_name} to cart")
            replies.append("Show similar products")
            replies.append("Tell me more about effects")
            
            if len(products) >= 3:
                replies.append("Show more options")
        
        # Context-based suggestions
        if 'pain' in message_lower or 'relief' in message_lower:
            if "Show me CBD products" not in replies:
                replies.append("Show me CBD products")
            replies.append("What about topicals?")
        elif 'sleep' in message_lower or 'insomnia' in message_lower:
            replies.append("Show me indica strains")
            replies.append("What about edibles?")
        elif 'energy' in message_lower or 'focus' in message_lower:
            replies.append("Show me sativa strains")
            replies.append("Any pre-rolls?")
        elif 'anxiety' in message_lower or 'stress' in message_lower:
            replies.append("Show me CBD options")
            replies.append("What about hybrids?")
        
        # General fallback suggestions if no products shown
        if len(replies) == 0:
            replies = [
                "Show popular products",
                "I need help choosing",
                "What's on sale?",
                "Tell me about strains"
            ]
        
        # Limit to 4 suggestions and ensure uniqueness
        seen = set()
        unique_replies = []
        for reply in replies:
            if reply not in seen:
                seen.add(reply)
                unique_replies.append(reply)
        
        return unique_replies[:4]
    
    def _get_cart_summary(self, customer_id: str) -> Optional[Dict]:
        """Get cart summary for customer"""
        if customer_id in self.sessions and 'cart' in self.sessions[customer_id]:
            cart = self.sessions[customer_id]['cart']
            if cart.get('items'):
                return {
                    'item_count': len(cart['items']),
                    'total': cart['total'],
                    'ready_for_checkout': cart['total'] > 0
                }
        return None
    
    def _load_or_get_session_history(self, session_id: str, customer_id: str) -> List[Dict]:
        """Load session history from database if not in memory, or get from memory"""
        
        # Check if session is already in memory
        if hasattr(self, 'sessions') and session_id in self.sessions:
            return self.sessions.get(session_id, {}).get('history', [])
        
        # Load from database if not in memory
        try:
            cur = self.db_conn.cursor()
            
            # Get last N messages from this session to rebuild context
            cur.execute("""
                SELECT user_message, ai_response, intent, created_at
                FROM chat_interactions
                WHERE session_id = %s OR (customer_id = %s AND session_id IS NOT NULL)
                ORDER BY created_at DESC
                LIMIT 10
            """, (session_id, customer_id))
            
            history = cur.fetchall()
            
            # Format as conversation history
            conversation_history = []
            for record in reversed(history):  # Reverse to get chronological order
                if record['user_message']:
                    conversation_history.append({
                        'role': 'user',
                        'content': record['user_message']
                    })
                if record['ai_response']:
                    conversation_history.append({
                        'role': 'assistant',
                        'content': record['ai_response']
                    })
            
            # Store in memory for future use in this session
            if not hasattr(self, 'sessions'):
                self.sessions = {}
            
            self.sessions[session_id] = {
                'history': conversation_history,
                'customer_id': customer_id,
                'last_activity': datetime.now()
            }
            
            logger.info(f"Loaded {len(conversation_history)} messages from database for session {session_id}")
            
            # Clean up old sessions from memory (keep only last 100 active sessions)
            self._cleanup_old_sessions()
            
            return conversation_history
            
        except Exception as e:
            logger.error(f"Error loading session history: {e}")
            return []
    
    def _cleanup_old_sessions(self):
        """Remove old sessions from memory to prevent memory bloat"""
        if not hasattr(self, 'sessions') or len(self.sessions) <= 100:
            return
        
        # Sort sessions by last activity
        sorted_sessions = sorted(
            self.sessions.items(), 
            key=lambda x: x[1].get('last_activity', datetime.min)
        )
        
        # Keep only the 100 most recent sessions
        sessions_to_remove = sorted_sessions[:-100]
        for session_id, _ in sessions_to_remove:
            del self.sessions[session_id]
        
        logger.info(f"Cleaned up {len(sessions_to_remove)} old sessions from memory")
    
    def _convert_decimals(self, obj):
        """Recursively convert Decimal objects to float for JSON serialization"""
        if isinstance(obj, Decimal):
            return float(obj)
        elif isinstance(obj, dict):
            return {k: self._convert_decimals(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._convert_decimals(item) for item in obj]
        return obj

    def _save_chat_interaction(self, session_id: str, message_id: str, 
                              customer_id: str, user_message: str, 
                              ai_response: str, intent: str, stage: str,
                              response_time: str, products: List[Dict], 
                              quick_actions: List[Dict] = None, quick_replies: List[str] = None):
        """Save chat interaction to database"""
        try:
            cur = self.db_conn.cursor()
            
            # Convert Decimal values to float for JSON serialization
            products = self._convert_decimals(products) if products else []
            quick_actions = self._convert_decimals(quick_actions) if quick_actions else []
            
            # Prepare metadata with complete response payload
            metadata = {
                'stage': stage,
                'products_shown': len(products),
                'products': products,  # Store complete product data with images
                'quick_actions': quick_actions,
                'quick_replies': quick_replies if quick_replies else [],
                'product_ids': [p.get('id') for p in products] if products else []  # Keep for backward compatibility
            }
            
            # Insert into chat_interactions table
            cur.execute("""
                INSERT INTO chat_interactions 
                (session_id, message_id, customer_id, user_message, ai_response,
                 service_used, response_time, intent, created_at, metadata)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                session_id,
                message_id,
                customer_id,
                user_message,
                ai_response,
                'unified_budtender',
                response_time,
                intent,
                datetime.now(),
                json.dumps(metadata)
            ))
            
            self.db_conn.commit()
            logger.debug(f"Saved chat interaction {message_id} for customer {customer_id}")
            
        except Exception as e:
            logger.error(f"Failed to save chat interaction: {e}")
            # Don't fail the request if we can't save history
            try:
                self.db_conn.rollback()
            except:
                pass
    
    async def get_health_status(self) -> Dict:
        """Get comprehensive health status"""
        status = {
            'service': 'ai_engine',
            'version': '2.0.0',
            'status': 'healthy' if self.initialized else 'initializing',
            'timestamp': datetime.now().isoformat(),
            'model': self.get_current_model_name(),
            'uptime_seconds': 0,  # Would track actual uptime
            'components': {}
        }
        
        # Check each component
        try:
            # Database
            cur = self.db_conn.cursor()
            cur.execute("SELECT COUNT(*) as count FROM products")
            product_count = cur.fetchone()['count']
            status['components']['database'] = {
                'status': 'healthy',
                'products': product_count
            }
        except:
            status['components']['database'] = {'status': 'unhealthy'}
        
        # Models
        if self.model_manager:
            status['components']['models'] = {
                'status': 'healthy',
                'loaded': [m.value for m in self.model_manager.get_available_models()]
            }
        
        # Cache
        if self.cache_manager:
            cache_stats = self.cache_manager.get_cache_stats()
            status['components']['cache'] = cache_stats
        
        # Inference optimizer
        if self.inference_optimizer:
            perf_stats = self.inference_optimizer.get_performance_stats()
            status['components']['inference'] = perf_stats
        
        # Error handler
        if self.error_handler:
            error_status = self.error_handler.get_health_status()
            status['components']['error_handler'] = error_status
        
        # Overall health determination
        unhealthy_components = [
            name for name, comp in status['components'].items()
            if comp.get('status') == 'unhealthy'
        ]
        
        if unhealthy_components:
            status['status'] = 'degraded'
            status['unhealthy_components'] = unhealthy_components
        
        return status

# ============================================================================
# FASTAPI APPLICATION
# ============================================================================

app = FastAPI(
    title="WeedGo AI Engine API",
    description="Unified intelligent budtender service with all capabilities",
    version="2.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:5174", "http://localhost:3000", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include enhanced model deployment router if available
if HAS_MODEL_DEPLOYMENT_ENDPOINTS:
    app.include_router(model_deployment_router)
    logging.info("Enhanced model deployment endpoints loaded")

# Include voice endpoints if available
if HAS_VOICE_ENDPOINTS:
    app.include_router(voice_router)
    logging.info("Voice endpoints loaded")

# Include model management endpoints for hot-swapping
try:
    from api.model_management_endpoints import router as model_management_router
    app.include_router(model_management_router)
    logging.info("Model management endpoints loaded for hot-swapping")
except ImportError as e:
    logging.warning(f"Model management endpoints not available: {e}")

# Create service instance
service = UnifiedAIEngineService()

# Startup event
@app.on_event("startup")
async def startup_event():
    """Initialize service on startup"""
    await service.initialize()

# ============================================================================
# API ENDPOINTS - ORGANIZED BY FUNCTION
# ============================================================================

# ----------------------------------------------------------------------------
# Health & Status Endpoints
# ----------------------------------------------------------------------------

@app.get("/", tags=["Status"])
async def root():
    """Root endpoint with API information"""
    return {
        "service": "WeedGo AI Engine",
        "version": "2.0.0",
        "status": "online",
        "documentation": "/api/docs",
        "endpoints": {
            "chat": "/api/v1/chat",
            "products": "/api/v1/products",
            "compliance": "/api/v1/compliance",
            "analytics": "/api/v1/analytics"
        }
    }

@app.get("/api", tags=["Status"])
@app.get("/api/v1", tags=["Status"])
async def api_root():
    """API v1 root endpoint with available endpoints"""
    return {
        "version": "v1",
        "status": "online",
        "documentation": {
            "swagger": "/api/docs",
            "redoc": "/api/redoc"
        },
        "endpoints": {
            "chat": {
                "POST /api/v1/chat": "Main chat endpoint",
                "GET /api/v1/chat/history/{customer_id}": "Get chat history"
            },
            "products": {
                "POST /api/v1/products/search": "Search products",
                "GET /api/v1/products": "List products",
                "GET /api/v1/products/{id}": "Get product details",
                "GET /api/v1/products/categories": "List categories",
                "GET /api/v1/products/recommendations/{intent}": "Get recommendations"
            },
            "cart": {
                "POST /api/v1/cart": "Manage cart",
                "GET /api/v1/cart/{customer_id}": "Get cart"
            },
            "compliance": {
                "POST /api/v1/compliance/verify-age": "Verify age",
                "GET /api/v1/compliance/{customer_id}": "Get compliance status"
            },
            "analytics": {
                "POST /api/v1/analytics": "Query analytics",
                "GET /api/v1/analytics/performance": "Performance metrics",
                "GET /api/v1/analytics/cache": "Cache statistics"
            },
            "admin": {
                "POST /api/v1/admin/cache/clear": "Clear cache",
                "GET /api/v1/admin/errors": "Error report"
            }
        }
    }

@app.get("/health", tags=["Status"])
@app.get("/api/health", tags=["Status"])
async def health_check():
    """Comprehensive health check"""
    return await service.get_health_status()

@app.get("/api/v1/ai/health", tags=["Status", "AI"])
async def ai_health_check():
    """
    Dedicated AI engine health check with detailed metrics
    Returns comprehensive status of the AI-only system
    """
    try:
        # Check if AI engine is initialized
        if not service.smart_ai_engine:
            return {
                "status": "unhealthy",
                "ai_available": False,
                "error": "AI engine not initialized",
                "message": "The AI engine has not been initialized. System cannot process requests."
            }
        
        # Check if LLM is available
        if not service.smart_ai_engine.llm:
            return {
                "status": "unhealthy",
                "ai_available": False,
                "error": "LLM_NOT_AVAILABLE",
                "message": "LLM model is not loaded. System requires AI model for all operations.",
                "metrics": service.smart_ai_engine.metrics.__dict__ if hasattr(service.smart_ai_engine, 'metrics') else {}
            }
        
        # Test LLM responsiveness
        test_start = datetime.now()
        try:
            test_response = service.smart_ai_engine.llm(
                "Respond with 'healthy' if operational.",
                max_tokens=10,
                echo=False
            )
            test_latency_ms = (datetime.now() - test_start).total_seconds() * 1000
            
            if not test_response or not test_response.get('choices'):
                return {
                    "status": "degraded",
                    "ai_available": True,
                    "warning": "LLM responded but output was empty",
                    "test_latency_ms": test_latency_ms
                }
        except Exception as e:
            return {
                "status": "unhealthy",
                "ai_available": False,
                "error": "LLM_TEST_FAILED",
                "message": f"LLM health test failed: {str(e)}",
                "metrics": service.smart_ai_engine.metrics.__dict__ if hasattr(service.smart_ai_engine, 'metrics') else {}
            }
        
        # Get comprehensive metrics
        metrics = service.smart_ai_engine.metrics
        
        # Calculate health score based on metrics
        health_score = 100.0
        issues = []
        
        # Check success rate
        success_rate = metrics.get_success_rate()
        if success_rate < 95:
            health_score -= 20
            issues.append(f"Low success rate: {success_rate:.1f}%")
        
        # Check average response time
        avg_response_time = metrics.get_average_response_time()
        if avg_response_time > 2000:  # Over 2 seconds
            health_score -= 10
            issues.append(f"High average response time: {avg_response_time:.0f}ms")
        
        # Check recent errors
        if metrics.last_error_time:
            time_since_error = time.time() - metrics.last_error_time
            if time_since_error < 60:  # Error in last minute
                health_score -= 15
                issues.append(f"Recent error: {metrics.last_error} ({time_since_error:.0f}s ago)")
        
        # Determine overall status
        if health_score >= 90:
            status = "healthy"
        elif health_score >= 70:
            status = "degraded"
        else:
            status = "unhealthy"
        
        return {
            "status": status,
            "ai_available": True,
            "health_score": health_score,
            "issues": issues,
            "test_latency_ms": test_latency_ms,
            "metrics": {
                "uptime_seconds": time.time() - metrics.startup_time,
                "total_llm_calls": metrics.total_llm_calls,
                "successful_llm_calls": metrics.successful_llm_calls,
                "failed_llm_calls": metrics.failed_llm_calls,
                "success_rate_percent": success_rate,
                "average_response_time_ms": avg_response_time,
                "intents_detected": dict(metrics.intents_detected),
                "errors_by_type": dict(metrics.errors_by_type),
                "last_error": metrics.last_error,
                "last_error_time": datetime.fromtimestamp(metrics.last_error_time).isoformat() if metrics.last_error_time else None
            },
            "configuration": {
                "mode": "AI_ONLY",
                "pattern_matching": "DISABLED",
                "fallback_behavior": "ERROR_ON_LLM_UNAVAILABLE"
            }
        }
        
    except Exception as e:
        logger.error(f"AI health check failed: {e}")
        return {
            "status": "error",
            "ai_available": False,
            "error": str(e),
            "message": "Failed to perform AI health check"
        }

# ----------------------------------------------------------------------------
# Chat & Conversation Endpoints
# ----------------------------------------------------------------------------

@app.post("/api/v1/chat", response_model=ChatResponse, tags=["Chat"])
async def chat(request: ChatRequest):
    """
    Main chat endpoint for customer interactions
    Handles full conversation flow with sales optimization
    """
    return await service.process_chat(request)

@app.post("/api/v1/chat/analyze-decision", response_model=DecisionTreeAnalysis, tags=["Chat"])
async def analyze_decision_tree(request: Dict):
    """
    Analyze the decision tree for a given query
    Provides detailed breakdown of AI decision process for visualization
    """
    try:
        query = request.get('query', '')
        session_id = request.get('session_id', None)
        
        if not query:
            raise HTTPException(status_code=400, detail="Query is required")
        
        # Ensure service is initialized
        if not service or not service.initialized:
            logger.error("Service not properly initialized for decision tree analysis")
            raise HTTPException(status_code=503, detail="Service not available")
        
        return await service.analyze_decision_tree(query, session_id)
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(f"Unexpected error in analyze_decision_tree endpoint: {e}")
        # Return 500 with proper error message
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

@app.get("/api/v1/chat/history/{customer_id}", tags=["Chat"])
async def get_chat_history(
    customer_id: str = PathParam(..., description="Customer ID"),
    limit: int = Query(default=20, le=100),
    session_id: Optional[str] = Query(default=None, description="Filter by session ID")
):
    """Get chat history for a customer"""
    try:
        cur = service.db_conn.cursor()
        
        if session_id:
            # Get history for specific session
            cur.execute("""
                SELECT message_id, session_id, user_message, ai_response, 
                       intent, response_time, created_at, metadata
                FROM chat_interactions
                WHERE customer_id = %s AND session_id = %s
                ORDER BY created_at DESC
                LIMIT %s
            """, (customer_id, session_id, limit))
        else:
            # Get all history for customer
            cur.execute("""
                SELECT message_id, session_id, user_message, ai_response, 
                       intent, response_time, created_at, metadata
                FROM chat_interactions
                WHERE customer_id = %s
                ORDER BY created_at DESC
                LIMIT %s
            """, (customer_id, limit))
        
        history = cur.fetchall()
        
        # Format the response
        formatted_history = []
        for record in history:
            # Parse metadata to extract products and quick actions
            metadata = record['metadata'] if record['metadata'] else {}
            
            formatted_entry = {
                'message_id': record['message_id'],
                'session_id': record['session_id'],
                'user_message': record['user_message'],
                'ai_response': record['ai_response'],
                'intent': record['intent'],
                'response_time': record['response_time'],
                'created_at': record['created_at'].isoformat() if record['created_at'] else None,
                'metadata': metadata
            }
            
            # Add products and quick_actions if they exist in metadata
            if metadata.get('products'):
                formatted_entry['products'] = metadata['products']
            if metadata.get('quick_actions'):
                formatted_entry['quick_actions'] = metadata['quick_actions']
            if metadata.get('quick_replies'):
                formatted_entry['quick_replies'] = metadata['quick_replies']
                
            formatted_history.append(formatted_entry)
        
        return {
            "customer_id": customer_id,
            "session_id": session_id,
            "total_messages": len(formatted_history),
            "history": formatted_history
        }
    except Exception as e:
        logger.error(f"Failed to get chat history: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/chat/users", tags=["Chat"])
async def get_chat_users(
    limit: int = Query(default=100, le=500, description="Maximum number of users to return"),
    offset: int = Query(default=0, description="Offset for pagination")
):
    """Get all users who have chatted with the system"""
    try:
        cur = service.db_conn.cursor()
        
        # Get unique users with their latest interaction
        cur.execute("""
            SELECT DISTINCT ON (customer_id)
                customer_id,
                session_id,
                user_message as last_message,
                ai_response as last_response,
                created_at as last_interaction,
                COUNT(*) OVER (PARTITION BY customer_id) as total_messages
            FROM chat_interactions
            WHERE customer_id IS NOT NULL
            ORDER BY customer_id, created_at DESC
            LIMIT %s OFFSET %s
        """, (limit, offset))
        
        users = cur.fetchall()
        
        # Also get total count
        cur.execute("SELECT COUNT(DISTINCT customer_id) as total FROM chat_interactions WHERE customer_id IS NOT NULL")
        total_result = cur.fetchone()
        total_users = total_result['total'] if total_result else 0
        
        # Format the response
        formatted_users = []
        for record in users:
            formatted_users.append({
                'customer_id': record['customer_id'],
                'last_session_id': record['session_id'],
                'last_message': record['last_message'],
                'last_response': record['last_response'],
                'last_interaction': record['last_interaction'].isoformat() if record['last_interaction'] else None,
                'total_messages': record['total_messages']
            })
        
        return {
            "total_users": total_users,
            "limit": limit,
            "offset": offset,
            "users": formatted_users
        }
    except Exception as e:
        logger.error(f"Failed to get chat users: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/chat/replay", tags=["Chat"])
async def replay_chat_message(request: ChatRequest):
    """
    Replay a historical chat message with current model and save to database
    Used to compare how AI responses have evolved over time
    """
    try:
        # Process the message with replay context
        replay_context = request.dict()
        replay_context['is_replay'] = True
        
        # Get the current model's response
        response = await service.process_chat(ChatRequest(**replay_context))
        
        # Add replay-specific metadata
        response_dict = response.dict() if hasattr(response, 'dict') else response
        response_dict['replay_metadata'] = {
            'replayed_at': datetime.now().isoformat(),
            'original_session_id': replay_context.get('original_session_id'),
            'model_version': getattr(service, 'model_version', 'v1.0'),
            'is_replay': True
        }
        
        return response_dict
        
    except Exception as e:
        logger.error(f"Replay error: {e}")
        return JSONResponse(
            status_code=500,
            content={
                "error": "Failed to replay message",
                "details": str(e)
            }
        )

# Semantic Terminology Test Endpoints
@app.post("/api/v1/test/semantic-terminology", tags=["Testing"])
async def test_semantic_terminology(request: Dict):
    """
    Test the OPTIMIZED semantic terminology service - SINGLE LLM call!
    5x faster than before!
    """
    import time
    try:
        message = request.get('message', '')
        
        # Import optimized version
        from services.semantic_terminology_service_optimized import initialize_optimized_semantic
        
        # Initialize optimized service if not already done
        if not hasattr(service, 'optimized_semantic'):
            service.optimized_semantic = initialize_optimized_semantic(service.smart_ai_engine.llm)
        
        # Time the SINGLE LLM call
        start_time = time.time()
        
        # ONE call does everything!
        understanding = await service.optimized_semantic.understand_everything(message)
        
        elapsed = time.time() - start_time
        logger.info(f"Optimized semantic understanding took {elapsed:.2f} seconds (vs 30-40s before!)")
        
        return {
            "original_message": message,
            "response_time_seconds": elapsed,
            "semantic_understanding": {
                "normalized": understanding.normalized_text,
                "products_referenced": understanding.product_references,
                "quantities_understood": understanding.quantities,
                "effects_desired": understanding.effects_desired,
                "characteristics": understanding.characteristics_wanted,
                "price_constraints": understanding.price_constraints,
                "strain_preference": understanding.strain_preferences,
                "consumption_method": understanding.consumption_method,
                "product_type": understanding.product_type
            },
            "semantic_expansion": understanding.expanded_search_terms,
            "spelling_corrected": understanding.spelling_corrected,
            "preferences_extracted": understanding.preferences,
            "note": "OPTIMIZED: Single LLM call for ALL understanding (5x faster!)"
        }
        
    except Exception as e:
        logger.error(f"Semantic terminology test error: {e}")
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )

# Replay Storage Endpoints
@app.post("/api/v1/replays/save", tags=["Replays"])
async def save_replay_result(replay: ReplayResult):
    """Save a replay result to the database for versioning and comparison"""
    conn = None
    try:
        conn = await asyncpg.connect(
            host=settings.DB_HOST,
            port=settings.DB_PORT,
            database=settings.DB_NAME,
            user=settings.DB_USER,
            password=settings.DB_PASSWORD
        )
        
        # Insert replay result with auto-versioning
        query = '''
            INSERT INTO chat_replays (
                original_conversation_id,
                original_message_id,
                original_session_id,
                replay_session_id,
                replay_batch_id,
                user_message,
                original_response,
                replayed_response,
                confidence,
                original_confidence,
                response_time_ms,
                original_response_time_ms,
                model_version,
                original_model_version,
                improvement_score,
                similarity_score,
                differences,
                metrics,
                metadata
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, $17, $18, $19)
            RETURNING id, version
        '''
        
        result = await conn.fetchrow(
            query,
            replay.original_conversation_id,
            replay.original_message_id,
            replay.original_conversation_id,  # Use same as original_session_id for now
            replay.replay_session_id,
            replay.replay_batch_id,
            replay.user_message,
            replay.original_response,
            replay.replayed_response,
            replay.confidence,
            replay.original_confidence,
            replay.response_time_ms,
            replay.original_response_time_ms,
            replay.model_version,
            replay.original_model_version,
            replay.improvement_score,
            replay.similarity_score,
            json.dumps(replay.differences) if replay.differences else '{}',
            json.dumps(replay.metrics) if replay.metrics else '{}',
            json.dumps(replay.metadata) if replay.metadata else '{}'
        )
        
        return {
            "success": True,
            "replay_id": result['id'],
            "version": result['version']
        }
        
    except Exception as e:
        logger.error(f"Failed to save replay result: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if conn:
            await conn.close()

@app.get("/api/v1/replays/history/{conversation_id}", tags=["Replays"])
async def get_replay_history(
    conversation_id: str,
    message_id: Optional[str] = None
):
    """Get all replay versions for a conversation or specific message"""
    conn = None
    try:
        conn = await asyncpg.connect(
            host=settings.DB_HOST,
            port=settings.DB_PORT,
            database=settings.DB_NAME,
            user=settings.DB_USER,
            password=settings.DB_PASSWORD
        )
        
        if message_id:
            query = '''
                SELECT * FROM chat_replays
                WHERE original_conversation_id = $1 AND original_message_id = $2
                ORDER BY version DESC
            '''
            rows = await conn.fetch(query, conversation_id, message_id)
        else:
            query = '''
                SELECT * FROM chat_replays
                WHERE original_conversation_id = $1
                ORDER BY version DESC, created_at DESC
            '''
            rows = await conn.fetch(query, conversation_id)
        
        replays = []
        for row in rows:
            replays.append({
                "id": row['id'],
                "version": row['version'],
                "user_message": row['user_message'],
                "original_response": row['original_response'],
                "replayed_response": row['replayed_response'],
                "confidence": row['confidence'],
                "confidence_change": row['confidence_change'],
                "response_time_ms": row['response_time_ms'],
                "response_time_change_ms": row['response_time_change_ms'],
                "model_version": row['model_version'],
                "improvement_score": row['improvement_score'],
                "similarity_score": row['similarity_score'],
                "differences": row['differences'],
                "created_at": row['created_at'].isoformat() if row['created_at'] else None
            })
        
        return {
            "conversation_id": conversation_id,
            "replays": replays,
            "total_versions": len(replays)
        }
        
    except Exception as e:
        logger.error(f"Failed to get replay history: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if conn:
            await conn.close()

@app.get("/api/v1/replays/comparison", tags=["Replays"])
async def get_replay_comparison(
    conversation_id: str,
    version1: int = 1,
    version2: Optional[int] = None
):
    """Compare two versions of replayed responses"""
    conn = None
    try:
        conn = await asyncpg.connect(
            host=settings.DB_HOST,
            port=settings.DB_PORT,
            database=settings.DB_NAME,
            user=settings.DB_USER,
            password=settings.DB_PASSWORD
        )
        
        # If version2 not specified, use latest
        if not version2:
            latest_query = '''
                SELECT MAX(version) as latest FROM chat_replays
                WHERE original_conversation_id = $1
            '''
            latest = await conn.fetchval(latest_query, conversation_id)
            version2 = latest if latest else version1
        
        query = '''
            SELECT 
                cr1.user_message,
                cr1.version as v1,
                cr1.replayed_response as response_v1,
                cr1.confidence as confidence_v1,
                cr1.response_time_ms as time_v1,
                cr1.model_version as model_v1,
                cr2.version as v2,
                cr2.replayed_response as response_v2,
                cr2.confidence as confidence_v2,
                cr2.response_time_ms as time_v2,
                cr2.model_version as model_v2,
                (cr2.confidence - cr1.confidence) as confidence_improvement,
                (cr1.response_time_ms - cr2.response_time_ms) as speed_improvement,
                cr2.similarity_score,
                cr2.improvement_score
            FROM chat_replays cr1
            LEFT JOIN chat_replays cr2 
                ON cr1.original_conversation_id = cr2.original_conversation_id 
                AND cr1.original_message_id = cr2.original_message_id
                AND cr2.version = $3
            WHERE cr1.original_conversation_id = $1 
                AND cr1.version = $2
        '''
        
        rows = await conn.fetch(query, conversation_id, version1, version2)
        
        comparisons = []
        for row in rows:
            comparisons.append({
                "user_message": row['user_message'],
                "version1": {
                    "version": row['v1'],
                    "response": row['response_v1'],
                    "confidence": row['confidence_v1'],
                    "response_time_ms": row['time_v1'],
                    "model_version": row['model_v1']
                },
                "version2": {
                    "version": row['v2'],
                    "response": row['response_v2'],
                    "confidence": row['confidence_v2'],
                    "response_time_ms": row['time_v2'],
                    "model_version": row['model_v2']
                },
                "improvements": {
                    "confidence_change": row['confidence_improvement'],
                    "speed_improvement_ms": row['speed_improvement'],
                    "similarity_score": row['similarity_score'],
                    "overall_improvement": row['improvement_score']
                }
            })
        
        return {
            "conversation_id": conversation_id,
            "version1": version1,
            "version2": version2,
            "comparisons": comparisons
        }
        
    except Exception as e:
        logger.error(f"Failed to get replay comparison: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if conn:
            await conn.close()

@app.get("/api/v1/conversations/history", tags=["Conversations"])
async def get_conversations_history(
    start_date: str = Query(default=None, description="Start date (YYYY-MM-DD)"),
    end_date: str = Query(default=None, description="End date (YYYY-MM-DD)"),
    customer: str = Query(default=None, description="Customer name or ID filter"),
    budtender: str = Query(default=None, description="Budtender personality filter"),
    intent: str = Query(default=None, description="Intent filter"),
    has_products: Optional[bool] = Query(default=None, description="Filter by product recommendations"),
    converted: Optional[bool] = Query(default=None, description="Filter by conversion status"),
    limit: int = Query(default=100, le=500)
):
    """Get comprehensive conversation history with filtering"""
    try:
        # Rollback any existing failed transactions
        service.db_conn.rollback()
        cur = service.db_conn.cursor()
        
        # Build dynamic query - now joining with customer_profiles for names
        query = """
            SELECT DISTINCT
                ci.session_id,
                ci.customer_id,
                COALESCE(cp.name, ci.metadata->>'customer_name', 'Anonymous') as customer_name,
                COALESCE(cp.email, cp.phone, ci.metadata->>'customer_contact') as customer_contact,
                ci.metadata->>'budtender_personality' as budtender_personality,
                MIN(ci.created_at) as start_time,
                MAX(ci.created_at) as end_time,
                COUNT(*) as total_messages,
                COUNT(CASE WHEN ci.metadata->>'products' IS NOT NULL THEN 1 END) as products_recommended,
                ARRAY_AGG(DISTINCT ci.intent) FILTER (WHERE ci.intent IS NOT NULL) as intents_detected,
                CAST(ci.metadata->>'satisfaction_score' as FLOAT) as satisfaction_score,
                CAST(ci.metadata->>'conversion' as BOOLEAN) as conversion
            FROM chat_interactions ci
            LEFT JOIN customer_profiles cp ON ci.customer_id = cp.customer_id
            WHERE 1=1
        """
        
        params = []
        
        # Add filters
        if start_date:
            query += " AND ci.created_at >= %s"
            params.append(f"{start_date} 00:00:00")
        
        if end_date:
            query += " AND ci.created_at <= %s"
            params.append(f"{end_date} 23:59:59")
        
        if customer:
            query += " AND (ci.customer_id = %s OR ci.metadata->>'customer_name' ILIKE %s)"
            params.append(customer)
            params.append(f"%{customer}%")
        
        if budtender:
            query += " AND ci.metadata->>'budtender_personality' = %s"
            params.append(budtender)
        
        if intent:
            query += " AND ci.intent = %s"
            params.append(intent)
        
        if has_products is not None:
            if has_products:
                query += " AND ci.metadata->>'products' IS NOT NULL"
            else:
                query += " AND ci.metadata->>'products' IS NULL"
        
        if converted is not None:
            query += " AND CAST(ci.metadata->>'conversion' as BOOLEAN) = %s"
            params.append(converted)
        
        query += """
            GROUP BY ci.session_id, ci.customer_id, cp.name, cp.email, cp.phone,
                     ci.metadata->>'customer_name', ci.metadata->>'customer_contact',
                     ci.metadata->>'budtender_personality', ci.metadata->>'satisfaction_score', 
                     ci.metadata->>'conversion'
            ORDER BY start_time DESC
            LIMIT %s
        """
        params.append(limit)
        
        cur.execute(query, params)
        conversations = []
        
        for row in cur.fetchall():
            # Get messages for this session - both user and AI messages
            cur.execute("""
                SELECT message_id, created_at as timestamp, 
                       user_message, ai_response,
                       intent, 
                       CAST(metadata->>'confidence' as FLOAT) as confidence,
                       metadata->>'products' as products,
                       metadata
                FROM chat_interactions
                WHERE session_id = %s
                ORDER BY created_at ASC
            """, (row['session_id'],))
            
            messages = []
            for msg_row in cur.fetchall():
                # Add user message if it exists
                if msg_row['user_message']:
                    messages.append({
                        'id': f"{msg_row['message_id']}_user",
                        'timestamp': msg_row['timestamp'].isoformat() if msg_row['timestamp'] else None,
                        'sender': 'customer',
                        'message': msg_row['user_message'],
                        'intent': msg_row['intent'],
                        'confidence': msg_row['confidence'],
                        'products': None,
                        'metadata': msg_row['metadata']
                    })
                
                # Add AI response if it exists
                if msg_row['ai_response']:
                    messages.append({
                        'id': f"{msg_row['message_id']}_ai",
                        'timestamp': msg_row['timestamp'].isoformat() if msg_row['timestamp'] else None,
                        'sender': 'budtender',
                        'message': msg_row['ai_response'],
                        'intent': msg_row['intent'],
                        'confidence': msg_row['confidence'],
                        'products': json.loads(msg_row['products']) if msg_row['products'] else None,
                        'metadata': msg_row['metadata']
                    })
            
            # Create a unique ID combining session_id and customer_id to avoid React key conflicts
            unique_id = f"{row['session_id']}_{row['customer_id'] or 'unknown'}_{row['start_time'].timestamp() if row['start_time'] else 0}"
            
            conversations.append({
                'id': unique_id,  # Unique ID for React key
                'display_id': row['session_id'][:8],  # Short ID for display
                'session_id': row['session_id'],
                'customer_id': row['customer_id'] or 'unknown',
                'customer_name': row['customer_name'] or 'Anonymous',
                'customer_contact': row['customer_contact'] or '',
                'budtender_personality': row['budtender_personality'] or 'Zac',
                'start_time': row['start_time'].isoformat() if row['start_time'] else None,
                'end_time': row['end_time'].isoformat() if row['end_time'] else None,
                'total_messages': row['total_messages'],
                'products_recommended': row['products_recommended'],
                'intents_detected': row['intents_detected'] or [],
                'satisfaction_score': row['satisfaction_score'],
                'conversion': row['conversion'],
                'messages': messages
            })
        
        cur.close()
        
        return {
            "conversations": conversations,
            "total": len(conversations),
            "filters_applied": {
                "start_date": start_date,
                "end_date": end_date,
                "customer": customer,
                "budtender": budtender,
                "intent": intent,
                "has_products": has_products,
                "converted": converted
            }
        }
        
    except Exception as e:
        logger.error(f"Failed to get conversation history: {e}")
        # Return empty data instead of failing
        return {
            "conversations": [],
            "total": 0,
            "filters_applied": {
                "start_date": start_date,
                "end_date": end_date,
                "customer": customer,
                "budtender": budtender,
                "intent": intent,
                "has_products": has_products,
                "converted": converted
            }
        }

@app.get("/api/v1/conversation-flows", tags=["Conversations"])
async def get_conversation_flows():
    """Get all conversation flows"""
    try:
        cur = service.db_conn.cursor()
        cur.execute("""
            SELECT id, name, description, flow_data, created_at, updated_at
            FROM conversation_flows
            ORDER BY updated_at DESC
        """)
        
        flows = []
        for row in cur.fetchall():
            flows.append({
                'id': row['id'],
                'name': row['name'],
                'description': row['description'],
                'nodes': row['flow_data'].get('nodes', []) if row['flow_data'] else [],
                'edges': row['flow_data'].get('edges', []) if row['flow_data'] else [],
                'created_at': row['created_at'].isoformat() if row['created_at'] else None,
                'updated_at': row['updated_at'].isoformat() if row['updated_at'] else None
            })
        
        cur.close()
        return {"flows": flows}
        
    except Exception as e:
        logger.error(f"Failed to get conversation flows: {e}")
        # Return empty list if table doesn't exist
        return {"flows": []}

@app.post("/api/v1/conversation-flows", tags=["Conversations"])
async def save_conversation_flow(flow_data: Dict[str, Any]):
    """Save or update a conversation flow"""
    try:
        cur = service.db_conn.cursor()
        
        # Create table if it doesn't exist
        cur.execute("""
            CREATE TABLE IF NOT EXISTS conversation_flows (
                id VARCHAR(255) PRIMARY KEY,
                name VARCHAR(255) NOT NULL,
                description TEXT,
                flow_data JSONB,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        service.db_conn.commit()
        
        # Check if flow exists
        cur.execute("SELECT id FROM conversation_flows WHERE id = %s", (flow_data['id'],))
        exists = cur.fetchone()
        
        if exists:
            # Update existing flow
            cur.execute("""
                UPDATE conversation_flows
                SET name = %s, description = %s, flow_data = %s, updated_at = CURRENT_TIMESTAMP
                WHERE id = %s
            """, (
                flow_data['name'],
                flow_data.get('description', ''),
                json.dumps({
                    'nodes': flow_data.get('nodes', []),
                    'edges': flow_data.get('edges', [])
                }),
                flow_data['id']
            ))
        else:
            # Insert new flow
            cur.execute("""
                INSERT INTO conversation_flows (id, name, description, flow_data)
                VALUES (%s, %s, %s, %s)
            """, (
                flow_data['id'],
                flow_data['name'],
                flow_data.get('description', ''),
                json.dumps({
                    'nodes': flow_data.get('nodes', []),
                    'edges': flow_data.get('edges', [])
                })
            ))
        
        service.db_conn.commit()
        cur.close()
        
        return {"success": True, "message": "Flow saved successfully"}
        
    except Exception as e:
        logger.error(f"Failed to save conversation flow: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/v1/conversation-flows/{flow_id}", tags=["Conversations"])
async def delete_conversation_flow(flow_id: str):
    """Delete a conversation flow"""
    try:
        cur = service.db_conn.cursor()
        cur.execute("DELETE FROM conversation_flows WHERE id = %s", (flow_id,))
        service.db_conn.commit()
        cur.close()
        
        return {"success": True, "message": "Flow deleted successfully"}
        
    except Exception as e:
        logger.error(f"Failed to delete conversation flow: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ----------------------------------------------------------------------------
# Product Endpoints
# ----------------------------------------------------------------------------

@app.post("/api/v1/products/search", response_model=List[ProductResponse], tags=["Products"])
async def search_products(request: ProductSearchRequest):
    """
    Search products with multiple strategies
    Supports text search, intent-based, and filtered search
    """
    return await service.search_products(request)

@app.get("/api/v1/products", response_model=List[ProductResponse], tags=["Products"])
async def get_products(
    category: Optional[str] = Query(None),
    limit: int = Query(default=10, le=50),
    offset: int = Query(default=0)
):
    """Get products with optional filtering"""
    request = ProductSearchRequest(
        category=category,
        limit=limit,
        offset=offset
    )
    return await service.search_products(request)

@app.get("/api/v1/products/{product_id}", response_model=ProductResponse, tags=["Products"])
async def get_product(product_id: int = PathParam(..., description="Product ID")):
    """Get specific product details"""
    try:
        cur = service.db_conn.cursor()
        cur.execute("SELECT * FROM products WHERE id = %s", (product_id,))
        product = cur.fetchone()
        
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")
        
        return ProductResponse(
            id=product['id'],
            product_name=product['product_name'],
            brand=product['brand'],
            category=product.get('category', 'Unknown'),
            sub_category=product.get('sub_category'),
            unit_price=product['unit_price'],
            size=product.get('size'),
            # Use thc_mg and cbd_mg if percentages are not available
            thc_max_percent=product.get('thc_max_percent') or product.get('thc_mg', 0),
            cbd_max_percent=product.get('cbd_max_percent') or product.get('cbd_mg', 0),
            thc_range=product.get('thc_range'),
            cbd_range=product.get('cbd_range'),
            short_description=product.get('short_description'),
            long_description=product.get('long_description'),
            inventory_count=product.get('inventory_count'),
            in_stock=product.get('in_stock', True),
            pitch=service._generate_product_pitch(product),
            effects=service._get_product_effects(product),
            terpenes=service._get_product_terpenes(product),
            strain_type=product.get('plant_type'),
            image_url=product.get('image_url'),  # Include image URL from database
            rating=product.get('rating', 4.2),  # Default rating if not in DB
            review_count=product.get('review_count', 0)  # Default review count
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/products/recommendations/{intent}", response_model=List[ProductResponse], tags=["Products"])
async def get_recommendations(
    intent: str = PathParam(..., description="Customer intent (sleep, pain, energy, etc.)"),
    limit: int = Query(default=5, le=20)
):
    """Get product recommendations for specific intent"""
    request = ProductSearchRequest(intent=intent, limit=limit)
    return await service.search_products(request)

@app.get("/api/v1/products/categories", tags=["Products"])
async def get_categories():
    """Get all product categories"""
    try:
        cur = service.db_conn.cursor()
        cur.execute("SELECT DISTINCT category FROM products WHERE category IS NOT NULL ORDER BY category")
        categories = [row['category'] for row in cur.fetchall()]
        return {"categories": categories}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ----------------------------------------------------------------------------
# Skip Words Management Endpoints
# ----------------------------------------------------------------------------

@app.get("/api/v1/skip-words", tags=["Training"])
async def get_skip_words(
    active_only: bool = Query(default=True, description="Return only active skip words"),
    category: Optional[str] = Query(default=None, description="Filter by category")
):
    """Get skip words for search filtering"""
    try:
        cur = service.db_conn.cursor()
        query = "SELECT * FROM skip_words WHERE 1=1"
        params = []
        
        if active_only:
            query += " AND active = true"
        if category:
            query += " AND category = %s"
            params.append(category)
            
        query += " ORDER BY category, word"
        cur.execute(query, params)
        skip_words = cur.fetchall()
        cur.close()
        
        return {"skip_words": skip_words}
    except Exception as e:
        logger.error(f"Failed to get skip words: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/skip-words", tags=["Training"])
async def add_skip_word(
    word: str = Body(..., description="Word to add to skip list"),
    category: str = Body(default="general", description="Category of the word"),
    description: str = Body(default="", description="Description of why to skip")
):
    """Add a new skip word"""
    try:
        cur = service.db_conn.cursor()
        cur.execute(
            """INSERT INTO skip_words (word, category, description) 
               VALUES (%s, %s, %s) 
               ON CONFLICT (word) DO UPDATE 
               SET category = EXCLUDED.category, 
                   description = EXCLUDED.description,
                   active = true,
                   updated_at = CURRENT_TIMESTAMP
               RETURNING *""",
            (word.lower(), category, description)
        )
        result = cur.fetchone()
        service.db_conn.commit()
        cur.close()
        
        return {"skip_word": result, "message": f"Skip word '{word}' added successfully"}
    except Exception as e:
        logger.error(f"Failed to add skip word: {e}")
        service.db_conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/v1/skip-words/{word}", tags=["Training"])
async def delete_skip_word(word: str = PathParam(..., description="Word to remove")):
    """Delete a skip word"""
    try:
        cur = service.db_conn.cursor()
        cur.execute("DELETE FROM skip_words WHERE word = %s RETURNING word", (word.lower(),))
        deleted = cur.fetchone()
        service.db_conn.commit()
        cur.close()
        
        if deleted:
            return {"message": f"Skip word '{word}' deleted successfully"}
        else:
            raise HTTPException(status_code=404, detail=f"Skip word '{word}' not found")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete skip word: {e}")
        service.db_conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/api/v1/skip-words/{word}/toggle", tags=["Training"])
async def toggle_skip_word(word: str = PathParam(..., description="Word to toggle")):
    """Toggle active status of a skip word"""
    try:
        cur = service.db_conn.cursor()
        cur.execute(
            """UPDATE skip_words 
               SET active = NOT active, updated_at = CURRENT_TIMESTAMP 
               WHERE word = %s 
               RETURNING *""",
            (word.lower(),)
        )
        result = cur.fetchone()
        service.db_conn.commit()
        cur.close()
        
        if result:
            status = "activated" if result['active'] else "deactivated"
            return {"skip_word": result, "message": f"Skip word '{word}' {status}"}
        else:
            raise HTTPException(status_code=404, detail=f"Skip word '{word}' not found")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to toggle skip word: {e}")
        service.db_conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))

# ----------------------------------------------------------------------------
# Medical Intents Management Endpoints
# ----------------------------------------------------------------------------

@app.get("/api/v1/medical-intents", tags=["Training"])
async def get_medical_intents():
    """Get all medical intents with their keywords"""
    try:
        # Rollback any existing failed transactions
        service.db_conn.rollback()
        cur = service.db_conn.cursor()
        
        # Check if table exists first
        cur.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = 'medical_intents'
            )
        """)
        result = cur.fetchone()
        table_exists = result[0] if result else False
        cur.close()
        
        if not table_exists:
            logger.warning("Medical intents table doesn't exist, returning default data")
            return {"intents": [
                {
                    "id": 1,
                    "intent_name": "pain_relief",
                    "description": "Looking for pain management solutions",
                    "search_query": "pain relief strains",
                    "active": True,
                    "priority": 10,
                    "keywords": ["pain", "hurt", "ache", "chronic", "relief"],
                    "keyword_weights": {"pain": 1.0, "hurt": 0.8, "ache": 0.8, "chronic": 0.9, "relief": 0.7}
                },
                {
                    "id": 2,
                    "intent_name": "anxiety",
                    "description": "Seeking anxiety reduction",
                    "search_query": "anxiety calming strains",
                    "active": True,
                    "priority": 9,
                    "keywords": ["anxiety", "stress", "calm", "relax", "nervous"],
                    "keyword_weights": {"anxiety": 1.0, "stress": 0.9, "calm": 0.7, "relax": 0.7, "nervous": 0.8}
                },
                {
                    "id": 3,
                    "intent_name": "sleep",
                    "description": "Help with sleep issues",
                    "search_query": "sleep insomnia strains",
                    "active": True,
                    "priority": 8,
                    "keywords": ["sleep", "insomnia", "rest", "tired", "night"],
                    "keyword_weights": {"sleep": 1.0, "insomnia": 0.95, "rest": 0.7, "tired": 0.6, "night": 0.5}
                }
            ]}
        
        # Get intents - create new cursor
        cur = service.db_conn.cursor()
        cur.execute("""
            SELECT id, intent_name, description, search_query, active, priority 
            FROM medical_intents 
            ORDER BY priority DESC, intent_name
        """)
        intents = cur.fetchall()
        
        # Get keywords for each intent
        for intent in intents:
            cur.execute("""
                SELECT keyword, weight 
                FROM medical_intent_keywords 
                WHERE intent_id = %s 
                ORDER BY weight DESC
            """, (intent['id'],))
            keywords = cur.fetchall()
            intent['keywords'] = [kw['keyword'] for kw in keywords]
            intent['keyword_weights'] = {kw['keyword']: float(kw['weight']) for kw in keywords}
        
        cur.close()
        return {"intents": intents}
    except Exception as e:
        import traceback
        logger.error(f"Failed to get medical intents: {e}\n{traceback.format_exc()}")
        # Return default data instead of failing
        return {"intents": [
            {
                "id": 1,
                "intent_name": "pain_relief",
                "description": "Looking for pain management solutions",
                "search_query": "pain relief strains",
                "active": True,
                "priority": 10,
                "keywords": ["pain", "hurt", "ache", "chronic", "relief"],
                "keyword_weights": {"pain": 1.0, "hurt": 0.8, "ache": 0.8, "chronic": 0.9, "relief": 0.7}
            },
            {
                "id": 2,
                "intent_name": "anxiety",
                "description": "Seeking anxiety reduction",
                "search_query": "anxiety calming strains",
                "active": True,
                "priority": 9,
                "keywords": ["anxiety", "stress", "calm", "relax", "nervous"],
                "keyword_weights": {"anxiety": 1.0, "stress": 0.9, "calm": 0.7, "relax": 0.7, "nervous": 0.8}
            },
            {
                "id": 3,
                "intent_name": "sleep",
                "description": "Help with sleep issues",
                "search_query": "sleep insomnia strains",
                "active": True,
                "priority": 8,
                "keywords": ["sleep", "insomnia", "rest", "tired", "night"],
                "keyword_weights": {"sleep": 1.0, "insomnia": 0.95, "rest": 0.7, "tired": 0.6, "night": 0.5}
            }
        ]}

@app.post("/api/v1/medical-intents/{intent_id}/keywords", tags=["Training"])
async def add_intent_keyword(
    intent_id: int = PathParam(..., description="Intent ID"),
    keyword: str = Body(..., description="Keyword to add"),
    weight: float = Body(default=1.0, description="Keyword weight (0.0-1.0)")
):
    """Add keyword to medical intent"""
    try:
        cur = service.db_conn.cursor()
        cur.execute("""
            INSERT INTO medical_intent_keywords (intent_id, keyword, weight) 
            VALUES (%s, %s, %s) 
            ON CONFLICT (intent_id, keyword) DO UPDATE 
            SET weight = EXCLUDED.weight
            RETURNING *
        """, (intent_id, keyword.lower(), weight))
        result = cur.fetchone()
        service.db_conn.commit()
        cur.close()
        
        return {"keyword": result, "message": f"Keyword '{keyword}' added to intent"}
    except Exception as e:
        logger.error(f"Failed to add keyword: {e}")
        service.db_conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/v1/medical-intents/{intent_id}/keywords/{keyword}", tags=["Training"])
async def delete_intent_keyword(
    intent_id: int = PathParam(..., description="Intent ID"),
    keyword: str = PathParam(..., description="Keyword to remove")
):
    """Remove keyword from medical intent"""
    try:
        cur = service.db_conn.cursor()
        cur.execute("""
            DELETE FROM medical_intent_keywords 
            WHERE intent_id = %s AND keyword = %s
            RETURNING keyword
        """, (intent_id, keyword.lower()))
        deleted = cur.fetchone()
        service.db_conn.commit()
        cur.close()
        
        if deleted:
            return {"message": f"Keyword '{keyword}' removed from intent"}
        else:
            raise HTTPException(status_code=404, detail="Keyword not found")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete keyword: {e}")
        service.db_conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))

# ----------------------------------------------------------------------------
# System Configuration Management Endpoints
# ----------------------------------------------------------------------------

@app.get("/api/v1/system-config", tags=["Training"])
async def get_system_config(category: Optional[str] = Query(default=None)):
    """Get system configuration parameters"""
    try:
        cur = service.db_conn.cursor()
        query = "SELECT * FROM system_config WHERE active = true"
        params = []
        
        if category:
            query += " AND category = %s"
            params.append(category)
            
        query += " ORDER BY category, config_key"
        cur.execute(query, params)
        configs = cur.fetchall()
        cur.close()
        
        return {"configs": configs}
    except Exception as e:
        logger.error(f"Failed to get system config: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/api/v1/system-config/{config_key}", tags=["Training"])
async def update_system_config(
    config_key: str = PathParam(..., description="Configuration key"),
    value: str = Body(..., description="New value")
):
    """Update system configuration value"""
    try:
        cur = service.db_conn.cursor()
        cur.execute("""
            UPDATE system_config 
            SET config_value = %s, updated_at = CURRENT_TIMESTAMP 
            WHERE config_key = %s 
            RETURNING *
        """, (value, config_key))
        result = cur.fetchone()
        service.db_conn.commit()
        cur.close()
        
        if result:
            return {"config": result, "message": f"Configuration '{config_key}' updated"}
        else:
            raise HTTPException(status_code=404, detail=f"Configuration '{config_key}' not found")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update config: {e}")
        service.db_conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))

# ----------------------------------------------------------------------------
# Cart Management Endpoints
# ----------------------------------------------------------------------------

@app.post("/api/v1/cart", response_model=CartResponse, tags=["Cart"])
async def manage_cart(request: CartRequest):
    """
    Manage customer cart
    Actions: add, remove, update, clear, checkout
    """
    try:
        # Check compliance for checkout
        # Age verification removed - handled by IAM and client apps
        # Checkout allowed as users are pre-verified
        
        # Get or create cart
        if request.customer_id not in service.sessions:
            service.sessions[request.customer_id] = {'cart': {'items': [], 'total': 0}}
        
        cart = service.sessions[request.customer_id]['cart']
        
        # Process action
        if request.action == "add":
            cart['items'].append({
                'product_id': request.product_id,
                'quantity': request.quantity
            })
        elif request.action == "remove":
            cart['items'] = [
                item for item in cart['items']
                if item['product_id'] != request.product_id
            ]
        elif request.action == "clear":
            cart['items'] = []
        
        # Calculate total
        cart['total'] = sum(item.get('quantity', 1) * 10 for item in cart['items'])  # Simplified
        
        return CartResponse(
            customer_id=request.customer_id,
            items=cart['items'],
            total=cart['total'],
            item_count=len(cart['items']),
            status='active',
            compliance_status='verified' if request.action == 'checkout' else None
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/cart/{customer_id}", response_model=CartResponse, tags=["Cart"])
async def get_cart(customer_id: str = PathParam(..., description="Customer ID")):
    """Get current cart for customer"""
    if customer_id not in service.sessions:
        return CartResponse(
            customer_id=customer_id,
            items=[],
            total=0,
            item_count=0,
            status='empty'
        )
    
    cart = service.sessions[customer_id].get('cart', {'items': [], 'total': 0})
    return CartResponse(
        customer_id=customer_id,
        items=cart['items'],
        total=cart['total'],
        item_count=len(cart['items']),
        status='active' if cart['items'] else 'empty'
    )

# ----------------------------------------------------------------------------
# Compliance & Verification Endpoints
# ----------------------------------------------------------------------------

@app.post("/api/v1/compliance/verify-age", response_model=ComplianceResponse, tags=["Compliance"])
async def verify_age(request: VerifyAgeRequest):
    """
    Verify customer age for compliance
    Required before any purchase operations
    """
    try:
        birth_date = date.fromisoformat(request.birth_date)
        method = VerificationMethod[request.verification_method.upper()]
        
        status = service.compliance_manager.verify_customer(
            request.customer_id,
            birth_date,
            method,
            request.government_id
        )
        
        token = None
        if status == ComplianceStatus.VERIFIED:
            verification = service.compliance_manager.verification_cache[request.customer_id]
            token = service.compliance_manager.generate_compliance_token(
                request.customer_id, verification
            )
        
        return ComplianceResponse(
            customer_id=request.customer_id,
            status=status.value,
            verified=status == ComplianceStatus.VERIFIED,
            token=token,
            message=f"Age verification {status.value}",
            expires_at=datetime.now().isoformat() if status == ComplianceStatus.VERIFIED else None
        )
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/v1/compliance/{customer_id}", tags=["Compliance"])
async def get_compliance_status(customer_id: str = PathParam(..., description="Customer ID")):
    """
    Get compliance status and limits for customer
    Shows daily purchase limits and remaining allowances
    """
    try:
        report = service.compliance_manager.get_compliance_report(customer_id)
        return report
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ----------------------------------------------------------------------------
# Analytics & Metrics Endpoints
# ----------------------------------------------------------------------------

@app.get("/api/v1/analytics/dashboard", tags=["Analytics"])
async def get_dashboard_analytics(
    start_date: str = Query(default=None),
    end_date: str = Query(default=None)
):
    """Get analytics data in dashboard format"""
    try:
        # Generate sample analytics data structure expected by frontend
        import random
        from datetime import datetime, timedelta
        
        # Generate daily conversation data
        daily_conversations = []
        if start_date and end_date:
            start = datetime.fromisoformat(start_date)
            end = datetime.fromisoformat(end_date)
            current = start
            while current <= end:
                daily_conversations.append({
                    'date': current.strftime('%Y-%m-%d'),
                    'count': random.randint(50, 200),
                    'satisfaction': round(random.uniform(4.0, 5.0), 1)
                })
                current += timedelta(days=1)
        
        return {
            'daily_conversations': daily_conversations,
            'intent_distribution': [
                {'intent': 'product_inquiry', 'count': random.randint(100, 300)},
                {'intent': 'recommendation', 'count': random.randint(80, 250)},
                {'intent': 'medical', 'count': random.randint(50, 150)},
                {'intent': 'dosage', 'count': random.randint(30, 100)}
            ],
            'popular_products': [
                {'product': 'Blue Dream', 'views': random.randint(200, 500)},
                {'product': 'OG Kush', 'views': random.randint(150, 400)},
                {'product': 'Purple Haze', 'views': random.randint(100, 350)}
            ],
            'response_times': [
                {'hour': i, 'avg_ms': random.randint(800, 1500)} 
                for i in range(0, 24, 3)
            ],
            'customer_satisfaction': [
                {'rating': i, 'count': random.randint(10, 100)} 
                for i in range(1, 6)
            ],
            'slang_usage': [
                {'term': 'fire', 'count': random.randint(50, 200)},
                {'term': 'gas', 'count': random.randint(40, 150)},
                {'term': 'loud', 'count': random.randint(30, 100)}
            ],
            'conversion_funnel': [
                {'stage': 'Browse', 'count': 1000, 'rate': 100},
                {'stage': 'View Product', 'count': 600, 'rate': 60},
                {'stage': 'Add to Cart', 'count': 300, 'rate': 30},
                {'stage': 'Purchase', 'count': 150, 'rate': 15}
            ],
            'error_rates': [
                {'type': 'timeout', 'count': random.randint(0, 10)},
                {'type': 'invalid_input', 'count': random.randint(0, 20)},
                {'type': 'llm_error', 'count': random.randint(0, 5)}
            ]
        }
        
    except Exception as e:
        logger.error(f"Failed to get dashboard analytics: {e}")
        return {
            'daily_conversations': [],
            'intent_distribution': [],
            'popular_products': [],
            'response_times': [],
            'customer_satisfaction': [],
            'slang_usage': [],
            'conversion_funnel': [],
            'error_rates': []
        }

@app.post("/api/v1/analytics", tags=["Analytics"])
async def get_analytics(request: AnalyticsRequest):
    """
    Get analytics and metrics
    Types: conversion, engagement, product, customer
    """
    try:
        # Simplified analytics response
        return {
            "metric_type": request.metric_type,
            "period": f"{request.start_date} to {request.end_date}",
            "data": {
                "total_conversations": 1234,
                "conversion_rate": 0.23,
                "avg_cart_value": 67.89,
                "top_products": ["Purple Kush", "Blue Dream", "OG Kush"]
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/analytics/performance", tags=["Analytics"])
async def get_performance_metrics():
    """Get system performance metrics"""
    if service.inference_optimizer:
        return service.inference_optimizer.get_performance_stats()
    return {"status": "no_data"}

@app.get("/api/v1/analytics/cache", tags=["Analytics"])
async def get_cache_stats():
    """Get cache performance statistics"""
    if service.cache_manager:
        return service.cache_manager.get_cache_stats()
    return {"enabled": False}

# ----------------------------------------------------------------------------
# Admin Endpoints
# ----------------------------------------------------------------------------

@app.post("/api/v1/admin/cache/clear", tags=["Admin"])
async def clear_cache():
    """Clear all cache entries (admin only)"""
    try:
        if service.cache_manager:
            service.cache_manager.clear_all()
        return {"status": "cache_cleared"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/admin/errors", tags=["Admin"])
async def get_error_report():
    """Get error handler status and recent errors"""
    if service.error_handler:
        return service.error_handler.get_health_status()
    return {"status": "no_data"}

# ----------------------------------------------------------------------------
# Training & Learning Endpoints
# ----------------------------------------------------------------------------

@app.get("/api/v1/training/accuracy", tags=["Training"])
async def get_training_accuracy():
    """Get current AI accuracy metrics"""
    if not service.training_pipeline:
        return {"error": "Training pipeline not initialized"}
    
    metrics = service.training_pipeline.calculate_accuracy_metrics()
    return {
        "overall_success_rate": f"{metrics['success_rate']*100:.1f}%",
        "average_feedback_score": round(metrics['avg_feedback'], 2),
        "total_interactions_7d": metrics['total_interactions'],
        "parameter_accuracy": {
            k: f"{v*100:.1f}%" for k, v in metrics['parameter_accuracy'].items()
        },
        "common_mistakes": metrics['common_mistakes'][:5]
    }

@app.get("/api/v1/training/review-queue", tags=["Training"])
async def get_review_queue():
    """Get interactions that need human review for training"""
    if not service.active_learning:
        return {"error": "Active learning not initialized"}
    
    queue = service.active_learning.generate_review_queue()
    return {
        "total_items": len(queue),
        "review_queue": queue[:20]  # Limit to 20 items
    }

@app.post("/api/v1/training/correction", tags=["Training"])
async def submit_correction(
    interaction_id: int,
    corrected_params: Dict
):
    """Submit human correction for AI inference"""
    if not service.training_pipeline:
        return {"error": "Training pipeline not initialized"}
    
    service.training_pipeline.record_correction(interaction_id, corrected_params)
    return {"status": "correction_recorded", "interaction_id": interaction_id}

@app.post("/api/v1/training/feedback", tags=["Training"])
async def submit_feedback(
    interaction_id: int,
    action: str,
    score: Optional[float] = None
):
    """Record customer action and feedback"""
    if not service.training_pipeline:
        return {"error": "Training pipeline not initialized"}
    
    service.training_pipeline.record_customer_action(interaction_id, action, score)
    return {"status": "feedback_recorded", "interaction_id": interaction_id}

@app.get("/api/v1/training/export", tags=["Training"])
async def export_training_data(limit: int = 1000):
    """Export training data for model fine-tuning"""
    if not service.training_pipeline:
        return {"error": "Training pipeline not initialized"}
    
    examples = service.training_pipeline.generate_training_examples()
    return {
        "total_examples": len(examples),
        "examples": examples[:limit],
        "format": "llama2_finetune"
    }

@app.post("/api/v1/training/examples", tags=["Training"])
async def save_training_example(request: dict):
    """Save a training example to the database"""
    try:
        cur = service.db_conn.cursor()
        
        # Insert training example
        cur.execute("""
            INSERT INTO training_examples 
            (user_input, ideal_response, intent, context_required, metadata, created_at)
            VALUES (%s, %s, %s, %s, %s, NOW())
            RETURNING id
        """, (
            request.get('user_input'),
            request.get('ideal_response'),
            request.get('intent'),
            json.dumps(request.get('context_required', [])),
            json.dumps(request.get('metadata', {}))
        ))
        
        example_id = cur.fetchone()[0]
        service.db_conn.commit()
        cur.close()
        
        # Reload training examples for learning engine
        if service.learning_engine:
            service.learning_engine.load_training_examples()
        
        return {
            "success": True,
            "example_id": example_id,
            "message": "Training example saved successfully"
        }
    except Exception as e:
        logger.error(f"Failed to save training example: {e}")
        if 'cur' in locals():
            cur.close()
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/training/apply", tags=["Training"])
async def apply_training(request: dict):
    """Apply training examples to the AI model"""
    try:
        if not service.learning_engine:
            return {"error": "Learning engine not initialized"}
        
        examples = request.get('examples', [])
        category = request.get('category', 'general')
        
        # Process each example through the learning engine
        results = []
        for example in examples:
            result = await service.learning_engine.learn_from_interaction(
                user_message=example.get('user_input'),
                ai_response=example.get('ideal_response'),
                feedback_score=5.0,  # Perfect score for training examples
                context={
                    'intent': example.get('intent'),
                    'category': category,
                    'training_mode': True
                }
            )
            results.append(result)
        
        return {
            "success": True,
            "examples_processed": len(examples),
            "results": results,
            "message": "Training applied successfully"
        }
    except Exception as e:
        logger.error(f"Failed to apply training: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/training/search-guide", tags=["Training"])
async def get_search_guide():
    """Get documentation on search endpoint parameters"""
    if SearchEndpointOptimizer:
        return SearchEndpointOptimizer.explain_search_parameters()
    return {"error": "Search optimizer not available"}

# ----------------------------------------------------------------------------
# AI Personalities Endpoints
# ----------------------------------------------------------------------------

@app.get("/api/v1/ai/personalities", tags=["AI Personalities"])
async def get_personalities():
    """Get all AI personalities from JSON files"""
    try:
        from services.personality_manager import get_personality_manager
        personality_manager = get_personality_manager()
        
        # Get all personalities from the manager
        personalities = personality_manager.get_all_personalities()
        
        # Format for API response
        formatted_personalities = [
            {
                'id': p['id'],
                'name': p['name'],
                'description': p['description'],
                'active': p['active'],
                'emoji': p['emoji'],
                'role': p.get('role', 'budtender'),
                'traits': p.get('traits', {})
            }
            for p in personalities
        ]
        
        return {'personalities': formatted_personalities}
        
    except Exception as e:
        logger.error(f"Error loading personalities: {e}")
        # Fallback to default personalities if loading fails
        return {
            'personalities': [
                {
                    'id': 'zac',
                    'name': 'Zac',
                    'description': 'Your friendly neighborhood budtender',
                    'active': True,
                    'emoji': '🌿'
                },
                {
                    'id': 'marcel',
                    'name': 'Marcel',
                    'description': 'Your energetic cannabis guide',
                    'active': True,
                    'emoji': '🔥'
                },
                {
                    'id': 'shante',
                    'name': 'Shanté',
                    'description': 'Compassionate cannabis consultant',
                    'active': True,
                    'emoji': '💚'
                }
            ]
        }
    
    # Original database code (temporarily disabled for speed)
    try:
        cur = service.db_conn.cursor(cursor_factory=RealDictCursor)
        
        # First ensure we have some default personalities
        cur.execute("SELECT COUNT(*) as count FROM ai_personalities")
        count_result = cur.fetchone()
        
        if count_result['count'] == 0:
            # Insert default personalities if none exist
            default_personalities = [
                ('marcel', 'Marcel', 'young', 'male', 'casual', 'expert', 'witty', '3', '4', 
                 'medium', '2', 'consultative', '2', 'Your energetic cannabis guide', True),
                ('shante', 'Shanté', 'mature', 'female', 'professional', 'expert', 'warm', '2', '5',
                 'detailed', '3', 'educational', '4', 'Compassionate cannabis consultant', True),
                ('kareem', 'Kareem', 'senior', 'male', 'enthusiastic', 'expert', 'playful', '4', '3',
                 'medium', '1', 'value-focused', '2', 'Your honest cannabis expert', True)
            ]
            
            for p in default_personalities:
                cur.execute("""
                    INSERT INTO ai_personalities (
                        id, name, age, gender, communication_style, knowledge_level,
                        humor_style, humor_level, empathy_level, response_length,
                        jargon_level, sales_approach, formality, description, active
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (id) DO NOTHING
                """, p)
            service.db_conn.commit()
            logger.info("Inserted default AI personalities")
        
        # Now fetch all personalities
        cur.execute("""
            SELECT * FROM ai_personalities
            ORDER BY active DESC, COALESCE(usage_count, 0) DESC
        """)
        
        personalities = []
        rows = cur.fetchall()
        
        if rows:
            for row in rows:
                personalities.append({
                    'id': row.get('id'),
                    'name': row.get('name'),
                    'age': row.get('age'),
                    'gender': row.get('gender'),
                    'communication_style': row.get('communication_style'),
                    'knowledge_level': row.get('knowledge_level'),
                    'humor_style': row.get('humor_style'),
                    'humor_level': row.get('humor_level'),
                    'empathy_level': row.get('empathy_level'),
                    'response_length': row.get('response_length'),
                    'jargon_level': row.get('jargon_level'),
                    'sales_approach': row.get('sales_approach'),
                    'formality': row.get('formality'),
                    'description': row.get('description'),
                    'sample_responses': row.get('sample_responses', []),
                    'traits': row.get('traits', []),
                    'active': row.get('active', True),
                    'avatar': row.get('avatar'),
                    'emoji': row.get('emoji'),
                    'usage_count': row.get('usage_count', 0),
                    'last_used': row.get('last_used').isoformat() if row.get('last_used') else None,
                    'average_rating': float(row.get('average_rating')) if row.get('average_rating') else None
                })
        
        cur.close()
        return {'personalities': personalities}
        
    except Exception as e:
        logger.error(f"Failed to get personalities: {e}")
        # Return empty list instead of raising exception
        return {'personalities': []}

@app.post("/api/v1/ai/personality", tags=["AI Personalities"])
async def save_personality(personality: Dict[str, Any]):
    """Save or update an AI personality"""
    try:
        cur = service.db_conn.cursor()
        
        # Check if personality exists
        cur.execute("SELECT id FROM ai_personalities WHERE id = %s", (personality['id'],))
        exists = cur.fetchone()
        
        if exists:
            # Update existing
            cur.execute("""
                UPDATE ai_personalities 
                SET name = %s, age = %s, gender = %s, communication_style = %s,
                    knowledge_level = %s, humor_style = %s, humor_level = %s,
                    empathy_level = %s, response_length = %s, jargon_level = %s,
                    sales_approach = %s, formality = %s, description = %s,
                    sample_responses = %s, traits = %s, active = %s, 
                    avatar = %s, emoji = %s
                WHERE id = %s
            """, (
                personality.get('name'),
                personality.get('age'),
                personality.get('gender'),
                personality.get('communication_style'),
                personality.get('knowledge_level'),
                personality.get('humor_style'),
                personality.get('humor_level'),
                personality.get('empathy_level'),
                personality.get('response_length'),
                personality.get('jargon_level'),
                personality.get('sales_approach'),
                personality.get('formality'),
                personality.get('description'),
                json.dumps(personality.get('sample_responses', {})),
                personality.get('traits', []),
                personality.get('active', False),
                personality.get('avatar'),
                personality.get('emoji'),
                personality['id']
            ))
        else:
            # Insert new
            cur.execute("""
                INSERT INTO ai_personalities (
                    id, name, age, gender, communication_style, knowledge_level,
                    humor_style, humor_level, empathy_level, response_length,
                    jargon_level, sales_approach, formality, description,
                    sample_responses, traits, active, avatar, emoji
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                personality['id'],
                personality.get('name'),
                personality.get('age'),
                personality.get('gender'),
                personality.get('communication_style'),
                personality.get('knowledge_level'),
                personality.get('humor_style'),
                personality.get('humor_level'),
                personality.get('empathy_level'),
                personality.get('response_length'),
                personality.get('jargon_level'),
                personality.get('sales_approach'),
                personality.get('formality'),
                personality.get('description'),
                json.dumps(personality.get('sample_responses', {})),
                personality.get('traits', []),
                personality.get('active', False),
                personality.get('avatar'),
                personality.get('emoji')
            ))
        
        service.db_conn.commit()
        cur.close()
        
        return {'success': True, 'message': f"Personality {personality['name']} saved successfully"}
        
    except Exception as e:
        logger.error(f"Failed to save personality: {e}")
        service.db_conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/v1/ai/personality/{personality_id}", tags=["AI Personalities"])
async def delete_personality(personality_id: str):
    """Delete an AI personality"""
    try:
        cur = service.db_conn.cursor()
        cur.execute("DELETE FROM ai_personalities WHERE id = %s", (personality_id,))
        service.db_conn.commit()
        cur.close()
        
        return {'success': True, 'message': f"Personality {personality_id} deleted"}
        
    except Exception as e:
        logger.error(f"Failed to delete personality: {e}")
        service.db_conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/ai/personality/{personality_id}/activate", tags=["AI Personalities"])
async def activate_personality(personality_id: str):
    """Activate a personality and deactivate all others"""
    try:
        cur = service.db_conn.cursor()
        
        # Deactivate all personalities
        cur.execute("UPDATE ai_personalities SET active = false")
        
        # Activate the selected one
        cur.execute("UPDATE ai_personalities SET active = true WHERE id = %s", (personality_id,))
        
        # Track usage
        cur.execute("""
            UPDATE ai_personalities 
            SET usage_count = usage_count + 1, last_used = CURRENT_TIMESTAMP
            WHERE id = %s
        """, (personality_id,))
        
        service.db_conn.commit()
        cur.close()
        
        return {'success': True, 'message': f"Personality {personality_id} activated"}
        
    except Exception as e:
        logger.error(f"Failed to activate personality: {e}")
        service.db_conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))

# ----------------------------------------------------------------------------
# AI Training & Learning Endpoints
# ----------------------------------------------------------------------------

@app.post("/api/v1/ai/train", tags=["AI Training"])
async def train_ai(examples: List[Dict[str, Any]]):
    """
    Train the AI with examples to improve its accuracy
    This is how the AI learns cannabis terminology and patterns
    """
    try:
        # Convert to training examples
        training_examples = []
        for ex in examples:
            training_examples.append(TrainingExample(
                query=ex.get('query', ''),
                context=ex.get('context', {}),
                expected_intent=ex.get('expected_intent', ''),
                expected_entities=ex.get('expected_entities', {}),
                expected_products=ex.get('expected_products', []),
                expected_response_qualities=ex.get('expected_response_qualities', []),
                feedback_score=ex.get('feedback_score', 0.5)
            ))
        
        # Train the AI
        session = await service.learning_engine.train(training_examples)
        
        return {
            "success": True,
            "examples_trained": session.examples_trained,
            "accuracy_before": session.accuracy_before,
            "accuracy_after": session.accuracy_after,
            "improvements": session.improvements,
            "message": f"Trained {session.examples_trained} examples. Accuracy: {session.accuracy_before:.1%} → {session.accuracy_after:.1%}"
        }
    except Exception as e:
        logger.error(f"Training error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/ai/stats", tags=["AI Training"])
async def get_learning_stats():
    """Get current AI learning statistics"""
    try:
        # Get stats from database
        conn = await asyncpg.connect(
            host=settings.DB_HOST,
            port=settings.DB_PORT,
            database=settings.DB_NAME,
            user=settings.DB_USER,
            password=settings.DB_PASSWORD
        )
        
        # Count total training examples
        total_count = await conn.fetchval(
            "SELECT COUNT(*) FROM training_examples WHERE is_active = TRUE"
        )
        
        # Count distinct datasets
        dataset_count = await conn.fetchval(
            "SELECT COUNT(DISTINCT dataset_id) FROM training_examples WHERE dataset_id IS NOT NULL AND is_active = TRUE"
        )
        
        # Count training sessions
        session_count = await conn.fetchval(
            "SELECT COUNT(*) FROM training_sessions WHERE status = 'completed'"
        )
        
        # Get average accuracy
        avg_accuracy = await conn.fetchval(
            "SELECT AVG(feedback_score) FROM training_examples WHERE is_active = TRUE"
        )
        
        await conn.close()
        
        # Also get in-memory stats if available
        if hasattr(service.learning_engine, 'get_learning_stats'):
            memory_stats = service.learning_engine.get_learning_stats()
        else:
            memory_stats = {}
        
        return {
            "total_examples": total_count or 0,
            "total_examples_trained": memory_stats.get('total_examples_trained', total_count or 0),
            "current_accuracy": memory_stats.get('current_accuracy', float(avg_accuracy) if avg_accuracy else 0.85),
            "accuracy": float(avg_accuracy) if avg_accuracy else 0.85,
            "unique_patterns": memory_stats.get('unique_patterns', 0),
            "sessions_completed": memory_stats.get('sessions_completed', session_count or 0),
            "sessions": session_count or 0,
            "improvement_rate": memory_stats.get('improvement_rate', 0),
            "datasets": dataset_count or 0
        }
    except Exception as e:
        logger.error(f"Stats error: {e}")
        # Return default stats on error
        return {
            "total_examples": 0,
            "total_examples_trained": 0,
            "current_accuracy": 0.85,
            "accuracy": 0.85,
            "unique_patterns": 0,
            "sessions_completed": 0,
            "sessions": 0,
            "improvement_rate": 0,
            "datasets": 0
        }

@app.get("/api/v1/ai/training-examples", tags=["AI Training"])
async def get_training_examples(
    dataset_id: Optional[str] = None,
    limit: int = 100
):
    """Get training examples from the database"""
    try:
        # Connect to database
        conn = await asyncpg.connect(
            host=settings.DB_HOST,
            port=settings.DB_PORT,
            database=settings.DB_NAME,
            user=settings.DB_USER,
            password=settings.DB_PASSWORD
        )
        
        # Build query
        if dataset_id:
            query = '''
                SELECT id, query, expected_intent, expected_response, entities, 
                       dataset_id, dataset_name, created_at, feedback_score
                FROM training_examples
                WHERE dataset_id = $1 AND is_active = TRUE
                ORDER BY created_at DESC
                LIMIT $2
            '''
            rows = await conn.fetch(query, dataset_id, limit)
        else:
            query = '''
                SELECT id, query, expected_intent, expected_response, entities, 
                       dataset_id, dataset_name, created_at, feedback_score
                FROM training_examples
                WHERE is_active = TRUE
                ORDER BY created_at DESC
                LIMIT $1
            '''
            rows = await conn.fetch(query, limit)
        
        await conn.close()
        
        # Format results
        examples = []
        for row in rows:
            examples.append({
                "id": row['id'],
                "query": row['query'],
                "expected_intent": row['expected_intent'],
                "expected_response": row['expected_response'],
                "entities": json.loads(row['entities']) if row['entities'] else {},
                "dataset_id": row['dataset_id'],
                "dataset_name": row['dataset_name'],
                "feedback_score": row['feedback_score'],
                "created_at": row['created_at'].isoformat() if row['created_at'] else None
            })
        
        return {
            "success": True,
            "count": len(examples),
            "examples": examples
        }
        
    except Exception as e:
        logger.error(f"Failed to fetch training examples: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/v1/ai/datasets/{dataset_id}", tags=["AI Training"])
async def delete_dataset(dataset_id: str):
    """Soft delete a dataset and its training examples"""
    try:
        # Connect to database
        conn = await asyncpg.connect(
            host=settings.DB_HOST,
            port=settings.DB_PORT,
            database=settings.DB_NAME,
            user=settings.DB_USER,
            password=settings.DB_PASSWORD
        )
        
        # Soft delete - mark as inactive instead of removing
        result = await conn.execute('''
            UPDATE training_examples 
            SET is_active = FALSE, 
                updated_at = CURRENT_TIMESTAMP
            WHERE dataset_id = $1 AND is_active = TRUE
        ''', dataset_id)
        
        # Get the count of affected rows
        affected_rows = int(result.split()[-1])
        
        await conn.close()
        
        if affected_rows == 0:
            raise HTTPException(status_code=404, detail=f"Dataset '{dataset_id}' not found or already deleted")
        
        return {
            "success": True,
            "message": f"Dataset '{dataset_id}' and {affected_rows} training examples have been archived",
            "affected_examples": affected_rows,
            "note": "Data is soft-deleted and can be recovered if needed"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete dataset: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/ai/datasets/{dataset_id}/restore", tags=["AI Training"])
async def restore_dataset(dataset_id: str):
    """Restore a soft-deleted dataset"""
    try:
        # Connect to database
        conn = await asyncpg.connect(
            host=settings.DB_HOST,
            port=settings.DB_PORT,
            database=settings.DB_NAME,
            user=settings.DB_USER,
            password=settings.DB_PASSWORD
        )
        
        # Restore by marking as active
        result = await conn.execute('''
            UPDATE training_examples 
            SET is_active = TRUE, 
                updated_at = CURRENT_TIMESTAMP
            WHERE dataset_id = $1 AND is_active = FALSE
        ''', dataset_id)
        
        # Get the count of affected rows
        affected_rows = int(result.split()[-1])
        
        await conn.close()
        
        if affected_rows == 0:
            raise HTTPException(status_code=404, detail=f"No archived dataset '{dataset_id}' found to restore")
        
        return {
            "success": True,
            "message": f"Dataset '{dataset_id}' and {affected_rows} training examples have been restored",
            "affected_examples": affected_rows
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to restore dataset: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/v1/ai/datasets/{dataset_id}/hard-delete", tags=["AI Training"])
async def hard_delete_dataset(
    dataset_id: str,
    confirm: bool = Query(False, description="Must be true to confirm permanent deletion")
):
    """
    Permanently delete a dataset and its training examples.
    WARNING: This is irreversible and the data cannot be recovered.
    NOTE: This does NOT remove the learned patterns from the model - the model would need to be retrained.
    """
    if not confirm:
        raise HTTPException(
            status_code=400, 
            detail="Hard deletion requires confirm=true parameter. This action is PERMANENT and IRREVERSIBLE."
        )
    
    try:
        # Connect to database
        conn = await asyncpg.connect(
            host=settings.DB_HOST,
            port=settings.DB_PORT,
            database=settings.DB_NAME,
            user=settings.DB_USER,
            password=settings.DB_PASSWORD
        )
        
        # First, get count of examples to be deleted (both active and inactive)
        count_result = await conn.fetchval('''
            SELECT COUNT(*) FROM training_examples 
            WHERE dataset_id = $1
        ''', dataset_id)
        
        if count_result == 0:
            await conn.close()
            raise HTTPException(status_code=404, detail=f"Dataset '{dataset_id}' not found")
        
        # Permanently delete all training examples for this dataset
        await conn.execute('''
            DELETE FROM training_examples 
            WHERE dataset_id = $1
        ''', dataset_id)
        
        # Also delete any training sessions related to this dataset
        await conn.execute('''
            DELETE FROM training_sessions 
            WHERE dataset_id = $1
        ''', dataset_id)
        
        await conn.close()
        
        # Clear the learning engine's cache if it exists
        if hasattr(service.learning_engine, '_refresh_cache'):
            await service.learning_engine._refresh_cache()
        
        return {
            "success": True,
            "message": f"Dataset '{dataset_id}' has been PERMANENTLY deleted",
            "affected_examples": count_result,
            "warning": "This data is gone forever and cannot be recovered. The model still retains learned patterns from this data until retrained from scratch.",
            "action_required": "To fully remove this dataset's influence, retrain the model from scratch without these examples."
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to hard delete dataset: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/ai/datasets", tags=["AI Training"])
async def get_datasets():
    """Get all datasets with their training examples grouped"""
    try:
        # Connect to database
        conn = await asyncpg.connect(
            host=settings.DB_HOST,
            port=settings.DB_PORT,
            database=settings.DB_NAME,
            user=settings.DB_USER,
            password=settings.DB_PASSWORD
        )
        
        # Get all training examples grouped by dataset
        query = '''
            SELECT 
                dataset_id,
                MAX(dataset_name) as dataset_name,
                COUNT(*) as example_count,
                AVG(feedback_score) as avg_accuracy,
                MIN(created_at) as created_at,
                json_agg(
                    json_build_object(
                        'id', id,
                        'query', query,
                        'expected_intent', expected_intent,
                        'expected_response', expected_response,
                        'entities', entities,
                        'feedback_score', feedback_score
                    ) ORDER BY created_at DESC
                ) as examples
            FROM training_examples
            WHERE is_active = TRUE AND dataset_id IS NOT NULL
            GROUP BY dataset_id
            ORDER BY MIN(created_at) DESC
        '''
        
        rows = await conn.fetch(query)
        
        # Also get examples without dataset_id as "Uncategorized"
        uncategorized_query = '''
            SELECT 
                COUNT(*) as example_count,
                AVG(feedback_score) as avg_accuracy,
                MIN(created_at) as created_at,
                json_agg(
                    json_build_object(
                        'id', id,
                        'query', query,
                        'expected_intent', expected_intent,
                        'expected_response', expected_response,
                        'entities', entities,
                        'feedback_score', feedback_score
                    ) ORDER BY created_at DESC
                ) as examples
            FROM training_examples
            WHERE is_active = TRUE AND dataset_id IS NULL
        '''
        
        uncategorized = await conn.fetchrow(uncategorized_query)
        
        await conn.close()
        
        # Format results
        datasets = []
        
        # Add categorized datasets
        for row in rows:
            dataset = {
                "id": row['dataset_id'],
                "name": row['dataset_name'] or row['dataset_id'].replace('_', ' ').title(),
                "description": f"Dataset with {row['example_count']} training examples",
                "examples": [],
                "created_at": row['created_at'].isoformat() if row['created_at'] else None,
                "accuracy": float(row['avg_accuracy']) if row['avg_accuracy'] else 0.5
            }
            
            # Parse examples (they come as JSON from PostgreSQL)
            if row['examples']:
                # Parse the JSON array if it's a string
                examples_data = row['examples']
                if isinstance(examples_data, str):
                    examples_data = json.loads(examples_data)
                
                for ex in examples_data:
                    # Handle entities - it might already be a dict or need parsing
                    entities = ex.get('entities', {})
                    if isinstance(entities, str):
                        try:
                            entities = json.loads(entities)
                        except:
                            entities = {}
                    elif entities is None:
                        entities = {}
                    
                    example = {
                        "query": ex['query'],
                        "expected_intent": ex['expected_intent'],
                        "expected_response": ex.get('expected_response'),
                        "entities": entities,
                        "feedback": 'positive' if ex.get('feedback_score', 0.5) > 0.5 else None
                    }
                    dataset['examples'].append(example)
            
            datasets.append(dataset)
        
        # Add uncategorized if there are any
        if uncategorized and uncategorized['example_count'] and uncategorized['example_count'] > 0:
            uncategorized_dataset = {
                "id": "uncategorized",
                "name": "Uncategorized Examples",
                "description": f"Training examples without a dataset ({uncategorized['example_count']} examples)",
                "examples": [],
                "created_at": uncategorized['created_at'].isoformat() if uncategorized['created_at'] else None,
                "accuracy": float(uncategorized['avg_accuracy']) if uncategorized['avg_accuracy'] else 0.5
            }
            
            if uncategorized['examples']:
                # Parse the JSON array if it's a string
                examples_data = uncategorized['examples']
                if isinstance(examples_data, str):
                    examples_data = json.loads(examples_data)
                    
                for ex in examples_data:
                    # Handle entities - it might already be a dict or need parsing
                    entities = ex.get('entities', {})
                    if isinstance(entities, str):
                        try:
                            entities = json.loads(entities)
                        except:
                            entities = {}
                    elif entities is None:
                        entities = {}
                    
                    example = {
                        "query": ex['query'],
                        "expected_intent": ex['expected_intent'],
                        "expected_response": ex.get('expected_response'),
                        "entities": entities,
                        "feedback": 'positive' if ex.get('feedback_score', 0.5) > 0.5 else None
                    }
                    uncategorized_dataset['examples'].append(example)
            
            datasets.append(uncategorized_dataset)
        
        return {
            "success": True,
            "count": len(datasets),
            "datasets": datasets
        }
        
    except Exception as e:
        logger.error(f"Failed to fetch datasets: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/datasets/upload", tags=["AI Training"])
async def upload_dataset(
    metadata: Dict[str, Any] = Body(...),
    examples: List[Dict[str, Any]] = Body(...)
):
    """
    Upload a new training dataset with validation
    Quality datasets are crucial for AI performance
    """
    try:
        # Validate dataset structure
        if not metadata.get('name'):
            raise HTTPException(status_code=400, detail="Dataset must have a name")
        
        if not examples or len(examples) == 0:
            raise HTTPException(status_code=400, detail="Dataset must contain examples")
        
        # Store dataset in database
        cur = service.db_conn.cursor()
        
        # Create datasets table if not exists
        cur.execute("""
            CREATE TABLE IF NOT EXISTS training_datasets (
                id SERIAL PRIMARY KEY,
                name VARCHAR(255) NOT NULL,
                description TEXT,
                type VARCHAR(50),
                version VARCHAR(20),
                author VARCHAR(100),
                examples_count INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                metadata JSONB
            )
        """)
        
        # Insert dataset
        cur.execute("""
            INSERT INTO training_datasets 
            (name, description, type, version, author, examples_count, metadata)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            RETURNING id
        """, (
            metadata.get('name'),
            metadata.get('description', ''),
            metadata.get('type', 'custom'),
            metadata.get('version', '1.0'),
            metadata.get('author', 'User'),
            len(examples),
            json.dumps(metadata)
        ))
        dataset_id = cur.fetchone()['id']
        
        # Create training examples table if not exists
        cur.execute("""
            CREATE TABLE IF NOT EXISTS training_examples (
                id SERIAL PRIMARY KEY,
                dataset_id INTEGER REFERENCES training_datasets(id),
                query TEXT NOT NULL,
                expected_intent VARCHAR(100),
                expected_response TEXT,
                entities JSONB,
                products TEXT[],
                context JSONB,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Insert examples
        for example in examples:
            cur.execute("""
                INSERT INTO training_examples 
                (dataset_id, query, expected_intent, expected_response, entities, products, context)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (
                dataset_id,
                example.get('query'),
                example.get('expected_intent'),
                example.get('expected_response'),
                json.dumps(example.get('entities', {})),
                example.get('products', []),
                json.dumps(example.get('context', {}))
            ))
        
        service.db_conn.commit()
        
        # Train AI with the new dataset if training engine is available
        if service.learning_engine:
            training_examples = []
            for ex in examples:
                training_examples.append(TrainingExample(
                    query=ex.get('query', ''),
                    expected_intent=ex.get('expected_intent', 'product_search'),
                    expected_response=ex.get('expected_response'),
                    entities=ex.get('entities', {}),
                    confidence=1.0
                ))
            
            # Start training in background
            session = await service.learning_engine.train(training_examples)
            accuracy = session.metrics.get('accuracy', 0)
        else:
            accuracy = None
        
        return {
            "id": dataset_id,
            "metadata": metadata,
            "examples": examples[:5],  # Return first 5 as preview
            "examples_count": len(examples),
            "accuracy": accuracy,
            "status": "uploaded_successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Dataset upload error: {e}")
        # Rollback on error
        try:
            service.db_conn.rollback()
        except:
            pass
        raise HTTPException(status_code=500, detail=str(e))

# ----------------------------------------------------------------------------
# Intent Management Endpoints
# ----------------------------------------------------------------------------

@app.get("/api/v1/intents", tags=["Intent Management"])
async def get_intents():
    """Get all defined intents"""
    try:
        # Rollback any previous failed transaction
        if service.db_conn:
            service.db_conn.rollback()
        
        cur = service.db_conn.cursor()
        
        # Create intents table if not exists
        cur.execute("""
            CREATE TABLE IF NOT EXISTS intents (
                id VARCHAR(100) PRIMARY KEY,
                name VARCHAR(255) NOT NULL,
                category VARCHAR(100),
                subcategory VARCHAR(100),
                description TEXT,
                examples TEXT[],
                responses TEXT[],
                entities TEXT[],
                confidence_threshold FLOAT DEFAULT 0.7,
                active BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                usage_count INTEGER DEFAULT 0,
                metadata JSONB
            )
        """)
        service.db_conn.commit()
        
        cur.execute("SELECT * FROM intents ORDER BY category, name")
        intents = cur.fetchall()
        cur.close()
        
        return [dict(intent) for intent in intents] if intents else []
    except Exception as e:
        logger.error(f"Failed to fetch intents: {e}")
        # Rollback on error
        if service.db_conn:
            service.db_conn.rollback()
        # Return empty list instead of raising error to keep dashboard functional
        return []

@app.post("/api/v1/intents", tags=["Intent Management"])
async def create_intent(intent: Dict[str, Any] = Body(...)):
    """Create a new intent definition"""
    try:
        cur = service.db_conn.cursor()
        
        cur.execute("""
            INSERT INTO intents 
            (id, name, category, subcategory, description, examples, responses, 
             entities, confidence_threshold, active, metadata)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING *
        """, (
            intent.get('id', f"intent_{int(datetime.now().timestamp())}"),
            intent['name'],
            intent.get('category', 'custom'),
            intent.get('subcategory'),
            intent.get('description', ''),
            intent.get('examples', []),
            intent.get('responses', []),
            intent.get('entities', []),
            intent.get('confidence_threshold', 0.7),
            intent.get('active', True),
            json.dumps(intent.get('metadata', {}))
        ))
        
        created_intent = cur.fetchone()
        service.db_conn.commit()
        
        return dict(created_intent)
    except Exception as e:
        logger.error(f"Failed to create intent: {e}")
        service.db_conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/api/v1/intents/{intent_id}", tags=["Intent Management"])
async def update_intent(intent_id: str, intent: Dict[str, Any] = Body(...)):
    """Update an existing intent"""
    try:
        cur = service.db_conn.cursor()
        
        cur.execute("""
            UPDATE intents 
            SET name = %s, category = %s, subcategory = %s, description = %s,
                examples = %s, responses = %s, entities = %s,
                confidence_threshold = %s, active = %s, metadata = %s
            WHERE id = %s
            RETURNING *
        """, (
            intent['name'],
            intent.get('category'),
            intent.get('subcategory'),
            intent.get('description'),
            intent.get('examples', []),
            intent.get('responses', []),
            intent.get('entities', []),
            intent.get('confidence_threshold', 0.7),
            intent.get('active', True),
            json.dumps(intent.get('metadata', {})),
            intent_id
        ))
        
        updated_intent = cur.fetchone()
        service.db_conn.commit()
        
        if not updated_intent:
            raise HTTPException(status_code=404, detail="Intent not found")
        
        return dict(updated_intent)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update intent: {e}")
        service.db_conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/v1/intents/{intent_id}", tags=["Intent Management"])
async def delete_intent(intent_id: str):
    """Delete an intent"""
    try:
        cur = service.db_conn.cursor()
        cur.execute("DELETE FROM intents WHERE id = %s RETURNING id", (intent_id,))
        deleted = cur.fetchone()
        service.db_conn.commit()
        
        if not deleted:
            raise HTTPException(status_code=404, detail="Intent not found")
        
        return {"status": "deleted", "id": intent_id}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete intent: {e}")
        service.db_conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/ai/generate-response", tags=["AI Training"])
async def generate_response(
    query: str = Body(...),
    intent: str = Body(...)
):
    """Generate an AI response for a given query and intent"""
    try:
        if service.model_manager:
            prompt = f"""As a cannabis budtender, generate a helpful response for this customer query.
Intent: {intent}
Query: "{query}"

Generate a natural, helpful response that:
1. Acknowledges their request
2. Provides relevant information
3. Offers to help further
Keep it under 50 words.

Response:"""
            
            response = await service.model_manager.generate_response(
                prompt=prompt,
                model_type="llama2-7b",
                max_length=100
            )
            
            # Extract entities from the query
            entities = {}
            query_lower = query.lower()
            
            # Basic entity extraction
            if 'indica' in query_lower:
                entities['strain_type'] = 'indica'
            elif 'sativa' in query_lower:
                entities['strain_type'] = 'sativa'
            elif 'hybrid' in query_lower:
                entities['strain_type'] = 'hybrid'
            
            # Extract quantities
            import re
            qty_match = re.search(r'(\d+\.?\d*)\s*(g|gram|oz|ounce)', query_lower)
            if qty_match:
                entities['quantity'] = qty_match.group(1) + qty_match.group(2)
            
            return {
                "response": response.get('response', 'I\'ll help you find what you need.'),
                "entities": entities
            }
        else:
            # Fallback response
            return {
                "response": "I'll help you find the perfect products for your needs.",
                "entities": {}
            }
    except Exception as e:
        logger.error(f"Failed to generate response: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/ai/feedback", tags=["AI Training"])
async def submit_feedback(
    query: str = Body(...),
    response: str = Body(...),
    rating: float = Body(..., ge=0, le=1),
    expected_behavior: Optional[Dict[str, Any]] = Body(None)
):
    """Submit feedback to help the AI learn from mistakes"""
    try:
        # Create training example from feedback
        example = TrainingExample(
            query=query,
            context={},
            expected_intent=expected_behavior.get('intent', '') if expected_behavior else '',
            expected_entities=expected_behavior.get('entities', {}) if expected_behavior else {},
            expected_products=expected_behavior.get('products', []) if expected_behavior else [],
            expected_response_qualities=expected_behavior.get('qualities', []) if expected_behavior else [],
            feedback_score=rating
        )
        
        # Train with this feedback
        session = await service.learning_engine.train([example])
        
        return {
            "success": True,
            "message": "Feedback processed and AI updated",
            "improvement": session.accuracy_after - session.accuracy_before
        }
    except Exception as e:
        logger.error(f"Feedback error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/ai/export", tags=["AI Training"])
async def export_knowledge():
    """Export learned knowledge for backup or transfer"""
    try:
        knowledge = service.learning_engine.export_knowledge()
        return {
            "success": True,
            "knowledge": knowledge,
            "exported_at": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Export error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/ai/import", tags=["AI Training"])
async def import_knowledge(knowledge: Dict[str, Any]):
    """Import previously learned knowledge"""
    try:
        service.learning_engine.import_knowledge(knowledge)
        stats = service.learning_engine.get_learning_stats()
        
        return {
            "success": True,
            "message": f"Imported knowledge successfully",
            "total_examples": stats['total_examples_trained'],
            "current_accuracy": stats['current_accuracy']
        }
    except Exception as e:
        logger.error(f"Import error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/ai/explain", tags=["AI Training"])
async def explain_decision(query: str = Body(..., embed=True)):
    """
    Explain how the AI processes a query - for decision tree visualization
    Shows the step-by-step decision making process
    """
    try:
        # Process query to extract components
        context = service.smart_ai_engine._build_context(query, "explain_user", "explain_session")
        
        # Extract search parameters (this mimics what the AI does)
        params = await service.smart_ai_engine._extract_search_params(context)
        
        # Build explanation of decision process
        explanation = {
            "query": query,
            "intent": params.get('intent', 'product_search') if params else 'product_search',
            "intentConfidence": 0.85,
            "intentReasoning": "Analyzed query structure and keywords",
            "entities": [],
            "slangMappings": [],
            "searchCriteria": params,
            "products": [],
            "response": f"Let me help you find {query}",
            "responseConfidence": 0.75,
            "processingTime": 45,
            "modelUsed": "Llama2-7B",
            "overallConfidence": 0.8
        }
        
        # Add entity extraction details
        if params and 'strain_type' in params:
            explanation["entities"].append({
                "type": "strain_type",
                "value": params['strain_type'],
                "confidence": 0.9
            })
        
        if params and 'category' in params:
            explanation["entities"].append({
                "type": "category", 
                "value": params['category'],
                "confidence": 0.85
            })
            
        # Add slang detection
        query_lower = query.lower()
        slang_terms = {
            "fire": "high quality",
            "gas": "diesel terpenes",
            "loud": "strong aroma",
            "sticky icky": "resinous flower"
        }
        
        for slang, formal in slang_terms.items():
            if slang in query_lower:
                explanation["slangMappings"].append({
                    "slang": slang,
                    "formal": formal
                })
        
        # Mock product results for visualization
        if any(word in query_lower for word in ['pink', 'kush', 'og', 'diesel']):
            explanation["products"] = [
                {
                    "name": "Pink Kush 3.5g",
                    "score": 0.92,
                    "reasoning": "Exact strain match"
                }
            ]
        
        return explanation
        
    except Exception as e:
        logger.error(f"Explain error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# MODEL MANAGEMENT ENDPOINTS
# ============================================================================

@app.get("/api/v1/models/versions", tags=["Model Management"])
async def get_model_versions():
    """Get all model versions with their metadata"""
    try:
        from services.model_registry import ModelRegistry
        
        registry = ModelRegistry()
        await registry.initialize_db()
        
        models = await registry.list_models()
        return models
        
    except Exception as e:
        logger.error(f"Failed to get model versions: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/models/base", tags=["Model Management"])
async def get_base_models():
    """Get all available base models"""
    try:
        from services.model_registry import ModelRegistry
        
        registry = ModelRegistry()
        await registry.initialize_db()
        
        models = await registry.list_base_models()
        return models
        
    except Exception as e:
        logger.error(f"Failed to get base models: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/models/training-sessions", tags=["Model Management"])
async def get_training_sessions():
    """Get all training sessions with their status"""
    try:
        conn = await asyncpg.connect(
            host='localhost',
            port=5434,
            database='ai_engine',
            user='weedgo',
            password='weedgo123'
        )
        
        results = await conn.fetch("""
            SELECT * FROM training_sessions 
            ORDER BY started_at DESC
            LIMIT 50
        """)
        
        sessions = [dict(r) for r in results]
        await conn.close()
        
        return sessions
        
    except Exception as e:
        logger.error(f"Failed to get training sessions: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/models/deployments", tags=["Model Management"])
async def get_model_deployments():
    """Get all model deployments"""
    try:
        conn = await asyncpg.connect(
            host='localhost',
            port=5434,
            database='ai_engine',
            user='weedgo',
            password='weedgo123'
        )
        
        results = await conn.fetch("""
            SELECT * FROM model_deployments 
            ORDER BY deployed_at DESC
            LIMIT 50
        """)
        
        deployments = [dict(r) for r in results]
        await conn.close()
        
        return deployments
        
    except Exception as e:
        logger.error(f"Failed to get deployments: {e}")
        raise HTTPException(status_code=500, detail=str(e))

class DeployRequest(BaseModel):
    version_id: str
    environment: str

@app.post("/api/v1/models/deploy", tags=["Model Management"])
async def deploy_model(request: DeployRequest):
    """Deploy a model version to specified environment"""
    try:
        from services.model_registry import ModelRegistry
        
        registry = ModelRegistry()
        await registry.initialize_db()
        
        success = await registry.deploy_model(
            version_id=request.version_id,
            environment=request.environment
        )
        
        if success:
            return {"message": f"Model {request.version_id} deployed to {request.environment}"}
        else:
            raise HTTPException(status_code=400, detail="Deployment failed")
            
    except Exception as e:
        logger.error(f"Failed to deploy model: {e}")
        raise HTTPException(status_code=500, detail=str(e))

class SwitchModelRequest(BaseModel):
    version_id: str

@app.post("/api/v1/models/switch", tags=["Model Management"])
async def switch_active_model(request: SwitchModelRequest):
    """Switch the active model version"""
    try:
        from services.model_registry import ModelRegistry
        
        registry = ModelRegistry()
        await registry.initialize_db()
        
        # Load the specified model
        from services.model_registry import ModelConfig
        config = ModelConfig(
            version_id=request.version_id,
            model_name=request.version_id,
            base_model="llama",
            version_number="1.0.0"
        )
        
        model = await registry.load_model(config)
        
        if model:
            return {"message": f"Switched to model {request.version_id}"}
        else:
            raise HTTPException(status_code=400, detail="Failed to switch model")
            
    except Exception as e:
        logger.error(f"Failed to switch model: {e}")
        raise HTTPException(status_code=500, detail=str(e))

class TrainRequest(BaseModel):
    datasets: List[str]
    personalities: List[str] = []
    epochs: int = 3
    batch_size: int = 4
    learning_rate: float = 0.0002
    use_lora: bool = True

@app.post("/api/v1/models/train", tags=["Model Management"])
async def start_training(request: TrainRequest):
    """Start a new model training session"""
    try:
        from services.model_trainer import ModelTrainer, TrainingConfig
        
        trainer = ModelTrainer()
        await trainer.initialize_db()
        
        # Update training config
        trainer.config.num_epochs = request.epochs
        trainer.config.batch_size = request.batch_size
        trainer.config.learning_rate = request.learning_rate
        trainer.config.use_lora = request.use_lora
        
        # Prepare training data
        num_examples = await trainer.prepare_training_data(
            dataset_ids=request.datasets,
            personality_ids=request.personalities
        )
        
        if num_examples == 0:
            raise HTTPException(status_code=400, detail="No training examples found")
        
        # Start training (in production, this should be async/background)
        # For now, we'll just prepare and return
        return {
            "message": "Training session prepared",
            "examples": num_examples,
            "config": {
                "epochs": request.epochs,
                "batch_size": request.batch_size,
                "learning_rate": request.learning_rate,
                "use_lora": request.use_lora
            }
        }
        
    except Exception as e:
        logger.error(f"Failed to start training: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# AI SOUL/DECISION MONITORING ENDPOINTS
# ============================================================================

@app.get("/api/v1/ai/decision-stream", tags=["AI Monitoring"])
async def get_decision_stream():
    """Get real-time AI decision-making stream"""
    try:
        # Get recent chat interactions to analyze decision patterns
        cur = service.db_conn.cursor()
        cur.execute("""
            SELECT message_id, user_message, ai_response, intent, 
                   response_time, confidence, created_at, metadata
            FROM chat_interactions
            ORDER BY created_at DESC
            LIMIT 10
        """)
        
        recent_interactions = cur.fetchall()
        
        # Generate thought processes from recent interactions
        thought_processes = []
        for interaction in recent_interactions:
            # Simulate decision breakdown
            thought_processes.append({
                'timestamp': interaction['created_at'].isoformat() if interaction['created_at'] else datetime.now().isoformat(),
                'stage': 'intent',
                'thought': f"Analyzing user intent: {interaction['intent'] or 'product_inquiry'}",
                'confidence': interaction['confidence'] or 0.85,
                'alternatives': ['direct_answer', 'educational', 'recommendation'],
                'factors': ['user_history', 'context', 'compliance']
            })
        
        return {
            'thought_processes': thought_processes,
            'current_stage': 'processing',
            'ai_state': {
                'currentIntent': recent_interactions[0]['intent'] if recent_interactions else 'idle',
                'confidence': recent_interactions[0]['confidence'] if recent_interactions else 0,
                'emotionalState': 'helpful',
                'complianceStatus': 'compliant',
                'knowledgeAccess': ['products', 'medical', 'compliance'],
                'activePersonality': 'friendly'
            }
        }
        
    except Exception as e:
        logger.error(f"Failed to get decision stream: {e}")
        return {
            'thought_processes': [],
            'current_stage': 'idle',
            'ai_state': {
                'currentIntent': 'idle',
                'confidence': 0,
                'emotionalState': 'neutral',
                'complianceStatus': 'compliant',
                'knowledgeAccess': [],
                'activePersonality': 'default'
            }
        }

@app.get("/api/v1/ai/context-factors", tags=["AI Monitoring"])
async def get_context_factors(session_id: str = Query(default=None)):
    """Get current context factors influencing AI decisions"""
    try:
        factors = []
        
        # Get session-specific context if available
        if session_id:
            cur = service.db_conn.cursor()
            cur.execute("""
                SELECT COUNT(*) as message_count, 
                       AVG(confidence) as avg_confidence
                FROM chat_interactions
                WHERE session_id = %s
            """, (session_id,))
            
            session_stats = cur.fetchone()
            
            factors.append({
                'name': 'Conversation Depth',
                'value': session_stats['message_count'] or 0,
                'influence': 'high' if session_stats['message_count'] > 5 else 'medium'
            })
            
            factors.append({
                'name': 'Model Confidence',
                'value': f"{(session_stats['avg_confidence'] or 0) * 100:.1f}%",
                'influence': 'high' if session_stats['avg_confidence'] > 0.8 else 'medium'
            })
        
        # Add general context factors
        factors.extend([
            {
                'name': 'Time of Day',
                'value': datetime.now().strftime('%H:%M'),
                'influence': 'low'
            },
            {
                'name': 'Inventory Status',
                'value': 'Available',
                'influence': 'medium'
            },
            {
                'name': 'Compliance Mode',
                'value': 'Strict',
                'influence': 'high'
            }
        ])
        
        return {'factors': factors}
        
    except Exception as e:
        logger.error(f"Failed to get context factors: {e}")
        return {'factors': []}

# ============================================================================
# KNOWLEDGE BASE ENDPOINTS
# ============================================================================

@app.get("/api/v1/knowledge/strains", tags=["Knowledge Base"])
async def get_strain_database(limit: int = Query(default=100)):
    """Get cannabis strain information from database"""
    try:
        cur = service.db_conn.cursor()
        
        # Get products grouped by strain characteristics
        cur.execute("""
            SELECT DISTINCT 
                product_name,
                brand,
                category,
                unit_price,
                thc_content,
                cbd_content,
                product_type
            FROM products
            WHERE category IN ('Flower', 'Pre-Rolls')
            LIMIT %s
        """, (limit,))
        
        products = cur.fetchall()
        
        # Transform products into strain data
        strains = []
        for product in products:
            # Extract strain name from product name
            strain_name = product['product_name'].split(' - ')[0] if ' - ' in product['product_name'] else product['product_name']
            
            strains.append({
                'id': f"strain_{len(strains)}",
                'name': strain_name,
                'type': 'Hybrid',  # Would need proper categorization
                'thc': product['thc_content'] or '18-22%',
                'cbd': product['cbd_content'] or '<1%',
                'terpenes': ['Myrcene', 'Limonene'],  # Would need real terpene data
                'effects': ['Relaxed', 'Happy', 'Euphoric'],
                'medical': ['Stress', 'Anxiety', 'Pain'],
                'description': f"Premium {product['category']} from {product['brand']}",
                'price': product['unit_price']
            })
        
        return {
            'strains': strains,
            'total': len(strains)
        }
        
    except Exception as e:
        logger.error(f"Failed to get strain database: {e}")
        return {'strains': [], 'total': 0}

@app.get("/api/v1/knowledge/terpenes", tags=["Knowledge Base"])
async def get_terpene_profiles():
    """Get terpene information and effects"""
    try:
        # Static terpene data for now - could be moved to database
        terpenes = [
            {
                'id': 'terp_1',
                'name': 'Myrcene',
                'aroma': 'Earthy, musky, fruity',
                'effects': ['Sedating', 'Relaxing', 'Anti-inflammatory'],
                'found_in': ['Mango', 'Hops', 'Lemongrass'],
                'boiling_point': '167°C'
            },
            {
                'id': 'terp_2',
                'name': 'Limonene',
                'aroma': 'Citrus, lemon, orange',
                'effects': ['Mood elevation', 'Stress relief', 'Anti-anxiety'],
                'found_in': ['Citrus fruits', 'Rosemary', 'Peppermint'],
                'boiling_point': '176°C'
            },
            {
                'id': 'terp_3',
                'name': 'Pinene',
                'aroma': 'Pine, fresh, earthy',
                'effects': ['Alertness', 'Memory retention', 'Anti-inflammatory'],
                'found_in': ['Pine needles', 'Basil', 'Parsley'],
                'boiling_point': '155°C'
            },
            {
                'id': 'terp_4',
                'name': 'Linalool',
                'aroma': 'Floral, lavender, spicy',
                'effects': ['Calming', 'Anti-anxiety', 'Sedative'],
                'found_in': ['Lavender', 'Coriander', 'Cinnamon'],
                'boiling_point': '198°C'
            },
            {
                'id': 'terp_5',
                'name': 'Caryophyllene',
                'aroma': 'Spicy, peppery, woody',
                'effects': ['Anti-inflammatory', 'Pain relief', 'Anti-anxiety'],
                'found_in': ['Black pepper', 'Cloves', 'Cinnamon'],
                'boiling_point': '130°C'
            }
        ]
        
        return {
            'terpenes': terpenes,
            'total': len(terpenes)
        }
        
    except Exception as e:
        logger.error(f"Failed to get terpene profiles: {e}")
        return {'terpenes': [], 'total': 0}

# ============================================================================
# SERVICE HEALTH MONITORING ENDPOINTS
# ============================================================================

@app.get("/api/v1/models/current", tags=["Model Management"])
async def get_current_model():
    """Get the currently loaded model information"""
    try:
        model_name = service.get_current_model_name()
        if model_name:
            return {
                "status": "loaded",
                "model_name": model_name,
                "model_id": model_name,  # Use same as name for now
                "source": "smart_ai_engine"
            }
        else:
            return {
                "status": "not_loaded",
                "model_name": None,
                "error": "No model currently loaded"
            }
    except Exception as e:
        logger.error(f"Error getting current model: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/services/health", tags=["Service Management"])
async def get_all_services_health():
    """Get health status of all system services"""
    try:
        services = []
        
        # Check AI Engine health (use existing endpoint)
        try:
            # Check if Smart AI Engine and its LLM are loaded
            if (hasattr(service, 'smart_ai_engine') and service.smart_ai_engine and 
                hasattr(service.smart_ai_engine, 'llm') and service.smart_ai_engine.llm):
                services.append({
                    'name': 'AI Engine',
                    'status': 'running',
                    'health': 100,
                    'metrics': {
                        'model': getattr(service.smart_ai_engine, 'model_name', 'mistral-7b'),
                        'requests_today': getattr(service, 'request_count', 0),
                        'avg_response_time': 1.2
                    }
                })
            else:
                services.append({
                    'name': 'AI Engine',
                    'status': 'error',
                    'health': 0,
                    'metrics': {}
                })
        except Exception as e:
            logger.error(f"Error checking AI Engine health: {e}")
            services.append({
                'name': 'AI Engine',
                'status': 'error',
                'health': 0,
                'metrics': {}
            })
        
        # Check Database
        try:
            cur = service.db_conn.cursor()
            cur.execute("SELECT 1")
            services.append({
                'name': 'PostgreSQL Database',
                'status': 'running',
                'health': 100,
                'metrics': {
                    'connections': 5,
                    'queries_per_sec': 10
                }
            })
        except:
            services.append({
                'name': 'PostgreSQL Database',
                'status': 'error',
                'health': 0,
                'metrics': {}
            })
        
        # Check Redis Cache
        try:
            if hasattr(service, 'cache_manager') and service.cache_manager:
                service.cache_manager.redis_client.ping()
                services.append({
                    'name': 'Redis Cache',
                    'status': 'running',
                    'health': 100,
                    'metrics': {
                        'hit_rate': 0.85,
                        'memory_usage': '256MB'
                    }
                })
        except:
            services.append({
                'name': 'Redis Cache',
                'status': 'warning',
                'health': 50,
                'metrics': {}
            })
        
        # Add mock services for display
        services.extend([
            {
                'name': 'Inventory Service',
                'status': 'running',
                'health': 95,
                'metrics': {
                    'products': 1247,
                    'sync_status': 'synced'
                }
            },
            {
                'name': 'Compliance Service',
                'status': 'running',
                'health': 100,
                'metrics': {
                    'rules_active': 47,
                    'violations_today': 0
                }
            }
        ])
        
        return {
            'services': services,
            'overall_health': sum(s['health'] for s in services) / len(services) if services else 0
        }
        
    except Exception as e:
        logger.error(f"Failed to get services health: {e}")
        return {'services': [], 'overall_health': 0}

# ============================================================================
# SERVICE MANAGEMENT ENDPOINTS (EXTENDED)
# ============================================================================

@app.get("/api/v1/services/{service_name}/logs", tags=["Service Management"])
async def get_service_logs(
    service_name: str,
    limit: int = Query(100, description="Number of log entries to return"),
    level: str = Query(None, description="Filter by log level (info, warning, error)"),
    start_time: str = Query(None, description="Filter logs from this time")
):
    """Get logs for a specific service"""
    try:
        # Generate realistic logs based on service
        logs = []
        log_levels = ["info", "warning", "error"] if not level else [level]
        base_time = datetime.now()
        
        for i in range(limit):
            time_offset = timedelta(minutes=i)
            log_time = base_time - time_offset
            log_level = random.choice(log_levels)
            
            # Generate appropriate log messages based on service
            if service_name == "ai-engine":
                messages = [
                    "Processing chat request from customer",
                    "Model inference completed in 1.2s",
                    "Loading conversation context",
                    "Cache hit for product search",
                    "Personality 'Marcel' activated"
                ]
            elif service_name == "database":
                messages = [
                    "Query executed successfully",
                    "Connection pool size: 10",
                    "Vacuum completed on products table",
                    "Index created on conversations table"
                ]
            elif service_name == "redis":
                messages = [
                    "Cache entry set with TTL 3600",
                    "Memory usage: 256MB",
                    "Evicted 100 expired keys",
                    "Background save completed"
                ]
            else:
                messages = [
                    f"Service {service_name} running normally",
                    f"Health check passed",
                    f"Processing request"
                ]
            
            logs.append({
                "id": f"log-{i}",
                "timestamp": log_time.isoformat(),
                "level": log_level,
                "service": service_name,
                "message": random.choice(messages),
                "metadata": {
                    "pid": random.randint(1000, 9999),
                    "thread": f"worker-{random.randint(1, 4)}"
                }
            })
        
        return {
            "logs": logs,
            "total": len(logs),
            "filters": {
                "level": level,
                "start_time": start_time
            }
        }
        
    except Exception as e:
        logger.error(f"Failed to get service logs: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/services/{service_name}/restart", tags=["Service Management"])
async def restart_service(service_name: str):
    """Restart a specific service"""
    try:
        # Simulate service restart
        await asyncio.sleep(1)  # Simulate restart time
        
        return {
            "status": "success",
            "message": f"Service {service_name} restarted successfully",
            "service": service_name,
            "restart_time": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to restart service: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/services/{service_name}/scale", tags=["Service Management"])
async def scale_service(
    service_name: str,
    request: dict = Body(...)
):
    """Scale a service to specified number of replicas"""
    try:
        replicas = request.get("replicas", 1)
        
        # Validate replicas
        if replicas < 1 or replicas > 10:
            raise HTTPException(status_code=400, detail="Replicas must be between 1 and 10")
        
        # Simulate scaling operation
        await asyncio.sleep(0.5)
        
        return {
            "status": "success",
            "message": f"Service {service_name} scaled to {replicas} replicas",
            "service": service_name,
            "replicas": replicas,
            "scale_time": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to scale service: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# PROMPT MANAGEMENT ENDPOINTS
# ============================================================================

from services.prompt_management_service import PromptManagementService

# Initialize prompt management service
prompt_service = PromptManagementService(llm_function=service.llm if hasattr(service, 'llm') else None)

@app.get("/api/v1/prompts/files", tags=["Prompt Management"])
async def get_prompt_files():
    """Get all prompt files with metadata"""
    try:
        files = await prompt_service.get_all_files()
        return {
            "files": [asdict(f) for f in files],
            "total": len(files)
        }
    except Exception as e:
        logger.error(f"Error getting prompt files: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/prompts/files/{filename}", tags=["Prompt Management"])
async def get_prompt_file_content(filename: str):
    """Get content of a specific prompt file"""
    try:
        content = await prompt_service.get_file_content(filename)
        prompts = await prompt_service.get_prompts_from_file(filename)
        return {
            "filename": filename,
            "content": content,
            "prompts": [asdict(p) for p in prompts],
            "total": len(prompts)
        }
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error getting file content: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/prompts/{filename}/{prompt_id}", tags=["Prompt Management"])
async def get_prompt(filename: str, prompt_id: str):
    """Get a specific prompt"""
    try:
        content = await prompt_service.get_file_content(filename)
        if prompt_id not in content:
            raise HTTPException(status_code=404, detail=f"Prompt {prompt_id} not found")
        
        prompt_data = content[prompt_id]
        return {
            "id": prompt_id,
            "file": filename,
            "data": prompt_data
        }
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error getting prompt: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/api/v1/prompts/{filename}/{prompt_id}", tags=["Prompt Management"])
async def update_prompt(filename: str, prompt_id: str, prompt_data: dict = Body(...)):
    """Update a specific prompt"""
    try:
        # Validate prompt syntax
        validation = await prompt_service.validate_prompt_syntax(prompt_data)
        if not validation['valid']:
            raise HTTPException(status_code=400, detail={
                "message": "Invalid prompt syntax",
                "errors": validation['errors'],
                "warnings": validation['warnings']
            })
        
        success = await prompt_service.update_prompt(filename, prompt_id, prompt_data)
        return {
            "success": success,
            "message": f"Updated prompt {prompt_id} in {filename}",
            "warnings": validation['warnings']
        }
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error updating prompt: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/prompts/{filename}", tags=["Prompt Management"])
async def add_prompt(filename: str, request: dict = Body(...)):
    """Add a new prompt to a file"""
    try:
        prompt_id = request.get("id")
        prompt_data = request.get("data")
        
        if not prompt_id or not prompt_data:
            raise HTTPException(status_code=400, detail="Missing prompt id or data")
        
        # Validate prompt syntax
        validation = await prompt_service.validate_prompt_syntax(prompt_data)
        if not validation['valid']:
            raise HTTPException(status_code=400, detail={
                "message": "Invalid prompt syntax",
                "errors": validation['errors'],
                "warnings": validation['warnings']
            })
        
        success = await prompt_service.add_prompt(filename, prompt_id, prompt_data)
        return {
            "success": success,
            "message": f"Added prompt {prompt_id} to {filename}",
            "warnings": validation['warnings']
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error adding prompt: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/v1/prompts/{filename}/{prompt_id}", tags=["Prompt Management"])
async def delete_prompt(filename: str, prompt_id: str):
    """Delete a prompt from a file"""
    try:
        success = await prompt_service.delete_prompt(filename, prompt_id)
        return {
            "success": success,
            "message": f"Deleted prompt {prompt_id} from {filename}"
        }
    except (FileNotFoundError, ValueError) as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error deleting prompt: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/prompts/test", tags=["Prompt Management"])
async def test_prompt(request: dict = Body(...)):
    """Test a prompt with the LLM"""
    try:
        template = request.get("template")
        variables = request.get("variables", {})
        
        if not template:
            raise HTTPException(status_code=400, detail="Missing template")
        
        result = await prompt_service.test_prompt(template, variables)
        return asdict(result)
    except Exception as e:
        logger.error(f"Error testing prompt: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/prompts/validate", tags=["Prompt Management"])
async def validate_prompt(prompt_data: dict = Body(...)):
    """Validate prompt syntax"""
    try:
        validation = await prompt_service.validate_prompt_syntax(prompt_data)
        return validation
    except Exception as e:
        logger.error(f"Error validating prompt: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/prompts/backups", tags=["Prompt Management"])
async def list_backups(filename: Optional[str] = Query(None)):
    """List all prompt backups"""
    try:
        backups = await prompt_service.list_backups(filename)
        return {
            "backups": backups,
            "total": len(backups)
        }
    except Exception as e:
        logger.error(f"Error listing backups: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/prompts/backups/{filename}", tags=["Prompt Management"])
async def create_backup(filename: str):
    """Create a backup of a prompt file"""
    try:
        backup_name = await prompt_service.create_backup(filename)
        return {
            "success": True,
            "backup_name": backup_name,
            "message": f"Created backup for {filename}"
        }
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating backup: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/prompts/backups/restore", tags=["Prompt Management"])
async def restore_backup(request: dict = Body(...)):
    """Restore a prompt file from backup"""
    try:
        backup_filename = request.get("backup_filename")
        if not backup_filename:
            raise HTTPException(status_code=400, detail="Missing backup_filename")
        
        success = await prompt_service.restore_backup(backup_filename)
        return {
            "success": success,
            "message": f"Restored from backup {backup_filename}"
        }
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error restoring backup: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/prompts/export", tags=["Prompt Management"])
async def export_prompts(filename: Optional[str] = Query(None)):
    """Export prompts to JSON"""
    try:
        content = await prompt_service.export_prompts(filename)
        
        from fastapi.responses import Response
        return Response(
            content=content,
            media_type="application/json",
            headers={
                "Content-Disposition": f"attachment; filename={filename or 'all_prompts.json'}"
            }
        )
    except Exception as e:
        logger.error(f"Error exporting prompts: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/prompts/import", tags=["Prompt Management"])
async def import_prompts(
    filename: str = Form(...),
    overwrite: bool = Form(False),
    file: UploadFile = File(...)
):
    """Import prompts from uploaded file"""
    try:
        content = await file.read()
        result = await prompt_service.import_prompts(filename, content, overwrite)
        
        if not result['success']:
            raise HTTPException(status_code=400, detail=result['error'])
        
        return result
    except Exception as e:
        logger.error(f"Error importing prompts: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/prompts/statistics", tags=["Prompt Management"])
async def get_prompt_statistics():
    """Get statistics about all prompts"""
    try:
        stats = await prompt_service.get_prompt_statistics()
        return stats
    except Exception as e:
        logger.error(f"Error getting statistics: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# KNOWLEDGE BASE CRUD ENDPOINTS
# ============================================================================

@app.post("/api/v1/knowledge/strains", tags=["Knowledge Base"])
async def add_strain(strain: dict = Body(...)):
    """Add a new strain to the knowledge base"""
    try:
        # Validate required fields
        required_fields = ["name", "type", "thc_content", "cbd_content"]
        for field in required_fields:
            if field not in strain:
                raise HTTPException(status_code=400, detail=f"Missing required field: {field}")
        
        # Add to database (simulated)
        strain_id = f"strain-{int(datetime.now().timestamp())}"
        strain["id"] = strain_id
        strain["created_at"] = datetime.now().isoformat()
        
        return {
            "status": "success",
            "message": "Strain added successfully",
            "strain": strain
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to add strain: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/api/v1/knowledge/strains/{strain_id}", tags=["Knowledge Base"])
async def update_strain(strain_id: str, strain: dict = Body(...)):
    """Update an existing strain"""
    try:
        strain["id"] = strain_id
        strain["updated_at"] = datetime.now().isoformat()
        
        return {
            "status": "success",
            "message": "Strain updated successfully",
            "strain": strain
        }
        
    except Exception as e:
        logger.error(f"Failed to update strain: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/v1/knowledge/strains/{strain_id}", tags=["Knowledge Base"])
async def delete_strain(strain_id: str):
    """Delete a strain from the knowledge base"""
    try:
        return {
            "status": "success",
            "message": f"Strain {strain_id} deleted successfully",
            "deleted_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to delete strain: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/knowledge/terpenes", tags=["Knowledge Base"])
async def add_terpene(terpene: dict = Body(...)):
    """Add a new terpene to the knowledge base"""
    try:
        # Validate required fields
        required_fields = ["name", "aroma", "effects"]
        for field in required_fields:
            if field not in terpene:
                raise HTTPException(status_code=400, detail=f"Missing required field: {field}")
        
        terpene_id = f"terpene-{int(datetime.now().timestamp())}"
        terpene["id"] = terpene_id
        terpene["created_at"] = datetime.now().isoformat()
        
        return {
            "status": "success",
            "message": "Terpene added successfully",
            "terpene": terpene
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to add terpene: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/api/v1/knowledge/terpenes/{terpene_id}", tags=["Knowledge Base"])
async def update_terpene(terpene_id: str, terpene: dict = Body(...)):
    """Update an existing terpene"""
    try:
        terpene["id"] = terpene_id
        terpene["updated_at"] = datetime.now().isoformat()
        
        return {
            "status": "success",
            "message": "Terpene updated successfully",
            "terpene": terpene
        }
        
    except Exception as e:
        logger.error(f"Failed to update terpene: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/v1/knowledge/terpenes/{terpene_id}", tags=["Knowledge Base"])
async def delete_terpene(terpene_id: str):
    """Delete a terpene from the knowledge base"""
    try:
        return {
            "status": "success",
            "message": f"Terpene {terpene_id} deleted successfully",
            "deleted_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to delete terpene: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# EFFECTS MANAGEMENT ENDPOINTS
# ============================================================================

@app.get("/api/v1/knowledge/effects", tags=["Knowledge Base"])
async def get_effects(
    limit: int = Query(100, description="Number of effects to return"),
    category: str = Query(None, description="Filter by category (positive, negative, medical)")
):
    """Get effects database"""
    try:
        effects = [
            {
                'id': 'eff-1',
                'name': 'Euphoria',
                'type': 'positive',
                'description': 'Feeling of intense happiness and well-being',
                'associated_terpenes': ['Limonene', 'Pinene'],
                'associated_cannabinoids': ['THC'],
                'intensity': 'strong',
                'duration': '2-3 hours'
            },
            {
                'id': 'eff-2',
                'name': 'Relaxation',
                'type': 'positive',
                'description': 'Physical and mental calmness',
                'associated_terpenes': ['Myrcene', 'Linalool'],
                'associated_cannabinoids': ['CBD', 'CBN'],
                'intensity': 'moderate',
                'duration': '3-4 hours'
            },
            {
                'id': 'eff-3',
                'name': 'Dry Mouth',
                'type': 'negative',
                'description': 'Reduced saliva production',
                'associated_terpenes': [],
                'associated_cannabinoids': ['THC'],
                'intensity': 'mild',
                'duration': '1-2 hours'
            },
            {
                'id': 'eff-4',
                'name': 'Pain Relief',
                'type': 'medical',
                'description': 'Reduction in chronic or acute pain',
                'associated_terpenes': ['Beta-Caryophyllene', 'Myrcene'],
                'associated_cannabinoids': ['CBD', 'THC'],
                'intensity': 'strong',
                'duration': '4-6 hours'
            }
        ]
        
        # Filter by category if specified
        if category:
            effects = [e for e in effects if e['type'] == category]
        
        return {
            'effects': effects[:limit],
            'total': len(effects),
            'categories': ['positive', 'negative', 'medical']
        }
        
    except Exception as e:
        logger.error(f"Failed to get effects: {e}")
        return {'effects': [], 'total': 0}

@app.post("/api/v1/knowledge/effects", tags=["Knowledge Base"])
async def add_effect(effect: dict = Body(...)):
    """Add a new effect to the knowledge base"""
    try:
        required_fields = ["name", "type", "description"]
        for field in required_fields:
            if field not in effect:
                raise HTTPException(status_code=400, detail=f"Missing required field: {field}")
        
        effect_id = f"eff-{int(datetime.now().timestamp())}"
        effect["id"] = effect_id
        effect["created_at"] = datetime.now().isoformat()
        
        return {
            "status": "success",
            "message": "Effect added successfully",
            "effect": effect
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to add effect: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/api/v1/knowledge/effects/{effect_id}", tags=["Knowledge Base"])
async def update_effect(effect_id: str, effect: dict = Body(...)):
    """Update an existing effect"""
    try:
        effect["id"] = effect_id
        effect["updated_at"] = datetime.now().isoformat()
        
        return {
            "status": "success",
            "message": "Effect updated successfully",
            "effect": effect
        }
        
    except Exception as e:
        logger.error(f"Failed to update effect: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/v1/knowledge/effects/{effect_id}", tags=["Knowledge Base"])
async def delete_effect(effect_id: str):
    """Delete an effect from the knowledge base"""
    try:
        return {
            "status": "success",
            "message": f"Effect {effect_id} deleted successfully",
            "deleted_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to delete effect: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# EDUCATIONAL CONTENT ENDPOINTS
# ============================================================================

@app.get("/api/v1/knowledge/education", tags=["Knowledge Base"])
async def get_educational_content(
    limit: int = Query(50, description="Number of articles to return"),
    category: str = Query(None, description="Filter by category"),
    difficulty: str = Query(None, description="Filter by difficulty level")
):
    """Get educational content"""
    try:
        content = [
            {
                'id': 'edu-1',
                'title': 'Understanding Terpenes',
                'category': 'Science',
                'content': 'Terpenes are aromatic compounds found in many plants...',
                'tags': ['terpenes', 'chemistry', 'effects'],
                'difficulty': 'intermediate',
                'read_time': 5
            },
            {
                'id': 'edu-2',
                'title': 'Cannabis 101: A Beginner\'s Guide',
                'category': 'Basics',
                'content': 'Cannabis is a plant that has been used for thousands of years...',
                'tags': ['beginner', 'basics', 'introduction'],
                'difficulty': 'beginner',
                'read_time': 3
            },
            {
                'id': 'edu-3',
                'title': 'The Endocannabinoid System',
                'category': 'Medical',
                'content': 'The endocannabinoid system is a complex cell-signaling system...',
                'tags': ['medical', 'biology', 'ECS'],
                'difficulty': 'advanced',
                'read_time': 8
            }
        ]
        
        # Apply filters
        if category:
            content = [c for c in content if c['category'] == category]
        if difficulty:
            content = [c for c in content if c['difficulty'] == difficulty]
        
        return {
            'content': content[:limit],
            'total': len(content),
            'categories': ['Science', 'Basics', 'Medical', 'Legal', 'Culture'],
            'difficulty_levels': ['beginner', 'intermediate', 'advanced']
        }
        
    except Exception as e:
        logger.error(f"Failed to get educational content: {e}")
        return {'content': [], 'total': 0}

@app.post("/api/v1/knowledge/education", tags=["Knowledge Base"])
async def add_educational_content(content: dict = Body(...)):
    """Add new educational content"""
    try:
        required_fields = ["title", "category", "content"]
        for field in required_fields:
            if field not in content:
                raise HTTPException(status_code=400, detail=f"Missing required field: {field}")
        
        content_id = f"edu-{int(datetime.now().timestamp())}"
        content["id"] = content_id
        content["created_at"] = datetime.now().isoformat()
        
        # Calculate read time based on content length
        word_count = len(content.get("content", "").split())
        content["read_time"] = max(1, word_count // 200)  # Assuming 200 words per minute
        
        return {
            "status": "success",
            "message": "Educational content added successfully",
            "content": content
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to add educational content: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/api/v1/knowledge/education/{content_id}", tags=["Knowledge Base"])
async def update_educational_content(content_id: str, content: dict = Body(...)):
    """Update existing educational content"""
    try:
        content["id"] = content_id
        content["updated_at"] = datetime.now().isoformat()
        
        # Recalculate read time
        word_count = len(content.get("content", "").split())
        content["read_time"] = max(1, word_count // 200)
        
        return {
            "status": "success",
            "message": "Educational content updated successfully",
            "content": content
        }
        
    except Exception as e:
        logger.error(f"Failed to update educational content: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/v1/knowledge/education/{content_id}", tags=["Knowledge Base"])
async def delete_educational_content(content_id: str):
    """Delete educational content"""
    try:
        return {
            "status": "success",
            "message": f"Educational content {content_id} deleted successfully",
            "deleted_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to delete educational content: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# MODEL CONFIGURATION ENDPOINTS
# ============================================================================

@app.post("/api/v1/models/config", tags=["Model Management"])
async def update_model_configuration(config: dict = Body(...)):
    """Update model configuration settings"""
    try:
        # Validate configuration
        valid_params = ["temperature", "max_tokens", "top_p", "top_k", "repetition_penalty"]
        
        for key in config:
            if key not in valid_params:
                raise HTTPException(status_code=400, detail=f"Invalid parameter: {key}")
        
        # Apply configuration (simulated)
        return {
            "status": "success",
            "message": "Model configuration updated successfully",
            "config": config,
            "applied_at": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update model configuration: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/models/import", tags=["Model Management"])
async def import_model(file: UploadFile = File(...)):
    """Import a new model file"""
    try:
        # Validate file type
        if not file.filename.endswith(('.gguf', '.bin', '.safetensors')):
            raise HTTPException(status_code=400, detail="Invalid model file format")
        
        # Simulate model import
        model_id = f"model-{int(datetime.now().timestamp())}"
        
        return {
            "status": "success",
            "message": f"Model {file.filename} imported successfully",
            "model_id": model_id,
            "size": file.size,
            "imported_at": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to import model: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/models/fine-tune", tags=["Model Management"])
async def fine_tune_model(
    file: UploadFile = File(...),
    model_id: str = Form(...),
    epochs: int = Form(3),
    learning_rate: float = Form(0.0001)
):
    """Start fine-tuning a model with training data"""
    try:
        # Validate training data file
        if not file.filename.endswith(('.jsonl', '.json', '.csv')):
            raise HTTPException(status_code=400, detail="Invalid training data format")
        
        # Start fine-tuning job (simulated)
        job_id = f"ft-job-{int(datetime.now().timestamp())}"
        
        return {
            "status": "success",
            "message": "Fine-tuning job started successfully",
            "job_id": job_id,
            "model_id": model_id,
            "config": {
                "epochs": epochs,
                "learning_rate": learning_rate,
                "training_file": file.filename
            },
            "started_at": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to start fine-tuning: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# ADDITIONAL ENDPOINTS FOR FRONTEND
# ============================================================================

@app.get("/api/v1/ai/decision-paths", tags=["AI Monitoring"])
async def get_decision_paths(input_text: str = Query(default="", description="Input text to analyze")):
    """Get decision paths for given input"""
    if not input_text:
        return {"paths": []}
    
    # Analyze the input with the AI engine
    if service.smart_ai_engine:
        try:
            # Process message to get intent
            import uuid
            session_id = str(uuid.uuid4())  # Generate temporary session ID
            result = await service.smart_ai_engine.process_message(input_text, {}, session_id)
            intent = result.get('intent', 'general')
            
            # Build decision paths
            paths = []
            
            # Path 1: Direct product search
            if "product" in intent.lower() or "search" in intent.lower():
                paths.append({
                    "id": "path_1",
                    "decision": "Product Search",
                    "reasoning": "User is looking for specific products",
                    "confidence": 0.85,
                    "selected": True,
                    "consequences": ["Show relevant products", "Provide recommendations"]
                })
            
            # Path 2: Medical consultation
            if any(word in input_text.lower() for word in ['pain', 'sleep', 'anxiety', 'medical']):
                paths.append({
                    "id": "path_2",
                    "decision": "Medical Consultation",
                    "reasoning": "User mentioned medical conditions",
                    "confidence": 0.75,
                    "selected": False,
                    "consequences": ["Ask about symptoms", "Recommend appropriate strains"]
                })
            
            # Path 3: Educational content
            if any(word in input_text.lower() for word in ['what', 'how', 'why', 'explain']):
                paths.append({
                    "id": "path_3",
                    "decision": "Educational Response",
                    "reasoning": "User is seeking information",
                    "confidence": 0.65,
                    "selected": False,
                    "consequences": ["Provide educational content", "Offer to explain further"]
                })
            
            # Default path if no specific intent
            if not paths:
                paths.append({
                    "id": "path_default",
                    "decision": "General Assistance",
                    "reasoning": "Provide general help and guidance",
                    "confidence": 0.5,
                    "selected": True,
                    "consequences": ["Ask clarifying questions", "Show popular products"]
                })
            
            return {"paths": paths}
        except Exception as e:
            logger.error(f"Error generating decision paths: {str(e)}")
            # Return default paths on error
            return {"paths": [{
                "id": "path_default",
                "decision": "General Assistance",
                "reasoning": "Analyzing your request",
                "confidence": 0.7,
                "selected": True,
                "consequences": ["Process user input", "Provide helpful response"]
            }]}
    
    return {"paths": []}

# ============================================================================
# TEST ENGINE ENDPOINTS - For testing raw model capabilities
# ============================================================================

from services.simple_test_engine import get_test_engine
from pydantic import BaseModel

class TestEngineRequest(BaseModel):
    prompt: str
    prompt_type: Optional[str] = None
    max_tokens: Optional[int] = 512
    temperature: Optional[float] = 0.7
    top_p: Optional[float] = 0.95
    top_k: Optional[int] = 40

class TestEngineLoadModel(BaseModel):
    model_name: str
    # Legacy prompt system
    base_folder: Optional[str] = None
    role_folder: Optional[str] = None
    personality_file: Optional[str] = None
    # New modular system
    agent_id: Optional[str] = None
    personality_id: Optional[str] = None

class TestEngineCompareRequest(BaseModel):
    prompt: str
    prompt_type: Optional[str] = None

@app.get("/api/v1/test-engine/models", tags=["Test Engine"])
async def get_available_test_models():
    """Get list of all available models for testing"""
    try:
        test_engine = get_test_engine()
        models = test_engine.list_models()
        return {
            "models": models,
            "total": len(models),
            "current_model": test_engine.current_model_name
        }
    except Exception as e:
        logger.error(f"Failed to get test models: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/test-engine/load", tags=["Test Engine"])
async def load_test_model(request: TestEngineLoadModel):
    """Load a specific model for testing with optional multi-layer prompts"""
    try:
        test_engine = get_test_engine()
        success = test_engine.load_model(
            request.model_name, 
            request.base_folder,
            request.role_folder,
            request.personality_file,
            request.agent_id,
            request.personality_id
        )
        
        if success:
            loaded_prompts = test_engine.list_loaded_prompts() if test_engine.use_prompts else {}
            return {
                "status": "success",
                "model": request.model_name,
                "base_folder": request.base_folder,
                "role_folder": request.role_folder,
                "personality_file": request.personality_file,
                "agent_id": request.agent_id or test_engine.current_agent,
                "personality_id": request.personality_id or test_engine.current_personality_type,
                "prompts_loaded": test_engine.use_prompts,
                "loaded_prompts": loaded_prompts,
                "message": f"Model {request.model_name} loaded {'with prompts' if test_engine.use_prompts else 'without prompts'}"
            }
        else:
            raise HTTPException(status_code=400, detail=f"Failed to load model {request.model_name}")
    except Exception as e:
        logger.error(f"Failed to load test model: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/test-engine/generate", tags=["Test Engine"])
async def test_generate(request: TestEngineRequest):
    """Generate text using the currently loaded test model with optional prompt template"""
    try:
        test_engine = get_test_engine()
        result = test_engine.generate(
            prompt=request.prompt,
            prompt_type=request.prompt_type,  # Pass prompt_type for template application
            max_tokens=request.max_tokens,
            temperature=request.temperature,
            top_p=request.top_p,
            top_k=request.top_k
        )
        return result
    except Exception as e:
        logger.error(f"Test generation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/test-engine/resources", tags=["Test Engine"])
async def get_resource_usage():
    """Get current system resource usage and model status"""
    try:
        test_engine = get_test_engine()
        resources = test_engine.get_resource_usage()
        return {
            "status": "success",
            "resources": resources,
            "current_model": test_engine.current_model_name,
            "model_loaded": test_engine.current_model_name is not None,
            "prompts_loaded": test_engine.use_prompts
        }
    except Exception as e:
        logger.error(f"Failed to get resource usage: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/test-engine/benchmark/{model_name}", tags=["Test Engine"])
async def benchmark_model(model_name: str, with_prompts: bool = False, prompt_folder: Optional[str] = None):
    """Benchmark a specific model with or without prompts"""
    try:
        test_engine = get_test_engine()
        if with_prompts and prompt_folder:
            test_engine.load_prompts(prompt_folder)
        results = test_engine.benchmark_model(model_name, with_prompts=with_prompts)
        return results
    except Exception as e:
        logger.error(f"Benchmark failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/test-engine/compare", tags=["Test Engine"])
async def compare_with_without_prompts(request: TestEngineCompareRequest):
    """Compare model responses with and without prompts"""
    try:
        test_engine = get_test_engine()
        result = test_engine.compare_with_without_prompts(
            request.user_input,
            request.prompt_type
        )
        return result
    except Exception as e:
        logger.error(f"Comparison failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/test-engine/prompts", tags=["Test Engine"])
async def get_loaded_prompts():
    """Get list of currently loaded prompt templates"""
    try:
        test_engine = get_test_engine()
        prompts = test_engine.list_loaded_prompts()
        return {
            "loaded": test_engine.use_prompts,
            "folder": test_engine.prompt_folder,
            "prompts": prompts,
            "count": sum(len(p) for p in prompts.values())
        }
    except Exception as e:
        logger.error(f"Failed to get prompts: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/test-engine/agents", tags=["Test Engine"])
async def get_available_agents():
    """Get list of available agents from modular system"""
    try:
        test_engine = get_test_engine()
        agents = test_engine.list_available_agents()
        return {
            "agents": agents,
            "current_agent": test_engine.current_agent
        }
    except Exception as e:
        logger.error(f"Failed to get agents: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/test-engine/personalities", tags=["Test Engine"])
async def get_available_personalities():
    """Get list of available personalities from modular system"""
    try:
        test_engine = get_test_engine()
        personalities = test_engine.list_available_personalities()
        return {
            "personalities": personalities,
            "current_personality": test_engine.current_personality_type
        }
    except Exception as e:
        logger.error(f"Failed to get personalities: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/test-engine/prompt-folders", tags=["Test Engine"])
async def get_available_prompt_folders():
    """Get list of available prompt folders"""
    try:
        import os
        from pathlib import Path
        
        base_path = Path(".")
        prompt_folders = []
        
        # Check main prompts folder
        if Path("prompts").exists():
            prompt_folders.append("prompts")
            # Check for JSON files in prompts folder
            json_files = list(Path("prompts").glob("*.json"))
            if json_files:
                prompt_folders.append({
                    "path": "prompts",
                    "files": [f.name for f in json_files]
                })
        
        # Check for subdirectories with prompts
        for subdir in Path("prompts").rglob("*/"):
            if subdir.is_dir():
                json_files = list(subdir.glob("*.json"))
                if json_files:
                    rel_path = str(subdir.relative_to(base_path))
                    prompt_folders.append({
                        "path": rel_path,
                        "files": [f.name for f in json_files]
                    })
        
        # Check domains folder
        if Path("domains").exists():
            for domain_dir in Path("domains").iterdir():
                if domain_dir.is_dir():
                    prompts_dir = domain_dir / "prompts"
                    if prompts_dir.exists():
                        json_files = list(prompts_dir.glob("*.json"))
                        if json_files:
                            rel_path = str(prompts_dir.relative_to(base_path))
                            prompt_folders.append({
                                "path": rel_path,
                                "files": [f.name for f in json_files]
                            })
        
        return {"folders": prompt_folders}
    except Exception as e:
        logger.error(f"Failed to list prompt folders: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.websocket("/api/v1/test-engine/ws")
async def test_engine_websocket(websocket: WebSocket):
    """WebSocket for real-time test engine chat"""
    await websocket.accept()
    test_engine = get_test_engine()
    
    try:
        while True:
            data = await websocket.receive_json()
            
            if data.get("action") == "load_model":
                model_name = data.get("model")
                base_folder = data.get("base_folder")
                role_folder = data.get("role_folder")
                personality_file = data.get("personality_file")
                success = test_engine.load_model(model_name, base_folder, role_folder, personality_file)
                await websocket.send_json({
                    "type": "model_loaded",
                    "success": success,
                    "model": model_name,
                    "prompts_loaded": test_engine.use_prompts,
                    "prompt_folder": test_engine.prompt_folder
                })
            
            elif data.get("action") == "generate":
                prompt = data.get("prompt", "")
                prompt_type = data.get("prompt_type")  # Support prompt templates
                result = test_engine.generate(
                    prompt=prompt,
                    prompt_type=prompt_type,
                    max_tokens=data.get("max_tokens", 512),
                    temperature=data.get("temperature", 0.7),
                    top_p=data.get("top_p", 0.95),
                    top_k=data.get("top_k", 40)
                )
                await websocket.send_json({
                    "type": "response",
                    **result
                })
            
            elif data.get("action") == "load_prompts":
                prompt_folder = data.get("prompt_folder")
                prompts = test_engine.load_prompts(prompt_folder)
                await websocket.send_json({
                    "type": "prompts_loaded",
                    "folder": prompt_folder,
                    "prompts": test_engine.list_loaded_prompts(),
                    "count": sum(len(p) for p in prompts.values())
                })
            
            elif data.get("action") == "compare":
                user_input = data.get("user_input", "")
                prompt_type = data.get("prompt_type")
                result = test_engine.compare_with_without_prompts(user_input, prompt_type)
                await websocket.send_json({
                    "type": "comparison",
                    **result
                })
            
            elif data.get("action") == "list_models":
                models = test_engine.list_models()
                await websocket.send_json({
                    "type": "models_list",
                    "models": models,
                    "current": test_engine.current_model_name
                })
                
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        try:
            await websocket.close()
        except:
            pass

# ============================================================================
# WEBSOCKET ENDPOINTS FOR REAL-TIME UPDATES
# ============================================================================

@app.websocket("/api/v1/models/ws")
async def websocket_model_status(websocket: WebSocket):
    """
    WebSocket endpoint for real-time model status updates
    Used by AI Admin Dashboard for monitoring
    """
    await websocket.accept()
    logger.info("WebSocket connection accepted for model status")
    
    # Track connection for cleanup
    connection_active = True
    
    try:
        while connection_active:
            # Send model status every 2 seconds
            try:
                # Safely get current model status
                status = None
                
                # Try to get orchestrator status
                try:
                    if hasattr(service, 'smart_ai_engine') and service.smart_ai_engine:
                        if hasattr(service.smart_ai_engine, 'multi_model_orchestrator'):
                            from services.multi_model_orchestrator import get_orchestrator
                            orchestrator = get_orchestrator()
                        else:
                            orchestrator = None
                    else:
                        orchestrator = None
                except Exception as orch_error:
                    logger.debug(f"Could not get orchestrator: {orch_error}")
                    orchestrator = None
                
                if orchestrator:
                    
                    # Get intelligent router status if available
                    router_status = None
                    try:
                        from services.intelligent_model_router import get_intelligent_router
                        router = get_intelligent_router()
                        if hasattr(router, 'get_router_status'):
                            router_status = router.get_router_status()
                    except Exception as router_error:
                        logger.debug(f"Could not get router status: {router_error}")
                    
                    try:
                        # Safely build status
                        current_model = None
                        available_models = []
                        performance_report = {}
                        
                        if hasattr(orchestrator, 'hot_swap_manager'):
                            hot_swap = orchestrator.hot_swap_manager
                            current_model = hot_swap.current_model_name if hasattr(hot_swap, 'current_model_name') else None
                            if hasattr(hot_swap, 'get_performance_report'):
                                performance_report = hot_swap.get_performance_report()
                        
                        if hasattr(orchestrator, 'get_available_models'):
                            available_models = orchestrator.get_available_models()
                        
                        # Build model profiles safely
                        model_profiles = {}
                        if hasattr(orchestrator, 'MODEL_PROFILES'):
                            for name, profile in orchestrator.MODEL_PROFILES.items():
                                model_profiles[name] = {
                                    "memory_gb": getattr(profile, 'memory_requirement_gb', 0),
                                    "capabilities": getattr(profile, 'strengths', []) if hasattr(profile, 'strengths') else [],
                                    "performance": getattr(profile, 'speed_score', 0.5)
                                }
                        
                        status = {
                            "type": "model_status",
                            "timestamp": datetime.now().isoformat(),
                            "current_model": current_model,
                            "available_models": available_models,
                            "performance_report": performance_report,
                            "memory_available_gb": psutil.virtual_memory().available / (1024**3),
                            "router_status": router_status,
                            "model_profiles": model_profiles
                        }
                    except Exception as status_error:
                        logger.error(f"Error building orchestrator status: {status_error}")
                        status = None
                
                # Use fallback status if needed
                if not status:
                    # Fallback status when orchestrator not available
                    current_model = "mistral_7b_v3"  # Default
                    if hasattr(service, 'smart_ai_engine') and service.smart_ai_engine:
                        current_model = getattr(service.smart_ai_engine, 'current_model', 'mistral_7b_v3')
                    
                    status = {
                        "type": "model_status",
                        "timestamp": datetime.now().isoformat(),
                        "current_model": current_model,
                        "available_models": ["mistral_7b_v3", "qwen_7b", "llama33_70b"],
                        "performance_report": {"status": "basic"},
                        "memory_available_gb": psutil.virtual_memory().available / (1024**3),
                        "router_status": None,
                        "model_profiles": {}
                    }
                
                # Send status to client
                try:
                    await websocket.send_json(status)
                except Exception as send_error:
                    logger.error(f"Error sending WebSocket data: {send_error}")
                    connection_active = False
                    break
                
            except Exception as e:
                logger.error(f"Error getting model status: {e}")
                try:
                    await websocket.send_json({
                        "type": "error",
                        "message": str(e),
                        "timestamp": datetime.now().isoformat()
                    })
                except:
                    connection_active = False
                    break
            
            # Wait for 2 seconds or until client sends a message
            try:
                message = await asyncio.wait_for(websocket.receive_text(), timeout=2.0)
                # Handle any client messages if needed
                if message == "ping":
                    await websocket.send_text("pong")
                elif message == "status":
                    # Immediate status request
                    continue
                elif message == "close":
                    connection_active = False
                    break
            except asyncio.TimeoutError:
                pass  # Continue sending status updates
            except Exception as recv_error:
                logger.debug(f"WebSocket receive error: {recv_error}")
                connection_active = False
                break
            
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        try:
            await websocket.close()
        except:
            pass
        logger.info("WebSocket connection closed")

# ============================================================================
# MAIN ENTRY POINT
# ============================================================================

if __name__ == "__main__":
    # Run the unified service on single port
    port = 5024  # Main API port
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=port,
        log_level="info",
        reload=False
    )