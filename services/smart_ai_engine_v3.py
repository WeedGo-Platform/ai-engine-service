"""
Smart AI Engine V3 - Interface-Based Architecture (Upgraded from V4)
Implements AI behaviors through interfaces following SRP principle
"""

import logging
import time
import json
import asyncio
from typing import Dict, Any, Optional, List
from pathlib import Path
import yaml

from services.ai_behavior_interfaces import (
    AIBehaviorOrchestrator,
    Intent
)
from services.role_based_ai_engine import (
    RoleBasedAIEngine,
    SearchStrategy
)
from services.search_interfaces import SearchOrchestrator, ISearchEngine
from services.search_first_engine import SearchFirstEngine
from services.llm_search_extractor import LLMSearchExtractor
from services.hot_swap_model_manager import HotSwapModelManager
from services.multi_model_orchestrator import MultiModelOrchestrator
from services.interfaces import (
    IModelManager,
    IBudtenderService,
    IProductRepository,
    IChatRepository
)

logger = logging.getLogger(__name__)

class SmartAIEngineV3(IBudtenderService):
    """
    Third generation AI engine with interface-based architecture
    All behaviors are abstracted through interfaces for flexibility
    """
    
    def __init__(self):
        self.llm = None
        self.db_pool = None
        self.db_conn = None  # For psycopg2 compatibility
        self.model_manager = None
        self.multi_model_orchestrator = None
        self.behavior_orchestrator = None
        self.role_engine = None
        self.search_orchestrator = None
        self.search_engine: ISearchEngine = None  # Interface-based search engine
        self.config = {}
        self.metrics = AIMetrics()
        
        # Configuration cache from original V3
        self._skip_words_cache = set()
        self._medical_intents_cache = {}
        self._category_keywords_cache = {}
        self._cache_timestamp = None
        self._cache_ttl = 300  # 5 minutes
        
        # Add LLM search extractor for compatibility
        self.llm_search_extractor = None
        
        # Add intent service for compatibility
        self.model_driven_intent_service = None
        
    async def initialize(self):
        """Initialize all components"""
        logger.info("Initializing Smart AI Engine V3 with interface-based architecture")
        
        # Load configuration
        config_path = Path("config/ai_config.yaml")
        if config_path.exists():
            with open(config_path) as f:
                self.config = yaml.safe_load(f)
        
        # Initialize database pool - use same credentials as V3
        import asyncpg
        import psycopg2
        import os
        
        try:
            self.db_pool = await asyncpg.create_pool(
                host=self.config.get('database', {}).get('host', 'localhost'),
                port=self.config.get('database', {}).get('port', 5434),
                user=self.config.get('database', {}).get('user', 'weedgo'),
                password=self.config.get('database', {}).get('password', 'weedgo123'),
                database=self.config.get('database', {}).get('name', 'ai_engine'),
                min_size=5,
                max_size=20
            )
            
            # Also create psycopg2 connection for compatibility
            self.db_conn = psycopg2.connect(
                host=os.getenv('DB_HOST', 'localhost'),
                port=os.getenv('DB_PORT', 5434),
                database=os.getenv('DB_NAME', 'ai_engine'),
                user=os.getenv('DB_USER', 'weedgo'),
                password=os.getenv('DB_PASSWORD', 'weedgo123')
            )
            
            # Refresh configuration cache
            await self._refresh_cache()
            
        except Exception as e:
            logger.warning(f"Database connection issue: {e}")
            self.db_pool = None
            self.db_conn = None
        
        # Initialize model manager (synchronous initialization)
        self.model_manager = HotSwapModelManager()
        
        # Get default LLM function - wrap in async handler
        def sync_llm(*args, **kwargs):
            return self.model_manager.generate(*args, **kwargs)
        
        self.llm = sync_llm
        
        # Initialize multi-model orchestrator if multiple models available
        if len(self.model_manager.get_available_models()) > 1:
            self.multi_model_orchestrator = MultiModelOrchestrator()
            logger.info("Multi-model orchestration enabled")
        
        # Initialize behavior orchestrator with default role
        default_role = self.config.get('default_role', 'budtender')
        self.behavior_orchestrator = AIBehaviorOrchestrator(
            role=default_role,
            llm_function=self.llm,
            db_pool=self.db_pool
        )
        logger.info(f"Behavior orchestrator initialized with role: {default_role}")
        
        # Initialize role-based engine for search
        self.role_engine = RoleBasedAIEngine(
            llm_function=self.llm,
            db_pool=self.db_pool
        )
        logger.info("Role-based AI engine initialized")
        
        # Initialize search engine using interface
        self.search_engine = SearchFirstEngine()  # Create instance
        await self.search_engine.initialize(
            db_pool=self.db_pool,
            llm=self.llm,
            prompt_manager=None  # Will use default CentralizedPromptManager
        )
        logger.info("✅ Search engine initialized via ISearchEngine interface")
        
        # Keep search orchestrator for backward compatibility
        self.search_orchestrator = SearchOrchestrator(
            role=SearchStrategy.BUDTENDER,
            llm_function=self.llm,
            db_pool=self.db_pool
        )
        logger.info("Search orchestrator initialized")
        
        # Initialize LLM search extractor for compatibility
        from services.llm_search_extractor import LLMSearchExtractor
        self.llm_search_extractor = LLMSearchExtractor(self.llm)
        logger.info("✅ LLM Search Extractor initialized")
        
        # Initialize model-driven intent service for compatibility
        from services.model_driven_intent_service import ModelDrivenIntentService
        self.model_driven_intent_service = ModelDrivenIntentService(self.llm)
        logger.info("✅ Model-Driven Intent Service initialized")
        
        logger.info("✓ Smart AI Engine V3 initialization complete")
    
    async def _refresh_cache(self):
        """Refresh cached configurations from database"""
        from datetime import datetime, timedelta
        
        if not self.db_pool:
            return
            
        now = datetime.now()
        if self._cache_timestamp and (now - self._cache_timestamp).seconds < self._cache_ttl:
            return
            
        logger.info("Refreshing configuration cache...")
        
        try:
            async with self.db_pool.acquire() as conn:
                # Load categories and subcategories (handle missing tables gracefully)
                try:
                    categories = await conn.fetch("SELECT name FROM categories WHERE active = true")
                except Exception:
                    categories = []
                
                try:
                    subcategories = await conn.fetch("SELECT name FROM sub_categories WHERE active = true")
                except Exception:
                    subcategories = []
                
                # Build category keywords
                self._category_keywords_cache = {}
                for cat in categories:
                    self._category_keywords_cache[cat['name'].lower()] = [cat['name'].lower()]
                    
                for subcat in subcategories:
                    if subcat['name']:
                        key = subcat['name'].lower()
                        self._category_keywords_cache[key] = [key]
                
                # Load skip words (common words to ignore)
                self._skip_words_cache = {
                    'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
                    'of', 'with', 'by', 'from', 'is', 'are', 'was', 'were', 'been',
                    'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could',
                    'should', 'may', 'might', 'must', 'can', 'could', 'i', 'you', 'we',
                    'they', 'he', 'she', 'it', 'me', 'him', 'her', 'us', 'them',
                    'some', 'any', 'all', 'each', 'every', 'no', 'none', 'one', 'two',
                    'please', 'thanks', 'thank', 'hello', 'hi', 'hey', 'bye', 'goodbye'
                }
                
                # Medical intents
                self._medical_intents_cache = {
                    'pain': ['pain', 'ache', 'hurt', 'sore', 'chronic'],
                    'anxiety': ['anxiety', 'anxious', 'panic', 'stress', 'nervous'],
                    'insomnia': ['sleep', 'insomnia', 'sleepless', 'rest'],
                    'appetite': ['appetite', 'hungry', 'eating', 'nausea'],
                    'inflammation': ['inflammation', 'swelling', 'arthritis'],
                    'depression': ['depression', 'depressed', 'mood', 'sad'],
                    'ptsd': ['ptsd', 'trauma', 'flashback']
                }
                
                self._cache_timestamp = now
                logger.info(f"Configuration cache refreshed: {len(self._skip_words_cache)} skip words, "
                          f"{len(self._medical_intents_cache)} medical intents, "
                          f"{len(self._category_keywords_cache)} category configs")
                          
        except Exception as e:
            logger.error(f"Error refreshing cache: {e}")
    
    async def get_skip_words(self) -> set:
        """Get skip words from cache, refreshing if needed"""
        await self._refresh_cache()
        return self._skip_words_cache
    
    async def get_medical_intents(self) -> dict:
        """Get medical intents from cache, refreshing if needed"""
        await self._refresh_cache()
        return self._medical_intents_cache
    
    async def get_category_keywords(self) -> dict:
        """Get category keywords from cache, refreshing if needed"""
        await self._refresh_cache()
        return self._category_keywords_cache
    
    async def chat(
        self,
        message: str,
        customer_id: str,
        language: str = "en",
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Process chat message using interface-based behaviors
        Implements IBudtenderService interface
        """
        start_time = time.time()
        
        try:
            # Prepare context
            full_context = context or {}
            full_context['customer_id'] = customer_id
            full_context['language'] = language
            
            # Use multi-model orchestrator if available
            if self.multi_model_orchestrator:
                # Detect task type for optimal model routing
                task_type = self.multi_model_orchestrator.detect_task_type(message)
                
                # Route to appropriate model
                model_response = await self.multi_model_orchestrator.process_with_optimal_model(
                    prompt=message,
                    task_type=task_type,
                    context=full_context
                )
                
                # Use the response from optimal model
                if model_response.get('success'):
                    message = model_response.get('response', message)
                    full_context['model_used'] = model_response.get('model_used')
            
            # Process through behavior orchestrator (intent, language, etc.)
            behavior_result = await self.behavior_orchestrator.process_message(
                message=message,
                context=full_context
            )
            
            # Detect and switch role if needed
            detected_role = self.role_engine.detect_role_from_context(
                message=message,
                context=behavior_result
            )
            
            if detected_role != self.role_engine.current_role:
                logger.info(f"Switching AI role to: {detected_role.value}")
                self.role_engine.switch_role(detected_role)
                self.search_orchestrator.switch_role(detected_role)
            
            # Process search if product intent detected
            products = []
            search_response = None
            
            if behavior_result.get('intent') in ['product_search', 'recommendation', 'checkout']:
                # Use the interface-based search engine
                if self.search_engine:
                    search_result = await self.search_engine.process_query(
                        message=message,
                        context=full_context,
                        session_id=context.get('session_id'),
                        personality=context.get('budtender_personality')
                    )
                    products = search_result.get('products', [])
                    search_response = search_result.get('message')
                else:
                    # Fallback to orchestrator if search engine not available
                    search_result = await self.search_orchestrator.process_search(
                        query=message,
                        context=full_context
                    )
                    products = search_result.get('products', [])
                    search_response = search_result.get('response')
            
            # Combine behavior and search results
            final_response = {
                'message': search_response or behavior_result.get('response'),
                'products': products,
                'intent': behavior_result.get('intent'),
                'intent_confidence': behavior_result.get('intent_confidence'),
                'language': behavior_result.get('language'),
                'language_confidence': behavior_result.get('language_confidence'),
                'entities': behavior_result.get('entities'),
                'remember_context': behavior_result.get('remember_context'),
                'followup_questions': behavior_result.get('followup_questions'),
                'role_used': behavior_result.get('role'),
                'model_used': self.model_manager.current_model_name if self.model_manager else 'default',
                'processing_time': time.time() - start_time
            }
            
            # Update metrics
            self.metrics.record_request(
                response_time=final_response['processing_time'],
                intent=final_response['intent'],
                success=True
            )
            
            return final_response
            
        except Exception as e:
            logger.error(f"Error in chat processing: {e}")
            self.metrics.record_request(
                response_time=time.time() - start_time,
                intent='error',
                success=False
            )
            
            # Return fallback response
            return {
                'message': "I'm here to help you find the perfect cannabis products. What are you looking for?",
                'products': [],
                'intent': 'error_recovery',
                'intent_confidence': 0.5,
                'processing_time': time.time() - start_time
            }
    
    async def process_message(
        self,
        message: str,
        context: Dict[str, Any],
        session_id: str
    ) -> Dict[str, Any]:
        """
        Process message with session context
        Backwards compatibility method
        """
        customer_id = context.get('customer_id', session_id)
        language = context.get('language', 'en')
        
        result = await self.chat(
            message=message,
            customer_id=customer_id,
            language=language,
            context=context
        )
        
        # Add session_id to result
        result['session_id'] = session_id
        
        return result
    
    def switch_model(self, model_name: str) -> bool:
        """Switch to a different AI model"""
        if self.model_manager:
            success = self.model_manager.switch_model(model_name)
            if success:
                # Update LLM reference
                self.llm = self.model_manager.get_llm_function()
                
                # Reinitialize orchestrators with new model
                self.behavior_orchestrator = AIBehaviorOrchestrator(
                    role=self.behavior_orchestrator.role,
                    llm_function=self.llm,
                    db_pool=self.db_pool
                )
                
                self.role_engine = RoleBasedAIEngine(
                    llm_function=self.llm,
                    db_pool=self.db_pool
                )
                
                logger.info(f"Switched to model: {model_name}")
                return True
        return False
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get current metrics"""
        return {
            'total_requests': self.metrics.total_requests,
            'successful_requests': self.metrics.successful_requests,
            'failed_requests': self.metrics.failed_requests,
            'average_response_time': self.metrics.get_average_response_time(),
            'intent_distribution': self.metrics.intent_counts,
            'current_model': self.model_manager.current_model if self.model_manager else 'unknown',
            'available_models': self.model_manager.get_available_models() if self.model_manager else []
        }
    
    async def cleanup(self):
        """Clean up resources"""
        if self.db_pool:
            await self.db_pool.close()
        if self.model_manager:
            await self.model_manager.cleanup()
        if self.multi_model_orchestrator:
            await self.multi_model_orchestrator.cleanup()
        logger.info("Smart AI Engine V3 cleaned up")


class AIMetrics:
    """Track AI engine metrics"""
    
    def __init__(self):
        self.total_requests = 0
        self.successful_requests = 0
        self.failed_requests = 0
        self.response_times = []
        self.intent_counts = {}
        self.last_error_time = None
        self.last_error_message = None
        self.startup_time = time.time()
        # Additional attributes for health check
        self.last_error = None
        self.total_llm_calls = 0
        self.successful_llm_calls = 0
        self.failed_llm_calls = 0
        self.intents_detected = {}
        self.errors_by_type = {}
        
    def record_request(self, response_time: float, intent: str, success: bool, error_message: str = None):
        """Record a request"""
        self.total_requests += 1
        self.total_llm_calls += 1
        
        if success:
            self.successful_requests += 1
            self.successful_llm_calls += 1
        else:
            self.failed_requests += 1
            self.failed_llm_calls += 1
            if error_message:
                self.last_error_time = time.time()
                self.last_error_message = error_message
                self.last_error = error_message
                # Track error type
                error_type = error_message.split(':')[0] if ':' in error_message else 'Unknown'
                self.errors_by_type[error_type] = self.errors_by_type.get(error_type, 0) + 1
        
        self.response_times.append(response_time)
        # Keep only last 100 response times
        if len(self.response_times) > 100:
            self.response_times.pop(0)
        
        # Track intent distribution
        self.intent_counts[intent] = self.intent_counts.get(intent, 0) + 1
        self.intents_detected[intent] = self.intents_detected.get(intent, 0) + 1
    
    def get_average_response_time(self) -> float:
        """Get average response time"""
        if not self.response_times:
            return 0.0
        return sum(self.response_times) / len(self.response_times)
    
    def get_success_rate(self) -> float:
        """Get success rate as a percentage"""
        if self.total_requests == 0:
            return 100.0
        return (self.successful_requests / self.total_requests) * 100