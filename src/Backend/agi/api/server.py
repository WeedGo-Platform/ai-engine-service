"""
AGI API Server
Serves the AGI system on port 5024 at /api/agi/*
"""

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
import asyncio
import logging
import json
import uuid
from datetime import datetime, timedelta

from agi.orchestrator import get_orchestrator
from agi.core.interfaces import ConversationContext, Message, MessageRole
from agi.models.registry import get_model_registry
from agi.config.agi_config import get_config
from agi.core.database import get_db_manager
from agi.tools import get_tool_registry
from agi.analytics import get_metrics_collector, get_conversation_analyzer, get_insights_generator
from agi.prompts import get_persona_manager, get_template_engine

# Import dashboard routes
try:
    from agi.api.dashboard_routes import router as dashboard_router
    DASHBOARD_AVAILABLE = True
except ImportError:
    DASHBOARD_AVAILABLE = False
    logger.warning("Dashboard routes not available")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="AGI System API",
    description="General Purpose AI Platform API",
    version="1.0.0",
    docs_url="/api/agi/docs",
    redoc_url="/api/agi/redoc",
    openapi_url="/api/agi/openapi.json"
)

# Configure CORS
config = get_config()
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.api.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include dashboard router if available
if DASHBOARD_AVAILABLE:
    app.include_router(dashboard_router)
    logger.info("Dashboard routes registered successfully")

# Request/Response Models
class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None
    tenant_id: Optional[str] = None
    user_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    stream: bool = False

class ChatResponse(BaseModel):
    response: str
    session_id: str
    metadata: Optional[Dict[str, Any]] = None

class ModelInfo(BaseModel):
    id: str
    name: str
    size: str
    context_length: int
    loaded: bool
    capabilities: List[str]

class ToolInfo(BaseModel):
    """Tool information response"""
    name: str
    description: str
    parameters: Dict[str, Any]
    examples: Optional[List[str]] = None

class ToolExecuteRequest(BaseModel):
    """Request for tool execution"""
    tool_name: str
    parameters: Dict[str, Any]

class SessionInfo(BaseModel):
    session_id: str
    tenant_id: Optional[str]
    user_id: Optional[str]
    created_at: str
    message_count: int

# Active sessions
active_sessions: Dict[str, ConversationContext] = {}

@app.on_event("startup")
async def startup_event():
    """Initialize AGI system on startup"""
    try:
        logger.info("Starting AGI API Server on port 5024...")

        # Initialize orchestrator
        orchestrator = await get_orchestrator()

        # Initialize model registry
        registry = await get_model_registry()

        # Initialize database
        db = await get_db_manager()

        logger.info("AGI API Server initialized successfully")

    except Exception as e:
        logger.error(f"Failed to initialize AGI API Server: {e}")
        raise

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    try:
        db = await get_db_manager()
        await db.close()
        logger.info("AGI API Server shut down cleanly")
    except Exception as e:
        logger.error(f"Error during shutdown: {e}")

# Health Check
@app.get("/api/agi/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0"
    }

# Chat Endpoint
@app.post("/api/agi/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Process a chat request

    Args:
        request: Chat request with message and context

    Returns:
        Chat response
    """
    try:
        # Get or create session
        session_id = request.session_id or str(uuid.uuid4())

        # Get or create conversation context
        if session_id in active_sessions:
            context = active_sessions[session_id]
        else:
            # Create new session in database
            db = await get_db_manager()
            if not request.session_id:
                session_id = await db.create_session(
                    tenant_id=request.tenant_id,
                    user_id=request.user_id,
                    metadata=request.metadata
                )

            # Create conversation context
            context = ConversationContext(
                messages=[],
                session_id=session_id,
                tenant_id=request.tenant_id,
                user_id=request.user_id,
                metadata=request.metadata or {}
            )
            active_sessions[session_id] = context

        # Get orchestrator
        orchestrator = await get_orchestrator()

        # Process request
        if request.stream:
            # Return streaming response
            return StreamingResponse(
                stream_response(orchestrator, request.message, context),
                media_type="text/event-stream"
            )
        else:
            # Get regular response
            response = await orchestrator.process_request(
                request=request.message,
                context=context,
                stream=False
            )

            return ChatResponse(
                response=response,
                session_id=session_id,
                metadata={"model_used": "auto-selected"}
            )

    except Exception as e:
        logger.error(f"Chat request failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

async def stream_response(orchestrator, message: str, context: ConversationContext):
    """Stream response generator"""
    try:
        result = await orchestrator.process_request(
            request=message,
            context=context,
            stream=True
        )

        # If result is an async generator, iterate over it
        if hasattr(result, '__aiter__'):
            async for chunk in result:
                yield f"data: {json.dumps({'chunk': chunk})}\n\n"
        else:
            # If result is a regular string, yield it as one chunk
            yield f"data: {json.dumps({'chunk': result})}\n\n"
    except Exception as e:
        yield f"data: {json.dumps({'error': str(e)})}\n\n"

# WebSocket Endpoint for Real-time Chat
@app.websocket("/api/agi/ws/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    """
    WebSocket endpoint for real-time chat

    Args:
        websocket: WebSocket connection
        session_id: Session ID
    """
    await websocket.accept()

    try:
        # Get or create conversation context
        if session_id in active_sessions:
            context = active_sessions[session_id]
        else:
            db = await get_db_manager()

            # Create conversation context
            context = ConversationContext(
                messages=[],
                session_id=session_id,
                tenant_id=None,
                user_id=None,
                metadata={}
            )
            active_sessions[session_id] = context

        # Get orchestrator
        orchestrator = await get_orchestrator()

        while True:
            # Receive message
            data = await websocket.receive_text()
            message = json.loads(data)

            # Process message
            if message.get("type") == "chat":
                user_message = message.get("message", "")

                # Stream response
                async for chunk in orchestrator.process_request(
                    request=user_message,
                    context=context,
                    stream=True
                ):
                    await websocket.send_json({
                        "type": "response",
                        "chunk": chunk
                    })

                # Send completion marker
                await websocket.send_json({
                    "type": "response_complete"
                })

            elif message.get("type") == "ping":
                await websocket.send_json({"type": "pong"})

    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for session {session_id}")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        await websocket.close()

# Model Management Endpoints
@app.get("/api/agi/models", response_model=List[ModelInfo])
async def list_models():
    """List available models"""
    try:
        registry = await get_model_registry()
        models = await registry.list_models()
        stats = await registry.get_registry_stats()

        model_list = []
        for model_id in models:
            model_data = stats["models"].get(model_id, {})
            model_list.append(ModelInfo(
                id=model_id,
                name=model_data.get("name", model_id),
                size=model_data.get("size", "unknown"),
                context_length=8192,  # Default
                loaded=model_data.get("loaded", False),
                capabilities=["chat", "streaming"]
            ))

        return model_list

    except Exception as e:
        logger.error(f"Failed to list models: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/agi/models/{model_id}/load")
async def load_model(model_id: str):
    """Load a specific model"""
    try:
        registry = await get_model_registry()
        model = await registry.get_model(model_id)

        if model:
            return {"status": "loaded", "model_id": model_id}
        else:
            raise HTTPException(status_code=404, detail="Model not found")

    except Exception as e:
        logger.error(f"Failed to load model: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/agi/models/{model_id}/unload")
async def unload_model(model_id: str):
    """Unload a specific model"""
    try:
        registry = await get_model_registry()
        await registry.unregister_model(model_id)
        return {"status": "unloaded", "model_id": model_id}

    except Exception as e:
        logger.error(f"Failed to unload model: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Session Management Endpoints
@app.get("/api/agi/sessions", response_model=List[SessionInfo])
async def list_sessions():
    """List active sessions"""
    sessions = []
    for session_id, context in active_sessions.items():
        sessions.append(SessionInfo(
            session_id=session_id,
            tenant_id=context.tenant_id,
            user_id=context.user_id,
            created_at=datetime.utcnow().isoformat(),
            message_count=len(context.messages)
        ))

    return sessions

@app.get("/api/agi/sessions/{session_id}/history")
async def get_session_history(session_id: str, limit: int = 10):
    """Get conversation history for a session"""
    try:
        db = await get_db_manager()
        history = await db.get_conversation_history(session_id, limit)
        return {"session_id": session_id, "history": history}

    except Exception as e:
        logger.error(f"Failed to get session history: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/agi/sessions/{session_id}")
async def delete_session(session_id: str):
    """Delete a session"""
    if session_id in active_sessions:
        del active_sessions[session_id]
        return {"status": "deleted", "session_id": session_id}
    else:
        raise HTTPException(status_code=404, detail="Session not found")

# Tool Management Endpoints
@app.get("/api/agi/tools", response_model=List[ToolInfo])
async def list_tools():
    """List available tools"""
    try:
        registry = await get_tool_registry()
        tools = registry.list_tools()

        tool_list = []
        for tool_def in tools:
            tool_list.append(ToolInfo(
                name=tool_def.name,
                description=tool_def.description,
                parameters=tool_def.parameters,
                examples=tool_def.examples
            ))

        return tool_list

    except Exception as e:
        logger.error(f"Failed to list tools: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/agi/tools/execute")
async def execute_tool(request: ToolExecuteRequest):
    """Execute a specific tool"""
    try:
        registry = await get_tool_registry()
        tool = registry.get_tool(request.tool_name)

        if not tool:
            raise HTTPException(status_code=404, detail=f"Tool {request.tool_name} not found")

        # Execute the tool
        result = await tool.execute(**request.parameters)

        return {
            "tool": request.tool_name,
            "success": result.success,
            "result": result.result,
            "error": result.error
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to execute tool: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/agi/tools/{tool_name}")
async def get_tool_details(tool_name: str):
    """Get details of a specific tool"""
    try:
        registry = await get_tool_registry()
        tool = registry.get_tool(tool_name)

        if not tool:
            raise HTTPException(status_code=404, detail=f"Tool {tool_name} not found")

        definition = tool.get_definition()
        return {
            "name": definition.name,
            "description": definition.description,
            "parameters": definition.parameters,
            "examples": definition.examples
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get tool details: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Statistics Endpoint
@app.get("/api/agi/stats")
async def get_stats():
    """Get system statistics"""
    try:
        model_registry = await get_model_registry()
        tool_registry = await get_tool_registry()
        registry_stats = await model_registry.get_registry_stats()

        # Count tools
        tools = tool_registry.list_tools()

        return {
            "sessions": {
                "active": len(active_sessions),
                "total_messages": sum(len(ctx.messages) for ctx in active_sessions.values())
            },
            "models": registry_stats,
            "tools": {
                "count": len(tools),
                "available": [t.name for t in tools]
            },
            "timestamp": datetime.utcnow().isoformat()
        }

    except Exception as e:
        logger.error(f"Failed to get stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Analytics Endpoints
@app.get("/api/agi/analytics/metrics")
async def get_metrics(
    metric_type: Optional[str] = None,
    session_id: Optional[str] = None,
    hours: int = 24
):
    """Get system metrics"""
    try:
        metrics_collector = await get_metrics_collector()
        from agi.analytics.metrics import MetricType

        # Get metrics for time window
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(hours=hours)

        # Convert metric_type string to enum if provided
        metric_enum = None
        if metric_type:
            try:
                metric_enum = MetricType(metric_type)
            except ValueError:
                raise HTTPException(status_code=400, detail=f"Invalid metric type: {metric_type}")

        metrics = await metrics_collector.get_metrics(
            metric_type=metric_enum,
            session_id=session_id,
            start_time=start_time,
            end_time=end_time
        )

        return {
            "metrics": [m.to_dict() for m in metrics],
            "time_window": {
                "start": start_time.isoformat(),
                "end": end_time.isoformat(),
                "hours": hours
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/agi/analytics/session/{session_id}")
async def get_session_analytics(session_id: str):
    """Get analytics for a specific session"""
    try:
        metrics_collector = await get_metrics_collector()
        analyzer = await get_conversation_analyzer()

        # Get session summary
        session_summary = await metrics_collector.get_session_summary(session_id)

        # Get conversation analysis if available
        analysis = None
        if session_id in active_sessions:
            context = active_sessions[session_id]
            analysis = await analyzer.analyze_conversation(context)

        return {
            "session_id": session_id,
            "summary": session_summary,
            "analysis": analysis.to_dict() if analysis else None
        }
    except Exception as e:
        logger.error(f"Failed to get session analytics: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/agi/analytics/insights")
async def get_insights(hours: int = 24):
    """Get system insights"""
    try:
        insights_gen = await get_insights_generator()

        # Generate insights
        insights = await insights_gen.generate_insights(time_window_hours=hours)

        return {
            "insights": [i.to_dict() for i in insights],
            "generated_at": datetime.utcnow().isoformat(),
            "time_window_hours": hours
        }
    except Exception as e:
        logger.error(f"Failed to generate insights: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/agi/analytics/system-stats")
async def get_system_stats(hours: int = 24):
    """Get overall system statistics"""
    try:
        metrics_collector = await get_metrics_collector()
        stats = await metrics_collector.get_system_stats(time_window_hours=hours)

        return stats
    except Exception as e:
        logger.error(f"Failed to get system stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Persona Management Endpoints
@app.get("/api/agi/personas")
async def list_personas():
    """List all available personas"""
    try:
        persona_manager = await get_persona_manager()
        personas = await persona_manager.list_personas()

        return {
            "personas": [p.to_dict() for p in personas],
            "count": len(personas)
        }
    except Exception as e:
        logger.error(f"Failed to list personas: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/agi/personas/{persona_name}")
async def get_persona(persona_name: str):
    """Get details of a specific persona"""
    try:
        persona_manager = await get_persona_manager()
        persona = await persona_manager.get_persona(persona_name)

        if not persona:
            raise HTTPException(status_code=404, detail=f"Persona {persona_name} not found")

        return persona.to_dict()
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get persona: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/agi/personas")
async def create_persona(request: dict):
    """Create a new persona"""
    try:
        persona_manager = await get_persona_manager()

        # Create persona from request
        from agi.prompts.persona_manager import Persona
        persona = Persona(
            name=request["name"],
            role=request["role"],
            system_prompt=request["system_prompt"],
            characteristics=request.get("characteristics", {}),
            language_style=request.get("language_style", {}),
            constraints=request.get("constraints", []),
            examples=request.get("examples", [])
        )

        saved = await persona_manager.save_persona(persona)
        return saved.to_dict()
    except Exception as e:
        logger.error(f"Failed to create persona: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/agi/personas/{persona_name}")
async def delete_persona(persona_name: str):
    """Delete a persona"""
    try:
        persona_manager = await get_persona_manager()
        success = await persona_manager.delete_persona(persona_name)

        if not success:
            raise HTTPException(status_code=404, detail=f"Persona {persona_name} not found")

        return {"message": f"Persona {persona_name} deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete persona: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Template Management Endpoints
@app.get("/api/agi/templates")
async def list_templates():
    """List all available templates"""
    try:
        template_engine = await get_template_engine()
        templates = await template_engine.list_templates()

        return {
            "templates": [t.to_dict() for t in templates],
            "count": len(templates)
        }
    except Exception as e:
        logger.error(f"Failed to list templates: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/agi/templates/{template_name}")
async def get_template(template_name: str):
    """Get details of a specific template"""
    try:
        template_engine = await get_template_engine()
        template = await template_engine.get_template(template_name)

        if not template:
            raise HTTPException(status_code=404, detail=f"Template {template_name} not found")

        return template.to_dict()
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get template: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/agi/templates")
async def create_template(request: dict):
    """Create a new template"""
    try:
        template_engine = await get_template_engine()

        # Create template from request
        from agi.prompts.template_engine import PromptTemplate
        template = PromptTemplate(
            name=request["name"],
            template=request["template"],
            description=request.get("description", ""),
            variables=request.get("variables", []),
            metadata=request.get("metadata", {})
        )

        saved = await template_engine.save_template(template)
        return saved.to_dict()
    except Exception as e:
        logger.error(f"Failed to create template: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/agi/templates/{template_name}/render")
async def render_template(template_name: str, variables: dict):
    """Render a template with given variables"""
    try:
        template_engine = await get_template_engine()
        rendered = await template_engine.render(template_name, variables)

        return {
            "template": template_name,
            "rendered": rendered,
            "variables": variables
        }
    except Exception as e:
        logger.error(f"Failed to render template: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/agi/templates/{template_name}")
async def delete_template(template_name: str):
    """Delete a template"""
    try:
        template_engine = await get_template_engine()
        success = await template_engine.delete_template(template_name)

        if not success:
            raise HTTPException(status_code=404, detail=f"Template {template_name} not found")

        return {"message": f"Template {template_name} deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete template: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Admin Endpoints
@app.post("/api/agi/admin/reload-models")
async def reload_models():
    """Reload model registry"""
    try:
        model_registry = await get_model_registry()

        # Reinitialize the registry
        await model_registry.initialize()

        # Get updated stats
        stats = await model_registry.get_registry_stats()

        return {
            "message": "Models reloaded successfully",
            "stats": stats
        }
    except Exception as e:
        logger.error(f"Failed to reload models: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/agi/admin/reload-tools")
async def reload_tools():
    """Reload tool registry"""
    try:
        tool_registry = await get_tool_registry()

        # Re-register tools
        await tool_registry.initialize()

        # Get updated list
        tools = tool_registry.list_tools()

        return {
            "message": "Tools reloaded successfully",
            "tools": [t.name for t in tools],
            "count": len(tools)
        }
    except Exception as e:
        logger.error(f"Failed to reload tools: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/agi/admin/database-stats")
async def get_database_stats():
    """Get database statistics"""
    try:
        db_manager = await get_db_manager()
        conn = await db_manager.get_connection()

        try:
            # Get table sizes
            query = """
            SELECT
                schemaname,
                tablename,
                pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size,
                n_tup_ins AS inserts,
                n_tup_upd AS updates,
                n_tup_del AS deletes
            FROM pg_stat_user_tables
            WHERE schemaname = 'agi'
            ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC
            """

            tables = await conn.fetch(query)

            # Get connection stats
            conn_query = """
            SELECT
                count(*) as total_connections,
                sum(CASE WHEN state = 'active' THEN 1 ELSE 0 END) as active_connections,
                sum(CASE WHEN state = 'idle' THEN 1 ELSE 0 END) as idle_connections
            FROM pg_stat_activity
            WHERE datname = current_database()
            """

            conn_stats = await conn.fetchrow(conn_query)

            return {
                "tables": [dict(row) for row in tables],
                "connections": dict(conn_stats)
            }
        finally:
            await db_manager.release_connection(conn)
    except Exception as e:
        logger.error(f"Failed to get database stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/agi/admin/flush-metrics")
async def flush_metrics():
    """Force flush of metrics buffer"""
    try:
        metrics_collector = await get_metrics_collector()
        await metrics_collector.flush()

        return {"message": "Metrics buffer flushed successfully"}
    except Exception as e:
        logger.error(f"Failed to flush metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/agi/admin/clear-sessions")
async def clear_sessions():
    """Clear all active sessions"""
    try:
        count = len(active_sessions)
        active_sessions.clear()

        return {
            "message": f"Cleared {count} active sessions",
            "cleared_count": count
        }
    except Exception as e:
        logger.error(f"Failed to clear sessions: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/agi/admin/config")
async def get_config_details():
    """Get current configuration"""
    try:
        config = get_config()

        # Return safe config without sensitive data
        safe_config = {
            "environment": config.environment,
            "database": {
                "host": config.database.host,
                "port": config.database.port,
                "database": config.database.database,
                "pool_size": config.database.pool_size
            },
            "services": {
                "enable_rag": config.services.enable_rag,
                "enable_memory": config.services.enable_memory,
                "enable_tools": config.services.enable_tools,
                "enable_analytics": config.services.enable_analytics
            },
            "models": {
                "default_model": config.models.default_model,
                "fallback_model": config.models.fallback_model,
                "temperature": config.models.temperature,
                "max_tokens": config.models.max_tokens
            },
            "rag": {
                "chunk_size": config.rag.chunk_size,
                "chunk_overlap": config.rag.chunk_overlap,
                "top_k": config.rag.top_k
            }
        }

        return safe_config
    except Exception as e:
        logger.error(f"Failed to get config: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/agi/admin/health")
async def health_check():
    """Comprehensive health check"""
    try:
        health = {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "components": {}
        }

        # Check database
        try:
            db_manager = await get_db_manager()
            conn = await db_manager.get_connection()
            await conn.fetchval("SELECT 1")
            await db_manager.release_connection(conn)
            health["components"]["database"] = "healthy"
        except Exception as e:
            health["components"]["database"] = f"unhealthy: {str(e)}"
            health["status"] = "degraded"

        # Check model registry
        try:
            model_registry = await get_model_registry()
            stats = await model_registry.get_registry_stats()
            if stats["total_models"] > 0:
                health["components"]["models"] = "healthy"
            else:
                health["components"]["models"] = "warning: no models loaded"
                health["status"] = "degraded"
        except Exception as e:
            health["components"]["models"] = f"unhealthy: {str(e)}"
            health["status"] = "degraded"

        # Check tool registry
        try:
            tool_registry = await get_tool_registry()
            tools = tool_registry.list_tools()
            if len(tools) > 0:
                health["components"]["tools"] = "healthy"
            else:
                health["components"]["tools"] = "warning: no tools loaded"
                health["status"] = "degraded"
        except Exception as e:
            health["components"]["tools"] = f"unhealthy: {str(e)}"
            health["status"] = "degraded"

        # Check orchestrator
        try:
            orchestrator = await get_orchestrator()
            if orchestrator:
                health["components"]["orchestrator"] = "healthy"
            else:
                health["components"]["orchestrator"] = "unhealthy: not initialized"
                health["status"] = "degraded"
        except Exception as e:
            health["components"]["orchestrator"] = f"unhealthy: {str(e)}"
            health["status"] = "degraded"

        return health
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }

# Main entry point for running the server
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=5024,
        log_level="info",
        access_log=True
    )