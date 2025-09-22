"""
User Context Service
Provides comprehensive user context including profile, chat history, and purchase history
"""

from typing import List, Dict, Optional, Any
from datetime import datetime, timedelta
from uuid import UUID
import asyncpg
import logging
import json

logger = logging.getLogger(__name__)


class UserContextService:
    """Service for managing user context and history"""
    
    def __init__(self, db_connection):
        """Initialize user context service with database connection"""
        self.db = db_connection
    
    async def get_user_profile(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user profile information"""
        try:
            query = """
                SELECT 
                    u.id,
                    u.email,
                    u.phone,
                    u.first_name,
                    u.last_name,
                    u.date_of_birth,
                    u.age_verified,
                    u.role,
                    u.active,
                    up.preferences,
                    up.loyalty_points,
                    up.total_spent,
                    up.created_at
                FROM users u
                LEFT JOIN profiles up ON u.id = up.user_id
                WHERE u.id = $1 OR u.email = $1 OR u.phone = $1
            """
            
            result = await self.db.fetchrow(query, user_id)
            if result:
                profile = dict(result)
                # Calculate age if DOB exists
                if profile.get('date_of_birth'):
                    today = datetime.now().date()
                    dob = profile['date_of_birth']
                    age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
                    profile['age'] = age
                return profile
            return None
            
        except Exception as e:
            logger.error(f"Error getting user profile: {str(e)}")
            raise
    
    async def get_chat_history(self, user_id: str, limit: int = 50, 
                             days_back: int = 30) -> List[Dict[str, Any]]:
        """Get user's chat history"""
        try:
            # First try ai_conversations table
            query = """
                SELECT 
                    conversation_id,
                    session_id,
                    messages,
                    context,
                    created_at,
                    updated_at
                FROM ai_conversations
                WHERE customer_id = $1
                AND created_at >= $2
                ORDER BY created_at DESC
                LIMIT $3
            """
            
            cutoff_date = datetime.now() - timedelta(days=days_back)
            conversations = await self.db.fetch(query, user_id, cutoff_date, limit)
            
            # Also get from chat_interactions
            interactions_query = """
                SELECT 
                    message_id,
                    session_id,
                    user_message,
                    ai_response,
                    intent,
                    response_time,
                    created_at,
                    metadata
                FROM chat_interactions
                WHERE customer_id = $1
                AND created_at >= $2
                ORDER BY created_at DESC
                LIMIT $3
            """
            
            interactions = await self.db.fetch(interactions_query, user_id, cutoff_date, limit)
            
            # Combine and format results
            chat_history = []
            
            # Process conversations
            for conv in conversations:
                conv_dict = dict(conv)
                if conv_dict.get('messages'):
                    # Extract messages from JSONB
                    messages = conv_dict['messages']
                    if isinstance(messages, str):
                        messages = json.loads(messages)
                    conv_dict['messages'] = messages
                chat_history.append({
                    'type': 'conversation',
                    'data': conv_dict
                })
            
            # Process interactions
            for interaction in interactions:
                chat_history.append({
                    'type': 'interaction',
                    'data': dict(interaction)
                })
            
            # Sort by timestamp
            chat_history.sort(key=lambda x: x['data'].get('created_at', datetime.min), reverse=True)
            
            return chat_history[:limit]
            
        except Exception as e:
            logger.error(f"Error getting chat history: {str(e)}")
            raise
    
    async def get_purchase_history(self, user_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Get user's purchase history"""
        try:
            query = """
                SELECT 
                    o.id,
                    o.order_number,
                    o.items,
                    o.subtotal,
                    o.tax_amount,
                    o.discount_amount,
                    o.delivery_fee,
                    o.total_amount,
                    o.status,
                    o.payment_status,
                    o.payment_method,
                    o.delivery_method,
                    o.delivery_address,
                    o.created_at,
                    o.completed_at
                FROM orders o
                WHERE o.user_id = $1 OR o.user_profile_id = $1
                ORDER BY o.created_at DESC
                LIMIT $2
            """
            
            orders = await self.db.fetch(query, user_id, limit)
            
            purchase_history = []
            for order in orders:
                order_dict = dict(order)
                # Convert Decimal to float for JSON serialization
                for field in ['subtotal', 'tax_amount', 'discount_amount', 'delivery_fee', 'total_amount']:
                    if order_dict.get(field):
                        order_dict[field] = float(order_dict[field])
                
                # Parse items JSONB
                if order_dict.get('items'):
                    if isinstance(order_dict['items'], str):
                        order_dict['items'] = json.loads(order_dict['items'])
                
                purchase_history.append(order_dict)
            
            return purchase_history
            
        except Exception as e:
            logger.error(f"Error getting purchase history: {str(e)}")
            raise
    
    async def get_conversation_context(self, session_id: str) -> Dict[str, Any]:
        """Get current conversation context for a session"""
        try:
            query = """
                SELECT 
                    session_id,
                    customer_id,
                    messages,
                    context,
                    created_at,
                    updated_at
                FROM ai_conversations
                WHERE session_id = $1
                ORDER BY updated_at DESC
                LIMIT 1
            """
            
            result = await self.db.fetchrow(query, session_id)
            if result:
                context = dict(result)
                if context.get('messages'):
                    if isinstance(context['messages'], str):
                        context['messages'] = json.loads(context['messages'])
                if context.get('context'):
                    if isinstance(context['context'], str):
                        context['context'] = json.loads(context['context'])
                return context
            return {}
            
        except Exception as e:
            logger.error(f"Error getting conversation context: {str(e)}")
            raise
    
    async def get_user_preferences(self, user_id: str) -> Dict[str, Any]:
        """Get user preferences and behavior patterns"""
        try:
            # Get user profile preferences
            profile_query = """
                SELECT
                    preferences,
                    loyalty_points
                FROM profiles
                WHERE user_id = $1
            """
            
            profile = await self.db.fetchrow(profile_query, user_id)
            
            # Analyze purchase patterns
            patterns_query = """
                SELECT 
                    COUNT(*) as total_orders,
                    AVG(total_amount) as avg_order_value,
                    MAX(created_at) as last_order_date,
                    COUNT(DISTINCT DATE(created_at)) as order_days
                FROM orders
                WHERE user_id = $1
                AND status != 'cancelled'
            """
            
            patterns = await self.db.fetchrow(patterns_query, user_id)
            
            # Get frequently purchased items
            frequent_items_query = """
                SELECT 
                    item->>'product_id' as product_id,
                    item->>'product_name' as product_name,
                    COUNT(*) as purchase_count,
                    SUM((item->>'quantity')::int) as total_quantity
                FROM orders o,
                     jsonb_array_elements(o.items) as item
                WHERE o.user_id = $1
                AND o.status != 'cancelled'
                GROUP BY item->>'product_id', item->>'product_name'
                ORDER BY purchase_count DESC
                LIMIT 10
            """
            
            frequent_items = await self.db.fetch(frequent_items_query, user_id)
            
            preferences = {
                'profile': dict(profile) if profile else {},
                'purchase_patterns': dict(patterns) if patterns else {},
                'frequent_items': [dict(item) for item in frequent_items]
            }
            
            # Convert Decimal to float
            if preferences['purchase_patterns'].get('avg_order_value'):
                preferences['purchase_patterns']['avg_order_value'] = float(
                    preferences['purchase_patterns']['avg_order_value']
                )
            
            return preferences
            
        except Exception as e:
            logger.error(f"Error getting user preferences: {str(e)}")
            raise
    
    async def get_complete_user_context(self, user_id: str, session_id: Optional[str] = None) -> Dict[str, Any]:
        """Get complete user context for AI model"""
        try:
            logger.info(f"[UserContextService] Starting complete context fetch for User ID: {user_id}, Session ID: {session_id}")

            # Fetch all context components
            logger.info(f"[UserContextService] Fetching user profile...")
            user_profile = await self.get_user_profile(user_id)
            logger.info(f"[UserContextService] User profile fetched: {bool(user_profile)}")

            logger.info(f"[UserContextService] Fetching user preferences...")
            preferences = await self.get_user_preferences(user_id)
            logger.info(f"[UserContextService] Preferences fetched: {bool(preferences)}")

            logger.info(f"[UserContextService] Fetching chat history...")
            chat_history = await self.get_chat_history(user_id, limit=20, days_back=7)
            logger.info(f"[UserContextService] Chat history fetched: {len(chat_history)} messages")

            logger.info(f"[UserContextService] Fetching purchase history...")
            purchase_history = await self.get_purchase_history(user_id, limit=10)
            logger.info(f"[UserContextService] Purchase history fetched: {len(purchase_history)} orders")

            context = {
                'user_profile': user_profile,
                'preferences': preferences,
                'recent_chat_history': chat_history,
                'recent_purchases': purchase_history
            }
            
            if session_id:
                logger.info(f"[UserContextService] Fetching conversation context for session: {session_id}")
                context['conversation_context'] = await self.get_conversation_context(session_id)
                logger.info(f"[UserContextService] Conversation context fetched: {bool(context.get('conversation_context'))}")
            
            # Add summary statistics
            if context['user_profile']:
                context['summary'] = {
                    'is_verified': context['user_profile'].get('age_verified', False),
                    'age': context['user_profile'].get('age'),
                    'member_since': context['user_profile'].get('created_at'),
                    'total_conversations': len(context['recent_chat_history']),
                    'total_purchases': len(context['recent_purchases'])
                }
            
            logger.info(f"[UserContextService] Complete context built successfully for User ID: {user_id}")
            return context

        except Exception as e:
            logger.error(f"[UserContextService] Error getting complete user context: {str(e)}")
            logger.exception("[UserContextService] Full stack trace:")
            raise
    
    async def save_conversation_message(self, session_id: str, user_id: str, 
                                       user_message: str, ai_response: str, 
                                       intent: Optional[str] = None,
                                       metadata: Optional[Dict] = None) -> bool:
        """Save a conversation message"""
        try:
            # Save to chat_interactions
            query = """
                INSERT INTO chat_interactions
                (session_id, customer_id, user_message, ai_response, intent, 
                 response_time, created_at, metadata)
                VALUES ($1, $2, $3, $4, $5, $6, CURRENT_TIMESTAMP, $7)
            """
            
            response_time = 0.0  # You can calculate actual response time
            await self.db.execute(
                query,
                session_id, user_id, user_message, ai_response,
                intent, response_time, json.dumps(metadata) if metadata else None
            )

            # Prepare message and context JSON
            message_json = json.dumps([{
                'role': 'user',
                'content': user_message,
                'timestamp': datetime.now().isoformat()
            }, {
                'role': 'assistant',
                'content': ai_response,
                'timestamp': datetime.now().isoformat()
            }])

            context_json = json.dumps(metadata) if metadata else '{}'

            # First check if conversation exists
            check_query = """
                SELECT conversation_id FROM ai_conversations
                WHERE session_id = $1
            """
            existing = await self.db.fetchrow(check_query, session_id)

            if existing:
                # Update existing conversation
                conv_query = """
                    UPDATE ai_conversations
                    SET messages = messages || $1,
                        context = $2,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE session_id = $3
                """
                await self.db.execute(conv_query, message_json, context_json, session_id)
            else:
                # Create new conversation
                conv_query = """
                    INSERT INTO ai_conversations (conversation_id, session_id, customer_id, messages, context, created_at, updated_at)
                    VALUES (gen_random_uuid(), $1, $2, $3, $4, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                """
                await self.db.execute(conv_query, session_id, user_id, message_json, context_json)
            
            return True
            
        except Exception as e:
            logger.error(f"Error saving conversation message: {str(e)}")
            return False