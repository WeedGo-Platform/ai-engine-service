-- Migration: Device Management System
-- Description: Add device registration and management support to stores.settings
-- Date: 2025-10-01
-- Version: 1.0.0

-- =====================================================
-- 1. UPDATE STORES TABLE
-- =====================================================
-- Ensure stores.settings JSONB column exists (should already exist from migration 008)
-- Add sample device settings structure for documentation

COMMENT ON COLUMN stores.settings IS
'JSONB column for store configuration including device management.
Structure:
{
  "devices": [
    {
      "device_id": "KIOSK-001",
      "device_type": "kiosk|pos|menu_display",
      "name": "Front Entrance Kiosk",
      "location": "Main Floor",
      "passcode_hash": "bcrypt_hash_here",
      "status": "active|inactive|pending_pairing",
      "paired_at": "2025-10-01T10:30:00Z",
      "last_seen": "2025-10-01T15:45:00Z",
      "created_at": "2025-09-15T09:00:00Z",
      "created_by": "admin-user-id",
      "updated_at": "2025-10-01T10:30:00Z",
      "metadata": {
        "hardware_id": "expo-session-id",
        "platform": "ios",
        "app_version": "1.0.0",
        "model": "iPad Pro",
        "ip_address": "192.168.1.100",
        "notes": "Primary customer-facing kiosk"
      },
      "permissions": {
        "can_process_orders": true,
        "can_access_inventory": true,
        "can_view_analytics": false,
        "restricted_categories": []
      },
      "configuration": {
        "idle_timeout": 120,
        "session_timeout": 1800,
        "language": "en",
        "theme": "modern",
        "enable_voice": false,
        "enable_budtender": true,
        "max_cart_value": 500.00,
        "receipt_printer_id": null
      }
    }
  ],
  "device_policy": {
    "max_devices": null,
    "require_approval": false,
    "auto_unpair_inactive_days": 30,
    "passcode_policy": {
      "min_length": 4,
      "require_uppercase": false,
      "require_numbers": true,
      "require_special_chars": false,
      "expiry_days": null
    }
  }
}';

-- =====================================================
-- 2. CREATE INDEXES FOR DEVICE QUERIES
-- =====================================================
-- Index for searching devices by device_id across all stores
CREATE INDEX IF NOT EXISTS idx_stores_settings_devices_device_id
ON stores USING GIN ((settings->'devices'));

-- Index for searching active devices
CREATE INDEX IF NOT EXISTS idx_stores_settings_devices_status
ON stores USING GIN ((settings->'devices'));

-- =====================================================
-- 3. CREATE HELPER FUNCTIONS
-- =====================================================

-- Function to add a device to a store
CREATE OR REPLACE FUNCTION add_device_to_store(
    p_store_id UUID,
    p_device_id VARCHAR,
    p_device_type VARCHAR,
    p_name VARCHAR,
    p_location VARCHAR,
    p_passcode_hash VARCHAR,
    p_created_by UUID,
    p_permissions JSONB DEFAULT '{}'::JSONB,
    p_configuration JSONB DEFAULT '{}'::JSONB
) RETURNS JSONB AS $$
DECLARE
    v_device JSONB;
    v_devices JSONB;
    v_current_settings JSONB;
BEGIN
    -- Get current settings
    SELECT settings INTO v_current_settings FROM stores WHERE id = p_store_id;

    IF v_current_settings IS NULL THEN
        v_current_settings := '{}'::JSONB;
    END IF;

    -- Get current devices array or initialize
    v_devices := COALESCE(v_current_settings->'devices', '[]'::JSONB);

    -- Create new device object
    v_device := jsonb_build_object(
        'device_id', p_device_id,
        'device_type', p_device_type,
        'name', p_name,
        'location', p_location,
        'passcode_hash', p_passcode_hash,
        'status', 'pending_pairing',
        'paired_at', NULL,
        'last_seen', NULL,
        'created_at', NOW(),
        'created_by', p_created_by,
        'updated_at', NOW(),
        'metadata', '{}'::JSONB,
        'permissions', p_permissions,
        'configuration', p_configuration
    );

    -- Check if device already exists
    IF v_devices @> jsonb_build_array(jsonb_build_object('device_id', p_device_id)) THEN
        RAISE EXCEPTION 'Device with ID % already exists in this store', p_device_id;
    END IF;

    -- Add device to array
    v_devices := v_devices || jsonb_build_array(v_device);

    -- Update settings
    v_current_settings := jsonb_set(
        v_current_settings,
        '{devices}',
        v_devices
    );

    -- Update store
    UPDATE stores
    SET settings = v_current_settings,
        updated_at = NOW()
    WHERE id = p_store_id;

    RETURN v_device;
END;
$$ LANGUAGE plpgsql;

-- Function to update a device
CREATE OR REPLACE FUNCTION update_device_in_store(
    p_store_id UUID,
    p_device_id VARCHAR,
    p_updates JSONB
) RETURNS JSONB AS $$
DECLARE
    v_devices JSONB;
    v_device JSONB;
    v_updated_device JSONB;
    v_device_index INT;
    v_current_settings JSONB;
BEGIN
    -- Get current settings
    SELECT settings INTO v_current_settings FROM stores WHERE id = p_store_id;

    IF v_current_settings IS NULL THEN
        RAISE EXCEPTION 'Store not found';
    END IF;

    v_devices := v_current_settings->'devices';

    IF v_devices IS NULL THEN
        RAISE EXCEPTION 'No devices found in store';
    END IF;

    -- Find device index
    SELECT i - 1 INTO v_device_index
    FROM jsonb_array_elements(v_devices) WITH ORDINALITY arr(elem, i)
    WHERE elem->>'device_id' = p_device_id;

    IF v_device_index IS NULL THEN
        RAISE EXCEPTION 'Device % not found in store', p_device_id;
    END IF;

    -- Get current device
    v_device := v_devices->v_device_index;

    -- Merge updates
    v_updated_device := v_device || p_updates || jsonb_build_object('updated_at', NOW());

    -- Replace device in array
    v_devices := jsonb_set(
        v_devices,
        ARRAY[v_device_index::text],
        v_updated_device
    );

    -- Update settings
    v_current_settings := jsonb_set(
        v_current_settings,
        '{devices}',
        v_devices
    );

    -- Update store
    UPDATE stores
    SET settings = v_current_settings,
        updated_at = NOW()
    WHERE id = p_store_id;

    RETURN v_updated_device;
END;
$$ LANGUAGE plpgsql;

-- Function to remove a device
CREATE OR REPLACE FUNCTION remove_device_from_store(
    p_store_id UUID,
    p_device_id VARCHAR
) RETURNS BOOLEAN AS $$
DECLARE
    v_devices JSONB;
    v_filtered_devices JSONB;
    v_current_settings JSONB;
BEGIN
    -- Get current settings
    SELECT settings INTO v_current_settings FROM stores WHERE id = p_store_id;

    IF v_current_settings IS NULL THEN
        RETURN FALSE;
    END IF;

    v_devices := v_current_settings->'devices';

    IF v_devices IS NULL THEN
        RETURN FALSE;
    END IF;

    -- Filter out the device
    SELECT jsonb_agg(elem)
    INTO v_filtered_devices
    FROM jsonb_array_elements(v_devices) elem
    WHERE elem->>'device_id' != p_device_id;

    IF v_filtered_devices IS NULL THEN
        v_filtered_devices := '[]'::JSONB;
    END IF;

    -- Update settings
    v_current_settings := jsonb_set(
        v_current_settings,
        '{devices}',
        v_filtered_devices
    );

    -- Update store
    UPDATE stores
    SET settings = v_current_settings,
        updated_at = NOW()
    WHERE id = p_store_id;

    RETURN TRUE;
END;
$$ LANGUAGE plpgsql;

-- Function to find device across all stores
CREATE OR REPLACE FUNCTION find_device_by_id(p_device_id VARCHAR)
RETURNS TABLE (
    store_id UUID,
    tenant_id UUID,
    device JSONB,
    store_name VARCHAR,
    tenant_name VARCHAR
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        s.id as store_id,
        s.tenant_id,
        elem as device,
        s.name as store_name,
        t.name as tenant_name
    FROM stores s
    JOIN tenants t ON s.tenant_id = t.id
    CROSS JOIN LATERAL jsonb_array_elements(s.settings->'devices') elem
    WHERE elem->>'device_id' = p_device_id
    AND s.status = 'active';
END;
$$ LANGUAGE plpgsql;

-- =====================================================
-- 4. ADD SAMPLE DEVICE TO FIRST STORE (FOR TESTING)
-- =====================================================
-- This is commented out - uncomment to add sample data
/*
DO $$
DECLARE
    v_store_id UUID;
    v_admin_id UUID;
    v_passcode_hash VARCHAR := '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5NU8RVL4Z3Zke'; -- bcrypt hash of '1234'
BEGIN
    -- Get first store
    SELECT id INTO v_store_id FROM stores LIMIT 1;

    -- Get first admin user
    SELECT id INTO v_admin_id FROM users WHERE role = 'admin' LIMIT 1;

    IF v_store_id IS NOT NULL THEN
        -- Add sample kiosk device
        PERFORM add_device_to_store(
            v_store_id,
            'KIOSK-001',
            'kiosk',
            'Front Entrance Kiosk',
            'Main Floor',
            v_passcode_hash,
            v_admin_id,
            '{"can_process_orders": true, "can_access_inventory": true}'::JSONB,
            '{"idle_timeout": 120, "enable_budtender": true}'::JSONB
        );

        -- Add sample POS device
        PERFORM add_device_to_store(
            v_store_id,
            'POS-MAIN-01',
            'pos',
            'Main Counter POS',
            'Counter 1',
            v_passcode_hash,
            v_admin_id,
            '{"can_process_orders": true, "can_access_inventory": true, "can_view_analytics": true}'::JSONB,
            '{"auto_lock_minutes": 5}'::JSONB
        );

        RAISE NOTICE 'Sample devices added to store %', v_store_id;
    END IF;
END $$;
*/

-- =====================================================
-- 5. VERIFICATION QUERIES
-- =====================================================
-- Run these to verify the migration

-- Check stores with devices
-- SELECT id, name, jsonb_array_length(settings->'devices') as device_count
-- FROM stores
-- WHERE settings->'devices' IS NOT NULL;

-- Find a specific device
-- SELECT * FROM find_device_by_id('KIOSK-001');

-- List all devices across all stores
-- SELECT
--     s.id as store_id,
--     s.name as store_name,
--     elem->>'device_id' as device_id,
--     elem->>'device_type' as device_type,
--     elem->>'name' as device_name,
--     elem->>'location' as location,
--     elem->>'status' as status
-- FROM stores s
-- CROSS JOIN LATERAL jsonb_array_elements(s.settings->'devices') elem
-- WHERE s.settings->'devices' IS NOT NULL;

-- =====================================================
-- ROLLBACK (if needed)
-- =====================================================
-- DROP FUNCTION IF EXISTS add_device_to_store;
-- DROP FUNCTION IF EXISTS update_device_in_store;
-- DROP FUNCTION IF EXISTS remove_device_from_store;
-- DROP FUNCTION IF EXISTS find_device_by_id;
-- DROP INDEX IF EXISTS idx_stores_settings_devices_device_id;
-- DROP INDEX IF EXISTS idx_stores_settings_devices_status;

COMMENT ON FUNCTION add_device_to_store IS 'Add a new device to a store';
COMMENT ON FUNCTION update_device_in_store IS 'Update device properties';
COMMENT ON FUNCTION remove_device_from_store IS 'Remove a device from store';
COMMENT ON FUNCTION find_device_by_id IS 'Find device across all stores by device_id';
