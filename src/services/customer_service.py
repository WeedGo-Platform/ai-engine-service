"""
Customer Service
Handles customer management operations
"""

import asyncpg
import logging
from typing import Dict, List, Any, Optional
from uuid import UUID
from datetime import datetime
from decimal import Decimal

logger = logging.getLogger(__name__)


class CustomerService:
    """Service for customer management operations"""
    
    def __init__(self, db_connection):
        """Initialize with database connection"""
        self.db = db_connection
    
    async def create_customer(self, customer_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new customer (user)"""
        try:
            # Insert into users table
            # Generate a placeholder password hash (in production, handle this properly)
            import hashlib
            password_hash = hashlib.sha256(f"temp_{customer_data['email']}".encode()).hexdigest()
            
            query = """
                INSERT INTO users (
                    first_name, last_name, email, phone, 
                    password_hash, role, active, email_verified, terms_accepted
                )
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                RETURNING *
            """
            
            result = await self.db.fetchrow(
                query,
                customer_data.get('first_name'),
                customer_data.get('last_name'),
                customer_data['email'],
                customer_data.get('phone'),
                password_hash,  # Temporary password hash
                'customer',  # Default role
                customer_data.get('is_active', True),
                False,  # email_verified default
                True   # terms_accepted default
            )
            
            user = dict(result)
            
            # Create customer profile if we have additional data
            if customer_data.get('address') or customer_data.get('tags') or customer_data.get('notes'):
                profile_query = """
                    INSERT INTO customer_profiles (
                        customer_id, preferences
                    )
                    VALUES ($1, $2)
                    ON CONFLICT (customer_id) DO UPDATE 
                    SET preferences = EXCLUDED.preferences,
                        updated_at = CURRENT_TIMESTAMP
                """
                
                preferences = {
                    'address': customer_data.get('address'),
                    'tags': customer_data.get('tags', []),
                    'notes': customer_data.get('notes')
                }
                
                import json
                await self.db.execute(
                    profile_query,
                    str(user['id']),
                    json.dumps(preferences)
                )
                
                user['preferences'] = preferences
            
            return user
            
        except asyncpg.UniqueViolationError:
            raise ValueError(f"Customer with email {customer_data['email']} already exists")
        except Exception as e:
            logger.error(f"Error creating customer: {str(e)}")
            raise
    
    async def get_customer(self, customer_id: UUID) -> Optional[Dict[str, Any]]:
        """Get customer by ID"""
        try:
            query = """
                SELECT u.*, cp.preferences 
                FROM users u
                LEFT JOIN customer_profiles cp ON cp.customer_id = u.id::text
                WHERE u.id = $1 AND u.role = 'customer'
            """
            
            result = await self.db.fetchrow(query, customer_id)
            return dict(result) if result else None
            
        except Exception as e:
            logger.error(f"Error getting customer: {str(e)}")
            raise
    
    async def update_customer(self, customer_id: UUID, 
                            update_data: Dict[str, Any]) -> bool:
        """Update customer information"""
        try:
            # Separate user fields from profile fields
            user_fields = ['first_name', 'last_name', 'email', 'phone', 'active']
            profile_data = {}
            user_updates = {}
            
            for field, value in update_data.items():
                if field in user_fields:
                    user_updates[field] = value
                elif field in ['address', 'tags', 'notes']:
                    profile_data[field] = value
            
            # Update users table if needed
            if user_updates:
                set_clauses = []
                params = []
                param_count = 1
                
                for field, value in user_updates.items():
                    set_clauses.append(f"{field} = ${param_count}")
                    params.append(value)
                    param_count += 1
                
                params.append(customer_id)
                query = f"""
                    UPDATE users
                    SET {', '.join(set_clauses)}, updated_at = CURRENT_TIMESTAMP
                    WHERE id = ${param_count} AND role = 'customer'
                """
                
                result = await self.db.execute(query, *params)
                
            # Update profile if needed
            if profile_data:
                import json
                await self.db.execute(
                    """
                    INSERT INTO customer_profiles (customer_id, preferences)
                    VALUES ($1, $2::jsonb)
                    ON CONFLICT (customer_id) DO UPDATE 
                    SET preferences = customer_profiles.preferences || $2::jsonb,
                        updated_at = CURRENT_TIMESTAMP
                    """,
                    str(customer_id),
                    json.dumps(profile_data)
                )
            
            return True
            
        except Exception as e:
            logger.error(f"Error updating customer: {str(e)}")
            raise
    
    async def delete_customer(self, customer_id: UUID) -> bool:
        """Soft delete a customer"""
        try:
            query = """
                UPDATE users
                SET active = false, updated_at = CURRENT_TIMESTAMP
                WHERE id = $1 AND role = 'customer'
            """
            
            result = await self.db.execute(query, customer_id)
            return result != "UPDATE 0"
            
        except Exception as e:
            logger.error(f"Error deleting customer: {str(e)}")
            raise
    
    async def list_customers(self, search: str = None, 
                           is_active: bool = None,
                           limit: int = 50,
                           offset: int = 0) -> List[Dict[str, Any]]:
        """List customers with optional filters"""
        try:
            query = """
                SELECT u.*, cp.preferences
                FROM users u
                LEFT JOIN customer_profiles cp ON cp.customer_id = u.id::text
                WHERE u.role = 'customer'
            """
            
            params = []
            param_count = 0
            
            if search:
                param_count += 1
                query += f""" AND (
                    u.first_name ILIKE ${param_count} OR 
                    u.last_name ILIKE ${param_count} OR 
                    u.email ILIKE ${param_count} OR
                    u.phone ILIKE ${param_count}
                )"""
                params.append(f"%{search}%")
            
            if is_active is not None:
                param_count += 1
                query += f" AND u.active = ${param_count}"
                params.append(is_active)
            
            query += f" ORDER BY u.created_at DESC LIMIT ${param_count + 1} OFFSET ${param_count + 2}"
            params.extend([limit, offset])
            
            results = await self.db.fetch(query, *params)
            return [dict(row) for row in results]
            
        except Exception as e:
            logger.error(f"Error listing customers: {str(e)}")
            raise
    
    async def get_customer_orders(self, customer_id: UUID) -> List[Dict[str, Any]]:
        """Get all orders for a customer"""
        try:
            query = """
                SELECT * FROM orders
                WHERE user_id = $1
                ORDER BY created_at DESC
            """
            
            results = await self.db.fetch(query, customer_id)
            return [dict(row) for row in results]
            
        except Exception as e:
            logger.error(f"Error getting customer orders: {str(e)}")
            raise
    
    async def update_loyalty_points(self, customer_id: UUID, 
                                   points_change: int) -> Dict[str, Any]:
        """Update customer loyalty points"""
        try:
            # Get current preferences
            profile = await self.db.fetchrow(
                "SELECT preferences FROM customer_profiles WHERE customer_id = $1",
                str(customer_id)
            )
            
            current_points = 0
            if profile and profile['preferences']:
                current_points = profile['preferences'].get('loyalty_points', 0)
            
            new_points = current_points + points_change
            
            # Update or create profile with new points
            import json
            await self.db.execute(
                """
                INSERT INTO customer_profiles (customer_id, preferences)
                VALUES ($1, $2::jsonb)
                ON CONFLICT (customer_id) DO UPDATE 
                SET preferences = customer_profiles.preferences || $2::jsonb,
                    updated_at = CURRENT_TIMESTAMP
                """,
                str(customer_id),
                json.dumps({'loyalty_points': new_points})
            )
            
            return {"loyalty_points": new_points}
            
        except Exception as e:
            logger.error(f"Error updating loyalty points: {str(e)}")
            raise
    
    async def get_customer_stats(self, customer_id: UUID) -> Dict[str, Any]:
        """Get customer statistics"""
        try:
            # Get customer basic info
            customer_query = """
                SELECT 
                    u.created_at,
                    cp.preferences
                FROM users u
                LEFT JOIN customer_profiles cp ON cp.customer_id = u.id::text
                WHERE u.id = $1 AND u.role = 'customer'
            """
            
            customer = await self.db.fetchrow(customer_query, customer_id)
            
            if not customer:
                return None
            
            # Extract stats from preferences
            preferences = customer.get('preferences', {}) or {}
            loyalty_points = preferences.get('loyalty_points', 0)
            total_spent = preferences.get('total_spent', 0)
            order_count = preferences.get('order_count', 0)
            
            # Get recent order info
            orders_query = """
                SELECT 
                    COUNT(*) as recent_orders,
                    SUM(total_amount) as recent_spent
                FROM orders
                WHERE user_id = $1 
                AND created_at > CURRENT_DATE - INTERVAL '30 days'
            """
            
            recent = await self.db.fetchrow(orders_query, customer_id)
            
            return {
                'loyalty_points': loyalty_points,
                'total_spent': float(total_spent),
                'total_orders': order_count,
                'recent_orders': recent['recent_orders'] or 0,
                'recent_spent': float(recent['recent_spent'] or 0),
                'member_since': customer['created_at'].isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting customer stats: {str(e)}")
            raise