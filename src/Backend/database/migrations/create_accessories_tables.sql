-- Accessories and Paraphernalia Database Schema
-- Separate inventory system for non-cannabis products

-- Categories for accessories (grinders, papers, pipes, vaporizers, etc.)
CREATE TABLE IF NOT EXISTS accessory_categories (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    slug VARCHAR(100) UNIQUE NOT NULL,
    parent_id INTEGER REFERENCES accessory_categories(id) ON DELETE SET NULL,
    description TEXT,
    icon VARCHAR(50),
    image_url TEXT,
    sort_order INTEGER DEFAULT 0,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Master catalog of all accessories
CREATE TABLE IF NOT EXISTS accessories_catalog (
    id SERIAL PRIMARY KEY,
    barcode VARCHAR(50) UNIQUE,
    upc VARCHAR(20),
    sku VARCHAR(100) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    brand VARCHAR(100),
    category_id INTEGER REFERENCES accessory_categories(id),
    description TEXT,
    
    -- Images and media
    image_url TEXT,
    thumbnail_url TEXT,
    additional_images JSONB DEFAULT '[]',
    
    -- Specifications and details
    specifications JSONB DEFAULT '{}',
    materials TEXT[],
    dimensions JSONB, -- {length, width, height, weight}
    color VARCHAR(50),
    
    -- Pricing hints
    msrp DECIMAL(10,2),
    default_cost DECIMAL(10,2),
    suggested_retail DECIMAL(10,2),
    
    -- Data source tracking
    data_source VARCHAR(50), -- 'manual', 'scan', 'web', 'ocr'
    source_url TEXT,
    confidence_score DECIMAL(3,2), -- 0.00 to 1.00
    verified BOOLEAN DEFAULT false,
    
    -- Search optimization
    search_vector tsvector,
    tags TEXT[],
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_verified TIMESTAMP
);

-- Create full-text search index
CREATE INDEX idx_accessories_search ON accessories_catalog USING GIN(search_vector);
CREATE INDEX idx_accessories_barcode ON accessories_catalog(barcode) WHERE barcode IS NOT NULL;
CREATE INDEX idx_accessories_category ON accessories_catalog(category_id);
CREATE INDEX idx_accessories_brand ON accessories_catalog(brand);

-- Store-specific accessory inventory
CREATE TABLE IF NOT EXISTS accessories_inventory (
    id SERIAL PRIMARY KEY,
    store_id VARCHAR(50) NOT NULL,
    accessory_id INTEGER NOT NULL REFERENCES accessories_catalog(id),
    
    -- Stock levels
    quantity INTEGER NOT NULL DEFAULT 0,
    reserved_quantity INTEGER DEFAULT 0,
    available_quantity INTEGER DEFAULT 0,
    
    -- Pricing
    cost_price DECIMAL(10,2) NOT NULL,
    retail_price DECIMAL(10,2) NOT NULL,
    sale_price DECIMAL(10,2),
    discount_percentage DECIMAL(5,2),
    
    -- Stock management
    min_stock_level INTEGER DEFAULT 5,
    max_stock_level INTEGER DEFAULT 100,
    reorder_point INTEGER DEFAULT 10,
    reorder_quantity INTEGER DEFAULT 20,
    
    -- Location in store
    location VARCHAR(50), -- 'shelf-A1', 'counter', 'display-case'
    bin_number VARCHAR(20),
    
    -- Status and tracking
    status VARCHAR(20) DEFAULT 'active', -- active, discontinued, out_of_stock
    last_restocked TIMESTAMP,
    last_sold TIMESTAMP,
    stock_check_date TIMESTAMP,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(store_id, accessory_id)
);

-- Track accessory inventory movements
CREATE TABLE IF NOT EXISTS accessories_movements (
    id SERIAL PRIMARY KEY,
    store_id VARCHAR(50) NOT NULL,
    accessory_id INTEGER NOT NULL REFERENCES accessories_catalog(id),
    movement_type VARCHAR(30) NOT NULL, -- 'purchase', 'sale', 'adjustment', 'return', 'transfer'
    quantity INTEGER NOT NULL,
    unit_cost DECIMAL(10,2),
    
    -- Reference to source document
    reference_type VARCHAR(30), -- 'purchase_order', 'sale', 'adjustment'
    reference_id VARCHAR(50),
    
    -- Additional details
    reason TEXT,
    notes TEXT,
    performed_by VARCHAR(100),
    
    -- Running balance
    quantity_before INTEGER,
    quantity_after INTEGER,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Accessory suppliers
CREATE TABLE IF NOT EXISTS accessory_suppliers (
    id SERIAL PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    company_name VARCHAR(200),
    contact_person VARCHAR(100),
    email VARCHAR(255),
    phone VARCHAR(30),
    website TEXT,
    
    -- Address
    address_line1 VARCHAR(255),
    address_line2 VARCHAR(255),
    city VARCHAR(100),
    state_province VARCHAR(100),
    postal_code VARCHAR(20),
    country VARCHAR(100),
    
    -- Business details
    tax_id VARCHAR(50),
    payment_terms VARCHAR(50),
    minimum_order DECIMAL(10,2),
    lead_time_days INTEGER,
    
    -- Catalog integration
    catalog_url TEXT,
    api_endpoint TEXT,
    api_key TEXT,
    
    notes TEXT,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Link accessories to suppliers
CREATE TABLE IF NOT EXISTS accessory_supplier_items (
    id SERIAL PRIMARY KEY,
    supplier_id INTEGER NOT NULL REFERENCES accessory_suppliers(id),
    accessory_id INTEGER NOT NULL REFERENCES accessories_catalog(id),
    supplier_sku VARCHAR(100),
    supplier_name VARCHAR(255),
    cost_price DECIMAL(10,2),
    min_order_quantity INTEGER DEFAULT 1,
    lead_time_days INTEGER,
    is_preferred BOOLEAN DEFAULT false,
    last_ordered TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(supplier_id, accessory_id)
);

-- Barcode lookup cache
CREATE TABLE IF NOT EXISTS barcode_lookup_cache (
    barcode VARCHAR(50) PRIMARY KEY,
    lookup_data JSONB NOT NULL,
    source VARCHAR(50), -- 'web', 'api', 'manual'
    confidence DECIMAL(3,2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP DEFAULT (CURRENT_TIMESTAMP + INTERVAL '30 days')
);

-- OCR scan history
CREATE TABLE IF NOT EXISTS ocr_scan_history (
    id SERIAL PRIMARY KEY,
    store_id VARCHAR(50),
    image_url TEXT,
    extracted_text TEXT,
    extracted_data JSONB,
    barcode VARCHAR(50),
    confidence_score DECIMAL(3,2),
    status VARCHAR(20), -- 'success', 'partial', 'failed'
    processed_by VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create update trigger for search vector
CREATE OR REPLACE FUNCTION update_accessories_search_vector()
RETURNS TRIGGER AS $$
BEGIN
    NEW.search_vector := 
        setweight(to_tsvector('english', COALESCE(NEW.name, '')), 'A') ||
        setweight(to_tsvector('english', COALESCE(NEW.brand, '')), 'B') ||
        setweight(to_tsvector('english', COALESCE(NEW.description, '')), 'C') ||
        setweight(to_tsvector('english', COALESCE(array_to_string(NEW.tags, ' '), '')), 'D');
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_accessories_search_vector_trigger
BEFORE INSERT OR UPDATE ON accessories_catalog
FOR EACH ROW
EXECUTE FUNCTION update_accessories_search_vector();

-- Insert default categories
INSERT INTO accessory_categories (name, slug, icon, sort_order) VALUES
    ('Rolling Papers', 'rolling-papers', '📜', 1),
    ('Grinders', 'grinders', '⚙️', 2),
    ('Pipes & Bongs', 'pipes-bongs', '🚬', 3),
    ('Vaporizers', 'vaporizers', '💨', 4),
    ('Storage', 'storage', '📦', 5),
    ('Lighters & Torches', 'lighters', '🔥', 6),
    ('Cleaning Supplies', 'cleaning', '🧹', 7),
    ('Scales', 'scales', '⚖️', 8),
    ('Trays & Accessories', 'trays', '🍽️', 9),
    ('Apparel', 'apparel', '👕', 10),
    ('Books & Media', 'books-media', '📚', 11),
    ('Other', 'other', '📌', 99)
ON CONFLICT (slug) DO NOTHING;