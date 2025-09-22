-- =====================================================
-- Update/Insert Canadian Provinces and Territories with accurate information
-- Using UPSERT (INSERT ... ON CONFLICT UPDATE)
-- =====================================================

-- Insert all Canadian provinces and territories with complete accurate information
-- If they already exist, update them with accurate data
INSERT INTO provinces_territories (
    code,
    name,
    type,
    tax_rate,
    cannabis_tax_rate,
    min_age,
    regulatory_body,
    license_prefix,
    delivery_allowed,
    pickup_allowed,
    settings
) VALUES
-- Provinces
('AB', 'Alberta', 'province', 5.00, 16.80, 18,
 'Alberta Gaming, Liquor and Cannabis', 'AB',
 true, true,
 '{"regulatory_website": "https://aglc.ca/", "excise_tax_flat": 1.25}'::jsonb),

('BC', 'British Columbia', 'province', 12.00, 20.00, 19,
 'Liquor and Cannabis Regulation Branch', 'BC',
 true, true,
 '{"regulatory_website": "https://www2.gov.bc.ca/gov/content/employment-business/business/liquor-regulation-licensing/cannabis-regulation", "excise_tax_flat": 1.25}'::jsonb),

('MB', 'Manitoba', 'province', 12.00, 9.00, 19,
 'Liquor, Gaming and Cannabis Authority of Manitoba', 'MB',
 true, true,
 '{"regulatory_website": "https://lgcamb.ca/", "social_responsibility_fee": 0.06}'::jsonb),

('NB', 'New Brunswick', 'province', 15.00, 20.00, 19,
 'Cannabis NB', 'NB',
 true, true,
 '{"regulatory_website": "https://www.cannabis-nb.com/", "excise_tax_flat": 1.25}'::jsonb),

('NL', 'Newfoundland and Labrador', 'province', 15.00, 20.00, 19,
 'Newfoundland and Labrador Liquor Corporation', 'NL',
 true, true,
 '{"regulatory_website": "https://nlliquor.com/", "excise_tax_flat": 1.25}'::jsonb),

('NS', 'Nova Scotia', 'province', 15.00, 20.00, 19,
 'Nova Scotia Liquor Corporation', 'NS',
 true, true,
 '{"regulatory_website": "https://cannabis.nslc.com/", "excise_tax_flat": 1.25}'::jsonb),

('ON', 'Ontario', 'province', 13.00, 13.40, 19,
 'Ontario Cannabis Store', 'ON',
 true, true,
 '{"regulatory_website": "https://ocs.ca/", "excise_tax_flat": 1.25, "ocs_integration": true}'::jsonb),

('PE', 'Prince Edward Island', 'province', 15.00, 20.00, 19,
 'Cannabis PEI', 'PE',
 true, true,
 '{"regulatory_website": "https://cannabispei.ca/", "excise_tax_flat": 1.25}'::jsonb),

('QC', 'Quebec', 'province', 14.975, 14.975, 21,
 'Société québécoise du cannabis (SQDC)', 'QC',
 true, true,
 '{"regulatory_website": "https://www.sqdc.ca/", "excise_tax_flat": 1.25}'::jsonb),

('SK', 'Saskatchewan', 'province', 11.00, 10.00, 19,
 'Saskatchewan Liquor and Gaming Authority', 'SK',
 true, true,
 '{"regulatory_website": "https://www.slga.com/", "excise_tax_flat": 1.25}'::jsonb),

-- Territories
('NT', 'Northwest Territories', 'territory', 5.00, 20.00, 19,
 'Northwest Territories Liquor and Cannabis Commission', 'NT',
 true, true,
 '{"regulatory_website": "https://www.ntlcc.ca/", "excise_tax_flat": 1.25}'::jsonb),

('NU', 'Nunavut', 'territory', 5.00, 20.00, 19,
 'Nunavut Liquor and Cannabis Commission', 'NU',
 true, true,
 '{"regulatory_website": "https://nulc.ca/", "excise_tax_flat": 1.25}'::jsonb),

('YT', 'Yukon', 'territory', 5.00, 20.00, 19,
 'Yukon Liquor Corporation', 'YT',
 true, true,
 '{"regulatory_website": "https://yukonliquor.com/", "excise_tax_flat": 1.25}'::jsonb)

ON CONFLICT (code) DO UPDATE SET
    name = EXCLUDED.name,
    type = EXCLUDED.type,
    tax_rate = EXCLUDED.tax_rate,
    cannabis_tax_rate = EXCLUDED.cannabis_tax_rate,
    min_age = EXCLUDED.min_age,
    regulatory_body = EXCLUDED.regulatory_body,
    license_prefix = EXCLUDED.license_prefix,
    delivery_allowed = EXCLUDED.delivery_allowed,
    pickup_allowed = EXCLUDED.pickup_allowed,
    settings = EXCLUDED.settings,
    updated_at = CURRENT_TIMESTAMP;