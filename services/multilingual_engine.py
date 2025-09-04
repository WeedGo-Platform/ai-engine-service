"""
Multilingual Engine for Cannabis Dispensary AI
Supports: English, Spanish, French, Portuguese, Chinese, Arabic
"""

import asyncio
import asyncpg
import hashlib
import json
import logging
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
from datetime import datetime, timedelta
import numpy as np

logger = logging.getLogger(__name__)

class LanguageTier(Enum):
    """Language support quality tiers"""
    TIER_1 = 1  # Excellent support (EN, ES, FR)
    TIER_2 = 2  # Good support (PT)
    TIER_3 = 3  # Basic support with fallbacks (ZH, AR)

@dataclass
class LanguageConfig:
    """Configuration for each supported language"""
    code: str
    name: str
    native_name: str
    tier: LanguageTier
    is_rtl: bool = False
    tokenizer_efficiency: float = 1.0
    max_tokens_multiplier: float = 1.0
    fallback_language: str = 'en'
    use_adapter: bool = False
    adapter_path: Optional[str] = None
    
class MultilingualEngine:
    """
    Core multilingual engine for cannabis AI assistant
    """
    
    def __init__(self, db_pool: asyncpg.Pool):
        self.db_pool = db_pool
        self.language_configs = self._initialize_languages()
        self.translation_cache = {}
        self.terminology_cache = {}
        self.quality_thresholds = {
            'en': 0.90,
            'es': 0.85,
            'fr': 0.85,
            'pt': 0.80,
            'zh': 0.70,
            'ar': 0.70
        }
        
    def _initialize_languages(self) -> Dict[str, LanguageConfig]:
        """Initialize language configurations"""
        return {
            'en': LanguageConfig(
                code='en', name='English', native_name='English',
                tier=LanguageTier.TIER_1, tokenizer_efficiency=1.0
            ),
            'es': LanguageConfig(
                code='es', name='Spanish', native_name='Español',
                tier=LanguageTier.TIER_1, tokenizer_efficiency=0.9,
                use_adapter=True, adapter_path='adapters/spanish_cannabis.bin'
            ),
            'fr': LanguageConfig(
                code='fr', name='French', native_name='Français',
                tier=LanguageTier.TIER_1, tokenizer_efficiency=0.9,
                use_adapter=True, adapter_path='adapters/french_cannabis.bin'
            ),
            'pt': LanguageConfig(
                code='pt', name='Portuguese', native_name='Português',
                tier=LanguageTier.TIER_2, tokenizer_efficiency=0.85,
                use_adapter=True, adapter_path='adapters/portuguese_cannabis.bin'
            ),
            'zh': LanguageConfig(
                code='zh', name='Chinese', native_name='中文',
                tier=LanguageTier.TIER_3, tokenizer_efficiency=0.3,
                max_tokens_multiplier=3.0
            ),
            'ar': LanguageConfig(
                code='ar', name='Arabic', native_name='العربية',
                tier=LanguageTier.TIER_3, is_rtl=True, tokenizer_efficiency=0.4,
                max_tokens_multiplier=2.5
            )
        }
    
    async def detect_language(self, text: str) -> Tuple[str, float]:
        """
        Detect language of input text using model-driven approach
        Returns: (language_code, confidence)
        """
        # This is now a fallback - primary detection should use ModelDrivenLanguageService
        # For now, return English as default since model-driven detection is handled elsewhere
        logger.warning("Legacy detect_language called - should use ModelDrivenLanguageService")
        return 'en', 0.5
    
    async def get_customer_language(self, customer_id: str) -> str:
        """Get customer's preferred language from database"""
        async with self.db_pool.acquire() as conn:
            result = await conn.fetchrow(
                """
                SELECT preferred_language 
                FROM customer_language_preferences 
                WHERE customer_id = $1
                """,
                customer_id
            )
            return result['preferred_language'] if result else 'en'
    
    async def save_customer_language(
        self, 
        customer_id: str, 
        language: str,
        confidence: float
    ):
        """Save customer language preference"""
        async with self.db_pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO customer_language_preferences 
                (customer_id, preferred_language, language_confidence, updated_at)
                VALUES ($1, $2, $3, CURRENT_TIMESTAMP)
                ON CONFLICT (customer_id) 
                DO UPDATE SET 
                    preferred_language = $2,
                    language_confidence = $3,
                    updated_at = CURRENT_TIMESTAMP
                """,
                customer_id, language, confidence
            )
    
    async def get_cached_translation(
        self,
        text: str,
        source_lang: str,
        target_lang: str
    ) -> Optional[str]:
        """Get cached translation if available"""
        async with self.db_pool.acquire() as conn:
            result = await conn.fetchrow(
                """
                SELECT translated_text, expires_at
                FROM translation_cache
                WHERE source_text = $1 
                  AND source_language = $2 
                  AND target_language = $3
                  AND (expires_at IS NULL OR expires_at > CURRENT_TIMESTAMP)
                """,
                text, source_lang, target_lang
            )
            
            if result:
                # Update usage count
                await conn.execute(
                    """
                    UPDATE translation_cache 
                    SET usage_count = usage_count + 1,
                        last_used_at = CURRENT_TIMESTAMP
                    WHERE source_text = $1 
                      AND source_language = $2 
                      AND target_language = $3
                    """,
                    text, source_lang, target_lang
                )
                return result['translated_text']
        return None
    
    async def cache_translation(
        self,
        text: str,
        source_lang: str,
        target_lang: str,
        translation: str,
        quality_score: float = 0.8,
        ttl_hours: int = 24
    ):
        """Cache a translation"""
        expires_at = datetime.now() + timedelta(hours=ttl_hours)
        
        async with self.db_pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO translation_cache
                (source_text, source_language, target_language, 
                 translated_text, quality_score, expires_at)
                VALUES ($1, $2, $3, $4, $5, $6)
                ON CONFLICT (source_text, source_language, target_language)
                DO UPDATE SET 
                    translated_text = $4,
                    quality_score = $5,
                    expires_at = $6,
                    usage_count = translation_cache.usage_count + 1
                """,
                text, source_lang, target_lang, 
                translation, quality_score, expires_at
            )
    
    async def get_cannabis_term(
        self,
        term_key: str,
        language: str,
        category: str = None
    ) -> str:
        """Get cannabis-specific term in target language"""
        async with self.db_pool.acquire() as conn:
            query = """
                SELECT term_en, term_es, term_fr, term_pt, term_zh, term_ar
                FROM cannabis_terminology
                WHERE term_key = $1
            """
            params = [term_key]
            
            if category:
                query += " AND category = $2"
                params.append(category)
            
            result = await conn.fetchrow(query, *params)
            
            if result:
                term_field = f"term_{language}"
                return result.get(term_field) or result['term_en']
        
        return term_key  # Return original if not found
    
    async def get_product_translation(
        self,
        product_id: int,
        language: str
    ) -> Dict:
        """Get translated product information"""
        async with self.db_pool.acquire() as conn:
            result = await conn.fetchrow(
                """
                SELECT 
                    name_en, name_es, name_fr, name_pt, name_zh, name_ar,
                    description_en, description_es, description_fr, 
                    description_pt, description_zh, description_ar,
                    effects_en, effects_es, effects_fr, 
                    effects_pt, effects_zh, effects_ar
                FROM multilingual_products
                WHERE product_id = $1
                """,
                product_id
            )
            
            if result:
                return {
                    'name': result[f'name_{language}'] or result['name_en'],
                    'description': result[f'description_{language}'] or result['description_en'],
                    'effects': result[f'effects_{language}'] or result['effects_en']
                }
        
        return None
    
    async def translate_products(
        self,
        products: List[Dict],
        target_language: str
    ) -> List[Dict]:
        """Translate a list of products to target language"""
        if target_language == 'en':
            return products
        
        translated_products = []
        for product in products:
            # Get translated product info
            translation = await self.get_product_translation(
                product.get('id'),
                target_language
            )
            
            if translation:
                product_copy = product.copy()
                product_copy['product_name'] = translation['name']
                product_copy['description'] = translation['description']
                product_copy['effects'] = translation['effects']
                translated_products.append(product_copy)
            else:
                # Fallback to original
                translated_products.append(product)
        
        return translated_products
    
    async def validate_response_quality(
        self,
        response: str,
        language: str,
        context: Dict
    ) -> Dict:
        """Validate quality of multilingual response"""
        
        checks = {
            'language_consistency': await self._check_language_consistency(
                response, language
            ),
            'completeness': self._check_completeness(response, context),
            'cannabis_accuracy': await self._check_cannabis_accuracy(
                response, context
            ),
            'cultural_appropriateness': self._check_cultural_appropriateness(
                response, language
            )
        }
        
        # Calculate weighted score
        weights = {
            'language_consistency': 0.30,
            'completeness': 0.25,
            'cannabis_accuracy': 0.30,
            'cultural_appropriateness': 0.15
        }
        
        total_score = sum(
            checks[key] * weights[key] 
            for key in checks
        )
        
        threshold = self.quality_thresholds.get(language, 0.75)
        
        return {
            'passed': total_score >= threshold,
            'score': total_score,
            'threshold': threshold,
            'details': checks,
            'should_fallback': total_score < threshold * 0.8
        }
    
    async def _check_language_consistency(
        self, 
        response: str, 
        expected_lang: str
    ) -> float:
        """Check if response is in the expected language"""
        detected_lang, confidence = await self.detect_language(response)
        
        if detected_lang == expected_lang:
            return min(1.0, confidence + 0.1)
        elif expected_lang == 'zh' and detected_lang in ['zh-cn', 'zh-tw']:
            return confidence
        else:
            return max(0.0, confidence - 0.5)
    
    def _check_completeness(self, response: str, context: Dict) -> float:
        """Check if response is complete"""
        # Basic completeness checks
        if not response or len(response) < 10:
            return 0.0
        
        # Check for incomplete sentences
        if response.rstrip()[-1] not in '.!?。！？':
            return 0.7
        
        # Check if it addresses the intent
        intent = context.get('intent', '')
        if intent == 'product_search' and '$' not in response:
            return 0.8  # Should include price
        
        return 1.0
    
    async def _check_cannabis_accuracy(
        self, 
        response: str, 
        context: Dict
    ) -> float:
        """Check cannabis information accuracy"""
        score = 1.0
        
        # Check for incorrect terminology
        incorrect_terms = {
            'marijuana': -0.2,  # Prefer "cannabis"
            'dope': -0.3,
            'weed': -0.1  # Informal but sometimes ok
        }
        
        response_lower = response.lower()
        for term, penalty in incorrect_terms.items():
            if term in response_lower:
                score += penalty
        
        # Check for medical claims (should be avoided)
        medical_claims = ['cure', 'treat', 'heal', 'medicine']
        if any(claim in response_lower for claim in medical_claims):
            score -= 0.5
        
        return max(0.0, min(1.0, score))
    
    def _check_cultural_appropriateness(
        self, 
        response: str, 
        language: str
    ) -> float:
        """Check cultural appropriateness of response"""
        score = 1.0
        
        # Language-specific checks
        if language == 'ar':
            # Arabic: Should be more formal
            if '!' in response:  # Too casual
                score -= 0.2
        elif language == 'zh':
            # Chinese: Check for appropriate honorifics
            if '您' not in response and '你' in response:
                score -= 0.1  # Should use formal "you"
        elif language == 'fr':
            # French: Check for appropriate formality
            if 'tu' in response.lower():
                score -= 0.1  # Should use "vous" for customers
        
        return max(0.0, score)
    
    async def log_conversation(
        self,
        session_id: str,
        customer_id: str,
        message: str,
        message_language: str,
        response: str,
        response_language: str,
        quality_score: float,
        processing_time: int,
        fallback_used: bool = False
    ):
        """Log multilingual conversation"""
        async with self.db_pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO multilingual_conversations
                (session_id, customer_id, message_original, message_language,
                 response_text, response_language, quality_score,
                 processing_time_ms, fallback_used, created_at)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, CURRENT_TIMESTAMP)
                """,
                session_id, customer_id, message, message_language,
                response, response_language, quality_score,
                processing_time, fallback_used
            )
    
    async def update_language_metrics(
        self,
        language: str,
        quality_score: float,
        response_time: int,
        fallback_used: bool = False
    ):
        """Update language performance metrics"""
        today = datetime.now().date()
        
        async with self.db_pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO language_quality_metrics
                (language_code, date, total_requests, successful_requests,
                 fallback_count, avg_quality_score, avg_response_time_ms)
                VALUES ($1, $2, 1, $3, $4, $5, $6)
                ON CONFLICT (language_code, date)
                DO UPDATE SET
                    total_requests = language_quality_metrics.total_requests + 1,
                    successful_requests = language_quality_metrics.successful_requests + $3,
                    fallback_count = language_quality_metrics.fallback_count + $4,
                    avg_quality_score = (
                        language_quality_metrics.avg_quality_score * language_quality_metrics.total_requests + $5
                    ) / (language_quality_metrics.total_requests + 1),
                    avg_response_time_ms = (
                        language_quality_metrics.avg_response_time_ms * language_quality_metrics.total_requests + $6
                    ) / (language_quality_metrics.total_requests + 1)
                """,
                language, today,
                1 if quality_score > 0.7 else 0,
                1 if fallback_used else 0,
                quality_score, response_time
            )
    
    def get_language_config(self, language_code: str) -> LanguageConfig:
        """Get configuration for a language"""
        return self.language_configs.get(
            language_code,
            self.language_configs['en']
        )
    
    def adjust_max_tokens(self, base_tokens: int, language: str) -> int:
        """Adjust max tokens based on language efficiency"""
        config = self.get_language_config(language)
        return int(base_tokens * config.max_tokens_multiplier)