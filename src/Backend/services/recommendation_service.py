"""
Product Recommendation Service
Provides intelligent product recommendations based on various factors
"""

from typing import List, Dict, Optional, Any
from datetime import datetime, timedelta
from decimal import Decimal
from uuid import UUID
import asyncpg
import logging
import json
import random
from collections import Counter

logger = logging.getLogger(__name__)


class RecommendationService:
    """Service for generating product recommendations"""
    
    def __init__(self, db_pool):
        """Initialize recommendation service with database connection pool"""
        self.db_pool = db_pool
    
    async def get_similar_products(
        self,
        product_id: str,
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """Get products similar to the given product"""
        async with self.db_pool.acquire() as conn:
            # Get the source product details
            source = await conn.fetchrow("""
                SELECT category, sub_category, strain_type, 
                       thc_max_percent as thc_percentage, cbd_max_percent as cbd_percentage, unit_price
                FROM product_catalog
                WHERE ocs_variant_number = $1
            """, product_id)
            
            if not source:
                return []
            
            # Find similar products based on category, strain, and cannabinoid content
            query = """
                SELECT 
                    ocs_variant_number as product_id,
                    product_name,
                    brand,
                    category,
                    strain_type,
                    thc_max_percent as thc_percentage,
                    cbd_max_percent as cbd_percentage,
                    unit_price,
                    image_url,
                    ABS(thc_max_percent - $4) as thc_diff,
                    ABS(cbd_max_percent - $5) as cbd_diff,
                    ABS(unit_price - $6) as price_diff
                FROM product_catalog
                WHERE ocs_variant_number != $1
                AND category = $2
                AND ($3 IS NULL OR strain_type = $3)
                ORDER BY 
                    thc_diff + cbd_diff + (price_diff / 10) ASC
                LIMIT $7
            """
            
            products = await conn.fetch(
                query,
                product_id,
                source['category'],
                source['strain_type'],
                source['thc_percentage'] or 0,
                source['cbd_percentage'] or 0,
                source['unit_price'] or 0,
                limit
            )
            
            # Store recommendations for future use
            for product in products:
                await self._store_recommendation(
                    conn,
                    product_id,
                    product['product_id'],
                    'similar',
                    0.8,  # High confidence for similar products
                    f"Similar {source['category']} product with comparable THC/CBD levels"
                )
            
            return [dict(p) for p in products]
    
    async def get_complementary_products(
        self,
        product_id: str,
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """Get products that complement the given product"""
        async with self.db_pool.acquire() as conn:
            # Get the source product category
            source = await conn.fetchrow("""
                SELECT category, sub_category
                FROM product_catalog
                WHERE ocs_variant_number = $1
            """, product_id)
            
            if not source:
                return []
            
            # Define complementary categories
            complements = {
                'Flower': ['Accessories', 'Vapes', 'Extracts'],
                'Pre-Roll': ['Accessories', 'Edibles'],
                'Vapes': ['Batteries', 'Accessories'],
                'Edibles': ['Beverages', 'CBD'],
                'Extracts': ['Accessories', 'Vapes'],
                'CBD': ['Topicals', 'Edibles']
            }
            
            complement_categories = complements.get(source['category'], [])
            
            if not complement_categories:
                return []
            
            # Find complementary products
            query = """
                SELECT 
                    ocs_variant_number as product_id,
                    product_name,
                    brand,
                    category,
                    unit_price,
                    image_url
                FROM product_catalog
                WHERE category = ANY($1)
                ORDER BY RANDOM()
                LIMIT $2
            """
            
            products = await conn.fetch(query, complement_categories, limit)
            
            # Store recommendations
            for product in products:
                await self._store_recommendation(
                    conn,
                    product_id,
                    product['product_id'],
                    'complementary',
                    0.7,
                    f"Pairs well with {source['category']} products"
                )
            
            return [dict(p) for p in products]
    
    async def get_trending_products(
        self,
        category: Optional[str] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Get trending products based on recent sales"""
        async with self.db_pool.acquire() as conn:
            # Get products with high recent activity
            # Since we don't have real sales data yet, we'll use inventory movements
            query = """
                SELECT 
                    pc.ocs_variant_number as product_id,
                    pc.product_name,
                    pc.brand,
                    pc.category,
                    pc.unit_price,
                    pc.image_url,
                    pc.thc_max_percent as thc_percentage,
                    pc.cbd_max_percent as cbd_percentage,
                    COUNT(im.id) as movement_count,
                    SUM(ABS(im.quantity)) as total_movement
                FROM product_catalog pc
                LEFT JOIN inventory_movements im ON pc.ocs_variant_number = im.sku
                    AND im.created_at > CURRENT_TIMESTAMP - INTERVAL '7 days'
                WHERE ($1::VARCHAR IS NULL OR pc.category = $1)
                GROUP BY pc.ocs_variant_number, pc.product_name, pc.brand, 
                         pc.category, pc.unit_price, pc.image_url,
                         pc.thc_max_percent, pc.cbd_max_percent
                ORDER BY movement_count DESC, total_movement DESC
                LIMIT $2
            """
            
            products = await conn.fetch(query, category, limit)
            
            # If no movements, get random popular categories
            if not products:
                query = """
                    SELECT 
                        ocs_variant_number as product_id,
                        product_name,
                        brand,
                        category,
                        unit_price,
                        image_url,
                        thc_max_percent as thc_percentage,
                        cbd_max_percent as cbd_percentage
                    FROM product_catalog
                    WHERE ($1::VARCHAR IS NULL OR category = $1)
                    AND category IN ('Flower', 'Pre-Roll', 'Vapes', 'Edibles')
                    ORDER BY RANDOM()
                    LIMIT $2
                """
                products = await conn.fetch(query, category, limit)
            
            return [dict(p) for p in products]
    
    async def get_personalized_recommendations(
        self,
        tenant_id: UUID,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Get personalized recommendations based on purchase history"""
        async with self.db_pool.acquire() as conn:
            # Get customer's purchase history categories
            query = """
                SELECT 
                    pc.category,
                    pc.strain_type,
                    AVG(pc.thc_max_percent) as avg_thc,
                    AVG(pc.cbd_max_percent) as avg_cbd,
                    COUNT(*) as purchase_count
                FROM purchase_order_items poi
                JOIN purchase_orders po ON poi.purchase_order_id = po.id
                JOIN product_catalog pc ON poi.sku = pc.ocs_variant_number
                WHERE po.tenant_id = $1
                GROUP BY pc.category, pc.strain_type
                ORDER BY purchase_count DESC
                LIMIT 5
            """
            
            preferences = await conn.fetch(query, tenant_id)
            
            if not preferences:
                # No history, return trending
                return await self.get_trending_products(limit=limit)
            
            # Get products matching preferences
            recommendations = []
            for pref in preferences:
                query = """
                    SELECT 
                        ocs_variant_number as product_id,
                        product_name,
                        brand,
                        category,
                        strain_type,
                        thc_max_percent as thc_percentage,
                        cbd_max_percent as cbd_percentage,
                        unit_price,
                        image_url
                    FROM product_catalog
                    WHERE category = $1
                    AND ($2 IS NULL OR strain_type = $2)
                    AND ($3 IS NULL OR ABS(thc_max_percent - $3) < 5)
                    AND ($4 IS NULL OR ABS(cbd_max_percent - $4) < 5)
                    ORDER BY RANDOM()
                    LIMIT $5
                """
                
                products = await conn.fetch(
                    query,
                    pref['category'],
                    pref['strain_type'],
                    pref['avg_thc'],
                    pref['avg_cbd'],
                    limit // len(preferences) + 1
                )
                
                recommendations.extend([dict(p) for p in products])
            
            # Remove duplicates and limit
            seen = set()
            unique_recommendations = []
            for rec in recommendations:
                if rec['product_id'] not in seen:
                    seen.add(rec['product_id'])
                    unique_recommendations.append(rec)
                    if len(unique_recommendations) >= limit:
                        break
            
            return unique_recommendations
    
    async def get_upsell_products(
        self,
        product_id: str,
        limit: int = 3
    ) -> List[Dict[str, Any]]:
        """Get higher-value alternatives to the given product"""
        async with self.db_pool.acquire() as conn:
            # Get the source product
            source = await conn.fetchrow("""
                SELECT category, sub_category, unit_price, thc_max_percent as thc_percentage
                FROM product_catalog
                WHERE ocs_variant_number = $1
            """, product_id)
            
            if not source:
                return []
            
            # Find similar but higher-priced products
            query = """
                SELECT 
                    ocs_variant_number as product_id,
                    product_name,
                    brand,
                    category,
                    unit_price,
                    image_url,
                    thc_max_percent as thc_percentage,
                    (unit_price - $3) as price_diff
                FROM product_catalog
                WHERE ocs_variant_number != $1
                AND category = $2
                AND unit_price > $3
                AND unit_price <= $3 * 1.5  -- Max 50% more expensive
                ORDER BY price_diff ASC
                LIMIT $4
            """
            
            products = await conn.fetch(
                query,
                product_id,
                source['category'],
                source['unit_price'] or 0,
                limit
            )
            
            # Store recommendations
            for product in products:
                await self._store_recommendation(
                    conn,
                    product_id,
                    product['product_id'],
                    'upsell',
                    0.6,
                    f"Premium {source['category']} option"
                )
            
            return [dict(p) for p in products]
    
    async def get_frequently_bought_together(
        self,
        product_id: str,
        limit: int = 3
    ) -> List[Dict[str, Any]]:
        """Get products frequently bought with the given product"""
        async with self.db_pool.acquire() as conn:
            # Check for existing recommendations
            query = """
                SELECT 
                    pr.recommended_product_id,
                    pc.product_name,
                    pc.brand,
                    pc.category,
                    pc.unit_price,
                    pc.image_url,
                    pr.score
                FROM product_recommendations pr
                JOIN product_catalog pc ON pr.recommended_product_id = pc.ocs_variant_number
                WHERE pr.product_id = $1
                AND pr.recommendation_type = 'crosssell'
                AND pr.active = true
                ORDER BY pr.score DESC
                LIMIT $2
            """
            
            products = await conn.fetch(query, product_id, limit)
            
            if products:
                return [dict(p) for p in products]
            
            # Fallback to complementary products
            return await self.get_complementary_products(product_id, limit)
    
    async def _store_recommendation(
        self,
        conn,
        source_id: str,
        recommended_id: str,
        rec_type: str,
        score: float,
        reason: str
    ):
        """Store a recommendation for future use"""
        try:
            await conn.execute("""
                INSERT INTO product_recommendations (
                    product_id, recommended_product_id, recommendation_type,
                    score, reason, based_on
                ) VALUES ($1, $2, $3, $4, $5, $6)
                ON CONFLICT (product_id, recommended_product_id, recommendation_type)
                DO UPDATE SET 
                    score = $4,
                    reason = $5,
                    updated_at = CURRENT_TIMESTAMP
            """, source_id, recommended_id, rec_type, score, reason, 'algorithm')
        except Exception as e:
            logger.warning(f"Failed to store recommendation: {e}")
    
    async def track_recommendation_event(
        self,
        product_id: str,
        recommended_id: str,
        event_type: str,
        customer_id: UUID = None,
        session_id: str = None,
        event_value: Decimal = None
    ):
        """Track user interaction with recommendations"""
        async with self.db_pool.acquire() as conn:
            # Find the recommendation
            rec = await conn.fetchrow("""
                SELECT id FROM product_recommendations
                WHERE product_id = $1 AND recommended_product_id = $2
            """, product_id, recommended_id)
            
            if rec:
                # Track the event
                await conn.execute("""
                    INSERT INTO recommendation_metrics (
                        recommendation_id, customer_id, session_id,
                        event_type, event_value
                    ) VALUES ($1, $2, $3, $4, $5)
                """, rec['id'], customer_id, session_id, event_type, event_value)
                
                # Update recommendation performance metrics
                if event_type == 'click':
                    await conn.execute("""
                        UPDATE product_recommendations
                        SET click_through_rate = (
                            SELECT COUNT(CASE WHEN event_type = 'click' THEN 1 END)::float /
                                   NULLIF(COUNT(CASE WHEN event_type = 'view' THEN 1 END), 0)
                            FROM recommendation_metrics
                            WHERE recommendation_id = $1
                        )
                        WHERE id = $1
                    """, rec['id'])
                elif event_type == 'purchase':
                    await conn.execute("""
                        UPDATE product_recommendations
                        SET conversion_rate = (
                            SELECT COUNT(CASE WHEN event_type = 'purchase' THEN 1 END)::float /
                                   NULLIF(COUNT(CASE WHEN event_type = 'click' THEN 1 END), 0)
                            FROM recommendation_metrics
                            WHERE recommendation_id = $1
                        ),
                        revenue_impact = revenue_impact + $2
                        WHERE id = $1
                    """, rec['id'], event_value or 0)
    
    async def get_recommendation_analytics(self) -> Dict[str, Any]:
        """Get analytics on recommendation performance"""
        async with self.db_pool.acquire() as conn:
            # Overall metrics
            overall = await conn.fetchrow("""
                SELECT 
                    COUNT(DISTINCT product_id) as products_with_recommendations,
                    COUNT(*) as total_recommendations,
                    AVG(score) as avg_confidence_score,
                    AVG(click_through_rate) as avg_ctr,
                    AVG(conversion_rate) as avg_conversion,
                    SUM(revenue_impact) as total_revenue_impact
                FROM product_recommendations
                WHERE active = true
            """)
            
            # By recommendation type
            by_type = await conn.fetch("""
                SELECT 
                    recommendation_type,
                    COUNT(*) as count,
                    AVG(score) as avg_score,
                    AVG(click_through_rate) as avg_ctr,
                    AVG(conversion_rate) as avg_conversion,
                    SUM(revenue_impact) as revenue_impact
                FROM product_recommendations
                WHERE active = true
                GROUP BY recommendation_type
                ORDER BY revenue_impact DESC
            """)
            
            # Top performing recommendations
            top_performers = await conn.fetch("""
                SELECT 
                    pr.product_id,
                    pr.recommended_product_id,
                    pr.recommendation_type,
                    pc1.product_name as source_product,
                    pc2.product_name as recommended_product,
                    pr.click_through_rate,
                    pr.conversion_rate,
                    pr.revenue_impact
                FROM product_recommendations pr
                JOIN product_catalog pc1 ON pr.product_id = pc1.ocs_variant_number
                JOIN product_catalog pc2 ON pr.recommended_product_id = pc2.ocs_variant_number
                WHERE pr.active = true
                AND pr.revenue_impact > 0
                ORDER BY pr.revenue_impact DESC
                LIMIT 10
            """)
            
            return {
                'overall': dict(overall) if overall else {},
                'by_type': [dict(t) for t in by_type],
                'top_performers': [dict(p) for p in top_performers]
            }