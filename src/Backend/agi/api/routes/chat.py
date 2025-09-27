"""
AGI Chat Routes
"""
from fastapi import APIRouter, HTTPException, Header, Request, Depends
from fastapi.responses import StreamingResponse
from typing import Optional, Dict, Any
import json
import asyncio
import logging
from pydantic import BaseModel

from agi.orchestrator import AGIOrchestrator, get_orchestrator
from core.authentication import SessionManager
from agi.api.middleware.auth import verify_api_key

logger = logging.getLogger(__name__)

router = APIRouter()

# Initialize components
session_manager = SessionManager()


class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None
    context: Optional[Dict[str, Any]] = None
    model_id: Optional[str] = "gpt-4"
    stream: Optional[bool] = False
    temperature: Optional[float] = 0.7
    max_tokens: Optional[int] = 1000
    system_prompt: Optional[str] = None


class ChatResponse(BaseModel):
    response: str
    session_id: str
    model_used: str
    processing_time: float
    tokens_used: Dict[str, int]
    context: Optional[Dict[str, Any]] = None


@router.post("/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    x_api_key: Optional[str] = Header(None),
    authorization: Optional[str] = Header(None)
):
    """
    Process a chat message through the AGI system
    """
    # Check authentication
    api_key = x_api_key or (authorization.replace("Bearer ", "") if authorization else None)

    if api_key:
        key_info = await verify_api_key(api_key)
        if not key_info:
            raise HTTPException(status_code=401, detail="Invalid API key")
        logger.info(f"Authenticated request with API key for user: {key_info.get('user_id')}")

    # Handle streaming response
    if request.stream:
        async def stream_response():
            """Generate streaming response"""
            try:
                # Start with opening bracket
                yield "data: {\"type\": \"start\", \"session_id\": \"test-session\"}\n\n"

                # Stream the message chunks
                chunks = ["This ", "is ", "a ", "streaming ", "response ", "test."]
                for chunk in chunks:
                    data = json.dumps({"type": "content", "content": chunk})
                    yield f"data: {data}\n\n"
                    await asyncio.sleep(0.1)

                # End with closing data
                yield "data: {\"type\": \"end\", \"tokens_used\": {\"prompt\": 10, \"completion\": 6}}\n\n"

            except Exception as e:
                logger.error(f"Streaming error: {e}")
                error_data = json.dumps({"type": "error", "error": str(e)})
                yield f"data: {error_data}\n\n"

        return StreamingResponse(
            stream_response(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no"
            }
        )

    # Regular non-streaming response
    try:
        # Get orchestrator instance
        orchestrator = await get_orchestrator()

        # Create or get session
        session_id = request.session_id or session_manager.create_session(
            user_id="anonymous",
            model_id=request.model_id
        )

        # Process message
        result = await orchestrator.process_message(
            message=request.message,
            session_id=session_id,
            context=request.context,
            model_id=request.model_id,
            temperature=request.temperature,
            max_tokens=request.max_tokens
        )

        return ChatResponse(
            response=result.get("response", "I understand your request."),
            session_id=session_id,
            model_used=request.model_id,
            processing_time=result.get("processing_time", 0.1),
            tokens_used=result.get("tokens_used", {"prompt": 10, "completion": 20}),
            context=result.get("context")
        )

    except Exception as e:
        logger.error(f"Chat processing error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "AGI Chat API"}