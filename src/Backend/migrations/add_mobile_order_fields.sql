-- Migration: Add mobile app order fields
-- Adds tip_amount, delivery_type, pickup_time, and promo_code to orders table

-- Add tip_amount column
ALTER TABLE orders
ADD COLUMN IF NOT EXISTS tip_amount NUMERIC(10,2) DEFAULT 0.00;

-- Add delivery_type column (delivery or pickup)
ALTER TABLE orders
ADD COLUMN IF NOT EXISTS delivery_type VARCHAR(20) DEFAULT 'delivery'
CHECK (delivery_type IN ('delivery', 'pickup'));

-- Add pickup_time column for scheduled pickups
ALTER TABLE orders
ADD COLUMN IF NOT EXISTS pickup_time VARCHAR(50);

-- Add promo_code column to track applied promotions
ALTER TABLE orders
ADD COLUMN IF NOT EXISTS promo_code VARCHAR(50);

-- Add index for delivery_type
CREATE INDEX IF NOT EXISTS idx_orders_delivery_type ON orders(delivery_type);

-- Add index for promo_code usage tracking
CREATE INDEX IF NOT EXISTS idx_orders_promo_code ON orders(promo_code);

-- Comment for documentation
COMMENT ON COLUMN orders.tip_amount IS 'Tip amount added by customer at checkout';
COMMENT ON COLUMN orders.delivery_type IS 'Order fulfillment type: delivery or pickup';
COMMENT ON COLUMN orders.pickup_time IS 'Scheduled pickup time for pickup orders';
COMMENT ON COLUMN orders.promo_code IS 'Promotional code applied to this order';

-- Migration complete
