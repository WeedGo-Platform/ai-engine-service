-- Remove Extra Tenant Tables
-- Keep only the main tenants table

BEGIN TRANSACTION;

-- Drop the extra tenant tables
DROP TABLE IF EXISTS tenant_settlement_accounts CASCADE;
DROP TABLE IF EXISTS tenant_payment_providers CASCADE;
DROP TABLE IF EXISTS tenant_subscriptions CASCADE;
DROP TABLE IF EXISTS tenant_features CASCADE;
DROP TABLE IF EXISTS tenant_settings CASCADE;

-- Verify only main tenants table remains
DO $$
DECLARE
    tenant_table_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO tenant_table_count
    FROM information_schema.tables
    WHERE table_schema = 'public'
    AND table_type = 'BASE TABLE'
    AND table_name LIKE '%tenant%';

    RAISE NOTICE 'Remaining tenant-related tables: %', tenant_table_count;
END $$;

COMMIT;