"""
Recipient Segmentation Service
Handles customer segmentation and filtering for targeted broadcast campaigns
"""

import logging
from typing import Dict, List, Optional, Any, Set
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
import json
import uuid

logger = logging.getLogger(__name__)


class SegmentOperator(Enum):
    """Operators for segment criteria"""
    EQUALS = "equals"
    NOT_EQUALS = "not_equals"
    GREATER_THAN = "greater_than"
    LESS_THAN = "less_than"
    GREATER_OR_EQUAL = "greater_or_equal"
    LESS_OR_EQUAL = "less_or_equal"
    CONTAINS = "contains"
    NOT_CONTAINS = "not_contains"
    IN = "in"
    NOT_IN = "not_in"
    BETWEEN = "between"
    IS_NULL = "is_null"
    IS_NOT_NULL = "is_not_null"


@dataclass
class SegmentCriteria:
    """Single segmentation criterion"""
    field: str
    operator: SegmentOperator
    value: Any
    data_type: str = "string"  # string, number, date, boolean, array


@dataclass
class SegmentGroup:
    """Group of criteria with logical operator"""
    criteria: List[SegmentCriteria]
    logic: str = "AND"  # AND or OR


class SegmentationService:
    """
    Service for customer segmentation and filtering
    Supports complex criteria for targeted messaging
    """

    def __init__(self, db_pool):
        self.db_pool = db_pool

        # Predefined segments
        self.predefined_segments = {
            "all_customers": {
                "name": "All Customers",
                "description": "All registered customers",
                "criteria": []
            },
            "new_customers": {
                "name": "New Customers",
                "description": "Customers registered in the last 30 days",
                "criteria": [
                    {
                        "field": "created_at",
                        "operator": "greater_than",
                        "value": "NOW() - INTERVAL '30 days'",
                        "data_type": "date"
                    }
                ]
            },
            "vip_customers": {
                "name": "VIP Customers",
                "description": "High-value customers",
                "criteria": [
                    {
                        "field": "total_spent",
                        "operator": "greater_than",
                        "value": 1000,
                        "data_type": "number"
                    }
                ]
            },
            "active_customers": {
                "name": "Active Customers",
                "description": "Customers with recent purchases",
                "criteria": [
                    {
                        "field": "last_purchase_date",
                        "operator": "greater_than",
                        "value": "NOW() - INTERVAL '90 days'",
                        "data_type": "date"
                    }
                ]
            },
            "dormant_customers": {
                "name": "Dormant Customers",
                "description": "Customers without recent activity",
                "criteria": [
                    {
                        "field": "last_purchase_date",
                        "operator": "less_than",
                        "value": "NOW() - INTERVAL '180 days'",
                        "data_type": "date"
                    }
                ]
            },
            "birthday_this_month": {
                "name": "Birthday This Month",
                "description": "Customers with birthdays this month",
                "criteria": [
                    {
                        "field": "EXTRACT(MONTH FROM date_of_birth)",
                        "operator": "equals",
                        "value": "EXTRACT(MONTH FROM NOW())",
                        "data_type": "sql_expression"
                    }
                ]
            },
            "high_frequency_buyers": {
                "name": "High Frequency Buyers",
                "description": "Customers who purchase frequently",
                "criteria": [
                    {
                        "field": "order_count",
                        "operator": "greater_than",
                        "value": 10,
                        "data_type": "number"
                    }
                ]
            },
            "email_subscribers": {
                "name": "Email Subscribers",
                "description": "Customers opted in for email",
                "criteria": [
                    {
                        "field": "email",
                        "operator": "is_not_null",
                        "value": None,
                        "data_type": "boolean"
                    },
                    {
                        "field": "email_opt_in",
                        "operator": "equals",
                        "value": True,
                        "data_type": "boolean"
                    }
                ]
            },
            "sms_subscribers": {
                "name": "SMS Subscribers",
                "description": "Customers opted in for SMS",
                "criteria": [
                    {
                        "field": "phone_number",
                        "operator": "is_not_null",
                        "value": None,
                        "data_type": "boolean"
                    },
                    {
                        "field": "sms_opt_in",
                        "operator": "equals",
                        "value": True,
                        "data_type": "boolean"
                    }
                ]
            },
            "push_enabled": {
                "name": "Push Notification Enabled",
                "description": "Customers with push tokens",
                "criteria": [
                    {
                        "field": "push_token",
                        "operator": "is_not_null",
                        "value": None,
                        "data_type": "boolean"
                    }
                ]
            }
        }

    async def get_segment_recipients(
        self,
        store_id: str,
        tenant_id: str,
        segment_id: Optional[str] = None,
        criteria: Optional[Dict[str, Any]] = None,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Get recipients based on segment or custom criteria

        Args:
            store_id: Store ID for filtering
            tenant_id: Tenant ID for filtering
            segment_id: Predefined segment ID
            criteria: Custom segmentation criteria
            limit: Optional limit on results

        Returns:
            List of recipient records
        """
        async with self.db_pool.acquire() as conn:
            # Build base query
            query = """
                SELECT DISTINCT
                    c.id::text as customer_id,
                    c.email,
                    c.phone_number,
                    c.name,
                    c.date_of_birth,
                    c.created_at,
                    c.metadata,
                    COALESCE(cs.total_spent, 0) as total_spent,
                    COALESCE(cs.order_count, 0) as order_count,
                    cs.last_purchase_date,
                    cs.average_order_value,
                    cp.channel_email as email_opt_in,
                    cp.channel_sms as sms_opt_in,
                    cp.channel_push as push_opt_in,
                    ps.device_token as push_token
                FROM customers c
                LEFT JOIN (
                    SELECT
                        customer_id,
                        SUM(total_amount) as total_spent,
                        COUNT(*) as order_count,
                        MAX(created_at) as last_purchase_date,
                        AVG(total_amount) as average_order_value
                    FROM orders
                    WHERE store_id = $1
                    GROUP BY customer_id
                ) cs ON c.id::text = cs.customer_id
                LEFT JOIN communication_preferences cp ON c.id::text = cp.customer_id
                LEFT JOIN push_subscriptions ps ON c.id::text = ps.customer_id AND ps.is_active = true
                WHERE 1=1
            """

            params = [uuid.UUID(store_id)]

            # Add tenant filter if provided
            if tenant_id:
                query += " AND EXISTS (SELECT 1 FROM stores s WHERE s.id = $1 AND s.tenant_id = $2)"
                params.append(uuid.UUID(tenant_id))

            # Apply segment or criteria
            if segment_id and segment_id in self.predefined_segments:
                segment_criteria = self.predefined_segments[segment_id]["criteria"]
                where_clause = self._build_where_clause(segment_criteria)
                if where_clause:
                    query += f" AND ({where_clause})"

            elif criteria:
                where_clause = self._build_where_clause(criteria)
                if where_clause:
                    query += f" AND ({where_clause})"

            # Add ordering
            query += " ORDER BY c.created_at DESC"

            # Add limit if specified
            if limit:
                query += f" LIMIT {limit}"

            # Execute query
            recipients = await conn.fetch(query, *params)

            return [dict(r) for r in recipients]

    async def get_segment_count(
        self,
        store_id: str,
        tenant_id: str,
        segment_id: Optional[str] = None,
        criteria: Optional[Dict[str, Any]] = None
    ) -> int:
        """
        Get count of recipients in a segment

        Args:
            store_id: Store ID
            tenant_id: Tenant ID
            segment_id: Predefined segment ID
            criteria: Custom criteria

        Returns:
            Count of recipients
        """
        async with self.db_pool.acquire() as conn:
            # Similar to get_segment_recipients but with COUNT
            query = """
                SELECT COUNT(DISTINCT c.id) as count
                FROM customers c
                LEFT JOIN (
                    SELECT
                        customer_id,
                        SUM(total_amount) as total_spent,
                        COUNT(*) as order_count,
                        MAX(created_at) as last_purchase_date
                    FROM orders
                    WHERE store_id = $1
                    GROUP BY customer_id
                ) cs ON c.id::text = cs.customer_id
                LEFT JOIN communication_preferences cp ON c.id::text = cp.customer_id
                WHERE 1=1
            """

            params = [uuid.UUID(store_id)]

            if tenant_id:
                query += " AND EXISTS (SELECT 1 FROM stores s WHERE s.id = $1 AND s.tenant_id = $2)"
                params.append(uuid.UUID(tenant_id))

            if segment_id and segment_id in self.predefined_segments:
                segment_criteria = self.predefined_segments[segment_id]["criteria"]
                where_clause = self._build_where_clause(segment_criteria)
                if where_clause:
                    query += f" AND ({where_clause})"

            elif criteria:
                where_clause = self._build_where_clause(criteria)
                if where_clause:
                    query += f" AND ({where_clause})"

            result = await conn.fetchval(query, *params)
            return result or 0

    def _build_where_clause(
        self,
        criteria: Any
    ) -> str:
        """Build SQL WHERE clause from criteria"""
        if isinstance(criteria, list):
            # List of criteria with AND logic
            clauses = []
            for criterion in criteria:
                clause = self._build_single_criterion(criterion)
                if clause:
                    clauses.append(clause)
            return " AND ".join(clauses) if clauses else ""

        elif isinstance(criteria, dict):
            if "groups" in criteria:
                # Complex criteria with groups
                return self._build_grouped_criteria(criteria)
            else:
                # Single criterion
                return self._build_single_criterion(criteria)

        return ""

    def _build_single_criterion(
        self,
        criterion: Dict[str, Any]
    ) -> str:
        """Build SQL for a single criterion"""
        field = criterion.get("field")
        operator = criterion.get("operator")
        value = criterion.get("value")
        data_type = criterion.get("data_type", "string")

        if not field or not operator:
            return ""

        # Map field names to SQL columns
        field_mapping = {
            "created_at": "c.created_at",
            "email": "c.email",
            "phone_number": "c.phone_number",
            "name": "c.name",
            "date_of_birth": "c.date_of_birth",
            "total_spent": "cs.total_spent",
            "order_count": "cs.order_count",
            "last_purchase_date": "cs.last_purchase_date",
            "average_order_value": "cs.average_order_value",
            "email_opt_in": "cp.channel_email",
            "sms_opt_in": "cp.channel_sms",
            "push_opt_in": "cp.channel_push",
            "push_token": "ps.device_token"
        }

        # Use mapped field or original if not in mapping (for SQL expressions)
        sql_field = field_mapping.get(field, field)

        # Handle different operators
        if operator == "equals":
            if data_type == "string":
                return f"{sql_field} = '{value}'"
            elif data_type == "number":
                return f"{sql_field} = {value}"
            elif data_type == "boolean":
                return f"{sql_field} = {value}"
            elif data_type == "sql_expression":
                return f"{sql_field} = {value}"

        elif operator == "not_equals":
            if data_type == "string":
                return f"{sql_field} != '{value}'"
            else:
                return f"{sql_field} != {value}"

        elif operator == "greater_than":
            if data_type == "date":
                return f"{sql_field} > {value}"
            else:
                return f"{sql_field} > {value}"

        elif operator == "less_than":
            if data_type == "date":
                return f"{sql_field} < {value}"
            else:
                return f"{sql_field} < {value}"

        elif operator == "greater_or_equal":
            return f"{sql_field} >= {value}"

        elif operator == "less_or_equal":
            return f"{sql_field} <= {value}"

        elif operator == "contains":
            return f"{sql_field} LIKE '%{value}%'"

        elif operator == "not_contains":
            return f"{sql_field} NOT LIKE '%{value}%'"

        elif operator == "in":
            if isinstance(value, list):
                values = ", ".join([f"'{v}'" if isinstance(v, str) else str(v) for v in value])
                return f"{sql_field} IN ({values})"

        elif operator == "not_in":
            if isinstance(value, list):
                values = ", ".join([f"'{v}'" if isinstance(v, str) else str(v) for v in value])
                return f"{sql_field} NOT IN ({values})"

        elif operator == "between":
            if isinstance(value, list) and len(value) == 2:
                return f"{sql_field} BETWEEN {value[0]} AND {value[1]}"

        elif operator == "is_null":
            return f"{sql_field} IS NULL"

        elif operator == "is_not_null":
            return f"{sql_field} IS NOT NULL"

        return ""

    def _build_grouped_criteria(
        self,
        criteria: Dict[str, Any]
    ) -> str:
        """Build SQL for grouped criteria with AND/OR logic"""
        groups = criteria.get("groups", [])
        group_logic = criteria.get("group_logic", "AND")

        group_clauses = []
        for group in groups:
            group_criteria = group.get("criteria", [])
            logic = group.get("logic", "AND")

            clauses = []
            for criterion in group_criteria:
                clause = self._build_single_criterion(criterion)
                if clause:
                    clauses.append(clause)

            if clauses:
                if logic == "OR":
                    group_clauses.append(f"({' OR '.join(clauses)})")
                else:
                    group_clauses.append(f"({' AND '.join(clauses)})")

        if group_logic == "OR":
            return " OR ".join(group_clauses)
        else:
            return " AND ".join(group_clauses)

    async def save_custom_segment(
        self,
        name: str,
        description: str,
        store_id: str,
        tenant_id: str,
        criteria: Dict[str, Any],
        created_by: str
    ) -> str:
        """
        Save a custom segment for reuse

        Args:
            name: Segment name
            description: Segment description
            store_id: Store ID
            tenant_id: Tenant ID
            criteria: Segment criteria
            created_by: User ID

        Returns:
            Segment ID
        """
        async with self.db_pool.acquire() as conn:
            segment_id = await conn.fetchval("""
                INSERT INTO custom_segments (
                    name, description, store_id, tenant_id,
                    criteria, created_by, created_at
                ) VALUES ($1, $2, $3, $4, $5, $6, NOW())
                RETURNING id
            """, name, description, uuid.UUID(store_id),
                uuid.UUID(tenant_id), json.dumps(criteria),
                uuid.UUID(created_by))

            return str(segment_id)

    async def get_custom_segments(
        self,
        store_id: str,
        tenant_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get all custom segments for a store"""
        async with self.db_pool.acquire() as conn:
            query = """
                SELECT
                    id, name, description, criteria,
                    created_by, created_at, updated_at
                FROM custom_segments
                WHERE store_id = $1
            """
            params = [uuid.UUID(store_id)]

            if tenant_id:
                query += " AND tenant_id = $2"
                params.append(uuid.UUID(tenant_id))

            query += " ORDER BY created_at DESC"

            segments = await conn.fetch(query, *params)
            return [dict(s) for s in segments]

    async def analyze_segment(
        self,
        store_id: str,
        segment_id: Optional[str] = None,
        criteria: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Analyze a segment for insights

        Args:
            store_id: Store ID
            segment_id: Segment ID
            criteria: Custom criteria

        Returns:
            Segment analytics
        """
        recipients = await self.get_segment_recipients(
            store_id, None, segment_id, criteria
        )

        if not recipients:
            return {
                "total_count": 0,
                "channels": {},
                "demographics": {},
                "behavior": {}
            }

        # Calculate analytics
        total = len(recipients)
        email_count = sum(1 for r in recipients if r.get("email"))
        sms_count = sum(1 for r in recipients if r.get("phone_number"))
        push_count = sum(1 for r in recipients if r.get("push_token"))

        # Calculate averages
        total_spent_sum = sum(r.get("total_spent", 0) for r in recipients)
        order_count_sum = sum(r.get("order_count", 0) for r in recipients)

        # Age demographics
        age_groups = {"18-24": 0, "25-34": 0, "35-44": 0, "45-54": 0, "55+": 0}
        for r in recipients:
            if r.get("date_of_birth"):
                age = (datetime.now().date() - r["date_of_birth"]).days // 365
                if age < 25:
                    age_groups["18-24"] += 1
                elif age < 35:
                    age_groups["25-34"] += 1
                elif age < 45:
                    age_groups["35-44"] += 1
                elif age < 55:
                    age_groups["45-54"] += 1
                else:
                    age_groups["55+"] += 1

        return {
            "total_count": total,
            "channels": {
                "email": {
                    "count": email_count,
                    "percentage": (email_count / total * 100) if total > 0 else 0
                },
                "sms": {
                    "count": sms_count,
                    "percentage": (sms_count / total * 100) if total > 0 else 0
                },
                "push": {
                    "count": push_count,
                    "percentage": (push_count / total * 100) if total > 0 else 0
                }
            },
            "demographics": {
                "age_groups": age_groups
            },
            "behavior": {
                "average_spent": total_spent_sum / total if total > 0 else 0,
                "average_orders": order_count_sum / total if total > 0 else 0,
                "total_revenue_potential": total_spent_sum
            }
        }

    def get_predefined_segments(self) -> List[Dict[str, Any]]:
        """Get list of predefined segments"""
        return [
            {
                "id": key,
                "name": value["name"],
                "description": value["description"]
            }
            for key, value in self.predefined_segments.items()
        ]