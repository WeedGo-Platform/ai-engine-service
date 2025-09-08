"""
Translation Service with Multi-Layer Caching
Provides AI-powered translation with memory cache, Redis cache, and database persistence
"""

import asyncio
import json
import hashlib
import logging
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta
from uuid import UUID
import asyncpg
import redis.asyncio as redis
from collections import OrderedDict

logger = logging.getLogger(__name__)


class TranslationCache:
    """In-memory LRU cache for hot translations"""
    
    def __init__(self, max_size: int = 1000):
        self.cache: OrderedDict = OrderedDict()
        self.max_size = max_size
    
    def get(self, key: str) -> Optional[str]:
        """Get translation from cache, moving to end (most recent)"""
        if key in self.cache:
            self.cache.move_to_end(key)
            return self.cache[key]
        return None
    
    def set(self, key: str, value: str):
        """Add translation to cache with LRU eviction"""
        if key in self.cache:
            self.cache.move_to_end(key)
        else:
            if len(self.cache) >= self.max_size:
                self.cache.popitem(last=False)  # Remove oldest
            self.cache[key] = value
    
    def clear(self):
        """Clear the cache"""
        self.cache.clear()


class TranslationService:
    """Service for managing translations with multi-tier caching"""
    
    def __init__(self, db_conn: asyncpg.Connection, redis_client: Optional[redis.Redis] = None):
        self.db = db_conn
        self.redis = redis_client
        self.memory_cache = TranslationCache(max_size=1000)
        self.cache_ttl = 3600  # 1 hour Redis cache TTL
        
    def _generate_cache_key(self, source_text: str, target_language: str, 
                           context: Optional[str] = None, namespace: Optional[str] = None) -> str:
        """Generate unique cache key for translation"""
        key_parts = [source_text, target_language]
        if context:
            key_parts.append(context)
        if namespace:
            key_parts.append(namespace)
        
        key_string = "|".join(key_parts)
        # Use hash for very long texts
        if len(key_string) > 200:
            return f"trans:{hashlib.md5(key_string.encode()).hexdigest()}"
        return f"trans:{key_string}"
    
    async def translate_single(
        self,
        text: str,
        target_language: str,
        source_language: str = 'en',
        context: Optional[str] = None,
        namespace: Optional[str] = None,
        use_cache: bool = True
    ) -> Dict[str, Any]:
        """
        Translate a single text with multi-tier caching
        
        Returns:
            Dict with translated_text, cache_hit, source
        """
        if not text or not target_language:
            return {
                "translated_text": text,
                "cache_hit": False,
                "source": "none",
                "error": "Invalid input"
            }
        
        # If same language, return as-is
        if source_language == target_language:
            return {
                "translated_text": text,
                "cache_hit": True,
                "source": "same_language"
            }
        
        cache_key = self._generate_cache_key(text, target_language, context, namespace)
        
        # 1. Check memory cache (fastest)
        if use_cache:
            cached = self.memory_cache.get(cache_key)
            if cached:
                await self._update_usage_stats(text, target_language, context, namespace)
                return {
                    "translated_text": cached,
                    "cache_hit": True,
                    "source": "memory"
                }
        
        # 2. Check Redis cache (fast)
        if use_cache and self.redis:
            try:
                cached = await self.redis.get(cache_key)
                if cached:
                    translated_text = cached.decode('utf-8') if isinstance(cached, bytes) else cached
                    self.memory_cache.set(cache_key, translated_text)
                    await self._update_usage_stats(text, target_language, context, namespace)
                    return {
                        "translated_text": translated_text,
                        "cache_hit": True,
                        "source": "redis"
                    }
            except Exception as e:
                logger.warning(f"Redis cache error: {e}")
        
        # 3. Check database (slower but persistent)
        if use_cache:
            db_translation = await self._get_from_database(
                text, source_language, target_language, context, namespace
            )
            if db_translation:
                # Populate caches
                translated_text = db_translation['translated_text']
                self.memory_cache.set(cache_key, translated_text)
                if self.redis:
                    try:
                        await self.redis.setex(cache_key, self.cache_ttl, translated_text)
                    except Exception as e:
                        logger.warning(f"Redis cache set error: {e}")
                
                return {
                    "translated_text": translated_text,
                    "cache_hit": True,
                    "source": "database",
                    "is_verified": db_translation.get('is_verified', False)
                }
        
        # 4. Perform AI translation (slowest)
        translated_text = await self._ai_translate(text, source_language, target_language, context)
        
        # Store in all caches
        if use_cache:
            # Save to database
            await self._save_to_database(
                text, source_language, target_language, translated_text,
                context, namespace
            )
            
            # Save to caches
            self.memory_cache.set(cache_key, translated_text)
            if self.redis:
                try:
                    await self.redis.setex(cache_key, self.cache_ttl, translated_text)
                except Exception as e:
                    logger.warning(f"Redis cache set error: {e}")
        
        return {
            "translated_text": translated_text,
            "cache_hit": False,
            "source": "ai_model"
        }
    
    async def translate_bulk(
        self,
        texts: List[Dict[str, Any]],
        target_language: str,
        source_language: str = 'en'
    ) -> Dict[str, Any]:
        """
        Translate multiple texts efficiently
        
        Args:
            texts: List of dicts with 'text', 'context', 'namespace' keys
            target_language: Target language code
            source_language: Source language code
        
        Returns:
            Dict with translations and statistics
        """
        results = []
        stats = {
            "total": len(texts),
            "from_cache": 0,
            "from_ai": 0,
            "errors": 0
        }
        
        # Process in batches for efficiency
        batch_size = 10
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            
            # Create translation tasks
            tasks = []
            for item in batch:
                task = self.translate_single(
                    text=item.get('text', ''),
                    target_language=target_language,
                    source_language=source_language,
                    context=item.get('context'),
                    namespace=item.get('namespace'),
                    use_cache=True
                )
                tasks.append(task)
            
            # Execute batch concurrently
            batch_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for item, result in zip(batch, batch_results):
                if isinstance(result, Exception):
                    stats["errors"] += 1
                    results.append({
                        "original": item.get('text', ''),
                        "translated": None,
                        "error": str(result)
                    })
                else:
                    if result.get('cache_hit'):
                        stats["from_cache"] += 1
                    else:
                        stats["from_ai"] += 1
                    
                    results.append({
                        "original": item.get('text', ''),
                        "translated": result.get('translated_text'),
                        "source": result.get('source'),
                        "cache_hit": result.get('cache_hit', False)
                    })
        
        return {
            "translations": results,
            "statistics": stats,
            "target_language": target_language
        }
    
    async def _get_from_database(
        self,
        source_text: str,
        source_language: str,
        target_language: str,
        context: Optional[str],
        namespace: Optional[str]
    ) -> Optional[Dict[str, Any]]:
        """Get translation from database"""
        try:
            query = """
                SELECT 
                    t.translated_text,
                    t.is_verified,
                    t.confidence_score,
                    COALESCE(o.override_text, t.translated_text) as final_text
                FROM translations t
                LEFT JOIN translation_overrides o ON t.id = o.translation_id AND o.is_active = TRUE
                WHERE t.source_text = $1
                AND t.source_language = $2
                AND t.target_language = $3
                AND ($4::text IS NULL OR t.context = $4)
                AND ($5::text IS NULL OR t.namespace = $5)
                LIMIT 1
            """
            
            row = await self.db.fetchrow(
                query, source_text, source_language, target_language, context, namespace
            )
            
            if row:
                return {
                    'translated_text': row['final_text'],
                    'is_verified': row['is_verified'],
                    'confidence_score': float(row['confidence_score']) if row['confidence_score'] else None
                }
            return None
            
        except Exception as e:
            logger.error(f"Database fetch error: {e}")
            return None
    
    async def _save_to_database(
        self,
        source_text: str,
        source_language: str,
        target_language: str,
        translated_text: str,
        context: Optional[str],
        namespace: Optional[str],
        confidence_score: float = 0.8
    ):
        """Save translation to database"""
        try:
            query = """
                INSERT INTO translations (
                    source_text, source_language, target_language,
                    translated_text, context, namespace,
                    confidence_score, model_version
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                ON CONFLICT (source_text, source_language, target_language, context, namespace)
                DO UPDATE SET
                    usage_count = translations.usage_count + 1,
                    last_used_at = CURRENT_TIMESTAMP
            """
            
            await self.db.execute(
                query,
                source_text, source_language, target_language,
                translated_text, context, namespace,
                confidence_score, "claude-3"
            )
            
        except Exception as e:
            logger.error(f"Database save error: {e}")
    
    async def _update_usage_stats(
        self,
        source_text: str,
        target_language: str,
        context: Optional[str],
        namespace: Optional[str]
    ):
        """Update usage statistics for a translation"""
        try:
            query = """
                UPDATE translations
                SET usage_count = usage_count + 1,
                    last_used_at = CURRENT_TIMESTAMP
                WHERE source_text = $1
                AND target_language = $2
                AND ($3::text IS NULL OR context = $3)
                AND ($4::text IS NULL OR namespace = $4)
            """
            
            await self.db.execute(query, source_text, target_language, context, namespace)
            
        except Exception as e:
            logger.warning(f"Failed to update usage stats: {e}")
    
    async def _ai_translate(
        self,
        text: str,
        source_language: str,
        target_language: str,
        context: Optional[str] = None
    ) -> str:
        """
        Perform AI translation using the model
        This integrates with your existing SmartAIEngine
        """
        try:
            # Import here to avoid circular dependency
            from services.smart_ai_engine_v5 import SmartAIEngineV5
            
            # Get or create AI engine instance
            engine = SmartAIEngineV5()
            
            # Prepare translation prompt
            prompt = f"""Translate the following text from {source_language} to {target_language}.
{f'Context: {context}' if context else ''}
Provide only the translated text without any explanation.

Text to translate: {text}"""
            
            # Get translation from AI model
            response = await engine.process_request({
                'message': prompt,
                'conversation_id': f'translation_{target_language}',
                'user_id': 'system_translation'
            })
            
            if response and 'response' in response:
                return response['response'].strip()
            
            # Fallback if AI fails
            logger.error("AI translation failed, returning original text")
            return text
            
        except Exception as e:
            logger.error(f"AI translation error: {e}")
            # Return original text as fallback
            return text
    
    async def get_supported_languages(self) -> List[Dict[str, Any]]:
        """Get list of supported languages"""
        query = """
            SELECT code, name, native_name, is_rtl, coverage_percentage
            FROM supported_languages
            WHERE is_active = TRUE
            ORDER BY name
        """
        
        rows = await self.db.fetch(query)
        return [dict(row) for row in rows]
    
    async def get_translation_stats(self, language: Optional[str] = None) -> Dict[str, Any]:
        """Get translation statistics"""
        if language:
            query = """
                SELECT 
                    COUNT(*) as total_translations,
                    COUNT(DISTINCT namespace) as namespaces,
                    SUM(usage_count) as total_usage,
                    AVG(confidence_score) as avg_confidence,
                    COUNT(*) FILTER (WHERE is_verified = TRUE) as verified_count
                FROM translations
                WHERE target_language = $1
            """
            row = await self.db.fetchrow(query, language)
        else:
            query = """
                SELECT 
                    target_language,
                    COUNT(*) as total_translations,
                    SUM(usage_count) as total_usage
                FROM translations
                GROUP BY target_language
                ORDER BY total_usage DESC
            """
            rows = await self.db.fetch(query)
            return {
                "languages": [dict(row) for row in rows],
                "total_languages": len(rows)
            }
        
        return dict(row) if row else {}
    
    async def warm_cache(self, language: str, limit: int = 100):
        """Pre-load most used translations into cache"""
        query = """
            SELECT source_text, translated_text, context, namespace
            FROM v_hot_translations
            WHERE target_language = $1
            LIMIT $2
        """
        
        rows = await self.db.fetch(query, language, limit)
        
        for row in rows:
            cache_key = self._generate_cache_key(
                row['source_text'], language, 
                row['context'], row['namespace']
            )
            self.memory_cache.set(cache_key, row['translated_text'])
            
            if self.redis:
                try:
                    await self.redis.setex(cache_key, self.cache_ttl, row['translated_text'])
                except Exception as e:
                    logger.warning(f"Failed to warm Redis cache: {e}")
        
        return len(rows)