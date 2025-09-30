"""
User Aggregate Root
Following DDD Architecture Document Section 2.2
"""

from dataclasses import dataclass, field
from datetime import datetime, date, timedelta
from typing import Optional, List, Dict, Any
from uuid import UUID, uuid4
from enum import Enum
import hashlib
import secrets

from ....shared.domain_base import AggregateRoot, BusinessRuleViolation, DomainEvent
from ..value_objects.permission import Permission, PermissionSet


class UserStatus(str, Enum):
    """User account status"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    PENDING = "pending"
    DELETED = "deleted"


class UserType(str, Enum):
    """Types of users in the system"""
    CUSTOMER = "customer"
    STAFF = "staff"
    ADMIN = "admin"
    SYSTEM = "system"


class AuthProvider(str, Enum):
    """Authentication providers"""
    LOCAL = "local"
    GOOGLE = "google"
    FACEBOOK = "facebook"
    APPLE = "apple"
    PHONE = "phone"


# Domain Events
class UserRegistered(DomainEvent):
    def __init__(self, user_id: UUID, email: str, user_type: str):
        super().__init__(user_id)
        self.email = email
        self.user_type = user_type

    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()
        data.update({
            'email': self.email,
            'user_type': self.user_type
        })
        return data


class UserActivated(DomainEvent):
    def __init__(self, user_id: UUID, activated_at: datetime):
        super().__init__(user_id)
        self.activated_at = activated_at

    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()
        data.update({
            'activated_at': self.activated_at.isoformat()
        })
        return data


class UserSuspended(DomainEvent):
    def __init__(self, user_id: UUID, reason: str):
        super().__init__(user_id)
        self.reason = reason

    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()
        data.update({
            'reason': self.reason
        })
        return data


class PasswordChanged(DomainEvent):
    def __init__(self, user_id: UUID):
        super().__init__(user_id)


class LoginAttempt(DomainEvent):
    def __init__(self, user_id: UUID, successful: bool, ip_address: Optional[str] = None):
        super().__init__(user_id)
        self.successful = successful
        self.ip_address = ip_address

    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()
        data.update({
            'successful': self.successful,
            'ip_address': self.ip_address
        })
        return data


@dataclass
class User(AggregateRoot):
    """
    User aggregate root
    As defined in DDD_ARCHITECTURE_REFACTORING.md Section 2.2
    """
    # Basic Information
    email: str = ""
    phone: Optional[str] = None
    username: Optional[str] = None
    user_type: UserType = UserType.CUSTOMER
    status: UserStatus = UserStatus.PENDING

    # Authentication
    password_hash: Optional[str] = None
    auth_provider: AuthProvider = AuthProvider.LOCAL
    provider_user_id: Optional[str] = None  # ID from external provider

    # Personal Information
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    date_of_birth: Optional[date] = None
    gender: Optional[str] = None

    # Verification
    email_verified: bool = False
    email_verified_at: Optional[datetime] = None
    phone_verified: bool = False
    phone_verified_at: Optional[datetime] = None
    age_verified: bool = False
    age_verified_at: Optional[datetime] = None

    # Security
    two_factor_enabled: bool = False
    two_factor_secret: Optional[str] = None
    security_questions: List[Dict[str, str]] = field(default_factory=list)
    failed_login_attempts: int = 0
    last_failed_login: Optional[datetime] = None
    account_locked_until: Optional[datetime] = None

    # Permissions
    permissions: List[str] = field(default_factory=list)  # Direct permissions
    roles: List[str] = field(default_factory=list)  # Role assignments

    # Activity Tracking
    last_login_at: Optional[datetime] = None
    last_login_ip: Optional[str] = None
    last_activity_at: Optional[datetime] = None
    login_count: int = 0
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    # Preferences
    language: str = "en"
    timezone: str = "America/Toronto"
    currency: str = "CAD"
    notifications_enabled: bool = True
    marketing_emails_enabled: bool = False

    # Metadata
    metadata: Dict[str, Any] = field(default_factory=dict)
    tags: List[str] = field(default_factory=list)

    @classmethod
    def create(
        cls,
        email: str,
        user_type: UserType = UserType.CUSTOMER,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        phone: Optional[str] = None
    ) -> 'User':
        """Factory method to create a new user"""
        user = cls(
            email=email.lower(),
            user_type=user_type,
            first_name=first_name,
            last_name=last_name,
            phone=phone,
            status=UserStatus.PENDING
        )

        # Raise domain event
        user.add_domain_event(UserRegistered(
            user_id=user.id,
            email=email,
            user_type=user_type.value
        ))

        return user

    def set_password(self, password: str):
        """Set user password (hashed)"""
        if len(password) < 8:
            raise BusinessRuleViolation("Password must be at least 8 characters")

        # Simple password hashing (in production, use bcrypt or similar)
        self.password_hash = hashlib.sha256(password.encode()).hexdigest()
        self.mark_as_modified()

        self.add_domain_event(PasswordChanged(user_id=self.id))

    def verify_password(self, password: str) -> bool:
        """Verify user password"""
        if not self.password_hash:
            return False

        password_hash = hashlib.sha256(password.encode()).hexdigest()
        return self.password_hash == password_hash

    def activate(self):
        """Activate user account"""
        if self.status == UserStatus.ACTIVE:
            raise BusinessRuleViolation("User is already active")

        if self.status == UserStatus.DELETED:
            raise BusinessRuleViolation("Cannot activate deleted user")

        self.status = UserStatus.ACTIVE
        self.email_verified = True
        self.email_verified_at = datetime.utcnow()
        self.mark_as_modified()

        self.add_domain_event(UserActivated(
            user_id=self.id,
            activated_at=datetime.utcnow()
        ))

    def suspend(self, reason: str):
        """Suspend user account"""
        if self.status == UserStatus.SUSPENDED:
            raise BusinessRuleViolation("User is already suspended")

        if self.status == UserStatus.DELETED:
            raise BusinessRuleViolation("Cannot suspend deleted user")

        self.status = UserStatus.SUSPENDED
        self.metadata['suspension_reason'] = reason
        self.metadata['suspension_date'] = datetime.utcnow().isoformat()
        self.mark_as_modified()

        self.add_domain_event(UserSuspended(
            user_id=self.id,
            reason=reason
        ))

    def reactivate(self):
        """Reactivate suspended user"""
        if self.status not in [UserStatus.SUSPENDED, UserStatus.INACTIVE]:
            raise BusinessRuleViolation("Can only reactivate suspended or inactive users")

        self.status = UserStatus.ACTIVE
        self.metadata.pop('suspension_reason', None)
        self.metadata.pop('suspension_date', None)
        self.failed_login_attempts = 0
        self.account_locked_until = None
        self.mark_as_modified()

    def soft_delete(self):
        """Soft delete user (mark as deleted)"""
        if self.status == UserStatus.DELETED:
            raise BusinessRuleViolation("User is already deleted")

        self.status = UserStatus.DELETED
        self.metadata['deleted_at'] = datetime.utcnow().isoformat()

        # Anonymize data
        self.email = f"deleted_{self.id}@deleted.com"
        self.phone = None
        self.first_name = "Deleted"
        self.last_name = "User"
        self.password_hash = None
        self.two_factor_secret = None

        self.mark_as_modified()

    def record_login(self, ip_address: Optional[str] = None, successful: bool = True):
        """Record login attempt"""
        if successful:
            self.last_login_at = datetime.utcnow()
            self.last_login_ip = ip_address
            self.login_count += 1
            self.failed_login_attempts = 0
            self.last_activity_at = datetime.utcnow()
        else:
            self.failed_login_attempts += 1
            self.last_failed_login = datetime.utcnow()

            # Lock account after 5 failed attempts
            if self.failed_login_attempts >= 5:
                self.account_locked_until = datetime.utcnow() + timedelta(minutes=30)

        self.mark_as_modified()

        self.add_domain_event(LoginAttempt(
            user_id=self.id,
            successful=successful,
            ip_address=ip_address
        ))

    def is_account_locked(self) -> bool:
        """Check if account is locked due to failed login attempts"""
        if not self.account_locked_until:
            return False
        return datetime.utcnow() < self.account_locked_until

    def unlock_account(self):
        """Unlock account"""
        self.account_locked_until = None
        self.failed_login_attempts = 0
        self.mark_as_modified()

    def verify_email(self):
        """Mark email as verified"""
        if self.email_verified:
            raise BusinessRuleViolation("Email is already verified")

        self.email_verified = True
        self.email_verified_at = datetime.utcnow()
        self.mark_as_modified()

    def verify_phone(self):
        """Mark phone as verified"""
        if not self.phone:
            raise BusinessRuleViolation("No phone number to verify")

        if self.phone_verified:
            raise BusinessRuleViolation("Phone is already verified")

        self.phone_verified = True
        self.phone_verified_at = datetime.utcnow()
        self.mark_as_modified()

    def verify_age(self):
        """Mark age as verified (19+ for cannabis)"""
        if self.age_verified:
            raise BusinessRuleViolation("Age is already verified")

        # Check if user is 19+ (for Ontario)
        if self.date_of_birth:
            today = date.today()
            age = today.year - self.date_of_birth.year
            if today.month < self.date_of_birth.month or \
               (today.month == self.date_of_birth.month and today.day < self.date_of_birth.day):
                age -= 1

            if age < 19:
                raise BusinessRuleViolation("User must be 19 or older")

        self.age_verified = True
        self.age_verified_at = datetime.utcnow()
        self.mark_as_modified()

    def enable_two_factor(self) -> str:
        """Enable two-factor authentication"""
        if self.two_factor_enabled:
            raise BusinessRuleViolation("Two-factor authentication is already enabled")

        # Generate secret
        self.two_factor_secret = secrets.token_hex(16)
        self.two_factor_enabled = True
        self.mark_as_modified()

        return self.two_factor_secret

    def disable_two_factor(self):
        """Disable two-factor authentication"""
        if not self.two_factor_enabled:
            raise BusinessRuleViolation("Two-factor authentication is not enabled")

        self.two_factor_enabled = False
        self.two_factor_secret = None
        self.mark_as_modified()

    def add_permission(self, permission: str):
        """Add a direct permission to user"""
        if permission not in self.permissions:
            self.permissions.append(permission)
            self.mark_as_modified()

    def remove_permission(self, permission: str):
        """Remove a direct permission from user"""
        if permission in self.permissions:
            self.permissions.remove(permission)
            self.mark_as_modified()

    def add_role(self, role: str):
        """Add a role to user"""
        if role not in self.roles:
            self.roles.append(role)
            self.mark_as_modified()

    def remove_role(self, role: str):
        """Remove a role from user"""
        if role in self.roles:
            self.roles.remove(role)
            self.mark_as_modified()

    def has_permission(self, permission: str) -> bool:
        """Check if user has a specific permission"""
        return permission in self.permissions

    def has_role(self, role: str) -> bool:
        """Check if user has a specific role"""
        return role in self.roles

    def update_profile(
        self,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        date_of_birth: Optional[date] = None,
        gender: Optional[str] = None
    ):
        """Update user profile information"""
        if first_name is not None:
            self.first_name = first_name
        if last_name is not None:
            self.last_name = last_name
        if date_of_birth is not None:
            self.date_of_birth = date_of_birth
        if gender is not None:
            self.gender = gender

        self.updated_at = datetime.utcnow()
        self.mark_as_modified()

    def update_preferences(
        self,
        language: Optional[str] = None,
        timezone: Optional[str] = None,
        currency: Optional[str] = None,
        notifications_enabled: Optional[bool] = None,
        marketing_emails_enabled: Optional[bool] = None
    ):
        """Update user preferences"""
        if language:
            self.language = language
        if timezone:
            self.timezone = timezone
        if currency:
            self.currency = currency
        if notifications_enabled is not None:
            self.notifications_enabled = notifications_enabled
        if marketing_emails_enabled is not None:
            self.marketing_emails_enabled = marketing_emails_enabled

        self.mark_as_modified()

    def add_tag(self, tag: str):
        """Add a tag to user"""
        if tag not in self.tags:
            self.tags.append(tag)
            self.mark_as_modified()

    def remove_tag(self, tag: str):
        """Remove a tag from user"""
        if tag in self.tags:
            self.tags.remove(tag)
            self.mark_as_modified()

    def get_full_name(self) -> str:
        """Get user's full name"""
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        elif self.first_name:
            return self.first_name
        elif self.last_name:
            return self.last_name
        else:
            return self.email.split('@')[0]

    def get_display_name(self) -> str:
        """Get display name for user"""
        if self.username:
            return self.username
        return self.get_full_name()

    def is_active(self) -> bool:
        """Check if user is active"""
        return self.status == UserStatus.ACTIVE and not self.is_account_locked()

    def is_verified(self) -> bool:
        """Check if user is fully verified"""
        return self.email_verified and (self.phone_verified if self.phone else True)

    def can_make_purchase(self) -> bool:
        """Check if user can make cannabis purchases"""
        return (
            self.is_active() and
            self.is_verified() and
            self.age_verified
        )

    def calculate_age(self) -> Optional[int]:
        """Calculate user's age"""
        if not self.date_of_birth:
            return None

        today = date.today()
        age = today.year - self.date_of_birth.year
        if today.month < self.date_of_birth.month or \
           (today.month == self.date_of_birth.month and today.day < self.date_of_birth.day):
            age -= 1

        return age

    def validate(self) -> List[str]:
        """Validate user data"""
        errors = []

        if not self.email:
            errors.append("Email is required")

        if self.email and '@' not in self.email:
            errors.append("Invalid email format")

        if self.phone and not self.phone.replace('+', '').replace('-', '').replace(' ', '').isdigit():
            errors.append("Invalid phone number")

        if self.date_of_birth:
            age = self.calculate_age()
            if age and age < 19:
                errors.append("User must be 19 or older")

        return errors