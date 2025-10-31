#!/usr/bin/env python3
"""
Create super admin user: admin@weedgo.ca
"""
import asyncio
import asyncpg
import bcrypt
import os
import sys
from uuid import uuid4

async def create_super_admin():
    # Database connection
    pool = await asyncpg.create_pool(
        host='localhost',
        port=5434,
        database='ai_engine',
        user='weedgo',
        password='your_password_here',
        min_size=1,
        max_size=2
    )
    
    try:
        async with pool.acquire() as conn:
            # Check if user already exists
            existing = await conn.fetchrow(
                "SELECT id, email, role FROM users WHERE email = $1",
                'admin@weedgo.ca'
            )
            
            if existing:
                print(f"❌ User already exists:")
                print(f"   Email: {existing['email']}")
                print(f"   Role: {existing['role']}")
                print(f"   ID: {existing['id']}")
                
                # Update password and role
                password_hash = bcrypt.hashpw(
                    'your_password_here'.encode('utf-8'),
                    bcrypt.gensalt()
                ).decode('utf-8')
                
                await conn.execute("""
                    UPDATE users 
                    SET password_hash = $1, 
                        role = 'super_admin',
                        updated_at = NOW()
                    WHERE email = $2
                """, password_hash, 'admin@weedgo.ca')
                
                print(f"✅ Updated password and role to 'super_admin'")
                return
            
            # Create new super admin user
            user_id = uuid4()
            password_hash = bcrypt.hashpw(
                'your_password_here'.encode('utf-8'),
                bcrypt.gensalt()
            ).decode('utf-8')
            
            await conn.execute("""
                INSERT INTO users (
                    id, email, password_hash, first_name, last_name,
                    role, email_verified, created_at, updated_at
                ) VALUES (
                    $1, $2, $3, $4, $5, $6, $7, NOW(), NOW()
                )
            """,
                user_id,
                'admin@weedgo.ca',
                password_hash,
                'Super',
                'Admin',
                'super_admin',
                True  # Email already verified
            )
            
            print(f"✅ Super admin user created successfully!")
            print(f"   Email: admin@weedgo.ca")
            print(f"   Password: your_password_here")
            print(f"   Role: super_admin")
            print(f"   ID: {user_id}")
            
    finally:
        await pool.close()

if __name__ == '__main__':
    asyncio.run(create_super_admin())
