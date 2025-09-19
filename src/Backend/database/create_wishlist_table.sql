-- Drop existing objects if they exist
DROP VIEW IF EXISTS wishlist_details CASCADE;
DROP FUNCTION IF EXISTS get_wishlist_stats CASCADE;
DROP TABLE IF EXISTS wishlist CASCADE;

-- Create wishlist table for storing user's favorite products
CREATE TABLE IF NOT EXISTS wishlist (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    customer_id UUID NOT NULL,
    product_id UUID NOT NULL,
    store_id UUID NOT NULL,
    added_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    notes TEXT,
    priority INTEGER DEFAULT 0, -- 0: normal, 1: high priority
    notify_on_sale BOOLEAN DEFAULT FALSE,
    notify_on_restock BOOLEAN DEFAULT FALSE,

    -- Ensure unique combination of customer and product per store
    CONSTRAINT unique_wishlist_item UNIQUE (customer_id, product_id, store_id),

    -- Foreign key constraints (assuming these tables exist)
    -- CONSTRAINT fk_customer FOREIGN KEY (customer_id) REFERENCES customer_users(id) ON DELETE CASCADE,
    -- CONSTRAINT fk_product FOREIGN KEY (product_id) REFERENCES ocs_inventory(id) ON DELETE CASCADE,
    -- CONSTRAINT fk_store FOREIGN KEY (store_id) REFERENCES stores(id) ON DELETE CASCADE

    -- Indexes for performance
    CONSTRAINT wishlist_customer_idx UNIQUE (customer_id, product_id, store_id)
);

-- Create indexes for better query performance
CREATE INDEX IF NOT EXISTS idx_wishlist_customer ON wishlist(customer_id);
CREATE INDEX IF NOT EXISTS idx_wishlist_store ON wishlist(store_id);
CREATE INDEX IF NOT EXISTS idx_wishlist_added_at ON wishlist(added_at DESC);
CREATE INDEX IF NOT EXISTS idx_wishlist_priority ON wishlist(priority DESC);

-- Create a view for wishlist with product details using existing comprehensive view
CREATE OR REPLACE VIEW wishlist_details AS
SELECT
    w.id as wishlist_id,
    w.customer_id,
    w.product_id,
    w.store_id,
    w.added_at,
    w.notes,
    w.priority,
    w.notify_on_sale,
    w.notify_on_restock,
    p.product_name,
    p.brand,
    p.supplier_name,
    p.category,
    p.sub_category,
    p.strain_type,
    p.thc_content_per_unit,
    p.cbd_content_per_unit,
    p.unit_price,
    p.retail_price,
    p.quantity_available,
    p.image_url,
    p.rating,
    p.rating_count,
    p.is_available,
    p.terpenes,
    p.product_size,
    p.unit_of_measure
FROM wishlist w
LEFT JOIN comprehensive_product_inventory_view p
    ON w.product_id = p.product_id
    AND w.store_id = p.store_id;

-- Function to get wishlist statistics for a customer
CREATE OR REPLACE FUNCTION get_wishlist_stats(p_customer_id UUID)
RETURNS TABLE (
    total_items INTEGER,
    high_priority_items INTEGER,
    on_sale_items INTEGER,
    out_of_stock_items INTEGER,
    total_value DECIMAL
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        COUNT(*)::INTEGER as total_items,
        COUNT(CASE WHEN w.priority = 1 THEN 1 END)::INTEGER as high_priority_items,
        0::INTEGER as on_sale_items, -- Sales tracking would need separate table
        COUNT(CASE WHEN p.quantity_available = 0 OR p.is_available = false THEN 1 END)::INTEGER as out_of_stock_items,
        COALESCE(SUM(COALESCE(p.retail_price, p.unit_price)), 0)::DECIMAL as total_value
    FROM wishlist w
    LEFT JOIN comprehensive_product_inventory_view p
        ON w.product_id = p.product_id
        AND w.store_id = p.store_id
    WHERE w.customer_id = p_customer_id;
END;
$$ LANGUAGE plpgsql;