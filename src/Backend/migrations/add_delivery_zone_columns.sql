-- Migration: Add delivery zone GeoJSON columns to stores table
-- Date: 2025-10-13
-- Description: Adds support for custom polygon-based delivery zones
--              to replace/supplement the simple delivery_radius_km field

-- Add delivery_zone column to store GeoJSON polygon
ALTER TABLE stores
ADD COLUMN IF NOT EXISTS delivery_zone JSONB DEFAULT NULL;

-- Add delivery_zone_stats column to cache zone calculations
ALTER TABLE stores
ADD COLUMN IF NOT EXISTS delivery_zone_stats JSONB DEFAULT NULL;

-- Add comment for documentation
COMMENT ON COLUMN stores.delivery_zone IS
'GeoJSON Polygon defining custom delivery boundary. Format: {"type": "Polygon", "coordinates": [[[lng, lat], ...]]}';

COMMENT ON COLUMN stores.delivery_zone_stats IS
'Cached statistics for delivery zone: {"area_km2": float, "perimeter_km": float, "approximate_radius_km": float, "point_count": int}';

-- Create index on delivery_zone for faster JSON queries
CREATE INDEX IF NOT EXISTS idx_stores_delivery_zone
ON stores USING GIN (delivery_zone);

-- Create function to validate GeoJSON polygon structure
CREATE OR REPLACE FUNCTION validate_delivery_zone_geojson(zone JSONB)
RETURNS BOOLEAN AS $$
BEGIN
    -- Check if zone is NULL (allowed)
    IF zone IS NULL THEN
        RETURN TRUE;
    END IF;

    -- Check required fields exist
    IF NOT (zone ? 'type' AND zone ? 'coordinates') THEN
        RETURN FALSE;
    END IF;

    -- Check type is 'Polygon'
    IF zone->>'type' != 'Polygon' THEN
        RETURN FALSE;
    END IF;

    -- Check coordinates is an array
    IF jsonb_typeof(zone->'coordinates') != 'array' THEN
        RETURN FALSE;
    END IF;

    -- Basic validation passed
    RETURN TRUE;
END;
$$ LANGUAGE plpgsql IMMUTABLE;

-- Add check constraint to ensure valid GeoJSON format
ALTER TABLE stores
DROP CONSTRAINT IF EXISTS stores_delivery_zone_valid_geojson;

ALTER TABLE stores
ADD CONSTRAINT stores_delivery_zone_valid_geojson
CHECK (validate_delivery_zone_geojson(delivery_zone));

-- Create helper function to extract zone area from stats
CREATE OR REPLACE FUNCTION get_delivery_zone_area(store_id UUID)
RETURNS NUMERIC AS $$
DECLARE
    area NUMERIC;
BEGIN
    SELECT (delivery_zone_stats->>'area_km2')::NUMERIC
    INTO area
    FROM stores
    WHERE id = store_id;

    RETURN COALESCE(area, 0);
END;
$$ LANGUAGE plpgsql STABLE;

-- Create helper function to check if a point is in a store's delivery zone
-- This is a simplified version - for production, use PostGIS ST_Contains
CREATE OR REPLACE FUNCTION point_in_delivery_zone(
    store_id UUID,
    check_latitude NUMERIC,
    check_longitude NUMERIC
)
RETURNS BOOLEAN AS $$
DECLARE
    zone JSONB;
    has_zone BOOLEAN;
    fallback_radius INTEGER;
    store_lat NUMERIC;
    store_lng NUMERIC;
    distance_km NUMERIC;
BEGIN
    -- Get store data
    SELECT delivery_zone, delivery_radius_km, latitude, longitude
    INTO zone, fallback_radius, store_lat, store_lng
    FROM stores
    WHERE id = store_id;

    -- If no custom zone defined, fall back to radius check
    IF zone IS NULL THEN
        -- Simple Haversine distance calculation (approximate)
        distance_km := (
            6371 * acos(
                cos(radians(store_lat)) *
                cos(radians(check_latitude)) *
                cos(radians(check_longitude) - radians(store_lng)) +
                sin(radians(store_lat)) *
                sin(radians(check_latitude))
            )
        );

        RETURN distance_km <= fallback_radius;
    END IF;

    -- For polygon zones, recommend using PostGIS ST_Contains in production
    -- This is a placeholder that returns true if zone exists
    RETURN TRUE;
END;
$$ LANGUAGE plpgsql STABLE;

-- Migration success message
DO $$
BEGIN
    RAISE NOTICE 'Migration completed: delivery_zone columns added to stores table';
    RAISE NOTICE 'Added columns: delivery_zone (JSONB), delivery_zone_stats (JSONB)';
    RAISE NOTICE 'Added functions: validate_delivery_zone_geojson, get_delivery_zone_area, point_in_delivery_zone';
    RAISE NOTICE 'Next steps: Update backend API to accept and validate delivery zone data';
END $$;
