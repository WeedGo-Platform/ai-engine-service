"""
StoreContext Value Object
Represents the current store selection context for multi-store operations
"""

from dataclasses import dataclass
from typing import Optional
from uuid import UUID

from ....shared.domain_base import ValueObject


@dataclass(frozen=True)
class StoreContext(ValueObject):
    """
    StoreContext Value Object - Represents user's current store selection

    This value object encapsulates the store context that determines which store's
    data should be displayed and operated upon. It's primarily used by the
    application layer to filter queries and scope operations.

    Usage in Application Layer:
    - Store selection modal updates this context
    - All store-scoped queries filter by current_store_id
    - Display "No Store Selected" message when current_store_id is None
    """
    user_id: UUID
    current_store_id: Optional[UUID] = None
    current_tenant_id: Optional[UUID] = None
    store_name: Optional[str] = None
    tenant_name: Optional[str] = None

    def has_store_selected(self) -> bool:
        """Check if a store is currently selected"""
        return self.current_store_id is not None

    def has_tenant_selected(self) -> bool:
        """Check if a tenant is currently selected"""
        return self.current_tenant_id is not None

    def is_multi_store_context(self) -> bool:
        """Check if user has access to multiple stores (tenant selected but not specific store)"""
        return self.has_tenant_selected() and not self.has_store_selected()

    def select_store(self, store_id: UUID, store_name: str, tenant_id: UUID, tenant_name: str) -> 'StoreContext':
        """Create new context with selected store"""
        return StoreContext(
            user_id=self.user_id,
            current_store_id=store_id,
            current_tenant_id=tenant_id,
            store_name=store_name,
            tenant_name=tenant_name
        )

    def clear_store(self) -> 'StoreContext':
        """Create new context with cleared store selection"""
        return StoreContext(
            user_id=self.user_id,
            current_store_id=None,
            current_tenant_id=self.current_tenant_id,
            store_name=None,
            tenant_name=self.tenant_name
        )

    def select_tenant(self, tenant_id: UUID, tenant_name: str) -> 'StoreContext':
        """Create new context with selected tenant (clears store)"""
        return StoreContext(
            user_id=self.user_id,
            current_store_id=None,
            current_tenant_id=tenant_id,
            store_name=None,
            tenant_name=tenant_name
        )

    def get_display_text(self) -> str:
        """Get human-readable display text for current context"""
        if not self.has_store_selected():
            if self.has_tenant_selected():
                return f"All Stores - {self.tenant_name}"
            return "No Store Selected"

        return f"{self.store_name} ({self.tenant_name})"

    def to_dict(self) -> dict:
        """Convert to dictionary representation"""
        return {
            'user_id': str(self.user_id),
            'current_store_id': str(self.current_store_id) if self.current_store_id else None,
            'current_tenant_id': str(self.current_tenant_id) if self.current_tenant_id else None,
            'store_name': self.store_name,
            'tenant_name': self.tenant_name,
            'has_store_selected': self.has_store_selected(),
            'display_text': self.get_display_text()
        }
