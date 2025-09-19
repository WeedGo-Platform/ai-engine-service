"""
Authentication Token Service
Manages all authentication tokens using the unified auth_tokens table
"""

import asyncpg
import logging
import hashlib
import secrets
from typing import Optional, Dict, Any, Tuple
from uuid import UUID
from datetime import datetime, timedelta
import json

logger = logging.getLogger(__name__)


class AuthTokenService:
    """Service for managing authentication tokens"""

    def __init__(self, db_pool: asyncpg.Pool):
        """Initialize with database connection pool"""
        self.db_pool = db_pool

    @staticmethod
    def generate_token() -> str:
        """Generate a secure random token"""
        return secrets.token_urlsafe(32)

    @staticmethod
    def hash_token(token: str) -> str:
        """Hash a token for secure storage"""
        return hashlib.sha256(token.encode()).hexdigest()

    async def create_email_verification_token(
        self,
        user_id: UUID,
        email: str,
        expires_in_hours: int = 24
    ) -> str:
        """Create an email verification token"""
        try:
            token = self.generate_token()
            token_hash = self.hash_token(token)

            async with self.db_pool.acquire() as conn:
                await conn.execute("""
                    INSERT INTO auth_tokens (
                        user_id, token_type, token_hash, expires_at, metadata
                    ) VALUES (
                        $1, 'email_verification', $2,
                        CURRENT_TIMESTAMP + ($3 || ' hours')::INTERVAL,
                        jsonb_build_object('email', $4)
                    )
                """, user_id, token_hash, expires_in_hours, email)

                logger.info(f"Created email verification token for user {user_id}")
                return token

        except Exception as e:
            logger.error(f"Error creating email verification token: {str(e)}")
            raise

    async def verify_email_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Verify an email verification token and mark email as verified"""
        try:
            token_hash = self.hash_token(token)

            async with self.db_pool.acquire() as conn:
                # Validate token and get user info
                result = await conn.fetchrow("""
                    UPDATE auth_tokens
                    SET is_used = true, used_at = CURRENT_TIMESTAMP
                    WHERE token_hash = $1
                    AND token_type = 'email_verification'
                    AND expires_at > CURRENT_TIMESTAMP
                    AND is_used = false
                    RETURNING user_id, metadata
                """, token_hash)

                if result:
                    # Update user email verification status
                    await conn.execute("""
                        UPDATE users
                        SET email_verified = true
                        WHERE id = $1
                    """, result['user_id'])

                    return {
                        'user_id': result['user_id'],
                        'email': result['metadata'].get('email')
                    }

                return None

        except Exception as e:
            logger.error(f"Error verifying email token: {str(e)}")
            return None

    async def create_password_reset_token(
        self,
        user_id: UUID,
        expires_in_hours: int = 1
    ) -> str:
        """Create a password reset token"""
        try:
            token = self.generate_token()
            token_hash = self.hash_token(token)

            async with self.db_pool.acquire() as conn:
                # Invalidate any existing password reset tokens
                await conn.execute("""
                    UPDATE auth_tokens
                    SET is_used = true
                    WHERE user_id = $1
                    AND token_type = 'password_reset'
                    AND is_used = false
                """, user_id)

                # Create new token
                await conn.execute("""
                    INSERT INTO auth_tokens (
                        user_id, token_type, token_hash, expires_at
                    ) VALUES (
                        $1, 'password_reset', $2,
                        CURRENT_TIMESTAMP + ($3 || ' hours')::INTERVAL
                    )
                """, user_id, token_hash, expires_in_hours)

                logger.info(f"Created password reset token for user {user_id}")
                return token

        except Exception as e:
            logger.error(f"Error creating password reset token: {str(e)}")
            raise

    async def verify_password_reset_token(self, token: str) -> Optional[UUID]:
        """Verify a password reset token and return user_id if valid"""
        try:
            token_hash = self.hash_token(token)

            async with self.db_pool.acquire() as conn:
                result = await conn.fetchrow("""
                    SELECT user_id
                    FROM auth_tokens
                    WHERE token_hash = $1
                    AND token_type = 'password_reset'
                    AND expires_at > CURRENT_TIMESTAMP
                    AND is_used = false
                """, token_hash)

                return result['user_id'] if result else None

        except Exception as e:
            logger.error(f"Error verifying password reset token: {str(e)}")
            return None

    async def use_password_reset_token(self, token: str) -> bool:
        """Mark a password reset token as used"""
        try:
            token_hash = self.hash_token(token)

            async with self.db_pool.acquire() as conn:
                result = await conn.execute("""
                    UPDATE auth_tokens
                    SET is_used = true, used_at = CURRENT_TIMESTAMP
                    WHERE token_hash = $1
                    AND token_type = 'password_reset'
                    AND expires_at > CURRENT_TIMESTAMP
                    AND is_used = false
                """, token_hash)

                return result.split()[-1] != '0'

        except Exception as e:
            logger.error(f"Error using password reset token: {str(e)}")
            return False

    async def create_refresh_token(
        self,
        user_id: UUID,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        expires_in_days: int = 30
    ) -> str:
        """Create a refresh token for JWT authentication"""
        try:
            token = self.generate_token()
            token_hash = self.hash_token(token)

            metadata = {}
            if ip_address:
                metadata['ip_address'] = ip_address
            if user_agent:
                metadata['user_agent'] = user_agent

            async with self.db_pool.acquire() as conn:
                await conn.execute("""
                    INSERT INTO auth_tokens (
                        user_id, token_type, token_hash, expires_at, metadata
                    ) VALUES (
                        $1, 'refresh', $2,
                        CURRENT_TIMESTAMP + ($3 || ' days')::INTERVAL,
                        $4
                    )
                """, user_id, token_hash, expires_in_days, json.dumps(metadata))

                logger.info(f"Created refresh token for user {user_id}")
                return token

        except Exception as e:
            logger.error(f"Error creating refresh token: {str(e)}")
            raise

    async def validate_refresh_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Validate a refresh token and update last used time"""
        try:
            token_hash = self.hash_token(token)

            async with self.db_pool.acquire() as conn:
                # Update last used time and get user info
                result = await conn.fetchrow("""
                    UPDATE auth_tokens
                    SET
                        used_at = CURRENT_TIMESTAMP,
                        metadata = jsonb_set(
                            metadata,
                            '{last_used}',
                            to_jsonb(CURRENT_TIMESTAMP)
                        )
                    WHERE token_hash = $1
                    AND token_type = 'refresh'
                    AND expires_at > CURRENT_TIMESTAMP
                    AND is_used = false
                    RETURNING user_id, metadata
                """, token_hash)

                if result:
                    return {
                        'user_id': result['user_id'],
                        'metadata': result['metadata']
                    }

                return None

        except Exception as e:
            logger.error(f"Error validating refresh token: {str(e)}")
            return None

    async def revoke_refresh_token(self, token: str) -> bool:
        """Revoke a refresh token"""
        try:
            token_hash = self.hash_token(token)

            async with self.db_pool.acquire() as conn:
                result = await conn.execute("""
                    UPDATE auth_tokens
                    SET is_used = true, used_at = CURRENT_TIMESTAMP
                    WHERE token_hash = $1
                    AND token_type = 'refresh'
                """, token_hash)

                return result.split()[-1] != '0'

        except Exception as e:
            logger.error(f"Error revoking refresh token: {str(e)}")
            return False

    async def revoke_all_refresh_tokens(self, user_id: UUID) -> int:
        """Revoke all refresh tokens for a user"""
        try:
            async with self.db_pool.acquire() as conn:
                result = await conn.execute("""
                    UPDATE auth_tokens
                    SET is_used = true, used_at = CURRENT_TIMESTAMP
                    WHERE user_id = $1
                    AND token_type = 'refresh'
                    AND is_used = false
                """, user_id)

                count = int(result.split()[-1])
                logger.info(f"Revoked {count} refresh tokens for user {user_id}")
                return count

        except Exception as e:
            logger.error(f"Error revoking all refresh tokens: {str(e)}")
            return 0

    async def cleanup_expired_tokens(self) -> int:
        """Clean up expired tokens from the database"""
        try:
            async with self.db_pool.acquire() as conn:
                result = await conn.fetchval("""
                    SELECT cleanup_expired_tokens()
                """)

                logger.info(f"Cleaned up {result} expired tokens")
                return result

        except Exception as e:
            logger.error(f"Error cleaning up expired tokens: {str(e)}")
            return 0

    async def create_api_key(
        self,
        user_id: UUID,
        key_name: str,
        permissions: Optional[Dict[str, Any]] = None,
        expires_in_days: Optional[int] = None
    ) -> str:
        """Create an API key for programmatic access"""
        try:
            token = self.generate_token()
            token_hash = self.hash_token(token)

            metadata = {
                'name': key_name,
                'permissions': permissions or {},
                'created_at': datetime.utcnow().isoformat()
            }

            async with self.db_pool.acquire() as conn:
                if expires_in_days:
                    expires_at = f"CURRENT_TIMESTAMP + ('{expires_in_days} days')::INTERVAL"
                else:
                    expires_at = "NULL"

                await conn.execute(f"""
                    INSERT INTO auth_tokens (
                        user_id, token_type, token_hash, expires_at, metadata
                    ) VALUES (
                        $1, 'api_key', $2,
                        {expires_at if expires_in_days else 'NULL'},
                        $3
                    )
                """, user_id, token_hash, json.dumps(metadata))

                logger.info(f"Created API key '{key_name}' for user {user_id}")
                return token

        except Exception as e:
            logger.error(f"Error creating API key: {str(e)}")
            raise

    async def validate_api_key(self, api_key: str) -> Optional[Dict[str, Any]]:
        """Validate an API key and return user info and permissions"""
        try:
            token_hash = self.hash_token(api_key)

            async with self.db_pool.acquire() as conn:
                result = await conn.fetchrow("""
                    SELECT user_id, metadata
                    FROM auth_tokens
                    WHERE token_hash = $1
                    AND token_type = 'api_key'
                    AND (expires_at IS NULL OR expires_at > CURRENT_TIMESTAMP)
                    AND is_used = false
                """, token_hash)

                if result:
                    # Update last used time
                    await conn.execute("""
                        UPDATE auth_tokens
                        SET
                            used_at = CURRENT_TIMESTAMP,
                            metadata = jsonb_set(
                                metadata,
                                '{last_used}',
                                to_jsonb(CURRENT_TIMESTAMP)
                            )
                        WHERE token_hash = $1
                    """, token_hash)

                    return {
                        'user_id': result['user_id'],
                        'permissions': result['metadata'].get('permissions', {}),
                        'key_name': result['metadata'].get('name')
                    }

                return None

        except Exception as e:
            logger.error(f"Error validating API key: {str(e)}")
            return None