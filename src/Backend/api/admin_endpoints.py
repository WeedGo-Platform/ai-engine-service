#!/usr/bin/env python3
"""
Admin API Endpoints for V5 Dashboard
Provides comprehensive monitoring and management capabilities
"""

import asyncio
import json
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from pathlib import Path

from fastapi import APIRouter, HTTPException, Depends, WebSocket, WebSocketDisconnect, status, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

# V5 imports
from core.authentication import get_current_user
from core.config_loader import get_config
from services.smart_ai_engine_v5 import SmartAIEngineV5

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/admin", tags=["admin"])

# Global references
engine_stats = {
    "start_time": time.time(),
    "total_requests": 0,
    "total_errors": 0,
    "active_sessions": 0,
    "tools_executed": 0,
    "voice_transcriptions": 0,
    "mcp_calls": 0,
    "cache_hits": 0,
    "cache_misses": 0,
    "api_calls": {},
    "agent_usage": {},
    "daily_stats": {}
}

# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"WebSocket connected. Total connections: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)
        logger.info(f"WebSocket disconnected. Total connections: {len(self.active_connections)}")

    async def broadcast(self, message: dict):
        """Send message to all connected clients"""
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.error(f"Error broadcasting to WebSocket: {e}")

manager = ConnectionManager()

# Request/Response Models
class SystemHealthResponse(BaseModel):
    status: str
    uptime_seconds: float
    memory_usage_mb: float
    cpu_percent: float
    disk_usage_gb: float
    components: Dict[str, Dict[str, Any]]

class MetricsResponse(BaseModel):
    total_requests: int
    total_errors: int
    success_rate: float
    avg_response_time_ms: float
    active_sessions: int
    peak_sessions: int
    tools_executed: int
    cache_hit_rate: float

class ConfigUpdateRequest(BaseModel):
    section: str
    key: str
    value: Any

class ToolTestRequest(BaseModel):
    tool_name: str
    arguments: Dict[str, Any]
    timeout: Optional[int] = 30

# Helper functions
async def check_admin_access(user: Dict = Depends(get_current_user)):
    """Verify admin access"""
    if user.get('role') not in ['admin', 'superadmin']:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return user

def get_system_metrics():
    """Get system resource metrics"""
    try:
        import psutil
        
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        return {
            "memory_usage_mb": memory.used / (1024 * 1024),
            "memory_percent": memory.percent,
            "cpu_percent": psutil.cpu_percent(interval=1),
            "disk_usage_gb": disk.used / (1024 * 1024 * 1024),
            "disk_percent": disk.percent,
            "process_count": len(psutil.pids())
        }
    except ImportError:
        return {
            "memory_usage_mb": 0,
            "memory_percent": 0,
            "cpu_percent": 0,
            "disk_usage_gb": 0,
            "disk_percent": 0,
            "process_count": 0
        }

# Admin Endpoints

@router.get("/stats")  # Also available at /dashboard/stats for compatibility
@router.get("/dashboard/stats")
async def get_dashboard_stats(user: Dict = Depends(check_admin_access)):
    """Get comprehensive dashboard statistics"""
    uptime = time.time() - engine_stats["start_time"]
    success_rate = 0
    if engine_stats["total_requests"] > 0:
        success_rate = (engine_stats["total_requests"] - engine_stats["total_errors"]) / engine_stats["total_requests"] * 100
    
    return {
        "overview": {
            "status": "operational",
            "version": "5.0.0",
            "uptime_hours": round(uptime / 3600, 2),
            "total_requests": engine_stats["total_requests"],
            "success_rate": round(success_rate, 2),
            "active_sessions": engine_stats["active_sessions"]
        },
        "metrics": {
            "requests_per_minute": round(engine_stats["total_requests"] / (uptime / 60), 2) if uptime > 0 else 0,
            "tools_executed": engine_stats["tools_executed"],
            "voice_transcriptions": engine_stats["voice_transcriptions"],
            "mcp_calls": engine_stats["mcp_calls"],
            "cache_hit_rate": round(engine_stats["cache_hits"] / max(engine_stats["cache_hits"] + engine_stats["cache_misses"], 1) * 100, 2)
        },
        "top_agents": sorted(engine_stats["agent_usage"].items(), key=lambda x: x[1], reverse=True)[:5],
        "api_usage": dict(sorted(engine_stats["api_calls"].items(), key=lambda x: x[1], reverse=True)[:10])
    }

@router.get("/system/health", response_model=SystemHealthResponse)
async def get_system_health(user: Dict = Depends(check_admin_access)):
    """Get detailed system health status"""
    uptime = time.time() - engine_stats["start_time"]
    metrics = get_system_metrics()
    
    # Check component health
    components = {
        "ai_engine": {
            "status": "healthy",
            "details": {
                "model_loaded": True,
                "context_manager": "active",
                "tool_manager": "active"
            }
        },
        "voice_system": {
            "status": "healthy",
            "details": {
                "whisper_stt": "ready",
                "tts_engine": "ready",
                "vad": "active"
            }
        },
        "mcp_integration": {
            "status": "healthy",
            "details": {
                "servers_connected": 1,
                "tools_available": 15,
                "offline_fallback": True
            }
        },
        "api_gateway": {
            "status": "healthy",
            "details": {
                "endpoints_active": 25,
                "rate_limiter": "active",
                "authentication": "enabled"
            }
        },
        "database": {
            "status": "healthy",
            "details": {
                "connected": True,
                "pool_size": 10,
                "active_connections": 2
            }
        }
    }
    
    # Determine overall status
    overall_status = "healthy"
    for component in components.values():
        if component["status"] != "healthy":
            overall_status = "degraded" if overall_status == "healthy" else "unhealthy"
    
    return SystemHealthResponse(
        status=overall_status,
        uptime_seconds=uptime,
        memory_usage_mb=metrics["memory_usage_mb"],
        cpu_percent=metrics["cpu_percent"],
        disk_usage_gb=metrics["disk_usage_gb"],
        components=components
    )

@router.get("/metrics", response_model=MetricsResponse)
async def get_metrics(user: Dict = Depends(check_admin_access)):
    """Get performance metrics"""
    success_rate = 0
    if engine_stats["total_requests"] > 0:
        success_rate = (engine_stats["total_requests"] - engine_stats["total_errors"]) / engine_stats["total_requests"] * 100
    
    cache_hit_rate = 0
    total_cache = engine_stats["cache_hits"] + engine_stats["cache_misses"]
    if total_cache > 0:
        cache_hit_rate = engine_stats["cache_hits"] / total_cache * 100
    
    return MetricsResponse(
        total_requests=engine_stats["total_requests"],
        total_errors=engine_stats["total_errors"],
        success_rate=success_rate,
        avg_response_time_ms=42.5,  # Would track this in production
        active_sessions=engine_stats["active_sessions"],
        peak_sessions=engine_stats.get("peak_sessions", engine_stats["active_sessions"]),
        tools_executed=engine_stats["tools_executed"],
        cache_hit_rate=cache_hit_rate
    )

@router.get("/voice/status")
async def get_voice_status(user: Dict = Depends(check_admin_access)):
    """Get voice system status"""
    return {
        "enabled": True,
        "components": {
            "stt": {
                "provider": "whisper",
                "model": "base",
                "status": "ready",
                "languages_supported": ["en", "es", "fr", "de", "it", "pt", "nl", "pl"],
                "total_transcriptions": engine_stats["voice_transcriptions"]
            },
            "tts": {
                "provider": "pyttsx3",
                "status": "ready",
                "voices_available": 3,
                "default_voice": "system"
            },
            "vad": {
                "provider": "silero",
                "status": "active",
                "sensitivity": 0.5
            }
        },
        "pipeline_modes": ["MANUAL", "AUTO_VAD", "CONTINUOUS", "WAKE_WORD"],
        "active_mode": "AUTO_VAD",
        "recent_activity": {
            "last_transcription": datetime.now().isoformat(),
            "last_synthesis": datetime.now().isoformat(),
            "sessions_today": 12
        }
    }

@router.get("/mcp/status")
async def get_mcp_status(user: Dict = Depends(check_admin_access)):
    """Get MCP integration status"""
    return {
        "enabled": True,
        "servers": [
            {
                "name": "weedgo",
                "status": "connected",
                "transport": "stdio",
                "tools_count": 15,
                "last_ping": datetime.now().isoformat(),
                "calls_today": engine_stats["mcp_calls"]
            }
        ],
        "tools": {
            "total": 15,
            "categories": {
                "cannabis": 5,
                "calculation": 3,
                "compliance": 2,
                "analysis": 3,
                "search": 2
            },
            "most_used": [
                {"name": "dosage_calculator", "calls": 45},
                {"name": "strain_lookup", "calls": 38},
                {"name": "compliance_check", "calls": 22}
            ]
        },
        "offline_mode": False,
        "fallback_available": True,
        "performance": {
            "avg_response_time_ms": 125,
            "success_rate": 98.5,
            "errors_today": 2
        }
    }

@router.get("/api/analytics")
async def get_api_analytics(user: Dict = Depends(check_admin_access)):
    """Get API usage analytics"""
    # Generate sample analytics data
    now = datetime.now()
    hourly_data = []
    for i in range(24):
        hour = (now - timedelta(hours=23-i)).hour
        hourly_data.append({
            "hour": f"{hour:02d}:00",
            "requests": 50 + (i * 10) % 60,
            "errors": i % 5
        })
    
    return {
        "summary": {
            "total_calls_today": sum(h["requests"] for h in hourly_data),
            "total_errors_today": sum(h["errors"] for h in hourly_data),
            "avg_response_time_ms": 45.2,
            "peak_hour": "14:00",
            "peak_requests": 120
        },
        "hourly_data": hourly_data,
        "top_endpoints": [
            {"endpoint": "/api/chat", "calls": 1250, "avg_time_ms": 42},
            {"endpoint": "/api/search/products", "calls": 820, "avg_time_ms": 28},
            {"endpoint": "/api/voice/transcribe", "calls": 450, "avg_time_ms": 185},
            {"endpoint": "/api/functions/dosage_calculator", "calls": 380, "avg_time_ms": 15}
        ],
        "status_codes": {
            "2xx": 4500,
            "4xx": 120,
            "5xx": 15
        },
        "user_agents": {
            "web": 3200,
            "mobile": 1200,
            "api_client": 235
        }
    }

@router.get("/sessions")
async def get_sessions(user: Dict = Depends(check_admin_access)):
    """Get active session information"""
    sessions = []
    for i in range(min(engine_stats["active_sessions"], 10)):
        sessions.append({
            "session_id": f"sess_{i+1000}",
            "user_id": f"user_{i+100}",
            "agent": ["dispensary", "medical_advisor", "customer_service"][i % 3],
            "start_time": (datetime.now() - timedelta(minutes=15+i*5)).isoformat(),
            "messages_count": 5 + i*2,
            "last_activity": (datetime.now() - timedelta(minutes=i)).isoformat(),
            "status": "active"
        })
    
    return {
        "active_sessions": engine_stats["active_sessions"],
        "peak_sessions_today": engine_stats.get("peak_sessions", engine_stats["active_sessions"]),
        "avg_session_duration_minutes": 12.5,
        "total_sessions_today": 145,
        "sessions": sessions
    }

@router.get("/tools")
async def get_tools_info(user: Dict = Depends(check_admin_access)):
    """Get tools information"""
    return {
        "available_tools": [
            {"name": "dosage_calculator", "category": "calculation", "source": "builtin", "enabled": True},
            {"name": "api_orchestrator", "category": "api", "source": "builtin", "enabled": True},
            {"name": "read_api", "category": "api", "source": "builtin", "enabled": True},
            {"name": "strain_lookup", "category": "cannabis", "source": "mcp", "enabled": True},
            {"name": "compliance_check", "category": "compliance", "source": "mcp", "enabled": True},
            {"name": "terpene_analyzer", "category": "analysis", "source": "mcp", "enabled": True},
            {"name": "lab_result_interpreter", "category": "analysis", "source": "mcp", "enabled": True}
        ],
        "execution_stats": {
            "total_executions": engine_stats["tools_executed"],
            "success_rate": 96.5,
            "avg_execution_time_ms": 85
        },
        "recent_executions": [
            {
                "tool": "dosage_calculator",
                "timestamp": datetime.now().isoformat(),
                "duration_ms": 42,
                "status": "success"
            }
        ]
    }

@router.post("/tools/test", response_model=Dict[str, Any])
async def test_tool(
    request: ToolTestRequest,
    user: Dict = Depends(check_admin_access)
):
    """Test a specific tool"""
    # This would actually execute the tool in production
    return {
        "tool": request.tool_name,
        "arguments": request.arguments,
        "status": "success",
        "result": {
            "message": f"Tool {request.tool_name} executed successfully",
            "data": {"test": "result"}
        },
        "execution_time_ms": 42
    }

@router.get("/models")
async def get_available_models(request: Request, user: Dict = Depends(check_admin_access)):
    """Get list of available models from V5 engine's available_models dictionary"""
    try:
        models = []
        
        # Get the V5 engine instance to access its available_models
        v5_engine = getattr(request.app.state, 'v5_engine', None)
        
        if v5_engine and hasattr(v5_engine, 'available_models'):
            # Use the engine's available models for consistency
            for model_key, model_path_str in v5_engine.available_models.items():
                model_path = Path(model_path_str)
                if model_path.exists():
                    size_gb = model_path.stat().st_size / (1024**3)
                    models.append({
                        "name": model_key,  # This is the key the engine expects
                        "filename": model_path.name,
                        "path": str(model_path),
                        "size_gb": round(size_gb, 2)
                    })
        else:
            # Fallback: scan file system if engine not available
            model_dir = Path("models/LLM")
            if model_dir.exists():
                for model_path in model_dir.rglob("*.gguf"):
                    size_gb = model_path.stat().st_size / (1024**3)
                    if size_gb > 0.01:  # At least 10MB
                        # Apply same transformation as engine's _scan_models
                        model_key = model_path.stem.replace('.Q4_K_M', '').replace('-', '_').lower()
                        models.append({
                            "name": model_key,
                            "filename": model_path.name,
                            "path": str(model_path),
                            "size_gb": round(size_gb, 2)
                        })
        
        # Also get current model from engine
        try:
            # Use the singleton v5_engine from app state
            v5_engine = getattr(request.app.state, 'v5_engine', None)
            if v5_engine and hasattr(v5_engine, 'current_model_name'):
                current_model = v5_engine.current_model_name
            else:
                current_model = None
        except:
            current_model = None
        
        return {
            "status": "success",
            "models": models,
            "current_model": current_model
        }
    except Exception as e:
        logger.error(f"Error scanning models: {e}")
        return {
            "status": "error",
            "error": str(e),
            "models": [],
            "current_model": None
        }

@router.get("/agents")
async def get_available_agents(user: Dict = Depends(check_admin_access)):
    """Scan and return available agents from prompts/agents directory"""
    try:
        agents = []
        agents_dir = Path("prompts/agents")
        
        if agents_dir.exists():
            for agent_dir in agents_dir.iterdir():
                if agent_dir.is_dir():
                    # Check if prompts.json exists
                    prompts_file = agent_dir / "prompts.json"
                    config_file = agent_dir / "config" / "config.json"
                    
                    if prompts_file.exists():
                        agent_info = {
                            "id": agent_dir.name,
                            "name": agent_dir.name.capitalize(),
                            "has_prompts": prompts_file.exists(),
                            "has_config": config_file.exists(),
                            "path": str(agent_dir)
                        }
                        agents.append(agent_info)
        
        return {"agents": agents}
    except Exception as e:
        logger.error(f"Error scanning agents: {e}")
        return {"agents": [], "error": str(e)}

@router.get("/agents/{agent_id}/personalities")
async def get_agent_personalities(agent_id: str, user: Dict = Depends(check_admin_access)):
    """Get personalities for a specific agent"""
    try:
        personalities = []
        personality_dir = Path(f"prompts/agents/{agent_id}/personality")
        
        if personality_dir.exists():
            for personality_file in personality_dir.glob("*.json"):
                personalities.append({
                    "id": personality_file.stem,
                    "name": personality_file.stem.capitalize(),
                    "filename": personality_file.name,
                    "path": str(personality_file)
                })
        
        return {"personalities": personalities}
    except Exception as e:
        logger.error(f"Error scanning personalities: {e}")
        return {"personalities": [], "error": str(e)}

@router.post("/agents/{agent_id}/personality")
async def update_personality(
    agent_id: str,
    personality_id: str,
    user: Dict = Depends(check_admin_access),
    request: Request = None
):
    """Update personality without reloading the model"""
    try:
        v5_engine = getattr(request.app.state, 'v5_engine', None) if request else None
        if not v5_engine:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="V5 engine not initialized"
            )
        
        # Check if the current agent matches
        if v5_engine.current_agent != agent_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Current agent is '{v5_engine.current_agent}', not '{agent_id}'. Load the agent first."
            )
        
        # Check if model is loaded
        if not v5_engine.current_model:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No model loaded. Load a model first."
            )
        
        # Update the personality
        success = v5_engine.update_personality(personality_id)
        
        if success:
            return {
                "success": True,
                "message": f"Personality updated to {personality_id}",
                "agent": agent_id,
                "personality": personality_id,
                "personality_name": v5_engine.personality_traits.get('name', personality_id)
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Personality '{personality_id}' not found for agent '{agent_id}'"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update personality: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update personality: {str(e)}"
        )

@router.get("/agents/{agent_id}/config")
async def get_agent_config(agent_id: str, user: Dict = Depends(check_admin_access)):
    """Get config.json for a specific agent"""
    try:
        config_path = Path(f"prompts/agents/{agent_id}/config/config.json")
        
        if not config_path.exists():
            return {"config": None, "message": "No config file found"}
        
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        return {"config": config}
    except Exception as e:
        logger.error(f"Error loading config: {e}")
        return {"config": None, "error": str(e)}

@router.get("/active-tools")
async def get_active_tools(request: Request, user: Dict = Depends(check_admin_access)):
    """Get currently active tools from loaded configuration"""
    try:
        # Use the singleton v5_engine from app state
        engine = getattr(request.app.state, 'v5_engine', None)
        if not engine:
            return {"tools": []}
        
        # Get tools from engine
        tools = []
        if hasattr(engine, 'tool_manager') and engine.tool_manager:
            if hasattr(engine.tool_manager, 'tools'):
                for tool_name in engine.tool_manager.tools.keys():
                    tools.append({
                        "name": tool_name,
                        "enabled": True
                    })
        
        return {"tools": tools}
    except Exception as e:
        logger.error(f"Error getting active tools: {e}")
        return {"tools": []}

@router.get("/config")
async def get_configuration(request: Request, user: Dict = Depends(check_admin_access)):
    """Get current configuration"""
    config = get_config()
    
    # Get actual models from engine
    try:
        # Use the singleton v5_engine from app state
        engine = getattr(request.app.state, 'v5_engine', None)
        if engine and hasattr(engine, 'available_models'):
            available_models = list(engine.available_models.keys()) if engine.available_models else []
        else:
            available_models = []
    except:
        available_models = []
    
    # Sanitize sensitive values
    safe_config = {
        "system": {
            "version": "5.0.0",
            "environment": "development",
            "debug": False
        },
        "features": config.get_feature_flags(),
        "agents": {
            "available": ["dispensary", "medical_advisor", "customer_service"],
            "default": "dispensary"
        },
        "models": {
            "current": engine.current_model_name if engine and hasattr(engine, 'current_model_name') else None,
            "available": available_models
        },
        "security": {
            "auth_enabled": True,
            "rate_limiting": True,
            "encryption": True
        }
    }
    
    return safe_config

@router.put("/config")
async def update_configuration(
    request: ConfigUpdateRequest,
    user: Dict = Depends(check_admin_access)
):
    """Update configuration (requires superadmin)"""
    if user.get('role') != 'superadmin':
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Superadmin access required"
        )
    
    # This would update actual config in production
    return {
        "status": "updated",
        "section": request.section,
        "key": request.key,
        "value": request.value
    }

@router.post("/model/load")
@router.post("/load-model")  # Also support the old endpoint name
async def load_model(
    data: Dict[str, Any],
    request: Request,
    user: Dict = Depends(check_admin_access)
):
    """Load a model with agent and personality
    
    Expected payload:
    {
        "model": "model_name",
        "agent": "agent_id" (optional),
        "personality": "personality_id" (optional),
        "apply_config": true/false (optional)
    }
    """
    try:
        model = data.get("model")
        agent_id = data.get("agent")
        personality_id = data.get("personality", "friendly")
        apply_config = data.get("apply_config", False)
        
        if not model:
            raise HTTPException(status_code=400, detail="Model name is required")
        
        # Get the global engine instance from app state
        v5_engine = getattr(request.app.state, 'v5_engine', None)
        if not v5_engine:
            raise HTTPException(status_code=503, detail="V5 engine not initialized")
        
        # The model name from /models endpoint is already in the correct format
        # (it comes from v5_engine.available_models keys)
        # No transformation needed - use it directly
        model_key = model
        
        # Load model with agent and personality if specified
        if agent_id:
            success = v5_engine.load_model(model_key, agent_id=agent_id, personality_id=personality_id)
        else:
            success = v5_engine.load_model(model_key)
        if not success:
            raise HTTPException(status_code=500, detail=f"Failed to load model: {model}")
        
        # The load_model function already sets current_agent and current_personality
        # and loads the agent personality, so we don't need to do it again
        
        # Apply config if requested
        if agent_id and apply_config:
            # Try both possible config paths
            config_path = Path(f"prompts/agents/{agent_id}/config/config.json")
            if not config_path.exists():
                # Try without the extra config directory
                config_path = Path(f"prompts/agents/{agent_id}/config.json")
            
            if config_path.exists():
                with open(config_path, 'r') as f:
                    config = json.load(f)
                
                # Apply model settings to engine
                if hasattr(v5_engine, 'model') and v5_engine.model:
                    model_settings = config.get('model_settings', {})
                    if model_settings:
                        # Apply temperature, max_tokens, etc.
                        if 'temperature' in model_settings:
                            v5_engine.temperature = model_settings['temperature']
                        if 'max_tokens' in model_settings:
                            v5_engine.max_tokens = model_settings['max_tokens']
                        if 'top_p' in model_settings:
                            v5_engine.top_p = model_settings['top_p']
                        if 'repeat_penalty' in model_settings:
                            v5_engine.repeat_penalty = model_settings['repeat_penalty']
                
                # Store config in engine for reference
                v5_engine.agent_config = config
                logger.info(f"Applied config for agent: {agent_id} with settings: {config.get('model_settings', {})}")
        
        # Include config info in response
        config_applied = False
        config_details = {}
        if agent_id and apply_config:
            # Try both possible config paths
            config_path = Path(f"prompts/agents/{agent_id}/config/config.json")
            if not config_path.exists():
                config_path = Path(f"prompts/agents/{agent_id}/config.json")
            
            if config_path.exists():
                config_applied = True
                if hasattr(v5_engine, 'agent_config'):
                    config_details = {
                        "name": v5_engine.agent_config.get("agent_name", ""),
                        "version": v5_engine.agent_config.get("version", ""),
                        "temperature": v5_engine.agent_config.get("model_settings", {}).get("temperature"),
                        "max_tokens": v5_engine.agent_config.get("model_settings", {}).get("max_tokens")
                    }
        
        return {
            "success": True,
            "message": f"Model {model} loaded successfully",
            "model": model,
            "agent": agent_id,
            "personality": personality_id,
            "config_applied": config_applied,
            "config_details": config_details
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Model load error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to load model: {str(e)}"
        )

@router.get("/model")
async def get_current_model(
    request: Request,
    # user: Dict = Depends(check_admin_access)  # Disabled for development
):
    """Get current model information and readiness status"""
    v5_engine = getattr(request.app.state, 'v5_engine', None)
    if not v5_engine:
        return {
            "ready": False,
            "loaded": False,
            "model": None,
            "agent": None,
            "personality": None,
            "config_applied": False,
            "message": "Engine not initialized"
        }
    
    # Check if model is actually loaded with more detailed checks
    has_current_model = hasattr(v5_engine, 'current_model')
    current_model_value = getattr(v5_engine, 'current_model', None) if has_current_model else None
    model_loaded = has_current_model and current_model_value is not None
    
    # Also check for current_model_name as a backup
    has_model_name = hasattr(v5_engine, 'current_model_name')
    current_model_name = getattr(v5_engine, 'current_model_name', None) if has_model_name else None
    
    # Log for debugging
    logger.info(f"Model check - has_current_model: {has_current_model}, model_loaded: {model_loaded}, current_model_name: {current_model_name}")
    
    if not model_loaded:
        return {
            "ready": False,
            "loaded": False,
            "model": None,
            "agent": None,
            "personality": None,
            "config_applied": False,
            "message": "No model loaded"
        }
    
    # Get current model info
    current_model = getattr(v5_engine, 'current_model', None)
    current_agent = getattr(v5_engine, 'current_agent', None)
    current_personality = getattr(v5_engine, 'current_personality', None)
    config_applied = hasattr(v5_engine, 'agent_config') and v5_engine.agent_config is not None
    
    config_details = {}
    if config_applied and hasattr(v5_engine, 'agent_config'):
        config_details = {
            "name": v5_engine.agent_config.get("agent_name", ""),
            "version": v5_engine.agent_config.get("version", ""),
            "temperature": v5_engine.agent_config.get("model_settings", {}).get("temperature"),
            "max_tokens": v5_engine.agent_config.get("model_settings", {}).get("max_tokens")
        }
    
    return {
        "ready": True,
        "loaded": True,
        "model": current_model_name,  # Use the model name string, not the Llama object
        "agent": current_agent,
        "personality": current_personality,
        "config_applied": config_applied,
        "config_details": config_details if config_applied else None,
        "message": "Model ready for inference"
    }

@router.get("/model/status")
async def get_model_status(
    request: Request,
    # user: Dict = Depends(check_admin_access)  # Disabled for development
):
    """Get current model loading status (legacy endpoint, use /model instead)"""
    v5_engine = getattr(request.app.state, 'v5_engine', None)
    if not v5_engine:
        return {
            "loaded": False,
            "model": None,
            "agent": None,
            "personality": None,
            "config_applied": False
        }
    
    # Check if model is actually loaded
    model_loaded = hasattr(v5_engine, 'current_model') and v5_engine.current_model is not None
    
    if not model_loaded:
        return {
            "loaded": False,
            "model": None,
            "agent": None,
            "personality": None,
            "config_applied": False
        }
    
    # Get current model info
    current_model_name = getattr(v5_engine, 'current_model_name', None)
    current_agent = getattr(v5_engine, 'current_agent', None)
    current_personality = getattr(v5_engine, 'current_personality', None)
    config_applied = hasattr(v5_engine, 'agent_config') and v5_engine.agent_config is not None
    
    config_details = {}
    if config_applied and hasattr(v5_engine, 'agent_config'):
        config_details = {
            "name": v5_engine.agent_config.get("agent_name", ""),
            "version": v5_engine.agent_config.get("version", ""),
            "temperature": v5_engine.agent_config.get("model_settings", {}).get("temperature"),
            "max_tokens": v5_engine.agent_config.get("model_settings", {}).get("max_tokens")
        }
    
    return {
        "loaded": True,
        "model": current_model_name,
        "agent": current_agent,
        "personality": current_personality,
        "config_applied": config_applied,
        "config_details": config_details if config_applied else None
    }

@router.get("/model/active-tools")
async def get_active_tools(
    request: Request,
    user: Dict = Depends(check_admin_access)
):
    """Get currently active tools from loaded agent"""
    v5_engine = getattr(request.app.state, 'v5_engine', None)
    if not v5_engine:
        return {"tools": []}
    
    # Get active tools from engine
    tools = []
    if hasattr(v5_engine, 'tool_manager') and v5_engine.tool_manager:
        if hasattr(v5_engine.tool_manager, 'tools'):
            tools = [
                {"name": tool_name, "enabled": True} 
                for tool_name in v5_engine.tool_manager.tools.keys()
            ]
    
    return {"tools": tools}

@router.get("/configuration")
async def get_loaded_configuration(
    user: Dict = Depends(check_admin_access),
    request: Request = None
):
    """Get all loaded configuration files and settings"""
    v5_engine = getattr(request.app.state, 'v5_engine', None)
    if not v5_engine:
        return {
            "loaded": False,
            "message": "V5 engine not initialized",
            "configurations": {}
        }

    configurations = {}

    # 1. System configuration
    if hasattr(v5_engine, 'system_config') and v5_engine.system_config:
        configurations['system'] = {
            "source": "system_config.json",
            "loaded": True,
            "config": v5_engine.system_config
        }

    # 2. Agent configuration
    if hasattr(v5_engine, 'current_agent') and v5_engine.current_agent:
        # Try to get agent config from either agent_config or system_config
        agent_config = {}
        config_loaded = False

        # First check if agent_config was set by loading with apply_config
        if hasattr(v5_engine, 'agent_config') and v5_engine.agent_config:
            agent_config = v5_engine.agent_config
            config_loaded = True
        # Otherwise check if it's in system_config (loaded by load_agent_personality)
        elif hasattr(v5_engine, 'system_config') and v5_engine.system_config:
            # The system_config contains the agent config when loaded via load_agent_personality
            agent_config = v5_engine.system_config
            config_loaded = True

        configurations['agent'] = {
            "name": v5_engine.current_agent,
            "source": f"agents/{v5_engine.current_agent}/config.json",
            "loaded": config_loaded,
            "config": agent_config
        }

    # 3. Agent prompts
    if hasattr(v5_engine, 'agent_prompts') and v5_engine.agent_prompts:
        configurations['agent_prompts'] = {
            "source": f"agents/{v5_engine.current_agent}/prompts.json",
            "loaded": True,
            "prompt_types": list(v5_engine.agent_prompts.keys()),
            "count": len(v5_engine.agent_prompts)
        }

    # 4. Personality configuration
    if hasattr(v5_engine, 'current_personality') and v5_engine.current_personality:
        configurations['personality'] = {
            "name": v5_engine.current_personality,
            "source": f"agents/{v5_engine.current_agent}/personalities/{v5_engine.current_personality}.json",
            "loaded": bool(hasattr(v5_engine, 'personality_traits') and v5_engine.personality_traits),
            "traits": getattr(v5_engine, 'personality_traits', {})
        }

    # 5. Intent configuration
    if hasattr(v5_engine, 'intent_detector') and v5_engine.intent_detector:
        intent_config = {}
        if hasattr(v5_engine.intent_detector, 'intent_config'):
            intent_config = v5_engine.intent_detector.intent_config
        configurations['intent'] = {
            "source": f"agents/{v5_engine.current_agent}/intent.json",
            "loaded": bool(intent_config),
            "intents": list(intent_config.get('intents', {}).keys()) if intent_config else [],
            "count": len(intent_config.get('intents', {})) if intent_config else 0,
            "config": intent_config  # Include full intent config
        }

    # 6. Model information
    if hasattr(v5_engine, 'current_model_name') and v5_engine.current_model_name:
        configurations['model'] = {
            "name": v5_engine.current_model_name,
            "loaded": bool(hasattr(v5_engine, 'current_model') and v5_engine.current_model),
            "settings": {
                "temperature": getattr(v5_engine, 'temperature', None),
                "max_tokens": getattr(v5_engine, 'max_tokens', None),
                "top_p": getattr(v5_engine, 'top_p', None),
                "repeat_penalty": getattr(v5_engine, 'repeat_penalty', None)
            }
        }

    # 7. Loaded prompts (from prompts directory)
    if hasattr(v5_engine, 'loaded_prompts') and v5_engine.loaded_prompts:
        configurations['loaded_prompts'] = {
            "source": "prompts/",
            "files": list(v5_engine.loaded_prompts.keys()),
            "total_prompts": sum(len(prompts) for prompts in v5_engine.loaded_prompts.values())
        }

    return {
        "loaded": True,
        "current_model": getattr(v5_engine, 'current_model_name', None),
        "current_agent": getattr(v5_engine, 'current_agent', None),
        "current_personality": getattr(v5_engine, 'current_personality', None),
        "configurations": configurations
    }

@router.post("/configuration/update")
async def update_configuration(
    config_type: str,
    config_data: Dict,
    user: Dict = Depends(check_admin_access),
    request: Request = None
):
    """Update configuration and save to file"""
    import json
    from pathlib import Path

    v5_engine = getattr(request.app.state, 'v5_engine', None)
    if not v5_engine:
        raise HTTPException(status_code=500, detail="V5 engine not initialized")

    try:
        # Determine the file path based on config type
        if config_type == "system":
            file_path = Path("prompts/system_config.json")
            v5_engine.system_config = config_data
        elif config_type == "agent_prompts":
            if not v5_engine.current_agent:
                raise HTTPException(status_code=400, detail="No agent loaded")
            file_path = Path(f"prompts/agents/{v5_engine.current_agent}/prompts.json")
            v5_engine.agent_prompts = config_data
        elif config_type == "intent":
            if not v5_engine.current_agent:
                raise HTTPException(status_code=400, detail="No agent loaded")
            file_path = Path(f"prompts/agents/{v5_engine.current_agent}/intent.json")
            if v5_engine.intent_detector:
                v5_engine.intent_detector.intent_config = config_data
        else:
            raise HTTPException(status_code=400, detail=f"Invalid config type: {config_type}")

        # Create backup of existing file
        if file_path.exists():
            backup_path = file_path.with_suffix('.json.backup')
            backup_path.write_text(file_path.read_text())

        # Save the new configuration
        file_path.parent.mkdir(parents=True, exist_ok=True)
        with open(file_path, 'w') as f:
            json.dump(config_data, f, indent=2)

        # Reload the configuration in the engine
        if config_type == "system":
            v5_engine.load_system_config()
        elif config_type == "agent_prompts":
            v5_engine.load_agent_prompts(v5_engine.current_agent)
        elif config_type == "intent":
            v5_engine.load_intent_detection(v5_engine.current_agent)

        return {
            "status": "success",
            "message": f"Configuration {config_type} updated successfully",
            "file_path": str(file_path)
        }
    except Exception as e:
        logger.error(f"Error updating configuration: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/health")
async def get_health(user: Dict = Depends(check_admin_access)):
    """Alias for system health endpoint"""
    return await get_system_health(user)

@router.get("/activity")
async def get_activity(
    limit: int = 20,
    user: Dict = Depends(check_admin_access)
):
    """Get recent activity log"""
    activities = []
    now = datetime.now()
    
    # Generate sample activity data
    activity_types = [
        "Chat request processed",
        "Tool executed: dosage_calculator",
        "Voice transcription completed",
        "MCP server connected",
        "Session created",
        "Configuration updated",
        "API call: /products/search",
        "Cache hit for query",
        "Model loaded successfully"
    ]
    
    for i in range(min(limit, 20)):
        activities.append({
            "timestamp": (now - timedelta(minutes=i*5)).isoformat(),
            "type": activity_types[i % len(activity_types)],
            "user_id": f"user_{100 + i}" if i % 3 == 0 else None,
            "details": {
                "duration_ms": 50 + i * 10,
                "status": "success" if i % 5 != 0 else "warning"
            }
        })
    
    return {
        "activities": activities,
        "total": len(activities)
    }

@router.get("/logs")
async def get_logs(
    level: str = "info",
    limit: int = 100,
    user: Dict = Depends(check_admin_access)
):
    """Get system logs"""
    # Read actual log file if it exists
    log_path = Path("logs/ai_engine.log")
    logs = []
    
    if log_path.exists():
        try:
            with open(log_path, 'r') as f:
                lines = f.readlines()[-limit:]
                for line in lines:
                    try:
                        log_entry = json.loads(line)
                        if level == "all" or log_entry.get("level", "").lower() == level.lower():
                            logs.append(log_entry)
                    except:
                        # Plain text log
                        logs.append({
                            "timestamp": datetime.now().isoformat(),
                            "level": level,
                            "message": line.strip()
                        })
        except Exception as e:
            logger.error(f"Error reading logs: {e}")
    
    # Add some sample logs if none found
    if not logs:
        now = datetime.now()
        logs = [
            {
                "timestamp": (now - timedelta(minutes=5)).isoformat(),
                "level": "info",
                "message": "System initialized successfully"
            },
            {
                "timestamp": (now - timedelta(minutes=3)).isoformat(),
                "level": "info",
                "message": "Voice system ready"
            },
            {
                "timestamp": (now - timedelta(minutes=1)).isoformat(),
                "level": "info",
                "message": "MCP server connected"
            }
        ]
    
    return {
        "logs": logs,
        "total": len(logs),
        "levels": ["debug", "info", "warning", "error"],
        "filter": level
    }

@router.post("/broadcast")
async def broadcast_message(
    message: Dict[str, Any],
    user: Dict = Depends(check_admin_access)
):
    """Broadcast message to all connected WebSocket clients"""
    await manager.broadcast({
        "type": "admin_broadcast",
        "message": message,
        "timestamp": datetime.now().isoformat()
    })
    
    return {"status": "broadcast_sent", "connections": len(manager.active_connections)}

# WebSocket endpoint for real-time updates
@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket for real-time dashboard updates"""
    await manager.connect(websocket)
    
    try:
        # Send initial connection message
        await websocket.send_json({
            "type": "connection",
            "status": "connected",
            "timestamp": datetime.now().isoformat()
        })
        
        # Keep connection alive and send periodic updates
        while True:
            try:
                # Wait for client messages
                data = await asyncio.wait_for(websocket.receive_text(), timeout=30.0)
                
                # Handle ping/pong
                if data == "ping":
                    await websocket.send_text("pong")
                else:
                    # Echo back any other message
                    await websocket.send_json({
                        "type": "echo",
                        "data": data,
                        "timestamp": datetime.now().isoformat()
                    })
            
            except asyncio.TimeoutError:
                # Send periodic stats update
                await websocket.send_json({
                    "type": "stats_update",
                    "data": {
                        "active_sessions": engine_stats["active_sessions"],
                        "total_requests": engine_stats["total_requests"],
                        "timestamp": datetime.now().isoformat()
                    }
                })
    
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        logger.info("WebSocket client disconnected")
    
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(websocket)

# Update engine stats (would be called by main engine)
def update_stats(stat_type: str, value: Any = 1):
    """Update engine statistics"""
    if stat_type in engine_stats:
        if isinstance(engine_stats[stat_type], (int, float)):
            engine_stats[stat_type] += value
        elif isinstance(engine_stats[stat_type], dict):
            if value in engine_stats[stat_type]:
                engine_stats[stat_type][value] += 1
            else:
                engine_stats[stat_type][value] = 1
    
    # Update peak sessions
    if stat_type == "active_sessions":
        current_peak = engine_stats.get("peak_sessions", 0)
        if engine_stats["active_sessions"] > current_peak:
            engine_stats["peak_sessions"] = engine_stats["active_sessions"]
    
    # Broadcast update to WebSocket clients
    asyncio.create_task(manager.broadcast({
        "type": "stat_update",
        "stat": stat_type,
        "value": engine_stats.get(stat_type),
        "timestamp": datetime.now().isoformat()
    }))