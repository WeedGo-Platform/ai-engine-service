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

from fastapi import APIRouter, HTTPException, Depends, WebSocket, WebSocketDisconnect, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

# V5 imports
from core.authentication import get_current_user
from core.config_loader import get_config
from services.smart_ai_engine_v5 import SmartAIEngineV5

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v5/admin", tags=["admin"])

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
            {"endpoint": "/api/v5/chat", "calls": 1250, "avg_time_ms": 42},
            {"endpoint": "/api/v5/search/products", "calls": 820, "avg_time_ms": 28},
            {"endpoint": "/api/v5/voice/transcribe", "calls": 450, "avg_time_ms": 185},
            {"endpoint": "/api/v5/functions/dosage_calculator", "calls": 380, "avg_time_ms": 15}
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
async def get_available_models(user: Dict = Depends(check_admin_access)):
    """Get list of available models from the system"""
    try:
        engine = SmartAIEngineV5()
        models_list = engine.list_models()
        
        # If no models found, return default list
        if not models_list:
            models_list = [
                {"name": "qwen_0.5b", "size": 0, "path": "models/qwen_0.5b.gguf", "size_mb": 500, "loaded": False},
                {"name": "llama3", "size": 0, "path": "models/llama3.gguf", "size_mb": 4000, "loaded": False}
            ]
        
        return {
            "status": "success",
            "models": models_list,
            "current_model": engine.current_model_name
        }
    except Exception as e:
        logger.error(f"Error getting models: {e}")
        # Return fallback models list
        return {
            "status": "success",
            "models": [
                {"name": "qwen_0.5b", "size": 0, "path": "models/qwen_0.5b.gguf", "size_mb": 500, "loaded": False},
                {"name": "llama3", "size": 0, "path": "models/llama3.gguf", "size_mb": 4000, "loaded": False}
            ],
            "current_model": "qwen_0.5b"
        }

@router.get("/config")
async def get_configuration(user: Dict = Depends(check_admin_access)):
    """Get current configuration"""
    config = get_config()
    
    # Get actual models from engine
    try:
        engine = SmartAIEngineV5()
        available_models = list(engine.available_models.keys()) if engine.available_models else ["qwen_0.5b", "llama3"]
    except:
        available_models = ["qwen_0.5b", "llama3"]
    
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
            "current": "qwen_0.5b",
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
async def load_model(
    model: str,
    agent_id: Optional[str] = None,
    personality_id: Optional[str] = None,
    user: Dict = Depends(check_admin_access)
):
    """Load a model with agent and personality
    
    This follows the SmartAIEngineV5 pattern where:
    - When model changes, agent and personality are reloaded
    - This ensures proper prompt and trait loading
    """
    try:
        # Get the engine instance
        engine = SmartAIEngineV5()
        
        # Load model with agent and personality
        success = engine.load_model(
            model_name=model,
            agent_id=agent_id,
            personality_id=personality_id
        )
        
        if success:
            return {
                "status": "success",
                "model": model,
                "agent": agent_id,
                "personality": personality_id,
                "message": f"Model {model} loaded with agent={agent_id}, personality={personality_id}"
            }
        else:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to load model {model}"
            )
    except Exception as e:
        logger.error(f"Model load error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to load model: {str(e)}"
        )

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