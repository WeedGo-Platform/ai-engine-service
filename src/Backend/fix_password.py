#!/usr/bin/env python3
import bcrypt
import asyncpg
import asyncio

async def update_password():
    # Connect to database
    conn = await asyncpg.connect(
        host='localhost',
        port=5434,
        user='weedgo',
        password='weedgo123',
        database='ai_engine'
    )
    
    # Hash the password
    password = "Password1$"
    hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
    
    # Update the user's password
    await conn.execute(
        "UPDATE users SET password_hash = $1 WHERE email = $2",
        hashed.decode('utf-8'),
        'support@potpalace.ca'
    )
    
    print(f"Password updated for support@potpalace.ca")
    print(f"New hash: {hashed.decode('utf-8')}")
    
    await conn.close()

if __name__ == "__main__":
    asyncio.run(update_password())