#!/usr/bin/env python3
"""
Create educational_only_sessions table for tracking underage users
"""

import psycopg2
import os
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database connection parameters
DB_PARAMS = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'port': os.getenv('DB_PORT', '5434'),
    'database': os.getenv('DB_NAME', 'ai_engine'),
    'user': os.getenv('DB_USER', 'weedgo'),
    'password': os.getenv('DB_PASSWORD', 'weedgo123')
}

def create_table():
    """Create educational_only_sessions table"""
    
    conn = None
    try:
        # Connect to database
        conn = psycopg2.connect(**DB_PARAMS)
        cur = conn.cursor()
        
        # Create table for educational-only sessions
        cur.execute("""
            CREATE TABLE IF NOT EXISTS educational_only_sessions (
                session_id VARCHAR(255) PRIMARY KEY,
                reason TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create index for faster lookups
        cur.execute("""
            CREATE INDEX IF NOT EXISTS idx_educational_sessions_created 
            ON educational_only_sessions(created_at DESC)
        """)
        
        conn.commit()
        logger.info("✓ Created educational_only_sessions table")
        
        # Also ensure blocked_sessions exists for completeness
        cur.execute("""
            CREATE TABLE IF NOT EXISTS blocked_sessions (
                session_id VARCHAR(255) PRIMARY KEY,
                reason TEXT,
                blocked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        conn.commit()
        logger.info("✓ Created blocked_sessions table")
        
    except Exception as e:
        logger.error(f"Error creating tables: {e}")
        if conn:
            conn.rollback()
        raise
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    create_table()