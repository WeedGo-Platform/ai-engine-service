"""
TenantUser Entity
Following DDD Architecture Document Section 2.1
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List, Dict, Any
from uuid import UUID, uuid4
from enum import Enum

from ....shared.domain_base import Entity, BusinessRuleViolation


class TenantUserRole(str, Enum):
    """Tenant-level user roles"""
    OWNER = "owner"
    ADMIN = "admin"
    MANAGER = "manager"
    STAFF = "staff"
    VIEWER = "viewer"


class TenantUserStatus(str, Enum):
    """Tenant user status"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    INVITED = "invited"
    SUSPENDED = "suspended"


@dataclass
class TenantUser(Entity):
    """
    TenantUser Entity - Manages user access at tenant level
    As defined in DDD_ARCHITECTURE_REFACTORING.md Section 2.1
    """
    tenant_id: UUID = field(default_factory=uuid4)
    user_id: UUID = field(default_factory=uuid4)  # Reference to Identity & Access Context
    role: TenantUserRole = TenantUserRole.STAFF
    status: TenantUserStatus = TenantUserStatus.ACTIVE

    # Access Control
    store_ids: List[UUID] = field(default_factory=list)  # Stores this user can access
    permissions: List[str] = field(default_factory=list)  # Tenant-level permissions

    # User Details (cached from Identity context)
    email: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone: Optional[str] = None

    # Employment Information
    employee_id: Optional[str] = None
    department: Optional[str] = None
    position: Optional[str] = None
    hire_date: Optional[datetime] = None

    # Invitation Details
    invited_by: Optional[UUID] = None
    invited_at: Optional[datetime] = None
    invitation_accepted_at: Optional[datetime] = None

    # Activity Tracking
    last_login_at: Optional[datetime] = None
    login_count: int = 0
    last_activity_at: Optional[datetime] = None

    # Settings
    preferences: Dict[str, Any] = field(default_factory=dict)
    notification_settings: Dict[str, bool] = field(default_factory=dict)

    @classmethod
    def create(
        cls,
        tenant_id: UUID,
        user_id: UUID,
        email: str,
        role: TenantUserRole = TenantUserRole.STAFF,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None
    ) -> 'TenantUser':
        """Factory method to create a new tenant user"""
        tenant_user = cls(
            tenant_id=tenant_id,
            user_id=user_id,
            email=email,
            role=role,
            first_name=first_name,
            last_name=last_name,
            status=TenantUserStatus.INVITED,
            invited_at=datetime.utcnow()
        )

        # Set default notification settings
        tenant_user.notification_settings = {
            'email_notifications': True,
            'sms_notifications': False,
            'order_updates': True,
            'inventory_alerts': role in [TenantUserRole.OWNER, TenantUserRole.ADMIN, TenantUserRole.MANAGER],
            'staff_updates': role in [TenantUserRole.OWNER, TenantUserRole.ADMIN],
            'system_alerts': role in [TenantUserRole.OWNER, TenantUserRole.ADMIN]
        }

        return tenant_user

    def has_permission(self, permission: str) -> bool:
        """Check if user has specific permission"""
        # Owners have all permissions
        if self.role == TenantUserRole.OWNER:
            return True

        # Check role-based permissions
        role_permissions = self._get_role_permissions()
        if permission in role_permissions:
            return True

        # Check explicit permissions
        return permission in self.permissions

    def _get_role_permissions(self) -> List[str]:
        """Get default permissions for role"""
        permissions_map = {
            TenantUserRole.OWNER: ['*'],  # All permissions
            TenantUserRole.ADMIN: [
                'manage_stores', 'manage_users', 'manage_inventory',
                'manage_orders', 'view_reports', 'manage_settings'
            ],
            TenantUserRole.MANAGER: [
                'manage_inventory', 'manage_orders', 'view_reports',
                'manage_staff_schedule'
            ],
            TenantUserRole.STAFF: [
                'view_inventory', 'create_orders', 'update_orders',
                'view_own_schedule'
            ],
            TenantUserRole.VIEWER: [
                'view_inventory', 'view_orders', 'view_reports'
            ]
        }
        return permissions_map.get(self.role, [])

    def can_access_store(self, store_id: UUID) -> bool:
        """Check if user can access a specific store"""
        # Owners and admins can access all stores
        if self.role in [TenantUserRole.OWNER, TenantUserRole.ADMIN]:
            return True

        # Others need explicit store access
        return store_id in self.store_ids

    def grant_store_access(self, store_id: UUID):
        """Grant access to a store"""
        if store_id not in self.store_ids:
            self.store_ids.append(store_id)
            self.mark_as_modified()

    def revoke_store_access(self, store_id: UUID):
        """Revoke access to a store"""
        if store_id in self.store_ids:
            self.store_ids.remove(store_id)
            self.mark_as_modified()

    def grant_permission(self, permission: str):
        """Grant additional permission"""
        if permission not in self.permissions:
            self.permissions.append(permission)
            self.mark_as_modified()

    def revoke_permission(self, permission: str):
        """Revoke a permission"""
        if permission in self.permissions:
            self.permissions.remove(permission)
            self.mark_as_modified()

    def update_role(self, new_role: TenantUserRole):
        """Update user role"""
        if self.role == TenantUserRole.OWNER and new_role != TenantUserRole.OWNER:
            raise BusinessRuleViolation("Cannot change owner role without transferring ownership")

        self.role = new_role
        self.mark_as_modified()

    def activate(self):
        """Activate the user"""
        if self.status == TenantUserStatus.ACTIVE:
            raise BusinessRuleViolation("User is already active")

        if self.status == TenantUserStatus.INVITED:
            self.invitation_accepted_at = datetime.utcnow()

        self.status = TenantUserStatus.ACTIVE
        self.mark_as_modified()

    def deactivate(self):
        """Deactivate the user"""
        if self.status == TenantUserStatus.INACTIVE:
            raise BusinessRuleViolation("User is already inactive")

        if self.role == TenantUserRole.OWNER:
            raise BusinessRuleViolation("Cannot deactivate owner account")

        self.status = TenantUserStatus.INACTIVE
        self.mark_as_modified()

    def suspend(self, reason: Optional[str] = None):
        """Suspend the user"""
        if self.status == TenantUserStatus.SUSPENDED:
            raise BusinessRuleViolation("User is already suspended")

        if self.role == TenantUserRole.OWNER:
            raise BusinessRuleViolation("Cannot suspend owner account")

        self.status = TenantUserStatus.SUSPENDED

        if reason:
            self.preferences['suspension_reason'] = reason
            self.preferences['suspension_date'] = datetime.utcnow().isoformat()

        self.mark_as_modified()

    def record_login(self):
        """Record user login"""
        self.last_login_at = datetime.utcnow()
        self.login_count += 1
        self.last_activity_at = datetime.utcnow()
        self.mark_as_modified()

    def record_activity(self):
        """Record user activity"""
        self.last_activity_at = datetime.utcnow()
        self.mark_as_modified()

    def update_preferences(self, preferences: Dict[str, Any]):
        """Update user preferences"""
        self.preferences.update(preferences)
        self.mark_as_modified()

    def update_notification_settings(self, settings: Dict[str, bool]):
        """Update notification settings"""
        self.notification_settings.update(settings)
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
            return self.email or "Unknown User"

    def is_active(self) -> bool:
        """Check if user is active"""
        return self.status == TenantUserStatus.ACTIVE

    def validate(self) -> List[str]:
        """Validate tenant user data"""
        errors = []

        if not self.tenant_id:
            errors.append("Tenant ID is required")

        if not self.user_id:
            errors.append("User ID is required")

        if not self.email:
            errors.append("Email is required")

        if self.email and '@' not in self.email:
            errors.append("Invalid email format")

        return errors