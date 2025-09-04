"""
Smart Multilingual Cannabis AI Engine
Integrates all multilingual components with the existing smart AI engine
"""

import asyncio
import asyncpg
import json
import logging
import time
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass

from services.smart_ai_engine_v3 import SmartAIEngineV3
from services.multilingual_engine import MultilingualEngine, LanguageTier
from services.translation_service import TranslationService
from services.multilingual_llm_service import MultilingualLLMService
from services.model_driven_language_service import ModelDrivenLanguageService
# from services.prompt_manager import PromptManager  # Commented out - has dependency issue

logger = logging.getLogger(__name__)

@dataclass
class MultilingualQueryContext:
    """Extended query context with language support"""
    message: str
    session_id: str
    customer_id: str
    detected_language: str
    target_language: str
    language_confidence: float
    session_context: List[Dict] = None
    budtender_personality: Dict = None
    use_translation: bool = False
    
class SmartMultilingualEngine:
    """
    Main multilingual AI engine for cannabis dispensary
    """
    
    def __init__(self, db_pool: asyncpg.Pool):
        self.db_pool = db_pool
        
        # Initialize components
        self.base_engine = SmartAIEngineV3()  # SmartAIEngineV3 doesn't take db_pool
        self.multilingual = MultilingualEngine(db_pool)
        self.translator = TranslationService(db_pool)
        self.llm_service = MultilingualLLMService(db_pool)  # New multilingual LLM service
        self.language_service = ModelDrivenLanguageService()  # Model-driven language detection
        
        # Load multilingual prompts
        self.multilingual_prompts = self._load_multilingual_prompts()
        
        # Performance metrics
        self.metrics = {
            'requests_by_language': {},
            'avg_response_time': {},
            'translation_usage': {},
            'quality_scores': {}
        }
    
    def _load_multilingual_prompts(self) -> Dict:
        """Load multilingual prompt templates"""
        try:
            with open('prompts/multilingual_prompts.json', 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load multilingual prompts: {e}")
            return {}
    
    async def initialize(self):
        """Initialize all components"""
        # Set the db_pool on base_engine before initializing
        self.base_engine.db_pool = self.db_pool
        await self.base_engine.initialize()
        
        # Initialize multilingual LLM service
        await self.llm_service.initialize()
        
        # Initialize language service with LLM instance if available
        if hasattr(self.llm_service, 'llm'):
            self.language_service.llm = self.llm_service.llm
        
        logger.info("Smart Multilingual Engine initialized")
    
    async def process_message(
        self,
        message: str,
        session_id: str,
        customer_id: str = None,
        preferred_language: str = None
    ) -> Dict:
        """
        Process message with automatic language detection and response
        """
        start_time = time.time()
        
        try:
            # Step 1: Detect or retrieve language
            if preferred_language:
                detected_lang = preferred_language
                confidence = 1.0
            else:
                # Build session context for language detection
                session_context = None
                if customer_id:
                    customer_lang = await self.multilingual.get_customer_language(customer_id)
                    if customer_lang:
                        session_context = {'previous_language': customer_lang}
                
                # Use model-driven language detection
                detected_lang, confidence = await self.language_service.detect_language(
                    text=message,
                    session_context=session_context
                )
                
                # If confidence is low and customer has preference, use that
                if confidence < 0.7 and customer_id:
                    customer_lang = await self.multilingual.get_customer_language(customer_id)
                    if customer_lang:
                        detected_lang = customer_lang
                        confidence = 0.8
                        logger.info(f"Using customer's preferred language: {customer_lang}")
            
            # Update metrics
            if detected_lang not in self.metrics['requests_by_language']:
                self.metrics['requests_by_language'][detected_lang] = 0
            self.metrics['requests_by_language'][detected_lang] += 1
            
            # Step 2: Determine processing strategy based on language tier
            lang_config = self.multilingual.get_language_config(detected_lang)
            
            if lang_config.tier == LanguageTier.TIER_1:
                # Process directly or with adapter
                response = await self._process_tier_1_message(
                    message, detected_lang, session_id, customer_id
                )
            elif lang_config.tier == LanguageTier.TIER_2:
                # Process with adapter and quality checks
                response = await self._process_tier_2_message(
                    message, detected_lang, session_id, customer_id
                )
            else:  # TIER_3
                # Translate to English, process, translate back
                response = await self._process_tier_3_message(
                    message, detected_lang, session_id, customer_id
                )
            
            # Step 3: Validate response quality
            quality = await self.multilingual.validate_response_quality(
                response['message'],
                detected_lang,
                {'intent': response.get('intent', 'general')}
            )
            
            # Step 4: Apply fallback if needed
            if quality['should_fallback']:
                response = await self._apply_fallback(
                    message, detected_lang, response
                )
            
            # Step 5: Save customer language preference
            if customer_id and confidence > 0.8:
                await self.multilingual.save_customer_language(
                    customer_id, detected_lang, confidence
                )
            
            # Step 6: Log conversation
            processing_time = int((time.time() - start_time) * 1000)
            await self.multilingual.log_conversation(
                session_id, customer_id or 'anonymous',
                message, detected_lang,
                response['message'], response.get('response_language', detected_lang),
                quality['score'], processing_time,
                quality['should_fallback']
            )
            
            # Step 7: Update metrics
            await self.multilingual.update_language_metrics(
                detected_lang, quality['score'], 
                processing_time, quality['should_fallback']
            )
            
            # Return enhanced response
            return {
                **response,
                'detected_language': detected_lang,
                'language_confidence': confidence,
                'quality_score': quality['score'],
                'processing_time_ms': processing_time
            }
            
        except Exception as e:
            logger.error(f"Multilingual processing failed: {e}")
            
            # Return error response in detected language
            error_template = self.multilingual_prompts.get(
                'error_fallback', {}
            ).get(detected_lang, {}).get('template', str(e))
            
            return {
                'message': error_template,
                'error': True,
                'detected_language': detected_lang,
                'products': []
            }
    
    async def _process_tier_1_message(
        self,
        message: str,
        language: str,
        session_id: str,
        customer_id: str
    ) -> Dict:
        """Process Tier 1 languages (English, Spanish, French)"""
        
        if language == 'en':
            # Process directly with base engine
            return await self.base_engine.process_message(
                message=message,
                customer_id=customer_id,
                session_id=session_id
            )
        
        elif language == 'es':
            # Spanish - Use Spanish-specific processing
            # Check if it's a greeting
            greetings = ['hola', 'buenos días', 'buenas tardes', 'buenas noches', 'hey', 'qué tal']
            message_lower = message.lower().strip()
            
            if any(greeting in message_lower for greeting in greetings):
                # Return a Spanish greeting
                response = {
                    'message': "¡Hola! Bienvenido a nuestra dispensario. ¿En qué puedo ayudarte hoy con productos de cannabis?",
                    'response_language': 'es',
                    'products': [],
                    'intent': 'greeting'
                }
                return response
            
            # For other messages, try to get Mistral to respond in Spanish
            # Create a Spanish-specific prompt
            spanish_system = "Eres un budtender en una dispensario de cannabis. IMPORTANTE: Responde SOLO en español. Sé amigable y profesional."
            
            # Modify the message to ensure Spanish response
            prompt_message = f"Cliente dice: '{message}'. Responde en español como budtender experto."
            
            response = await self.base_engine.process_message(
                message=prompt_message,
                customer_id=customer_id,
                session_id=session_id
            )
            
            # If response is still in English, provide a fallback Spanish response
            if response.get('message'):
                # Check if response contains English phrases
                english_indicators = ['How', 'What', 'Can I', 'Would you', 'Do you']
                if any(indicator in response['message'] for indicator in english_indicators):
                    # Provide appropriate Spanish fallback based on intent
                    if 'thc' in message.lower() or 'cbd' in message.lower():
                        response['message'] = "Tenemos excelentes productos con diferentes niveles de THC y CBD. ¿Buscas algo específico para relajación o energía?"
                    elif 'product' in message.lower() or 'producto' in message.lower():
                        response['message'] = "Tenemos una gran variedad de productos: flores, comestibles, vaporizadores y más. ¿Qué tipo prefieres?"
                    elif 'ayuda' in message.lower() or 'help' in message.lower():
                        response['message'] = "Por supuesto, estoy aquí para ayudarte. ¿Qué tipo de efecto buscas: relajación, creatividad, o alivio del dolor?"
                    else:
                        response['message'] = "Claro, puedo ayudarte con eso. ¿Me puedes dar más detalles sobre lo que buscas?"
                
                response['response_language'] = 'es'
            
            return response
        
        else:
            # French - use translation approach
            # First, check for cached response
            cached = await self.translator.translate(
                message, language, 'en', cache_result=False
            )
            
            if cached['cached']:
                return {
                    'message': cached['text'],
                    'cached': True,
                    'response_language': language
                }
            
            # Translate cannabis terms if present
            translated_message = await self._translate_cannabis_terms(
                message, language, 'en'
            )
            
            # Process with base engine
            english_response = await self.base_engine.process_message(
                message=translated_message,
                customer_id=customer_id,
                session_id=session_id
            )
            
            # Translate response back
            if english_response.get('message'):
                translated_response = await self.translator.translate(
                    english_response['message'],
                    'en', language
                )
                
                english_response['message'] = translated_response['text']
                english_response['response_language'] = language
                
                # Translate products if present
                if english_response.get('products'):
                    english_response['products'] = await self.multilingual.translate_products(
                        english_response['products'], language
                    )
            
            return english_response
    
    async def _process_tier_2_message(
        self,
        message: str,
        language: str,
        session_id: str,
        customer_id: str
    ) -> Dict:
        """Process Tier 2 languages (Portuguese)"""
        
        # Similar to Tier 1 but with additional quality checks
        response = await self._process_tier_1_message(
            message, language, session_id, customer_id
        )
        
        # Additional quality validation
        if response.get('message'):
            # Check for untranslated English words
            english_words = ['the', 'and', 'for', 'with', 'this']
            message_lower = response['message'].lower()
            english_count = sum(1 for word in english_words if word in message_lower)
            
            if english_count > 2:
                # Quality issue detected, apply correction
                response['quality_warning'] = 'partial_translation'
        
        return response
    
    async def _process_tier_3_message(
        self,
        message: str,
        language: str,
        session_id: str,
        customer_id: str
    ) -> Dict:
        """Process Tier 3 languages (Chinese, Arabic)"""
        
        # First, try to use native multilingual LLM (Qwen)
        llm_response, confidence = await self.llm_service.generate_response(
            message=message,
            language=language,
            context={
                'session_id': session_id,
                'customer_id': customer_id,
                'previous_messages': []  # TODO: Add conversation history
            }
        )
        
        # If native LLM succeeded, return the response
        if llm_response and confidence > 0.7:
            return {
                'message': llm_response,
                'response_language': language,
                'model_used': 'qwen',
                'confidence': confidence,
                'products': []  # Products are embedded in the response
            }
        
        # Fallback to translation approach if native LLM not available
        translation_result = await self.translator.translate(
            message, language, 'en', preferred_provider='openai'
        )
        
        if translation_result['confidence'] < 0.5:
            # Translation failed, return error
            error_template = self.multilingual_prompts.get(
                'error_fallback', {}
            ).get(language, {}).get('template', 'Translation error')
            
            return {
                'message': error_template,
                'error': True,
                'response_language': language
            }
        
        # Process in English
        english_response = await self.base_engine.process_message(
            message=translation_result['text'],
            customer_id=customer_id,
            session_id=session_id
        )
        
        # Translate response back
        if english_response.get('message'):
            # For Arabic, handle RTL formatting
            if language == 'ar':
                english_response['message'] = self._prepare_rtl_text(
                    english_response['message']
                )
            
            back_translation = await self.translator.translate(
                english_response['message'],
                'en', language,
                preferred_provider='openai'
            )
            
            english_response['message'] = back_translation['text']
            english_response['response_language'] = language
            english_response['translation_used'] = True
            
            # Translate products
            if english_response.get('products'):
                # For Chinese/Arabic, keep strain names in English
                for product in english_response['products']:
                    # Translate description and effects only
                    if product.get('description'):
                        desc_trans = await self.translator.translate(
                            product['description'], 'en', language
                        )
                        product['description'] = desc_trans['text']
                    
                    if product.get('effects'):
                        effects_trans = await self.translator.translate(
                            ', '.join(product['effects']), 'en', language
                        )
                        product['effects'] = effects_trans['text'].split('، ' if language == 'ar' else '，')
        
        return english_response
    
    async def _translate_cannabis_terms(
        self,
        text: str,
        from_lang: str,
        to_lang: str
    ) -> str:
        """Translate cannabis-specific terms in text"""
        
        # Common cannabis terms to check
        terms_to_check = [
            'sativa', 'indica', 'hybrid',
            'flower', 'edibles', 'vape',
            'thc', 'cbd', 'gram', 'ounce'
        ]
        
        translated_text = text
        for term in terms_to_check:
            # Get translation from cannabis terminology
            translated_term = await self.multilingual.get_cannabis_term(
                term, to_lang, 'general'
            )
            
            # Replace in text (case-insensitive)
            if from_lang in ['es', 'fr', 'pt']:
                # For Romance languages, check for the translated term
                source_term = await self.multilingual.get_cannabis_term(
                    term, from_lang, 'general'
                )
                translated_text = translated_text.replace(
                    source_term, translated_term
                )
        
        return translated_text
    
    def _prepare_rtl_text(self, text: str) -> str:
        """Prepare text for RTL languages (Arabic)"""
        # Add RTL markers for proper display
        # Note: This is simplified - proper RTL handling requires frontend support
        return text
    
    async def _apply_fallback(
        self,
        original_message: str,
        language: str,
        failed_response: Dict
    ) -> Dict:
        """Apply fallback strategy when response quality is poor"""
        
        logger.warning(f"Applying fallback for {language} response")
        
        # Strategy 1: Use pre-defined template response
        if language in self.multilingual_prompts.get('fallback_responses', {}):
            template = self.multilingual_prompts['fallback_responses'][language]
            return {
                'message': template,
                'fallback': True,
                'response_language': language,
                'products': []
            }
        
        # Strategy 2: Always respond in native language - never fallback to English
        # Check if this is a location query
        location_keywords = ['donde', 'dónde', 'où', 'onde', '哪里', 'أين', 'where', 'location', 'address', 
                           'ubicada', 'situé', 'localizada', '位於', 'يقع', 'tienda', 'magasin', 'loja', '商店', 'متجر']
        is_location_query = any(keyword in original_message.lower() for keyword in location_keywords)
        
        if is_location_query:
            # Provide location in native language
            location_responses = {
                'es': 'Estamos en 553 Rogers Road, Toronto. Abierto Lun-Vie 10am-10pm, Sáb 10am-11pm, Dom 11am-8pm.',
                'fr': 'Nous sommes au 553 Rogers Road, Toronto. Ouvert Lun-Ven 10h-22h, Sam 10h-23h, Dim 11h-20h.',
                'pt': 'Estamos em 553 Rogers Road, Toronto. Aberto Seg-Sex 10h-22h, Sáb 10h-23h, Dom 11h-20h.',
                'zh': '我們位於多倫多羅傑斯路553號。營業時間：週一至週五10am-10pm，週六10am-11pm，週日11am-8pm。',
                'ar': 'نحن في 553 طريق روجرز، تورونتو. مفتوح الإثنين-الجمعة 10ص-10م، السبت 10ص-11م، الأحد 11ص-8م.'
            }
            
            return {
                'message': location_responses.get(language, 'We are at 553 Rogers Road, Toronto.'),
                'fallback': False,
                'response_language': language,
                'products': []
            }
        
        # For other queries, use native language responses from prompts
        return {
            'message': failed_response.get('message', 'Please visit us at 553 Rogers Road, Toronto.'),
            'fallback': False,
            'response_language': language,
            'products': failed_response.get('products', [])
        }
    
    async def get_language_analytics(self) -> Dict:
        """Get analytics for language usage"""
        
        async with self.db_pool.acquire() as conn:
            # Get today's metrics
            today_metrics = await conn.fetch(
                """
                SELECT language_code, total_requests, successful_requests,
                       fallback_count, avg_quality_score, avg_response_time_ms
                FROM language_quality_metrics
                WHERE date = CURRENT_DATE
                ORDER BY total_requests DESC
                """
            )
            
            # Get language distribution
            language_dist = await conn.fetch(
                """
                SELECT message_language, COUNT(*) as count
                FROM multilingual_conversations
                WHERE created_at > CURRENT_TIMESTAMP - INTERVAL '7 days'
                GROUP BY message_language
                ORDER BY count DESC
                """
            )
            
            # Get quality trends
            quality_trends = await conn.fetch(
                """
                SELECT language_code, date, avg_quality_score
                FROM language_quality_metrics
                WHERE date > CURRENT_DATE - INTERVAL '30 days'
                ORDER BY date DESC
                """
            )
        
        return {
            'today_metrics': [dict(row) for row in today_metrics],
            'language_distribution': [dict(row) for row in language_dist],
            'quality_trends': [dict(row) for row in quality_trends],
            'supported_languages': list(self.multilingual.language_configs.keys()),
            'cache_stats': {
                'size': len(self.translator.cache),
                'languages': list(set(
                    key.split(':')[1] 
                    for key in self.translator.cache.keys()
                ))
            }
        }