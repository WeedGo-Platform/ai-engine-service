"""
Permission Value Object
Following DDD Architecture Document Section 2.2
"""

from dataclasses import dataclass
from typing import Optional, List
from enum import Enum

from ....shared.domain_base import ValueObject


class PermissionScope(str, Enum):
    """Permission scope levels"""
    SYSTEM = "system"
    TENANT = "tenant"
    STORE = "store"
    USER = "user"


class ResourceType(str, Enum):
    """Resource types for permissions"""
    ALL = "*"
    TENANT = "tenant"
    STORE = "store"
    USER = "user"
    PRODUCT = "product"
    INVENTORY = "inventory"
    ORDER = "order"
    PAYMENT = "payment"
    DELIVERY = "delivery"
    CUSTOMER = "customer"
    REPORT = "report"
    SETTINGS = "settings"
    API = "api"


class Action(str, Enum):
    """Actions that can be performed"""
    ALL = "*"
    CREATE = "create"
    READ = "read"
    UPDATE = "update"
    DELETE = "delete"
    EXECUTE = "execute"
    APPROVE = "approve"
    REJECT = "reject"
    EXPORT = "export"
    IMPORT = "import"


@dataclass(frozen=True)
class Permission(ValueObject):
    """
    Permission value object
    As defined in DDD_ARCHITECTURE_REFACTORING.md Section 2.2

    Format: scope:resource:action
    Examples:
    - system:*:* (full system access)
    - tenant:store:create (create stores in tenant)
    - store:order:read (read orders in store)
    """
    scope: PermissionScope
    resource: ResourceType
    action: Action
    conditions: Optional[dict] = None  # Additional conditions (e.g., time-based, IP-based)

    def __str__(self) -> str:
        """String representation of permission"""
        return f"{self.scope.value}:{self.resource.value}:{self.action.value}"

    @classmethod
    def from_string(cls, permission_string: str) -> 'Permission':
        """Create Permission from string representation"""
        parts = permission_string.split(':')
        if len(parts) != 3:
            raise ValueError(f"Invalid permission format: {permission_string}")

        try:
            scope = PermissionScope(parts[0])
            resource = ResourceType(parts[1])
            action = Action(parts[2])
        except ValueError as e:
            raise ValueError(f"Invalid permission components: {permission_string}") from e

        return cls(scope=scope, resource=resource, action=action)

    def matches(self, required_permission: 'Permission') -> bool:
        """Check if this permission matches or supersedes the required permission"""
        # Wildcard matching
        if self.action == Action.ALL or self.action == required_permission.action:
            action_match = True
        else:
            action_match = False

        if self.resource == ResourceType.ALL or self.resource == required_permission.resource:
            resource_match = True
        else:
            resource_match = False

        # Scope hierarchy: system > tenant > store > user
        scope_hierarchy = {
            PermissionScope.SYSTEM: 4,
            PermissionScope.TENANT: 3,
            PermissionScope.STORE: 2,
            PermissionScope.USER: 1
        }

        scope_match = scope_hierarchy.get(self.scope, 0) >= scope_hierarchy.get(required_permission.scope, 0)

        return scope_match and resource_match and action_match

    def is_system_permission(self) -> bool:
        """Check if this is a system-level permission"""
        return self.scope == PermissionScope.SYSTEM

    def is_tenant_permission(self) -> bool:
        """Check if this is a tenant-level permission"""
        return self.scope == PermissionScope.TENANT

    def is_store_permission(self) -> bool:
        """Check if this is a store-level permission"""
        return self.scope == PermissionScope.STORE

    def is_read_only(self) -> bool:
        """Check if this permission only allows read access"""
        return self.action == Action.READ

    def is_full_access(self) -> bool:
        """Check if this permission grants full access"""
        return (
            self.scope == PermissionScope.SYSTEM and
            self.resource == ResourceType.ALL and
            self.action == Action.ALL
        )

    def to_dict(self) -> dict:
        """Convert to dictionary representation"""
        return {
            'scope': self.scope.value,
            'resource': self.resource.value,
            'action': self.action.value,
            'conditions': self.conditions,
            'string': str(self)
        }


@dataclass(frozen=True)
class PermissionSet(ValueObject):
    """
    Collection of permissions
    """
    permissions: List[Permission]

    def has_permission(self, required: Permission) -> bool:
        """Check if permission set contains the required permission"""
        return any(perm.matches(required) for perm in self.permissions)

    def has_any_permission(self, required_permissions: List[Permission]) -> bool:
        """Check if permission set contains any of the required permissions"""
        return any(self.has_permission(perm) for perm in required_permissions)

    def has_all_permissions(self, required_permissions: List[Permission]) -> bool:
        """Check if permission set contains all required permissions"""
        return all(self.has_permission(perm) for perm in required_permissions)

    def add_permission(self, permission: Permission) -> 'PermissionSet':
        """Create new PermissionSet with additional permission"""
        if permission not in self.permissions:
            return PermissionSet(permissions=self.permissions + [permission])
        return self

    def remove_permission(self, permission: Permission) -> 'PermissionSet':
        """Create new PermissionSet without specified permission"""
        return PermissionSet(
            permissions=[p for p in self.permissions if p != permission]
        )

    def merge(self, other: 'PermissionSet') -> 'PermissionSet':
        """Merge with another permission set"""
        unique_perms = list(set(self.permissions + other.permissions))
        return PermissionSet(permissions=unique_perms)

    @classmethod
    def from_strings(cls, permission_strings: List[str]) -> 'PermissionSet':
        """Create PermissionSet from list of permission strings"""
        permissions = [Permission.from_string(s) for s in permission_strings]
        return cls(permissions=permissions)

    def to_strings(self) -> List[str]:
        """Convert to list of permission strings"""
        return [str(p) for p in self.permissions]


# Predefined permission sets for common roles
class PredefinedPermissions:
    """Common permission sets for standard roles"""

    SUPER_ADMIN = PermissionSet.from_strings([
        "system:*:*"
    ])

    TENANT_ADMIN = PermissionSet.from_strings([
        "tenant:*:*",
        "store:*:*",
        "user:*:read"
    ])

    STORE_MANAGER = PermissionSet.from_strings([
        "store:*:*",
        "user:user:read",
        "tenant:tenant:read"
    ])

    BUDTENDER = PermissionSet.from_strings([
        "store:product:read",
        "store:inventory:read",
        "store:order:create",
        "store:order:read",
        "store:order:update",
        "store:customer:read",
        "store:customer:create"
    ])

    CUSTOMER = PermissionSet.from_strings([
        "user:order:create",
        "user:order:read",
        "user:payment:create",
        "user:product:read"
    ])

    VIEWER = PermissionSet.from_strings([
        "store:product:read",
        "store:order:read",
        "store:report:read"
    ])