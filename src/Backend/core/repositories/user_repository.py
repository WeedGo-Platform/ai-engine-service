"""
User Repository for database operations
"""

import asyncpg
import bcrypt
from typing import Optional, List, Dict, Any
from uuid import UUID, uuid4
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class UserRepository:
    """Repository for user-related database operations"""
    
    def __init__(self, pool: asyncpg.Pool):
        self.pool = pool
    
    async def create_user(
        self,
        email: str,
        password: str,
        first_name: str,
        last_name: str,
        phone: Optional[str] = None,
        is_active: bool = True
    ) -> Dict[str, Any]:
        """Create a new user"""
        async with self.pool.acquire() as conn:
            try:
                # Hash the password
                password_hash = self._hash_password(password)
                
                # Create user
                user_id = uuid4()
                query = """
                    INSERT INTO users (
                        id, email, password_hash, first_name, last_name, 
                        phone, active, created_at, updated_at
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                    RETURNING id, email, first_name, last_name, phone, active, created_at
                """
                
                now = datetime.utcnow()
                row = await conn.fetchrow(
                    query,
                    user_id,
                    email.lower(),
                    password_hash,
                    first_name,
                    last_name,
                    phone,
                    is_active,
                    now,
                    now
                )
                
                return dict(row)
                
            except asyncpg.UniqueViolationError as e:
                if 'users_email_key' in str(e):
                    raise ValueError(f"User with email {email} already exists")
                raise
            except Exception as e:
                logger.error(f"Error creating user: {e}")
                raise
    
    async def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """Get user by email"""
        async with self.pool.acquire() as conn:
            query = """
                SELECT id, email, first_name, last_name, phone, 
                       active as is_active, created_at, updated_at
                FROM users 
                WHERE email = $1
            """
            row = await conn.fetchrow(query, email.lower())
            return dict(row) if row else None
    
    async def get_user_by_id(self, user_id: UUID) -> Optional[Dict[str, Any]]:
        """Get user by ID"""
        async with self.pool.acquire() as conn:
            query = """
                SELECT id, email, first_name, last_name, phone, 
                       active as is_active, created_at, updated_at
                FROM users 
                WHERE id = $1
            """
            row = await conn.fetchrow(query, user_id)
            return dict(row) if row else None
    
    async def update_user_tenant(
        self,
        user_id: UUID,
        tenant_id: UUID,
        role: str = 'admin'
    ) -> Dict[str, Any]:
        """Update user with tenant information"""
        async with self.pool.acquire() as conn:
            try:
                query = """
                    UPDATE users 
                    SET tenant_id = $2, tenant_role = $3, updated_at = $4
                    WHERE id = $1
                    RETURNING id, tenant_id, tenant_role as role
                """
                
                now = datetime.utcnow()
                row = await conn.fetchrow(
                    query,
                    user_id,
                    tenant_id,
                    role,
                    now
                )
                
                if not row:
                    raise ValueError(f"User {user_id} does not exist")
                    
                return dict(row)
                
            except asyncpg.ForeignKeyViolationError as e:
                if 'tenant_id' in str(e):
                    raise ValueError(f"Tenant {tenant_id} does not exist")
                raise
            except Exception as e:
                logger.error(f"Error updating user tenant: {e}")
                raise
    
    async def verify_password(self, email: str, password: str) -> Optional[Dict[str, Any]]:
        """Verify user password and return user data if valid"""
        async with self.pool.acquire() as conn:
            query = """
                SELECT id, email, password_hash, first_name, last_name, 
                       phone, active as is_active, created_at
                FROM users 
                WHERE email = $1 AND active = true
            """
            row = await conn.fetchrow(query, email.lower())
            
            if row and self._verify_password(password, row['password_hash']):
                user_data = dict(row)
                del user_data['password_hash']  # Don't return password hash
                return user_data
            
            return None
    
    def _hash_password(self, password: str) -> str:
        """Hash password using bcrypt"""
        salt = bcrypt.gensalt()
        return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')
    
    def _verify_password(self, password: str, password_hash: str) -> bool:
        """Verify password against hash"""
        try:
            # Check if it's a valid bcrypt hash
            if not password_hash or not password_hash.startswith('$2'):
                return False
            return bcrypt.checkpw(
                password.encode('utf-8'),
                password_hash.encode('utf-8')
            )
        except Exception as e:
            logger.error(f"Password verification error: {e}")
            return False