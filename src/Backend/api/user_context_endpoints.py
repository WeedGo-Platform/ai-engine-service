"""
User Context and Chat History API Endpoints
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Dict, Optional, Any
from datetime import datetime
import logging
import asyncpg
import os

from services.user_context_service import UserContextService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["user-context"])

# Database connection pool
db_pool = None

async def get_db_pool():
    """Get or create database connection pool"""
    global db_pool
    if db_pool is None:
        db_pool = await asyncpg.create_pool(
            host=os.getenv('DB_HOST', 'localhost'),
            port=int(os.getenv('DB_PORT', 5434)),
            database=os.getenv('DB_NAME', 'ai_engine'),
            user=os.getenv('DB_USER', 'weedgo'),
            password=os.getenv('DB_PASSWORD', 'weedgo123'),
            min_size=1,
            max_size=10
        )
    return db_pool


async def get_user_context_service():
    """Get user context service instance"""
    pool = await get_db_pool()
    conn = await pool.acquire()
    try:
        yield UserContextService(conn)
    finally:
        await pool.release(conn)


@router.get("/chat/history/{user_id}")
async def get_chat_history(
    user_id: str,
    limit: int = Query(50, ge=1, le=200),
    days_back: int = Query(30, ge=1, le=365),
    service: UserContextService = Depends(get_user_context_service)
):
    """
    Get chat history for a user
    
    Args:
        user_id: User ID, email, or phone
        limit: Maximum number of conversations to return
        days_back: Number of days to look back
    
    Returns:
        Chat history with conversations and interactions
    """
    try:
        history = await service.get_chat_history(user_id, limit=limit, days_back=days_back)
        
        return {
            "user_id": user_id,
            "count": len(history),
            "days_back": days_back,
            "history": history
        }
    except Exception as e:
        logger.error(f"Error getting chat history: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/user/context/{user_id}")
async def get_user_context(
    user_id: str,
    session_id: Optional[str] = None,
    service: UserContextService = Depends(get_user_context_service)
):
    """
    Get complete user context for AI model
    
    Args:
        user_id: User ID, email, or phone
        session_id: Optional session ID for current conversation
    
    Returns:
        Complete user context including profile, preferences, history
    """
    try:
        context = await service.get_complete_user_context(user_id, session_id)
        
        if not context.get('user_profile'):
            raise HTTPException(status_code=404, detail=f"User {user_id} not found")
        
        return context
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting user context: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/chat/conversation/{session_id}")
async def get_conversation_context(
    session_id: str,
    service: UserContextService = Depends(get_user_context_service)
):
    """
    Get current conversation context for a session
    
    Args:
        session_id: Session ID
    
    Returns:
        Conversation context with messages
    """
    try:
        context = await service.get_conversation_context(session_id)
        
        if not context:
            raise HTTPException(status_code=404, detail=f"Session {session_id} not found")
        
        return context
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting conversation context: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/chat/message")
async def save_chat_message(
    session_id: str,
    user_id: str,
    user_message: str,
    ai_response: str,
    intent: Optional[str] = None,
    metadata: Optional[Dict] = None,
    service: UserContextService = Depends(get_user_context_service)
):
    """
    Save a chat message to history
    
    Args:
        session_id: Session ID
        user_id: User ID
        user_message: User's message
        ai_response: AI's response
        intent: Detected intent (optional)
        metadata: Additional metadata (optional)
    
    Returns:
        Success status
    """
    try:
        success = await service.save_conversation_message(
            session_id=session_id,
            user_id=user_id,
            user_message=user_message,
            ai_response=ai_response,
            intent=intent,
            metadata=metadata
        )
        
        if not success:
            raise HTTPException(status_code=500, detail="Failed to save message")
        
        return {
            "success": True,
            "message": "Chat message saved successfully"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error saving chat message: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/user/preferences/{user_id}")
async def get_user_preferences(
    user_id: str,
    service: UserContextService = Depends(get_user_context_service)
):
    """
    Get user preferences and behavior patterns
    
    Args:
        user_id: User ID, email, or phone
    
    Returns:
        User preferences, favorite products, and purchase patterns
    """
    try:
        preferences = await service.get_user_preferences(user_id)
        
        return {
            "user_id": user_id,
            "preferences": preferences
        }
    except Exception as e:
        logger.error(f"Error getting user preferences: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/user/purchase-history/{user_id}")
async def get_purchase_history(
    user_id: str,
    limit: int = Query(50, ge=1, le=200),
    service: UserContextService = Depends(get_user_context_service)
):
    """
    Get user's purchase history
    
    Args:
        user_id: User ID, email, or phone
        limit: Maximum number of orders to return
    
    Returns:
        Purchase history with order details
    """
    try:
        history = await service.get_purchase_history(user_id, limit=limit)
        
        # Calculate summary statistics
        total_spent = sum(order.get('total_amount', 0) for order in history)
        total_orders = len(history)
        avg_order_value = total_spent / total_orders if total_orders > 0 else 0
        
        return {
            "user_id": user_id,
            "total_orders": total_orders,
            "total_spent": round(total_spent, 2),
            "average_order_value": round(avg_order_value, 2),
            "orders": history
        }
    except Exception as e:
        logger.error(f"Error getting purchase history: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/user/profile/{user_id}")
async def get_user_profile(
    user_id: str,
    service: UserContextService = Depends(get_user_context_service)
):
    """
    Get user profile information
    
    Args:
        user_id: User ID, email, or phone
    
    Returns:
        User profile with personal information and verification status
    """
    try:
        profile = await service.get_user_profile(user_id)
        
        if not profile:
            raise HTTPException(status_code=404, detail=f"User {user_id} not found")
        
        return profile
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting user profile: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))