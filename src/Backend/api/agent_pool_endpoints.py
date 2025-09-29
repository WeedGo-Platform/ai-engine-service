"""
Agent Pool API Endpoints - For managing multiple agents and personalities
"""

import logging
from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any, List, Optional
from datetime import datetime

from services.agent_pool_manager import get_agent_pool

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/agent-pool", tags=["agent-pool"])


@router.get("/available")
async def get_available_agents():
    """Get all available agents and their personalities"""
    try:
        pool = get_agent_pool()
        agents = pool.get_available_agents()

        # Ensure we only return agents that actually exist
        return {
            "success": True,
            "agents": agents,
            "total": len(agents)
        }
    except Exception as e:
        logger.error(f"Error getting available agents: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{agent_id}/personalities")
async def get_agent_personalities(agent_id: str):
    """Get personalities for a specific agent"""
    try:
        pool = get_agent_pool()
        agent = pool.get_agent(agent_id)

        if not agent:
            raise HTTPException(status_code=404, detail=f"Agent '{agent_id}' not found")

        personalities = [
            {
                "id": p_id,
                "name": p.name,
                "traits": p.traits,
                "greeting": p.greeting
            }
            for p_id, p in agent.personalities.items()
        ]

        return {
            "success": True,
            "agent_id": agent_id,
            "agent_name": agent.name,
            "personalities": personalities,
            "default": agent.default_personality
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting personalities for agent {agent_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/session/create")
async def create_agent_session(
    session_id: str,
    agent_id: str,
    personality_id: Optional[str] = None,
    user_id: Optional[str] = None
):
    """Create a new session with specific agent/personality"""
    try:
        pool = get_agent_pool()

        # Create session
        session = await pool.create_session(
            session_id=session_id,
            agent_id=agent_id,
            personality_id=personality_id,
            user_id=user_id
        )

        return {
            "success": True,
            "session_id": session.session_id,
            "agent_id": session.agent_id,
            "personality_id": session.personality_id,
            "created_at": session.created_at.isoformat()
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating session: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/session/{session_id}/switch-personality")
async def switch_personality(
    session_id: str,
    new_personality_id: str,
    preserve_context: bool = True
):
    """Hot-swap personality for an active session"""
    try:
        pool = get_agent_pool()

        success = await pool.switch_personality(
            session_id=session_id,
            new_personality_id=new_personality_id,
            preserve_context=preserve_context
        )

        if not success:
            raise HTTPException(status_code=400, detail="Failed to switch personality")

        return {
            "success": True,
            "session_id": session_id,
            "new_personality": new_personality_id,
            "context_preserved": preserve_context
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error switching personality: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/session/{session_id}/switch-agent")
async def switch_agent(
    session_id: str,
    new_agent_id: str,
    personality_id: Optional[str] = None
):
    """Switch to a different agent (clears context)"""
    try:
        pool = get_agent_pool()

        success = await pool.switch_agent(
            session_id=session_id,
            new_agent_id=new_agent_id,
            personality_id=personality_id
        )

        if not success:
            raise HTTPException(status_code=400, detail="Failed to switch agent")

        # Get updated session info
        session = pool.get_session(session_id)

        return {
            "success": True,
            "session_id": session_id,
            "new_agent": session.agent_id,
            "new_personality": session.personality_id,
            "context_cleared": True
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error switching agent: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/metrics")
async def get_agent_pool_metrics():
    """Get performance metrics for the agent pool"""
    try:
        pool = get_agent_pool()
        metrics = pool.get_metrics()

        return {
            "success": True,
            "metrics": metrics,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Error getting metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sessions/active")
async def get_active_sessions():
    """Get list of active sessions"""
    try:
        pool = get_agent_pool()

        sessions = []
        for session_id, session in pool.sessions.items():
            sessions.append({
                "session_id": session_id,
                "agent_id": session.agent_id,
                "personality_id": session.personality_id,
                "user_id": session.user_id,
                "created_at": session.created_at.isoformat(),
                "last_activity": session.last_activity.isoformat(),
                "message_count": len(session.context_history)
            })

        return {
            "success": True,
            "sessions": sessions,
            "total": len(sessions)
        }
    except Exception as e:
        logger.error(f"Error getting active sessions: {e}")
        raise HTTPException(status_code=500, detail=str(e))