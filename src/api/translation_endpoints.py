"""
Translation API Endpoints
Provides RESTful API for translation services with caching
"""

from fastapi import APIRouter, HTTPException, Depends, Query, BackgroundTasks
from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field
import logging
import asyncpg
import redis.asyncio as redis
import os

from services.translation_service import TranslationService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/translate", tags=["translation"])

# Database and Redis connection pools
db_pool = None
redis_client = None


async def get_db_pool():
    """Get or create database connection pool"""
    global db_pool
    if db_pool is None:
        db_pool = await asyncpg.create_pool(
            host=os.getenv('DB_HOST', 'localhost'),
            port=int(os.getenv('DB_PORT', 5434)),
            database=os.getenv('DB_NAME', 'ai_engine'),
            user=os.getenv('DB_USER', 'weedgo'),
            password=os.getenv('DB_PASSWORD', 'your_password_here'),
            min_size=1,
            max_size=10
        )
    return db_pool


async def get_redis_client():
    """Get or create Redis client"""
    global redis_client
    if redis_client is None:
        try:
            redis_client = await redis.from_url(
                os.getenv('REDIS_URL', 'redis://localhost:6379'),
                encoding="utf-8",
                decode_responses=True
            )
            # Test connection
            await redis_client.ping()
            logger.info("Redis connection established")
        except Exception as e:
            logger.warning(f"Redis not available, using memory cache only: {e}")
            redis_client = None
    return redis_client


# Pydantic Models
class TranslateRequest(BaseModel):
    text: str = Field(..., description="Text to translate")
    target_language: str = Field(..., description="Target language code (e.g., 'fr', 'es')")
    source_language: str = Field(default='en', description="Source language code")
    context: Optional[str] = Field(None, description="Context for disambiguation")
    namespace: Optional[str] = Field(None, description="Namespace for grouping")
    use_cache: bool = Field(default=True, description="Whether to use cached translations")


class BulkTranslateItem(BaseModel):
    text: str = Field(..., description="Text to translate")
    context: Optional[str] = Field(None, description="Context for this specific text")
    namespace: Optional[str] = Field(None, description="Namespace for this specific text")


class BulkTranslateRequest(BaseModel):
    texts: List[BulkTranslateItem] = Field(..., description="List of texts to translate")
    target_language: str = Field(..., description="Target language code")
    source_language: str = Field(default='en', description="Source language code")


class TranslationOverrideRequest(BaseModel):
    source_text: str
    target_language: str
    override_text: str
    reason: Optional[str] = None
    context: Optional[str] = None
    namespace: Optional[str] = None


async def get_translation_service():
    """Get translation service instance"""
    pool = await get_db_pool()
    redis_cli = await get_redis_client()
    conn = await pool.acquire()
    try:
        yield TranslationService(conn, redis_cli)
    finally:
        await pool.release(conn)


@router.post("/")
async def translate_single(
    request: TranslateRequest,
    service: TranslationService = Depends(get_translation_service)
):
    """
    Translate a single text to the target language
    
    Uses multi-tier caching:
    1. Memory cache (fastest)
    2. Redis cache (fast)
    3. Database (persistent)
    4. AI model (slowest, for new translations)
    """
    try:
        result = await service.translate_single(
            text=request.text,
            target_language=request.target_language,
            source_language=request.source_language,
            context=request.context,
            namespace=request.namespace,
            use_cache=request.use_cache
        )
        
        return {
            "success": True,
            "original": request.text,
            "translated": result.get("translated_text"),
            "target_language": request.target_language,
            "cache_hit": result.get("cache_hit", False),
            "source": result.get("source", "unknown")
        }
        
    except Exception as e:
        logger.error(f"Translation error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/bulk")
async def translate_bulk(
    request: BulkTranslateRequest,
    background_tasks: BackgroundTasks,
    service: TranslationService = Depends(get_translation_service)
):
    """
    Translate multiple texts efficiently
    
    Optimized for bulk operations with:
    - Concurrent processing
    - Batch caching
    - Statistics tracking
    """
    try:
        # Convert request items to dicts
        texts = [
            {
                "text": item.text,
                "context": item.context,
                "namespace": item.namespace
            }
            for item in request.texts
        ]
        
        result = await service.translate_bulk(
            texts=texts,
            target_language=request.target_language,
            source_language=request.source_language
        )
        
        # Warm cache in background for this language
        if result["statistics"]["from_ai"] > 0:
            background_tasks.add_task(
                service.warm_cache,
                request.target_language,
                limit=50
            )
        
        return {
            "success": True,
            "translations": result["translations"],
            "statistics": result["statistics"],
            "target_language": request.target_language
        }
        
    except Exception as e:
        logger.error(f"Bulk translation error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/languages")
async def get_supported_languages(
    service: TranslationService = Depends(get_translation_service)
):
    """Get list of supported languages with their metadata"""
    try:
        languages = await service.get_supported_languages()
        return {
            "success": True,
            "languages": languages,
            "count": len(languages)
        }
    except Exception as e:
        logger.error(f"Error fetching languages: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats")
async def get_translation_stats(
    language: Optional[str] = Query(None, description="Filter by language code"),
    service: TranslationService = Depends(get_translation_service)
):
    """Get translation statistics"""
    try:
        stats = await service.get_translation_stats(language)
        return {
            "success": True,
            "statistics": stats,
            "language": language
        }
    except Exception as e:
        logger.error(f"Error fetching stats: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/override")
async def create_translation_override(
    request: TranslationOverrideRequest,
    service: TranslationService = Depends(get_translation_service)
):
    """
    Create a manual override for a translation
    Useful for correcting AI translations
    """
    try:
        # First, find the translation ID
        query = """
            SELECT id FROM translations
            WHERE source_text = $1
            AND target_language = $2
            AND ($3::text IS NULL OR context = $3)
            AND ($4::text IS NULL OR namespace = $4)
            LIMIT 1
        """
        
        row = await service.db.fetchrow(
            query,
            request.source_text,
            request.target_language,
            request.context,
            request.namespace
        )
        
        if not row:
            raise HTTPException(
                status_code=404,
                detail="Translation not found. Translate the text first before overriding."
            )
        
        # Create the override
        insert_query = """
            INSERT INTO translation_overrides (
                translation_id, override_text, reason, created_by
            ) VALUES ($1, $2, $3, $4)
            RETURNING id
        """
        
        override_id = await service.db.fetchval(
            insert_query,
            row['id'],
            request.override_text,
            request.reason,
            "api_user"  # In production, get from auth
        )
        
        # Clear caches for this translation
        cache_key = service._generate_cache_key(
            request.source_text,
            request.target_language,
            request.context,
            request.namespace
        )
        
        # Clear from memory cache
        if cache_key in service.memory_cache.cache:
            del service.memory_cache.cache[cache_key]
        
        # Clear from Redis
        if service.redis:
            try:
                await service.redis.delete(cache_key)
            except Exception as e:
                logger.warning(f"Failed to clear Redis cache: {e}")
        
        return {
            "success": True,
            "override_id": str(override_id),
            "message": "Translation override created successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating override: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/warm-cache/{language}")
async def warm_cache(
    language: str,
    background_tasks: BackgroundTasks,
    limit: int = Query(100, ge=1, le=1000),
    service: TranslationService = Depends(get_translation_service)
):
    """
    Pre-load most used translations into cache
    Useful for improving performance for new language users
    """
    try:
        # Run cache warming in background
        background_tasks.add_task(
            service.warm_cache,
            language,
            limit
        )
        
        return {
            "success": True,
            "message": f"Cache warming initiated for {language} with {limit} translations",
            "status": "processing"
        }
        
    except Exception as e:
        logger.error(f"Error warming cache: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/cache")
async def clear_cache(
    language: Optional[str] = Query(None, description="Clear cache for specific language only"),
    service: TranslationService = Depends(get_translation_service)
):
    """
    Clear translation caches
    Useful for forcing fresh translations
    """
    try:
        # Clear memory cache
        if language:
            # Clear specific language entries
            keys_to_remove = [
                k for k in service.memory_cache.cache.keys()
                if language in k
            ]
            for key in keys_to_remove:
                del service.memory_cache.cache[key]
            cleared_memory = len(keys_to_remove)
        else:
            # Clear all
            service.memory_cache.clear()
            cleared_memory = "all"
        
        # Clear Redis cache
        cleared_redis = 0
        if service.redis:
            try:
                if language:
                    # Clear specific language patterns
                    pattern = f"trans:*{language}*"
                    keys = await service.redis.keys(pattern)
                    if keys:
                        cleared_redis = await service.redis.delete(*keys)
                else:
                    # Clear all translation keys
                    keys = await service.redis.keys("trans:*")
                    if keys:
                        cleared_redis = await service.redis.delete(*keys)
            except Exception as e:
                logger.warning(f"Failed to clear Redis cache: {e}")
        
        return {
            "success": True,
            "cleared": {
                "memory": cleared_memory,
                "redis": cleared_redis
            },
            "language": language
        }
        
    except Exception as e:
        logger.error(f"Error clearing cache: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# Health check endpoint
@router.get("/health")
async def health_check():
    """Check translation service health"""
    try:
        # Check database
        pool = await get_db_pool()
        async with pool.acquire() as conn:
            await conn.fetchval("SELECT 1")
        
        # Check Redis
        redis_status = "not_configured"
        redis_cli = await get_redis_client()
        if redis_cli:
            try:
                await redis_cli.ping()
                redis_status = "healthy"
            except:
                redis_status = "unhealthy"
        
        return {
            "status": "healthy",
            "database": "connected",
            "redis": redis_status
        }
        
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e)
        }