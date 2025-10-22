"""
Tenant LLM Configuration Management Endpoints
Handles per-tenant API tokens and inference preferences
"""
from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel, Field, validator
from typing import Optional, Dict, Any
import asyncpg
import os
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/tenants", tags=["Tenant LLM Configuration"])

# Database configuration
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'port': int(os.getenv('DB_PORT', '5434')),
    'database': os.getenv('DB_NAME', 'ai_engine'),
    'user': os.getenv('DB_USER', 'weedgo'),
    'password': os.getenv('DB_PASSWORD', 'your_password_here')
}

# ============================================================================
# Pydantic Models
# ============================================================================

class LLMTokens(BaseModel):
    """Cloud provider API tokens"""
    groq: Optional[str] = Field(None, description="Groq API key (gsk_...)")
    openrouter: Optional[str] = Field(None, description="OpenRouter API key (sk-or-...)")
    llm7: Optional[str] = Field(None, description="LLM7 API key")
    
    @validator('groq')
    def validate_groq(cls, v):
        if v and not v.startswith('gsk_'):
            raise ValueError('Groq API key must start with gsk_')
        return v
    
    @validator('openrouter')
    def validate_openrouter(cls, v):
        if v and not v.startswith('sk-or-'):
            raise ValueError('OpenRouter API key must start with sk-or-')
        return v
    
    class Config:
        schema_extra = {
            "example": {
                "groq": "gsk_xxxxxxxxxxxxxxxxxxxx",
                "openrouter": "sk-or-xxxxxxxxxxxxxxxxxxxx",
                "llm7": "your-llm7-key"
            }
        }


class InferenceConfig(BaseModel):
    """Tenant inference configuration"""
    preferred_provider: str = Field("groq", description="Preferred cloud provider")
    auto_failover: bool = Field(True, description="Auto-switch on rate limits")
    provider_models: Dict[str, str] = Field(
        default_factory=lambda: {
            "groq": "llama-3.3-70b-versatile",
            "openrouter": "deepseek/deepseek-r1",
            "llm7": "gpt-4o-mini"
        },
        description="Active model per provider"
    )
    
    @validator('preferred_provider')
    def validate_provider(cls, v):
        valid_providers = ['groq', 'openrouter', 'llm7']
        if v not in valid_providers:
            raise ValueError(f'Provider must be one of: {", ".join(valid_providers)}')
        return v
    
    class Config:
        schema_extra = {
            "example": {
                "preferred_provider": "groq",
                "auto_failover": True,
                "provider_models": {
                    "groq": "llama-3.3-70b-versatile",
                    "openrouter": "deepseek/deepseek-r1",
                    "llm7": "gpt-4o-mini"
                }
            }
        }


class TokenTestRequest(BaseModel):
    """Request to test API tokens"""
    provider: str = Field(..., description="Provider to test (groq, openrouter, llm7)")
    api_key: str = Field(..., description="API key to test")


class TokenTestResponse(BaseModel):
    """Response from token test"""
    valid: bool
    provider: str
    message: str
    details: Optional[Dict[str, Any]] = None


# ============================================================================
# Helper Functions
# ============================================================================

async def get_db_connection():
    """Get database connection"""
    try:
        conn = await asyncpg.connect(**DB_CONFIG)
        return conn
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database connection failed"
        )


async def verify_tenant_exists(tenant_id: str, conn: asyncpg.Connection):
    """Verify tenant exists"""
    result = await conn.fetchrow(
        "SELECT id, name FROM tenants WHERE id = $1",
        tenant_id
    )
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tenant {tenant_id} not found"
        )
    return result


async def test_groq_token(api_key: str) -> Dict[str, Any]:
    """Test Groq API token"""
    import httpx
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={"Authorization": f"Bearer {api_key}"},
                json={
                    "model": "llama-3.3-70b-versatile",
                    "messages": [{"role": "user", "content": "test"}],
                    "max_tokens": 5
                }
            )
            
            if response.status_code == 200:
                return {"valid": True, "message": "Token is valid"}
            elif response.status_code == 401:
                return {"valid": False, "message": "Invalid API key"}
            elif response.status_code == 429:
                return {"valid": True, "message": "Token is valid (rate limited)"}
            else:
                return {"valid": False, "message": f"Unexpected status: {response.status_code}"}
    except Exception as e:
        return {"valid": False, "message": f"Test failed: {str(e)}"}


async def test_openrouter_token(api_key: str) -> Dict[str, Any]:
    """Test OpenRouter API token"""
    import httpx
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={"Authorization": f"Bearer {api_key}"},
                json={
                    "model": "deepseek/deepseek-r1",
                    "messages": [{"role": "user", "content": "test"}],
                    "max_tokens": 5
                }
            )
            
            if response.status_code == 200:
                return {"valid": True, "message": "Token is valid"}
            elif response.status_code == 401:
                return {"valid": False, "message": "Invalid API key"}
            elif response.status_code == 429:
                return {"valid": True, "message": "Token is valid (rate limited)"}
            else:
                return {"valid": False, "message": f"Unexpected status: {response.status_code}"}
    except Exception as e:
        return {"valid": False, "message": f"Test failed: {str(e)}"}


async def test_llm7_token(api_key: str) -> Dict[str, Any]:
    """Test LLM7 API token"""
    import httpx
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                "https://api.llm7.ai/v1/chat/completions",
                headers={"Authorization": f"Bearer {api_key}"},
                json={
                    "model": "gpt-4o-mini",
                    "messages": [{"role": "user", "content": "test"}],
                    "max_tokens": 5
                }
            )
            
            if response.status_code == 200:
                return {"valid": True, "message": "Token is valid"}
            elif response.status_code == 401:
                return {"valid": False, "message": "Invalid API key"}
            elif response.status_code == 429:
                return {"valid": True, "message": "Token is valid (rate limited)"}
            else:
                return {"valid": False, "message": f"Unexpected status: {response.status_code}"}
    except Exception as e:
        return {"valid": False, "message": f"Test failed: {str(e)}"}


# ============================================================================
# API Endpoints
# ============================================================================

@router.get("/{tenant_id}/llm-tokens")
async def get_llm_tokens(tenant_id: str):
    """
    Get LLM provider tokens for a tenant.
    Returns token existence (not the actual tokens for security).
    """
    conn = await get_db_connection()
    try:
        await verify_tenant_exists(tenant_id, conn)
        
        result = await conn.fetchrow(
            "SELECT llm_tokens FROM tenants WHERE id = $1",
            tenant_id
        )
        
        # Don't return actual tokens, just indicate which are set
        tokens = result['llm_tokens'] if result else {}
        
        return {
            "success": True,
            "tenant_id": tenant_id,
            "tokens_configured": {
                "groq": bool(tokens.get('groq')),
                "openrouter": bool(tokens.get('openrouter')),
                "llm7": bool(tokens.get('llm7'))
            },
            "last_updated": tokens.get('migrated_at') or tokens.get('updated_at')
        }
        
    finally:
        await conn.close()


@router.put("/{tenant_id}/llm-tokens")
async def update_llm_tokens(tenant_id: str, tokens: LLMTokens):
    """
    Update LLM provider tokens for a tenant.
    Only updates provided tokens, leaves others unchanged.
    """
    conn = await get_db_connection()
    try:
        await verify_tenant_exists(tenant_id, conn)
        
        # Get existing tokens
        result = await conn.fetchrow(
            "SELECT llm_tokens FROM tenants WHERE id = $1",
            tenant_id
        )
        
        existing_tokens = result['llm_tokens'] if result and result['llm_tokens'] else {}
        
        # Update only provided tokens
        updated_tokens = {**existing_tokens}
        
        if tokens.groq is not None:
            updated_tokens['groq'] = tokens.groq
        if tokens.openrouter is not None:
            updated_tokens['openrouter'] = tokens.openrouter
        if tokens.llm7 is not None:
            updated_tokens['llm7'] = tokens.llm7
        
        updated_tokens['updated_at'] = datetime.now().isoformat()
        
        # Save to database
        await conn.execute(
            "UPDATE tenants SET llm_tokens = $1 WHERE id = $2",
            updated_tokens,
            tenant_id
        )
        
        logger.info(f"Updated LLM tokens for tenant {tenant_id}")
        
        return {
            "success": True,
            "message": "Tokens updated successfully",
            "tenant_id": tenant_id,
            "tokens_configured": {
                "groq": bool(updated_tokens.get('groq')),
                "openrouter": bool(updated_tokens.get('openrouter')),
                "llm7": bool(updated_tokens.get('llm7'))
            }
        }
        
    except Exception as e:
        logger.error(f"Failed to update tokens: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update tokens: {str(e)}"
        )
    finally:
        await conn.close()


@router.post("/{tenant_id}/llm-tokens/test")
async def test_llm_token(tenant_id: str, request: TokenTestRequest):
    """
    Test an LLM provider API token before saving.
    """
    conn = await get_db_connection()
    try:
        await verify_tenant_exists(tenant_id, conn)
        
        # Test the token based on provider
        if request.provider == 'groq':
            result = await test_groq_token(request.api_key)
        elif request.provider == 'openrouter':
            result = await test_openrouter_token(request.api_key)
        elif request.provider == 'llm7':
            result = await test_llm7_token(request.api_key)
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid provider: {request.provider}"
            )
        
        return TokenTestResponse(
            valid=result['valid'],
            provider=request.provider,
            message=result['message'],
            details=result.get('details')
        )
        
    finally:
        await conn.close()


@router.get("/{tenant_id}/inference-config")
async def get_inference_config(tenant_id: str):
    """
    Get inference configuration for a tenant.
    """
    conn = await get_db_connection()
    try:
        await verify_tenant_exists(tenant_id, conn)
        
        result = await conn.fetchrow(
            "SELECT inference_config FROM tenants WHERE id = $1",
            tenant_id
        )
        
        config = result['inference_config'] if result and result['inference_config'] else {
            "preferred_provider": "groq",
            "auto_failover": True,
            "provider_models": {
                "groq": "llama-3.3-70b-versatile",
                "openrouter": "deepseek/deepseek-r1",
                "llm7": "gpt-4o-mini"
            }
        }
        
        return {
            "success": True,
            "tenant_id": tenant_id,
            "config": config
        }
        
    finally:
        await conn.close()


@router.put("/{tenant_id}/inference-config")
async def update_inference_config(tenant_id: str, config: InferenceConfig):
    """
    Update inference configuration for a tenant.
    """
    conn = await get_db_connection()
    try:
        await verify_tenant_exists(tenant_id, conn)
        
        config_dict = config.dict()
        config_dict['updated_at'] = datetime.now().isoformat()
        
        await conn.execute(
            "UPDATE tenants SET inference_config = $1 WHERE id = $2",
            config_dict,
            tenant_id
        )
        
        logger.info(f"Updated inference config for tenant {tenant_id}: {config.preferred_provider}")
        
        return {
            "success": True,
            "message": "Inference configuration updated successfully",
            "tenant_id": tenant_id,
            "config": config_dict
        }
        
    except Exception as e:
        logger.error(f"Failed to update inference config: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update configuration: {str(e)}"
        )
    finally:
        await conn.close()


@router.get("/{tenant_id}/available-models")
async def get_available_models(tenant_id: str):
    """
    Get available models for each provider.
    """
    conn = await get_db_connection()
    try:
        await verify_tenant_exists(tenant_id, conn)
        
        # Hardcoded model list (can be moved to database later)
        available_models = {
            "groq": [
                {"id": "llama-3.3-70b-versatile", "name": "Llama 3.3 70B", "context": "128K", "speed": "fast"},
                {"id": "llama-3.1-70b-versatile", "name": "Llama 3.1 70B", "context": "128K", "speed": "fast"},
                {"id": "mixtral-8x7b-32768", "name": "Mixtral 8x7B", "context": "32K", "speed": "very_fast"}
            ],
            "openrouter": [
                {"id": "deepseek/deepseek-r1", "name": "DeepSeek R1", "context": "64K", "speed": "medium"},
                {"id": "anthropic/claude-3.5-sonnet", "name": "Claude 3.5 Sonnet", "context": "200K", "speed": "medium"},
                {"id": "google/gemini-pro-1.5", "name": "Gemini Pro 1.5", "context": "1M", "speed": "medium"}
            ],
            "llm7": [
                {"id": "gpt-4o-mini", "name": "GPT-4o Mini", "context": "128K", "speed": "fast"},
                {"id": "gpt-4o", "name": "GPT-4o", "context": "128K", "speed": "medium"},
                {"id": "gpt-4-turbo", "name": "GPT-4 Turbo", "context": "128K", "speed": "medium"}
            ]
        }
        
        return {
            "success": True,
            "tenant_id": tenant_id,
            "models": available_models
        }
        
    finally:
        await conn.close()
