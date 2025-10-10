-- ============================================================================
-- Migration: Alter STORES Table
-- Description: Add all missing columns from legacy database to stores table
-- Dependencies: 003_alter_users_table.sql
-- ============================================================================

-- Add missing columns to stores table
ALTER TABLE stores ADD COLUMN IF NOT EXISTS province_territory_id UUID NOT NULL DEFAULT gen_random_uuid();
ALTER TABLE stores ADD COLUMN IF NOT EXISTS address JSONB DEFAULT '{}'::jsonb;
ALTER TABLE stores ADD COLUMN IF NOT EXISTS phone VARCHAR(50);
ALTER TABLE stores ADD COLUMN IF NOT EXISTS email VARCHAR(255);
ALTER TABLE stores ADD COLUMN IF NOT EXISTS hours JSONB DEFAULT '{}'::jsonb;
ALTER TABLE stores ADD COLUMN IF NOT EXISTS timezone VARCHAR(50) DEFAULT 'America/Toronto';
ALTER TABLE stores ADD COLUMN IF NOT EXISTS license_number VARCHAR(100);
ALTER TABLE stores ADD COLUMN IF NOT EXISTS license_expiry DATE;
ALTER TABLE stores ADD COLUMN IF NOT EXISTS tax_rate NUMERIC(5,2);
ALTER TABLE stores ADD COLUMN IF NOT EXISTS delivery_radius_km INTEGER DEFAULT 10;
ALTER TABLE stores ADD COLUMN IF NOT EXISTS delivery_enabled BOOLEAN DEFAULT true;
ALTER TABLE stores ADD COLUMN IF NOT EXISTS pickup_enabled BOOLEAN DEFAULT true;
ALTER TABLE stores ADD COLUMN IF NOT EXISTS kiosk_enabled BOOLEAN DEFAULT false;
ALTER TABLE stores ADD COLUMN IF NOT EXISTS pos_enabled BOOLEAN DEFAULT true;
ALTER TABLE stores ADD COLUMN IF NOT EXISTS ecommerce_enabled BOOLEAN DEFAULT true;
ALTER TABLE stores ADD COLUMN IF NOT EXISTS settings JSONB DEFAULT '{}'::jsonb;
ALTER TABLE stores ADD COLUMN IF NOT EXISTS pos_integration JSONB DEFAULT '{}'::jsonb;
ALTER TABLE stores ADD COLUMN IF NOT EXISTS seo_config JSONB DEFAULT '{}'::jsonb;
ALTER TABLE stores ADD COLUMN IF NOT EXISTS latitude NUMERIC(10,8);
ALTER TABLE stores ADD COLUMN IF NOT EXISTS longitude NUMERIC(11,8);
ALTER TABLE stores ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP;
ALTER TABLE stores ADD COLUMN IF NOT EXISTS pos_payment_terminal_settings JSONB DEFAULT '{}'::jsonb;

-- Add missing indexes
CREATE INDEX IF NOT EXISTS idx_stores_location ON stores(latitude, longitude);
CREATE INDEX IF NOT EXISTS idx_stores_province_territory ON stores(province_territory_id);
CREATE INDEX IF NOT EXISTS idx_stores_status ON stores(status);
CREATE INDEX IF NOT EXISTS idx_stores_tenant ON stores(tenant_id);

-- Add check constraint for status
ALTER TABLE stores DROP CONSTRAINT IF EXISTS stores_status_check;
ALTER TABLE stores ADD CONSTRAINT stores_status_check
    CHECK (status IN ('active', 'inactive', 'suspended'));

-- Add trigger for updated_at
DROP TRIGGER IF EXISTS update_stores_updated_at ON stores;
CREATE TRIGGER update_stores_updated_at
    BEFORE UPDATE ON stores
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

COMMENT ON COLUMN stores.province_territory_id IS 'Reference to Canadian province/territory for compliance';
COMMENT ON COLUMN stores.address IS 'Store physical address in JSONB format';
COMMENT ON COLUMN stores.hours IS 'Store operating hours by day of week in JSONB format';
COMMENT ON COLUMN stores.license_number IS 'Cannabis retail license number (required for compliance)';
COMMENT ON COLUMN stores.license_expiry IS 'Cannabis license expiration date';
COMMENT ON COLUMN stores.delivery_radius_km IS 'Maximum delivery radius in kilometers';
COMMENT ON COLUMN stores.latitude IS 'Geographic latitude for location-based services';
COMMENT ON COLUMN stores.longitude IS 'Geographic longitude for location-based services';
COMMENT ON COLUMN stores.pos_integration IS 'POS system integration configuration';
COMMENT ON COLUMN stores.pos_payment_terminal_settings IS 'Payment terminal configuration for POS';
