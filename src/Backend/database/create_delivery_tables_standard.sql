-- Delivery Management System Tables
-- Production-ready schema without PostGIS dependency

BEGIN TRANSACTION;

-- =========================================
-- Delivery status enum for consistency
-- =========================================
DO $$ BEGIN
    CREATE TYPE delivery_status AS ENUM (
        'pending',
        'assigned',
        'accepted',
        'preparing',
        'ready_for_pickup',
        'picked_up',
        'en_route',
        'arrived',
        'delivering',
        'completed',
        'failed',
        'cancelled'
    );
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

-- =========================================
-- Main deliveries table
-- =========================================
CREATE TABLE IF NOT EXISTS deliveries (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    order_id UUID NOT NULL REFERENCES orders(id) ON DELETE CASCADE,
    store_id UUID NOT NULL REFERENCES stores(id) ON DELETE CASCADE,
    assigned_to UUID REFERENCES users(id) ON DELETE SET NULL,

    -- Status tracking
    status delivery_status NOT NULL DEFAULT 'pending',

    -- Customer information (denormalized for performance)
    customer_id UUID REFERENCES profiles(id),
    customer_name VARCHAR(200) NOT NULL,
    customer_phone VARCHAR(20) NOT NULL,
    customer_email VARCHAR(255),

    -- Address information
    delivery_address JSONB NOT NULL CHECK (
        delivery_address ? 'street' AND
        delivery_address ? 'city' AND
        delivery_address ? 'postal_code'
    ),
    delivery_latitude DECIMAL(10, 8),
    delivery_longitude DECIMAL(11, 8),
    delivery_notes TEXT,

    -- Time tracking
    scheduled_at TIMESTAMP,
    assigned_at TIMESTAMP,
    accepted_at TIMESTAMP,
    picked_up_at TIMESTAMP,
    departed_at TIMESTAMP,
    arrived_at TIMESTAMP,
    completed_at TIMESTAMP,
    cancelled_at TIMESTAMP,

    -- Delivery metrics
    estimated_delivery_time TIMESTAMP,
    actual_delivery_time TIMESTAMP,
    distance_km DECIMAL(10,2),
    delivery_fee DECIMAL(10,2) DEFAULT 0,
    tip_amount DECIMAL(10,2) DEFAULT 0,

    -- Proof of delivery
    signature_data TEXT,
    signature_captured_at TIMESTAMP,
    photo_proof_urls TEXT[],
    id_verified BOOLEAN DEFAULT false,
    id_verification_type VARCHAR(50), -- 'manual', 'scan', 'photo'
    id_verification_data JSONB,
    age_verified BOOLEAN DEFAULT false,

    -- Batch delivery support
    batch_id UUID,
    batch_sequence INTEGER,

    -- Service quality
    rating INTEGER CHECK (rating >= 1 AND rating <= 5),
    feedback TEXT,
    issues_reported JSONB DEFAULT '[]'::jsonb,

    -- Metadata
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by UUID REFERENCES users(id),
    updated_by UUID REFERENCES users(id)
);

-- =========================================
-- Delivery tracking table for GPS breadcrumbs
-- =========================================
CREATE TABLE IF NOT EXISTS delivery_tracking (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    delivery_id UUID NOT NULL REFERENCES deliveries(id) ON DELETE CASCADE,

    -- Location data
    latitude DECIMAL(10, 8) NOT NULL,
    longitude DECIMAL(11, 8) NOT NULL,
    altitude_meters DECIMAL(10,2),
    accuracy_meters DECIMAL(10,2),
    speed_kmh DECIMAL(5,2),
    heading INTEGER CHECK (heading >= 0 AND heading <= 360),

    -- Device information
    provider VARCHAR(50), -- 'gps', 'network', 'fused'
    battery_level INTEGER CHECK (battery_level >= 0 AND battery_level <= 100),
    is_mock_location BOOLEAN DEFAULT false,

    -- Timestamps
    recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    received_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- Additional context
    activity_type VARCHAR(50), -- 'stationary', 'walking', 'running', 'driving'
    metadata JSONB DEFAULT '{}'::jsonb
);

-- =========================================
-- Delivery events for audit trail
-- =========================================
CREATE TABLE IF NOT EXISTS delivery_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    delivery_id UUID NOT NULL REFERENCES deliveries(id) ON DELETE CASCADE,
    event_type VARCHAR(50) NOT NULL,
    event_data JSONB DEFAULT '{}'::jsonb,
    performed_by UUID REFERENCES users(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =========================================
-- Delivery batches for grouped deliveries
-- =========================================
CREATE TABLE IF NOT EXISTS delivery_batches (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    store_id UUID NOT NULL REFERENCES stores(id) ON DELETE CASCADE,
    assigned_to UUID REFERENCES users(id) ON DELETE SET NULL,

    -- Batch info
    batch_number VARCHAR(50) UNIQUE NOT NULL,
    total_deliveries INTEGER NOT NULL DEFAULT 0,
    completed_deliveries INTEGER NOT NULL DEFAULT 0,

    -- Optimization
    optimized_route JSONB,
    total_distance_km DECIMAL(10,2),
    estimated_duration_minutes INTEGER,

    -- Status
    status VARCHAR(50) DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP
);

-- =========================================
-- Geofence configurations for locations
-- =========================================
CREATE TABLE IF NOT EXISTS delivery_geofences (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    delivery_id UUID NOT NULL REFERENCES deliveries(id) ON DELETE CASCADE,

    -- Geofence definition
    center_latitude DECIMAL(10, 8) NOT NULL,
    center_longitude DECIMAL(11, 8) NOT NULL,
    radius_meters INTEGER NOT NULL DEFAULT 100,
    fence_type VARCHAR(50) DEFAULT 'arrival', -- 'arrival', 'departure', 'waypoint'

    -- Trigger tracking
    entered_at TIMESTAMP,
    exited_at TIMESTAMP,
    dwell_time_seconds INTEGER,

    -- Configuration
    notify_on_enter BOOLEAN DEFAULT true,
    notify_on_exit BOOLEAN DEFAULT false,
    auto_complete_on_enter BOOLEAN DEFAULT false,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =========================================
-- Staff delivery availability
-- =========================================
CREATE TABLE IF NOT EXISTS staff_delivery_status (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,

    -- Availability
    is_available BOOLEAN DEFAULT false,
    available_from TIMESTAMP,
    available_until TIMESTAMP,

    -- Current status
    current_status VARCHAR(50) DEFAULT 'offline', -- 'offline', 'available', 'busy', 'break'
    current_latitude DECIMAL(10, 8),
    current_longitude DECIMAL(11, 8),
    last_location_update TIMESTAMP,

    -- Capacity
    current_deliveries INTEGER DEFAULT 0,
    max_deliveries INTEGER DEFAULT 5,

    -- Performance metrics
    deliveries_today INTEGER DEFAULT 0,
    deliveries_completed INTEGER DEFAULT 0,
    average_delivery_time_minutes INTEGER,

    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id)
);

-- =========================================
-- Create indexes for performance
-- =========================================

-- Deliveries indexes
CREATE INDEX IF NOT EXISTS idx_deliveries_status ON deliveries(status);
CREATE INDEX IF NOT EXISTS idx_deliveries_store_id ON deliveries(store_id);
CREATE INDEX IF NOT EXISTS idx_deliveries_assigned_to ON deliveries(assigned_to);
CREATE INDEX IF NOT EXISTS idx_deliveries_customer_id ON deliveries(customer_id);
CREATE INDEX IF NOT EXISTS idx_deliveries_order_id ON deliveries(order_id);
CREATE INDEX IF NOT EXISTS idx_deliveries_batch_id ON deliveries(batch_id);
CREATE INDEX IF NOT EXISTS idx_deliveries_scheduled_at ON deliveries(scheduled_at);
CREATE INDEX IF NOT EXISTS idx_deliveries_created_at ON deliveries(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_deliveries_location ON deliveries(delivery_latitude, delivery_longitude);

-- Tracking indexes
CREATE INDEX IF NOT EXISTS idx_delivery_tracking_delivery_id ON delivery_tracking(delivery_id);
CREATE INDEX IF NOT EXISTS idx_delivery_tracking_recorded_at ON delivery_tracking(recorded_at DESC);
CREATE INDEX IF NOT EXISTS idx_delivery_tracking_location ON delivery_tracking(latitude, longitude);

-- Events indexes
CREATE INDEX IF NOT EXISTS idx_delivery_events_delivery_id ON delivery_events(delivery_id);
CREATE INDEX IF NOT EXISTS idx_delivery_events_event_type ON delivery_events(event_type);
CREATE INDEX IF NOT EXISTS idx_delivery_events_created_at ON delivery_events(created_at DESC);

-- Geofence indexes
CREATE INDEX IF NOT EXISTS idx_delivery_geofences_delivery_id ON delivery_geofences(delivery_id);
CREATE INDEX IF NOT EXISTS idx_delivery_geofences_location ON delivery_geofences(center_latitude, center_longitude);

-- Staff status indexes
CREATE INDEX IF NOT EXISTS idx_staff_delivery_status_user_id ON staff_delivery_status(user_id);
CREATE INDEX IF NOT EXISTS idx_staff_delivery_status_available ON staff_delivery_status(is_available);
CREATE INDEX IF NOT EXISTS idx_staff_delivery_status_location ON staff_delivery_status(current_latitude, current_longitude);

-- =========================================
-- Create update trigger for updated_at
-- =========================================
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create triggers only if they don't exist
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_trigger WHERE tgname = 'update_deliveries_updated_at') THEN
        CREATE TRIGGER update_deliveries_updated_at
        BEFORE UPDATE ON deliveries
        FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
    END IF;

    IF NOT EXISTS (SELECT 1 FROM pg_trigger WHERE tgname = 'update_staff_delivery_status_updated_at') THEN
        CREATE TRIGGER update_staff_delivery_status_updated_at
        BEFORE UPDATE ON staff_delivery_status
        FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
    END IF;
END $$;

-- =========================================
-- Helper functions
-- =========================================

-- Calculate distance between two points using Haversine formula
CREATE OR REPLACE FUNCTION calculate_distance(
    lat1 DECIMAL, lon1 DECIMAL,
    lat2 DECIMAL, lon2 DECIMAL
) RETURNS DECIMAL AS $$
DECLARE
    R CONSTANT DECIMAL := 6371; -- Earth radius in kilometers
    dlat DECIMAL;
    dlon DECIMAL;
    a DECIMAL;
    c DECIMAL;
BEGIN
    dlat := radians(lat2 - lat1);
    dlon := radians(lon2 - lon1);
    a := sin(dlat/2) * sin(dlat/2) +
         cos(radians(lat1)) * cos(radians(lat2)) *
         sin(dlon/2) * sin(dlon/2);
    c := 2 * atan2(sqrt(a), sqrt(1-a));
    RETURN R * c;
END;
$$ LANGUAGE plpgsql;

-- Check if point is within geofence
CREATE OR REPLACE FUNCTION check_geofence_entry(
    point_lat DECIMAL, point_lon DECIMAL,
    fence_lat DECIMAL, fence_lon DECIMAL,
    fence_radius_meters INTEGER
) RETURNS BOOLEAN AS $$
DECLARE
    distance_km DECIMAL;
BEGIN
    distance_km := calculate_distance(point_lat, point_lon, fence_lat, fence_lon);
    RETURN (distance_km * 1000) <= fence_radius_meters;
END;
$$ LANGUAGE plpgsql;

-- Get active deliveries for a staff member
CREATE OR REPLACE FUNCTION get_staff_active_deliveries(staff_id UUID)
RETURNS TABLE (
    delivery_id UUID,
    order_id UUID,
    customer_name VARCHAR,
    delivery_address JSONB,
    status delivery_status,
    estimated_time TIMESTAMP
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        d.id,
        d.order_id,
        d.customer_name,
        d.delivery_address,
        d.status,
        d.estimated_delivery_time
    FROM deliveries d
    WHERE d.assigned_to = staff_id
    AND d.status NOT IN ('completed', 'failed', 'cancelled')
    ORDER BY d.scheduled_at, d.created_at;
END;
$$ LANGUAGE plpgsql;

-- Log delivery event
CREATE OR REPLACE FUNCTION log_delivery_event(
    p_delivery_id UUID,
    p_event_type VARCHAR,
    p_event_data JSONB DEFAULT '{}',
    p_user_id UUID DEFAULT NULL
) RETURNS UUID AS $$
DECLARE
    event_id UUID;
BEGIN
    INSERT INTO delivery_events (delivery_id, event_type, event_data, performed_by)
    VALUES (p_delivery_id, p_event_type, p_event_data, p_user_id)
    RETURNING id INTO event_id;

    RETURN event_id;
END;
$$ LANGUAGE plpgsql;

COMMIT;