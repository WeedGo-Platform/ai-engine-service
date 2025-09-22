-- =====================================================
-- Create Province/Territories Table
-- =====================================================

-- Drop table if exists (careful in production!)
DROP TABLE IF EXISTS province_territories CASCADE;

-- Create province_territories table
CREATE TABLE province_territories (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    code VARCHAR(2) UNIQUE NOT NULL,  -- Two-letter province/territory code (e.g., 'ON', 'BC')
    name VARCHAR(100) NOT NULL,       -- Full province/territory name
    country VARCHAR(50) DEFAULT 'Canada',
    tax_rate DECIMAL(5, 4) NOT NULL DEFAULT 0.13,  -- Provincial tax rate
    cannabis_tax_rate DECIMAL(5, 4) DEFAULT 0.134,  -- Cannabis-specific tax rate
    minimum_age INTEGER NOT NULL DEFAULT 19,  -- Minimum age for cannabis purchase
    regulatory_body VARCHAR(200),     -- Name of the regulatory body
    regulatory_website VARCHAR(500),  -- Official regulatory website
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes
CREATE INDEX idx_province_territories_code ON province_territories(code);
CREATE INDEX idx_province_territories_country ON province_territories(country);
CREATE INDEX idx_province_territories_active ON province_territories(is_active);

-- Create trigger to update updated_at on changes
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_province_territories_updated_at
    BEFORE UPDATE ON province_territories
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();