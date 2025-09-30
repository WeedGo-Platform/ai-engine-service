"""
SupplierInvoice Entity
Following DDD Architecture Document Section 2.5
"""

from dataclasses import dataclass, field
from datetime import datetime, date, timedelta
from decimal import Decimal
from typing import Optional, List, Dict, Any
from uuid import UUID, uuid4

from ....shared.domain_base import Entity, BusinessRuleViolation
from ..value_objects import PaymentTerms


@dataclass
class SupplierInvoice(Entity):
    """
    SupplierInvoice Entity - Supplier billing documents
    As defined in DDD_ARCHITECTURE_REFACTORING.md Section 2.5
    """
    # Identifiers
    purchase_order_id: UUID = field(default_factory=uuid4)
    supplier_id: UUID = field(default_factory=uuid4)
    store_id: UUID = field(default_factory=uuid4)
    invoice_number: str = ""  # Supplier's invoice number
    internal_invoice_number: str = ""  # INV-YYYY-MM-XXXXX

    # Reference Numbers
    purchase_order_number: str = ""
    receiving_document_number: Optional[str] = None
    credit_memo_number: Optional[str] = None

    # Invoice Details
    invoice_date: date = field(default_factory=date.today)
    received_date: datetime = field(default_factory=datetime.utcnow)
    due_date: Optional[date] = None
    payment_terms: PaymentTerms = PaymentTerms.NET_30

    # Financial Amounts
    subtotal: Decimal = Decimal("0")
    tax_amount: Decimal = Decimal("0")
    shipping_amount: Decimal = Decimal("0")
    discount_amount: Decimal = Decimal("0")
    adjustment_amount: Decimal = Decimal("0")
    total_amount: Decimal = Decimal("0")

    # Tax Breakdown
    federal_tax: Decimal = Decimal("0")
    provincial_tax: Decimal = Decimal("0")
    excise_tax: Decimal = Decimal("0")  # Cannabis specific
    other_tax: Decimal = Decimal("0")
    tax_rate: Decimal = Decimal("0")

    # Payment Information
    amount_paid: Decimal = Decimal("0")
    amount_due: Decimal = Decimal("0")
    payment_status: str = "pending"  # pending, partial, paid, overdue
    last_payment_date: Optional[datetime] = None
    payment_method: Optional[str] = None
    payment_reference: Optional[str] = None

    # Line Items Summary
    total_line_items: int = 0
    total_units: int = 0

    # Discrepancies
    has_discrepancies: bool = False
    po_amount: Optional[Decimal] = None  # Expected from PO
    variance_amount: Decimal = Decimal("0")
    variance_reason: Optional[str] = None

    # Approval
    requires_approval: bool = False
    approval_status: str = "pending"  # pending, approved, rejected
    approved_by: Optional[UUID] = None
    approval_date: Optional[datetime] = None
    approval_notes: Optional[str] = None
    approval_threshold: Decimal = Decimal("5000")  # Requires approval if over

    # Three-Way Match
    three_way_match_performed: bool = False
    three_way_match_passed: Optional[bool] = None
    po_matched: bool = False
    receipt_matched: bool = False
    price_matched: bool = False

    # Status
    status: str = "draft"  # draft, submitted, approved, posted, cancelled
    is_posted: bool = False
    posted_date: Optional[datetime] = None
    posted_by: Optional[UUID] = None

    # Dispute
    is_disputed: bool = False
    dispute_reason: Optional[str] = None
    dispute_date: Optional[datetime] = None
    dispute_resolved: bool = False
    resolution_date: Optional[datetime] = None

    # Credit/Debit Notes
    is_credit_note: bool = False
    original_invoice_number: Optional[str] = None  # For credit notes
    credit_notes: List[str] = field(default_factory=list)  # Related credit notes

    # Document Management
    document_url: Optional[str] = None
    attachment_urls: List[str] = field(default_factory=list)

    # Notes
    internal_notes: Optional[str] = None
    supplier_notes: Optional[str] = None

    # Metadata
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    created_by: Optional[UUID] = None
    updated_by: Optional[UUID] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def create(
        cls,
        purchase_order_id: UUID,
        supplier_id: UUID,
        store_id: UUID,
        invoice_number: str,
        invoice_date: date,
        total_amount: Decimal,
        payment_terms: PaymentTerms = PaymentTerms.NET_30
    ) -> 'SupplierInvoice':
        """Factory method to create new supplier invoice"""
        if not invoice_number:
            raise BusinessRuleViolation("Invoice number is required")
        if total_amount < 0:
            raise BusinessRuleViolation("Total amount cannot be negative")

        # Generate internal invoice number
        now = datetime.utcnow()
        internal_number = f"INV-{now.year}-{now.month:02d}-{uuid4().hex[:5].upper()}"

        # Calculate due date
        due_date = cls._calculate_due_date(invoice_date, payment_terms)

        invoice = cls(
            purchase_order_id=purchase_order_id,
            supplier_id=supplier_id,
            store_id=store_id,
            invoice_number=invoice_number,
            internal_invoice_number=internal_number,
            invoice_date=invoice_date,
            due_date=due_date,
            payment_terms=payment_terms,
            total_amount=total_amount,
            amount_due=total_amount
        )

        # Check if approval required
        if total_amount > invoice.approval_threshold:
            invoice.requires_approval = True

        return invoice

    @staticmethod
    def _calculate_due_date(invoice_date: date, payment_terms: PaymentTerms) -> date:
        """Calculate payment due date based on terms"""
        if payment_terms == PaymentTerms.COD or payment_terms == PaymentTerms.DUE_ON_RECEIPT:
            return invoice_date
        elif payment_terms == PaymentTerms.NET_15:
            return invoice_date + timedelta(days=15)
        elif payment_terms == PaymentTerms.NET_30:
            return invoice_date + timedelta(days=30)
        elif payment_terms == PaymentTerms.NET_45:
            return invoice_date + timedelta(days=45)
        elif payment_terms == PaymentTerms.NET_60:
            return invoice_date + timedelta(days=60)
        elif payment_terms == PaymentTerms.NET_90:
            return invoice_date + timedelta(days=90)
        else:
            return invoice_date + timedelta(days=30)

    def set_amounts(
        self,
        subtotal: Decimal,
        tax_amount: Optional[Decimal] = None,
        shipping_amount: Optional[Decimal] = None,
        discount_amount: Optional[Decimal] = None
    ):
        """Set invoice amounts"""
        if subtotal < 0:
            raise BusinessRuleViolation("Subtotal cannot be negative")

        self.subtotal = subtotal

        if tax_amount is not None:
            if tax_amount < 0:
                raise BusinessRuleViolation("Tax amount cannot be negative")
            self.tax_amount = tax_amount

        if shipping_amount is not None:
            if shipping_amount < 0:
                raise BusinessRuleViolation("Shipping amount cannot be negative")
            self.shipping_amount = shipping_amount

        if discount_amount is not None:
            if discount_amount < 0:
                raise BusinessRuleViolation("Discount amount cannot be negative")
            self.discount_amount = discount_amount

        self._recalculate_total()
        self.mark_as_modified()

    def set_tax_breakdown(
        self,
        federal: Optional[Decimal] = None,
        provincial: Optional[Decimal] = None,
        excise: Optional[Decimal] = None,
        other: Optional[Decimal] = None
    ):
        """Set tax breakdown"""
        if federal is not None:
            self.federal_tax = federal
        if provincial is not None:
            self.provincial_tax = provincial
        if excise is not None:
            self.excise_tax = excise
        if other is not None:
            self.other_tax = other

        # Update total tax
        self.tax_amount = self.federal_tax + self.provincial_tax + self.excise_tax + self.other_tax
        self._recalculate_total()
        self.mark_as_modified()

    def _recalculate_total(self):
        """Recalculate total amount"""
        self.total_amount = (
            self.subtotal +
            self.tax_amount +
            self.shipping_amount -
            self.discount_amount +
            self.adjustment_amount
        )
        self.amount_due = self.total_amount - self.amount_paid

    def perform_three_way_match(
        self,
        po_amount: Decimal,
        received_amount: Decimal,
        tolerance_percentage: Decimal = Decimal("2")
    ):
        """Perform three-way match against PO and receipt"""
        self.three_way_match_performed = True
        self.po_amount = po_amount

        # Check PO match
        po_variance = abs(self.total_amount - po_amount)
        po_tolerance = po_amount * (tolerance_percentage / 100)
        self.po_matched = po_variance <= po_tolerance

        # Check receipt match
        receipt_variance = abs(self.total_amount - received_amount)
        receipt_tolerance = received_amount * (tolerance_percentage / 100)
        self.receipt_matched = receipt_variance <= receipt_tolerance

        # Price match is considered passed if within tolerance
        self.price_matched = self.po_matched

        # Overall match
        self.three_way_match_passed = self.po_matched and self.receipt_matched

        # Calculate variance
        self.variance_amount = self.total_amount - po_amount

        if not self.three_way_match_passed:
            self.has_discrepancies = True
            self.requires_approval = True

        self.mark_as_modified()

    def add_line_item(self, quantity: int, unit_price: Decimal):
        """Add a line item summary"""
        if quantity <= 0:
            raise BusinessRuleViolation("Quantity must be positive")
        if unit_price < 0:
            raise BusinessRuleViolation("Unit price cannot be negative")

        self.total_line_items += 1
        self.total_units += quantity
        self.mark_as_modified()

    def record_payment(
        self,
        amount: Decimal,
        payment_date: datetime,
        payment_method: str,
        reference: Optional[str] = None
    ):
        """Record a payment against the invoice"""
        if amount <= 0:
            raise BusinessRuleViolation("Payment amount must be positive")

        if amount > self.amount_due:
            raise BusinessRuleViolation(f"Payment amount ({amount}) exceeds amount due ({self.amount_due})")

        self.amount_paid += amount
        self.amount_due = self.total_amount - self.amount_paid
        self.last_payment_date = payment_date
        self.payment_method = payment_method

        if reference:
            self.payment_reference = reference

        # Update payment status
        if self.amount_due == 0:
            self.payment_status = "paid"
        else:
            self.payment_status = "partial"

        # Track payment history
        if 'payment_history' not in self.metadata:
            self.metadata['payment_history'] = []

        self.metadata['payment_history'].append({
            'amount': str(amount),
            'date': payment_date.isoformat(),
            'method': payment_method,
            'reference': reference
        })

        self.mark_as_modified()

    def approve(self, approved_by: UUID, notes: Optional[str] = None):
        """Approve the invoice"""
        if not self.requires_approval:
            raise BusinessRuleViolation("Invoice does not require approval")

        if self.approval_status == "approved":
            raise BusinessRuleViolation("Invoice already approved")

        self.approval_status = "approved"
        self.approved_by = approved_by
        self.approval_date = datetime.utcnow()
        self.approval_notes = notes
        self.status = "approved"

        self.mark_as_modified()

    def reject(self, rejected_by: UUID, reason: str):
        """Reject the invoice"""
        if not self.requires_approval:
            raise BusinessRuleViolation("Invoice does not require approval")

        self.approval_status = "rejected"
        self.metadata['rejected_by'] = str(rejected_by)
        self.metadata['rejection_date'] = datetime.utcnow().isoformat()
        self.metadata['rejection_reason'] = reason
        self.status = "draft"  # Return to draft

        self.mark_as_modified()

    def post_to_ledger(self, posted_by: UUID):
        """Post invoice to general ledger"""
        if self.is_posted:
            raise BusinessRuleViolation("Invoice already posted")

        if self.requires_approval and self.approval_status != "approved":
            raise BusinessRuleViolation("Invoice requires approval before posting")

        if self.has_discrepancies and not self.variance_reason:
            raise BusinessRuleViolation("Discrepancies must be explained before posting")

        self.is_posted = True
        self.posted_date = datetime.utcnow()
        self.posted_by = posted_by
        self.status = "posted"

        self.mark_as_modified()

    def dispute(self, reason: str, disputed_by: UUID):
        """Dispute the invoice"""
        if self.is_disputed:
            raise BusinessRuleViolation("Invoice already disputed")

        self.is_disputed = True
        self.dispute_reason = reason
        self.dispute_date = datetime.utcnow()
        self.metadata['disputed_by'] = str(disputed_by)

        self.mark_as_modified()

    def resolve_dispute(self, resolution: str, resolved_by: UUID):
        """Resolve a dispute"""
        if not self.is_disputed:
            raise BusinessRuleViolation("Invoice is not disputed")

        if self.dispute_resolved:
            raise BusinessRuleViolation("Dispute already resolved")

        self.dispute_resolved = True
        self.resolution_date = datetime.utcnow()
        self.metadata['resolution'] = resolution
        self.metadata['resolved_by'] = str(resolved_by)

        self.mark_as_modified()

    def create_credit_note(self, credit_amount: Decimal, reason: str) -> 'SupplierInvoice':
        """Create a credit note for this invoice"""
        if credit_amount <= 0:
            raise BusinessRuleViolation("Credit amount must be positive")

        if credit_amount > self.total_amount:
            raise BusinessRuleViolation("Credit amount cannot exceed invoice total")

        # Generate credit note number
        credit_number = f"CN-{self.invoice_number}"

        credit_note = SupplierInvoice.create(
            purchase_order_id=self.purchase_order_id,
            supplier_id=self.supplier_id,
            store_id=self.store_id,
            invoice_number=credit_number,
            invoice_date=date.today(),
            total_amount=-credit_amount,  # Negative amount for credit
            payment_terms=self.payment_terms
        )

        credit_note.is_credit_note = True
        credit_note.original_invoice_number = self.invoice_number
        credit_note.metadata['credit_reason'] = reason

        # Track credit note on original invoice
        self.credit_notes.append(credit_number)
        self.mark_as_modified()

        return credit_note

    def add_attachment(self, url: str):
        """Add an attachment URL"""
        if url not in self.attachment_urls:
            self.attachment_urls.append(url)
            self.mark_as_modified()

    def cancel(self, cancelled_by: UUID, reason: str):
        """Cancel the invoice"""
        if self.is_posted:
            raise BusinessRuleViolation("Cannot cancel posted invoice")

        if self.amount_paid > 0:
            raise BusinessRuleViolation("Cannot cancel invoice with payments")

        self.status = "cancelled"
        self.metadata['cancelled_by'] = str(cancelled_by)
        self.metadata['cancellation_date'] = datetime.utcnow().isoformat()
        self.metadata['cancellation_reason'] = reason

        self.mark_as_modified()

    def is_overdue(self) -> bool:
        """Check if invoice is overdue"""
        if self.payment_status == "paid":
            return False

        if not self.due_date:
            return False

        return date.today() > self.due_date and self.amount_due > 0

    def days_overdue(self) -> int:
        """Calculate days overdue"""
        if not self.is_overdue():
            return 0

        delta = date.today() - self.due_date
        return delta.days

    def get_payment_percentage(self) -> Decimal:
        """Calculate payment percentage"""
        if self.total_amount == 0:
            return Decimal("100")

        percentage = (self.amount_paid / self.total_amount) * 100
        return percentage.quantize(Decimal("0.01"))

    def requires_three_way_match(self) -> bool:
        """Check if three-way match is required"""
        # Business rule: Invoices over $1000 require three-way match
        return self.total_amount > Decimal("1000")

    def validate(self) -> List[str]:
        """Validate invoice data"""
        errors = []

        if not self.invoice_number:
            errors.append("Invoice number is required")

        if not self.supplier_id:
            errors.append("Supplier ID is required")

        if not self.store_id:
            errors.append("Store ID is required")

        if self.total_amount < 0 and not self.is_credit_note:
            errors.append("Total amount cannot be negative unless credit note")

        if self.amount_paid < 0:
            errors.append("Amount paid cannot be negative")

        if self.amount_paid > self.total_amount and not self.is_credit_note:
            errors.append("Amount paid cannot exceed total amount")

        if self.subtotal < 0 and not self.is_credit_note:
            errors.append("Subtotal cannot be negative")

        if self.tax_amount < 0:
            errors.append("Tax amount cannot be negative")

        if self.shipping_amount < 0:
            errors.append("Shipping amount cannot be negative")

        if self.discount_amount < 0:
            errors.append("Discount amount cannot be negative")

        return errors