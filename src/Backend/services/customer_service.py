"""
Customer Service - Now uses profiles table
Handles customer/profile management operations
"""

import asyncpg
import logging
from typing import Dict, List, Any, Optional
from uuid import UUID
from datetime import datetime
from decimal import Decimal

logger = logging.getLogger(__name__)


class CustomerService:
    """Service for customer/profile management operations using profiles table"""

    def __init__(self, db_connection):
        """Initialize with database connection"""
        self.db = db_connection

    async def create_customer(self, customer_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new customer profile"""
        try:
            # Prepare data for profiles table
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
                INSERT INTO profiles (
                    user_id, first_name, last_name, email, phone,
                    customer_type, medical_license, preferences,
                    loyalty_points, total_spent, order_count, is_verified
                )
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12)
                RETURNING *
            """

            result = await self.db.fetchrow(
                query,
                customer_data.get('user_id'),  # Required for profiles
                customer_data.get('first_name'),
                customer_data.get('last_name'),
                customer_data['email'],
                customer_data.get('phone'),
                customer_data.get('customer_type', 'recreational'),
                customer_data.get('medical_license'),
                json.dumps(preferences) if preferences else '{}',
                0,  # Initial loyalty points
                Decimal('0.0'),  # Initial total spent
                0,  # Initial order count
                customer_data.get('is_verified', False)
            )

            return dict(result)

        except asyncpg.UniqueViolationError:
            raise ValueError(f"Profile for user already exists")
        except Exception as e:
            logger.error(f"Error creating customer profile: {str(e)}")
            raise

    async def get_customer(self, customer_id: UUID) -> Optional[Dict[str, Any]]:
        """Get customer profile by ID"""
        try:
            query = """
                SELECT p.*, u.email_verified, u.terms_accepted
                FROM profiles p
                LEFT JOIN users u ON p.user_id = u.id
                WHERE p.id = $1
            """

            result = await self.db.fetchrow(query, customer_id)
            return dict(result) if result else None

        except Exception as e:
            logger.error(f"Error getting customer profile: {str(e)}")
            raise

    async def get_customer_by_user_id(self, user_id: UUID) -> Optional[Dict[str, Any]]:
        """Get customer profile by user ID"""
        try:
            query = """
                SELECT p.*, u.email_verified, u.terms_accepted
                FROM profiles p
                LEFT JOIN users u ON p.user_id = u.id
                WHERE p.user_id = $1
            """

            result = await self.db.fetchrow(query, user_id)
            return dict(result) if result else None

        except Exception as e:
            logger.error(f"Error getting customer profile by user_id: {str(e)}")
            raise

    async def update_customer(self, customer_id: UUID,
                            update_data: Dict[str, Any]) -> bool:
        """Update customer profile information"""
        try:
            import json

            # Build update clauses
            set_clauses = []
            params = []
            param_count = 1

            # Direct profile fields
            profile_fields = ['first_name', 'last_name', 'email', 'phone',
                             'customer_type', 'medical_license', 'is_verified']

            for field, value in update_data.items():
                if field in profile_fields:
                    set_clauses.append(f"{field} = ${param_count}")
                    params.append(value)
                    param_count += 1
                elif field in ['address', 'city', 'state', 'postal_code', 'country']:
                    # These are now direct fields in profiles
                    set_clauses.append(f"{field} = ${param_count}")
                    params.append(value)
                    param_count += 1
                elif field in ['tags', 'notes']:
                    # Update preferences JSONB field
                    if 'preferences' not in [c.split(' = ')[0] for c in set_clauses]:
                        # Get current preferences first
                        current = await self.db.fetchrow(
                            "SELECT preferences FROM profiles WHERE id = $1",
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
                UPDATE profiles
                SET {', '.join(set_clauses)}, updated_at = CURRENT_TIMESTAMP
                WHERE id = ${param_count}
            """

            result = await self.db.execute(query, *params)
            return result != "UPDATE 0"

        except Exception as e:
            logger.error(f"Error updating customer profile: {str(e)}")
            raise

    async def delete_customer(self, customer_id: UUID) -> bool:
        """Soft delete a customer profile"""
        try:
            query = """
                UPDATE profiles
                SET is_verified = false, updated_at = CURRENT_TIMESTAMP
                WHERE id = $1
            """

            result = await self.db.execute(query, customer_id)
            return result != "UPDATE 0"

        except Exception as e:
            logger.error(f"Error deleting customer profile: {str(e)}")
            raise

    async def list_customers(self, search: str = None,
                           is_active: bool = None,
                           limit: int = 50,
                           offset: int = 0) -> List[Dict[str, Any]]:
        """List customer profiles with optional filters"""
        try:
            query = """
                SELECT p.*, u.email_verified, u.terms_accepted
                FROM profiles p
                LEFT JOIN users u ON p.user_id = u.id
                WHERE 1=1
            """

            params = []
            param_count = 0

            if search:
                param_count += 1
                query += f""" AND (
                    p.first_name ILIKE ${param_count} OR
                    p.last_name ILIKE ${param_count} OR
                    p.email ILIKE ${param_count} OR
                    p.phone ILIKE ${param_count}
                )"""
                params.append(f"%{search}%")

            if is_active is not None:
                param_count += 1
                query += f" AND p.is_verified = ${param_count}"
                params.append(is_active)

            query += f" ORDER BY p.created_at DESC LIMIT ${param_count + 1} OFFSET ${param_count + 2}"
            params.extend([limit, offset])

            results = await self.db.fetch(query, *params)
            return [dict(row) for row in results]

        except Exception as e:
            logger.error(f"Error listing customer profiles: {str(e)}")
            raise

    async def get_customer_orders(self, customer_id: UUID) -> List[Dict[str, Any]]:
        """Get all orders for a customer"""
        try:
            # First get user_id from profile
            profile = await self.db.fetchrow(
                "SELECT user_id FROM profiles WHERE id = $1",
                customer_id
            )

            if not profile:
                return []

            query = """
                SELECT * FROM orders
                WHERE user_id = $1 OR customer_id = $2
                ORDER BY created_at DESC
            """

            results = await self.db.fetch(query, profile['user_id'], customer_id)
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
                "SELECT loyalty_points FROM profiles WHERE id = $1",
                customer_id
            )

            if not current:
                raise ValueError("Customer profile not found")

            current_points = current['loyalty_points'] or 0
            new_points = max(0, current_points + points_change)  # Don't go negative

            # Update points
            await self.db.execute(
                """
                UPDATE profiles
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
            # Get customer info from profiles table
            customer_query = """
                SELECT
                    created_at,
                    loyalty_points,
                    total_spent,
                    order_count
                FROM profiles
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