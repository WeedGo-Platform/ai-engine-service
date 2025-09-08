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
        """Create a new customer"""
        try:
            # Prepare data for customers table
            import json
            
            # Extract preferences data
            preferences = {}
            if customer_data.get('address'):
                preferences['address'] = customer_data['address']
            if customer_data.get('tags'):
                preferences['tags'] = customer_data['tags']
            if customer_data.get('notes'):
                preferences['notes'] = customer_data['notes']
            
            query = """
                INSERT INTO customers (
                    first_name, last_name, email, phone,
                    customer_type, medical_license, preferences,
                    loyalty_points, total_spent, order_count, status
                )
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
                RETURNING *
            """
            
            result = await self.db.fetchrow(
                query,
                customer_data.get('first_name'),
                customer_data.get('last_name'),
                customer_data['email'],
                customer_data.get('phone'),
                customer_data.get('customer_type', 'recreational'),
                customer_data.get('medical_license'),
                json.dumps(preferences) if preferences else None,
                0,  # Initial loyalty points
                0.0,  # Initial total spent
                0,  # Initial order count
                'active'  # Default status
            )
            
            return dict(result)
            
        except asyncpg.UniqueViolationError:
            raise ValueError(f"Customer with email {customer_data['email']} already exists")
        except Exception as e:
            logger.error(f"Error creating customer: {str(e)}")
            raise
    
    async def get_customer(self, customer_id: UUID) -> Optional[Dict[str, Any]]:
        """Get customer by ID"""
        try:
            query = """
                SELECT c.*, u.email_verified, u.terms_accepted
                FROM customers c
                LEFT JOIN users u ON c.user_id = u.id
                WHERE c.id = $1
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
            import json
            
            # Build update clauses
            set_clauses = []
            params = []
            param_count = 1
            
            # Direct customer fields
            customer_fields = ['first_name', 'last_name', 'email', 'phone', 
                             'customer_type', 'medical_license']
            
            # Handle status field mapping
            if 'is_active' in update_data:
                update_data['status'] = 'active' if update_data['is_active'] else 'inactive'
                del update_data['is_active']
            
            for field, value in update_data.items():
                if field in customer_fields:
                    set_clauses.append(f"{field} = ${param_count}")
                    params.append(value)
                    param_count += 1
                elif field == 'status':
                    set_clauses.append(f"status = ${param_count}")
                    params.append(value)
                    param_count += 1
                elif field in ['address', 'tags', 'notes']:
                    # Update preferences JSONB field
                    if 'preferences' not in [c.split(' = ')[0] for c in set_clauses]:
                        # Get current preferences first
                        current = await self.db.fetchrow(
                            "SELECT preferences FROM customers WHERE id = $1",
                            customer_id
                        )
                        prefs = current['preferences'] if current and current['preferences'] else {}
                        prefs[field] = value
                        set_clauses.append(f"preferences = ${param_count}")
                        params.append(json.dumps(prefs))
                        param_count += 1
            
            if not set_clauses:
                return True  # Nothing to update
            
            params.append(customer_id)
            query = f"""
                UPDATE customers
                SET {', '.join(set_clauses)}, updated_at = CURRENT_TIMESTAMP
                WHERE id = ${param_count}
            """
            
            result = await self.db.execute(query, *params)
            return result != "UPDATE 0"
            
        except Exception as e:
            logger.error(f"Error updating customer: {str(e)}")
            raise
    
    async def delete_customer(self, customer_id: UUID) -> bool:
        """Soft delete a customer"""
        try:
            query = """
                UPDATE customers
                SET status = 'inactive', updated_at = CURRENT_TIMESTAMP
                WHERE id = $1
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
                SELECT c.*, u.email_verified, u.terms_accepted
                FROM customers c
                LEFT JOIN users u ON c.user_id = u.id
                WHERE 1=1
            """
            
            params = []
            param_count = 0
            
            if search:
                param_count += 1
                query += f""" AND (
                    c.first_name ILIKE ${param_count} OR 
                    c.last_name ILIKE ${param_count} OR 
                    c.email ILIKE ${param_count} OR
                    c.phone ILIKE ${param_count}
                )"""
                params.append(f"%{search}%")
            
            if is_active is not None:
                param_count += 1
                status = 'active' if is_active else 'inactive'
                query += f" AND c.status = ${param_count}"
                params.append(status)
            
            query += f" ORDER BY c.created_at DESC LIMIT ${param_count + 1} OFFSET ${param_count + 2}"
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
            # Get current points
            current = await self.db.fetchrow(
                "SELECT loyalty_points FROM customers WHERE id = $1",
                customer_id
            )
            
            if not current:
                raise ValueError("Customer not found")
            
            current_points = current['loyalty_points'] or 0
            new_points = max(0, current_points + points_change)  # Don't go negative
            
            # Update points
            await self.db.execute(
                """
                UPDATE customers
                SET loyalty_points = $1, updated_at = CURRENT_TIMESTAMP
                WHERE id = $2
                """,
                new_points,
                customer_id
            )
            
            return {"loyalty_points": new_points}
            
        except Exception as e:
            logger.error(f"Error updating loyalty points: {str(e)}")
            raise
    
    async def get_customer_stats(self, customer_id: UUID) -> Dict[str, Any]:
        """Get customer statistics"""
        try:
            # Get customer info from customers table
            customer_query = """
                SELECT 
                    created_at,
                    loyalty_points,
                    total_spent,
                    order_count
                FROM customers
                WHERE id = $1
            """
            
            customer = await self.db.fetchrow(customer_query, customer_id)
            
            if not customer:
                return None
            
            # Get recent order info
            orders_query = """
                SELECT 
                    COUNT(*) as recent_orders,
                    SUM(total_amount) as recent_spent
                FROM orders
                WHERE customer_id = $1 
                AND created_at > CURRENT_DATE - INTERVAL '30 days'
            """
            
            recent = await self.db.fetchrow(orders_query, customer_id)
            
            return {
                'loyalty_points': customer['loyalty_points'] or 0,
                'total_spent': float(customer['total_spent'] or 0),
                'total_orders': customer['order_count'] or 0,
                'recent_orders': recent['recent_orders'] or 0,
                'recent_spent': float(recent['recent_spent'] or 0),
                'member_since': customer['created_at'].isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting customer stats: {str(e)}")
            raise