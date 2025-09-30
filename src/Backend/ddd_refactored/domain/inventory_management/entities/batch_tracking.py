"""
BatchTracking Entity
Following DDD Architecture Document Section 2.4
"""

from dataclasses import dataclass, field
from datetime import datetime, date
from decimal import Decimal
from typing import Optional, List, Dict, Any
from uuid import UUID, uuid4

from ....shared.domain_base import Entity, BusinessRuleViolation
from ..value_objects import GTIN


@dataclass
class BatchTracking(Entity):
    """
    BatchTracking Entity - Track inventory by batch/lot numbers
    As defined in DDD_ARCHITECTURE_REFACTORING.md Section 2.4
    """
    # Identifiers
    store_id: UUID = field(default_factory=uuid4)
    sku: str = ""
    batch_lot: str = ""  # Lot/batch number

    # Batch Information
    gtin: Optional[str] = None
    supplier_batch: Optional[str] = None  # Supplier's batch number
    production_date: Optional[date] = None
    expiry_date: Optional[date] = None

    # Quantities
    quantity_received: int = 0
    quantity_remaining: int = 0
    quantity_damaged: int = 0
    quantity_expired: int = 0

    # Cost
    unit_cost: Decimal = Decimal("0")
    total_cost: Decimal = Decimal("0")

    # Receiving Information
    received_date: datetime = field(default_factory=datetime.utcnow)
    purchase_order_id: Optional[UUID] = None
    supplier_id: Optional[UUID] = None
    received_by: Optional[UUID] = None

    # Location
    location_id: Optional[UUID] = None  # Current shelf location

    # Quality Control
    quality_check_status: str = "pending"  # pending, passed, failed
    quality_check_date: Optional[datetime] = None
    quality_check_by: Optional[UUID] = None
    quality_notes: Optional[str] = None

    # Cannabis Specific (for OCS products)
    thc_percentage: Optional[Decimal] = None
    cbd_percentage: Optional[Decimal] = None
    packaged_date: Optional[date] = None

    # Status
    is_active: bool = True
    is_quarantined: bool = False
    quarantine_reason: Optional[str] = None

    # Metadata
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def create(
        cls,
        store_id: UUID,
        sku: str,
        batch_lot: str,
        quantity_received: int,
        unit_cost: Decimal,
        purchase_order_id: Optional[UUID] = None,
        supplier_id: Optional[UUID] = None
    ) -> 'BatchTracking':
        """Factory method to create new batch"""
        if not batch_lot:
            raise BusinessRuleViolation("Batch/lot number is required")
        if quantity_received <= 0:
            raise BusinessRuleViolation("Received quantity must be positive")
        if unit_cost < 0:
            raise BusinessRuleViolation("Unit cost cannot be negative")

        batch = cls(
            store_id=store_id,
            sku=sku,
            batch_lot=batch_lot,
            quantity_received=quantity_received,
            quantity_remaining=quantity_received,
            unit_cost=unit_cost,
            total_cost=unit_cost * Decimal(quantity_received),
            purchase_order_id=purchase_order_id,
            supplier_id=supplier_id
        )

        return batch

    def set_gtin(self, gtin_string: str):
        """Set and validate GTIN"""
        try:
            gtin_obj = GTIN.from_string(gtin_string)
            self.gtin = gtin_obj.format_for_barcode()
        except ValueError as e:
            raise BusinessRuleViolation(f"Invalid GTIN: {e}")
        self.mark_as_modified()

    def set_dates(
        self,
        production_date: Optional[date] = None,
        expiry_date: Optional[date] = None,
        packaged_date: Optional[date] = None
    ):
        """Set batch dates"""
        if production_date:
            self.production_date = production_date

        if expiry_date:
            if production_date and expiry_date <= production_date:
                raise BusinessRuleViolation("Expiry date must be after production date")
            self.expiry_date = expiry_date

        if packaged_date:
            if production_date and packaged_date < production_date:
                raise BusinessRuleViolation("Packaged date cannot be before production date")
            self.packaged_date = packaged_date

        self.mark_as_modified()

    def set_cannabinoid_content(
        self,
        thc_percentage: Optional[Decimal] = None,
        cbd_percentage: Optional[Decimal] = None
    ):
        """Set cannabinoid content for cannabis products"""
        if thc_percentage is not None:
            if thc_percentage < 0 or thc_percentage > 100:
                raise BusinessRuleViolation("THC percentage must be between 0 and 100")
            self.thc_percentage = thc_percentage

        if cbd_percentage is not None:
            if cbd_percentage < 0 or cbd_percentage > 100:
                raise BusinessRuleViolation("CBD percentage must be between 0 and 100")
            self.cbd_percentage = cbd_percentage

        self.mark_as_modified()

    def consume(self, quantity: int) -> bool:
        """Consume quantity from batch"""
        if quantity <= 0:
            raise BusinessRuleViolation("Consume quantity must be positive")

        if quantity > self.quantity_remaining:
            return False

        self.quantity_remaining -= quantity
        self.mark_as_modified()
        return True

    def damage(self, quantity: int, reason: Optional[str] = None):
        """Record damaged items"""
        if quantity <= 0:
            raise BusinessRuleViolation("Damage quantity must be positive")

        if quantity > self.quantity_remaining:
            raise BusinessRuleViolation("Cannot damage more than remaining quantity")

        self.quantity_remaining -= quantity
        self.quantity_damaged += quantity

        if reason:
            self.metadata['last_damage_reason'] = reason
            self.metadata['last_damage_date'] = datetime.utcnow().isoformat()

        self.mark_as_modified()

    def expire(self, quantity: Optional[int] = None):
        """Mark items as expired"""
        if quantity is None:
            # Expire all remaining
            quantity = self.quantity_remaining

        if quantity <= 0:
            raise BusinessRuleViolation("Expire quantity must be positive")

        if quantity > self.quantity_remaining:
            raise BusinessRuleViolation("Cannot expire more than remaining quantity")

        self.quantity_remaining -= quantity
        self.quantity_expired += quantity
        self.mark_as_modified()

    def perform_quality_check(
        self,
        status: str,
        checked_by: UUID,
        notes: Optional[str] = None
    ):
        """Perform quality control check"""
        if status not in ['passed', 'failed']:
            raise BusinessRuleViolation("Status must be 'passed' or 'failed'")

        self.quality_check_status = status
        self.quality_check_date = datetime.utcnow()
        self.quality_check_by = checked_by
        self.quality_notes = notes

        if status == 'failed':
            self.quarantine("Failed quality check")

        self.mark_as_modified()

    def quarantine(self, reason: str):
        """Quarantine the batch"""
        self.is_quarantined = True
        self.quarantine_reason = reason
        self.mark_as_modified()

    def release_from_quarantine(self):
        """Release batch from quarantine"""
        if not self.is_quarantined:
            raise BusinessRuleViolation("Batch is not quarantined")

        self.is_quarantined = False
        self.quarantine_reason = None
        self.mark_as_modified()

    def move_to_location(self, location_id: UUID):
        """Move batch to new location"""
        self.location_id = location_id
        self.mark_as_modified()

    def is_expired(self) -> bool:
        """Check if batch is expired"""
        if not self.expiry_date:
            return False
        return date.today() > self.expiry_date

    def days_until_expiry(self) -> Optional[int]:
        """Calculate days until expiry"""
        if not self.expiry_date:
            return None

        delta = self.expiry_date - date.today()
        return delta.days

    def is_near_expiry(self, days_threshold: int = 30) -> bool:
        """Check if batch is near expiry"""
        days_left = self.days_until_expiry()
        if days_left is None:
            return False
        return 0 < days_left <= days_threshold

    def get_age_days(self) -> int:
        """Get age of batch in days"""
        if self.production_date:
            delta = date.today() - self.production_date
            return delta.days
        else:
            delta = datetime.utcnow() - self.received_date
            return delta.days

    def get_utilization_rate(self) -> Decimal:
        """Calculate utilization rate"""
        if self.quantity_received == 0:
            return Decimal("0")

        used = self.quantity_received - self.quantity_remaining
        rate = (Decimal(used) / Decimal(self.quantity_received)) * 100
        return rate.quantize(Decimal("0.01"))

    def get_wastage_rate(self) -> Decimal:
        """Calculate wastage rate (damaged + expired)"""
        if self.quantity_received == 0:
            return Decimal("0")

        wasted = self.quantity_damaged + self.quantity_expired
        rate = (Decimal(wasted) / Decimal(self.quantity_received)) * 100
        return rate.quantize(Decimal("0.01"))

    def get_remaining_value(self) -> Decimal:
        """Calculate value of remaining inventory"""
        return self.unit_cost * Decimal(self.quantity_remaining)

    def can_allocate(self, quantity: int) -> bool:
        """Check if quantity can be allocated from batch"""
        return (
            not self.is_quarantined and
            not self.is_expired() and
            quantity <= self.quantity_remaining and
            self.quality_check_status in ['pending', 'passed']
        )

    def validate(self) -> List[str]:
        """Validate batch data"""
        errors = []

        if not self.batch_lot:
            errors.append("Batch/lot number is required")

        if not self.sku:
            errors.append("SKU is required")

        if self.quantity_received < 0:
            errors.append("Received quantity cannot be negative")

        if self.quantity_remaining < 0:
            errors.append("Remaining quantity cannot be negative")

        if self.quantity_remaining > self.quantity_received:
            errors.append("Remaining quantity cannot exceed received quantity")

        if self.unit_cost < 0:
            errors.append("Unit cost cannot be negative")

        if self.production_date and self.expiry_date:
            if self.expiry_date <= self.production_date:
                errors.append("Expiry date must be after production date")

        if self.thc_percentage is not None:
            if self.thc_percentage < 0 or self.thc_percentage > 100:
                errors.append("THC percentage must be between 0 and 100")

        if self.cbd_percentage is not None:
            if self.cbd_percentage < 0 or self.cbd_percentage > 100:
                errors.append("CBD percentage must be between 0 and 100")

        return errors