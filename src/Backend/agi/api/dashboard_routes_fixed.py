"""
AGI Dashboard API Routes - Fixed Version
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
import random

from agi.agents import CoordinatorAgent, ResearchAgent, AnalystAgent, ExecutorAgent, ValidatorAgent
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

# Storage for agent data (in production, use database)
agents_data = {}

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

        # Store agent data for updates
        agent_id = f"agent_{agent_type}"
        if agent_id not in agents_data:
            agents_data[agent_id] = {
                "name": f"{agent_type.capitalize()} Agent",
                "type": agent_type,
                "model": capabilities.get("model", "unknown"),
            }

        # Mock some statistics (in production, fetch from database)
        agents.append({
            "id": agent_id,
            "name": agents_data[agent_id].get("name", f"{agent_type.capitalize()} Agent"),
            "type": agent_type,
            "model": agents_data[agent_id].get("model", capabilities.get("model", "unknown")),
            "status": "active" if state == AgentState.EXECUTING else "idle",
            "tasks": 100 + len(agent_type) * 10,
            "successRate": 95 + len(agent_type) % 5,
            "currentLoad": 30 + len(agent_type) * 10
        })

    return agents

@router.get("/agents/{agent_id}")
async def get_agent(agent_id: str):
    """Get specific agent details"""
    # Check if agent exists
    if agent_id in agents_data:
        agent_info = agents_data[agent_id]
    else:
        agent_info = {
            "name": f"Agent {agent_id}",
            "type": "research",
            "model": "claude-3-sonnet"
        }

    return {
        "id": agent_id,
        "name": agent_info.get("name", f"Agent {agent_id}"),
        "type": agent_info.get("type", "research"),
        "model": agent_info.get("model", "claude-3-sonnet"),
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

@router.put("/agents/{agent_id}")
async def update_agent(agent_id: str, update_data: dict):
    """Update an agent configuration"""
    if agent_id not in agents_data:
        agents_data[agent_id] = {}

    agents_data[agent_id].update(update_data)

    await manager.broadcast({
        "type": "agent_update",
        "agentId": agent_id,
        "update": update_data
    })

    return {"success": True, "agent_id": agent_id, "updated": update_data}

@router.delete("/agents/{agent_id}")
async def delete_agent(agent_id: str):
    """Delete an agent (disable it)"""
    if agent_id in agents_data:
        agents_data[agent_id]["status"] = "disabled"

    await manager.broadcast({
        "type": "agent_deleted",
        "agentId": agent_id
    })

    return {"success": True, "agent_id": agent_id, "message": "Agent disabled"}

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

@router.get("/stats/history")
async def get_stats_history(period: str = Query("24h", regex="^(1h|6h|24h|7d|30d)$")):
    """Get historical statistics"""
    # Mock historical data
    history = []

    if period == "1h":
        points = 12  # 5-minute intervals
    elif period == "6h":
        points = 12  # 30-minute intervals
    elif period == "24h":
        points = 24  # hourly
    elif period == "7d":
        points = 7  # daily
    else:  # 30d
        points = 30  # daily

    base_time = datetime.now()
    for i in range(points):
        history.append({
            "timestamp": (base_time - timedelta(hours=i)).isoformat(),
            "requests": random.randint(500, 1500),
            "success_rate": 95 + random.random() * 5,
            "response_time": 200 + random.randint(0, 100)
        })

    return {
        "period": period,
        "data": history
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
    # Mock audit logs - in production, fetch from database
    logs = []

    for i in range(min(limit, 50)):
        timestamp = datetime.now() - timedelta(minutes=i*5)

        # Apply filters if provided
        if start_time and timestamp < start_time:
            continue
        if end_time and timestamp > end_time:
            continue

        log_entry = {
            "id": f"log_{i}",
            "timestamp": timestamp.isoformat(),
            "user_id": user_id if user_id else f"user_{i % 5}",
            "event_type": event_type if event_type else f"event.type.{i % 3}",
            "description": f"Event {i} occurred",
            "status": "success" if i % 10 != 0 else "failed",
            "metadata": {
                "ip_address": f"192.168.1.{i % 255}",
                "user_agent": "Mozilla/5.0"
            }
        }
        logs.append(log_entry)

    return logs

# Security Endpoints

@router.get("/security/status")
async def get_security_status():
    """Get current security system status"""
    # Mock security status - in production, fetch from security modules
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
            "content_filter": 12,
            "rate_limits": 6
        }
    }

@router.get("/security/events")
async def get_security_events(limit: int = Query(50, le=500)):
    """Get recent security events"""
    # Mock security events
    events = []

    event_types = ["authentication", "authorization", "threat_blocked", "rate_limit", "content_filter"]
    severities = ["low", "medium", "high", "critical"]

    for i in range(min(limit, 20)):
        events.append({
            "id": f"security_event_{i}",
            "timestamp": (datetime.now() - timedelta(minutes=i*10)).isoformat(),
            "event_type": f"security.{event_types[i % len(event_types)]}",
            "severity": severities[i % len(severities)],
            "description": f"Security event {i} detected",
            "action_taken": "blocked" if i % 3 == 0 else "logged",
            "user_id": f"user_{i % 10}" if i % 2 == 0 else None
        })

    return events

@router.get("/security/threats")
async def get_security_threats():
    """Get threat analysis"""
    return {
        "total_threats": 156,
        "threats_blocked": 148,
        "threats_passed": 8,
        "threat_categories": {
            "sql_injection": 45,
            "xss": 32,
            "csrf": 12,
            "ddos": 67
        },
        "recent_threats": [
            {
                "id": "threat_1",
                "type": "sql_injection",
                "timestamp": datetime.now().isoformat(),
                "source_ip": "192.168.1.100",
                "blocked": True
            }
        ]
    }

@router.put("/security/rules/{rule}")
async def update_security_rule(rule: str, rule_data: dict):
    """Update a security rule"""
    value = rule_data.get("value")

    # Mock update - in production, update actual security rules
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
    # Mock metrics - in production, fetch from learning system
    return {
        "patternCount": 847,
        "feedbackPositive": 92,  # percentage
        "adaptationsToday": 34,
        "learningRate": 0.85,
        "confidenceScore": 0.92
    }

@router.get("/learning/patterns")
async def get_patterns(limit: int = Query(50, le=500)):
    """Get recognized patterns"""
    # Mock patterns
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
    # Mock feedback data
    feedback_data = []

    sentiments = ["positive", "negative", "neutral"]
    categories = ["accuracy", "speed", "relevance", "helpfulness"]

    for i in range(min(limit, 20)):
        feedback_data.append({
            "id": f"feedback_{i}",
            "timestamp": (datetime.now() - timedelta(hours=i)).isoformat(),
            "sentiment": sentiments[i % len(sentiments)],
            "category": categories[i % len(categories)],
            "score": 0.7 + (i % 30) / 100,
            "message": f"Feedback message {i}",
            "user_id": f"user_{i % 10}"
        })

    return feedback_data

# Rate Limiting Endpoints

@router.get("/rate-limits")
async def get_rate_limits():
    """Get current rate limit rules"""
    # Mock rate limits
    return [
        {"rule": "global_requests", "limit": 10000, "window": 60, "current": 3421},
        {"rule": "user_requests", "limit": 100, "window": 60, "current": 42},
        {"rule": "model_invocations", "limit": 50, "window": 3600, "current": 12},
        {"rule": "tool_executions", "limit": 200, "window": 3600, "current": 67}
    ]

@router.put("/rate-limits/{rule}")
async def update_rate_limit(rule: str, limit_data: dict):
    """Update a rate limit rule"""
    new_limit = limit_data.get("limit")

    # Mock update
    await manager.broadcast({
        "type": "rate_limit_update",
        "rule": rule,
        "limit": new_limit
    })

    return {"success": True, "rule": rule, "limit": new_limit}

# System Actions

@router.post("/system/restart-agents")
async def restart_agents():
    """Restart all agents"""
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
    await manager.broadcast({
        "type": "system_action",
        "action": "clear_cache",
        "status": "completed"
    })

    return {"success": True, "action": "clear_cache", "cleared_items": 1247}

@router.post("/system/backup")
async def create_backup():
    """Create system backup"""
    backup_id = f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

    await manager.broadcast({
        "type": "system_action",
        "action": "backup",
        "backup_id": backup_id,
        "status": "in_progress"
    })

    await asyncio.sleep(2)  # Simulate backup

    await manager.broadcast({
        "type": "system_action",
        "action": "backup",
        "backup_id": backup_id,
        "status": "completed"
    })

    return {
        "success": True,
        "action": "backup",
        "backup_id": backup_id,
        "size_mb": 1234,
        "timestamp": datetime.now().isoformat()
    }

@router.post("/system/restore")
async def restore_backup(restore_data: dict):
    """Restore from backup"""
    backup_id = restore_data.get("backup_id", "backup_123")

    await manager.broadcast({
        "type": "system_action",
        "action": "restore",
        "backup_id": backup_id,
        "status": "in_progress"
    })

    await asyncio.sleep(3)  # Simulate restore

    await manager.broadcast({
        "type": "system_action",
        "action": "restore",
        "backup_id": backup_id,
        "status": "completed"
    })

    return {
        "success": True,
        "action": "restore",
        "backup_id": backup_id,
        "restored_at": datetime.now().isoformat()
    }

@router.get("/system/export-logs")
async def export_logs(format: str = Query("json", regex="^(json|csv)$")):
    """Export system logs"""
    # Mock logs
    logs = []

    for i in range(100):
        logs.append({
            "id": f"log_{i}",
            "timestamp": (datetime.now() - timedelta(minutes=i)).isoformat(),
            "level": "INFO" if i % 5 != 0 else "WARNING",
            "message": f"Log entry {i}",
            "module": f"module_{i % 10}"
        })

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

# Health check endpoint
@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "AGI Dashboard API",
        "timestamp": datetime.now().isoformat(),
        "uptime": "99.9%"
    }

# Background task to send periodic updates
async def send_periodic_updates():
    """Send periodic updates to connected clients"""
    while True:
        await asyncio.sleep(5)  # Send updates every 5 seconds

        # Get current stats
        stats = {
            "totalRequests": 8462 + int(asyncio.get_event_loop().time()) % 100,
            "successRate": 98.5 + (int(asyncio.get_event_loop().time()) % 10) / 10
        }

        await manager.broadcast({
            "type": "stats_update",
            "stats": stats
        })

# Start background task on module load
# asyncio.create_task(send_periodic_updates())