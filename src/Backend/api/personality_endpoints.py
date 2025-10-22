"""
AI Personality Management API Endpoints
Handles personality CRUD, voice sample uploads, and tier limits
"""
from fastapi import APIRouter, File, UploadFile, HTTPException, Depends, Form, Request, Body
from fastapi.responses import FileResponse
from typing import Optional, Dict, Any, List
from pydantic import BaseModel
import os
import logging
import asyncpg
import wave
import io
import hashlib
from pathlib import Path
from datetime import datetime
import json

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/api/personalities", tags=["personalities"])


# Request models
class PersonalityCreate(BaseModel):
    name: str
    personality_name: str
    tone: str
    greeting_message: str
    system_prompt: str
    tenant_id: str
    response_style: Optional[Dict[str, Any]] = {}
    traits: Optional[Dict[str, Any]] = {}


class PersonalityUpdate(BaseModel):
    name: str
    personality_name: str
    tone: str
    greeting_message: str
    system_prompt: str
    response_style: Optional[Dict[str, Any]] = {}
    traits: Optional[Dict[str, Any]] = {}


# Voice sample storage configuration
# Use environment variable or fall back to local data directory
try:
    VOICE_SAMPLES_BASE = os.getenv("VOICE_SAMPLES_DIR", str(Path(__file__).parent.parent / "data" / "voices"))
    VOICE_SAMPLES_DIR = Path(VOICE_SAMPLES_BASE) / "personalities"
    VOICE_SAMPLES_DIR.mkdir(parents=True, exist_ok=True)
    logger.info(f"Voice samples directory initialized: {VOICE_SAMPLES_DIR}")
except Exception as e:
    logger.error(f"Failed to create voice samples directory at {VOICE_SAMPLES_DIR}: {e}")
    logger.warning("Voice upload functionality may not work properly")
    # Set to a temporary location as fallback
    VOICE_SAMPLES_DIR = Path("/tmp/weedgo_voices/personalities")
    VOICE_SAMPLES_DIR.mkdir(parents=True, exist_ok=True)
    logger.info(f"Using temporary voice samples directory: {VOICE_SAMPLES_DIR}")

# Subscription tier limits
PERSONALITY_LIMITS = {
    "free": 0,  # Free tier: 3 default personalities only (no custom)
    "small_business": 2,  # Small Business: +2 custom personalities
    "professional": 3,  # Professional: +3 custom personalities
    "enterprise": 5  # Enterprise: +5 custom personalities
}

# Default personalities (hardcoded, read-only)
DEFAULT_PERSONALITIES = ["marcel", "shante", "zac"]


async def get_db_conn():
    """Get database connection (dependency injection)"""
    # TODO: Replace with proper dependency injection
    conn = await asyncpg.connect(
        host=os.getenv("DB_HOST", "localhost"),
        port=int(os.getenv("DB_PORT", 5434)),
        database=os.getenv("DB_NAME", "ai_engine"),
        user=os.getenv("DB_USER", "weedgo"),
        password=os.getenv("DB_PASSWORD", "weedgo123")
    )
    try:
        yield conn
    finally:
        await conn.close()


def validate_audio_file(audio_data: bytes, min_duration: float = 5.0, max_duration: float = 30.0) -> Dict[str, Any]:
    """Validate audio file format and quality

    Args:
        audio_data: Audio file bytes
        min_duration: Minimum duration in seconds
        max_duration: Maximum duration in seconds

    Returns:
        Validation result with metadata

    Raises:
        HTTPException: If validation fails
    """
    try:
        # Try to open as WAV
        with io.BytesIO(audio_data) as audio_buffer:
            with wave.open(audio_buffer, 'rb') as wav_file:
                # Get audio properties
                channels = wav_file.getnchannels()
                sample_width = wav_file.getsampwidth()
                frame_rate = wav_file.getframerate()
                n_frames = wav_file.getnframes()

                # Calculate duration
                duration = n_frames / float(frame_rate)

                # Validate format
                if channels not in [1, 2]:
                    raise HTTPException(
                        400,
                        f"Invalid audio channels: {channels}. Must be mono (1) or stereo (2)"
                    )

                if sample_width not in [2, 3, 4]:  # 16-bit, 24-bit, or 32-bit
                    raise HTTPException(
                        400,
                        f"Invalid bit depth: {sample_width * 8}-bit. Must be 16-bit, 24-bit, or 32-bit"
                    )

                if frame_rate < 16000:
                    raise HTTPException(
                        400,
                        f"Sample rate too low: {frame_rate}Hz. Must be at least 16000Hz (recommended: 22050Hz or 44100Hz)"
                    )

                # Validate duration
                if duration < min_duration:
                    raise HTTPException(
                        400,
                        f"Audio too short: {duration:.1f}s. Must be at least {min_duration}s for good voice cloning quality"
                    )

                if duration > max_duration:
                    raise HTTPException(
                        400,
                        f"Audio too long: {duration:.1f}s. Must be at most {max_duration}s"
                    )

                # Calculate file size in MB
                file_size_mb = len(audio_data) / (1024 * 1024)

                if file_size_mb > 10:  # 10MB limit
                    raise HTTPException(
                        400,
                        f"File too large: {file_size_mb:.2f}MB. Maximum is 10MB"
                    )

                return {
                    "valid": True,
                    "duration": duration,
                    "channels": channels,
                    "sample_rate": frame_rate,
                    "bit_depth": sample_width * 8,
                    "file_size_mb": file_size_mb,
                    "format": "wav"
                }

    except wave.Error as e:
        raise HTTPException(
            400,
            f"Invalid WAV file: {str(e)}. Please upload a valid WAV audio file"
        )
    except Exception as e:
        logger.error(f"Audio validation error: {e}")
        raise HTTPException(
            400,
            f"Audio validation failed: {str(e)}"
        )


@router.post("/{personality_id}/voice")
async def upload_personality_voice(
    personality_id: str,
    audio: UploadFile = File(...),
    db: asyncpg.Connection = Depends(get_db_conn)
) -> Dict[str, Any]:
    """Upload voice sample for a personality

    Args:
        personality_id: Personality UUID
        audio: Voice sample audio file (WAV format)

    Returns:
        Upload result with voice configuration
    """
    try:
        # Read audio file
        audio_data = await audio.read()

        # Validate audio
        validation = validate_audio_file(audio_data)

        logger.info(f"Voice sample validation passed: {validation}")

        # Check if personality exists
        personality = await db.fetchrow(
            "SELECT id, tenant_id, name, voice_config FROM ai_personalities WHERE id = $1",
            personality_id
        )

        if not personality:
            raise HTTPException(404, f"Personality {personality_id} not found")

        # Generate unique filename
        file_hash = hashlib.sha256(audio_data).hexdigest()[:12]
        filename = f"{personality_id}-{personality['name']}-{file_hash}.wav"
        file_path = VOICE_SAMPLES_DIR / filename

        # Save audio file
        with open(file_path, 'wb') as f:
            f.write(audio_data)

        logger.info(f"Saved voice sample: {file_path}")

        # Update voice_config in database
        voice_config = personality['voice_config'] or {}
        voice_config.update({
            "sample_path": str(file_path),
            "sample_metadata": {
                "duration": validation["duration"],
                "sample_rate": validation["sample_rate"],
                "channels": validation["channels"],
                "bit_depth": validation["bit_depth"],
                "file_size_mb": validation["file_size_mb"],
                "uploaded_at": datetime.now().isoformat()
            },
            "provider": voice_config.get("provider", "xtts_v2"),  # Default to XTTS v2
            "fallback_chain": voice_config.get("fallback_chain", ["xtts_v2", "google_tts", "piper"])
        })

        # Update database
        await db.execute(
            "UPDATE ai_personalities SET voice_config = $1, updated_at = NOW() WHERE id = $2",
            json.dumps(voice_config),
            personality_id
        )

        logger.info(f"Updated personality {personality_id} voice_config")

        # TODO: Load voice sample into VoiceModelRouter cache
        # This would be done by calling:
        # await voice_router.load_personality_voice(personality_id, str(file_path))

        return {
            "status": "success",
            "message": "Voice sample uploaded successfully",
            "personality_id": personality_id,
            "voice_config": voice_config,
            "validation": validation,
            "file_path": str(file_path)
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Voice upload error: {e}")
        raise HTTPException(500, f"Failed to upload voice sample: {str(e)}")


@router.get("/{personality_id}/voice")
async def get_personality_voice(
    personality_id: str,
    db: asyncpg.Connection = Depends(get_db_conn)
) -> Dict[str, Any]:
    """Get voice configuration for a personality

    Args:
        personality_id: Personality UUID

    Returns:
        Voice configuration details
    """
    try:
        # Get personality
        personality = await db.fetchrow(
            "SELECT id, name, voice_config FROM ai_personalities WHERE id = $1",
            personality_id
        )

        if not personality:
            raise HTTPException(404, f"Personality {personality_id} not found")

        voice_config = personality['voice_config'] or {}

        # Check if voice sample exists
        has_voice_sample = False
        sample_path = voice_config.get("sample_path")

        if sample_path and Path(sample_path).exists():
            has_voice_sample = True

        return {
            "status": "success",
            "personality_id": personality_id,
            "name": personality['name'],
            "has_voice_sample": has_voice_sample,
            "voice_config": voice_config
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting voice config: {e}")
        raise HTTPException(500, f"Failed to get voice configuration: {str(e)}")


@router.delete("/{personality_id}/voice")
async def delete_personality_voice(
    personality_id: str,
    db: asyncpg.Connection = Depends(get_db_conn)
) -> Dict[str, Any]:
    """Delete voice sample for a personality

    Args:
        personality_id: Personality UUID

    Returns:
        Deletion confirmation
    """
    try:
        # Get personality
        personality = await db.fetchrow(
            "SELECT id, voice_config FROM ai_personalities WHERE id = $1",
            personality_id
        )

        if not personality:
            raise HTTPException(404, f"Personality {personality_id} not found")

        # Parse voice_config (JSONB can return string or dict)
        voice_config_raw = personality['voice_config']
        if isinstance(voice_config_raw, str):
            voice_config = json.loads(voice_config_raw) if voice_config_raw else {}
        else:
            voice_config = voice_config_raw or {}
        
        sample_path = voice_config.get("sample_path")

        # Delete file if exists
        if sample_path:
            file_path = Path(sample_path)
            if file_path.exists():
                file_path.unlink()
                logger.info(f"Deleted voice sample: {file_path}")

        # Clear voice_config
        voice_config.pop("sample_path", None)
        voice_config.pop("sample_metadata", None)

        # Update database
        await db.execute(
            "UPDATE ai_personalities SET voice_config = $1, updated_at = NOW() WHERE id = $2",
            json.dumps(voice_config) if voice_config else None,
            personality_id
        )

        # TODO: Remove from VoiceModelRouter cache
        # await voice_router.remove_personality_voice(personality_id)

        return {
            "status": "success",
            "message": "Voice sample deleted successfully",
            "personality_id": personality_id
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Voice deletion error: {e}")
        raise HTTPException(500, f"Failed to delete voice sample: {str(e)}")


@router.get("")
async def list_personalities(
    tenant_id: Optional[str] = None,
    include_defaults: bool = True,
    db: asyncpg.Connection = Depends(get_db_conn)
) -> Dict[str, Any]:
    """List all personalities for a tenant

    Args:
        tenant_id: Optional tenant ID filter
        include_defaults: Include default personalities

    Returns:
        List of personalities
    """
    try:
        # Build query
        if tenant_id:
            query = """
                SELECT id, tenant_id, name, personality_name, tone, greeting_message,
                       system_prompt, response_style, traits, voice_config, is_default,
                       is_active, created_at, updated_at
                FROM ai_personalities
                WHERE tenant_id = $1
                ORDER BY is_default DESC, name ASC
            """
            rows = await db.fetch(query, tenant_id)
        else:
            query = """
                SELECT id, tenant_id, name, personality_name, tone, greeting_message,
                       system_prompt, response_style, traits, voice_config, is_default,
                       is_active, created_at, updated_at
                FROM ai_personalities
                ORDER BY tenant_id, is_default DESC, name ASC
            """
            rows = await db.fetch(query)

        personalities = []
        for row in rows:
            # Skip defaults if not requested
            if not include_defaults and row['is_default']:
                continue

            # Parse JSONB fields (asyncpg returns them as dicts/lists already)
            voice_config = row['voice_config'] if row['voice_config'] else {}
            traits = row['traits'] if row['traits'] else {}
            response_style = row['response_style'] if row['response_style'] else {}

            # If they're strings, parse them
            if isinstance(voice_config, str):
                voice_config = json.loads(voice_config)
            if isinstance(traits, str):
                traits = json.loads(traits)
            if isinstance(response_style, str):
                response_style = json.loads(response_style)

            # Check if voice sample exists
            has_voice = False
            sample_path = voice_config.get("sample_path") if isinstance(voice_config, dict) else None
            if sample_path and Path(sample_path).exists():
                has_voice = True

            personalities.append({
                "id": str(row['id']),
                "tenant_id": str(row['tenant_id']),
                "name": row['name'],
                "personality_name": row['personality_name'],
                "tone": row['tone'],
                "description": row['greeting_message'],  # Use greeting_message as description
                "greeting_message": row['greeting_message'],
                "system_prompt": row['system_prompt'],
                "response_style": response_style,
                "traits": traits,
                "is_default": row['is_default'],
                "is_active": row['is_active'],
                "has_voice_sample": has_voice,
                "voice_provider": voice_config.get("provider", "piper") if isinstance(voice_config, dict) else "piper",
                "created_at": row['created_at'].isoformat() if row['created_at'] else None,
                "updated_at": row['updated_at'].isoformat() if row['updated_at'] else None
            })

        return {
            "status": "success",
            "personalities": personalities,
            "count": len(personalities)
        }

    except Exception as e:
        logger.error(f"Error listing personalities: {e}")
        raise HTTPException(500, f"Failed to list personalities: {str(e)}")


@router.post("")
async def create_personality(
    data: PersonalityCreate,
    db: asyncpg.Connection = Depends(get_db_conn)
) -> Dict[str, Any]:
    """Create a new personality

    Args:
        data: Personality creation data

    Returns:
        Created personality
    """
    try:
        # Insert personality
        personality = await db.fetchrow(
            """
            INSERT INTO ai_personalities (
                tenant_id, name, personality_name, tone, greeting_message,
                system_prompt, response_style, traits, is_default, is_active
            )
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, FALSE, TRUE)
            RETURNING id, tenant_id, name, personality_name, tone, greeting_message,
                      system_prompt, response_style, traits, voice_config, is_default,
                      is_active, created_at, updated_at
            """,
            data.tenant_id, data.name, data.personality_name, data.tone, 
            data.greeting_message, data.system_prompt, 
            json.dumps(data.response_style), json.dumps(data.traits)
        )

        return {
            "status": "success",
            "personality": {
                "id": str(personality['id']),
                "tenant_id": str(personality['tenant_id']),
                "name": personality['name'],
                "personality_name": personality['personality_name'],
                "tone": personality['tone'],
                "greeting_message": personality['greeting_message'],
                "system_prompt": personality['system_prompt'],
                "response_style": data.response_style,
                "traits": data.traits,
                "is_default": personality['is_default'],
                "is_active": personality['is_active'],
                "has_voice_sample": False,
                "created_at": personality['created_at'].isoformat() if personality['created_at'] else None,
                "updated_at": personality['updated_at'].isoformat() if personality['updated_at'] else None
            }
        }

    except Exception as e:
        logger.error(f"Error creating personality: {e}")
        raise HTTPException(500, f"Failed to create personality: {str(e)}")


@router.put("/{personality_id}")
async def update_personality(
    personality_id: str,
    data: PersonalityUpdate,
    db: asyncpg.Connection = Depends(get_db_conn)
) -> Dict[str, Any]:
    """Update an existing personality

    Args:
        personality_id: Personality UUID
        data: Personality update data

    Returns:
        Updated personality
    """
    try:
        # Update personality
        personality = await db.fetchrow(
            """
            UPDATE ai_personalities
            SET name = $2,
                personality_name = $3,
                tone = $4,
                greeting_message = $5,
                system_prompt = $6,
                response_style = $7,
                traits = $8,
                updated_at = NOW()
            WHERE id = $1
            RETURNING id, tenant_id, name, personality_name, tone, greeting_message,
                      system_prompt, response_style, traits, voice_config, is_default,
                      is_active, created_at, updated_at
            """,
            personality_id, data.name, data.personality_name, data.tone, 
            data.greeting_message, data.system_prompt,
            json.dumps(data.response_style), json.dumps(data.traits)
        )

        if not personality:
            raise HTTPException(404, f"Personality {personality_id} not found")

        # Parse voice_config
        voice_config = personality['voice_config']
        if isinstance(voice_config, str):
            voice_config = json.loads(voice_config)

        # Check if voice sample exists
        has_voice = False
        sample_path = voice_config.get("sample_path") if isinstance(voice_config, dict) else None
        if sample_path and Path(sample_path).exists():
            has_voice = True

        return {
            "status": "success",
            "personality": {
                "id": str(personality['id']),
                "tenant_id": str(personality['tenant_id']),
                "name": personality['name'],
                "personality_name": personality['personality_name'],
                "tone": personality['tone'],
                "greeting_message": personality['greeting_message'],
                "system_prompt": personality['system_prompt'],
                "response_style": data.response_style,
                "traits": data.traits,
                "is_default": personality['is_default'],
                "is_active": personality['is_active'],
                "has_voice_sample": has_voice,
                "created_at": personality['created_at'].isoformat() if personality['created_at'] else None,
                "updated_at": personality['updated_at'].isoformat() if personality['updated_at'] else None
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating personality: {e}")
        raise HTTPException(500, f"Failed to update personality: {str(e)}")


@router.get("/limits/{tenant_id}")
async def get_personality_limits(
    tenant_id: str,
    db: asyncpg.Connection = Depends(get_db_conn)
) -> Dict[str, Any]:
    """Get personality creation limits for a tenant based on subscription tier

    Args:
        tenant_id: Tenant UUID

    Returns:
        Tier limits and current usage
    """
    try:
        # Get tenant subscription tier
        tenant = await db.fetchrow(
            "SELECT subscription_tier FROM tenants WHERE id = $1",
            tenant_id
        )

        if not tenant:
            raise HTTPException(404, f"Tenant {tenant_id} not found")

        subscription_tier = tenant['subscription_tier'] or 'free'

        # Get current custom personality count
        custom_count = await db.fetchval(
            """
            SELECT COUNT(*) FROM ai_personalities
            WHERE tenant_id = $1 AND is_default = FALSE
            """,
            tenant_id
        )

        # Get limits for tier
        custom_limit = PERSONALITY_LIMITS.get(subscription_tier, 0)

        return {
            "status": "success",
            "tenant_id": tenant_id,
            "subscription_tier": subscription_tier,
            "limits": {
                "default_personalities": 3,  # Always 3
                "custom_personalities_allowed": custom_limit,
                "custom_personalities_used": custom_count,
                "custom_personalities_remaining": max(0, custom_limit - custom_count),
                "can_create_more": custom_count < custom_limit
            },
            "tier_details": {
                "free": {"custom": 0, "description": "3 default personalities only"},
                "small_business": {"custom": 2, "description": "3 defaults + 2 custom"},
                "professional": {"custom": 3, "description": "3 defaults + 3 custom"},
                "enterprise": {"custom": 5, "description": "3 defaults + 5 custom"}
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting personality limits: {e}")
        raise HTTPException(500, f"Failed to get personality limits: {str(e)}")


@router.post("/validate-voice")
async def validate_voice_sample(
    audio: UploadFile = File(...)
) -> Dict[str, Any]:
    """Validate a voice sample without saving it

    Useful for client-side validation before upload

    Args:
        audio: Voice sample audio file

    Returns:
        Validation result with quality assessment
    """
    try:
        # Read audio file
        audio_data = await audio.read()

        # Validate
        validation = validate_audio_file(audio_data)

        # Quality assessment
        quality_score = 100
        warnings = []

        # Check duration (optimal: 15-20s for XTTS v2, 5-8s for StyleTTS2)
        if validation["duration"] < 8:
            quality_score -= 10
            warnings.append("Audio is short. For best results, use 15-20 seconds for XTTS v2")
        elif validation["duration"] > 25:
            quality_score -= 5
            warnings.append("Audio is long. Optimal duration is 15-20 seconds")

        # Check sample rate
        if validation["sample_rate"] < 22050:
            quality_score -= 15
            warnings.append(f"Sample rate is {validation['sample_rate']}Hz. Recommended: 22050Hz or 44100Hz for best quality")

        # Check bit depth
        if validation["bit_depth"] < 16:
            quality_score -= 20
            warnings.append("Bit depth too low. Use at least 16-bit audio")

        # Determine quality rating
        if quality_score >= 90:
            quality_rating = "excellent"
        elif quality_score >= 70:
            quality_rating = "good"
        elif quality_score >= 50:
            quality_rating = "acceptable"
        else:
            quality_rating = "poor"

        return {
            "status": "success",
            "validation": validation,
            "quality": {
                "score": quality_score,
                "rating": quality_rating,
                "warnings": warnings
            },
            "recommendations": [
                "Record in a quiet environment (minimal background noise)",
                "Keep consistent distance from microphone (6-12 inches)",
                "Speak naturally with varied intonation",
                "Avoid music, echo, or other speakers in the recording",
                "Use WAV format at 22050Hz or 44100Hz, 16-bit or higher"
            ]
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Voice validation error: {e}")
        raise HTTPException(400, f"Voice validation failed: {str(e)}")
