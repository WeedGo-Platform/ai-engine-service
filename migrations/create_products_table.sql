-- Create products table for dispensary items
CREATE TABLE IF NOT EXISTS products (
    product_id SERIAL PRIMARY KEY,
    product_name VARCHAR(255) NOT NULL,
    brand VARCHAR(100),
    category VARCHAR(50),
    sub_category VARCHAR(50),
    sub_sub_category VARCHAR(50),
    strain_type VARCHAR(20) CHECK (strain_type IN ('Sativa', 'Indica', 'Hybrid', 'CBD', NULL)),
    plant_type VARCHAR(50),
    unit_price DECIMAL(10, 2),
    thc_level DECIMAL(5, 2),
    cbd_level DECIMAL(5, 2),
    product_description TEXT,
    inventory_quantity INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for better search performance
CREATE INDEX IF NOT EXISTS idx_products_name ON products(product_name);
CREATE INDEX IF NOT EXISTS idx_products_brand ON products(brand);
CREATE INDEX IF NOT EXISTS idx_products_category ON products(category);
CREATE INDEX IF NOT EXISTS idx_products_strain_type ON products(strain_type);
CREATE INDEX IF NOT EXISTS idx_products_price ON products(unit_price);

-- Insert sample data
INSERT INTO products (product_name, brand, category, sub_category, sub_sub_category, strain_type, plant_type, unit_price, thc_level, cbd_level, product_description, inventory_quantity) VALUES
-- Flower products
('Blue Dream', 'COOKIES', 'Flower', 'Pre-Packaged', 'Eighths', 'Sativa', 'Cannabis', 45.00, 22.5, 0.5, 'Sweet berry aroma with cerebral invigoration and full-body relaxation', 50),
('Northern Lights', 'DIVVY', 'Flower', 'Pre-Packaged', 'Quarters', 'Indica', 'Cannabis', 80.00, 19.0, 0.2, 'Famous for its resinous buds and fast flowering', 30),
('Gelato #33', 'CONNECTED', 'Flower', 'Premium', 'Eighths', 'Hybrid', 'Cannabis', 60.00, 25.0, 0.1, 'Sweet citrus and fruity flavors with a creamy finish', 25),
('OG Kush', 'WEST COAST CURE', 'Flower', 'Pre-Packaged', 'Half Ounce', 'Hybrid', 'Cannabis', 150.00, 23.0, 0.0, 'Classic strain with a complex terpene profile', 20),
('Sour Diesel', 'RAW GARDEN', 'Flower', 'Live Resin', 'Grams', 'Sativa', 'Cannabis', 35.00, 26.0, 0.1, 'Energizing and dreamy cerebral effects', 40),

-- Pre-rolls
('DIVVY Black Cherry Punch Pre-Roll', 'DIVVY', 'Pre-rolls', 'Singles', '1g', 'Indica', 'Cannabis', 15.00, 18.0, 0.3, 'Relaxing indica pre-roll with berry flavors', 100),
('Baby Jeeter Strawberry', 'JEETER', 'Pre-rolls', 'Infused', '5-pack', 'Sativa', 'Cannabis', 45.00, 35.0, 0.0, 'Premium infused pre-rolls with strawberry terpenes', 60),
('Packwoods x Runtz Collab', 'PACKWOODS', 'Pre-rolls', 'Blunts', '2g', 'Hybrid', 'Cannabis', 50.00, 28.0, 0.0, 'Luxury cannabis blunt with premium flower', 35),

-- Edibles
('KIVA Dark Chocolate Bar', 'KIVA', 'Edibles', 'Chocolates', '100mg', 'Hybrid', 'Cannabis', 25.00, 100.0, 0.0, 'Artisan dark chocolate with precise dosing', 80),
('WYLD Raspberry Gummies', 'WYLD', 'Edibles', 'Gummies', '100mg', 'Sativa', 'Cannabis', 20.00, 100.0, 0.0, 'Real fruit gummies with sativa blend', 120),
('CAMINO Midnight Blueberry', 'KIVA', 'Edibles', 'Gummies', '100mg', 'Indica', 'Cannabis', 18.00, 100.0, 5.0, 'Sleep-promoting gummies with CBN', 90),
('PLUS Uplift Gummies', 'PLUS', 'Edibles', 'Gummies', '100mg', 'Sativa', 'Cannabis', 22.00, 100.0, 0.0, 'Energizing sativa gummies', 70),

-- Concentrates
('RAW GARDEN Live Resin', 'RAW GARDEN', 'Concentrates', 'Live Resin', '1g', 'Hybrid', 'Cannabis', 40.00, 75.0, 0.0, 'Fresh frozen, whole plant extract', 40),
('STIIIZY Live Rosin', 'STIIIZY', 'Concentrates', 'Rosin', '1g', 'Indica', 'Cannabis', 60.00, 80.0, 0.0, 'Solventless hash rosin', 30),
('710 LABS Persy Sauce', '710 LABS', 'Concentrates', 'Sauce', '1g', 'Sativa', 'Cannabis', 70.00, 85.0, 0.0, 'High terpene full spectrum extract', 25),

-- Vapes
('STIIIZY Blue Dream Pod', 'STIIIZY', 'Vapes', 'Pods', '1g', 'Sativa', 'Cannabis', 50.00, 85.0, 0.0, 'Premium distillate pod system', 150),
('PAX Era Pro Pods', 'PAX', 'Vapes', 'Pods', '0.5g', 'Hybrid', 'Cannabis', 40.00, 82.0, 0.0, 'Temperature controlled vaping experience', 100),
('SELECT Elite Cartridge', 'SELECT', 'Vapes', 'Cartridges', '1g', 'Indica', 'Cannabis', 45.00, 88.0, 0.0, 'High potency distillate cartridge', 120),
('KURVANA ASCND', 'KURVANA', 'Vapes', 'Cartridges', '0.5g', 'Hybrid', 'Cannabis', 35.00, 90.0, 0.0, 'Full spectrum cannabis oil', 80),

-- CBD Products  
('Charlotte''s Web CBD Oil', 'CHARLOTTE''S WEB', 'Tinctures', 'CBD', '30ml', 'CBD', 'Hemp', 60.00, 0.0, 25.0, 'Full spectrum CBD oil tincture', 50),
('PAPA & BARKLEY Balm', 'PAPA & BARKLEY', 'Topicals', 'Balms', '15ml', 'CBD', 'Cannabis', 45.00, 3.0, 50.0, 'Targeted relief balm with CBD and THC', 40),
('Mary''s Medicinals Patch', 'MARY''S', 'Topicals', 'Patches', '20mg', 'CBD', 'Cannabis', 16.00, 0.0, 20.0, 'Transdermal CBD patch for all-day relief', 60),

-- Budget Options
('House Flower Eighths', 'HOUSE BRAND', 'Flower', 'Budget', 'Eighths', 'Hybrid', 'Cannabis', 25.00, 18.0, 0.2, 'Quality flower at an affordable price', 200),
('Value Pack Pre-Rolls', 'HOUSE BRAND', 'Pre-rolls', 'Multi-pack', '7-pack', 'Hybrid', 'Cannabis', 35.00, 16.0, 0.1, 'Weekly supply of quality pre-rolls', 150),

-- Premium/Exotic
('Jungle Boys Zack''s Pie', 'JUNGLE BOYS', 'Flower', 'Exotic', 'Eighths', 'Indica', 'Cannabis', 75.00, 28.0, 0.1, 'Award-winning exotic strain', 15),
('Cookies Gary Payton', 'COOKIES', 'Flower', 'Premium', 'Eighths', 'Hybrid', 'Cannabis', 70.00, 27.0, 0.0, 'Collaboration with NBA star Gary Payton', 20);

-- Add more variety
INSERT INTO products (product_name, brand, category, sub_category, strain_type, unit_price, thc_level, cbd_level, product_description, inventory_quantity) VALUES
('Zkittlez', 'CONNECTED', 'Flower', 'Indoor', 'Indica', 55.00, 24.0, 0.1, 'Award-winning fruity strain', 30),
('Wedding Cake', 'JUNGLE BOYS', 'Flower', 'Premium', 'Hybrid', 65.00, 26.0, 0.0, 'Sweet and tangy with relaxing effects', 25),
('Purple Punch', 'DIVVY', 'Flower', 'Pre-Packaged', 'Indica', 40.00, 20.0, 0.1, 'Grape and berry flavors with sedating effects', 45);