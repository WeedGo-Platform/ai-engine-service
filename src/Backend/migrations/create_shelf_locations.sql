-- Migration: Create shelf locations table for inventory management
-- Date: 2025-01-13
-- Description: 
--   Creates tables to manage warehouse shelf locations for inventory items
--   Supports hierarchical location structure (zone -> aisle -> shelf -> bin)

BEGIN;

-- Create shelf_locations table
CREATE TABLE IF NOT EXISTS shelf_locations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    store_id UUID NOT NULL REFERENCES stores(id) ON DELETE CASCADE,
    
    -- Location hierarchy
    zone VARCHAR(50),           -- e.g., "A", "B", "COLD", "SECURE"
    aisle VARCHAR(50),          -- e.g., "01", "02", "03"
    shelf VARCHAR(50),          -- e.g., "A", "B", "C", "TOP", "MIDDLE", "BOTTOM"
    bin VARCHAR(50),            -- e.g., "01", "02", "03"
    
    -- Full location code (generated)
    location_code VARCHAR(200) GENERATED ALWAYS AS (
        COALESCE(zone, '') || 
        CASE WHEN aisle IS NOT NULL THEN '-' || aisle ELSE '' END ||
        CASE WHEN shelf IS NOT NULL THEN '-' || shelf ELSE '' END ||
        CASE WHEN bin IS NOT NULL THEN '-' || bin ELSE '' END
    ) STORED,
    
    -- Location details
    location_type VARCHAR(50) DEFAULT 'standard', -- standard, cold_storage, secure, bulk, display
    max_weight_kg DECIMAL(10,2),
    max_volume_m3 DECIMAL(10,4),
    temperature_range VARCHAR(100), -- e.g., "15-25°C", "2-8°C"
    
    -- Status
    is_active BOOLEAN DEFAULT true,
    is_available BOOLEAN DEFAULT true,
    
    -- Metadata
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- Constraints
    CONSTRAINT unique_location_per_store UNIQUE (store_id, zone, aisle, shelf, bin)
);

-- Create inventory_locations table (many-to-many relationship)
CREATE TABLE IF NOT EXISTS inventory_locations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    store_id UUID NOT NULL REFERENCES stores(id) ON DELETE CASCADE,
    sku VARCHAR(100) NOT NULL,
    location_id UUID NOT NULL REFERENCES shelf_locations(id) ON DELETE CASCADE,
    
    -- Quantity at this location
    quantity INTEGER NOT NULL DEFAULT 0,
    
    -- Batch tracking
    batch_lot VARCHAR(100),
    
    -- Status
    is_primary BOOLEAN DEFAULT false, -- Primary picking location
    
    -- Metadata
    assigned_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- Constraints
    CONSTRAINT fk_inventory_locations_store_sku 
        FOREIGN KEY (store_id, sku) 
        REFERENCES ocs_inventory(store_id, sku) ON DELETE CASCADE,
    CONSTRAINT unique_sku_location_batch 
        UNIQUE (store_id, sku, location_id, batch_lot)
);

-- Create location_assignments_log table for tracking movements
CREATE TABLE IF NOT EXISTS location_assignments_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    store_id UUID NOT NULL REFERENCES stores(id) ON DELETE CASCADE,
    sku VARCHAR(100) NOT NULL,
    batch_lot VARCHAR(100),
    
    -- Movement details
    from_location_id UUID REFERENCES shelf_locations(id),
    to_location_id UUID REFERENCES shelf_locations(id),
    quantity_moved INTEGER NOT NULL,
    
    -- Reason
    movement_type VARCHAR(50) NOT NULL, -- receive, pick, transfer, cycle_count, return
    reference_id UUID, -- PO ID, Order ID, etc.
    notes TEXT,
    
    -- User tracking
    performed_by UUID REFERENCES users(id),
    
    -- Timestamp
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Add indexes for performance
CREATE INDEX idx_shelf_locations_store ON shelf_locations(store_id);
CREATE INDEX idx_shelf_locations_code ON shelf_locations(location_code);
CREATE INDEX idx_shelf_locations_type ON shelf_locations(location_type);
CREATE INDEX idx_shelf_locations_active ON shelf_locations(is_active, is_available);

CREATE INDEX idx_inventory_locations_store_sku ON inventory_locations(store_id, sku);
CREATE INDEX idx_inventory_locations_location ON inventory_locations(location_id);
CREATE INDEX idx_inventory_locations_batch ON inventory_locations(batch_lot);
CREATE INDEX idx_inventory_locations_primary ON inventory_locations(is_primary);

CREATE INDEX idx_location_assignments_log_store ON location_assignments_log(store_id);
CREATE INDEX idx_location_assignments_log_sku ON location_assignments_log(sku);
CREATE INDEX idx_location_assignments_log_date ON location_assignments_log(created_at);

-- Create triggers for updated_at
CREATE TRIGGER update_shelf_locations_updated_at 
    BEFORE UPDATE ON shelf_locations 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_inventory_locations_updated_at 
    BEFORE UPDATE ON inventory_locations 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

-- Add comments for documentation
COMMENT ON TABLE shelf_locations IS 'Physical shelf locations within a store warehouse';
COMMENT ON TABLE inventory_locations IS 'Maps inventory items to their physical shelf locations';
COMMENT ON TABLE location_assignments_log IS 'Historical log of inventory location movements';

COMMENT ON COLUMN shelf_locations.location_type IS 'Type of storage location: standard, cold_storage, secure, bulk, display';
COMMENT ON COLUMN inventory_locations.is_primary IS 'Indicates if this is the primary picking location for the SKU';
COMMENT ON COLUMN location_assignments_log.movement_type IS 'Type of movement: receive, pick, transfer, cycle_count, return';

-- Insert sample shelf locations for testing (optional, can be commented out)
/*
INSERT INTO shelf_locations (store_id, zone, aisle, shelf, bin, location_type, notes)
SELECT 
    s.id,
    z.zone,
    a.aisle,
    sh.shelf,
    b.bin,
    'standard',
    'Auto-generated location'
FROM stores s
CROSS JOIN (VALUES ('A'), ('B'), ('C')) AS z(zone)
CROSS JOIN (VALUES ('01'), ('02'), ('03')) AS a(aisle)
CROSS JOIN (VALUES ('TOP'), ('MID'), ('BOT')) AS sh(shelf)
CROSS JOIN (VALUES ('01'), ('02'), ('03'), ('04')) AS b(bin)
WHERE s.is_active = true
LIMIT 100;
*/

COMMIT;

-- Verification queries
-- \dt shelf_locations
-- \dt inventory_locations
-- \dt location_assignments_log
-- SELECT * FROM shelf_locations LIMIT 5;