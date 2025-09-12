#!/usr/bin/env python3
"""
Script to purge purchase orders, inventory, orders and related tables for testing
"""

import psycopg2
from psycopg2 import sql
import logging
import sys

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Database connection parameters
DB_CONFIG = {
    'host': 'localhost',
    'port': 5434,
    'database': 'ai_engine',
    'user': 'weedgo',
    'password': 'your_password_here'
}

def connect_to_db():
    """Establish database connection"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        conn.autocommit = False
        return conn
    except Exception as e:
        logger.error(f"Failed to connect to database: {e}")
        sys.exit(1)

def purge_tables(conn):
    """Purge all test data from specified tables"""
    cursor = conn.cursor()
    
    # Tables to purge in order (considering foreign key constraints)
    tables_to_purge = [
        # Order related tables
        'order_items',
        'order_status_history',
        'orders',
        
        # Inventory related tables
        'inventory_movements',
        'inventory_adjustments',
        'inventory',
        
        # Purchase order related tables
        'purchase_order_items',
        'purchase_order_status_history',
        'purchase_orders',
        
        # Transaction related tables
        'transaction_items',
        'transactions',
        
        # Supporting tables
        'stock_alerts',
        'price_history',
        'product_batches'
    ]
    
    try:
        # Check which tables exist
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_type = 'BASE TABLE'
        """)
        existing_tables = [row[0] for row in cursor.fetchall()]
        
        logger.info(f"Found {len(existing_tables)} tables in database")
        
        # Count records before purging
        logger.info("\n=== Current record counts ===")
        for table in tables_to_purge:
            if table in existing_tables:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = cursor.fetchone()[0]
                if count > 0:
                    logger.info(f"{table}: {count} records")
        
        # Disable foreign key checks temporarily (PostgreSQL way)
        cursor.execute("SET session_replication_role = 'replica';")
        
        # Purge each table
        logger.info("\n=== Starting purge ===")
        total_deleted = 0
        
        for table in tables_to_purge:
            if table in existing_tables:
                try:
                    # Delete all records from the table
                    cursor.execute(f"DELETE FROM {table}")
                    deleted = cursor.rowcount
                    if deleted > 0:
                        logger.info(f"✓ Deleted {deleted} records from {table}")
                        total_deleted += deleted
                    
                    # Reset sequences if they exist
                    cursor.execute(f"""
                        SELECT column_name, column_default 
                        FROM information_schema.columns 
                        WHERE table_name = %s 
                        AND column_default LIKE 'nextval%%'
                    """, (table,))
                    
                    sequences = cursor.fetchall()
                    for seq_col, seq_default in sequences:
                        # Extract sequence name from default value
                        if seq_default:
                            seq_name = seq_default.split("'")[1]
                            cursor.execute(f"ALTER SEQUENCE {seq_name} RESTART WITH 1")
                            logger.info(f"  → Reset sequence for {table}.{seq_col}")
                            
                except Exception as e:
                    logger.warning(f"Issue with table {table}: {e}")
        
        # Re-enable foreign key checks
        cursor.execute("SET session_replication_role = 'origin';")
        
        # Commit the transaction
        conn.commit()
        
        logger.info(f"\n=== Purge Complete ===")
        logger.info(f"Total records deleted: {total_deleted}")
        
        # Verify purge
        logger.info("\n=== Verification ===")
        for table in tables_to_purge:
            if table in existing_tables:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = cursor.fetchone()[0]
                if count == 0:
                    logger.info(f"✓ {table}: EMPTY")
                else:
                    logger.warning(f"✗ {table}: Still has {count} records")
        
        return True
        
    except Exception as e:
        logger.error(f"Error during purge: {e}")
        conn.rollback()
        return False
    finally:
        cursor.close()

def main():
    """Main execution"""
    logger.info("=== Database Purge Script ===")
    logger.info("This will delete ALL data from purchase_orders, inventory, orders and related tables")
    
    # Confirm action
    response = input("\nAre you sure you want to purge all test data? (yes/no): ")
    if response.lower() != 'yes':
        logger.info("Purge cancelled")
        return
    
    # Connect to database
    conn = connect_to_db()
    
    try:
        # Perform purge
        success = purge_tables(conn)
        
        if success:
            logger.info("\n✅ All test data has been successfully purged!")
        else:
            logger.error("\n❌ Purge failed. Some data may not have been deleted.")
            
    finally:
        conn.close()

if __name__ == "__main__":
    main()