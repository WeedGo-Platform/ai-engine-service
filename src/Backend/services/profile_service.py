"""
Profile Service - Unified User Profile Management
Replaces the old CustomerService with unified model
"""

import asyncpg
import logging
from typing import Dict, List, Any, Optional
from uuid import UUID
from datetime import datetime
from decimal import Decimal
import json

logger = logging.getLogger(__name__)


class ProfileService:
    """Service for unified user profile management"""

    def __init__(self, db_connection):
        """Initialize with database connection"""
        self.db = db_connection

    async def get_or_create_profile(self, user_id: UUID) -> Dict[str, Any]:
        """Get existing profile or create a new one for a user"""
        try:
            # First try to get existing profile
            profile = await self.get_profile_by_user_id(user_id)
            if profile:
                return profile

            # Create new profile if doesn't exist
            query = """
                INSERT INTO profiles (user_id)
                VALUES ($1)
                RETURNING *
            """

            result = await self.db.fetchrow(query, user_id)
            return dict(result) if result else None

        except Exception as e:
            logger.error(f"Error getting/creating profile: {e}")
            raise

    async def get_profile_by_user_id(self, user_id: UUID) -> Optional[Dict[str, Any]]:
        """Get profile by user ID"""
        try:
            query = """
                SELECT p.*, u.email, u.role, u.tenant_id, u.active
                FROM profiles p
                JOIN users u ON p.user_id = u.id
                WHERE p.user_id = $1
            """

            result = await self.db.fetchrow(query, user_id)
            return dict(result) if result else None

        except Exception as e:
            logger.error(f"Error fetching profile: {e}")
            return None

    async def update_profile(self, user_id: UUID, profile_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update user profile"""
        try:
            # Build dynamic UPDATE query
            update_fields = []
            values = []
            idx = 2  # Start at $2 since $1 is user_id

            allowed_fields = [
                'first_name', 'last_name', 'phone', 'date_of_birth',
                'address', 'city', 'state', 'postal_code', 'country',
                'customer_type', 'preferred_payment_method',
                'preferences', 'needs', 'experience_level',
                'medical_conditions', 'preferred_categories',
                'preferred_effects', 'price_range',
                'marketing_consent', 'sms_consent',
                'tags', 'notes', 'language', 'timezone'
            ]

            for field in allowed_fields:
                if field in profile_data:
                    update_fields.append(f"{field} = ${idx}")

                    # Handle JSONB fields
                    if field in ['preferences', 'needs', 'medical_conditions',
                               'preferred_categories', 'preferred_effects',
                               'price_range', 'tags', 'purchase_history']:
                        values.append(json.dumps(profile_data[field]) if profile_data[field] else '{}')
                    else:
                        values.append(profile_data[field])
                    idx += 1

            if not update_fields:
                return await self.get_profile_by_user_id(user_id)

            update_fields.append(f"updated_at = CURRENT_TIMESTAMP")

            query = f"""
                UPDATE profiles
                SET {', '.join(update_fields)}
                WHERE user_id = $1
                RETURNING *
            """

            result = await self.db.fetchrow(query, user_id, *values)
            return dict(result) if result else None

        except Exception as e:
            logger.error(f"Error updating profile: {e}")
            raise

    async def search_profiles(self,
                            search_term: Optional[str] = None,
                            customer_type: Optional[str] = None,
                            limit: int = 50,
                            offset: int = 0) -> List[Dict[str, Any]]:
        """Search profiles with filters"""
        try:
            conditions = ["1=1"]
            values = []
            idx = 1

            if search_term:
                conditions.append(f"""
                    (p.first_name ILIKE ${idx} OR
                     p.last_name ILIKE ${idx} OR
                     u.email ILIKE ${idx} OR
                     p.phone ILIKE ${idx})
                """)
                values.append(f"%{search_term}%")
                idx += 1

            if customer_type:
                conditions.append(f"p.customer_type = ${idx}")
                values.append(customer_type)
                idx += 1

            query = f"""
                SELECT
                    p.*,
                    u.email,
                    u.role,
                    u.tenant_id,
                    u.active,
                    u.last_login
                FROM profiles p
                JOIN users u ON p.user_id = u.id
                WHERE {' AND '.join(conditions)}
                ORDER BY p.created_at DESC
                LIMIT ${idx} OFFSET ${idx + 1}
            """

            values.extend([limit, offset])

            results = await self.db.fetch(query, *values)
            return [dict(row) for row in results]

        except Exception as e:
            logger.error(f"Error searching profiles: {e}")
            return []

    async def update_loyalty_points(self, user_id: UUID, points_delta: int, reason: str) -> Dict[str, Any]:
        """Update loyalty points for a user"""
        try:
            # First ensure profile exists
            await self.get_or_create_profile(user_id)

            query = """
                UPDATE profiles
                SET
                    loyalty_points = loyalty_points + $2,
                    updated_at = CURRENT_TIMESTAMP
                WHERE user_id = $1
                RETURNING *
            """

            result = await self.db.fetchrow(query, user_id, points_delta)

            # Log the loyalty point change
            await self._log_loyalty_change(user_id, points_delta, reason)

            return dict(result) if result else None

        except Exception as e:
            logger.error(f"Error updating loyalty points: {e}")
            raise

    async def update_purchase_stats(self, user_id: UUID, order_total: Decimal) -> Dict[str, Any]:
        """Update purchase statistics after an order"""
        try:
            # First ensure profile exists
            await self.get_or_create_profile(user_id)

            query = """
                UPDATE profiles
                SET
                    total_spent = total_spent + $2,
                    order_count = order_count + 1,
                    last_order_date = CURRENT_TIMESTAMP,
                    updated_at = CURRENT_TIMESTAMP
                WHERE user_id = $1
                RETURNING *
            """

            result = await self.db.fetchrow(query, user_id, order_total)
            return dict(result) if result else None

        except Exception as e:
            logger.error(f"Error updating purchase stats: {e}")
            raise

    async def get_profile_analytics(self, user_id: UUID) -> Dict[str, Any]:
        """Get analytics data for a user profile"""
        try:
            profile = await self.get_profile_by_user_id(user_id)
            if not profile:
                return {}

            # Get order history
            order_query = """
                SELECT
                    COUNT(*) as total_orders,
                    COALESCE(SUM(total_amount), 0) as lifetime_value,
                    COALESCE(AVG(total_amount), 0) as avg_order_value,
                    MAX(created_at) as last_order_date
                FROM orders
                WHERE user_id = $1
            """

            order_stats = await self.db.fetchrow(order_query, user_id)

            return {
                'profile': profile,
                'order_stats': dict(order_stats) if order_stats else {},
                'loyalty_points': profile.get('loyalty_points', 0),
                'customer_type': profile.get('customer_type', 'regular'),
                'total_spent': float(profile.get('total_spent', 0)),
                'order_count': profile.get('order_count', 0)
            }

        except Exception as e:
            logger.error(f"Error getting profile analytics: {e}")
            return {}

    async def _log_loyalty_change(self, user_id: UUID, points_delta: int, reason: str):
        """Log loyalty point changes for audit trail"""
        try:
            # This could be a separate table for tracking loyalty history
            # For now, we'll just log it
            logger.info(f"Loyalty points changed for user {user_id}: {points_delta} points ({reason})")
        except Exception as e:
            logger.error(f"Error logging loyalty change: {e}")

