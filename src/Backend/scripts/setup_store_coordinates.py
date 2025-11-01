"""
Setup Store Coordinates Script
Geocodes all stores and updates their GPS coordinates
"""

import asyncio
import asyncpg
import os
import sys
import logging
import json
from decimal import Decimal

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.geocoding.mapbox_service import MapboxGeocodingService

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


async def setup_store_coordinates():
    """Geocode all active stores and update their coordinates"""

    # Get Mapbox API key
    mapbox_key = os.getenv('MAPBOX_API_KEY')
    if not mapbox_key:
        logger.error("MAPBOX_API_KEY environment variable not set!")
        logger.error("Get your API key from: https://account.mapbox.com/access-tokens/")
        return

    # Initialize services
    geocoder = MapboxGeocodingService(mapbox_key)

    # Validate API key with a known Canadian address
    logger.info("Validating Mapbox API key...")
    test_result = await geocoder.geocode_address(
        street="1 Yonge Street",
        city="Toronto",
        province="ON",
        postal_code="M5E 1W7"
    )

    if not test_result:
        logger.error("Mapbox API key validation failed!")
        return

    logger.info("✓ Mapbox API key is valid (tested with Toronto address)")

    # Connect to database
    db = await asyncpg.connect(
        host=os.getenv('DB_HOST', 'localhost'),
        port=int(os.getenv('DB_PORT', 5434)),
        database=os.getenv('DB_NAME', 'ai_engine'),
        user=os.getenv('DB_USER', 'weedgo'),
        password=os.getenv('DB_PASSWORD', 'weedgo123')
    )

    try:
        # Get all active stores without coordinates
        stores = await db.fetch("""
            SELECT id, name, store_code, address
            FROM stores
            WHERE status = 'active'
            AND (latitude IS NULL OR longitude IS NULL)
        """)

        logger.info(f"Found {len(stores)} stores needing geocoding")

        updated_count = 0
        failed_count = 0

        for store in stores:
            store_id = store['id']
            store_name = store['name']
            address_data = store['address']

            # Parse address if it's a JSON string
            if isinstance(address_data, str):
                address = json.loads(address_data)
            else:
                address = address_data

            logger.info(f"\nProcessing: {store_name}")
            logger.info(f"  Address: {address}")

            # Extract address components (Canadian addresses only)
            street = address.get('street', '')
            city = address.get('city', '')
            province = address.get('province', '')
            postal_code = address.get('postal_code', '')

            # Geocode Canadian address
            result = await geocoder.geocode_address(
                street=street,
                city=city,
                province=province,
                postal_code=postal_code
            )

            if result:
                latitude, longitude = result
                logger.info(f"  ✓ Geocoded to: ({latitude}, {longitude})")

                # Update store in database
                # Note: PostGIS location column update will be done separately if PostGIS is installed
                await db.execute("""
                    UPDATE stores
                    SET
                        latitude = $1,
                        longitude = $2,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = $3
                """, latitude, longitude, store_id)

                logger.info(f"  ✓ Updated database")
                updated_count += 1
            else:
                logger.error(f"  ✗ Failed to geocode")
                failed_count += 1

        logger.info(f"\n{'='*60}")
        logger.info(f"Geocoding complete!")
        logger.info(f"  Updated: {updated_count} stores")
        logger.info(f"  Failed: {failed_count} stores")
        logger.info(f"{'='*60}")

        # Show all stores with coordinates
        all_stores = await db.fetch("""
            SELECT name, latitude, longitude,
                   address->>'street' as street,
                   address->>'city' as city
            FROM stores
            WHERE status = 'active'
            ORDER BY name
        """)

        logger.info("\nAll Active Stores:")
        for store in all_stores:
            coord_status = "✓" if store['latitude'] and store['longitude'] else "✗"
            logger.info(f"  {coord_status} {store['name']}")
            logger.info(f"     {store['street']}, {store['city']}")
            if store['latitude'] and store['longitude']:
                logger.info(f"     GPS: ({store['latitude']}, {store['longitude']})")

    finally:
        await db.close()


if __name__ == "__main__":
    asyncio.run(setup_store_coordinates())
