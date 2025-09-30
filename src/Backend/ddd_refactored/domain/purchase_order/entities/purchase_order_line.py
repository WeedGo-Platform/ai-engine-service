"""
PurchaseOrderLine Entity
Following DDD Architecture Document Section 2.5
"""

from dataclasses import dataclass, field
from datetime import datetime, date
from decimal import Decimal
from typing import Optional, Dict, Any
from uuid import UUID, uuid4

from ....shared.domain_base import Entity, BusinessRuleViolation
from ..value_objects import ReceivingStatus


@dataclass
class PurchaseOrderLine(Entity):
    """
    PurchaseOrderLine Entity - Line items in purchase orders
    As defined in DDD_ARCHITECTURE_REFACTORING.md Section 2.5
    """
    # Identifiers
    purchase_order_id: UUID = field(default_factory=uuid4)
    line_number: int = 0
    sku: str = ""
    product_id: Optional[UUID] = None

    # Product Information
    product_name: str = ""
    product_description: Optional[str] = None
    supplier_sku: Optional[str] = None  # Supplier's product code
    barcode: Optional[str] = None  # GTIN/UPC/EAN

    # Cannabis Specific
    product_category: Optional[str] = None  # flower, edible, concentrate, etc.
    thc_percentage: Optional[Decimal] = None
    cbd_percentage: Optional[Decimal] = None
    strain_type: Optional[str] = None  # sativa, indica, hybrid

    # Quantities
    quantity_ordered: int = 0
    quantity_received: int = 0
    quantity_damaged: int = 0
    quantity_returned: int = 0
    quantity_accepted: int = 0

    # Units
    unit_of_measure: str = "EA"  # EA (each), CS (case), PK (pack)
    units_per_case: Optional[int] = None
    case_quantity: Optional[int] = None

    # Pricing
    unit_cost: Decimal = Decimal("0")
    discount_percentage: Decimal = Decimal("0")
    discount_amount: Decimal = Decimal("0")
    tax_rate: Decimal = Decimal("0")
    tax_amount: Decimal = Decimal("0")
    line_total: Decimal = Decimal("0")

    # Extended Amounts
    subtotal: Decimal = Decimal("0")
    total_discount: Decimal = Decimal("0")
    total_tax: Decimal = Decimal("0")
    total_amount: Decimal = Decimal("0")

    # Receiving
    receiving_status: ReceivingStatus = ReceivingStatus.NOT_RECEIVED
    expected_delivery_date: Optional[datetime] = None
    actual_delivery_date: Optional[datetime] = None
    batch_lot: Optional[str] = None
    expiry_date: Optional[date] = None

    # Quality Control
    quality_check_required: bool = False
    quality_check_passed: Optional[bool] = None
    quality_check_notes: Optional[str] = None
    quality_check_date: Optional[datetime] = None
    quality_check_by: Optional[UUID] = None

    # Notes
    notes: Optional[str] = None
    receiving_notes: Optional[str] = None
    damage_notes: Optional[str] = None

    # Status
    is_active: bool = True
    is_cancelled: bool = False
    cancellation_reason: Optional[str] = None

    # Metadata
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def create(
        cls,
        purchase_order_id: UUID,
        line_number: int,
        sku: str,
        product_name: str,
        quantity_ordered: int,
        unit_cost: Decimal,
        unit_of_measure: str = "EA"
    ) -> 'PurchaseOrderLine':
        """Factory method to create new purchase order line"""
        if line_number <= 0:
            raise BusinessRuleViolation("Line number must be positive")
        if quantity_ordered <= 0:
            raise BusinessRuleViolation("Quantity ordered must be positive")
        if unit_cost < 0:
            raise BusinessRuleViolation("Unit cost cannot be negative")

        line = cls(
            purchase_order_id=purchase_order_id,
            line_number=line_number,
            sku=sku,
            product_name=product_name,
            quantity_ordered=quantity_ordered,
            unit_cost=unit_cost,
            unit_of_measure=unit_of_measure
        )

        # Calculate initial totals
        line._calculate_totals()

        return line

    def _calculate_totals(self):
        """Calculate line totals"""
        # Calculate subtotal
        self.subtotal = self.unit_cost * Decimal(self.quantity_ordered)

        # Apply discount
        if self.discount_percentage > 0:
            self.discount_amount = self.subtotal * (self.discount_percentage / 100)
        self.total_discount = self.discount_amount

        # Calculate after discount
        amount_after_discount = self.subtotal - self.total_discount

        # Calculate tax
        if self.tax_rate > 0:
            self.tax_amount = amount_after_discount * (self.tax_rate / 100)
        self.total_tax = self.tax_amount

        # Calculate final totals
        self.total_amount = amount_after_discount + self.total_tax
        self.line_total = self.total_amount

    def update_quantity(self, new_quantity: int):
        """Update ordered quantity"""
        if new_quantity < 0:
            raise BusinessRuleViolation("Quantity cannot be negative")

        if self.quantity_received > 0 and new_quantity < self.quantity_received:
            raise BusinessRuleViolation("Cannot reduce quantity below received amount")

        self.quantity_ordered = new_quantity
        self._calculate_totals()
        self.mark_as_modified()

    def update_pricing(
        self,
        unit_cost: Optional[Decimal] = None,
        discount_percentage: Optional[Decimal] = None,
        tax_rate: Optional[Decimal] = None
    ):
        """Update pricing information"""
        if unit_cost is not None:
            if unit_cost < 0:
                raise BusinessRuleViolation("Unit cost cannot be negative")
            self.unit_cost = unit_cost

        if discount_percentage is not None:
            if discount_percentage < 0 or discount_percentage > 100:
                raise BusinessRuleViolation("Discount percentage must be between 0 and 100")
            self.discount_percentage = discount_percentage

        if tax_rate is not None:
            if tax_rate < 0:
                raise BusinessRuleViolation("Tax rate cannot be negative")
            self.tax_rate = tax_rate

        self._calculate_totals()
        self.mark_as_modified()

    def set_supplier_info(
        self,
        supplier_sku: Optional[str] = None,
        barcode: Optional[str] = None
    ):
        """Set supplier-specific information"""
        if supplier_sku:
            self.supplier_sku = supplier_sku
        if barcode:
            self.barcode = barcode

        self.mark_as_modified()

    def set_cannabis_attributes(
        self,
        category: Optional[str] = None,
        thc_percentage: Optional[Decimal] = None,
        cbd_percentage: Optional[Decimal] = None,
        strain_type: Optional[str] = None
    ):
        """Set cannabis-specific attributes"""
        if category:
            self.product_category = category

        if thc_percentage is not None:
            if thc_percentage < 0 or thc_percentage > 100:
                raise BusinessRuleViolation("THC percentage must be between 0 and 100")
            self.thc_percentage = thc_percentage

        if cbd_percentage is not None:
            if cbd_percentage < 0 or cbd_percentage > 100:
                raise BusinessRuleViolation("CBD percentage must be between 0 and 100")
            self.cbd_percentage = cbd_percentage

        if strain_type:
            if strain_type not in ['sativa', 'indica', 'hybrid', 'balanced']:
                raise BusinessRuleViolation("Invalid strain type")
            self.strain_type = strain_type

        self.mark_as_modified()

    def receive(
        self,
        quantity_received: int,
        batch_lot: Optional[str] = None,
        expiry_date: Optional[date] = None,
        notes: Optional[str] = None
    ):
        """Receive items for this line"""
        if quantity_received <= 0:
            raise BusinessRuleViolation("Received quantity must be positive")

        total_received = self.quantity_received + quantity_received
        if total_received > self.quantity_ordered:
            raise BusinessRuleViolation(f"Cannot receive more than ordered ({self.quantity_ordered})")

        self.quantity_received += quantity_received
        self.quantity_accepted = self.quantity_received - self.quantity_damaged - self.quantity_returned

        if batch_lot:
            self.batch_lot = batch_lot
        if expiry_date:
            self.expiry_date = expiry_date
        if notes:
            self.receiving_notes = notes

        # Update receiving status
        if self.quantity_received == 0:
            self.receiving_status = ReceivingStatus.NOT_RECEIVED
        elif self.quantity_received < self.quantity_ordered:
            self.receiving_status = ReceivingStatus.PARTIALLY_RECEIVED
        else:
            self.receiving_status = ReceivingStatus.FULLY_RECEIVED

        self.actual_delivery_date = datetime.utcnow()
        self.mark_as_modified()

    def report_damage(self, quantity_damaged: int, notes: Optional[str] = None):
        """Report damaged items"""
        if quantity_damaged <= 0:
            raise BusinessRuleViolation("Damaged quantity must be positive")

        if quantity_damaged > self.quantity_received:
            raise BusinessRuleViolation("Damaged quantity cannot exceed received quantity")

        self.quantity_damaged += quantity_damaged
        self.quantity_accepted = self.quantity_received - self.quantity_damaged - self.quantity_returned

        if notes:
            self.damage_notes = notes

        if self.quantity_damaged > 0:
            self.receiving_status = ReceivingStatus.RECEIVED_WITH_ISSUES

        self.mark_as_modified()

    def return_items(self, quantity_returned: int, reason: str):
        """Return items to supplier"""
        if quantity_returned <= 0:
            raise BusinessRuleViolation("Return quantity must be positive")

        if quantity_returned > self.quantity_received:
            raise BusinessRuleViolation("Cannot return more than received")

        self.quantity_returned += quantity_returned
        self.quantity_accepted = self.quantity_received - self.quantity_damaged - self.quantity_returned

        self.metadata['return_reason'] = reason
        self.metadata['return_date'] = datetime.utcnow().isoformat()

        if self.quantity_returned > 0:
            self.receiving_status = ReceivingStatus.RECEIVED_WITH_ISSUES

        self.mark_as_modified()

    def perform_quality_check(
        self,
        passed: bool,
        checked_by: UUID,
        notes: Optional[str] = None
    ):
        """Perform quality check on received items"""
        if not self.quality_check_required:
            raise BusinessRuleViolation("Quality check not required for this item")

        if self.quantity_received == 0:
            raise BusinessRuleViolation("Cannot perform quality check before receiving")

        self.quality_check_passed = passed
        self.quality_check_by = checked_by
        self.quality_check_date = datetime.utcnow()

        if notes:
            self.quality_check_notes = notes

        if not passed:
            self.receiving_status = ReceivingStatus.RECEIVED_WITH_ISSUES

        self.mark_as_modified()

    def cancel(self, reason: str):
        """Cancel this line item"""
        if self.quantity_received > 0:
            raise BusinessRuleViolation("Cannot cancel line with received items")

        self.is_cancelled = True
        self.is_active = False
        self.cancellation_reason = reason
        self.mark_as_modified()

    def get_received_percentage(self) -> Decimal:
        """Calculate percentage of items received"""
        if self.quantity_ordered == 0:
            return Decimal("0")

        percentage = (Decimal(self.quantity_received) / Decimal(self.quantity_ordered)) * 100
        return percentage.quantize(Decimal("0.01"))

    def get_accepted_percentage(self) -> Decimal:
        """Calculate percentage of items accepted"""
        if self.quantity_ordered == 0:
            return Decimal("0")

        percentage = (Decimal(self.quantity_accepted) / Decimal(self.quantity_ordered)) * 100
        return percentage.quantize(Decimal("0.01"))

    def is_fully_received(self) -> bool:
        """Check if line is fully received"""
        return self.quantity_received >= self.quantity_ordered

    def is_partially_received(self) -> bool:
        """Check if line is partially received"""
        return 0 < self.quantity_received < self.quantity_ordered

    def has_issues(self) -> bool:
        """Check if line has receiving issues"""
        return (
            self.quantity_damaged > 0 or
            self.quantity_returned > 0 or
            (self.quality_check_required and self.quality_check_passed == False)
        )

    def get_remaining_quantity(self) -> int:
        """Get quantity still to be received"""
        return max(0, self.quantity_ordered - self.quantity_received)

    def get_effective_cost(self) -> Decimal:
        """Get effective unit cost after discounts"""
        if self.quantity_ordered == 0:
            return Decimal("0")

        return (self.subtotal - self.total_discount) / Decimal(self.quantity_ordered)

    def validate(self) -> list[str]:
        """Validate line item data"""
        errors = []

        if not self.purchase_order_id:
            errors.append("Purchase order ID is required")

        if self.line_number <= 0:
            errors.append("Line number must be positive")

        if not self.sku:
            errors.append("SKU is required")

        if not self.product_name:
            errors.append("Product name is required")

        if self.quantity_ordered < 0:
            errors.append("Quantity ordered cannot be negative")

        if self.quantity_received < 0:
            errors.append("Quantity received cannot be negative")

        if self.quantity_received > self.quantity_ordered:
            errors.append("Quantity received cannot exceed quantity ordered")

        if self.quantity_damaged > self.quantity_received:
            errors.append("Quantity damaged cannot exceed quantity received")

        if self.quantity_returned > self.quantity_received:
            errors.append("Quantity returned cannot exceed quantity received")

        if self.unit_cost < 0:
            errors.append("Unit cost cannot be negative")

        if self.discount_percentage < 0 or self.discount_percentage > 100:
            errors.append("Discount percentage must be between 0 and 100")

        if self.tax_rate < 0:
            errors.append("Tax rate cannot be negative")

        return errors