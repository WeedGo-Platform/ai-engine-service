#!/usr/bin/env python3
import bcrypt
import asyncpg
import asyncio
import os

async def update_password():
    # Connect to database
    conn = await asyncpg.connect(
        host=os.getenv('DB_HOST', 'localhost'),
        port=int(os.getenv('DB_PORT', 5434)),
        user=os.getenv('DB_USER', 'weedgo'),
        password=os.getenv('DB_PASSWORD', 'your_password_here'),
        database=os.getenv('DB_NAME', 'ai_engine')
    )
    
    # Hash the password
    password = "your_password_here"
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