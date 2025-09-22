-- =====================================================
-- Rename suppliers table to provincial_suppliers and add province linkage
-- =====================================================

-- Step 1: Rename the table
ALTER TABLE suppliers RENAME TO provincial_suppliers;

-- Step 2: Add province_code column to link with provinces_territories
ALTER TABLE provincial_suppliers
ADD COLUMN province_code VARCHAR(2);

-- Step 3: Add foreign key constraint to provinces_territories
ALTER TABLE provincial_suppliers
ADD CONSTRAINT fk_provincial_supplier_province
FOREIGN KEY (province_code)
REFERENCES provinces_territories(code)
ON DELETE SET NULL
ON UPDATE CASCADE;

-- Step 4: Update existing OCS Wholesale supplier to be linked to Ontario
UPDATE provincial_suppliers
SET province_code = 'ON'
WHERE name = 'OCS Wholesale';

-- Step 5: Insert provincial suppliers for each province/territory
-- This ensures each province has its designated supplier
INSERT INTO provincial_suppliers (name, contact_person, email, phone, address, payment_terms, is_active, province_code, tenant_id)
VALUES
    -- British Columbia
    ('BC Cannabis Stores', 'BC Support', 'b2bsupport@bccannabis.ca', '1-888-555-0101', '2410 Cambie Street, Vancouver, BC V5Z 3Y1', 'Net 30', true, 'BC', NULL),

    -- Alberta
    ('Alberta Cannabis', 'AB Support', 'support@albertacannabis.org', '1-877-555-0102', '1901 1 Street SW, Calgary, AB T2S 1W4', 'Net 30', true, 'AB', NULL),

    -- Saskatchewan
    ('Saskatchewan Cannabis Authority', 'SK Support', 'wholesale@saskcannabis.ca', '1-800-555-0103', '2233 13th Avenue, Regina, SK S4P 3M7', 'Net 30', true, 'SK', NULL),

    -- Manitoba
    ('Manitoba Cannabis', 'MB Support', 'b2b@manitobacannabis.ca', '1-855-555-0104', '1485 Plessis Road, Winnipeg, MB R3W 1G9', 'Net 30', true, 'MB', NULL),

    -- Quebec
    ('SQDC Wholesale', 'QC Support', 'b2b@sqdc.ca', '1-866-555-0105', '5355 Rue des Jockeys, Montreal, QC H4P 1T7', 'Net 45', true, 'QC', NULL),

    -- Nova Scotia
    ('NSLC Cannabis', 'NS Support', 'cannabis@mynslc.com', '1-800-555-0106', '93 Chain Lake Drive, Halifax, NS B3S 1A3', 'Net 30', true, 'NS', NULL),

    -- New Brunswick
    ('Cannabis NB', 'NB Support', 'wholesale@cannabisnb.ca', '1-833-555-0107', '20 McGloin Street, Fredericton, NB E3A 5T8', 'Net 30', true, 'NB', NULL),

    -- Newfoundland and Labrador
    ('NLC Cannabis', 'NL Support', 'cannabis@nlliquor.com', '1-877-555-0108', '90 Kenmount Road, St. Johns, NL A1B 3V1', 'Net 30', true, 'NL', NULL),

    -- Prince Edward Island
    ('PEI Cannabis', 'PE Support', 'wholesale@peicannabis.ca', '1-800-555-0109', '16 Fitzroy Street, Charlottetown, PE C1A 1R2', 'Net 30', true, 'PE', NULL),

    -- Northwest Territories
    ('NWT Cannabis', 'NT Support', 'cannabis@ntlcc.ca', '1-855-555-0110', '201 Range Lake Road, Yellowknife, NT X1A 3S9', 'Net 45', true, 'NT', NULL),

    -- Yukon
    ('Yukon Cannabis', 'YT Support', 'cannabis@yukonliquor.com', '1-867-555-0111', '9031 Quartz Road, Whitehorse, YT Y1A 4P9', 'Net 45', true, 'YT', NULL),

    -- Nunavut
    ('Nunavut Cannabis', 'NU Support', 'cannabis@nulc.ca', '1-866-555-0112', 'Building 804, Iqaluit, NU X0A 0H0', 'Net 60', true, 'NU', NULL)
ON CONFLICT DO NOTHING;

-- Step 6: Update is_ocs flag to be more generic (rename to is_provincial_supplier)
ALTER TABLE provincial_suppliers
RENAME COLUMN is_ocs TO is_provincial_supplier;

-- Step 7: Set is_provincial_supplier flag for all provincial suppliers
UPDATE provincial_suppliers
SET is_provincial_supplier = true
WHERE province_code IS NOT NULL;

-- Step 8: Create index on province_code for faster lookups
CREATE INDEX idx_provincial_suppliers_province ON provincial_suppliers(province_code);

-- Step 9: Create a unique constraint to ensure one supplier per province
ALTER TABLE provincial_suppliers
ADD CONSTRAINT unique_province_supplier
UNIQUE (province_code)
WHERE province_code IS NOT NULL AND is_provincial_supplier = true;

-- Step 10: Update the primary key constraint name
ALTER TABLE provincial_suppliers
RENAME CONSTRAINT suppliers_pkey TO provincial_suppliers_pkey;

-- Step 11: Update trigger name
ALTER TRIGGER update_suppliers_updated_at ON provincial_suppliers
RENAME TO update_provincial_suppliers_updated_at;

-- Step 12: Add comment to the table
COMMENT ON TABLE provincial_suppliers IS 'Provincial cannabis suppliers for each Canadian province/territory';
COMMENT ON COLUMN provincial_suppliers.province_code IS 'Two-letter province/territory code linking to provinces_territories table';
COMMENT ON COLUMN provincial_suppliers.is_provincial_supplier IS 'Flag indicating if this is an official provincial cannabis supplier';