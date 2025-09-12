"""
Registration Integration API
Handles voice registration during user signup flow
"""

from fastapi import APIRouter, Depends, HTTPException, Form, File, UploadFile
from typing import Optional, Dict, Any
import logging
import json
import requests
import os
from datetime import datetime
from services.voice_auth_service import VoiceAuthService
from api.auth_voice import get_voice_auth_service

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/registration", tags=["registration"])

# Configuration for identity service
IDENTITY_SERVICE_URL = os.getenv('IDENTITY_SERVICE_URL', 'http://localhost:5011')


@router.post("/register-with-voice")
async def register_user_with_voice(
    # Standard registration fields
    email: str = Form(..., description="User email address"),
    password: str = Form(..., description="User password"),
    first_name: str = Form(..., description="User first name"),
    last_name: str = Form(..., description="User last name"),
    phone_number: str = Form(..., description="User phone number"),
    tenant_id: str = Form(..., description="Tenant ID"),
    date_of_birth: str = Form(..., description="Date of birth (ISO format)"),
    accept_terms: bool = Form(..., description="Accept terms and conditions"),
    accept_privacy: bool = Form(..., description="Accept privacy policy"),
    role: str = Form(default="Customer", description="User role"),
    registration_source: str = Form(default="web", description="Registration source"),
    
    # Voice registration fields (optional)
    voice_audio: Optional[UploadFile] = File(None, description="Voice sample for authentication"),
    enable_voice_auth: bool = Form(default=False, description="Enable voice authentication"),
    
    # Optional fields
    accept_marketing: bool = Form(default=False, description="Accept marketing communications"),
    referral_code: Optional[str] = Form(None, description="Referral code"),
    device_id: Optional[str] = Form(None, description="Device ID"),
    
    # Voice auth service dependency
    voice_service: VoiceAuthService = Depends(get_voice_auth_service)
):
    """
    Register a new user with optional voice authentication setup.
    
    This endpoint:
    1. Calls the identity service to register the user
    2. Optionally registers voice authentication if audio is provided
    3. Returns combined registration and voice setup results
    """
    
    try:
        logger.info(f"Starting registration with voice for {email}")
        
        # Step 1: Register user with identity service
        user_registration_data = {
            "email": email,
            "password": password,
            "firstName": first_name,
            "lastName": last_name,
            "phoneNumber": phone_number,
            "tenantId": tenant_id,
            "dateOfBirth": date_of_birth,
            "acceptTermsAndConditions": accept_terms,
            "acceptPrivacyPolicy": accept_privacy,
            "acceptMarketingCommunications": accept_marketing,
            "role": role,
            "registrationSource": registration_source,
            "referralCode": referral_code,
            "deviceInfo": {
                "deviceId": device_id
            } if device_id else None
        }
        
        # Call identity service
        identity_response = await call_identity_service(user_registration_data)
        
        if not identity_response.get('success'):
            logger.error(f"User registration failed: {identity_response}")
            raise HTTPException(
                status_code=400, 
                detail=f"Registration failed: {identity_response.get('message', 'Unknown error')}"
            )
        
        user_id = identity_response.get('userId')
        logger.info(f"User registered successfully with ID: {user_id}")
        
        # Step 2: Optional voice registration
        voice_registration_result = None
        if enable_voice_auth and voice_audio and user_id:
            try:
                logger.info(f"Setting up voice authentication for user {user_id}")
                
                # Read audio data
                audio_data = await voice_audio.read()
                
                # Register voice profile
                voice_success = await voice_service.register_voice_profile(
                    user_id=str(user_id),
                    audio_data=audio_data,
                    metadata={
                        "registration_source": registration_source,
                        "setup_during_registration": True,
                        "device_id": device_id
                    }
                )
                
                if voice_success:
                    # Get the created voice profile for response
                    voice_profile = await voice_service.get_voice_profile(str(user_id))
                    voice_registration_result = {
                        "success": True,
                        "message": "Voice authentication setup successfully",
                        "age_verification": voice_profile.get('age_verification') if voice_profile else None
                    }
                    logger.info(f"Voice authentication setup completed for user {user_id}")
                else:
                    voice_registration_result = {
                        "success": False,
                        "message": "Voice authentication setup failed",
                        "error": "Failed to register voice profile"
                    }
                    logger.warning(f"Voice registration failed for user {user_id}")
                    
            except Exception as voice_error:
                logger.error(f"Voice registration error for user {user_id}: {str(voice_error)}")
                voice_registration_result = {
                    "success": False,
                    "message": "Voice authentication setup failed",
                    "error": str(voice_error)
                }
        
        # Step 3: Prepare combined response
        response = {
            "success": True,
            "message": "Registration completed successfully",
            "user_registration": {
                "user_id": user_id,
                "email": identity_response.get('email'),
                "requires_email_confirmation": identity_response.get('requiresEmailConfirmation', False)
            },
            "voice_authentication": voice_registration_result
        }
        
        logger.info(f"Registration with voice completed for {email}")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Registration with voice failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Registration failed: {str(e)}")


async def call_identity_service(registration_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Call the identity service to register a new user.
    """
    try:
        # Convert the data to match the identity service expected format
        identity_payload = {
            "email": registration_data["email"],
            "password": registration_data["password"],
            "firstName": registration_data["firstName"],
            "lastName": registration_data["lastName"],
            "phoneNumber": registration_data["phoneNumber"],
            "tenantId": registration_data["tenantId"],
            "dateOfBirth": registration_data["dateOfBirth"],
            "acceptTermsAndConditions": registration_data["acceptTermsAndConditions"],
            "acceptPrivacyPolicy": registration_data["acceptPrivacyPolicy"],
            "acceptMarketingCommunications": registration_data["acceptMarketingCommunications"],
            "role": registration_data["role"],
            "registrationSource": registration_data["registrationSource"]
        }
        
        # Add optional fields
        if registration_data.get("referralCode"):
            identity_payload["referralCode"] = registration_data["referralCode"]
        
        if registration_data.get("deviceInfo"):
            identity_payload["deviceInfo"] = registration_data["deviceInfo"]
        
        url = f"{IDENTITY_SERVICE_URL}/api/v1/registration/register"
        headers = {
            "Content-Type": "application/json",
            "User-Agent": "WeedGo-AI-Engine/1.0"
        }
        
        logger.info(f"Calling identity service at {url}")
        
        # Use requests for synchronous HTTP call (can be replaced with aiohttp for async)
        import aiohttp
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=identity_payload, headers=headers) as response:
                response_data = await response.json()
                
                if response.status == 201:
                    return {
                        "success": True,
                        "userId": response_data.get("userId"),
                        "email": response_data.get("email"),
                        "requiresEmailConfirmation": response_data.get("requiresEmailConfirmation", False),
                        "message": response_data.get("message", "Registration successful")
                    }
                else:
                    logger.error(f"Identity service error {response.status}: {response_data}")
                    return {
                        "success": False,
                        "message": response_data.get("message", "Registration failed"),
                        "errors": response_data.get("errors", {})
                    }
                    
    except Exception as e:
        logger.error(f"Error calling identity service: {str(e)}")
        return {
            "success": False,
            "message": f"Identity service unavailable: {str(e)}",
            "errors": {"identity_service": [str(e)]}
        }


@router.post("/setup-voice-after-registration")
async def setup_voice_after_registration(
    user_id: str = Form(..., description="User ID from registration"),
    audio: UploadFile = File(..., description="Voice sample for authentication"),
    metadata: Optional[str] = Form(None, description="Optional metadata as JSON string"),
    service: VoiceAuthService = Depends(get_voice_auth_service)
):
    """
    Set up voice authentication for an existing user after registration.
    
    This endpoint can be called if the user skips voice setup during registration
    but wants to enable it later.
    """
    try:
        logger.info(f"Setting up voice authentication for existing user {user_id}")
        
        # Read audio data
        audio_data = await audio.read()
        
        # Parse metadata if provided
        parsed_metadata = {}
        if metadata:
            try:
                parsed_metadata = json.loads(metadata)
            except json.JSONDecodeError:
                logger.warning(f"Invalid metadata JSON for user {user_id}")
        
        # Add setup context
        parsed_metadata.update({
            "setup_after_registration": True,
            "setup_timestamp": datetime.now().isoformat()
        })
        
        # Register voice profile
        success = await service.register_voice_profile(
            user_id=user_id,
            audio_data=audio_data,
            metadata=parsed_metadata
        )
        
        if success:
            # Get the created profile
            profile = await service.get_voice_profile(user_id)
            
            return {
                "success": True,
                "message": "Voice authentication setup successfully",
                "user_id": user_id,
                "age_verification": profile.get('age_verification') if profile else None
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to register voice profile")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Voice setup after registration failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))