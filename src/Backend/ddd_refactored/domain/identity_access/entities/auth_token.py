"""
AuthToken Entity
Following DDD Architecture Document Section 2.2
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from uuid import UUID, uuid4
from enum import Enum
import secrets
import hashlib

from ....shared.domain_base import Entity, BusinessRuleViolation


class TokenType(str, Enum):
    """Types of authentication tokens"""
    ACCESS = "access"
    REFRESH = "refresh"
    PASSWORD_RESET = "password_reset"
    EMAIL_VERIFICATION = "email_verification"
    PHONE_VERIFICATION = "phone_verification"
    API = "api"
    SESSION = "session"


class TokenStatus(str, Enum):
    """Token status"""
    ACTIVE = "active"
    EXPIRED = "expired"
    REVOKED = "revoked"
    USED = "used"


@dataclass
class AuthToken(Entity):
    """
    AuthToken Entity - Authentication and verification tokens
    As defined in DDD_ARCHITECTURE_REFACTORING.md Section 2.2
    """
    user_id: UUID = field(default_factory=uuid4)

    # Token Information
    token_hash: str = ""  # Hashed token value
    token_type: TokenType = TokenType.ACCESS
    status: TokenStatus = TokenStatus.ACTIVE

    # Expiration
    expires_at: datetime = field(default_factory=lambda: datetime.utcnow() + timedelta(hours=1))

    # Usage Tracking
    used_at: Optional[datetime] = None
    use_count: int = 0
    max_uses: Optional[int] = None  # None means unlimited

    # Device/Session Information
    device_id: Optional[str] = None
    device_type: Optional[str] = None  # mobile, web, desktop
    device_name: Optional[str] = None  # e.g., "iPhone 12 Pro"
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None

    # Scope and Permissions
    scope: List[str] = field(default_factory=list)  # Token permissions/scope

    # Related Tokens
    refresh_token_id: Optional[UUID] = None  # For access tokens
    parent_token_id: Optional[UUID] = None  # For refresh chains

    # Security
    revoked_at: Optional[datetime] = None
    revoked_by: Optional[UUID] = None
    revocation_reason: Optional[str] = None

    # Metadata
    created_at: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def create_access_token(
        cls,
        user_id: UUID,
        expires_in: timedelta = timedelta(hours=1),
        scope: Optional[List[str]] = None,
        device_info: Optional[Dict[str, str]] = None
    ) -> tuple['AuthToken', str]:
        """Create an access token"""
        raw_token = secrets.token_urlsafe(32)
        token_hash = hashlib.sha256(raw_token.encode()).hexdigest()

        token = cls(
            user_id=user_id,
            token_hash=token_hash,
            token_type=TokenType.ACCESS,
            expires_at=datetime.utcnow() + expires_in,
            scope=scope or [],
            device_id=device_info.get('device_id') if device_info else None,
            device_type=device_info.get('device_type') if device_info else None,
            device_name=device_info.get('device_name') if device_info else None
        )

        return token, raw_token

    @classmethod
    def create_refresh_token(
        cls,
        user_id: UUID,
        access_token_id: UUID,
        expires_in: timedelta = timedelta(days=30)
    ) -> tuple['AuthToken', str]:
        """Create a refresh token"""
        raw_token = secrets.token_urlsafe(48)
        token_hash = hashlib.sha256(raw_token.encode()).hexdigest()

        token = cls(
            user_id=user_id,
            token_hash=token_hash,
            token_type=TokenType.REFRESH,
            expires_at=datetime.utcnow() + expires_in,
            parent_token_id=access_token_id
        )

        return token, raw_token

    @classmethod
    def create_verification_token(
        cls,
        user_id: UUID,
        token_type: TokenType,
        expires_in: timedelta = timedelta(hours=24),
        max_uses: int = 1
    ) -> tuple['AuthToken', str]:
        """Create a verification token (email, phone, password reset)"""
        if token_type not in [TokenType.EMAIL_VERIFICATION, TokenType.PHONE_VERIFICATION, TokenType.PASSWORD_RESET]:
            raise BusinessRuleViolation(f"Invalid verification token type: {token_type}")

        raw_token = secrets.token_urlsafe(32)
        token_hash = hashlib.sha256(raw_token.encode()).hexdigest()

        token = cls(
            user_id=user_id,
            token_hash=token_hash,
            token_type=token_type,
            expires_at=datetime.utcnow() + expires_in,
            max_uses=max_uses
        )

        return token, raw_token

    def verify_token(self, raw_token: str) -> bool:
        """Verify if the provided raw token matches this token"""
        provided_hash = hashlib.sha256(raw_token.encode()).hexdigest()
        return provided_hash == self.token_hash

    def is_valid(self) -> bool:
        """Check if token is valid"""
        if self.status != TokenStatus.ACTIVE:
            return False

        if datetime.utcnow() > self.expires_at:
            self.status = TokenStatus.EXPIRED
            return False

        if self.max_uses and self.use_count >= self.max_uses:
            self.status = TokenStatus.USED
            return False

        return True

    def use(self):
        """Record token usage"""
        if not self.is_valid():
            raise BusinessRuleViolation("Cannot use invalid token")

        self.use_count += 1
        self.used_at = datetime.utcnow()

        if self.max_uses and self.use_count >= self.max_uses:
            self.status = TokenStatus.USED

        self.mark_as_modified()

    def revoke(self, revoked_by: Optional[UUID] = None, reason: Optional[str] = None):
        """Revoke the token"""
        if self.status == TokenStatus.REVOKED:
            raise BusinessRuleViolation("Token is already revoked")

        self.status = TokenStatus.REVOKED
        self.revoked_at = datetime.utcnow()
        self.revoked_by = revoked_by
        self.revocation_reason = reason
        self.mark_as_modified()

    def extend_expiration(self, additional_time: timedelta):
        """Extend token expiration"""
        if self.status != TokenStatus.ACTIVE:
            raise BusinessRuleViolation("Can only extend active tokens")

        self.expires_at = self.expires_at + additional_time
        self.mark_as_modified()

    def rotate(self) -> tuple['AuthToken', str]:
        """Rotate token (create new token, invalidate this one)"""
        if self.token_type != TokenType.REFRESH:
            raise BusinessRuleViolation("Only refresh tokens can be rotated")

        # Create new token
        new_token, raw_token = AuthToken.create_refresh_token(
            user_id=self.user_id,
            access_token_id=self.parent_token_id,
            expires_in=self.expires_at - datetime.utcnow()
        )

        # Revoke current token
        self.revoke(reason="Token rotated")

        return new_token, raw_token

    def add_scope(self, scope: str):
        """Add a scope to the token"""
        if scope not in self.scope:
            self.scope.append(scope)
            self.mark_as_modified()

    def remove_scope(self, scope: str):
        """Remove a scope from the token"""
        if scope in self.scope:
            self.scope.remove(scope)
            self.mark_as_modified()

    def has_scope(self, required_scope: str) -> bool:
        """Check if token has required scope"""
        return required_scope in self.scope

    def get_time_until_expiry(self) -> timedelta:
        """Get time remaining until token expires"""
        return self.expires_at - datetime.utcnow()

    def is_expired(self) -> bool:
        """Check if token is expired"""
        return datetime.utcnow() > self.expires_at

    def update_device_info(
        self,
        device_id: Optional[str] = None,
        device_type: Optional[str] = None,
        device_name: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ):
        """Update device information"""
        if device_id is not None:
            self.device_id = device_id
        if device_type is not None:
            self.device_type = device_type
        if device_name is not None:
            self.device_name = device_name
        if ip_address is not None:
            self.ip_address = ip_address
        if user_agent is not None:
            self.user_agent = user_agent

        self.mark_as_modified()

    def validate(self) -> List[str]:
        """Validate token data"""
        errors = []

        if not self.user_id:
            errors.append("User ID is required")

        if not self.token_hash:
            errors.append("Token hash is required")

        if self.expires_at <= datetime.utcnow():
            errors.append("Token expiration must be in the future")

        if self.max_uses and self.max_uses < 1:
            errors.append("Max uses must be at least 1")

        return errors