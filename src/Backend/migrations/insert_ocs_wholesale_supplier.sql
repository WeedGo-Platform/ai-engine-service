-- =====================================================
-- Insert OCS Wholesale Supplier
-- =====================================================

-- First check if OCS Wholesale exists, if not insert it
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM suppliers WHERE name = 'OCS Wholesale') THEN
        INSERT INTO suppliers (
            name,
            contact_person,
            email,
            phone,
            address,
            payment_terms,
            is_active,
            is_ocs,
            tenant_id  -- NULL means it's available to all tenants
        ) VALUES (
            'OCS Wholesale',
            'OCS Support',
            'b2bsupport@ocs.ca',
            '1-888-910-0627',
            '655 Warden Avenue, Scarborough, ON M1L 3Z3',
            'Net 30',
            true,
            true,
            NULL
        );
        RAISE NOTICE 'OCS Wholesale supplier created successfully';
    ELSE
        -- Update existing OCS Wholesale record
        UPDATE suppliers
        SET
            contact_person = 'OCS Support',
            email = 'b2bsupport@ocs.ca',
            phone = '1-888-910-0627',
            address = '655 Warden Avenue, Scarborough, ON M1L 3Z3',
            payment_terms = 'Net 30',
            is_active = true,
            is_ocs = true,
            updated_at = CURRENT_TIMESTAMP
        WHERE name = 'OCS Wholesale';
        RAISE NOTICE 'OCS Wholesale supplier updated successfully';
    END IF;
END $$;

-- Insert other common cannabis suppliers if they don't exist
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM suppliers WHERE name = 'Direct Cannabis Supplier') THEN
        INSERT INTO suppliers (name, contact_person, email, phone, payment_terms, is_active, tenant_id)
        VALUES ('Direct Cannabis Supplier', 'Sales Team', 'sales@directcannabis.ca', '416-555-0100', 'Net 30', true, NULL);
    END IF;

    IF NOT EXISTS (SELECT 1 FROM suppliers WHERE name = 'Provincial Cannabis Distribution') THEN
        INSERT INTO suppliers (name, contact_person, email, phone, payment_terms, is_active, tenant_id)
        VALUES ('Provincial Cannabis Distribution', 'B2B Support', 'b2b@provincialcannabis.ca', '1-800-555-0200', 'Net 45', true, NULL);
    END IF;

    IF NOT EXISTS (SELECT 1 FROM suppliers WHERE name = 'Licensed Producer Direct') THEN
        INSERT INTO suppliers (name, contact_person, email, phone, payment_terms, is_active, tenant_id)
        VALUES ('Licensed Producer Direct', 'LP Sales', 'sales@lpdirect.ca', '905-555-0300', 'Net 60', true, NULL);
    END IF;
END $$;

-- Verify the insertion
SELECT id, name, is_ocs, is_active, email, phone
FROM suppliers
WHERE is_ocs = true OR name LIKE '%OCS%' OR name LIKE '%Cannabis%' OR name LIKE '%Producer%'
ORDER BY is_ocs DESC, name;