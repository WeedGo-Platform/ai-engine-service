#!/usr/bin/env python3
"""Run database migration for AI personalities table"""

import psycopg2
from psycopg2.extras import RealDictCursor
import os

# Database connection parameters
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'port': os.getenv('DB_PORT', 5434),
    'database': os.getenv('DB_NAME', 'ai_engine'),
    'user': os.getenv('DB_USER', 'weedgo'),
    'password': os.getenv('DB_PASSWORD', 'weedgo123')
}

def run_migration():
    """Run the AI personalities table migration"""
    try:
        # Connect to database
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        # Read migration file
        migration_file = '/Users/charrcy/projects/WeedGo/microservices/ai-engine-service/data/migrations/004_create_ai_personalities_table.sql'
        with open(migration_file, 'r') as f:
            migration_sql = f.read()
        
        # Execute migration
        cur.execute(migration_sql)
        conn.commit()
        
        print("✅ Migration completed successfully!")
        print("Created ai_personalities table with default personalities")
        
        # Verify the table was created
        cur.execute("""
            SELECT id, name, active, created_at 
            FROM ai_personalities 
            ORDER BY active DESC, name
        """)
        personalities = cur.fetchall()
        
        print("\n📋 Personalities in database:")
        for p in personalities:
            status = "✓ ACTIVE" if p['active'] else "  inactive"
            print(f"  [{status}] {p['name']} (ID: {p['id']})")
        
        cur.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        return False
    
    return True

if __name__ == "__main__":
    run_migration()