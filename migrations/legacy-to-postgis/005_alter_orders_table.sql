-- ============================================================================
-- Migration: Alter ORDERS Table
-- Description: Add all missing columns from legacy database to orders table
-- Dependencies: 004_alter_stores_table.sql
-- ============================================================================

-- Add missing columns to orders table
ALTER TABLE orders ADD COLUMN IF NOT EXISTS cart_session_id UUID;
ALTER TABLE orders ADD COLUMN IF NOT EXISTS user_profile_id UUID;
ALTER TABLE orders ADD COLUMN IF NOT EXISTS items JSONB NOT NULL DEFAULT '[]'::jsonb;
ALTER TABLE orders ADD COLUMN IF NOT EXISTS payment_details JSONB;
ALTER TABLE orders ADD COLUMN IF NOT EXISTS delivery_status VARCHAR(50) DEFAULT 'pending';
ALTER TABLE orders ADD COLUMN IF NOT EXISTS delivery_time TIMESTAMP WITHOUT TIME ZONE;
ALTER TABLE orders ADD COLUMN IF NOT EXISTS special_instructions TEXT;
ALTER TABLE orders ADD COLUMN IF NOT EXISTS tenant_id UUID;
ALTER TABLE orders ADD COLUMN IF NOT EXISTS ai_agent_id UUID;
ALTER TABLE orders ADD COLUMN IF NOT EXISTS tax_breakdown JSONB;
ALTER TABLE orders ADD COLUMN IF NOT EXISTS order_source VARCHAR(20) DEFAULT 'web';
ALTER TABLE orders ADD COLUMN IF NOT EXISTS pos_metadata JSONB;
ALTER TABLE orders ADD COLUMN IF NOT EXISTS channel_reference_id VARCHAR(100);
ALTER TABLE orders ADD COLUMN IF NOT EXISTS cashier_id UUID;
ALTER TABLE orders ADD COLUMN IF NOT EXISTS receipt_number VARCHAR(100);
ALTER TABLE orders ADD COLUMN IF NOT EXISTS order_status VARCHAR(50) DEFAULT 'pending';
ALTER TABLE orders ADD COLUMN IF NOT EXISTS is_pos_transaction BOOLEAN DEFAULT false;
ALTER TABLE orders ADD COLUMN IF NOT EXISTS tip_amount NUMERIC(10,2) DEFAULT 0.00;
ALTER TABLE orders ADD COLUMN IF NOT EXISTS delivery_type VARCHAR(20) DEFAULT 'delivery';
ALTER TABLE orders ADD COLUMN IF NOT EXISTS pickup_time VARCHAR(50);
ALTER TABLE orders ADD COLUMN IF NOT EXISTS promo_code VARCHAR(50);

-- Rename existing columns to match legacy schema
ALTER TABLE orders RENAME COLUMN delivery_method TO delivery_type_old;
ALTER TABLE orders RENAME COLUMN status TO order_status_old;

-- Move data if needed
UPDATE orders SET delivery_type = delivery_type_old WHERE delivery_type_old IS NOT NULL;
UPDATE orders SET order_status = order_status_old WHERE order_status_old IS NOT NULL;

-- Drop old columns
ALTER TABLE orders DROP COLUMN IF EXISTS delivery_type_old;
ALTER TABLE orders DROP COLUMN IF EXISTS order_status_old;

-- Add missing indexes
CREATE INDEX IF NOT EXISTS idx_orders_cashier_id ON orders(cashier_id);
CREATE INDEX IF NOT EXISTS idx_orders_created ON orders(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_orders_created_at ON orders(created_at);
CREATE INDEX IF NOT EXISTS idx_orders_delivery_status ON orders(delivery_status);
CREATE INDEX IF NOT EXISTS idx_orders_delivery_type ON orders(delivery_type);
CREATE INDEX IF NOT EXISTS idx_orders_is_pos ON orders(is_pos_transaction);
CREATE INDEX IF NOT EXISTS idx_orders_order_source ON orders(order_source);
CREATE INDEX IF NOT EXISTS idx_orders_order_status ON orders(order_status);
CREATE INDEX IF NOT EXISTS idx_orders_payment_status ON orders(payment_status);
CREATE INDEX IF NOT EXISTS idx_orders_promo_code ON orders(promo_code);
CREATE INDEX IF NOT EXISTS idx_orders_receipt_number ON orders(receipt_number);
CREATE UNIQUE INDEX IF NOT EXISTS idx_orders_unique_receipt ON orders(receipt_number) WHERE receipt_number IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_orders_user_id ON orders(user_id);

-- Add check constraints
ALTER TABLE orders DROP CONSTRAINT IF EXISTS orders_delivery_type_check;
ALTER TABLE orders ADD CONSTRAINT orders_delivery_type_check
    CHECK (delivery_type IN ('delivery', 'pickup'));

ALTER TABLE orders DROP CONSTRAINT IF EXISTS orders_order_source_check;
ALTER TABLE orders ADD CONSTRAINT orders_order_source_check
    CHECK (order_source IN ('web', 'pos', 'mobile', 'kiosk', 'phone', 'marketplace'));

ALTER TABLE orders DROP CONSTRAINT IF EXISTS orders_order_status_check;
ALTER TABLE orders ADD CONSTRAINT orders_order_status_check
    CHECK (order_status IN ('pending', 'processing', 'completed', 'cancelled', 'refunded', 'parked', 'void'));

-- Add trigger for updated_at
DROP TRIGGER IF EXISTS update_orders_updated_at ON orders;
CREATE TRIGGER update_orders_updated_at
    BEFORE UPDATE ON orders
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

COMMENT ON COLUMN orders.items IS 'Order line items stored as JSONB array';
COMMENT ON COLUMN orders.ai_agent_id IS 'ID of AI agent that assisted with this order';
COMMENT ON COLUMN orders.order_source IS 'Channel where order was placed (web, pos, mobile, kiosk, phone, marketplace)';
COMMENT ON COLUMN orders.pos_metadata IS 'POS-specific metadata for in-store transactions';
COMMENT ON COLUMN orders.receipt_number IS 'POS receipt number for in-store transactions';
COMMENT ON COLUMN orders.is_pos_transaction IS 'Flag indicating this is a POS transaction';
COMMENT ON COLUMN orders.tip_amount IS 'Customer tip amount';
COMMENT ON COLUMN orders.delivery_type IS 'Delivery method: delivery or pickup';
COMMENT ON COLUMN orders.promo_code IS 'Promotional code applied to order';
