-- ============================================================================
-- Migration: Create Custom Types and Enums
-- Description: Define custom types used throughout the database schema
-- Dependencies: 001_install_extensions.sql
-- ============================================================================

-- Create user_role_simple enum type
DO $$ BEGIN
    CREATE TYPE user_role_simple AS ENUM (
        'customer',
        'staff',
        'store_manager',
        'tenant_admin',
        'super_admin'
    );
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

-- Create helper function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create helper function for generating order numbers
CREATE OR REPLACE FUNCTION generate_order_number()
RETURNS VARCHAR(50) AS $$
BEGIN
    RETURN 'ORD-' || to_char(NOW(), 'YYYYMMDD') || '-' || LPAD(nextval('order_number_seq')::TEXT, 6, '0');
END;
$$ LANGUAGE plpgsql;

-- Create sequence for order numbers
CREATE SEQUENCE IF NOT EXISTS order_number_seq START 1;

COMMENT ON TYPE user_role_simple IS 'User role enumeration for RBAC system';
COMMENT ON FUNCTION update_updated_at_column() IS 'Trigger function to automatically update updated_at timestamp';
COMMENT ON FUNCTION generate_order_number() IS 'Generate sequential order numbers with date prefix';
