-- Restore Inventory Tables
-- This script recreates the inventory tables that were deleted

BEGIN TRANSACTION;

-- =========================================
-- Restore inventory management tables
-- =========================================

-- 1. Inventory movements tracking
CREATE TABLE IF NOT EXISTS ocs_inventory_movements (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    inventory_id UUID REFERENCES ocs_inventory(id) ON DELETE CASCADE,
    movement_type VARCHAR(50) NOT NULL, -- 'purchase', 'sale', 'adjustment', 'transfer'
    quantity INTEGER NOT NULL,
    reference_type VARCHAR(50), -- 'order', 'adjustment', 'transfer'
    reference_id VARCHAR(100),
    reason TEXT,
    performed_by UUID,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB DEFAULT '{}'::jsonb
);

-- 2. Inventory snapshots for history
CREATE TABLE IF NOT EXISTS ocs_inventory_snapshots (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    inventory_id UUID REFERENCES ocs_inventory(id) ON DELETE CASCADE,
    quantity_on_hand INTEGER NOT NULL,
    available_quantity INTEGER NOT NULL,
    reserved_quantity INTEGER DEFAULT 0,
    snapshot_date DATE NOT NULL,
    last_movement_id UUID,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 3. Inventory reservations
CREATE TABLE IF NOT EXISTS ocs_inventory_reservations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    inventory_id UUID REFERENCES ocs_inventory(id) ON DELETE CASCADE,
    order_id UUID,
    cart_session_id UUID,
    quantity INTEGER NOT NULL,
    expires_at TIMESTAMP,
    status VARCHAR(50) DEFAULT 'active', -- 'active', 'fulfilled', 'expired', 'cancelled'
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 4. Inventory locations
CREATE TABLE IF NOT EXISTS inventory_locations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    store_id UUID REFERENCES stores(id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL,
    code VARCHAR(50) UNIQUE,
    type VARCHAR(50), -- 'shelf', 'backroom', 'vault', 'display'
    zone VARCHAR(50),
    aisle VARCHAR(20),
    shelf VARCHAR(20),
    bin VARCHAR(20),
    capacity INTEGER,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 5. Location assignments log
CREATE TABLE IF NOT EXISTS location_assignments_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    inventory_id UUID REFERENCES ocs_inventory(id) ON DELETE CASCADE,
    location_id UUID REFERENCES inventory_locations(id) ON DELETE SET NULL,
    quantity INTEGER NOT NULL,
    assigned_by UUID,
    assignment_type VARCHAR(50), -- 'initial', 'restock', 'reorganize'
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_inventory_movements_inventory_id ON ocs_inventory_movements(inventory_id);
CREATE INDEX IF NOT EXISTS idx_inventory_movements_created_at ON ocs_inventory_movements(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_inventory_snapshots_inventory_id ON ocs_inventory_snapshots(inventory_id);
CREATE INDEX IF NOT EXISTS idx_inventory_snapshots_date ON ocs_inventory_snapshots(snapshot_date DESC);
CREATE INDEX IF NOT EXISTS idx_inventory_reservations_inventory_id ON ocs_inventory_reservations(inventory_id);
CREATE INDEX IF NOT EXISTS idx_inventory_reservations_status ON ocs_inventory_reservations(status);
CREATE INDEX IF NOT EXISTS idx_inventory_locations_store_id ON inventory_locations(store_id);
CREATE INDEX IF NOT EXISTS idx_location_assignments_inventory_id ON location_assignments_log(inventory_id);

-- =========================================
-- Restore ocs_inventory_logs if it doesn't exist
-- =========================================
CREATE TABLE IF NOT EXISTS ocs_inventory_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    inventory_id UUID REFERENCES ocs_inventory(id) ON DELETE CASCADE,
    action VARCHAR(50) NOT NULL, -- 'create', 'update', 'delete', 'adjust'
    previous_quantity INTEGER,
    new_quantity INTEGER,
    change_quantity INTEGER,
    reason TEXT,
    performed_by UUID,
    order_id UUID,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB DEFAULT '{}'::jsonb
);

CREATE INDEX IF NOT EXISTS idx_inventory_logs_inventory_id ON ocs_inventory_logs(inventory_id);
CREATE INDEX IF NOT EXISTS idx_inventory_logs_created_at ON ocs_inventory_logs(created_at DESC);

COMMIT;

-- Verify restoration
DO $$
DECLARE
    table_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO table_count
    FROM information_schema.tables
    WHERE table_schema = 'public'
    AND table_type = 'BASE TABLE'
    AND table_name IN (
        'ocs_inventory_movements',
        'ocs_inventory_snapshots',
        'ocs_inventory_reservations',
        'inventory_locations',
        'location_assignments_log',
        'ocs_inventory_logs'
    );

    RAISE NOTICE 'Restored % inventory-related tables', table_count;
END $$;