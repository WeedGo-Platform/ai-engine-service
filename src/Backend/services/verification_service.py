"""
Verification Service - Manages verification codes for signup flow
Handles code generation, storage, validation, and rate limiting
Supports both in-memory and Redis storage backends
"""

import secrets
import hashlib
import logging
import os
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
import json

logger = logging.getLogger(__name__)


@dataclass
class VerificationCode:
    """Verification code data structure"""
    email: str
    code_hash: str
    attempts: int
    max_attempts: int
    created_at: datetime
    expires_at: datetime
    verification_tier: str  # "auto_approved" or "manual_review"
    store_info: Dict[str, Any]
    phone: Optional[str] = None

    def to_dict(self) -> dict:
        """Convert to dictionary for storage"""
        data = asdict(self)
        data['created_at'] = self.created_at.isoformat()
        data['expires_at'] = self.expires_at.isoformat()
        return data

    @classmethod
    def from_dict(cls, data: dict) -> 'VerificationCode':
        """Create from dictionary"""
        data['created_at'] = datetime.fromisoformat(data['created_at'])
        data['expires_at'] = datetime.fromisoformat(data['expires_at'])
        return cls(**data)


class VerificationService:
    """
    Service for managing verification codes during signup

    Supports both in-memory and Redis storage backends
    Redis is used if REDIS_HOST environment variable is set
    """

    def __init__(self, use_redis: Optional[bool] = None):
        # Determine storage backend
        if use_redis is None:
            use_redis = os.getenv('REDIS_HOST') is not None

        self.use_redis = use_redis
        self.redis_store = None

        if self.use_redis:
            try:
                from services.redis_verification_store import get_redis_verification_store
                self.redis_store = get_redis_verification_store()
                logger.info("VerificationService initialized with Redis backend")
            except Exception as e:
                logger.warning(f"Failed to initialize Redis, falling back to in-memory: {e}")
                self.use_redis = False

        if not self.use_redis:
            self._storage: Dict[str, VerificationCode] = {}
            self._rate_limits: Dict[str, list] = {}  # email -> list of timestamps
            logger.info("VerificationService initialized with in-memory backend")

    def _hash_code(self, code: str) -> str:
        """Hash verification code for secure storage"""
        return hashlib.sha256(code.encode()).hexdigest()

    def _check_rate_limit(self, email: str, max_requests: int = 3, window_hours: int = 1) -> bool:
        """
        Check if email has exceeded rate limit

        Args:
            email: Email address to check
            max_requests: Maximum requests allowed in window
            window_hours: Time window in hours

        Returns:
            True if within limit, False if exceeded
        """
        if self.use_redis and self.redis_store:
            # Use Redis rate limiting
            window_seconds = window_hours * 3600
            return self.redis_store.check_rate_limit(
                identifier=f"verification:{email}",
                max_requests=max_requests,
                window_seconds=window_seconds
            )
        else:
            # Use in-memory rate limiting
            now = datetime.utcnow()
            cutoff = now - timedelta(hours=window_hours)

            # Get timestamps for this email
            if email not in self._rate_limits:
                self._rate_limits[email] = []

            # Remove old timestamps
            self._rate_limits[email] = [
                ts for ts in self._rate_limits[email]
                if ts > cutoff
            ]

            # Check limit
            if len(self._rate_limits[email]) >= max_requests:
                logger.warning(f"Rate limit exceeded for {email}")
                return False

            # Add current request
            self._rate_limits[email].append(now)
            return True

    def generate_code(
        self,
        email: str,
        store_info: Dict[str, Any],
        verification_tier: str,
        phone: Optional[str] = None,
        code_length: int = 6,
        expiry_minutes: int = 5
    ) -> tuple[str, str]:
        """
        Generate a new verification code

        Args:
            email: Email address for verification
            store_info: Store information from CRSA
            verification_tier: "auto_approved" or "manual_review"
            phone: Optional phone number
            code_length: Length of code (default 6)
            expiry_minutes: Code expiry time in minutes (default 5)

        Returns:
            tuple of (code, verification_id)

        Raises:
            ValueError: If rate limit exceeded
        """
        # Check rate limit (3 codes per hour per email)
        if not self._check_rate_limit(email, max_requests=3, window_hours=1):
            raise ValueError(
                "Too many verification requests. Please try again in an hour."
            )

        # Generate random code
        code = ''.join(secrets.choice('0123456789') for _ in range(code_length))

        # Create verification record
        now = datetime.utcnow()
        expires_at = now + timedelta(minutes=expiry_minutes)

        verification_record = VerificationCode(
            email=email,
            code_hash=self._hash_code(code),
            attempts=0,
            max_attempts=3,
            created_at=now,
            expires_at=expires_at,
            verification_tier=verification_tier,
            store_info=store_info,
            phone=phone
        )

        # Store verification code
        verification_id = f"verify_{email}_{int(now.timestamp())}"

        if self.use_redis and self.redis_store:
            # Store in Redis
            self.redis_store.store_verification_code(
                verification_id=verification_id,
                code_hash=verification_record.code_hash,
                email=email,
                store_info=store_info,
                verification_tier=verification_tier,
                phone=phone,
                expiry_minutes=expiry_minutes,
                max_attempts=3
            )
        else:
            # Store in memory
            self._storage[verification_id] = verification_record

        logger.info(
            f"Generated verification code for {email} "
            f"(tier: {verification_tier}, expires: {expiry_minutes}min, backend: {'redis' if self.use_redis else 'memory'})"
        )

        return code, verification_id

    def verify_code(
        self,
        verification_id: str,
        code: str,
        email: str
    ) -> tuple[bool, Optional[str], Optional[VerificationCode]]:
        """
        Verify a code provided by user

        Args:
            verification_id: Verification ID from generate_code
            code: Code provided by user
            email: Email address for double-check

        Returns:
            tuple of (is_valid, error_message, verification_record)
        """
        if self.use_redis and self.redis_store:
            return self._verify_code_redis(verification_id, code, email)
        else:
            return self._verify_code_memory(verification_id, code, email)

    def _verify_code_redis(
        self,
        verification_id: str,
        code: str,
        email: str
    ) -> tuple[bool, Optional[str], Optional[VerificationCode]]:
        """Verify code using Redis backend"""
        # Get verification from Redis
        data = self.redis_store.get_verification_code(verification_id)

        if not data:
            return False, "Verification session not found or expired", None

        # Verify email matches
        if data['email'] != email:
            logger.warning(f"Email mismatch for verification {verification_id}")
            return False, "Invalid verification session", None

        # Check expiry
        expires_at = datetime.fromisoformat(data['expires_at'])
        if datetime.utcnow() > expires_at:
            self.redis_store.delete_verification_code(verification_id)
            return False, "Verification code has expired. Please request a new one.", None

        # Check max attempts
        if data['attempts'] >= data['max_attempts']:
            self.redis_store.delete_verification_code(verification_id)
            return False, "Too many incorrect attempts. Please request a new code.", None

        # Verify code
        code_hash = self._hash_code(code)
        new_attempts = self.redis_store.increment_attempts(verification_id)

        if code_hash == data['code_hash']:
            logger.info(f"Verification successful for {email} (Redis)")
            # Convert Redis data to VerificationCode for consistency
            verification = VerificationCode(
                email=data['email'],
                code_hash=data['code_hash'],
                attempts=new_attempts,
                max_attempts=data['max_attempts'],
                created_at=datetime.fromisoformat(data['created_at']),
                expires_at=expires_at,
                verification_tier=data['verification_tier'],
                store_info=data['store_info'],
                phone=data.get('phone')
            )
            return True, None, verification
        else:
            attempts_remaining = data['max_attempts'] - new_attempts
            logger.info(f"Incorrect code for {email}. Attempts remaining: {attempts_remaining}")

            if attempts_remaining > 0:
                return (
                    False,
                    f"Incorrect code. {attempts_remaining} attempts remaining.",
                    None
                )
            else:
                self.redis_store.delete_verification_code(verification_id)
                return (
                    False,
                    "Maximum attempts exceeded. Please request a new code.",
                    None
                )

    def _verify_code_memory(
        self,
        verification_id: str,
        code: str,
        email: str
    ) -> tuple[bool, Optional[str], Optional[VerificationCode]]:
        """Verify code using in-memory backend"""
        # Check if verification exists
        if verification_id not in self._storage:
            return False, "Verification session not found or expired", None

        verification = self._storage[verification_id]

        # Verify email matches
        if verification.email != email:
            logger.warning(f"Email mismatch for verification {verification_id}")
            return False, "Invalid verification session", None

        # Check expiry
        if datetime.utcnow() > verification.expires_at:
            del self._storage[verification_id]
            return False, "Verification code has expired. Please request a new one.", None

        # Check max attempts
        if verification.attempts >= verification.max_attempts:
            del self._storage[verification_id]
            return False, "Too many incorrect attempts. Please request a new code.", None

        # Verify code
        code_hash = self._hash_code(code)
        verification.attempts += 1

        if code_hash == verification.code_hash:
            logger.info(f"Verification successful for {email} (memory)")
            return True, None, verification
        else:
            attempts_remaining = verification.max_attempts - verification.attempts
            logger.info(
                f"Incorrect code for {email}. "
                f"Attempts remaining: {attempts_remaining}"
            )

            if attempts_remaining > 0:
                return (
                    False,
                    f"Incorrect code. {attempts_remaining} attempts remaining.",
                    None
                )
            else:
                del self._storage[verification_id]
                return (
                    False,
                    "Maximum attempts exceeded. Please request a new code.",
                    None
                )

    def mark_verified(self, verification_id: str) -> bool:
        """
        Mark a verification as completed and remove from storage

        Args:
            verification_id: Verification ID to mark as complete

        Returns:
            True if found and removed, False otherwise
        """
        if self.use_redis and self.redis_store:
            result = self.redis_store.delete_verification_code(verification_id)
            if result:
                logger.info(f"Marked verification {verification_id} as complete (Redis)")
            return result
        else:
            if verification_id in self._storage:
                del self._storage[verification_id]
                logger.info(f"Marked verification {verification_id} as complete (memory)")
                return True
            return False

    def get_verification_info(self, verification_id: str) -> Optional[Dict[str, Any]]:
        """
        Get verification information without validating code

        Args:
            verification_id: Verification ID to lookup

        Returns:
            Dictionary with verification info or None
        """
        if self.use_redis and self.redis_store:
            data = self.redis_store.get_verification_code(verification_id)
            if not data:
                return None

            expires_at = datetime.fromisoformat(data['expires_at'])
            return {
                "email": data['email'],
                "phone": data.get('phone'),
                "verification_tier": data['verification_tier'],
                "store_info": data['store_info'],
                "attempts": data['attempts'],
                "max_attempts": data['max_attempts'],
                "expires_at": data['expires_at'],
                "is_expired": datetime.utcnow() > expires_at
            }
        else:
            if verification_id not in self._storage:
                return None

            verification = self._storage[verification_id]

            return {
                "email": verification.email,
                "phone": verification.phone,
                "verification_tier": verification.verification_tier,
                "store_info": verification.store_info,
                "attempts": verification.attempts,
                "max_attempts": verification.max_attempts,
                "expires_at": verification.expires_at.isoformat(),
                "is_expired": datetime.utcnow() > verification.expires_at
            }

    def cleanup_expired(self) -> int:
        """
        Remove expired verification codes

        Returns:
            Number of codes removed
        """
        if self.use_redis and self.redis_store:
            # Redis handles expiry automatically with TTL
            return self.redis_store.cleanup_expired()
        else:
            now = datetime.utcnow()
            expired_ids = [
                vid for vid, verification in self._storage.items()
                if now > verification.expires_at
            ]

            for vid in expired_ids:
                del self._storage[vid]

            if expired_ids:
                logger.info(f"Cleaned up {len(expired_ids)} expired verification codes")

            return len(expired_ids)


# Global singleton instance
_verification_service: Optional[VerificationService] = None


def get_verification_service() -> VerificationService:
    """Get or create verification service singleton"""
    global _verification_service
    if _verification_service is None:
        _verification_service = VerificationService()
    return _verification_service
