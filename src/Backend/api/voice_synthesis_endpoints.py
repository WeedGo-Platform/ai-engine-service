"""
Voice Synthesis API Endpoints - Personality-Aware TTS
Integrates personality system with VoiceModelRouter for voice synthesis
"""

import os
import asyncio
import logging
from pathlib import Path
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Header
from fastapi.responses import Response
from pydantic import BaseModel
import asyncpg

from core.voice.voice_model_router import VoiceModelRouter, SynthesisContext, VoiceQuality
from core.voice.voice_cache import VoiceCache

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/voice-synthesis", tags=["voice-synthesis"])

# Global instances (initialized on startup)
voice_router: Optional[VoiceModelRouter] = None
voice_cache: Optional[VoiceCache] = None


class VoiceSynthesisRequest(BaseModel):
    """Request model for voice synthesis"""
    text: str
    personality_id: str
    language: str = "en"
    speed: float = 1.0
    pitch: float = 0.0
    quality: str = "high"  # highest, high, medium, fast

    class Config:
        json_schema_extra = {
            "example": {
                "text": "Hello! Welcome to WeedGo. How can I help you today?",
                "personality_id": "00000000-0000-0000-0001-000000000001",
                "language": "en",
                "speed": 1.0,
                "pitch": 0.0,
                "quality": "high"
            }
        }


class VoiceSynthesisResponse(BaseModel):
    """Response model for voice synthesis"""
    success: bool
    provider: str
    duration_ms: float
    sample_rate: int
    message: str


async def get_db_connection():
    """Get database connection"""
    return await asyncpg.connect(
        host=os.getenv("DB_HOST", "localhost"),
        port=int(os.getenv("DB_PORT", 5434)),
        database=os.getenv("DB_NAME", "ai_engine"),
        user=os.getenv("DB_USER", "weedgo"),
        password=os.getenv("DB_PASSWORD", "weedgo123")
    )


async def get_voice_router() -> VoiceModelRouter:
    """Get or initialize voice router"""
    global voice_router

    if voice_router is None:
        logger.info("Initializing VoiceModelRouter...")
        voice_router = VoiceModelRouter(device="cpu")  # TODO: Auto-detect GPU
        success = await voice_router.initialize()

        if not success:
            raise HTTPException(
                status_code=503,
                detail="Voice synthesis service unavailable"
            )

        logger.info("VoiceModelRouter initialized successfully")

    return voice_router


def get_voice_cache() -> VoiceCache:
    """Get or initialize voice cache"""
    global voice_cache

    if voice_cache is None:
        logger.info("Initializing VoiceCache...")
        voice_cache = VoiceCache(
            redis_host=os.getenv("REDIS_HOST", "localhost"),
            redis_port=int(os.getenv("REDIS_PORT", 6379)),
            redis_db=int(os.getenv("REDIS_VOICE_DB", 2)),  # Use DB 2 for voice cache
            ttl_days=7,
            max_audio_size_mb=10
        )
        logger.info("VoiceCache initialized successfully")

    return voice_cache


@router.post("/synthesize", response_model=VoiceSynthesisResponse)
async def synthesize_voice(
    request: VoiceSynthesisRequest,
    authorization: Optional[str] = Header(None)
):
    """
    Synthesize speech using personality voice

    This endpoint:
    1. Loads personality from database
    2. Gets voice sample path from personality voice_config
    3. Uses VoiceModelRouter to synthesize with appropriate provider
    4. Returns audio as MP3 or WAV

    Args:
        request: Voice synthesis request
        authorization: Bearer token

    Returns:
        Audio file (audio/wav or audio/mpeg)
    """
    try:
        # Get voice router and cache
        router = await get_voice_router()
        cache = get_voice_cache()

        # Check cache first
        cached = cache.get(
            text=request.text,
            personality_id=request.personality_id,
            language=request.language,
            speed=request.speed,
            pitch=request.pitch,
            quality=request.quality
        )

        if cached:
            # Cache hit - return cached audio
            logger.info(f"✓ Cache HIT - returning cached audio")
            return Response(
                content=cached["audio_data"],
                media_type="audio/wav",
                headers={
                    "Content-Disposition": f"attachment; filename=voice_{request.personality_id[:8]}.wav",
                    "X-Provider": cached["metadata"].get("provider", "unknown"),
                    "X-Duration-MS": str(int(cached["metadata"].get("duration_ms", 0))),
                    "X-Sample-Rate": str(cached["metadata"].get("sample_rate", 0)),
                    "X-Cache-Status": "HIT"
                }
            )

        # Cache miss - synthesize
        # Get personality from database
        conn = await get_db_connection()

        try:
            personality = await conn.fetchrow("""
                SELECT id, name, personality_name, voice_config
                FROM ai_personalities
                WHERE id = $1 AND is_active = TRUE
            """, request.personality_id)

            if not personality:
                raise HTTPException(
                    status_code=404,
                    detail=f"Active personality not found: {request.personality_id}"
                )

            # Parse voice_config
            voice_config = personality['voice_config']
            if isinstance(voice_config, str):
                import json
                voice_config = json.loads(voice_config)

            # Get voice sample path
            voice_sample_path = voice_config.get('sample_path')
            
            # Auto-load voice sample into XTTS v2 cache if it exists and isn't already loaded
            if voice_sample_path and os.path.exists(voice_sample_path):
                try:
                    # Check if already loaded by checking XTTS v2 handler cache
                    xtts_handler = router.providers.get('xtts_v2')
                    if xtts_handler and hasattr(xtts_handler, 'voice_cache'):
                        if request.personality_id not in xtts_handler.voice_cache:
                            # Not in cache - load it now
                            logger.info(f"Auto-loading voice sample for personality {request.personality_id}")
                            load_results = await router.load_personality_voice(
                                personality_id=request.personality_id,
                                voice_sample_path=voice_sample_path
                            )
                            logger.info(f"Voice sample loaded: {load_results}")
                        else:
                            logger.debug(f"Voice sample already cached for {request.personality_id}")
                except Exception as e:
                    logger.warning(f"Failed to auto-load voice sample: {e}")

            # Map quality string to enum
            quality_map = {
                "highest": VoiceQuality.HIGHEST,
                "high": VoiceQuality.HIGH,
                "medium": VoiceQuality.MEDIUM,
                "fast": VoiceQuality.FAST
            }
            quality = quality_map.get(request.quality, VoiceQuality.HIGH)

            # Create synthesis context
            context = SynthesisContext(
                personality_id=request.personality_id,
                language=request.language,
                speed=request.speed,
                pitch=request.pitch,
                quality=quality,
                prefer_local=True,
                voice_sample_path=voice_sample_path
            )

            logger.info(
                f"Synthesizing voice for personality '{personality['personality_name']}' "
                f"({request.personality_id})"
            )

            # Synthesize audio
            result = await router.synthesize(
                text=request.text,
                context=context
            )

            logger.info(
                f"✓ Synthesis complete: {result.provider} - "
                f"{result.duration_ms:.0f}ms audio, {result.sample_rate}Hz"
            )

            # Cache the result
            cache.set(
                text=request.text,
                personality_id=request.personality_id,
                audio_data=result.audio,
                metadata={
                    "provider": result.provider,
                    "duration_ms": result.duration_ms,
                    "sample_rate": result.sample_rate
                },
                language=request.language,
                speed=request.speed,
                pitch=request.pitch,
                quality=request.quality
            )

            # Return audio file
            return Response(
                content=result.audio,
                media_type="audio/wav",
                headers={
                    "Content-Disposition": f"attachment; filename=voice_{request.personality_id[:8]}.wav",
                    "X-Provider": result.provider,
                    "X-Duration-MS": str(int(result.duration_ms)),
                    "X-Sample-Rate": str(result.sample_rate),
                    "X-Cache-Status": "MISS"
                }
            )

        finally:
            await conn.close()

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Voice synthesis error: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"Voice synthesis failed: {str(e)}"
        )


@router.post("/personalities/{personality_id}/voice/load")
async def load_personality_voice(
    personality_id: str,
    authorization: Optional[str] = Header(None)
):
    """
    Pre-load personality voice sample into voice providers

    This optimizes synthesis by caching the voice sample in memory
    for faster generation on subsequent requests.

    Args:
        personality_id: Personality UUID
        authorization: Bearer token

    Returns:
        Load status for each provider
    """
    try:
        # Get voice router
        router = await get_voice_router()

        # Get personality from database
        conn = await get_db_connection()

        try:
            personality = await conn.fetchrow("""
                SELECT id, personality_name, voice_config
                FROM ai_personalities
                WHERE id = $1
            """, personality_id)

            if not personality:
                raise HTTPException(
                    status_code=404,
                    detail=f"Personality not found: {personality_id}"
                )

            # Parse voice_config
            voice_config = personality['voice_config']
            if isinstance(voice_config, str):
                import json
                voice_config = json.loads(voice_config)

            # Get voice sample path
            voice_sample_path = voice_config.get('sample_path')

            if not voice_sample_path:
                raise HTTPException(
                    status_code=400,
                    detail="Personality has no voice sample uploaded"
                )

            # Verify file exists
            if not Path(voice_sample_path).exists():
                raise HTTPException(
                    status_code=404,
                    detail=f"Voice sample file not found: {voice_sample_path}"
                )

            # Load voice into providers
            logger.info(f"Loading voice sample for personality '{personality['personality_name']}'")

            results = await router.load_personality_voice(
                personality_id=personality_id,
                voice_sample_path=voice_sample_path
            )

            success_count = sum(1 for r in results.values() if r)

            return {
                "success": success_count > 0,
                "personality_id": personality_id,
                "personality_name": personality['personality_name'],
                "providers_loaded": results,
                "message": f"Voice sample loaded into {success_count}/{len(results)} providers"
            }

        finally:
            await conn.close()

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Voice loading error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to load voice sample: {str(e)}"
        )


@router.delete("/personalities/{personality_id}/voice/unload")
async def unload_personality_voice(
    personality_id: str,
    authorization: Optional[str] = Header(None)
):
    """
    Remove personality voice sample from provider cache

    Args:
        personality_id: Personality UUID
        authorization: Bearer token

    Returns:
        Unload status for each provider
    """
    try:
        # Get voice router
        router = await get_voice_router()

        # Remove voice from providers
        logger.info(f"Unloading voice sample for personality {personality_id}")

        results = await router.remove_personality_voice(personality_id)

        success_count = sum(1 for r in results.values() if r)

        return {
            "success": success_count > 0,
            "personality_id": personality_id,
            "providers_unloaded": results,
            "message": f"Voice sample unloaded from {success_count}/{len(results)} providers"
        }

    except Exception as e:
        logger.error(f"Voice unloading error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to unload voice sample: {str(e)}"
        )


@router.get("/providers/status")
async def get_provider_status():
    """
    Get status of all voice providers

    Returns:
        Provider availability and statistics
    """
    try:
        router = await get_voice_router()
        stats = router.get_statistics()

        return {
            "success": True,
            "providers_available": stats["providers_available"],
            "provider_usage": stats["provider_usage"],
            "total_requests": stats["total_requests"],
            "total_cost": stats["total_cost"]
        }

    except Exception as e:
        logger.error(f"Provider status error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get provider status: {str(e)}"
        )


@router.get("/cache/stats")
async def get_cache_stats():
    """
    Get voice cache statistics

    Returns:
        Cache performance metrics
    """
    try:
        cache = get_voice_cache()
        stats = cache.get_stats()

        return {
            "success": True,
            "cache": stats
        }

    except Exception as e:
        logger.error(f"Cache stats error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get cache stats: {str(e)}"
        )


@router.delete("/cache/clear")
async def clear_cache(
    authorization: Optional[str] = Header(None)
):
    """
    Clear all voice cache

    WARNING: This clears ALL cached audio

    Args:
        authorization: Bearer token (admin only)

    Returns:
        Success status
    """
    try:
        cache = get_voice_cache()
        success = cache.clear_all()

        return {
            "success": success,
            "message": "Voice cache cleared successfully"
        }

    except Exception as e:
        logger.error(f"Cache clear error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to clear cache: {str(e)}"
        )


@router.delete("/personalities/{personality_id}/cache")
async def invalidate_personality_cache(
    personality_id: str,
    authorization: Optional[str] = Header(None)
):
    """
    Invalidate cache for a specific personality

    Use this when personality voice sample is updated or deleted

    Args:
        personality_id: Personality UUID
        authorization: Bearer token

    Returns:
        Number of cache entries deleted
    """
    try:
        cache = get_voice_cache()
        deleted_count = cache.invalidate_personality(personality_id)

        return {
            "success": True,
            "personality_id": personality_id,
            "deleted_entries": deleted_count,
            "message": f"Invalidated {deleted_count} cache entries"
        }

    except Exception as e:
        logger.error(f"Cache invalidation error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to invalidate cache: {str(e)}"
        )
