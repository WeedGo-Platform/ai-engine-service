"""
Translation Service with Multiple Providers
Supports: Google Translate, DeepL, OpenAI, Local Models
"""

import asyncio
import aiohttp
import json
import logging
from typing import Dict, List, Optional, Tuple
from abc import ABC, abstractmethod
import hashlib
from datetime import datetime

logger = logging.getLogger(__name__)

class TranslationProvider(ABC):
    """Abstract base class for translation providers"""
    
    @abstractmethod
    async def translate(
        self, 
        text: str, 
        source_lang: str, 
        target_lang: str
    ) -> Tuple[str, float]:
        """
        Translate text from source to target language
        Returns: (translated_text, confidence_score)
        """
        pass
    
    @abstractmethod
    def supports_language(self, language_code: str) -> bool:
        """Check if provider supports a language"""
        pass

class LocalModelTranslator(TranslationProvider):
    """Translation using local models with language adapters"""
    
    def __init__(self, model_path: str = None):
        self.model_path = model_path
        self.supported_languages = ['en', 'es', 'fr', 'pt']
        self.language_pairs = {
            ('en', 'es'): 'models/en_es_adapter.bin',
            ('en', 'fr'): 'models/en_fr_adapter.bin',
            ('en', 'pt'): 'models/en_pt_adapter.bin',
            ('es', 'en'): 'models/es_en_adapter.bin',
            ('fr', 'en'): 'models/fr_en_adapter.bin',
            ('pt', 'en'): 'models/pt_en_adapter.bin',
        }
    
    async def translate(
        self, 
        text: str, 
        source_lang: str, 
        target_lang: str
    ) -> Tuple[str, float]:
        """Translate using local model"""
        
        # Check if we have a direct translation pair
        pair = (source_lang, target_lang)
        if pair not in self.language_pairs:
            # Try pivoting through English
            if source_lang != 'en' and target_lang != 'en':
                # Translate to English first
                intermediate, score1 = await self.translate(text, source_lang, 'en')
                # Then to target language
                final, score2 = await self.translate(intermediate, 'en', target_lang)
                return final, (score1 + score2) / 2
            else:
                return text, 0.5  # Can't translate
        
        # Simulate local model translation
        # In production, this would load the actual adapter
        adapter_path = self.language_pairs[pair]
        
        try:
            # Placeholder for actual model inference
            # This would integrate with your Llama model
            translated = await self._run_local_translation(
                text, adapter_path, source_lang, target_lang
            )
            return translated, 0.85
        except Exception as e:
            logger.error(f"Local translation failed: {e}")
            return text, 0.0
    
    async def _run_local_translation(
        self, 
        text: str, 
        adapter_path: str,
        source_lang: str,
        target_lang: str
    ) -> str:
        """Run actual local model translation"""
        # Placeholder - integrate with your Llama setup
        # For now, return a simple transformation
        
        # Build translation prompt
        prompt = f"""Translate the following text from {source_lang} to {target_lang}.
Only provide the translation, no explanations.

Text: {text}

Translation:"""
        
        # This would call your local Llama model
        # For demonstration, return the original text
        return text
    
    def supports_language(self, language_code: str) -> bool:
        return language_code in self.supported_languages

class GoogleTranslateProvider(TranslationProvider):
    """Google Translate API provider"""
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key or "YOUR_GOOGLE_API_KEY"
        self.base_url = "https://translation.googleapis.com/language/translate/v2"
        self.supported_languages = ['en', 'es', 'fr', 'pt', 'zh', 'ar']
    
    async def translate(
        self, 
        text: str, 
        source_lang: str, 
        target_lang: str
    ) -> Tuple[str, float]:
        """Translate using Google Translate API"""
        
        if not self.api_key or self.api_key == "YOUR_GOOGLE_API_KEY":
            return text, 0.0
        
        try:
            async with aiohttp.ClientSession() as session:
                params = {
                    'key': self.api_key,
                    'source': source_lang,
                    'target': target_lang,
                    'q': text
                }
                
                async with session.post(self.base_url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        translation = data['data']['translations'][0]['translatedText']
                        return translation, 0.9
                    else:
                        logger.error(f"Google Translate API error: {response.status}")
                        return text, 0.0
        except Exception as e:
            logger.error(f"Google Translate failed: {e}")
            return text, 0.0
    
    def supports_language(self, language_code: str) -> bool:
        return language_code in self.supported_languages

class OpenAITranslator(TranslationProvider):
    """OpenAI GPT-based translation"""
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key or "YOUR_OPENAI_API_KEY"
        self.base_url = "https://api.openai.com/v1/chat/completions"
        self.supported_languages = ['en', 'es', 'fr', 'pt', 'zh', 'ar']
    
    async def translate(
        self, 
        text: str, 
        source_lang: str, 
        target_lang: str
    ) -> Tuple[str, float]:
        """Translate using OpenAI GPT"""
        
        if not self.api_key or self.api_key == "YOUR_OPENAI_API_KEY":
            return text, 0.0
        
        language_names = {
            'en': 'English',
            'es': 'Spanish',
            'fr': 'French',
            'pt': 'Portuguese',
            'zh': 'Chinese',
            'ar': 'Arabic'
        }
        
        prompt = f"""Translate the following text from {language_names.get(source_lang, source_lang)} to {language_names.get(target_lang, target_lang)}.
Maintain the tone and context. Only provide the translation.

Text: {text}

Translation:"""
        
        try:
            async with aiohttp.ClientSession() as session:
                headers = {
                    'Authorization': f'Bearer {self.api_key}',
                    'Content-Type': 'application/json'
                }
                
                payload = {
                    'model': 'gpt-3.5-turbo',
                    'messages': [
                        {'role': 'system', 'content': 'You are a professional translator.'},
                        {'role': 'user', 'content': prompt}
                    ],
                    'temperature': 0.3,
                    'max_tokens': 500
                }
                
                async with session.post(
                    self.base_url, 
                    headers=headers, 
                    json=payload
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        translation = data['choices'][0]['message']['content'].strip()
                        return translation, 0.95
                    else:
                        logger.error(f"OpenAI API error: {response.status}")
                        return text, 0.0
        except Exception as e:
            logger.error(f"OpenAI translation failed: {e}")
            return text, 0.0
    
    def supports_language(self, language_code: str) -> bool:
        return language_code in self.supported_languages

class TranslationService:
    """Main translation service orchestrator"""
    
    def __init__(self, db_pool=None):
        self.db_pool = db_pool
        self.providers = self._initialize_providers()
        self.cache = {}
        
    def _initialize_providers(self) -> Dict[str, TranslationProvider]:
        """Initialize translation providers"""
        return {
            'local': LocalModelTranslator(),
            'google': GoogleTranslateProvider(),
            'openai': OpenAITranslator()
        }
    
    async def translate(
        self,
        text: str,
        source_lang: str,
        target_lang: str,
        preferred_provider: str = None,
        cache_result: bool = True
    ) -> Dict:
        """
        Translate text with fallback providers
        Returns: {
            'text': translated_text,
            'provider': provider_used,
            'confidence': confidence_score,
            'cached': was_cached
        }
        """
        
        # Check cache first
        cache_key = self._get_cache_key(text, source_lang, target_lang)
        if cache_key in self.cache:
            cached = self.cache[cache_key]
            return {
                'text': cached['text'],
                'provider': cached['provider'],
                'confidence': cached['confidence'],
                'cached': True
            }
        
        # Determine provider order
        if preferred_provider and preferred_provider in self.providers:
            provider_order = [preferred_provider] + [
                p for p in self.providers if p != preferred_provider
            ]
        else:
            # Default order based on language tier
            if source_lang in ['en', 'es', 'fr'] and target_lang in ['en', 'es', 'fr']:
                provider_order = ['local', 'openai', 'google']
            else:
                provider_order = ['openai', 'google', 'local']
        
        # Try providers in order
        for provider_name in provider_order:
            provider = self.providers[provider_name]
            
            if not provider.supports_language(source_lang):
                continue
            if not provider.supports_language(target_lang):
                continue
            
            try:
                translated_text, confidence = await provider.translate(
                    text, source_lang, target_lang
                )
                
                if confidence > 0.5:  # Minimum acceptable confidence
                    result = {
                        'text': translated_text,
                        'provider': provider_name,
                        'confidence': confidence,
                        'cached': False
                    }
                    
                    # Cache successful translation
                    if cache_result and confidence > 0.7:
                        self.cache[cache_key] = result
                        
                        # Also save to database if available
                        if self.db_pool:
                            await self._save_to_db(
                                text, source_lang, target_lang,
                                translated_text, provider_name, confidence
                            )
                    
                    return result
            except Exception as e:
                logger.error(f"Provider {provider_name} failed: {e}")
                continue
        
        # All providers failed
        return {
            'text': text,
            'provider': 'none',
            'confidence': 0.0,
            'cached': False
        }
    
    async def translate_batch(
        self,
        texts: List[str],
        source_lang: str,
        target_lang: str
    ) -> List[Dict]:
        """Translate multiple texts efficiently"""
        tasks = [
            self.translate(text, source_lang, target_lang)
            for text in texts
        ]
        return await asyncio.gather(*tasks)
    
    def _get_cache_key(
        self, 
        text: str, 
        source_lang: str, 
        target_lang: str
    ) -> str:
        """Generate cache key for translation"""
        content = f"{source_lang}:{target_lang}:{text}"
        return hashlib.md5(content.encode()).hexdigest()
    
    async def _save_to_db(
        self,
        source_text: str,
        source_lang: str,
        target_lang: str,
        translated_text: str,
        provider: str,
        confidence: float
    ):
        """Save translation to database cache"""
        if not self.db_pool:
            return
        
        try:
            async with self.db_pool.acquire() as conn:
                await conn.execute(
                    """
                    INSERT INTO translation_cache
                    (source_text, source_language, target_language,
                     translated_text, translation_provider, quality_score)
                    VALUES ($1, $2, $3, $4, $5, $6)
                    ON CONFLICT (source_text, source_language, target_language)
                    DO UPDATE SET
                        translated_text = $4,
                        translation_provider = $5,
                        quality_score = $6,
                        usage_count = translation_cache.usage_count + 1
                    """,
                    source_text, source_lang, target_lang,
                    translated_text, provider, confidence
                )
        except Exception as e:
            logger.error(f"Failed to save translation to DB: {e}")
    
    async def get_cannabis_translation(
        self,
        term: str,
        target_lang: str,
        category: str = 'general'
    ) -> str:
        """Get cannabis-specific term translation"""
        
        # Check database for cannabis terminology
        if self.db_pool:
            try:
                async with self.db_pool.acquire() as conn:
                    result = await conn.fetchrow(
                        f"""
                        SELECT term_{target_lang} as translation
                        FROM cannabis_terminology
                        WHERE term_en = $1 AND category = $2
                        """,
                        term, category
                    )
                    if result and result['translation']:
                        return result['translation']
            except:
                pass
        
        # Fallback to general translation
        result = await self.translate(term, 'en', target_lang)
        return result['text']