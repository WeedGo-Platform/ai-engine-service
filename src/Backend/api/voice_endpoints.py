"""
Voice API Endpoints for V5
RESTful API for voice processing
"""
from fastapi import APIRouter, File, UploadFile, HTTPException, Form, Response, Request
from fastapi.responses import StreamingResponse
from typing import Optional, Dict, Any
import io
import logging
import base64
import json

from core.voice import VoicePipeline, PipelineMode

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/api/voice", tags=["voice"])

# Global voice pipeline instance
voice_pipeline = None

async def get_pipeline() -> VoicePipeline:
    """Get or create voice pipeline instance"""
    global voice_pipeline
    if voice_pipeline is None:
        voice_pipeline = VoicePipeline()
        if not await voice_pipeline.initialize():
            raise HTTPException(500, "Failed to initialize voice pipeline")
    return voice_pipeline

@router.post("/transcribe")
async def transcribe_audio(
    audio: UploadFile = File(...),
    language: Optional[str] = Form(None),
    mode: str = Form("auto_vad")
) -> Dict[str, Any]:
    """Transcribe audio to text
    
    Args:
        audio: Audio file (WAV, MP3, etc.)
        language: Language code (e.g., 'en', 'es', 'zh')
        mode: Processing mode (manual, auto_vad, continuous)
    
    Returns:
        Transcription result with text and metadata
    """
    try:
        # Get pipeline
        pipeline = await get_pipeline()
        
        # Read audio data
        audio_data = await audio.read()
        
        # Parse mode
        try:
            pipeline_mode = PipelineMode[mode.upper()]
        except KeyError:
            pipeline_mode = PipelineMode.AUTO_VAD
        
        # Process audio
        result = await pipeline.process_audio(
            audio_data,
            mode=pipeline_mode,
            language=language
        )
        
        return {
            "status": "success",
            "result": result
        }
        
    except Exception as e:
        logger.error(f"Transcription error: {e}")
        raise HTTPException(500, f"Transcription failed: {str(e)}")

@router.post("/synthesize")
async def synthesize_speech(
    text: str = Form(...),
    voice: Optional[str] = Form(None),
    language: Optional[str] = Form(None),
    speed: float = Form(1.0),
    format: str = Form("wav")
) -> Response:
    """Synthesize speech from text
    
    Args:
        text: Text to synthesize
        voice: Voice ID or name
        language: Language code
        speed: Speech rate (0.5-2.0)
        format: Audio format (wav, mp3)
    
    Returns:
        Audio file response
    """
    try:
        # Get pipeline
        pipeline = await get_pipeline()
        
        # Synthesize speech
        audio_data = await pipeline.synthesize_response(
            text,
            voice=voice,
            language=language,
            speed=speed
        )
        
        # Return audio response
        return Response(
            content=audio_data,
            media_type="audio/wav" if format == "wav" else "audio/mpeg",
            headers={
                "Content-Disposition": f"attachment; filename=speech.{format}"
            }
        )
        
    except Exception as e:
        logger.error(f"Synthesis error: {e}")
        raise HTTPException(500, f"Synthesis failed: {str(e)}")

@router.post("/detect_speech")
async def detect_speech(
    audio: UploadFile = File(...),
    threshold: float = Form(0.5)
) -> Dict[str, Any]:
    """Detect speech segments in audio
    
    Args:
        audio: Audio file
        threshold: Detection threshold (0.0-1.0)
    
    Returns:
        VAD result with speech segments
    """
    try:
        # Get pipeline
        pipeline = await get_pipeline()
        
        # Read audio data
        audio_data = await audio.read()
        
        # Detect speech
        result = await pipeline.vad.detect(audio_data, threshold)
        
        return {
            "status": "success",
            "has_speech": result.has_speech,
            "confidence": result.confidence,
            "segments": result.speech_segments,
            "energy_level": result.energy_level
        }
        
    except Exception as e:
        logger.error(f"VAD error: {e}")
        raise HTTPException(500, f"Speech detection failed: {str(e)}")

@router.post("/process")
async def process_voice(
    audio: Optional[UploadFile] = File(None),
    audio_base64: Optional[str] = Form(None),
    text: Optional[str] = Form(None),
    action: str = Form("transcribe"),
    language: Optional[str] = Form(None),
    voice: Optional[str] = Form(None),
    domain: str = Form("general")
) -> Dict[str, Any]:
    """Unified voice processing endpoint
    
    Args:
        audio: Audio file for transcription
        audio_base64: Base64 encoded audio
        text: Text for synthesis
        action: Action to perform (transcribe, synthesize, detect)
        language: Language code
        voice: Voice for synthesis
        domain: Domain context (general, healthcare, budtender, legal)
    
    Returns:
        Processing result based on action
    """
    try:
        # Get pipeline
        pipeline = await get_pipeline()
        
        # Set domain context
        if pipeline.current_session:
            pipeline.current_session.domain = domain
        
        if action == "transcribe":
            # Get audio data
            if audio:
                audio_data = await audio.read()
            elif audio_base64:
                audio_data = base64.b64decode(audio_base64)
            else:
                raise HTTPException(400, "No audio provided")
            
            # Transcribe
            result = await pipeline.process_audio(
                audio_data,
                mode=PipelineMode.AUTO_VAD,
                language=language
            )
            
            return {
                "status": "success",
                "action": "transcribe",
                "result": result
            }
            
        elif action == "synthesize":
            if not text:
                raise HTTPException(400, "No text provided")
            
            # Synthesize
            audio_data = await pipeline.synthesize_response(
                text,
                voice=voice,
                language=language
            )
            
            # Encode as base64 for JSON response
            audio_base64 = base64.b64encode(audio_data).decode('utf-8')
            
            return {
                "status": "success",
                "action": "synthesize",
                "audio_base64": audio_base64,
                "format": "wav"
            }
            
        elif action == "detect":
            # Get audio data
            if audio:
                audio_data = await audio.read()
            elif audio_base64:
                audio_data = base64.b64decode(audio_base64)
            else:
                raise HTTPException(400, "No audio provided")
            
            # Detect speech
            result = await pipeline.vad.detect(audio_data)
            
            return {
                "status": "success",
                "action": "detect",
                "has_speech": result.has_speech,
                "confidence": result.confidence,
                "segments": result.speech_segments
            }
            
        else:
            raise HTTPException(400, f"Unknown action: {action}")
            
    except Exception as e:
        logger.error(f"Process error: {e}")
        raise HTTPException(500, f"Processing failed: {str(e)}")

@router.get("/voices")
async def get_available_voices() -> Dict[str, Any]:
    """Get list of available TTS voices
    
    Returns:
        List of voice configurations
    """
    try:
        # Get pipeline
        pipeline = await get_pipeline()
        
        # Get voices
        voices = await pipeline.tts.get_available_voices()
        
        return {
            "status": "success",
            "voices": voices,
            "current_voice": pipeline.tts.current_voice if hasattr(pipeline.tts, 'current_voice') else None
        }
        
    except Exception as e:
        logger.error(f"Error getting voices: {e}")
        raise HTTPException(500, f"Failed to get voices: {str(e)}")

@router.post("/voice")
async def set_voice(
    request: Request
) -> Dict[str, Any]:
    """Set the current TTS voice
    
    Args:
        voice_id: Voice identifier to use
        voice_settings: Optional voice-specific settings as JSON string (speed, pitch, etc.)
    
    Returns:
        Confirmation with voice details
    """
    try:
        # Parse request body
        data = await request.json()
        voice_id = data.get("voice_id")
        voice_settings = data.get("voice_settings")
        quality = data.get("quality", "high")  # Default to high quality
        
        if not voice_id:
            raise HTTPException(400, "voice_id is required")
        
        # Get pipeline
        pipeline = await get_pipeline()
        
        # Parse voice settings if provided
        settings = None
        if voice_settings:
            try:
                settings = json.loads(voice_settings)
            except json.JSONDecodeError:
                raise HTTPException(400, "Invalid voice_settings JSON format")
        
        # Configure audio quality (always use high quality for better sound)
        if quality == "high":
            pipeline.tts.config.sample_rate = 48000
            pipeline.tts.config.channels = 2  # Stereo
            pipeline.tts.config.quality = "high"
        elif quality == "medium":
            pipeline.tts.config.sample_rate = 44100
            pipeline.tts.config.channels = 2  # Stereo
            pipeline.tts.config.quality = "medium"
        else:
            pipeline.tts.config.sample_rate = 22050
            pipeline.tts.config.channels = 1  # Mono for low quality
            pipeline.tts.config.quality = "low"
        
        # Set the voice
        if hasattr(pipeline.tts, '_set_voice'):
            await pipeline.tts._set_voice(voice_id)
            success = True
        else:
            # Fallback: Store voice preference for next synthesis
            pipeline.tts.current_voice_id = voice_id
            if settings:
                pipeline.tts.voice_settings = settings
            success = True
        
        if success:
            return {
                "status": "success",
                "message": f"Voice changed to {voice_id}",
                "voice_id": voice_id,
                "settings": settings,
                "quality": quality,
                "sample_rate": pipeline.tts.config.sample_rate
            }
        else:
            raise HTTPException(400, f"Failed to set voice: {voice_id} not found")
        
    except Exception as e:
        logger.error(f"Error setting voice: {e}")
        raise HTTPException(500, f"Failed to set voice: {str(e)}")

@router.get("/voice")
async def get_current_voice() -> Dict[str, Any]:
    """Get the current TTS voice configuration
    
    Returns:
        Current voice settings
    """
    try:
        # Get pipeline
        pipeline = await get_pipeline()
        
        current_voice = getattr(pipeline.tts, 'current_voice_id', None)
        voice_settings = getattr(pipeline.tts, 'voice_settings', {})
        quality = getattr(pipeline.tts.config, 'quality', 'high')
        sample_rate = getattr(pipeline.tts.config, 'sample_rate', 44100)
        
        return {
            "status": "success",
            "current_voice": current_voice,
            "settings": voice_settings,
            "quality": quality,
            "sample_rate": sample_rate,
            "available_settings": {
                "speed": "Speech rate (0.5-2.0)",
                "pitch": "Voice pitch adjustment (-20 to 20)",
                "volume": "Volume level (0.0-1.0)",
                "emotion": "Emotional tone (neutral, happy, sad, etc.)"
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting current voice: {e}")
        raise HTTPException(500, f"Failed to get current voice: {str(e)}")

@router.get("/metrics")
async def get_voice_metrics() -> Dict[str, Any]:
    """Get voice pipeline performance metrics
    
    Returns:
        Metrics from all voice components
    """
    try:
        # Get pipeline
        pipeline = await get_pipeline()
        
        # Get metrics
        metrics = pipeline.get_metrics()
        
        return {
            "status": "success",
            "metrics": metrics
        }
        
    except Exception as e:
        logger.error(f"Error getting metrics: {e}")
        raise HTTPException(500, f"Failed to get metrics: {str(e)}")

@router.get("/status")
async def get_voice_status() -> Dict[str, Any]:
    """Get voice system status
    
    Returns:
        Status of voice components
    """
    try:
        # Get pipeline
        pipeline = await get_pipeline()
        
        return {
            "status": "success",
            "initialized": pipeline.is_initialized,
            "components": {
                "stt": {
                    "state": pipeline.stt.get_state().value,
                    "model": pipeline.stt.model_name
                },
                "tts": {
                    "state": pipeline.tts.get_state().value
                },
                "vad": {
                    "state": pipeline.vad.get_state().value
                }
            },
            "session": {
                "id": pipeline.current_session.session_id if pipeline.current_session else None,
                "domain": pipeline.current_session.domain if pipeline.current_session else None
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting status: {e}")
        return {
            "status": "error",
            "error": str(e),
            "initialized": False
        }