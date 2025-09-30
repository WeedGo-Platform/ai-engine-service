"""
ReceivingDocument Entity
Following DDD Architecture Document Section 2.5
"""

from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from typing import Optional, List, Dict, Any
from uuid import UUID, uuid4

from ....shared.domain_base import Entity, BusinessRuleViolation
from ..value_objects import ReceivingStatus


@dataclass
class ReceivingDocument(Entity):
    """
    ReceivingDocument Entity - Track goods receipt
    As defined in DDD_ARCHITECTURE_REFACTORING.md Section 2.5
    """
    # Identifiers
    purchase_order_id: UUID = field(default_factory=uuid4)
    document_number: str = ""  # RCV-YYYY-MM-XXXXX
    store_id: UUID = field(default_factory=uuid4)
    supplier_id: UUID = field(default_factory=uuid4)

    # Reference Numbers
    purchase_order_number: str = ""
    supplier_invoice_number: Optional[str] = None
    packing_slip_number: Optional[str] = None
    bill_of_lading: Optional[str] = None

    # Receiving Details
    receiving_date: datetime = field(default_factory=datetime.utcnow)
    receiving_status: ReceivingStatus = ReceivingStatus.NOT_RECEIVED
    received_by: Optional[UUID] = None
    received_by_name: Optional[str] = None

    # Delivery Information
    delivery_date: datetime = field(default_factory=datetime.utcnow)
    carrier_name: Optional[str] = None
    tracking_number: Optional[str] = None
    driver_name: Optional[str] = None
    vehicle_number: Optional[str] = None

    # Quantities
    total_items_expected: int = 0
    total_items_received: int = 0
    total_items_damaged: int = 0
    total_items_rejected: int = 0
    total_items_accepted: int = 0

    # Line Items Summary
    total_line_items: int = 0
    lines_fully_received: int = 0
    lines_partially_received: int = 0
    lines_not_received: int = 0

    # Financial Summary
    expected_value: Decimal = Decimal("0")
    received_value: Decimal = Decimal("0")
    damaged_value: Decimal = Decimal("0")
    accepted_value: Decimal = Decimal("0")

    # Temperature Control (for cannabis/perishables)
    temperature_on_arrival: Optional[Decimal] = None
    temperature_compliant: Optional[bool] = None
    cold_chain_maintained: Optional[bool] = None

    # Quality Control
    quality_check_required: bool = False
    quality_check_completed: bool = False
    quality_check_passed: Optional[bool] = None
    quality_inspector: Optional[UUID] = None
    quality_check_date: Optional[datetime] = None

    # Discrepancies
    has_discrepancies: bool = False
    discrepancy_notes: Optional[str] = None
    discrepancy_resolved: bool = False
    resolution_notes: Optional[str] = None

    # Documentation
    documents_received: List[str] = field(default_factory=list)  # invoice, packing_slip, coa, etc.
    certificate_of_analysis: bool = False
    excise_stamps_verified: bool = False

    # Photos/Attachments
    photo_urls: List[str] = field(default_factory=list)
    attachment_urls: List[str] = field(default_factory=list)

    # Approval
    requires_approval: bool = False
    approved_by: Optional[UUID] = None
    approval_date: Optional[datetime] = None
    approval_notes: Optional[str] = None

    # Status
    is_complete: bool = False
    is_cancelled: bool = False
    cancellation_reason: Optional[str] = None

    # Notes
    general_notes: Optional[str] = None
    damage_description: Optional[str] = None
    return_instructions: Optional[str] = None

    # Metadata
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def create(
        cls,
        purchase_order_id: UUID,
        purchase_order_number: str,
        store_id: UUID,
        supplier_id: UUID,
        received_by: UUID
    ) -> 'ReceivingDocument':
        """Factory method to create new receiving document"""
        # Generate document number
        now = datetime.utcnow()
        document_number = f"RCV-{now.year}-{now.month:02d}-{uuid4().hex[:5].upper()}"

        document = cls(
            purchase_order_id=purchase_order_id,
            purchase_order_number=purchase_order_number,
            document_number=document_number,
            store_id=store_id,
            supplier_id=supplier_id,
            received_by=received_by,
            receiving_date=now,
            delivery_date=now
        )

        return document

    def set_delivery_info(
        self,
        carrier: Optional[str] = None,
        tracking: Optional[str] = None,
        driver: Optional[str] = None,
        vehicle: Optional[str] = None
    ):
        """Set delivery information"""
        if carrier:
            self.carrier_name = carrier
        if tracking:
            self.tracking_number = tracking
        if driver:
            self.driver_name = driver
        if vehicle:
            self.vehicle_number = vehicle

        self.mark_as_modified()

    def set_reference_numbers(
        self,
        invoice: Optional[str] = None,
        packing_slip: Optional[str] = None,
        bill_of_lading: Optional[str] = None
    ):
        """Set reference numbers"""
        if invoice:
            self.supplier_invoice_number = invoice
        if packing_slip:
            self.packing_slip_number = packing_slip
        if bill_of_lading:
            self.bill_of_lading = bill_of_lading

        self.mark_as_modified()

    def record_temperature(
        self,
        temperature: Decimal,
        min_required: Decimal,
        max_required: Decimal
    ):
        """Record temperature on arrival"""
        self.temperature_on_arrival = temperature
        self.temperature_compliant = min_required <= temperature <= max_required
        self.cold_chain_maintained = self.temperature_compliant

        if not self.temperature_compliant:
            self.has_discrepancies = True
            self.discrepancy_notes = f"Temperature {temperature}°C out of range {min_required}-{max_required}°C"

        self.mark_as_modified()

    def receive_line_item(
        self,
        quantity_expected: int,
        quantity_received: int,
        quantity_damaged: int = 0,
        quantity_rejected: int = 0
    ):
        """Record receipt of a line item"""
        if quantity_received < 0:
            raise BusinessRuleViolation("Received quantity cannot be negative")
        if quantity_damaged < 0:
            raise BusinessRuleViolation("Damaged quantity cannot be negative")
        if quantity_rejected < 0:
            raise BusinessRuleViolation("Rejected quantity cannot be negative")

        # Update quantities
        self.total_items_expected += quantity_expected
        self.total_items_received += quantity_received
        self.total_items_damaged += quantity_damaged
        self.total_items_rejected += quantity_rejected
        self.total_items_accepted += (quantity_received - quantity_damaged - quantity_rejected)

        # Update line counts
        self.total_line_items += 1
        if quantity_received == 0:
            self.lines_not_received += 1
        elif quantity_received < quantity_expected:
            self.lines_partially_received += 1
            self.has_discrepancies = True
        else:
            self.lines_fully_received += 1

        # Update receiving status
        self._update_receiving_status()

        self.mark_as_modified()

    def _update_receiving_status(self):
        """Update overall receiving status"""
        if self.total_items_received == 0:
            self.receiving_status = ReceivingStatus.NOT_RECEIVED
        elif self.total_items_received < self.total_items_expected:
            self.receiving_status = ReceivingStatus.PARTIALLY_RECEIVED
        elif self.total_items_damaged > 0 or self.total_items_rejected > 0:
            self.receiving_status = ReceivingStatus.RECEIVED_WITH_ISSUES
        else:
            self.receiving_status = ReceivingStatus.FULLY_RECEIVED

    def add_document(self, document_type: str):
        """Add a received document"""
        if document_type not in self.documents_received:
            self.documents_received.append(document_type)

            # Special handling for specific documents
            if document_type.lower() == "certificate_of_analysis":
                self.certificate_of_analysis = True
            elif document_type.lower() == "excise_stamps":
                self.excise_stamps_verified = True

            self.mark_as_modified()

    def add_photo(self, photo_url: str):
        """Add a photo"""
        if photo_url not in self.photo_urls:
            self.photo_urls.append(photo_url)
            self.mark_as_modified()

    def add_attachment(self, attachment_url: str):
        """Add an attachment"""
        if attachment_url not in self.attachment_urls:
            self.attachment_urls.append(attachment_url)
            self.mark_as_modified()

    def perform_quality_check(
        self,
        passed: bool,
        inspector: UUID,
        notes: Optional[str] = None
    ):
        """Perform quality check"""
        if not self.quality_check_required:
            raise BusinessRuleViolation("Quality check not required for this receipt")

        self.quality_check_completed = True
        self.quality_check_passed = passed
        self.quality_inspector = inspector
        self.quality_check_date = datetime.utcnow()

        if notes:
            self.metadata['quality_notes'] = notes

        if not passed:
            self.has_discrepancies = True
            self.receiving_status = ReceivingStatus.RECEIVED_WITH_ISSUES

        self.mark_as_modified()

    def report_discrepancy(self, description: str):
        """Report a discrepancy"""
        self.has_discrepancies = True
        self.discrepancy_notes = description
        self.receiving_status = ReceivingStatus.RECEIVED_WITH_ISSUES
        self.mark_as_modified()

    def resolve_discrepancy(self, resolution: str):
        """Resolve discrepancies"""
        if not self.has_discrepancies:
            raise BusinessRuleViolation("No discrepancies to resolve")

        self.discrepancy_resolved = True
        self.resolution_notes = resolution
        self.mark_as_modified()

    def approve(
        self,
        approved_by: UUID,
        notes: Optional[str] = None
    ):
        """Approve the receiving document"""
        if not self.requires_approval:
            raise BusinessRuleViolation("Approval not required")

        self.approved_by = approved_by
        self.approval_date = datetime.utcnow()
        self.approval_notes = notes
        self.mark_as_modified()

    def complete(self):
        """Mark document as complete"""
        if self.has_discrepancies and not self.discrepancy_resolved:
            raise BusinessRuleViolation("Cannot complete with unresolved discrepancies")

        if self.quality_check_required and not self.quality_check_completed:
            raise BusinessRuleViolation("Cannot complete without quality check")

        if self.requires_approval and not self.approved_by:
            raise BusinessRuleViolation("Cannot complete without approval")

        self.is_complete = True
        self.mark_as_modified()

    def cancel(self, reason: str):
        """Cancel the receiving document"""
        if self.is_complete:
            raise BusinessRuleViolation("Cannot cancel completed document")

        self.is_cancelled = True
        self.cancellation_reason = reason
        self.mark_as_modified()

    def calculate_variance(self) -> Dict[str, Any]:
        """Calculate receiving variance"""
        quantity_variance = self.total_items_received - self.total_items_expected
        quantity_variance_pct = Decimal("0")
        if self.total_items_expected > 0:
            quantity_variance_pct = (Decimal(quantity_variance) / Decimal(self.total_items_expected)) * 100

        return {
            "quantity_variance": quantity_variance,
            "quantity_variance_percentage": quantity_variance_pct.quantize(Decimal("0.01")),
            "damaged_quantity": self.total_items_damaged,
            "rejected_quantity": self.total_items_rejected,
            "acceptance_rate": self.get_acceptance_rate()
        }

    def get_acceptance_rate(self) -> Decimal:
        """Calculate acceptance rate"""
        if self.total_items_received == 0:
            return Decimal("0")

        rate = (Decimal(self.total_items_accepted) / Decimal(self.total_items_received)) * 100
        return rate.quantize(Decimal("0.01"))

    def get_completion_percentage(self) -> Decimal:
        """Calculate completion percentage"""
        if self.total_items_expected == 0:
            return Decimal("100")

        percentage = (Decimal(self.total_items_received) / Decimal(self.total_items_expected)) * 100
        return min(percentage, Decimal("100")).quantize(Decimal("0.01"))

    def has_temperature_issues(self) -> bool:
        """Check if there are temperature compliance issues"""
        return self.temperature_compliant == False

    def validate(self) -> List[str]:
        """Validate receiving document"""
        errors = []

        if not self.document_number:
            errors.append("Document number is required")

        if not self.purchase_order_id:
            errors.append("Purchase order ID is required")

        if not self.store_id:
            errors.append("Store ID is required")

        if not self.supplier_id:
            errors.append("Supplier ID is required")

        if self.total_items_received < 0:
            errors.append("Total items received cannot be negative")

        if self.total_items_damaged > self.total_items_received:
            errors.append("Damaged items cannot exceed received items")

        if self.total_items_rejected > self.total_items_received:
            errors.append("Rejected items cannot exceed received items")

        return errors