"""
Repository Interfaces for Multi-Tenancy
Following Repository Pattern
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from uuid import UUID
from datetime import date, datetime
from decimal import Decimal

from core.domain.models import (
    Tenant, Store, TenantUser, StoreUser,
    TenantSubscription, AIPersonality, StoreAIAgent,
    ProvinceTerritory, StoreCompliance, OntarioCRSA,
    TenantStatus, StoreStatus, SubscriptionTier, CRSAVerificationStatus
)


class ITenantRepository(ABC):
    """Interface for Tenant repository"""
    
    @abstractmethod
    async def create(self, tenant: Tenant) -> Tenant:
        """Create a new tenant"""
        pass
    
    @abstractmethod
    async def get_by_id(self, tenant_id: UUID) -> Optional[Tenant]:
        """Get tenant by ID"""
        pass
    
    @abstractmethod
    async def get_by_code(self, code: str) -> Optional[Tenant]:
        """Get tenant by unique code"""
        pass
    
    @abstractmethod
    async def update(self, tenant: Tenant) -> Tenant:
        """Update tenant information"""
        pass
    
    @abstractmethod
    async def delete(self, tenant_id: UUID) -> bool:
        """Soft delete a tenant"""
        pass
    
    @abstractmethod
    async def list(
        self, 
        status: Optional[TenantStatus] = None,
        subscription_tier: Optional[SubscriptionTier] = None,
        limit: int = 100, 
        offset: int = 0
    ) -> List[Tenant]:
        """List tenants with optional filters"""
        pass
    
    @abstractmethod
    async def count_stores(self, tenant_id: UUID) -> int:
        """Count stores for a tenant"""
        pass


class IStoreRepository(ABC):
    """Interface for Store repository"""
    
    @abstractmethod
    async def create(self, store: Store) -> Store:
        """Create a new store"""
        pass
    
    @abstractmethod
    async def get_by_id(self, store_id: UUID) -> Optional[Store]:
        """Get store by ID"""
        pass
    
    @abstractmethod
    async def get_by_code(self, tenant_id: UUID, store_code: str) -> Optional[Store]:
        """Get store by tenant and store code"""
        pass

    @abstractmethod
    async def get_by_store_code_only(self, store_code: str) -> Optional[Store]:
        """Get store by store code (globally unique lookup)"""
        pass

    @abstractmethod
    async def update(self, store: Store) -> Store:
        """Update store information"""
        pass
    
    @abstractmethod
    async def delete(self, store_id: UUID) -> bool:
        """Soft delete a store"""
        pass
    
    @abstractmethod
    async def list_by_tenant(
        self, 
        tenant_id: UUID,
        status: Optional[StoreStatus] = None,
        limit: int = 100, 
        offset: int = 0
    ) -> List[Store]:
        """List stores for a tenant"""
        pass
    
    @abstractmethod
    async def list_by_province(
        self, 
        province_territory_id: UUID,
        status: Optional[StoreStatus] = None,
        limit: int = 100, 
        offset: int = 0
    ) -> List[Store]:
        """List stores in a province/territory"""
        pass


class ITenantUserRepository(ABC):
    """Interface for TenantUser repository"""
    
    @abstractmethod
    async def create(self, tenant_user: TenantUser) -> TenantUser:
        """Create tenant-user association"""
        pass
    
    @abstractmethod
    async def get(self, tenant_id: UUID, user_id: UUID) -> Optional[TenantUser]:
        """Get tenant-user association"""
        pass
    
    @abstractmethod
    async def update(self, tenant_user: TenantUser) -> TenantUser:
        """Update tenant-user association"""
        pass
    
    @abstractmethod
    async def delete(self, tenant_id: UUID, user_id: UUID) -> bool:
        """Remove user from tenant"""
        pass
    
    @abstractmethod
    async def list_by_tenant(self, tenant_id: UUID) -> List[TenantUser]:
        """List users for a tenant"""
        pass
    
    @abstractmethod
    async def list_by_user(self, user_id: UUID) -> List[TenantUser]:
        """List tenants for a user"""
        pass


class IStoreUserRepository(ABC):
    """Interface for StoreUser repository"""
    
    @abstractmethod
    async def create(self, store_user: StoreUser) -> StoreUser:
        """Create store-user association"""
        pass
    
    @abstractmethod
    async def get(self, store_id: UUID, user_id: UUID) -> Optional[StoreUser]:
        """Get store-user association"""
        pass
    
    @abstractmethod
    async def update(self, store_user: StoreUser) -> StoreUser:
        """Update store-user association"""
        pass
    
    @abstractmethod
    async def delete(self, store_id: UUID, user_id: UUID) -> bool:
        """Remove user from store"""
        pass
    
    @abstractmethod
    async def list_by_store(self, store_id: UUID) -> List[StoreUser]:
        """List users for a store"""
        pass
    
    @abstractmethod
    async def list_by_user(self, user_id: UUID) -> List[StoreUser]:
        """List stores for a user"""
        pass


class ISubscriptionRepository(ABC):
    """Interface for Subscription repository"""
    
    @abstractmethod
    async def create(self, subscription: TenantSubscription) -> TenantSubscription:
        """Create subscription"""
        pass
    
    @abstractmethod
    async def get_by_tenant(self, tenant_id: UUID) -> Optional[TenantSubscription]:
        """Get active subscription for tenant"""
        pass
    
    @abstractmethod
    async def update(self, subscription: TenantSubscription) -> TenantSubscription:
        """Update subscription"""
        pass
    
    @abstractmethod
    async def list_expiring(self, days_ahead: int = 7) -> List[TenantSubscription]:
        """List subscriptions expiring soon"""
        pass


class IAIPersonalityRepository(ABC):
    """Interface for AI Personality repository"""
    
    @abstractmethod
    async def create(self, personality: AIPersonality) -> AIPersonality:
        """Create AI personality"""
        pass
    
    @abstractmethod
    async def get_by_id(self, personality_id: UUID) -> Optional[AIPersonality]:
        """Get personality by ID"""
        pass
    
    @abstractmethod
    async def update(self, personality: AIPersonality) -> AIPersonality:
        """Update personality"""
        pass
    
    @abstractmethod
    async def delete(self, personality_id: UUID) -> bool:
        """Delete personality"""
        pass
    
    @abstractmethod
    async def list_by_tenant(self, tenant_id: UUID) -> List[AIPersonality]:
        """List personalities for tenant"""
        pass
    
    @abstractmethod
    async def list_by_store(self, store_id: UUID) -> List[AIPersonality]:
        """List personalities for store"""
        pass


class IProvinceRepository(ABC):
    """Interface for Province/Territory repository"""
    
    @abstractmethod
    async def get_by_code(self, code: str) -> Optional[ProvinceTerritory]:
        """Get province/territory by code"""
        pass
    
    @abstractmethod
    async def get_by_id(self, province_id: UUID) -> Optional[ProvinceTerritory]:
        """Get province/territory by ID"""
        pass
    
    @abstractmethod
    async def list_all(self) -> List[ProvinceTerritory]:
        """List all provinces/territories"""
        pass


class IOntarioCRSARepository(ABC):
    """Interface for Ontario CRSA repository"""

    @abstractmethod
    async def get_by_id(self, crsa_id: UUID) -> Optional[OntarioCRSA]:
        """Get CRSA record by ID"""
        pass

    @abstractmethod
    async def get_by_license(self, license_number: str) -> Optional[OntarioCRSA]:
        """Get CRSA record by license number"""
        pass

    @abstractmethod
    async def search_stores(
        self,
        query: str,
        limit: int = 10,
        authorized_only: bool = True
    ) -> List[OntarioCRSA]:
        """
        Search CRSA stores by name or address using fuzzy matching

        Args:
            query: Search term (store name or address)
            limit: Maximum number of results
            authorized_only: Only return authorized stores

        Returns:
            List of matching CRSA records
        """
        pass

    @abstractmethod
    async def list_authorized(
        self,
        limit: int = 100,
        offset: int = 0
    ) -> List[OntarioCRSA]:
        """List all authorized stores"""
        pass

    @abstractmethod
    async def list_available_for_signup(
        self,
        limit: int = 100,
        offset: int = 0
    ) -> List[OntarioCRSA]:
        """List authorized stores not yet linked to a tenant"""
        pass

    @abstractmethod
    async def get_statistics(self) -> Dict[str, Any]:
        """
        Get CRSA database statistics

        Returns:
            Dictionary with counts and statistics
        """
        pass

    @abstractmethod
    async def mark_linked(self, license_number: str, tenant_id: UUID) -> OntarioCRSA:
        """
        Link a CRSA record to a tenant

        Args:
            license_number: License number to link
            tenant_id: Tenant ID to link to

        Returns:
            Updated CRSA record
        """
        pass

    @abstractmethod
    async def mark_unlinked(self, license_number: str) -> OntarioCRSA:
        """
        Unlink a CRSA record from tenant

        Args:
            license_number: License number to unlink

        Returns:
            Updated CRSA record
        """
        pass

    @abstractmethod
    async def verify_license(
        self,
        license_number: str,
        verified_by_user_id: UUID
    ) -> OntarioCRSA:
        """
        Mark a license as verified

        Args:
            license_number: License number to verify
            verified_by_user_id: User ID performing verification

        Returns:
            Updated CRSA record
        """
        pass

    @abstractmethod
    async def list_by_municipality(
        self,
        municipality: str,
        limit: int = 100,
        offset: int = 0
    ) -> List[OntarioCRSA]:
        """List stores in a specific municipality"""
        pass