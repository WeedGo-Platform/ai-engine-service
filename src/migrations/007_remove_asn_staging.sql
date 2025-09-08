-- Migration: Remove ASN staging table (not needed for client-side processing)
-- Date: 2025-09-08
-- Description: Removes the ASN staging table and functions that were incorrectly added

BEGIN;

-- Drop the staging table if it exists
DROP TABLE IF EXISTS asn_import_staging CASCADE;

-- Drop the functions that were created for server-side processing
DROP FUNCTION IF EXISTS process_asn_to_purchase_order CASCADE;

-- Keep the check_inventory_exists function as it may be useful
-- Keep the receive_purchase_order function as it's still needed
-- Keep all the columns added to purchase_orders and purchase_order_items tables

COMMIT;