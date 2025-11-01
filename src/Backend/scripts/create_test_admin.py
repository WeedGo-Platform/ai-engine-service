#!/usr/bin/env python3
"""
Create a test admin user with proper bcrypt password hashing
"""

import asyncio
import asyncpg
import bcrypt
import os
import uuid
from datetime import datetime

async def create_test_admin():
    """Create a test admin user"""
    
    # Database connection
    conn = await asyncpg.connect(
        host=os.getenv('DB_HOST', 'localhost'),
        port=int(os.getenv('DB_PORT', 5434)),
        database=os.getenv('DB_NAME', 'ai_engine'),
        user=os.getenv('DB_USER', 'weedgo'),
        password=os.getenv('DB_PASSWORD', 'weedgo123')
    )
    
    try:
        # Test user details
        email = 'admin@test.com'
        password = 'Test123!'
        
        # Hash password using bcrypt
        salt = bcrypt.gensalt()
        password_hash = bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')
        
        # Check if user already exists
        existing = await conn.fetchval(
            "SELECT id FROM users WHERE email = $1",
            email
        )
        
        if existing:
            # Update existing user's password
            await conn.execute(
                """
                UPDATE users 
                SET password_hash = $1, 
                    role = 'super_admin',
                    active = true,
                    updated_at = $2
                WHERE email = $3
                """,
                password_hash,
                datetime.utcnow(),
                email
            )
            print(f"Updated existing user: {email}")
        else:
            # Create new user
            user_id = str(uuid.uuid4())
            await conn.execute(
                """
                INSERT INTO users (
                    id, email, password_hash, first_name, last_name,
                    role, active, email_verified, created_at, updated_at
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
                """,
                user_id, email, password_hash, 'Test', 'Admin',
                'super_admin', True, True, datetime.utcnow(), datetime.utcnow()
            )
            print(f"Created new admin user: {email}")
        
        print(f"Password: {password}")
        print(f"Password hash starts with: {password_hash[:20]}...")
        print("\nYou can now login with:")
        print(f"Email: {email}")
        print(f"Password: {password}")
        
    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(create_test_admin())