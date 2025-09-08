-- Migration: Resolve Customer Table Conflict
-- Purpose: Merge the two conflicting customer table definitions and establish proper user relationship
-- Date: 2025-01-07

-- 1. First, drop the existing customers table if it exists (we'll recreate it properly)
DROP TABLE IF EXISTS customers CASCADE;

-- 2. Create the unified customers table with all necessary fields
CREATE TABLE customers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,  -- Link to users table for authenticated customers
    email VARCHAR(255) NOT NULL,  -- Email is required but not unique (guest checkouts)
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    phone VARCHAR(50),
    date_of_birth DATE,
    
    -- Address fields (structured)
    address TEXT,  -- Can be JSON or text
    city VARCHAR(100),
    state VARCHAR(50),
    postal_code VARCHAR(20),
    country VARCHAR(100) DEFAULT 'USA',
    
    -- Commerce fields
    loyalty_points INTEGER DEFAULT 0,
    customer_type VARCHAR(50) DEFAULT 'regular',  -- regular, vip, wholesale, etc.
    preferred_payment_method VARCHAR(50),
    total_spent DECIMAL(12,2) DEFAULT 0,
    order_count INTEGER DEFAULT 0,
    
    -- Consent and preferences
    marketing_consent BOOLEAN DEFAULT false,
    sms_consent BOOLEAN DEFAULT false,
    
    -- Metadata
    tags JSONB DEFAULT '[]'::JSONB,  -- Flexible tagging system
    notes TEXT,
    
    -- Status
    is_active BOOLEAN DEFAULT true,
    is_verified BOOLEAN DEFAULT false,
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_order_date TIMESTAMP,
    
    -- Constraints
    CONSTRAINT unique_user_id UNIQUE(user_id),  -- One customer record per user
    CONSTRAINT unique_email_for_registered UNIQUE(email, user_id)  -- Unique email per registered user
);

-- 3. Create indexes for better performance
CREATE INDEX idx_customers_email ON customers(email);
CREATE INDEX idx_customers_user_id ON customers(user_id);
CREATE INDEX idx_customers_phone ON customers(phone);
CREATE INDEX idx_customers_active ON customers(is_active);
CREATE INDEX idx_customers_type ON customers(customer_type);
CREATE INDEX idx_customers_created ON customers(created_at DESC);

-- 4. Add or update foreign key constraint on orders table
ALTER TABLE orders DROP CONSTRAINT IF EXISTS orders_customer_id_fkey;
ALTER TABLE orders ADD COLUMN IF NOT EXISTS customer_id UUID;
ALTER TABLE orders ADD CONSTRAINT orders_customer_id_fkey 
    FOREIGN KEY (customer_id) REFERENCES customers(id) ON DELETE SET NULL;

-- 5. Create function to automatically create customer record when user registers
CREATE OR REPLACE FUNCTION create_customer_for_user()
RETURNS TRIGGER AS $$
BEGIN
    -- Only create customer if user has required fields
    IF NEW.email IS NOT NULL THEN
        INSERT INTO customers (
            user_id,
            email,
            first_name,
            last_name,
            phone,
            date_of_birth,
            marketing_consent,
            is_verified
        ) VALUES (
            NEW.id,
            NEW.email,
            NEW.first_name,
            NEW.last_name,
            NEW.phone,
            NEW.date_of_birth,
            NEW.marketing_consent,
            NEW.email_verified OR NEW.phone_verified
        )
        ON CONFLICT (user_id) DO UPDATE SET
            email = EXCLUDED.email,
            first_name = COALESCE(EXCLUDED.first_name, customers.first_name),
            last_name = COALESCE(EXCLUDED.last_name, customers.last_name),
            phone = COALESCE(EXCLUDED.phone, customers.phone),
            date_of_birth = COALESCE(EXCLUDED.date_of_birth, customers.date_of_birth),
            marketing_consent = EXCLUDED.marketing_consent,
            is_verified = EXCLUDED.is_verified,
            updated_at = CURRENT_TIMESTAMP;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- 6. Create trigger to auto-create customer records
DROP TRIGGER IF EXISTS create_customer_on_user_insert ON users;
CREATE TRIGGER create_customer_on_user_insert
AFTER INSERT OR UPDATE ON users
FOR EACH ROW
EXECUTE FUNCTION create_customer_for_user();

-- 7. Update existing timestamp trigger for customers
DROP TRIGGER IF EXISTS update_customers_timestamp ON customers;
DROP TRIGGER IF EXISTS update_customers_updated_at ON customers;

CREATE TRIGGER update_customers_timestamp
BEFORE UPDATE ON customers
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();

-- 8. Migrate existing user data to customers table
INSERT INTO customers (
    user_id,
    email,
    first_name,
    last_name,
    phone,
    date_of_birth,
    marketing_consent,
    is_verified,
    is_active
)
SELECT 
    u.id,
    u.email,
    u.first_name,
    u.last_name,
    u.phone,
    u.date_of_birth,
    u.marketing_consent,
    u.email_verified OR u.phone_verified,
    u.active
FROM users u
WHERE NOT EXISTS (
    SELECT 1 FROM customers c WHERE c.user_id = u.id
)
AND u.email IS NOT NULL;

-- 9. Update orders to link with customers based on user_id
UPDATE orders o
SET customer_id = c.id
FROM customers c
WHERE o.user_id = c.user_id
AND o.customer_id IS NULL;

-- 10. Create view for easy access to customer with user info
CREATE OR REPLACE VIEW customer_details AS
SELECT 
    c.*,
    u.email_verified,
    u.phone_verified,
    u.role as user_role,
    u.active as user_active,
    u.created_at as user_created_at,
    CASE 
        WHEN c.user_id IS NOT NULL THEN 'registered'
        ELSE 'guest'
    END as account_type
FROM customers c
LEFT JOIN users u ON c.user_id = u.id;

-- 11. Add helpful comments
COMMENT ON TABLE customers IS 'Customer records for both registered users and guest checkouts';
COMMENT ON COLUMN customers.user_id IS 'References users table for registered customers, NULL for guests';
COMMENT ON COLUMN customers.email IS 'Customer email (not unique to allow guest checkouts)';
COMMENT ON COLUMN customers.customer_type IS 'Customer classification: regular, vip, wholesale, medical, etc.';
COMMENT ON COLUMN customers.tags IS 'Flexible JSON tags for customer segmentation';

-- 12. Grant permissions
GRANT ALL ON customers TO weedgo;
GRANT ALL ON customer_details TO weedgo;

-- Success message
DO $$
BEGIN
    RAISE NOTICE 'Customer table conflict resolved successfully';
    RAISE NOTICE 'Customers table now properly linked to users table';
    RAISE NOTICE 'Guest customers (without user_id) are supported';
END $$;