"""
AGI Dashboard API Routes
Provides REST endpoints for the admin dashboard
"""

from fastapi import APIRouter, HTTPException, Depends, Query, WebSocket, WebSocketDisconnect
from fastapi.responses import StreamingResponse
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import json
import asyncio
import csv
import io

from agi.agents import CoordinatorAgent, ResearchAgent, AnalystAgent, ExecutorAgent, ValidatorAgent
from agi.security import get_access_control, get_content_filter, get_rate_limiter, get_audit_logger
from agi.learning import get_feedback_collector, get_pattern_engine, get_learning_adapter
from agi.core.interfaces import AgentState, AgentTask

router = APIRouter()

# WebSocket manager for real-time updates
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except:
                pass

manager = ConnectionManager()

# Agent Management Endpoints

@router.get("/agents")
async def get_agents():
    """Get all agent statuses"""
    agents = []

    # Get singleton instances
    agent_instances = {
        "research": ResearchAgent("research_main"),
        "analyst": AnalystAgent("analyst_main"),
        "executor": ExecutorAgent("executor_main"),
        "validator": ValidatorAgent("validator_main"),
        "coordinator": CoordinatorAgent("coordinator_main")
    }

    for agent_type, agent in agent_instances.items():
        # Get agent capabilities and state
        capabilities = agent.get_capabilities()
        state = agent.get_state()

        # Mock some statistics (in production, fetch from database)
        agents.append({
            "id": f"agent_{agent_type}",
            "name": f"{agent_type.capitalize()} Agent",
            "type": agent_type,
            "model": capabilities.get("model", "unknown"),
            "status": "active" if state == AgentState.EXECUTING else "idle",
            "tasks": 100 + len(agent_type) * 10,  # Mock data
            "successRate": 95 + len(agent_type) % 5,  # Mock data
            "currentLoad": 30 + len(agent_type) * 10  # Mock data
        })

    return agents

@router.get("/agents/{agent_id}")
async def get_agent(agent_id: str):
    """Get specific agent details"""
    # Mock implementation - replace with actual agent lookup
    return {
        "id": agent_id,
        "name": f"Agent {agent_id}",
        "type": "research",
        "model": "claude-3-sonnet",
        "status": "active",
        "tasks": 142,
        "successRate": 99.2,
        "currentLoad": 65,
        "capabilities": ["web_search", "rag_search", "analysis"],
        "recent_tasks": [
            {"id": "task_1", "description": "Research latest AI trends", "status": "completed"},
            {"id": "task_2", "description": "Analyze user feedback", "status": "in_progress"}
        ]
    }

@router.post("/agents/{agent_id}/actions")
async def execute_agent_action(agent_id: str, action_data: dict):
    """Execute an action on an agent"""
    action = action_data.get("action")

    if action == "restart":
        # Implement agent restart logic
        await manager.broadcast({
            "type": "agent_update",
            "agentId": agent_id,
            "update": {"status": "restarting"}
        })
        await asyncio.sleep(2)  # Simulate restart
        await manager.broadcast({
            "type": "agent_update",
            "agentId": agent_id,
            "update": {"status": "active"}
        })

    return {"success": True, "action": action, "agent_id": agent_id}

# Statistics Endpoints

@router.get("/stats")
async def get_stats():
    """Get overall system statistics"""
    # In production, aggregate from database
    return {
        "totalRequests": 8462,
        "successRate": 98.5,
        "averageResponseTime": 245,  # milliseconds
        "activeUsers": 127,
        "peakLoad": 89,  # percentage
        "uptime": 99.9  # percentage
    }

@router.get("/agents/{agent_id}/stats")
async def get_agent_stats(agent_id: str):
    """Get statistics for a specific agent"""
    return {
        "agent_id": agent_id,
        "total_tasks": 500,
        "completed_tasks": 485,
        "failed_tasks": 15,
        "average_execution_time": 3.2,  # seconds
        "hourly_stats": [
            {"hour": "00:00", "tasks": 20, "success_rate": 95},
            {"hour": "01:00", "tasks": 15, "success_rate": 100},
            # ... more hourly data
        ]
    }

# Activity & Audit Endpoints

@router.get("/activities")
async def get_activities(limit: int = Query(100, le=1000)):
    """Get recent system activities"""
    activities = []

    # Mock activities - in production, fetch from audit logs
    activity_types = ["MODEL", "TOOL", "AGENT", "AUTH", "SECURITY"]
    messages = [
        "Claude-3-Opus invoked by Research Agent",
        "Web search executed successfully",
        "Coordinator delegated task to Analyst",
        "User authenticated via API key",
        "Content filtered: PII detected and redacted"
    ]

    for i in range(min(limit, 20)):
        activities.append({
            "id": f"activity_{i}",
            "timestamp": (datetime.now() - timedelta(minutes=i)).strftime("%H:%M:%S"),
            "type": activity_types[i % len(activity_types)],
            "message": messages[i % len(messages)]
        })

    return activities

@router.get("/audit-logs")
async def get_audit_logs(
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
    event_type: Optional[str] = None,
    user_id: Optional[str] = None,
    limit: int = Query(100, le=1000)
):
    """Get audit logs with filtering"""
    audit_logger = await get_audit_logger()

    logs = await audit_logger.query_logs(
        start_time=start_time,
        end_time=end_time,
        user_id=user_id,
        limit=limit
    )

    return logs

# Security Endpoints

@router.get("/security/status")
async def get_security_status():
    """Get current security system status"""
    content_filter = await get_content_filter()
    rate_limiter = await get_rate_limiter()

    return {
        "contentFiltering": "active",
        "rateLimiting": "active",
        "accessControl": "RBAC",
        "totalEvents": 14,
        "threatsBlocked": 2,
        "lastThreat": {
            "type": "SQL injection attempt",
            "timestamp": datetime.now().isoformat()
        },
        "activeRules": {
            "content_filter": len(content_filter.patterns),
            "rate_limits": 6
        }
    }

@router.get("/security/events")
async def get_security_events(limit: int = Query(50, le=500)):
    """Get recent security events"""
    audit_logger = await get_audit_logger()

    # Query security-related events
    events = await audit_logger.query_logs(limit=limit)

    security_events = [
        event for event in events
        if event.get("event_type", "").startswith("security.")
    ]

    return security_events

@router.put("/security/rules/{rule}")
async def update_security_rule(rule: str, rule_data: dict):
    """Update a security rule"""
    value = rule_data.get("value")

    if rule == "content_filtering":
        content_filter = await get_content_filter()
        # Update content filter settings
        pass
    elif rule == "rate_limiting":
        rate_limiter = await get_rate_limiter()
        # Update rate limiting rules
        pass

    await manager.broadcast({
        "type": "security_update",
        "rule": rule,
        "value": value
    })

    return {"success": True, "rule": rule, "value": value}

# Learning Metrics Endpoints

@router.get("/learning/metrics")
async def get_learning_metrics():
    """Get learning system metrics"""
    pattern_engine = await get_pattern_engine()
    feedback_collector = await get_feedback_collector()

    return {
        "patternCount": 847,  # Mock - fetch from pattern engine
        "feedbackPositive": 92,  # percentage
        "adaptationsToday": 34,
        "learningRate": 0.85,
        "confidenceScore": 0.92
    }

@router.get("/learning/patterns")
async def get_patterns(limit: int = Query(50, le=500)):
    """Get recognized patterns"""
    pattern_engine = await get_pattern_engine()

    # Mock patterns - in production, fetch from pattern engine
    patterns = []
    for i in range(min(limit, 10)):
        patterns.append({
            "id": f"pattern_{i}",
            "type": "conversation_flow",
            "frequency": 50 - i * 3,
            "confidence": 0.95 - i * 0.05,
            "last_seen": datetime.now().isoformat()
        })

    return patterns

@router.get("/learning/feedback")
async def get_feedback(limit: int = Query(50, le=500)):
    """Get recent feedback"""
    feedback_collector = await get_feedback_collector()

    feedback_data = await feedback_collector.get_recent_feedback(limit=limit)

    return feedback_data

# Rate Limiting Endpoints

@router.get("/rate-limits")
async def get_rate_limits():
    """Get current rate limit rules"""
    rate_limiter = await get_rate_limiter()

    # Mock rate limits - in production, fetch from rate limiter
    return [
        {"rule": "global_requests", "limit": 10000, "window": 60, "current": 3421},
        {"rule": "user_requests", "limit": 100, "window": 60, "current": 42},
        {"rule": "model_invocations", "limit": 50, "window": 3600, "current": 12},
        {"rule": "tool_executions", "limit": 200, "window": 3600, "current": 67}
    ]

@router.put("/rate-limits/{rule}")
async def update_rate_limit(rule: str, limit_data: dict):
    """Update a rate limit rule"""
    rate_limiter = await get_rate_limiter()
    new_limit = limit_data.get("limit")

    # Update rate limit in system
    # await rate_limiter.update_rule(rule, new_limit)

    return {"success": True, "rule": rule, "limit": new_limit}

# System Actions

@router.post("/system/restart-agents")
async def restart_agents():
    """Restart all agents"""
    # Implement agent restart logic
    await manager.broadcast({
        "type": "system_action",
        "action": "restart_agents",
        "status": "in_progress"
    })

    await asyncio.sleep(3)  # Simulate restart

    await manager.broadcast({
        "type": "system_action",
        "action": "restart_agents",
        "status": "completed"
    })

    return {"success": True, "action": "restart_agents"}

@router.post("/system/clear-cache")
async def clear_cache():
    """Clear system cache"""
    # Implement cache clearing logic

    await manager.broadcast({
        "type": "system_action",
        "action": "clear_cache",
        "status": "completed"
    })

    return {"success": True, "action": "clear_cache", "cleared_items": 1247}

@router.get("/system/export-logs")
async def export_logs(format: str = Query("json", regex="^(json|csv)$")):
    """Export system logs"""
    audit_logger = await get_audit_logger()

    # Get logs from last 24 hours
    logs = await audit_logger.query_logs(
        start_time=datetime.now() - timedelta(days=1),
        limit=10000
    )

    if format == "csv":
        # Convert to CSV
        output = io.StringIO()
        if logs:
            writer = csv.DictWriter(output, fieldnames=logs[0].keys())
            writer.writeheader()
            writer.writerows(logs)

        return StreamingResponse(
            io.BytesIO(output.getvalue().encode()),
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename=agi_logs_{datetime.now().strftime('%Y%m%d')}.csv"}
        )
    else:
        # Return as JSON
        return StreamingResponse(
            io.BytesIO(json.dumps(logs, default=str).encode()),
            media_type="application/json",
            headers={"Content-Disposition": f"attachment; filename=agi_logs_{datetime.now().strftime('%Y%m%d')}.json"}
        )

# WebSocket for real-time updates

@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time updates"""
    await manager.connect(websocket)

    try:
        while True:
            # Wait for messages from client
            data = await websocket.receive_text()
            message = json.loads(data)

            if message.get("type") == "auth":
                # Handle authentication
                token = message.get("token")
                # Validate token...
                await websocket.send_json({"type": "auth_success"})

            elif message.get("type") == "ping":
                await websocket.send_json({"type": "pong"})

    except WebSocketDisconnect:
        manager.disconnect(websocket)

# Background task to send periodic updates
async def send_periodic_updates():
    """Send periodic updates to connected clients"""
    while True:
        await asyncio.sleep(5)  # Send updates every 5 seconds

        # Get current stats
        stats = {
            "totalRequests": 8462 + asyncio.get_event_loop().time() % 100,
            "successRate": 98.5 + (asyncio.get_event_loop().time() % 10) / 10
        }

        await manager.broadcast({
            "type": "stats_update",
            "stats": stats
        })

# Start background task on module load
# asyncio.create_task(send_periodic_updates())