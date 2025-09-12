-- Migration: Spatial Store Locations and Location Services
-- Description: Add PostGIS support for store locations with spatial indexing
-- Date: 2025-09-10
-- Version: 1.0.0

-- =====================================================
-- 1. ENABLE POSTGIS EXTENSION
-- =====================================================
-- Note: Requires PostGIS to be installed on the database server
-- For production: Ensure PostGIS is available in your PostgreSQL installation
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS postgis_topology;

-- =====================================================
-- 2. ADD SPATIAL COLUMNS TO STORES TABLE
-- =====================================================
-- Add geography column for accurate distance calculations
ALTER TABLE stores 
ADD COLUMN IF NOT EXISTS location GEOGRAPHY(POINT, 4326);

-- Add geometry column for faster local queries
ALTER TABLE stores 
ADD COLUMN IF NOT EXISTS location_geom GEOMETRY(POINT, 4326);

-- Add columns for normalized address components
ALTER TABLE stores
ADD COLUMN IF NOT EXISTS latitude DECIMAL(10, 8),
ADD COLUMN IF NOT EXISTS longitude DECIMAL(11, 8),
ADD COLUMN IF NOT EXISTS street_address VARCHAR(255),
ADD COLUMN IF NOT EXISTS city VARCHAR(100),
ADD COLUMN IF NOT EXISTS province VARCHAR(100),
ADD COLUMN IF NOT EXISTS postal_code VARCHAR(20),
ADD COLUMN IF NOT EXISTS country VARCHAR(100) DEFAULT 'Canada';

-- =====================================================
-- 3. CREATE SPATIAL INDEXES
-- =====================================================
-- Index for geography-based distance queries
CREATE INDEX IF NOT EXISTS idx_stores_location_geography 
ON stores USING GIST(location);

-- Index for geometry-based queries (faster for nearby searches)
CREATE INDEX IF NOT EXISTS idx_stores_location_geometry 
ON stores USING GIST(location_geom);

-- Composite index for tenant-based location queries
CREATE INDEX IF NOT EXISTS idx_stores_tenant_location 
ON stores(tenant_id, status) 
WHERE location IS NOT NULL;

-- =====================================================
-- 4. UPDATE EXISTING STORES WITH LOCATION DATA
-- =====================================================
-- Migrate existing latitude/longitude data to spatial columns
UPDATE stores 
SET 
    location = ST_SetSRID(ST_MakePoint(longitude, latitude), 4326)::geography,
    location_geom = ST_SetSRID(ST_MakePoint(longitude, latitude), 4326)::geometry
WHERE latitude IS NOT NULL 
  AND longitude IS NOT NULL 
  AND location IS NULL;

-- =====================================================
-- 5. CREATE GEOCODING CACHE TABLE
-- =====================================================
CREATE TABLE IF NOT EXISTS geocoding_cache (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    address_hash VARCHAR(64) UNIQUE NOT NULL, -- SHA256 hash of normalized address
    full_address TEXT NOT NULL,
    latitude DECIMAL(10, 8) NOT NULL,
    longitude DECIMAL(11, 8) NOT NULL,
    location GEOGRAPHY(POINT, 4326) NOT NULL,
    provider VARCHAR(50), -- google, mapbox, nominatim, etc.
    raw_response JSONB,
    confidence_score DECIMAL(3, 2), -- 0.00 to 1.00
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP DEFAULT (CURRENT_TIMESTAMP + INTERVAL '90 days')
);

-- Index for efficient cache lookups
CREATE INDEX idx_geocoding_cache_hash ON geocoding_cache(address_hash);
CREATE INDEX idx_geocoding_cache_expires ON geocoding_cache(expires_at);

-- =====================================================
-- 6. CREATE CUSTOMER LOCATION TRACKING TABLE
-- =====================================================
CREATE TABLE IF NOT EXISTS customer_locations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id VARCHAR(255),
    user_id UUID,
    ip_address INET,
    location GEOGRAPHY(POINT, 4326),
    latitude DECIMAL(10, 8),
    longitude DECIMAL(11, 8),
    accuracy_meters INTEGER,
    source VARCHAR(50) CHECK (source IN ('gps', 'ip', 'manual', 'browser', 'mobile')),
    address JSONB,
    timezone VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT customer_location_session_or_user CHECK (
        session_id IS NOT NULL OR user_id IS NOT NULL
    )
);

-- Indexes for customer location queries
CREATE INDEX idx_customer_locations_session ON customer_locations(session_id);
CREATE INDEX idx_customer_locations_user ON customer_locations(user_id);
CREATE INDEX idx_customer_locations_created ON customer_locations(created_at);

-- =====================================================
-- 7. CREATE DELIVERY ZONES TABLE
-- =====================================================
CREATE TABLE IF NOT EXISTS delivery_zones (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    store_id UUID NOT NULL REFERENCES stores(id) ON DELETE CASCADE,
    zone_name VARCHAR(100) NOT NULL,
    zone_type VARCHAR(20) CHECK (zone_type IN ('radius', 'polygon', 'postal_codes')),
    -- For radius-based zones
    radius_km DECIMAL(5, 2),
    -- For polygon-based zones
    boundary GEOGRAPHY(POLYGON, 4326),
    -- For postal code based zones
    postal_codes TEXT[],
    delivery_fee DECIMAL(10, 2) DEFAULT 0.00,
    minimum_order DECIMAL(10, 2) DEFAULT 0.00,
    estimated_minutes_min INTEGER,
    estimated_minutes_max INTEGER,
    active BOOLEAN DEFAULT true,
    priority INTEGER DEFAULT 0, -- Higher priority zones override lower ones
    settings JSONB DEFAULT '{}'::JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for delivery zone queries
CREATE INDEX idx_delivery_zones_store ON delivery_zones(store_id);
CREATE INDEX idx_delivery_zones_boundary ON delivery_zones USING GIST(boundary);
CREATE INDEX idx_delivery_zones_active ON delivery_zones(active, priority);

-- =====================================================
-- 8. CREATE STORE DISTANCE FUNCTION
-- =====================================================
CREATE OR REPLACE FUNCTION calculate_store_distance(
    store_lat DECIMAL,
    store_lng DECIMAL,
    customer_lat DECIMAL,
    customer_lng DECIMAL
) RETURNS DECIMAL AS $$
DECLARE
    distance_meters DECIMAL;
BEGIN
    -- Use PostGIS for accurate distance calculation
    distance_meters := ST_Distance(
        ST_SetSRID(ST_MakePoint(store_lng, store_lat), 4326)::geography,
        ST_SetSRID(ST_MakePoint(customer_lng, customer_lat), 4326)::geography
    );
    
    -- Return distance in kilometers
    RETURN ROUND(distance_meters / 1000, 2);
END;
$$ LANGUAGE plpgsql IMMUTABLE;

-- =====================================================
-- 9. CREATE FIND NEAREST STORES FUNCTION
-- =====================================================
CREATE OR REPLACE FUNCTION find_nearest_stores(
    p_latitude DECIMAL,
    p_longitude DECIMAL,
    p_tenant_id UUID DEFAULT NULL,
    p_limit INTEGER DEFAULT 5,
    p_max_distance_km DECIMAL DEFAULT 50
) RETURNS TABLE (
    store_id UUID,
    tenant_id UUID,
    store_name VARCHAR,
    store_code VARCHAR,
    distance_km DECIMAL,
    address JSONB,
    phone VARCHAR,
    email VARCHAR,
    hours JSONB,
    delivery_enabled BOOLEAN,
    pickup_enabled BOOLEAN,
    delivery_radius_km INTEGER
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        s.id as store_id,
        s.tenant_id,
        s.name as store_name,
        s.store_code,
        ROUND(ST_Distance(
            s.location,
            ST_SetSRID(ST_MakePoint(p_longitude, p_latitude), 4326)::geography
        ) / 1000, 2) as distance_km,
        s.address,
        s.phone,
        s.email,
        s.hours,
        s.delivery_enabled,
        s.pickup_enabled,
        s.delivery_radius_km
    FROM stores s
    WHERE s.status = 'active'
      AND s.location IS NOT NULL
      AND (p_tenant_id IS NULL OR s.tenant_id = p_tenant_id)
      AND ST_DWithin(
          s.location,
          ST_SetSRID(ST_MakePoint(p_longitude, p_latitude), 4326)::geography,
          p_max_distance_km * 1000  -- Convert km to meters
      )
    ORDER BY distance_km ASC
    LIMIT p_limit;
END;
$$ LANGUAGE plpgsql STABLE;

-- =====================================================
-- 10. CREATE CHECK DELIVERY AVAILABILITY FUNCTION
-- =====================================================
CREATE OR REPLACE FUNCTION check_delivery_availability(
    p_store_id UUID,
    p_latitude DECIMAL,
    p_longitude DECIMAL
) RETURNS TABLE (
    available BOOLEAN,
    distance_km DECIMAL,
    delivery_fee DECIMAL,
    minimum_order DECIMAL,
    estimated_minutes_min INTEGER,
    estimated_minutes_max INTEGER,
    zone_name VARCHAR
) AS $$
DECLARE
    v_store_location GEOGRAPHY;
    v_customer_location GEOGRAPHY;
    v_distance_km DECIMAL;
    v_delivery_radius_km INTEGER;
    v_zone RECORD;
BEGIN
    -- Get store location and delivery radius
    SELECT location, delivery_radius_km 
    INTO v_store_location, v_delivery_radius_km
    FROM stores 
    WHERE id = p_store_id AND status = 'active';
    
    IF v_store_location IS NULL THEN
        RETURN QUERY SELECT 
            FALSE::BOOLEAN as available,
            NULL::DECIMAL as distance_km,
            NULL::DECIMAL as delivery_fee,
            NULL::DECIMAL as minimum_order,
            NULL::INTEGER as estimated_minutes_min,
            NULL::INTEGER as estimated_minutes_max,
            NULL::VARCHAR as zone_name;
        RETURN;
    END IF;
    
    -- Create customer location point
    v_customer_location := ST_SetSRID(ST_MakePoint(p_longitude, p_latitude), 4326)::geography;
    
    -- Calculate distance
    v_distance_km := ROUND(ST_Distance(v_store_location, v_customer_location) / 1000, 2);
    
    -- Check custom delivery zones first
    FOR v_zone IN 
        SELECT * FROM delivery_zones 
        WHERE store_id = p_store_id 
          AND active = true
        ORDER BY priority DESC
    LOOP
        -- Check if customer is in this zone
        IF v_zone.zone_type = 'radius' AND v_distance_km <= v_zone.radius_km THEN
            RETURN QUERY SELECT 
                TRUE::BOOLEAN as available,
                v_distance_km,
                v_zone.delivery_fee,
                v_zone.minimum_order,
                v_zone.estimated_minutes_min,
                v_zone.estimated_minutes_max,
                v_zone.zone_name;
            RETURN;
        ELSIF v_zone.zone_type = 'polygon' AND ST_Within(v_customer_location::geometry, v_zone.boundary::geometry) THEN
            RETURN QUERY SELECT 
                TRUE::BOOLEAN as available,
                v_distance_km,
                v_zone.delivery_fee,
                v_zone.minimum_order,
                v_zone.estimated_minutes_min,
                v_zone.estimated_minutes_max,
                v_zone.zone_name;
            RETURN;
        END IF;
    END LOOP;
    
    -- Fall back to default radius check
    IF v_distance_km <= v_delivery_radius_km THEN
        RETURN QUERY SELECT 
            TRUE::BOOLEAN as available,
            v_distance_km,
            5.00::DECIMAL as delivery_fee, -- Default fee
            25.00::DECIMAL as minimum_order, -- Default minimum
            30::INTEGER as estimated_minutes_min,
            60::INTEGER as estimated_minutes_max,
            'Standard Delivery'::VARCHAR as zone_name;
    ELSE
        RETURN QUERY SELECT 
            FALSE::BOOLEAN as available,
            v_distance_km,
            NULL::DECIMAL as delivery_fee,
            NULL::DECIMAL as minimum_order,
            NULL::INTEGER as estimated_minutes_min,
            NULL::INTEGER as estimated_minutes_max,
            NULL::VARCHAR as zone_name;
    END IF;
END;
$$ LANGUAGE plpgsql STABLE;

-- =====================================================
-- 11. CREATE TENANT-TEMPLATE MAPPING TABLE
-- =====================================================
CREATE TABLE IF NOT EXISTS tenant_templates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    template_id VARCHAR(50) NOT NULL,
    template_name VARCHAR(100) NOT NULL,
    is_default BOOLEAN DEFAULT false,
    configuration JSONB DEFAULT '{}'::JSONB,
    custom_css TEXT,
    custom_logo_url VARCHAR(500),
    theme_colors JSONB DEFAULT '{}'::JSONB,
    active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(tenant_id, template_id)
);

-- Ensure only one default template per tenant
CREATE UNIQUE INDEX idx_tenant_templates_default 
ON tenant_templates(tenant_id) 
WHERE is_default = true;

-- Index for template lookups
CREATE INDEX idx_tenant_templates_tenant ON tenant_templates(tenant_id);
CREATE INDEX idx_tenant_templates_active ON tenant_templates(tenant_id, active);

-- =====================================================
-- 12. ADD TEMPLATE CONFIGURATION TO TENANTS
-- =====================================================
ALTER TABLE tenants
ADD COLUMN IF NOT EXISTS default_template_id VARCHAR(50) DEFAULT 'modern-minimal',
ADD COLUMN IF NOT EXISTS allowed_templates TEXT[] DEFAULT ARRAY['modern-minimal'],
ADD COLUMN IF NOT EXISTS custom_domain VARCHAR(255),
ADD COLUMN IF NOT EXISTS subdomain VARCHAR(100) UNIQUE;

-- Create index for subdomain lookups
CREATE INDEX IF NOT EXISTS idx_tenants_subdomain ON tenants(subdomain);
CREATE INDEX IF NOT EXISTS idx_tenants_custom_domain ON tenants(custom_domain);

-- =====================================================
-- 13. CREATE AUDIT LOG FOR LOCATION ACCESS
-- =====================================================
CREATE TABLE IF NOT EXISTS location_access_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID,
    session_id VARCHAR(255),
    store_id UUID,
    action VARCHAR(50), -- 'search', 'select', 'delivery_check'
    customer_location GEOGRAPHY(POINT, 4326),
    selected_store_id UUID,
    distance_km DECIMAL(10, 2),
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Index for audit queries
CREATE INDEX idx_location_access_log_created ON location_access_log(created_at);
CREATE INDEX idx_location_access_log_user ON location_access_log(user_id);
CREATE INDEX idx_location_access_log_session ON location_access_log(session_id);

-- =====================================================
-- 14. CREATE TRIGGER FOR LOCATION UPDATES
-- =====================================================
CREATE OR REPLACE FUNCTION update_store_location()
RETURNS TRIGGER AS $$
BEGIN
    -- Update spatial columns when lat/lng changes
    IF NEW.latitude IS NOT NULL AND NEW.longitude IS NOT NULL THEN
        NEW.location := ST_SetSRID(ST_MakePoint(NEW.longitude, NEW.latitude), 4326)::geography;
        NEW.location_geom := ST_SetSRID(ST_MakePoint(NEW.longitude, NEW.latitude), 4326)::geometry;
    END IF;
    
    -- Update timestamp
    NEW.updated_at := CURRENT_TIMESTAMP;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create trigger
DROP TRIGGER IF EXISTS trigger_update_store_location ON stores;
CREATE TRIGGER trigger_update_store_location
    BEFORE INSERT OR UPDATE OF latitude, longitude
    ON stores
    FOR EACH ROW
    EXECUTE FUNCTION update_store_location();

-- =====================================================
-- 15. ADD SAMPLE TENANT-TEMPLATE MAPPINGS
-- =====================================================
-- Insert sample tenant-template configurations
INSERT INTO tenant_templates (tenant_id, template_id, template_name, is_default, configuration)
SELECT 
    id,
    'modern-minimal',
    'Modern Minimal',
    true,
    jsonb_build_object(
        'primary_color', '#10b981',
        'secondary_color', '#3b82f6',
        'font_family', 'Inter',
        'show_reviews', true,
        'enable_chat', true
    )
FROM tenants
WHERE NOT EXISTS (
    SELECT 1 FROM tenant_templates tt 
    WHERE tt.tenant_id = tenants.id
)
LIMIT 1;

-- =====================================================
-- 16. CREATE VIEW FOR STORE LOCATIONS WITH DETAILS
-- =====================================================
CREATE OR REPLACE VIEW v_store_locations AS
SELECT 
    s.id,
    s.tenant_id,
    t.name as tenant_name,
    t.subdomain,
    s.store_code,
    s.name as store_name,
    s.latitude,
    s.longitude,
    s.street_address,
    s.city,
    s.province,
    s.postal_code,
    s.country,
    s.phone,
    s.email,
    s.delivery_radius_km,
    s.delivery_enabled,
    s.pickup_enabled,
    s.status,
    ST_AsGeoJSON(s.location_geom) as geojson
FROM stores s
JOIN tenants t ON s.tenant_id = t.id
WHERE s.location IS NOT NULL;

-- Grant appropriate permissions
GRANT SELECT ON v_store_locations TO PUBLIC;

-- =====================================================
-- 17. CREATE FUNCTION FOR BATCH GEOCODING
-- =====================================================
CREATE OR REPLACE FUNCTION batch_update_store_locations()
RETURNS INTEGER AS $$
DECLARE
    updated_count INTEGER := 0;
    store_record RECORD;
BEGIN
    FOR store_record IN 
        SELECT id, address 
        FROM stores 
        WHERE location IS NULL 
          AND address IS NOT NULL
          AND address != '{}'::jsonb
    LOOP
        -- Extract address components from JSONB
        IF store_record.address->>'latitude' IS NOT NULL 
           AND store_record.address->>'longitude' IS NOT NULL THEN
            UPDATE stores 
            SET 
                latitude = (store_record.address->>'latitude')::DECIMAL,
                longitude = (store_record.address->>'longitude')::DECIMAL,
                location = ST_SetSRID(
                    ST_MakePoint(
                        (store_record.address->>'longitude')::DECIMAL,
                        (store_record.address->>'latitude')::DECIMAL
                    ), 4326
                )::geography,
                location_geom = ST_SetSRID(
                    ST_MakePoint(
                        (store_record.address->>'longitude')::DECIMAL,
                        (store_record.address->>'latitude')::DECIMAL
                    ), 4326
                )::geometry
            WHERE id = store_record.id;
            
            updated_count := updated_count + 1;
        END IF;
    END LOOP;
    
    RETURN updated_count;
END;
$$ LANGUAGE plpgsql;

-- =====================================================
-- END OF MIGRATION
-- =====================================================