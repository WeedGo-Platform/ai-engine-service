"""
Voice Provider Management API - Configuration & Control
Manage voice synthesis providers, credentials, and activation
"""

import os
import json
import logging
import tempfile
from pathlib import Path
from typing import Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Header, UploadFile, File
from fastapi.responses import Response
from pydantic import BaseModel
import asyncpg

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/voice-providers", tags=["voice-providers"])


# Database connection helper
async def get_db_connection():
    """Get database connection"""
    return await asyncpg.connect(
        host=os.getenv('DB_HOST', 'localhost'),
        port=int(os.getenv('DB_PORT', 5434)),
        user=os.getenv('DB_USER', 'weedgo'),
        password=os.getenv('DB_PASSWORD', 'weedgo123'),
        database=os.getenv('DB_NAME', 'ai_engine')
    )


# Request/Response Models
class ProviderConfigRequest(BaseModel):
    """Provider configuration request"""
    credentials: Dict[str, Any]
    enabled: bool = True

    class Config:
        json_schema_extra = {
            "example": {
                "credentials": {
                    "api_key": "your-google-cloud-api-key",
                    "project_id": "your-project-id"
                },
                "enabled": True
            }
        }


class SetActiveProviderRequest(BaseModel):
    """Set active provider request"""
    provider: str

    class Config:
        json_schema_extra = {
            "example": {
                "provider": "piper"
            }
        }


class TestProviderRequest(BaseModel):
    """Test provider request"""
    text: str = "Hello, this is a test."
    provider: str

    class Config:
        json_schema_extra = {
            "example": {
                "text": "Testing voice synthesis",
                "provider": "piper"
            }
        }


@router.get("/list")
async def list_providers(authorization: Optional[str] = Header(None)):
    """
    Get all voice providers with configuration status

    Returns:
        List of providers with status, configuration, and capabilities
    """
    try:
        conn = await get_db_connection()
        try:
            # Get active provider from settings
            active_provider_row = await conn.fetchrow(
                """
                SELECT value FROM system_settings
                WHERE category = 'voice' AND key = 'active_provider'
                """
            )
            
            # Handle value being string or dict (JSONB can return either)
            if active_provider_row:
                value = active_provider_row['value']
                if isinstance(value, str):
                    value = json.loads(value)
                active_provider = value.get('provider', 'piper')
            else:
                active_provider = 'piper'

            # Get provider configurations
            config_rows = await conn.fetch(
                """
                SELECT key, value FROM system_settings
                WHERE category = 'voice_providers'
                """
            )

            # Handle value being string or dict for each config
            provider_configs = {}
            for row in config_rows:
                value = row['value']
                if isinstance(value, str):
                    value = json.loads(value)
                provider_configs[row['key']] = value

            # Define all providers with their capabilities
            providers = [
                {
                    "id": "piper",
                    "name": "Piper TTS",
                    "type": "local",
                    "description": "Fast neural TTS with 14 voices",
                    "status": "available",
                    "configured": True,
                    "enabled": True,
                    "active": active_provider == "piper",
                    "capabilities": {
                        "voices": 14,
                        "languages": ["en"],
                        "quality": "high",
                        "speed": "fast",
                        "voice_cloning": False
                    },
                    "config_required": False
                },
                {
                    "id": "xtts_v2",
                    "name": "XTTS v2",
                    "type": "local",
                    "description": "Zero-shot voice cloning with 17 languages",
                    "status": "available",
                    "configured": True,
                    "enabled": True,
                    "active": active_provider == "xtts_v2",
                    "capabilities": {
                        "voices": "unlimited",
                        "languages": ["en", "es", "fr", "de", "it", "pt", "pl", "tr", "ru", "nl", "cs", "ar", "zh-cn", "hu", "ko", "ja", "hi"],
                        "quality": "high",
                        "speed": "medium",
                        "voice_cloning": True
                    },
                    "config_required": False,
                    "requires_voice_sample": True
                },
                {
                    "id": "styletts2",
                    "name": "StyleTTS2",
                    "type": "local",
                    "description": "Human-level voice cloning (experimental)",
                    "status": "needs_setup",
                    "configured": False,
                    "enabled": False,
                    "active": False,
                    "capabilities": {
                        "voices": "unlimited",
                        "languages": ["en"],
                        "quality": "human-level",
                        "speed": "slow",
                        "voice_cloning": True
                    },
                    "config_required": False,
                    "requires_voice_sample": True,
                    "setup_note": "Requires PyTorch 2.6 compatibility fix"
                },
                {
                    "id": "google_cloud",
                    "name": "Google Cloud TTS",
                    "type": "cloud",
                    "description": "500+ voices in 100+ languages",
                    "status": "needs_config" if "google_cloud" not in provider_configs else "available",
                    "configured": "google_cloud" in provider_configs,
                    "enabled": provider_configs.get("google_cloud", {}).get("enabled", False) if "google_cloud" in provider_configs else False,
                    "active": active_provider == "google_cloud",
                    "capabilities": {
                        "voices": "500+",
                        "languages": "100+",
                        "quality": "high",
                        "speed": "fast",
                        "voice_cloning": False,
                        "pricing": "Free tier: 1-4M chars/month"
                    },
                    "config_required": True,
                    "config_fields": [
                        {"name": "credentials_path", "label": "Credentials File Path", "type": "file", "description": "Path to Google Cloud service account JSON"},
                        {"name": "project_id", "label": "Project ID", "type": "text", "description": "Google Cloud Project ID"}
                    ]
                }
            ]

            return {
                "success": True,
                "active_provider": active_provider,
                "providers": providers,
                "total": len(providers),
                "local_count": sum(1 for p in providers if p["type"] == "local"),
                "cloud_count": sum(1 for p in providers if p["type"] == "cloud")
            }

        finally:
            await conn.close()

    except Exception as e:
        logger.error(f"Error listing providers: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to list providers: {str(e)}")


@router.post("/{provider_id}/configure")
async def configure_provider(
    provider_id: str,
    config: ProviderConfigRequest,
    authorization: Optional[str] = Header(None)
):
    """
    Configure a voice provider with credentials

    Args:
        provider_id: Provider ID (e.g., 'google_cloud')
        config: Provider configuration including credentials

    Returns:
        Configuration status
    """
    try:
        conn = await get_db_connection()
        try:
            # Store configuration in system_settings
            await conn.execute(
                """
                INSERT INTO system_settings (category, key, value, description)
                VALUES ('voice_providers', $1, $2, $3)
                ON CONFLICT (category, key)
                DO UPDATE SET value = $2, updated_at = CURRENT_TIMESTAMP
                """,
                provider_id,
                json.dumps({
                    "enabled": config.enabled,
                    "credentials": config.credentials,
                    "configured_at": "now()"
                }),
                f"Configuration for {provider_id} voice provider"
            )

            # If Google Cloud, set environment variable
            if provider_id == "google_cloud" and "credentials_path" in config.credentials:
                os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = config.credentials['credentials_path']

            return {
                "success": True,
                "provider": provider_id,
                "message": f"Provider {provider_id} configured successfully",
                "enabled": config.enabled
            }

        finally:
            await conn.close()

    except Exception as e:
        logger.error(f"Error configuring provider {provider_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to configure provider: {str(e)}")


@router.put("/active")
async def set_active_provider(
    request: SetActiveProviderRequest,
    authorization: Optional[str] = Header(None)
):
    """
    Set the active voice provider

    Args:
        request: Active provider request

    Returns:
        Updated active provider
    """
    try:
        conn = await get_db_connection()
        try:
            await conn.execute(
                """
                INSERT INTO system_settings (category, key, value, description)
                VALUES ('voice', 'active_provider', $1, 'Currently active voice synthesis provider')
                ON CONFLICT (category, key)
                DO UPDATE SET value = $1, updated_at = CURRENT_TIMESTAMP
                """,
                json.dumps({"provider": request.provider})
            )

            return {
                "success": True,
                "active_provider": request.provider,
                "message": f"Active provider set to {request.provider}"
            }

        finally:
            await conn.close()

    except Exception as e:
        logger.error(f"Error setting active provider: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to set active provider: {str(e)}")


@router.post("/test")
async def test_provider(
    request: TestProviderRequest,
    authorization: Optional[str] = Header(None)
):
    """
    Test a voice provider by generating sample audio

    Args:
        request: Test request with text and provider

    Returns:
        Audio file (audio/wav)
    """
    try:
        # Import here to avoid circular dependency
        from core.voice.voice_model_router import VoiceModelRouter, SynthesisContext, VoiceQuality

        router_instance = VoiceModelRouter()
        await router_instance.initialize()

        context = SynthesisContext(
            language="en",
            speed=1.0,
            quality=VoiceQuality.HIGH
        )

        result = await router_instance.synthesize(
            text=request.text,
            context=context
        )

        # Return audio file
        return Response(
            content=result.audio,
            media_type="audio/wav",
            headers={
                "Content-Disposition": f"attachment; filename=test_{request.provider}.wav",
                "X-Provider": result.provider,
                "X-Duration-MS": str(int(result.duration_ms)),
                "X-Sample-Rate": str(result.sample_rate)
            }
        )

    except Exception as e:
        logger.error(f"Error testing provider {request.provider}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Test failed: {str(e)}"
        )


@router.post("/voice-samples/upload")
async def upload_voice_sample(
    personality_id: str,
    file: UploadFile = File(...),
    authorization: Optional[str] = Header(None)
):
    """
    Upload a voice sample for voice cloning (XTTS v2/StyleTTS2)

    Args:
        personality_id: Personality UUID
        file: Audio file (WAV, MP3, etc.)

    Returns:
        Upload status and file path
    """
    try:
        # Create voice samples directory
        samples_dir = os.path.join(
            os.path.dirname(__file__),
            "..", "models", "voice", "samples"
        )
        os.makedirs(samples_dir, exist_ok=True)

        # Read uploaded file
        contents = await file.read()
        
        # Save to temporary file first
        with tempfile.NamedTemporaryFile(delete=False, suffix=Path(file.filename or "audio.webm").suffix) as tmp_input:
            tmp_input.write(contents)
            tmp_input_path = tmp_input.name

        # Final WAV file path
        wav_path = os.path.join(samples_dir, f"{personality_id}.wav")

        try:
            # Try to use pydub for conversion (more portable)
            try:
                from pydub import AudioSegment
                
                # Load audio file (pydub auto-detects format)
                audio = AudioSegment.from_file(tmp_input_path)
                
                # Convert to 16kHz mono WAV for XTTS v2
                audio = audio.set_frame_rate(16000).set_channels(1).set_sample_width(2)
                
                # Export as WAV
                audio.export(wav_path, format="wav")
                
                logger.info(f"Converted audio using pydub: {wav_path}")
                
            except ImportError:
                # Fallback to ffmpeg if pydub not available
                import subprocess
                
                result = subprocess.run([
                    'ffmpeg', '-y',
                    '-i', tmp_input_path,
                    '-ar', '16000',  # 16kHz sample rate
                    '-ac', '1',      # Mono
                    '-sample_fmt', 's16',  # 16-bit PCM
                    wav_path
                ], capture_output=True, text=True, timeout=30)

                if result.returncode != 0:
                    logger.error(f"FFmpeg conversion failed: {result.stderr}")
                    raise Exception(f"Audio conversion failed: {result.stderr}")

                logger.info(f"Converted audio using ffmpeg: {wav_path}")
            
            # Get final file size
            file_size = os.path.getsize(wav_path)

        finally:
            # Clean up temp file
            Path(tmp_input_path).unlink(missing_ok=True)

        # Store reference in database
        conn = await get_db_connection()
        try:
            # Update voice_config JSONB field in ai_personalities table
            await conn.execute(
                """
                UPDATE ai_personalities
                SET voice_config = COALESCE(voice_config, '{}'::jsonb) || 
                    jsonb_build_object(
                        'sample_path', $1::text, 
                        'sample_metadata', jsonb_build_object(
                            'uploaded_at', NOW()::text,
                            'file_size_bytes', $2::integer
                        )
                    ),
                    updated_at = NOW()
                WHERE id = $3::uuid
                """,
                wav_path,
                file_size,
                personality_id
            )

        finally:
            await conn.close()

        # Load voice sample into XTTS v2 and StyleTTS2 caches
        try:
            from api.voice_synthesis_endpoints import get_voice_router
            router = await get_voice_router()
            load_results = await router.load_personality_voice(
                personality_id=personality_id,
                voice_sample_path=wav_path
            )
            logger.info(f"Voice sample loaded into providers: {load_results}")
        except Exception as e:
            logger.error(f"Failed to load voice sample into cache: {e}")
            # Don't fail the upload, just warn

        return {
            "success": True,
            "personality_id": personality_id,
            "file_path": wav_path,
            "file_size_bytes": file_size,
            "message": "Voice sample uploaded successfully",
            "loaded_providers": load_results if 'load_results' in locals() else {}
        }

    except Exception as e:
        logger.error(f"Error uploading voice sample: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to upload voice sample: {str(e)}")


@router.delete("/{provider_id}/config")
async def delete_provider_config(
    provider_id: str,
    authorization: Optional[str] = Header(None)
):
    """
    Delete provider configuration

    Args:
        provider_id: Provider ID

    Returns:
        Deletion status
    """
    try:
        conn = await get_db_connection()
        try:
            await conn.execute(
                """
                DELETE FROM system_settings
                WHERE category = 'voice_providers' AND key = $1
                """,
                provider_id
            )

            return {
                "success": True,
                "provider": provider_id,
                "message": f"Configuration for {provider_id} deleted"
            }

        finally:
            await conn.close()

    except Exception as e:
        logger.error(f"Error deleting provider config: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to delete config: {str(e)}")
