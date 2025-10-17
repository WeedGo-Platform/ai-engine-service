"""
Store Service - Business Logic Layer
"""

from typing import List, Optional, Dict, Any
from uuid import UUID, uuid4
from datetime import datetime, date
from decimal import Decimal
import logging

from core.domain.models import (
    Store, StoreStatus, Address, GeoLocation,
    ProvinceTerritory
)
from core.repositories.interfaces import (
    IStoreRepository, ITenantRepository, IProvinceRepository
)
from core.services.tenant_service import TenantService

logger = logging.getLogger(__name__)


class StoreService:
    """Service for managing stores"""
    
    def __init__(
        self,
        store_repository: IStoreRepository,
        tenant_repository: ITenantRepository,
        province_repository: IProvinceRepository,
        tenant_service: TenantService
    ):
        self.store_repo = store_repository
        self.tenant_repo = tenant_repository
        self.province_repo = province_repository
        self.tenant_service = tenant_service
    
    async def create_store(
        self,
        tenant_id: UUID,
        province_code: str,
        store_code: str,
        name: str,
        address: Dict[str, Any],
        phone: Optional[str] = None,
        email: Optional[str] = None,
        hours: Optional[Dict[str, Any]] = None,
        timezone: str = "America/Toronto",
        license_number: Optional[str] = None,
        license_expiry: Optional[date] = None,
        delivery_radius_km: int = 10,
        delivery_enabled: bool = True,
        pickup_enabled: bool = True,
        kiosk_enabled: bool = False,
        pos_enabled: bool = True,
        ecommerce_enabled: bool = True,
        settings: Optional[Dict[str, Any]] = None,
        pos_integration: Optional[Dict[str, Any]] = None,
        seo_config: Optional[Dict[str, Any]] = None,
        latitude: Optional[float] = None,
        longitude: Optional[float] = None,
        delivery_zone: Optional[Dict[str, Any]] = None,
        delivery_zone_stats: Optional[Dict[str, Any]] = None
    ) -> Store:
        """Create a new store"""
        try:
            # Validate tenant exists and can add stores
            tenant = await self.tenant_repo.get_by_id(tenant_id)
            if not tenant:
                raise ValueError(f"Tenant {tenant_id} not found")
            
            can_add = await self.tenant_service.can_add_store(tenant_id)
            if not can_add:
                raise ValueError(f"Tenant has reached store limit for {tenant.subscription_tier.value} tier")
            
            # Get province/territory
            province = await self.province_repo.get_by_code(province_code)
            if not province:
                raise ValueError(f"Province/Territory '{province_code}' not found")
            
            # Validate unique store code within tenant
            existing = await self.store_repo.get_by_code(tenant_id, store_code)
            if existing:
                raise ValueError(f"Store with code '{store_code}' already exists for this tenant")
            
            # Create address object
            address_obj = Address(
                street=address.get('street', ''),
                city=address.get('city', ''),
                province=address.get('province', province_code),
                postal_code=address.get('postal_code', ''),
                country=address.get('country', 'Canada')
            )
            
            # Create location if coordinates provided
            location = None
            if latitude is not None and longitude is not None:
                location = GeoLocation(
                    latitude=Decimal(str(latitude)),
                    longitude=Decimal(str(longitude))
                )
            
            # Set default hours if not provided
            if not hours:
                hours = self._get_default_hours()
            
            # Create store entity
            store = Store(
                id=uuid4(),
                tenant_id=tenant_id,
                province_territory_id=province.id,
                store_code=store_code,
                name=name,
                address=address_obj,
                phone=phone,
                email=email,
                hours=hours,
                timezone=timezone,
                license_number=license_number,
                license_expiry=license_expiry,
                tax_rate=province.tax_rate,  # Use province tax rate
                delivery_radius_km=delivery_radius_km,
                delivery_enabled=delivery_enabled and province.delivery_allowed,
                pickup_enabled=pickup_enabled and province.pickup_allowed,
                kiosk_enabled=kiosk_enabled,
                pos_enabled=pos_enabled,
                ecommerce_enabled=ecommerce_enabled,
                status=StoreStatus.ACTIVE,
                settings=settings or {},
                pos_integration=pos_integration or {},
                seo_config=seo_config or self._get_default_seo_config(name),
                location=location,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )

            # Add delivery zone fields if provided
            if delivery_zone:
                store.delivery_zone = delivery_zone
            if delivery_zone_stats:
                store.delivery_zone_stats = delivery_zone_stats

            # Save store
            saved_store = await self.store_repo.create(store)
            
            logger.info(f"Created store '{name}' (code: {store_code}) for tenant {tenant_id}")
            return saved_store
            
        except Exception as e:
            logger.error(f"Error creating store: {e}")
            raise
    
    async def get_store(self, store_id: UUID) -> Optional[Store]:
        """Get store by ID"""
        return await self.store_repo.get_by_id(store_id)
    
    async def get_store_by_code(self, tenant_id: UUID, store_code: str) -> Optional[Store]:
        """Get store by tenant and code"""
        return await self.store_repo.get_by_code(tenant_id, store_code)

    async def get_store_by_code_only(self, store_code: str) -> Optional[Store]:
        """Get store by store code (globally unique lookup)"""
        return await self.store_repo.get_by_store_code_only(store_code)

    async def update_store(
        self,
        store_id: UUID,
        name: Optional[str] = None,
        address: Optional[Dict[str, Any]] = None,
        phone: Optional[str] = None,
        email: Optional[str] = None,
        hours: Optional[Dict[str, Any]] = None,
        timezone: Optional[str] = None,
        license_number: Optional[str] = None,
        license_expiry: Optional[date] = None,
        delivery_radius_km: Optional[int] = None,
        delivery_enabled: Optional[bool] = None,
        pickup_enabled: Optional[bool] = None,
        kiosk_enabled: Optional[bool] = None,
        pos_enabled: Optional[bool] = None,
        ecommerce_enabled: Optional[bool] = None,
        settings: Optional[Dict[str, Any]] = None,
        pos_integration: Optional[Dict[str, Any]] = None,
        seo_config: Optional[Dict[str, Any]] = None,
        latitude: Optional[float] = None,
        longitude: Optional[float] = None,
        delivery_zone: Optional[Dict[str, Any]] = None,
        delivery_zone_stats: Optional[Dict[str, Any]] = None
    ) -> Store:
        """Update store information"""
        try:
            store = await self.store_repo.get_by_id(store_id)
            if not store:
                raise ValueError(f"Store {store_id} not found")
            
            # Update fields if provided
            if name is not None:
                store.name = name
            if address is not None:
                store.address = Address(
                    street=address.get('street', ''),
                    city=address.get('city', ''),
                    province=address.get('province', store.address.province if store.address else ''),
                    postal_code=address.get('postal_code', ''),
                    country=address.get('country', 'Canada')
                )
            if phone is not None:
                store.phone = phone
            if email is not None:
                store.email = email
            if hours is not None:
                store.hours = hours
            if timezone is not None:
                store.timezone = timezone
            if license_number is not None:
                store.license_number = license_number
            if license_expiry is not None:
                store.license_expiry = license_expiry
            if delivery_radius_km is not None:
                store.delivery_radius_km = delivery_radius_km
            if delivery_enabled is not None:
                store.delivery_enabled = delivery_enabled
            if pickup_enabled is not None:
                store.pickup_enabled = pickup_enabled
            if kiosk_enabled is not None:
                store.kiosk_enabled = kiosk_enabled
            if pos_enabled is not None:
                store.pos_enabled = pos_enabled
            if ecommerce_enabled is not None:
                store.ecommerce_enabled = ecommerce_enabled
            if settings is not None:
                store.settings = settings
            if pos_integration is not None:
                store.pos_integration = pos_integration
            if seo_config is not None:
                store.seo_config = seo_config
            if latitude is not None and longitude is not None:
                store.location = GeoLocation(
                    latitude=Decimal(str(latitude)),
                    longitude=Decimal(str(longitude))
                )
            if delivery_zone is not None:
                store.delivery_zone = delivery_zone
            if delivery_zone_stats is not None:
                store.delivery_zone_stats = delivery_zone_stats

            return await self.store_repo.update(store)
            
        except Exception as e:
            logger.error(f"Error updating store {store_id}: {e}")
            raise
    
    async def suspend_store(self, store_id: UUID, reason: str) -> Store:
        """Suspend a store"""
        try:
            store = await self.store_repo.get_by_id(store_id)
            if not store:
                raise ValueError(f"Store {store_id} not found")
            
            store.status = StoreStatus.SUSPENDED
            store.settings['suspension_reason'] = reason
            store.settings['suspended_at'] = datetime.utcnow().isoformat()
            
            updated_store = await self.store_repo.update(store)
            
            logger.warning(f"Suspended store {store_id}: {reason}")
            return updated_store
            
        except Exception as e:
            logger.error(f"Error suspending store {store_id}: {e}")
            raise
    
    async def reactivate_store(self, store_id: UUID) -> Store:
        """Reactivate a suspended store"""
        try:
            store = await self.store_repo.get_by_id(store_id)
            if not store:
                raise ValueError(f"Store {store_id} not found")
            
            if store.status != StoreStatus.SUSPENDED:
                raise ValueError(f"Store {store_id} is not suspended")
            
            # Check license validity
            if not store.is_license_valid():
                raise ValueError(f"Store license has expired. Please update license before reactivating.")
            
            store.status = StoreStatus.ACTIVE
            store.settings['reactivated_at'] = datetime.utcnow().isoformat()
            
            updated_store = await self.store_repo.update(store)
            
            logger.info(f"Reactivated store {store_id}")
            return updated_store
            
        except Exception as e:
            logger.error(f"Error reactivating store {store_id}: {e}")
            raise
    
    async def close_store(self, store_id: UUID) -> Store:
        """Permanently close a store"""
        try:
            store = await self.store_repo.get_by_id(store_id)
            if not store:
                raise ValueError(f"Store {store_id} not found")
            
            store.status = StoreStatus.INACTIVE
            store.settings['closed_at'] = datetime.utcnow().isoformat()
            
            updated_store = await self.store_repo.update(store)
            
            logger.info(f"Closed store {store_id}")
            return updated_store
            
        except Exception as e:
            logger.error(f"Error closing store {store_id}: {e}")
            raise
    
    async def list_stores_by_tenant(
        self,
        tenant_id: UUID,
        status: Optional[StoreStatus] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Store]:
        """List stores for a tenant"""
        return await self.store_repo.list_by_tenant(
            tenant_id=tenant_id,
            status=status,
            limit=limit,
            offset=offset
        )
    
    async def list_stores_by_province(
        self,
        province_territory_id: UUID,
        status: Optional[StoreStatus] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Store]:
        """List stores in a province/territory"""
        return await self.store_repo.list_by_province(
            province_territory_id=province_territory_id,
            status=status,
            limit=limit,
            offset=offset
        )
    
    async def validate_license(self, store_id: UUID) -> bool:
        """Validate store license"""
        try:
            store = await self.store_repo.get_by_id(store_id)
            if not store:
                return False
            
            if not store.is_license_valid():
                # Auto-suspend if license expired
                await self.suspend_store(store_id, "License expired")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error validating license for store {store_id}: {e}")
            return False
    
    def _get_default_hours(self) -> Dict[str, Any]:
        """Get default store hours"""
        return {
            "monday": {"open": "09:00", "close": "21:00"},
            "tuesday": {"open": "09:00", "close": "21:00"},
            "wednesday": {"open": "09:00", "close": "21:00"},
            "thursday": {"open": "09:00", "close": "21:00"},
            "friday": {"open": "09:00", "close": "22:00"},
            "saturday": {"open": "10:00", "close": "22:00"},
            "sunday": {"open": "11:00", "close": "20:00"}
        }
    
    def _get_default_seo_config(self, store_name: str) -> Dict[str, Any]:
        """Get default SEO configuration"""
        return {
            "title": f"{store_name} - Cannabis Store",
            "description": f"Shop premium cannabis products at {store_name}. Licensed dispensary offering flower, edibles, concentrates and more.",
            "keywords": ["cannabis", "dispensary", "marijuana", "weed", "shop"],
            "og_image": None,
            "structured_data": {
                "@type": "Store",
                "name": store_name
            }
        }