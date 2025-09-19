-- POS Transactions to Orders Unification Migration
-- This script merges POS transactions into the unified orders system
-- Created: 2025-09-17

BEGIN TRANSACTION;

-- =========================================
-- STEP 1: Create backup tables
-- =========================================
CREATE TABLE IF NOT EXISTS backup_pos_transactions AS SELECT * FROM pos_transactions;
CREATE TABLE IF NOT EXISTS backup_orders_before_pos AS SELECT * FROM orders;

-- =========================================
-- STEP 2: Add POS-specific columns to orders table
-- =========================================

-- Add order source to track channel (web, pos, mobile, etc.)
ALTER TABLE orders
ADD COLUMN IF NOT EXISTS order_source VARCHAR(20) DEFAULT 'web'
CHECK (order_source IN ('web', 'pos', 'mobile', 'kiosk', 'phone', 'marketplace'));

-- Add POS-specific metadata
ALTER TABLE orders
ADD COLUMN IF NOT EXISTS pos_metadata JSONB;

-- Add channel reference ID for external system tracking
ALTER TABLE orders
ADD COLUMN IF NOT EXISTS channel_reference_id VARCHAR(100);

-- Add cashier_id for POS orders
ALTER TABLE orders
ADD COLUMN IF NOT EXISTS cashier_id UUID;

-- Add receipt_number for POS tracking
ALTER TABLE orders
ADD COLUMN IF NOT EXISTS receipt_number VARCHAR(100);

-- Add order status to replace delivery_status for unified handling
ALTER TABLE orders
ADD COLUMN IF NOT EXISTS order_status VARCHAR(50) DEFAULT 'pending'
CHECK (order_status IN ('pending', 'processing', 'completed', 'cancelled', 'refunded', 'parked', 'void'));

-- Add is_pos_transaction flag for quick filtering
ALTER TABLE orders
ADD COLUMN IF NOT EXISTS is_pos_transaction BOOLEAN DEFAULT FALSE;

-- Create indexes for new fields
CREATE INDEX IF NOT EXISTS idx_orders_order_source ON orders(order_source);
CREATE INDEX IF NOT EXISTS idx_orders_is_pos ON orders(is_pos_transaction);
CREATE INDEX IF NOT EXISTS idx_orders_order_status ON orders(order_status);
CREATE INDEX IF NOT EXISTS idx_orders_receipt_number ON orders(receipt_number);
CREATE INDEX IF NOT EXISTS idx_orders_cashier_id ON orders(cashier_id);

-- =========================================
-- STEP 3: Migrate existing POS transactions to orders
-- =========================================

-- Insert POS transactions into orders table
INSERT INTO orders (
    -- Core fields
    id,
    order_number,
    user_id,
    customer_id,
    store_id,

    -- Items and pricing
    items,
    subtotal,
    tax_amount,
    discount_amount,
    total_amount,

    -- Payment information
    payment_status,
    payment_method,
    payment_details,

    -- POS-specific fields
    order_source,
    order_status,
    is_pos_transaction,
    cashier_id,
    receipt_number,
    channel_reference_id,
    pos_metadata,

    -- Timestamps
    created_at,
    updated_at
)
SELECT
    -- Use existing POS transaction ID to maintain referential integrity
    pt.id,

    -- Generate order number from receipt number or create new
    COALESCE(
        (pt.transaction_data->>'receipt_number'),
        'POS-' || EXTRACT(EPOCH FROM pt.created_at)::TEXT
    ) as order_number,

    -- User mapping (null for anonymous POS transactions)
    CASE
        WHEN pt.customer_id IS NOT NULL THEN p.user_id
        ELSE NULL
    END as user_id,

    -- Customer ID mapping
    pt.customer_id,

    -- Store ID (convert from text to UUID if possible)
    CASE
        WHEN pt.store_id ~ '^[a-fA-F0-9]{8}-[a-fA-F0-9]{4}-[a-fA-F0-9]{4}-[a-fA-F0-9]{4}-[a-fA-F0-9]{12}$'
        THEN pt.store_id::UUID
        ELSE NULL
    END as store_id,

    -- Items from transaction_data
    pt.transaction_data->'items' as items,

    -- Pricing information
    COALESCE((pt.transaction_data->>'subtotal')::NUMERIC, pt.total_amount) as subtotal,
    COALESCE((pt.transaction_data->>'tax')::NUMERIC, 0) as tax_amount,
    COALESCE((pt.transaction_data->>'discounts')::NUMERIC, 0) as discount_amount,
    pt.total_amount,

    -- Payment information
    CASE
        WHEN pt.status = 'completed' THEN 'paid'
        WHEN pt.status = 'parked' THEN 'pending'
        ELSE 'pending'
    END as payment_status,

    COALESCE(pt.transaction_data->>'payment_method', 'cash') as payment_method,
    pt.transaction_data->'payment_details' as payment_details,

    -- POS-specific fields
    'pos' as order_source,
    pt.status as order_status,
    TRUE as is_pos_transaction,

    -- Cashier ID (need to map text to UUID or store in metadata)
    NULL as cashier_id, -- Will store in pos_metadata instead

    pt.transaction_data->>'receipt_number' as receipt_number,
    pt.id::TEXT as channel_reference_id, -- Reference to original POS transaction

    -- Store complete POS metadata
    jsonb_build_object(
        'cashier_id', pt.cashier_id,
        'original_pos_id', pt.id::TEXT,
        'store_id_text', pt.store_id,
        'original_status', pt.status,
        'notes', pt.transaction_data->>'notes',
        'migrated_from', 'pos_transactions',
        'migration_date', CURRENT_TIMESTAMP
    ) as pos_metadata,

    -- Timestamps
    pt.created_at,
    pt.updated_at
FROM pos_transactions pt
LEFT JOIN profiles p ON pt.customer_id = p.id
WHERE NOT EXISTS (
    -- Prevent duplicate migration
    SELECT 1 FROM orders o
    WHERE o.id = pt.id OR o.channel_reference_id = pt.id::TEXT
);

-- =========================================
-- STEP 4: Create views for backward compatibility
-- =========================================

-- Create POS orders view for easy access to POS-specific orders
CREATE OR REPLACE VIEW pos_orders AS
SELECT
    o.*,
    o.pos_metadata->>'cashier_id' as pos_cashier_id,
    o.pos_metadata->>'original_pos_id' as original_pos_transaction_id,
    o.pos_metadata->>'store_id_text' as pos_store_id,
    o.pos_metadata->>'notes' as pos_notes
FROM orders o
WHERE o.order_source = 'pos';

-- Create a view that mimics the old pos_transactions structure
CREATE OR REPLACE VIEW pos_transactions_legacy AS
SELECT
    o.id,
    COALESCE(o.store_id::TEXT, o.pos_metadata->>'store_id_text') as store_id,
    COALESCE(o.pos_metadata->>'cashier_id', 'unknown') as cashier_id,
    o.customer_id,
    jsonb_build_object(
        'items', o.items,
        'subtotal', o.subtotal,
        'tax', o.tax_amount,
        'discounts', o.discount_amount,
        'total', o.total_amount,
        'payment_method', o.payment_method,
        'payment_details', o.payment_details,
        'receipt_number', o.receipt_number,
        'notes', o.pos_metadata->>'notes',
        'status', o.order_status
    ) as transaction_data,
    o.order_status as status,
    o.total_amount,
    o.created_at,
    o.updated_at
FROM orders o
WHERE o.order_source = 'pos';

-- =========================================
-- STEP 5: Create helper functions
-- =========================================

-- Function to create POS order
CREATE OR REPLACE FUNCTION create_pos_order(
    p_store_id UUID,
    p_cashier_id TEXT,
    p_customer_id UUID,
    p_items JSONB,
    p_subtotal NUMERIC,
    p_tax NUMERIC,
    p_discounts NUMERIC,
    p_total NUMERIC,
    p_payment_method TEXT,
    p_payment_details JSONB,
    p_receipt_number TEXT,
    p_status TEXT DEFAULT 'completed'
) RETURNS UUID AS $$
DECLARE
    v_order_id UUID;
    v_order_number TEXT;
BEGIN
    -- Generate order number
    v_order_number := COALESCE(p_receipt_number, 'POS-' || EXTRACT(EPOCH FROM NOW())::TEXT);

    -- Insert into orders table
    INSERT INTO orders (
        order_number,
        customer_id,
        store_id,
        items,
        subtotal,
        tax_amount,
        discount_amount,
        total_amount,
        payment_status,
        payment_method,
        payment_details,
        order_source,
        order_status,
        is_pos_transaction,
        receipt_number,
        pos_metadata
    ) VALUES (
        v_order_number,
        p_customer_id,
        p_store_id,
        p_items,
        p_subtotal,
        p_tax,
        p_discounts,
        p_total,
        CASE WHEN p_status = 'completed' THEN 'paid' ELSE 'pending' END,
        p_payment_method,
        p_payment_details,
        'pos',
        p_status,
        TRUE,
        p_receipt_number,
        jsonb_build_object(
            'cashier_id', p_cashier_id,
            'created_via', 'pos_terminal'
        )
    ) RETURNING id INTO v_order_id;

    RETURN v_order_id;
END;
$$ LANGUAGE plpgsql;

-- =========================================
-- STEP 6: Update sequences and constraints
-- =========================================

-- Add unique constraint on receipt_number for POS orders
CREATE UNIQUE INDEX IF NOT EXISTS idx_orders_unique_receipt
ON orders(receipt_number)
WHERE receipt_number IS NOT NULL;

-- =========================================
-- STEP 7: Grant permissions
-- =========================================
GRANT SELECT ON pos_orders TO weedgo;
GRANT SELECT ON pos_transactions_legacy TO weedgo;
GRANT EXECUTE ON FUNCTION create_pos_order TO weedgo;

-- =========================================
-- VERIFICATION QUERIES
-- =========================================
DO $$
DECLARE
    pos_count INTEGER;
    orders_count INTEGER;
    migrated_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO pos_count FROM backup_pos_transactions;
    SELECT COUNT(*) INTO orders_count FROM orders WHERE order_source = 'pos';
    SELECT COUNT(*) INTO migrated_count FROM orders WHERE pos_metadata->>'migrated_from' = 'pos_transactions';

    RAISE NOTICE 'Original POS transactions: %', pos_count;
    RAISE NOTICE 'POS orders in unified table: %', orders_count;
    RAISE NOTICE 'Newly migrated records: %', migrated_count;

    IF pos_count != orders_count THEN
        RAISE WARNING 'Count mismatch! Check migration results.';
    ELSE
        RAISE NOTICE 'Migration successful! All POS transactions migrated.';
    END IF;
END $$;

-- =========================================
-- OPTIONAL: Archive original pos_transactions table
-- =========================================
-- After verifying migration success, you can rename the original table
-- ALTER TABLE pos_transactions RENAME TO pos_transactions_archived;

COMMIT;

-- =========================================
-- ROLLBACK SCRIPT (Save separately)
-- =========================================
/*
-- To rollback this migration:
BEGIN TRANSACTION;

-- Remove POS orders from orders table
DELETE FROM orders WHERE pos_metadata->>'migrated_from' = 'pos_transactions';

-- Drop new columns
ALTER TABLE orders DROP COLUMN IF EXISTS order_source;
ALTER TABLE orders DROP COLUMN IF EXISTS pos_metadata;
ALTER TABLE orders DROP COLUMN IF EXISTS channel_reference_id;
ALTER TABLE orders DROP COLUMN IF EXISTS cashier_id;
ALTER TABLE orders DROP COLUMN IF EXISTS receipt_number;
ALTER TABLE orders DROP COLUMN IF EXISTS order_status;
ALTER TABLE orders DROP COLUMN IF EXISTS is_pos_transaction;

-- Drop views
DROP VIEW IF EXISTS pos_orders;
DROP VIEW IF EXISTS pos_transactions_legacy;

-- Drop function
DROP FUNCTION IF EXISTS create_pos_order;

-- Restore original pos_transactions if archived
-- ALTER TABLE pos_transactions_archived RENAME TO pos_transactions;

-- Drop indexes
DROP INDEX IF EXISTS idx_orders_order_source;
DROP INDEX IF EXISTS idx_orders_is_pos;
DROP INDEX IF EXISTS idx_orders_order_status;
DROP INDEX IF EXISTS idx_orders_receipt_number;
DROP INDEX IF EXISTS idx_orders_cashier_id;
DROP INDEX IF EXISTS idx_orders_unique_receipt;

COMMIT;
*/