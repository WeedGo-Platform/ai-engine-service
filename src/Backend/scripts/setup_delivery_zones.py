"""
Setup Delivery Zones Script
Creates delivery zones for all stores based on their configuration
"""

import asyncio
import asyncpg
import os
import sys
import logging

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


async def setup_delivery_zones():
    """Create delivery zones for all active stores"""

    # Connect to database
    db = await asyncpg.connect(
        host=os.getenv('DB_HOST', 'localhost'),
        port=int(os.getenv('DB_PORT', 5434)),
        database=os.getenv('DB_NAME', 'ai_engine'),
        user=os.getenv('DB_USER', 'weedgo'),
        password=os.getenv('DB_PASSWORD', 'your_password_here')
    )

    try:
        # Get all active stores with coordinates
        stores = await db.fetch("""
            SELECT id, name, tenant_id, delivery_radius_km
            FROM stores
            WHERE status = 'active'
            AND latitude IS NOT NULL
            AND longitude IS NOT NULL
            AND delivery_enabled = true
        """)

        logger.info(f"Found {len(stores)} stores needing delivery zones")

        created_count = 0

        for store in stores:
            store_id = store['id']
            store_name = store['name']
            tenant_id = store['tenant_id']
            radius_km = store['delivery_radius_km'] or 10  # Default 10km

            logger.info(f"\nProcessing: {store_name}")

            # Check if zone already exists
            existing = await db.fetchval("""
                SELECT COUNT(*)
                FROM delivery_zones
                WHERE store_id = $1 AND zone_type = 'radius'
            """, store_id)

            if existing > 0:
                logger.info(f"  ✓ Delivery zone already exists")
                continue

            # Create delivery zone
            await db.execute("""
                INSERT INTO delivery_zones (
                    store_id,
                    tenant_id,
                    zone_name,
                    zone_type,
                    radius_km,
                    base_delivery_fee,
                    free_delivery_minimum,
                    delivery_time_minutes,
                    is_active
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
            """,
                store_id,
                tenant_id,
                f"{store_name} - Local Delivery",
                'radius',  # Circular zone
                radius_km,
                7.50,  # $7.50 base delivery fee
                100.00,  # Free delivery over $100
                45,  # 45 minute estimate
                True
            )

            logger.info(f"  ✓ Created delivery zone:")
            logger.info(f"     Radius: {radius_km} km")
            logger.info(f"     Base fee: $7.50")
            logger.info(f"     Free delivery: >$100.00")
            logger.info(f"     Est. time: 45 minutes")

            created_count += 1

        logger.info(f"\n{'='*60}")
        logger.info(f"Delivery zones setup complete!")
        logger.info(f"  Created: {created_count} zones")
        logger.info(f"{'='*60}")

        # Show all delivery zones
        zones = await db.fetch("""
            SELECT
                s.name as store_name,
                dz.zone_name,
                dz.zone_type,
                dz.radius_km,
                dz.base_delivery_fee,
                dz.free_delivery_minimum,
                dz.delivery_time_minutes,
                dz.is_active
            FROM delivery_zones dz
            JOIN stores s ON s.id = dz.store_id
            WHERE dz.is_active = true
            ORDER BY s.name
        """)

        logger.info("\nActive Delivery Zones:")
        for zone in zones:
            status = "✓" if zone['is_active'] else "✗"
            logger.info(f"  {status} {zone['store_name']}")
            logger.info(f"     Type: {zone['zone_type']} ({zone['radius_km']} km)")
            logger.info(f"     Fee: ${zone['base_delivery_fee']} (free over ${zone['free_delivery_minimum']})")
            logger.info(f"     Time: ~{zone['delivery_time_minutes']} minutes")

    finally:
        await db.close()


if __name__ == "__main__":
    asyncio.run(setup_delivery_zones())
