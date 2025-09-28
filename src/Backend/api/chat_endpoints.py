"""Chat WebSocket endpoints for real-time messaging"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.responses import JSONResponse
from typing import Dict, List, Optional
import json
import uuid
import asyncio
from datetime import datetime
import logging
import time
import asyncpg
import os
from services.smart_ai_engine_v5 import SmartAIEngineV5
from services.user_context_service import UserContextService

logger = logging.getLogger(__name__)

# Initialize AI engine
ai_engine = SmartAIEngineV5()

# Database connection pool
db_pool = None

async def get_db_connection():
    """Get database connection from pool"""
    global db_pool
    if not db_pool:
        db_pool = await asyncpg.create_pool(
            host=os.getenv('DB_HOST', 'localhost'),
            port=int(os.getenv('DB_PORT', 5434)),
            user=os.getenv('DB_USER', 'weedgo'),
            password=os.getenv('DB_PASSWORD', 'weedgo123'),
            database=os.getenv('DB_NAME', 'ai_engine'),
            min_size=5,
            max_size=20
        )
    return await db_pool.acquire()

# Load default model on startup with dispensary agent
try:
    from pathlib import Path

    # Load the default model configured in system_config.json
    default_model = "qwen2.5_0.5b_instruct_q4_k_m"  # or get from config

    # Get marcel personality for dispensary agent
    dispensary_personality = "marcel"  # default
    personalities_dir = Path("prompts/agents/dispensary/personality")
    if personalities_dir.exists():
        personality_files = list(personalities_dir.glob("*.json"))
        marcel_file = Path(personalities_dir / "marcel.json")
        if marcel_file.exists():
            dispensary_personality = "marcel"
        elif personality_files:
            dispensary_personality = personality_files[0].stem

    if default_model in ai_engine.available_models:
        # Load with dispensary agent and marcel personality
        success = ai_engine.load_model(default_model, agent_id="dispensary", personality_id=dispensary_personality)
        if success:
            logger.info(f"Loaded default model: {default_model} with dispensary/{dispensary_personality}")
        else:
            # Fallback to assistant if dispensary fails
            success = ai_engine.load_model(default_model, agent_id="assistant", personality_id="friendly")
            if success:
                logger.info(f"Loaded default model with dispensary agent as fallback")
            else:
                logger.error(f"Failed to load default model: {default_model}")
    else:
        logger.warning(f"Default model {default_model} not found in available models")
        # Try to load first available model
        if ai_engine.available_models:
            first_model = list(ai_engine.available_models.keys())[0]
            success = ai_engine.load_model(first_model, agent_id="dispensary", personality_id=dispensary_personality)
            if success:
                logger.info(f"Loaded fallback model: {first_model} with dispensary/{dispensary_personality}")
except Exception as e:
    logger.error(f"Failed to load model on startup: {e}")

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
                    user_id = message_data.get("user_id")  # Get user_id from message

                    # Log user context status
                    logger.info(f"[chat_endpoints] Received message - Session: {session_id}, User ID: {user_id}, Has User: {bool(user_id)}")

                    # Debug timing
                    debug_start = time.time()
                    timing_points = {}

                    # Get session agent and personality
                    session_data = chat_sessions.get(session_id, {})
                    agent = session_data.get("agent", "dispensary")
                    personality = session_data.get("personality", "friendly")
                    timing_points['session_lookup'] = time.time() - debug_start

                    # Load agent and personality if needed
                    agent_load_start = time.time()
                    if ai_engine.current_agent != agent or ai_engine.current_personality_type != personality:
                        ai_engine.load_agent_personality(agent, personality)
                    timing_points['agent_load'] = time.time() - agent_load_start

                    # Send typing indicator
                    await manager.send_message(json.dumps({
                        "type": "typing",
                        "status": "start"
                    }), session_id)

                    # Track response time and tokens
                    start_time = time.time()
                    prompt_tokens = len(user_message.split())  # Simple approximation

                    # Log before AI response
                    logger.info(f"[chat_endpoints] Calling AI engine - User ID: {user_id}, Agent: {agent}, Personality: {personality}")

                    try:
                        ai_response_start = time.time()
                        # Use async version if available
                        if hasattr(ai_engine, 'get_response_async'):
                            ai_response = await ai_engine.get_response_async(
                                user_message,
                                session_id=session_id,
                                user_id=user_id,  # Pass user_id for context
                                max_tokens=500
                            )
                        else:
                            ai_response = ai_engine.get_response(
                                user_message,
                                session_id=session_id,
                                user_id=user_id,  # Pass user_id for context
                                max_tokens=500
                            )
                        timing_points['ai_response'] = time.time() - ai_response_start
                    except Exception as e:
                        logger.error(f"AI engine error: {e}")
                        ai_response = "I apologize, but I'm having trouble processing your request. Please try again."
                        timing_points['ai_response'] = time.time() - ai_response_start

                    # Calculate metrics
                    response_time = time.time() - start_time

                    # Log debug timing
                    logger.info(f"Chat timing breakdown - Total: {response_time:.3f}s | Session: {timing_points.get('session_lookup', 0):.3f}s | Agent: {timing_points.get('agent_load', 0):.3f}s | AI Response: {timing_points.get('ai_response', 0):.3f}s")
                    completion_tokens = len(ai_response.split())  # Simple approximation
                    total_tokens = prompt_tokens + completion_tokens

                    # Get current model name
                    current_model = ai_engine.current_model_name if hasattr(ai_engine, 'current_model_name') else 'qwen2.5_0.5b_instruct_q4_k_m'

                    # Save conversation to database if user_id is provided
                    if user_id:
                        try:
                            conn = await get_db_connection()
                            try:
                                user_context_service = UserContextService(conn)
                                await user_context_service.save_conversation_message(
                                    session_id=session_id,
                                    user_id=user_id,
                                    user_message=user_message,
                                    ai_response=ai_response,
                                    intent=None,  # Could be determined based on message analysis
                                    metadata={
                                        'agent': agent,
                                        'personality': personality,
                                        'model': current_model,
                                        'response_time': response_time,
                                        'tokens': {
                                            'prompt': prompt_tokens,
                                            'completion': completion_tokens,
                                            'total': total_tokens
                                        }
                                    }
                                )
                                logger.info(f"[chat_endpoints] Conversation saved for user {user_id} in session {session_id}")
                            finally:
                                await db_pool.release(conn)
                        except Exception as e:
                            logger.error(f"[chat_endpoints] Failed to save conversation: {e}")

                    await manager.send_message(json.dumps({
                        "type": "typing",
                        "status": "stop"
                    }), session_id)

                    await manager.send_message(json.dumps({
                        "type": "message",
                        "role": "assistant",
                        "content": ai_response,
                        "timestamp": datetime.utcnow().isoformat(),
                        "response_time": response_time,
                        "token_count": total_tokens,
                        "prompt_tokens": prompt_tokens,
                        "completion_tokens": completion_tokens,
                        "model": current_model
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

                    # Store session settings
                    if session_id not in chat_sessions:
                        chat_sessions[session_id] = {
                            "id": session_id,
                            "created_at": datetime.utcnow().isoformat(),
                            "messages": []
                        }

                    chat_sessions[session_id]["agent"] = agent
                    chat_sessions[session_id]["personality"] = personality

                    # Load the agent and personality in the AI engine
                    try:
                        ai_engine.load_agent_personality(agent, personality)
                        logger.info(f"Loaded agent '{agent}' with personality '{personality}' for session {session_id}")
                    except Exception as e:
                        logger.warning(f"Could not load agent/personality: {e}")

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
    logger.info(f"[chat_endpoints] REST message received - Session: {session_id}, User ID: {user_id}, Has User: {bool(user_id)}")

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

    # Track response time and tokens
    start_time = time.time()
    prompt_tokens = len(message.split())  # Simple approximation

    # Log before AI response
    logger.info(f"[chat_endpoints] REST calling AI engine - User ID: {user_id}, Agent: {agent}, Personality: {personality}")

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

    # Calculate metrics
    response_time = time.time() - start_time
    completion_tokens = len(ai_response.split())  # Simple approximation
    total_tokens = prompt_tokens + completion_tokens

    # Get current model name
    current_model = ai_engine.current_model_name if hasattr(ai_engine, 'current_model_name') else 'qwen2.5_0.5b_instruct_q4_k_m'

    # Save conversation to database if user_id is provided
    if user_id:
        try:
            conn = await get_db_connection()
            try:
                user_context_service = UserContextService(conn)
                await user_context_service.save_conversation_message(
                    session_id=session_id,
                    user_id=user_id,
                    user_message=message,
                    ai_response=ai_response,
                    intent=None,  # Could be determined based on message analysis
                    metadata={
                        'agent': agent,
                        'personality': personality,
                        'model': current_model,
                        'response_time': response_time,
                        'tokens': {
                            'prompt': prompt_tokens,
                            'completion': completion_tokens,
                            'total': total_tokens
                        }
                    }
                )
                logger.info(f"[chat_endpoints REST] Conversation saved for user {user_id} in session {session_id}")
            finally:
                await db_pool.release(conn)
        except Exception as e:
            logger.error(f"[chat_endpoints REST] Failed to save conversation: {e}")

    # Add AI response to session
    chat_sessions[session_id]["messages"].append({
        "role": "assistant",
        "content": ai_response,
        "timestamp": datetime.utcnow().isoformat()
    })

    return JSONResponse({
        "response": ai_response,
        "session_id": session_id,
        "response_time": response_time,
        "token_count": total_tokens,
        "prompt_tokens": prompt_tokens,
        "completion_tokens": completion_tokens
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

@router.get("/history/{user_id}")
async def get_chat_history(user_id: str, limit: int = 20):
    """Get chat history for a user"""
    try:
        conn = await get_db_connection()
        try:
            # Query to get recent chat interactions
            query = """
                SELECT
                    message_id,
                    session_id,
                    user_message,
                    ai_response,
                    created_at,
                    metadata
                FROM chat_interactions
                WHERE customer_id = $1
                ORDER BY created_at DESC
                LIMIT $2
            """

            rows = await conn.fetch(query, user_id, limit)

            # Format messages for frontend
            messages = []
            for row in rows:
                # Add user message
                messages.append({
                    "id": f"user-{row['message_id']}",
                    "role": "user",
                    "content": row['user_message'],
                    "timestamp": row['created_at'].isoformat() if row['created_at'] else None,
                    "session_id": row['session_id']
                })
                # Add AI response
                messages.append({
                    "id": f"ai-{row['message_id']}",
                    "role": "assistant",
                    "content": row['ai_response'],
                    "timestamp": row['created_at'].isoformat() if row['created_at'] else None,
                    "session_id": row['session_id'],
                    "metadata": row['metadata'] if isinstance(row['metadata'], dict) else None
                })

            # Reverse to get chronological order (oldest first)
            messages.reverse()

            logger.info(f"[chat_endpoints] Retrieved {len(messages)} messages for user {user_id}")

            return JSONResponse({
                "messages": messages,
                "count": len(messages)
            })

        finally:
            await db_pool.release(conn)

    except Exception as e:
        logger.error(f"[chat_endpoints] Failed to get chat history: {e}")
        return JSONResponse({
            "messages": [],
            "count": 0,
            "error": str(e)
        }, status_code=500)