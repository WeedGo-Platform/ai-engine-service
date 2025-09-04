"""
Customer Repository - Data access for customer information
Handles customer profiles and preferences
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

from repositories.base_repository import BaseRepository

logger = logging.getLogger(__name__)

class CustomerRepository(BaseRepository):
    """
    Repository for customer data access
    Manages customer profiles, preferences, and history
    """
    
    def __init__(self):
        """Initialize customer repository"""
        super().__init__("customers")
    
    async def create(
        self,
        customer_id: str,
        face_encoding: bytes,
        metadata: Dict[str, Any]
    ) -> bool:
        """Create new customer record"""
        
        data = {
            "customer_id": customer_id,
            "name": metadata.get("name", ""),
            "birth_date": metadata.get("birth_date"),
            "face_encoding": face_encoding,
            "enrolled_at": datetime.now(),
            "visit_count": 0
        }
        
        try:
            await self.insert(data)
            return True
        except Exception as e:
            logger.error(f"Failed to create customer: {str(e)}")
            return False
    
    async def get_by_store(self, store_id: str) -> List[Dict[str, Any]]:
        """Get all customers for a store"""
        
        query = """
            SELECT 
                customer_id,
                name,
                face_encoding,
                visit_count,
                last_visit,
                preferences
            FROM customers
            WHERE store_id = $1
            ORDER BY last_visit DESC
        """
        
        return await self.fetch_many(query, store_id)
    
    async def update_visit(self, customer_id: str) -> None:
        """Update customer visit information"""
        
        query = """
            UPDATE customers
            SET 
                visit_count = visit_count + 1,
                last_visit = $2
            WHERE customer_id = $1
        """
        
        await self.execute(query, customer_id, datetime.now())
    
    async def get_preferences(
        self,
        customer_id: str
    ) -> Optional[Dict[str, Any]]:
        """Get customer preferences"""
        
        query = """
            SELECT preferences
            FROM customers
            WHERE customer_id = $1
        """
        
        result = await self.fetch_one(query, customer_id)
        return result["preferences"] if result else None