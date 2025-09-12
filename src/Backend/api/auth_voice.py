"""
Voice Authentication API Endpoints
Handles voice-based login and age verification
"""

from fastapi import APIRouter, HTTPException, Depends, File, UploadFile, Form
from typing import Dict, Optional, Any
import logging
import asyncpg
import os
import base64

from services.voice_auth_service import VoiceAuthService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/auth/voice", tags=["Voice Authentication"])

# Database connection pool
db_pool = None

async def get_db_pool():
    """Get or create database connection pool"""
    global db_pool
    if db_pool is None:
        db_pool = await asyncpg.create_pool(
            host=os.getenv('DB_HOST', 'localhost'),
            port=int(os.getenv('DB_PORT', 5432)),
            database=os.getenv('DB_NAME', 'ai_engine'),
            user=os.getenv('DB_USER', 'weedgo'),
            password=os.getenv('DB_PASSWORD', 'your_password_here'),
            min_size=1,
            max_size=10
        )
    return db_pool


async def get_voice_auth_service():
    """Get voice auth service instance"""
    pool = await get_db_pool()
    conn = await pool.acquire()
    try:
        service = VoiceAuthService(conn)
        yield service
    finally:
        await pool.release(conn)


@router.post("/login")
async def voice_login(
    audio: UploadFile = File(..., description="Audio file containing user's voice"),
    service: VoiceAuthService = Depends(get_voice_auth_service)
):
    """
    Authenticate user using voice biometrics
    
    Args:
        audio: Audio file containing user's voice sample
    
    Returns:
        Authentication result with user information and age verification
    """
    try:
        # Read audio data
        audio_data = await audio.read()
        
        # Authenticate voice
        result = await service.authenticate_voice(audio_data)
        
        if result is None:
            raise HTTPException(status_code=500, detail="Voice authentication service error")
        
        if result['authenticated']:
            # Success - return user info
            return {
                "success": True,
                "authenticated": True,
                "user": {
                    "id": result['user_id'],
                    "email": result['email'],
                    "name": result['name'],
                    "age_verified": result['age_verified']
                },
                "confidence": float(result['confidence']),
                "age_info": result['age_info']
            }
        else:
            # Authentication failed
            return {
                "success": False,
                "authenticated": False,
                "message": result.get('message', 'Voice not recognized'),
                "age_info": result.get('age_info')
            }
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in voice login: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/register")
async def register_voice_profile(
    user_id: str = Form(..., description="User ID to register voice for"),
    audio: UploadFile = File(..., description="Audio file containing user's voice"),
    metadata: Optional[str] = Form(None, description="Optional metadata as JSON string"),
    service: VoiceAuthService = Depends(get_voice_auth_service)
):
    """
    Register a voice profile for a user
    
    Args:
        user_id: User ID to register voice for
        audio: Audio file containing user's voice sample
        metadata: Optional metadata (JSON string)
    
    Returns:
        Registration result with age verification
    """
    try:
        # Read audio data
        audio_data = await audio.read()
        
        # Parse metadata if provided
        import json
        metadata_dict = json.loads(metadata) if metadata else None
        
        # Register voice profile
        success = await service.register_voice_profile(
            user_id=user_id,
            audio_data=audio_data,
            metadata=metadata_dict
        )
        
        if success:
            # Get the profile to return age info
            profile = await service.get_voice_profile(user_id)
            
            return {
                "success": True,
                "message": "Voice profile registered successfully",
                "user_id": user_id,
                "age_verification": profile.get('age_verification') if profile else None
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to register voice profile")
            
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid metadata JSON")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error registering voice profile: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/verify-age")
async def verify_age(
    audio: UploadFile = File(..., description="Audio file containing voice sample"),
    service: VoiceAuthService = Depends(get_voice_auth_service)
):
    """
    Verify age from voice without authentication
    Useful for anonymous age verification
    
    Args:
        audio: Audio file containing voice sample
    
    Returns:
        Age verification result
    """
    try:
        # Read audio data
        audio_data = await audio.read()
        
        # Verify age
        result = await service.verify_age_only(audio_data)
        
        return {
            "success": True,
            "verified": result['verified'],
            "age_info": result['age_info'],
            "timestamp": result['timestamp']
        }
        
    except Exception as e:
        logger.error(f"Error verifying age: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/profile/{user_id}")
async def get_voice_profile(
    user_id: str,
    service: VoiceAuthService = Depends(get_voice_auth_service)
):
    """
    Get voice profile for a user
    
    Args:
        user_id: User ID
    
    Returns:
        Voice profile with age verification status
    """
    try:
        profile = await service.get_voice_profile(user_id)
        
        if not profile:
            raise HTTPException(status_code=404, detail=f"Voice profile not found for user {user_id}")
        
        return profile
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting voice profile: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/login/base64")
async def voice_login_base64(
    audio_base64: str = Form(..., description="Base64 encoded audio data"),
    service: VoiceAuthService = Depends(get_voice_auth_service)
):
    """
    Authenticate user using voice biometrics (Base64 input)
    Alternative endpoint for clients that send base64 encoded audio
    
    Args:
        audio_base64: Base64 encoded audio data
    
    Returns:
        Authentication result with user information and age verification
    """
    try:
        logger.info(f"Voice login base64 request received, audio length: {len(audio_base64)}")
        
        # Decode base64 audio
        try:
            audio_data = base64.b64decode(audio_base64)
            logger.info(f"Audio decoded successfully: {len(audio_data)} bytes")
        except Exception as decode_error:
            logger.error(f"Base64 decode error: {decode_error}")
            raise HTTPException(status_code=400, detail="Invalid base64 audio data")
        
        # Authenticate voice
        logger.info("Calling service.authenticate_voice...")
        try:
            result = await service.authenticate_voice(audio_data)
            logger.info(f"Service returned result: {result}")
        except Exception as auth_error:
            logger.error(f"Authentication service error: {auth_error}")
            raise HTTPException(status_code=500, detail=f"Authentication failed: {str(auth_error)}")
        
        if result is None:
            logger.error("Authentication service returned None")
            raise HTTPException(status_code=500, detail="Voice authentication service returned None")
        
        logger.info(f"Authentication result: authenticated={result.get('authenticated')}")
        
        if result['authenticated']:
            # Success - return user info
            logger.info("Authentication successful, returning user info")
            return {
                "success": True,
                "authenticated": True,
                "user": {
                    "id": result['user_id'],
                    "email": result['email'],
                    "name": result['name'],
                    "age_verified": result['age_verified']
                },
                "confidence": float(result['confidence']),
                "age_info": result['age_info']
            }
        else:
            # Authentication failed
            logger.info("Authentication failed, returning failure message")
            return {
                "success": False,
                "authenticated": False,
                "message": result.get('message', 'Voice not recognized'),
                "age_info": result.get('age_info')
            }
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in voice login (base64): {str(e)}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")


@router.delete("/profile/{user_id}")
async def delete_voice_profile(
    user_id: str,
    service: VoiceAuthService = Depends(get_voice_auth_service)
):
    """
    Delete voice profile for a user
    
    Args:
        user_id: User ID
    
    Returns:
        Deletion status
    """
    try:
        conn = service.db
        
        query = """
            DELETE FROM voice_profiles 
            WHERE user_id = $1
            RETURNING user_id
        """
        
        result = await conn.fetchval(query, user_id)
        
        if result:
            return {
                "success": True,
                "message": f"Voice profile deleted for user {user_id}"
            }
        else:
            raise HTTPException(status_code=404, detail=f"Voice profile not found for user {user_id}")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting voice profile: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))