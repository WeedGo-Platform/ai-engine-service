-- Compliance and Age Verification Tables
-- For tracking regulatory compliance in cannabis sales

-- Customer verifications table
CREATE TABLE IF NOT EXISTS customer_verifications (
    id SERIAL PRIMARY KEY,
    customer_id VARCHAR(255) UNIQUE NOT NULL,
    birth_date DATE NOT NULL,
    method VARCHAR(50) NOT NULL, -- government_id, credit_card, biometric, manual, third_party
    verified_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP NOT NULL,
    status VARCHAR(20) NOT NULL, -- verified, pending, failed, expired, blocked
    government_id_hash VARCHAR(255), -- SHA-256 hash of government ID
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Purchase records for compliance tracking
CREATE TABLE IF NOT EXISTS purchase_records (
    id SERIAL PRIMARY KEY,
    customer_id VARCHAR(255) NOT NULL,
    transaction_id VARCHAR(255) NOT NULL,
    product_id INTEGER NOT NULL,
    category VARCHAR(50) NOT NULL,
    quantity DECIMAL(10,2) NOT NULL,
    thc_mg DECIMAL(10,2),
    cbd_mg DECIMAL(10,2),
    price DECIMAL(10,2) NOT NULL,
    dried_flower_equivalent DECIMAL(10,2) NOT NULL, -- For daily limit tracking
    timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (product_id) REFERENCES products(id)
);

-- Compliance violations tracking
CREATE TABLE IF NOT EXISTS compliance_violations (
    id SERIAL PRIMARY KEY,
    customer_id VARCHAR(255) NOT NULL,
    violation_type VARCHAR(50) NOT NULL, -- age_verification, purchase_limit, time_restriction
    violation_details TEXT,
    attempted_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    blocked_until TIMESTAMP
);

-- Compliance audit log
CREATE TABLE IF NOT EXISTS compliance_audit_log (
    id SERIAL PRIMARY KEY,
    customer_id VARCHAR(255),
    action VARCHAR(50) NOT NULL, -- verification, purchase, rejection
    details JSONB,
    ip_address VARCHAR(45),
    user_agent TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for performance
CREATE INDEX idx_verifications_customer ON customer_verifications(customer_id);
CREATE INDEX idx_verifications_status ON customer_verifications(status);
CREATE INDEX idx_verifications_expires ON customer_verifications(expires_at);

CREATE INDEX idx_purchases_customer ON purchase_records(customer_id);
CREATE INDEX idx_purchases_transaction ON purchase_records(transaction_id);
CREATE INDEX idx_purchases_timestamp ON purchase_records(timestamp);

CREATE INDEX idx_violations_customer ON compliance_violations(customer_id);
CREATE INDEX idx_violations_type ON compliance_violations(violation_type);

CREATE INDEX idx_audit_customer ON compliance_audit_log(customer_id);
CREATE INDEX idx_audit_created ON compliance_audit_log(created_at);

-- Function to automatically update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Trigger for customer_verifications
CREATE TRIGGER update_customer_verifications_updated_at 
    BEFORE UPDATE ON customer_verifications 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();