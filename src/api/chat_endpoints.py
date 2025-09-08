"""Chat WebSocket endpoints for real-time messaging"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.responses import JSONResponse
from typing import Dict, List, Optional
import json
import uuid
import asyncio
from datetime import datetime
import logging
from services.smart_ai_engine_v5 import SmartAIEngineV5

logger = logging.getLogger(__name__)

# Initialize AI engine
ai_engine = SmartAIEngineV5()

router = APIRouter(prefix="/chat", tags=["chat"])

# Store active WebSocket connections
active_connections: Dict[str, WebSocket] = {}

# Store chat sessions
chat_sessions: Dict[str, Dict] = {}

class ConnectionManager:
    """Manages WebSocket connections for chat"""
    
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
    
    async def connect(self, websocket: WebSocket, session_id: str):
        """Accept and store a new WebSocket connection"""
        await websocket.accept()
        self.active_connections[session_id] = websocket
        logger.info(f"Client {session_id} connected")
    
    def disconnect(self, session_id: str):
        """Remove a WebSocket connection"""
        if session_id in self.active_connections:
            del self.active_connections[session_id]
            logger.info(f"Client {session_id} disconnected")
    
    async def send_message(self, message: str, session_id: str):
        """Send a message to a specific client"""
        if session_id in self.active_connections:
            await self.active_connections[session_id].send_text(message)
    
    async def broadcast(self, message: str):
        """Broadcast a message to all connected clients"""
        for connection in self.active_connections.values():
            await connection.send_text(message)

# Create connection manager instance
manager = ConnectionManager()

@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """Main WebSocket endpoint for chat communication"""
    session_id = str(uuid.uuid4())
    
    try:
        # Accept the connection
        await manager.connect(websocket, session_id)
        
        # Send initial connection success message
        await manager.send_message(json.dumps({
            "type": "connection",
            "status": "connected",
            "session_id": session_id,
            "message": "Connected to WeedGo AI Chat"
        }), session_id)
        
        # Keep the connection alive and handle messages
        while True:
            # Receive message from client
            data = await websocket.receive_text()
            
            try:
                message_data = json.loads(data)
                message_type = message_data.get("type", "message")
                
                if message_type == "ping":
                    # Respond to ping with pong
                    await manager.send_message(json.dumps({
                        "type": "pong",
                        "timestamp": datetime.utcnow().isoformat()
                    }), session_id)
                
                elif message_type == "message":
                    # Process chat message
                    user_message = message_data.get("message", "")
                    
                    # Get session agent and personality
                    session_data = chat_sessions.get(session_id, {})
                    agent = session_data.get("agent", "dispensary")
                    personality = session_data.get("personality", "friendly")
                    
                    # Load agent and personality if needed
                    if ai_engine.current_agent != agent or ai_engine.current_personality_type != personality:
                        ai_engine.load_agent_personality(agent, personality)
                    
                    # Send typing indicator
                    await manager.send_message(json.dumps({
                        "type": "typing",
                        "status": "start"
                    }), session_id)
                    
                    # Get actual AI response with user context if available
                    user_id = message_data.get("user_id")  # Get user_id if provided
                    try:
                        ai_response = ai_engine.get_response(
                            user_message,
                            session_id=session_id,
                            user_id=user_id,  # Pass user_id for context
                            max_tokens=500
                        )
                    except Exception as e:
                        logger.error(f"AI engine error: {e}")
                        ai_response = "I apologize, but I'm having trouble processing your request. Please try again."
                    
                    await manager.send_message(json.dumps({
                        "type": "typing",
                        "status": "stop"
                    }), session_id)
                    
                    await manager.send_message(json.dumps({
                        "type": "message",
                        "role": "assistant",
                        "content": ai_response,
                        "timestamp": datetime.utcnow().isoformat()
                    }), session_id)
                
                elif message_type == "voice":
                    # Process voice message
                    audio_data = message_data.get("audio", "")
                    
                    # Send processing indicator
                    await manager.send_message(json.dumps({
                        "type": "voice_processing",
                        "status": "processing"
                    }), session_id)
                    
                    # Simulate voice processing
                    await asyncio.sleep(1.5)
                    
                    # Send transcription and response
                    transcription = "This is a simulated transcription of your voice message"
                    
                    await manager.send_message(json.dumps({
                        "type": "transcription",
                        "text": transcription,
                        "timestamp": datetime.utcnow().isoformat()
                    }), session_id)
                    
                    await manager.send_message(json.dumps({
                        "type": "message",
                        "role": "assistant",
                        "content": f"I heard you say: '{transcription}'",
                        "timestamp": datetime.utcnow().isoformat()
                    }), session_id)
                
                elif message_type == "session_update":
                    # Update session settings
                    agent = message_data.get("agent")
                    personality = message_data.get("personality")
                    
                    await manager.send_message(json.dumps({
                        "type": "session_updated",
                        "agent": agent,
                        "personality": personality,
                        "message": f"Session updated: Agent={agent}, Personality={personality}"
                    }), session_id)
                
                else:
                    # Unknown message type
                    await manager.send_message(json.dumps({
                        "type": "error",
                        "message": f"Unknown message type: {message_type}"
                    }), session_id)
            
            except json.JSONDecodeError:
                await manager.send_message(json.dumps({
                    "type": "error",
                    "message": "Invalid JSON format"
                }), session_id)
            except Exception as e:
                logger.error(f"Error processing message: {e}")
                await manager.send_message(json.dumps({
                    "type": "error",
                    "message": f"Error processing message: {str(e)}"
                }), session_id)
    
    except WebSocketDisconnect:
        manager.disconnect(session_id)
        logger.info(f"Client {session_id} disconnected")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(session_id)

@router.post("/session")
async def create_session(agent: str = "dispensary", personality: str = "friendly"):
    """Create a new chat session"""
    session_id = str(uuid.uuid4())
    
    # Load the agent and personality in the AI engine
    try:
        ai_engine.load_agent_personality(agent, personality)
    except Exception as e:
        logger.warning(f"Could not load agent/personality: {e}")
    
    # Store session data
    chat_sessions[session_id] = {
        "id": session_id,
        "agent": agent,
        "personality": personality,
        "created_at": datetime.utcnow().isoformat(),
        "messages": []
    }
    
    return JSONResponse({
        "session_id": session_id,
        "agent": agent,
        "personality": personality,
        "status": "created"
    })

@router.get("/session/{session_id}")
async def get_session(session_id: str):
    """Get session information"""
    if session_id not in chat_sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    return JSONResponse(chat_sessions[session_id])

@router.post("/message")
async def send_message(session_id: str, message: str, user_id: Optional[str] = None):
    """Send a message in a chat session (REST alternative to WebSocket)"""
    if session_id not in chat_sessions:
        # Create session if it doesn't exist
        chat_sessions[session_id] = {
            "id": session_id,
            "agent": "dispensary",
            "personality": "friendly",
            "created_at": datetime.utcnow().isoformat(),
            "messages": [],
            "user_id": user_id  # Store user_id in session
        }
    
    # Add user message to session
    chat_sessions[session_id]["messages"].append({
        "role": "user",
        "content": message,
        "timestamp": datetime.utcnow().isoformat()
    })
    
    # Get session agent and personality
    agent = chat_sessions[session_id].get("agent", "dispensary")
    personality = chat_sessions[session_id].get("personality", "friendly")
    
    # Load agent and personality if needed
    if ai_engine.current_agent != agent or ai_engine.current_personality_type != personality:
        ai_engine.load_agent_personality(agent, personality)
    
    # Get user_id from session if not provided
    if not user_id and "user_id" in chat_sessions[session_id]:
        user_id = chat_sessions[session_id]["user_id"]
    
    # Generate AI response with user context
    try:
        ai_response = ai_engine.get_response(
            message,
            session_id=session_id,
            user_id=user_id,  # Pass user_id for context-aware responses
            max_tokens=500
        )
    except Exception as e:
        logger.error(f"AI engine error: {e}")
        ai_response = "I apologize, but I'm having trouble processing your request. Please try again."
    
    # Add AI response to session
    chat_sessions[session_id]["messages"].append({
        "role": "assistant",
        "content": ai_response,
        "timestamp": datetime.utcnow().isoformat()
    })
    
    return JSONResponse({
        "response": ai_response,
        "session_id": session_id,
        "token_count": len(message.split()) + len(ai_response.split())
    })

@router.delete("/session/{session_id}")
async def end_session(session_id: str):
    """End a chat session"""
    if session_id not in chat_sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Clean up session
    del chat_sessions[session_id]
    
    # Disconnect WebSocket if active
    if session_id in manager.active_connections:
        manager.disconnect(session_id)
    
    return JSONResponse({"status": "session_ended", "session_id": session_id})

@router.get("/sessions")
async def list_sessions():
    """List all active chat sessions"""
    return JSONResponse({
        "sessions": list(chat_sessions.keys()),
        "count": len(chat_sessions),
        "active_websockets": len(manager.active_connections)
    })