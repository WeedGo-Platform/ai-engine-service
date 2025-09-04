#!/usr/bin/env python3
"""
Create compliance tables for age verification and purchase tracking
"""

import os
import psycopg2
from psycopg2.extras import RealDictCursor

def create_compliance_tables():
    """Create all compliance-related tables"""
    
    # Database connection
    conn = psycopg2.connect(
        host=os.getenv('DB_HOST', 'localhost'),
        port=os.getenv('DB_PORT', 5434),
        database=os.getenv('DB_NAME', 'ai_engine'),
        user=os.getenv('DB_USER', 'weedgo'),
        password=os.getenv('DB_PASSWORD', 'your_password_here')
    )
    
    cur = conn.cursor()
    
    try:
        # Customer verifications table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS customer_verifications (
                id SERIAL PRIMARY KEY,
                customer_id VARCHAR(255) UNIQUE NOT NULL,
                birth_date DATE NOT NULL,
                method VARCHAR(50) NOT NULL,
                verified_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                expires_at TIMESTAMP NOT NULL,
                status VARCHAR(20) NOT NULL,
                government_id_hash VARCHAR(255),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        print("✓ Created customer_verifications table")
        
        # Purchase records table
        cur.execute("""
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
                dried_flower_equivalent DECIMAL(10,2) NOT NULL,
                timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (product_id) REFERENCES products(id)
            )
        """)
        print("✓ Created purchase_records table")
        
        # Compliance violations table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS compliance_violations (
                id SERIAL PRIMARY KEY,
                customer_id VARCHAR(255) NOT NULL,
                violation_type VARCHAR(50) NOT NULL,
                violation_details TEXT,
                attempted_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                blocked_until TIMESTAMP
            )
        """)
        print("✓ Created compliance_violations table")
        
        # Compliance audit log
        cur.execute("""
            CREATE TABLE IF NOT EXISTS compliance_audit_log (
                id SERIAL PRIMARY KEY,
                customer_id VARCHAR(255),
                action VARCHAR(50) NOT NULL,
                details JSONB,
                ip_address VARCHAR(45),
                user_agent TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        print("✓ Created compliance_audit_log table")
        
        # Create indexes
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_verifications_customer ON customer_verifications(customer_id)",
            "CREATE INDEX IF NOT EXISTS idx_verifications_status ON customer_verifications(status)",
            "CREATE INDEX IF NOT EXISTS idx_verifications_expires ON customer_verifications(expires_at)",
            "CREATE INDEX IF NOT EXISTS idx_purchases_customer ON purchase_records(customer_id)",
            "CREATE INDEX IF NOT EXISTS idx_purchases_transaction ON purchase_records(transaction_id)",
            "CREATE INDEX IF NOT EXISTS idx_purchases_timestamp ON purchase_records(timestamp)",
            "CREATE INDEX IF NOT EXISTS idx_violations_customer ON compliance_violations(customer_id)",
            "CREATE INDEX IF NOT EXISTS idx_violations_type ON compliance_violations(violation_type)",
            "CREATE INDEX IF NOT EXISTS idx_audit_customer ON compliance_audit_log(customer_id)",
            "CREATE INDEX IF NOT EXISTS idx_audit_created ON compliance_audit_log(created_at)"
        ]
        
        for index_sql in indexes:
            cur.execute(index_sql)
        print("✓ Created all indexes")
        
        # Create update trigger function
        cur.execute("""
            CREATE OR REPLACE FUNCTION update_updated_at_column()
            RETURNS TRIGGER AS $$
            BEGIN
                NEW.updated_at = CURRENT_TIMESTAMP;
                RETURN NEW;
            END;
            $$ language 'plpgsql'
        """)
        
        # Create trigger
        cur.execute("""
            DROP TRIGGER IF EXISTS update_customer_verifications_updated_at ON customer_verifications
        """)
        cur.execute("""
            CREATE TRIGGER update_customer_verifications_updated_at 
                BEFORE UPDATE ON customer_verifications 
                FOR EACH ROW 
                EXECUTE FUNCTION update_updated_at_column()
        """)
        print("✓ Created update triggers")
        
        # Commit changes
        conn.commit()
        
        # Verify tables
        cur.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name IN ('customer_verifications', 'purchase_records', 
                              'compliance_violations', 'compliance_audit_log')
        """)
        
        tables = cur.fetchall()
        print(f"\n✓ Successfully created {len(tables)} compliance tables:")
        for table in tables:
            print(f"  - {table['table_name']}")
        
    except Exception as e:
        print(f"✗ Error creating tables: {e}")
        conn.rollback()
        raise
    finally:
        cur.close()
        conn.close()

if __name__ == "__main__":
    create_compliance_tables()