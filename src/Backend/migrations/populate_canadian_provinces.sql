-- =====================================================
-- Populate Canadian Provinces and Territories
-- =====================================================

-- Clear existing data (if any)
TRUNCATE TABLE province_territories CASCADE;

-- Insert all Canadian provinces and territories with complete accurate information
INSERT INTO province_territories (
    code,
    name,
    country,
    tax_rate,
    cannabis_tax_rate,
    minimum_age,
    regulatory_body,
    regulatory_website,
    is_active,
    created_at,
    updated_at
) VALUES
-- Provinces
('AB', 'Alberta', 'Canada', 0.05, 0.168, 18,
 'Alberta Gaming, Liquor and Cannabis',
 'https://aglc.ca/',
 true, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),

('BC', 'British Columbia', 'Canada', 0.12, 0.20, 19,
 'Liquor and Cannabis Regulation Branch',
 'https://www2.gov.bc.ca/gov/content/employment-business/business/liquor-regulation-licensing/cannabis-regulation',
 true, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),

('MB', 'Manitoba', 'Canada', 0.12, 0.09, 19,
 'Liquor, Gaming and Cannabis Authority of Manitoba',
 'https://lgcamb.ca/',
 true, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),

('NB', 'New Brunswick', 'Canada', 0.15, 0.20, 19,
 'Cannabis NB',
 'https://www.cannabis-nb.com/',
 true, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),

('NL', 'Newfoundland and Labrador', 'Canada', 0.15, 0.20, 19,
 'Newfoundland and Labrador Liquor Corporation',
 'https://nlliquor.com/',
 true, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),

('NS', 'Nova Scotia', 'Canada', 0.15, 0.20, 19,
 'Nova Scotia Liquor Corporation',
 'https://cannabis.nslc.com/',
 true, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),

('ON', 'Ontario', 'Canada', 0.13, 0.134, 19,
 'Ontario Cannabis Store',
 'https://ocs.ca/',
 true, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),

('PE', 'Prince Edward Island', 'Canada', 0.15, 0.20, 19,
 'Cannabis PEI',
 'https://cannabispei.ca/',
 true, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),

('QC', 'Quebec', 'Canada', 0.14975, 0.14975, 21,
 'Société québécoise du cannabis (SQDC)',
 'https://www.sqdc.ca/',
 true, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),

('SK', 'Saskatchewan', 'Canada', 0.11, 0.10, 19,
 'Saskatchewan Liquor and Gaming Authority',
 'https://www.slga.com/',
 true, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),

-- Territories
('NT', 'Northwest Territories', 'Canada', 0.05, 0.20, 19,
 'Northwest Territories Liquor and Cannabis Commission',
 'https://www.ntlcc.ca/',
 true, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),

('NU', 'Nunavut', 'Canada', 0.05, 0.20, 19,
 'Nunavut Liquor and Cannabis Commission',
 'https://nulc.ca/',
 true, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),

('YT', 'Yukon', 'Canada', 0.05, 0.20, 19,
 'Yukon Liquor Corporation',
 'https://yukonliquor.com/',
 true, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP);

-- Create an index for faster lookups
CREATE INDEX IF NOT EXISTS idx_province_territories_code ON province_territories(code);
CREATE INDEX IF NOT EXISTS idx_province_territories_country ON province_territories(country);

-- Add comments for documentation
COMMENT ON TABLE province_territories IS 'Canadian provinces and territories with cannabis regulatory information';
COMMENT ON COLUMN province_territories.tax_rate IS 'General sales tax rate (HST/GST/PST combined where applicable)';
COMMENT ON COLUMN province_territories.cannabis_tax_rate IS 'Additional cannabis-specific excise tax rate';
COMMENT ON COLUMN province_territories.minimum_age IS 'Legal age for cannabis purchase in the province/territory';
COMMENT ON COLUMN province_territories.regulatory_body IS 'Government body responsible for cannabis regulation';
COMMENT ON COLUMN province_territories.regulatory_website IS 'Official website for cannabis regulations and information';