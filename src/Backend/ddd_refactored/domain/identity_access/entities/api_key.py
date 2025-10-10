"""
ApiKey Entity
Following DDD Architecture Document Section 2.2
"""

from dataclasses import dataclass, field
from datetime import datetime, date
from typing import Optional, List, Dict, Any
from uuid import UUID, uuid4
from enum import Enum
import secrets
import hashlib

from ....shared.domain_base import Entity, BusinessRuleViolation


class ApiKeyStatus(str, Enum):
    """API key status"""
    ACTIVE = "active"
    EXPIRED = "expired"
    REVOKED = "revoked"
    SUSPENDED = "suspended"


class ApiKeyType(str, Enum):
    """Types of API keys"""
    PUBLIC = "public"  # Read-only, can be exposed in frontend
    PRIVATE = "private"  # Full access, server-side only
    RESTRICTED = "restricted"  # Limited scope


@dataclass
class ApiKey(Entity):
    """
    ApiKey Entity - API access keys for programmatic access
    As defined in DDD_ARCHITECTURE_REFACTORING.md Section 2.2
    """
    user_id: Optional[UUID] = None  # Can be null for system keys
    tenant_id: Optional[UUID] = None  # For tenant-specific keys

    # Key Information
    key_hash: str = ""  # Hashed key value
    key_prefix: str = ""  # First 8 chars for identification (e.g., "pk_live_")
    name: str = ""  # Human-readable name
    description: Optional[str] = None

    # Key Type and Status
    key_type: ApiKeyType = ApiKeyType.RESTRICTED
    status: ApiKeyStatus = ApiKeyStatus.ACTIVE

    # Permissions and Scope
    permissions: List[str] = field(default_factory=list)
    allowed_origins: List[str] = field(default_factory=list)  # CORS origins
    allowed_ips: List[str] = field(default_factory=list)  # IP whitelist

    # Rate Limiting
    rate_limit_per_minute: Optional[int] = 60
    rate_limit_per_hour: Optional[int] = 1000
    rate_limit_per_day: Optional[int] = 10000

    # Expiration
    expires_at: Optional[datetime] = None
    last_rotated_at: Optional[datetime] = None

    # Usage Statistics
    last_used_at: Optional[datetime] = None
    last_used_ip: Optional[str] = None
    usage_count: int = 0
    successful_requests: int = 0
    failed_requests: int = 0

    # Security
    revoked_at: Optional[datetime] = None
    revoked_by: Optional[UUID] = None
    revocation_reason: Optional[str] = None

    # Metadata
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def create(
        cls,
        name: str,
        key_type: ApiKeyType = ApiKeyType.RESTRICTED,
        user_id: Optional[UUID] = None,
        tenant_id: Optional[UUID] = None,
        permissions: Optional[List[str]] = None
    ) -> tuple['ApiKey', str]:
        """Factory method to create a new API key"""
        # Generate key with appropriate prefix
        prefix_map = {
            ApiKeyType.PUBLIC: "pk_",
            ApiKeyType.PRIVATE: "sk_",
            ApiKeyType.RESTRICTED: "rk_"
        }

        environment = "live"  # Could be "test" for test keys
        prefix = f"{prefix_map[key_type]}{environment}_"

        raw_key = prefix + secrets.token_urlsafe(32)
        key_hash = hashlib.sha256(raw_key.encode()).hexdigest()

        api_key = cls(
            user_id=user_id,
            tenant_id=tenant_id,
            key_hash=key_hash,
            key_prefix=raw_key[:12] + "...",  # Store prefix for identification
            name=name,
            key_type=key_type,
            permissions=permissions or []
        )

        return api_key, raw_key

    def verify_key(self, raw_key: str) -> bool:
        """Verify if the provided raw key matches this API key"""
        provided_hash = hashlib.sha256(raw_key.encode()).hexdigest()
        return provided_hash == self.key_hash

    def is_valid(self) -> bool:
        """Check if API key is valid"""
        if self.status != ApiKeyStatus.ACTIVE:
            return False

        if self.expires_at and datetime.utcnow() > self.expires_at:
            self.status = ApiKeyStatus.EXPIRED
            return False

        return True

    def is_allowed_origin(self, origin: str) -> bool:
        """Check if origin is allowed"""
        if not self.allowed_origins:
            return True  # No restrictions

        return origin in self.allowed_origins

    def is_allowed_ip(self, ip: str) -> bool:
        """Check if IP is allowed"""
        if not self.allowed_ips:
            return True  # No restrictions

        return ip in self.allowed_ips

    def has_permission(self, permission: str) -> bool:
        """Check if key has specific permission"""
        if self.key_type == ApiKeyType.PRIVATE:
            return True  # Private keys have all permissions

        if self.key_type == ApiKeyType.PUBLIC:
            # Public keys only have read permissions
            return permission.startswith("read:") or permission.startswith("list:")

        return permission in self.permissions

    def record_usage(self, ip_address: Optional[str] = None, successful: bool = True):
        """Record API key usage"""
        self.usage_count += 1
        self.last_used_at = datetime.utcnow()
        self.last_used_ip = ip_address

        if successful:
            self.successful_requests += 1
        else:
            self.failed_requests += 1

        self.mark_as_modified()

    def add_permission(self, permission: str):
        """Add a permission to the API key"""
        if self.key_type == ApiKeyType.PUBLIC:
            raise BusinessRuleViolation("Cannot add permissions to public keys")

        if permission not in self.permissions:
            self.permissions.append(permission)
            self.mark_as_modified()

    def remove_permission(self, permission: str):
        """Remove a permission from the API key"""
        if permission in self.permissions:
            self.permissions.remove(permission)
            self.mark_as_modified()

    def add_allowed_origin(self, origin: str):
        """Add an allowed origin"""
        if origin not in self.allowed_origins:
            self.allowed_origins.append(origin)
            self.mark_as_modified()

    def remove_allowed_origin(self, origin: str):
        """Remove an allowed origin"""
        if origin in self.allowed_origins:
            self.allowed_origins.remove(origin)
            self.mark_as_modified()

    def add_allowed_ip(self, ip: str):
        """Add an allowed IP"""
        if ip not in self.allowed_ips:
            self.allowed_ips.append(ip)
            self.mark_as_modified()

    def remove_allowed_ip(self, ip: str):
        """Remove an allowed IP"""
        if ip in self.allowed_ips:
            self.allowed_ips.remove(ip)
            self.mark_as_modified()

    def set_rate_limits(
        self,
        per_minute: Optional[int] = None,
        per_hour: Optional[int] = None,
        per_day: Optional[int] = None
    ):
        """Set rate limits"""
        if per_minute is not None:
            if per_minute < 0:
                raise BusinessRuleViolation("Rate limit must be positive")
            self.rate_limit_per_minute = per_minute

        if per_hour is not None:
            if per_hour < 0:
                raise BusinessRuleViolation("Rate limit must be positive")
            self.rate_limit_per_hour = per_hour

        if per_day is not None:
            if per_day < 0:
                raise BusinessRuleViolation("Rate limit must be positive")
            self.rate_limit_per_day = per_day

        self.mark_as_modified()

    def set_expiration(self, expires_at: datetime):
        """Set expiration date"""
        if expires_at <= datetime.utcnow():
            raise BusinessRuleViolation("Expiration must be in the future")

        self.expires_at = expires_at
        self.mark_as_modified()

    def rotate(self) -> tuple['ApiKey', str]:
        """Rotate API key (create new key, revoke this one)"""
        # Create new key with same settings
        new_key, raw_key = ApiKey.create(
            name=f"{self.name} (rotated)",
            key_type=self.key_type,
            user_id=self.user_id,
            tenant_id=self.tenant_id,
            permissions=self.permissions.copy()
        )

        # Copy settings
        new_key.allowed_origins = self.allowed_origins.copy()
        new_key.allowed_ips = self.allowed_ips.copy()
        new_key.rate_limit_per_minute = self.rate_limit_per_minute
        new_key.rate_limit_per_hour = self.rate_limit_per_hour
        new_key.rate_limit_per_day = self.rate_limit_per_day

        # Revoke current key
        self.revoke(reason="Key rotated")
        self.last_rotated_at = datetime.utcnow()

        return new_key, raw_key

    def revoke(self, revoked_by: Optional[UUID] = None, reason: Optional[str] = None):
        """Revoke the API key"""
        if self.status == ApiKeyStatus.REVOKED:
            raise BusinessRuleViolation("API key is already revoked")

        self.status = ApiKeyStatus.REVOKED
        self.revoked_at = datetime.utcnow()
        self.revoked_by = revoked_by
        self.revocation_reason = reason
        self.mark_as_modified()

    def suspend(self):
        """Temporarily suspend the API key"""
        if self.status != ApiKeyStatus.ACTIVE:
            raise BusinessRuleViolation("Can only suspend active keys")

        self.status = ApiKeyStatus.SUSPENDED
        self.mark_as_modified()

    def reactivate(self):
        """Reactivate a suspended API key"""
        if self.status != ApiKeyStatus.SUSPENDED:
            raise BusinessRuleViolation("Can only reactivate suspended keys")

        self.status = ApiKeyStatus.ACTIVE
        self.mark_as_modified()

    def get_failure_rate(self) -> float:
        """Calculate failure rate"""
        total = self.successful_requests + self.failed_requests
        if total == 0:
            return 0.0
        return self.failed_requests / total

    def validate(self) -> List[str]:
        """Validate API key data"""
        errors = []

        if not self.name:
            errors.append("API key name is required")

        if not self.key_hash:
            errors.append("Key hash is required")

        if self.rate_limit_per_minute and self.rate_limit_per_minute < 0:
            errors.append("Rate limit must be positive")

        if self.expires_at and self.expires_at <= datetime.utcnow():
            errors.append("Expiration must be in the future")

        return errors