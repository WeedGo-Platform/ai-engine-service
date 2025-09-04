"""
Chat Repository - Data access for chat history
Stores and retrieves conversation history
"""

import logging
from typing import List, Dict, Any
from datetime import datetime

from repositories.base_repository import BaseRepository
from services.interfaces import IChatRepository

logger = logging.getLogger(__name__)

class ChatRepository(BaseRepository, IChatRepository):
    """
    Repository for chat history data access
    Manages conversation history and analytics
    """
    
    def __init__(self):
        """Initialize chat repository"""
        super().__init__("chat_history")
    
    async def save_interaction(
        self,
        customer_id: str,
        message: str,
        response: str,
        language: str,
        model_used: str,
        session_id: str = None
    ) -> None:
        """Save chat interaction to database"""
        
        data = {
            "customer_id": customer_id,
            "message": message,
            "response": response,
            "language": language,
            "model_used": model_used,
            "session_id": session_id,
            "timestamp": datetime.now()
        }
        
        try:
            await self.insert(data)
            logger.debug(f"Saved chat interaction for {customer_id}")
        except Exception as e:
            logger.error(f"Failed to save chat interaction: {str(e)}")
    
    async def get_history(
        self,
        customer_id: str,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Get chat history for customer"""
        
        query = """
            SELECT 
                message,
                response,
                language,
                model_used,
                timestamp
            FROM chat_history
            WHERE customer_id = $1
            ORDER BY timestamp DESC
            LIMIT $2
        """
        
        results = await self.fetch_many(query, customer_id, limit)
        
        # Return in chronological order
        return list(reversed(results))
    
    async def get_popular_queries(
        self,
        language: str = None,
        days: int = 7,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """Get popular queries for analytics"""
        
        if language:
            query = """
                SELECT 
                    message,
                    COUNT(*) as count
                FROM chat_history
                WHERE 
                    timestamp > NOW() - INTERVAL '%s days'
                    AND language = $1
                GROUP BY message
                ORDER BY count DESC
                LIMIT $2
            """
            return await self.fetch_many(query % days, language, limit)
        else:
            query = """
                SELECT 
                    message,
                    COUNT(*) as count
                FROM chat_history
                WHERE timestamp > NOW() - INTERVAL '%s days'
                GROUP BY message
                ORDER BY count DESC
                LIMIT $1
            """
            return await self.fetch_many(query % days, limit)
    
    async def get_session_history(
        self,
        session_id: str
    ) -> List[Dict[str, Any]]:
        """Get chat history for a specific session"""
        
        query = """
            SELECT 
                message,
                response,
                language,
                model_used,
                timestamp,
                customer_id,
                'user' as role
            FROM chat_history
            WHERE session_id = $1
            ORDER BY timestamp ASC
        """
        
        results = await self.fetch_many(query, session_id)
        
        # Format results with role indicators
        formatted = []
        for result in results:
            formatted.append({
                "role": "user",
                "message": result["message"],
                "timestamp": result["timestamp"]
            })
            formatted.append({
                "role": "assistant",
                "response": result["response"],
                "timestamp": result["timestamp"]
            })
        
        return formatted
    
    async def get_customer_history(
        self,
        customer_id: str,
        days_back: int = 30
    ) -> List[Dict[str, Any]]:
        """Get complete history for a customer within time range"""
        
        query = """
            SELECT 
                message,
                response,
                language,
                model_used,
                session_id,
                timestamp as created_at
            FROM chat_history
            WHERE 
                customer_id = $1
                AND timestamp > NOW() - INTERVAL '%s days'
            ORDER BY timestamp ASC
        """
        
        return await self.fetch_many(query % days_back, customer_id)