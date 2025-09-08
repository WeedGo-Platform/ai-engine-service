-- Migration: Dashboard Compatibility Updates
-- Purpose: Align database schema with dashboard UI expectations

-- 1. Create products table (dashboard expects 'products' not 'product_catalog')
CREATE TABLE IF NOT EXISTS products (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    sku VARCHAR(100) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    category VARCHAR(100),
    subcategory VARCHAR(100),
    brand VARCHAR(100),
    supplier VARCHAR(100),
    unit_price DECIMAL(10, 2),
    thc_content DECIMAL(5, 2),
    cbd_content DECIMAL(5, 2),
    strain_type VARCHAR(50),
    terpenes JSONB,
    effects JSONB,
    medical_benefits JSONB,
    image_url TEXT,
    tags JSONB,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Copy data from product_catalog if it exists
INSERT INTO products (
    sku, name, description, category, subcategory, brand, supplier,
    unit_price, thc_content, cbd_content, strain_type, terpenes,
    effects, medical_benefits, image_url, tags, is_active
)
SELECT 
    sku, name, description, category, subcategory, brand, supplier,
    unit_price, thc_content, cbd_content, strain_type, terpenes,
    effects, medical_benefits, image_url, tags, is_active
FROM product_catalog
ON CONFLICT (sku) DO NOTHING;

-- 2. Add missing columns to suppliers table
ALTER TABLE suppliers 
ADD COLUMN IF NOT EXISTS city VARCHAR(100),
ADD COLUMN IF NOT EXISTS state VARCHAR(50),
ADD COLUMN IF NOT EXISTS postal_code VARCHAR(20),
ADD COLUMN IF NOT EXISTS country VARCHAR(100),
ADD COLUMN IF NOT EXISTS notes TEXT;

-- 3. Create customers table if it doesn't exist (dashboard expects this)
CREATE TABLE IF NOT EXISTS customers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    phone VARCHAR(20),
    date_of_birth DATE,
    address TEXT,
    city VARCHAR(100),
    state VARCHAR(50),
    postal_code VARCHAR(20),
    country VARCHAR(100),
    loyalty_points INTEGER DEFAULT 0,
    customer_type VARCHAR(50) DEFAULT 'regular',
    preferred_payment_method VARCHAR(50),
    marketing_consent BOOLEAN DEFAULT false,
    notes TEXT,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 4. Add missing columns to orders table if needed
ALTER TABLE orders
ADD COLUMN IF NOT EXISTS order_number VARCHAR(50) UNIQUE,
ADD COLUMN IF NOT EXISTS customer_name VARCHAR(255),
ADD COLUMN IF NOT EXISTS customer_email VARCHAR(255),
ADD COLUMN IF NOT EXISTS delivery_address TEXT,
ADD COLUMN IF NOT EXISTS payment_method VARCHAR(50),
ADD COLUMN IF NOT EXISTS payment_status VARCHAR(50) DEFAULT 'pending',
ADD COLUMN IF NOT EXISTS delivery_date TIMESTAMP,
ADD COLUMN IF NOT EXISTS tracking_number VARCHAR(100),
ADD COLUMN IF NOT EXISTS discount_amount DECIMAL(10, 2) DEFAULT 0,
ADD COLUMN IF NOT EXISTS tax_amount DECIMAL(10, 2) DEFAULT 0,
ADD COLUMN IF NOT EXISTS shipping_cost DECIMAL(10, 2) DEFAULT 0,
ADD COLUMN IF NOT EXISTS notes TEXT;

-- Generate order numbers for existing orders without them
UPDATE orders 
SET order_number = 'ORD-' || EXTRACT(YEAR FROM created_at) || '-' || LPAD(id::text, 6, '0')
WHERE order_number IS NULL;

-- 5. Create order_items table if it doesn't exist
CREATE TABLE IF NOT EXISTS order_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    order_id UUID REFERENCES orders(id) ON DELETE CASCADE,
    product_id UUID,
    product_sku VARCHAR(100),
    product_name VARCHAR(255),
    quantity INTEGER NOT NULL,
    unit_price DECIMAL(10, 2) NOT NULL,
    discount_amount DECIMAL(10, 2) DEFAULT 0,
    total_price DECIMAL(10, 2) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 6. Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_products_sku ON products(sku);
CREATE INDEX IF NOT EXISTS idx_products_category ON products(category);
CREATE INDEX IF NOT EXISTS idx_products_active ON products(is_active);
CREATE INDEX IF NOT EXISTS idx_products_search ON products USING gin(to_tsvector('english', name || ' ' || COALESCE(description, '')));

CREATE INDEX IF NOT EXISTS idx_customers_email ON customers(email);
CREATE INDEX IF NOT EXISTS idx_customers_active ON customers(is_active);

CREATE INDEX IF NOT EXISTS idx_orders_order_number ON orders(order_number);
CREATE INDEX IF NOT EXISTS idx_orders_status ON orders(status);
CREATE INDEX IF NOT EXISTS idx_orders_customer ON orders(customer_id);
CREATE INDEX IF NOT EXISTS idx_orders_created ON orders(created_at DESC);

CREATE INDEX IF NOT EXISTS idx_suppliers_active ON suppliers(is_active);
CREATE INDEX IF NOT EXISTS idx_suppliers_name ON suppliers(name);

-- 7. Create views for dashboard analytics
CREATE OR REPLACE VIEW dashboard_order_summary AS
SELECT 
    COUNT(*) as total_orders,
    COUNT(CASE WHEN status = 'pending' THEN 1 END) as pending_orders,
    COUNT(CASE WHEN status = 'processing' THEN 1 END) as processing_orders,
    COUNT(CASE WHEN status = 'completed' THEN 1 END) as completed_orders,
    COUNT(CASE WHEN status = 'cancelled' THEN 1 END) as cancelled_orders,
    SUM(total_amount) as total_revenue,
    AVG(total_amount) as average_order_value,
    COUNT(DISTINCT customer_id) as unique_customers
FROM orders
WHERE created_at >= CURRENT_DATE - INTERVAL '30 days';

CREATE OR REPLACE VIEW dashboard_product_summary AS
SELECT 
    p.id,
    p.sku,
    p.name,
    p.category,
    p.unit_price,
    COALESCE(i.quantity_on_hand, 0) as stock_quantity,
    COALESCE(i.quantity_available, 0) as available_quantity,
    CASE 
        WHEN COALESCE(i.quantity_available, 0) = 0 THEN 'out_of_stock'
        WHEN COALESCE(i.quantity_available, 0) < COALESCE(i.reorder_point, 10) THEN 'low_stock'
        ELSE 'in_stock'
    END as stock_status
FROM products p
LEFT JOIN inventory i ON p.sku = i.sku
WHERE p.is_active = true;

CREATE OR REPLACE VIEW dashboard_recent_orders AS
SELECT 
    o.id,
    o.order_number,
    o.customer_id,
    COALESCE(o.customer_name, c.first_name || ' ' || c.last_name) as customer_name,
    o.total_amount,
    o.status,
    o.created_at,
    o.updated_at
FROM orders o
LEFT JOIN customers c ON o.customer_id = c.id
ORDER BY o.created_at DESC
LIMIT 100;

-- 8. Add trigger to update updated_at timestamps
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_products_updated_at BEFORE UPDATE ON products
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_customers_updated_at BEFORE UPDATE ON customers
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_suppliers_updated_at BEFORE UPDATE ON suppliers
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_orders_updated_at BEFORE UPDATE ON orders
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- 9. Insert sample data if tables are empty (for testing)
INSERT INTO products (sku, name, description, category, unit_price, thc_content, cbd_content, strain_type)
SELECT 
    'SKU-' || generate_series,
    'Product ' || generate_series,
    'High-quality cannabis product',
    CASE (generate_series % 3)
        WHEN 0 THEN 'Flower'
        WHEN 1 THEN 'Edibles'
        ELSE 'Vapes'
    END,
    (20 + random() * 80)::numeric(10,2),
    (15 + random() * 10)::numeric(5,2),
    (random() * 5)::numeric(5,2),
    CASE (generate_series % 3)
        WHEN 0 THEN 'Indica'
        WHEN 1 THEN 'Sativa'
        ELSE 'Hybrid'
    END
FROM generate_series(1, 10)
WHERE NOT EXISTS (SELECT 1 FROM products LIMIT 1);

INSERT INTO suppliers (name, contact_person, email, phone, city, state, payment_terms)
SELECT
    'Supplier ' || generate_series,
    'Contact ' || generate_series,
    'supplier' || generate_series || '@example.com',
    '555-' || LPAD(generate_series::text, 4, '0'),
    'Los Angeles',
    'CA',
    'Net 30'
FROM generate_series(1, 5)
WHERE NOT EXISTS (SELECT 1 FROM suppliers WHERE city IS NOT NULL LIMIT 1);

-- Grant permissions
GRANT ALL ON ALL TABLES IN SCHEMA public TO weedgo;
GRANT ALL ON ALL SEQUENCES IN SCHEMA public TO weedgo;
GRANT ALL ON ALL FUNCTIONS IN SCHEMA public TO weedgo;