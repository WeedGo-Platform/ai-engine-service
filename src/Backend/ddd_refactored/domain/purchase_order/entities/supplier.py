"""
Supplier Entity
Following DDD Architecture Document Section 2.5
"""

from dataclasses import dataclass, field
from datetime import datetime, date
from decimal import Decimal
from typing import Optional, List, Dict, Any
from uuid import UUID, uuid4

from ....shared.domain_base import Entity, BusinessRuleViolation
from ....shared.value_objects import Address, ContactInfo
from ..value_objects import PaymentTerms


@dataclass
class Supplier(Entity):
    """
    Supplier Entity - Supplier management
    As defined in DDD_ARCHITECTURE_REFACTORING.md Section 2.5
    """
    # Identifiers
    tenant_id: UUID = field(default_factory=uuid4)
    supplier_code: str = ""  # Unique supplier code
    tax_id: Optional[str] = None  # Business number/Tax ID

    # Basic Information
    name: str = ""
    legal_name: Optional[str] = None
    dba_name: Optional[str] = None  # Doing Business As
    supplier_type: str = "vendor"  # vendor, manufacturer, distributor, licensed_producer

    # Contact Information
    primary_contact_name: Optional[str] = None
    primary_contact_title: Optional[str] = None
    primary_email: Optional[str] = None
    primary_phone: Optional[str] = None
    secondary_email: Optional[str] = None
    secondary_phone: Optional[str] = None
    website: Optional[str] = None

    # Addresses
    billing_address: Optional[Address] = None
    shipping_address: Optional[Address] = None
    remittance_address: Optional[Address] = None  # For payments

    # Payment Information
    payment_terms: PaymentTerms = PaymentTerms.NET_30
    credit_limit: Decimal = Decimal("0")
    current_balance: Decimal = Decimal("0")
    payment_method: Optional[str] = None  # check, eft, wire, credit_card
    bank_account_info: Optional[str] = None  # Encrypted

    # Order Requirements
    minimum_order_amount: Decimal = Decimal("0")
    minimum_order_quantity: Optional[int] = None
    lead_time_days: int = 0
    order_cutoff_time: Optional[str] = None  # e.g., "14:00"
    delivery_days: Optional[List[str]] = None  # ["Monday", "Wednesday", "Friday"]

    # Cannabis Compliance
    license_number: Optional[str] = None
    license_type: Optional[str] = None  # cultivation, processing, distribution
    license_expiry: Optional[date] = None
    license_status: str = "active"  # active, expired, suspended
    is_licensed_producer: bool = False
    health_canada_license: Optional[str] = None  # For Canadian LPs

    # Certifications
    certifications: List[str] = field(default_factory=list)  # GMP, ISO, Organic, etc.
    insurance_coverage: Optional[Decimal] = None
    insurance_expiry: Optional[date] = None

    # Product Categories
    product_categories: List[str] = field(default_factory=list)  # Categories supplied
    brands_carried: List[str] = field(default_factory=list)

    # Performance Metrics
    on_time_delivery_rate: Decimal = Decimal("100")
    quality_rating: Decimal = Decimal("5.0")  # Out of 5
    total_orders_placed: int = 0
    total_orders_received: int = 0
    total_spend: Decimal = Decimal("0")

    # Status
    status: str = "active"  # active, inactive, suspended, blacklisted
    is_preferred: bool = False
    is_approved: bool = True
    approval_date: Optional[datetime] = None
    approved_by: Optional[UUID] = None

    # Integration
    api_enabled: bool = False
    api_endpoint: Optional[str] = None
    api_credentials: Optional[str] = None  # Encrypted
    edi_enabled: bool = False
    edi_id: Optional[str] = None

    # Notes
    notes: Optional[str] = None
    internal_notes: Optional[str] = None
    compliance_notes: Optional[str] = None

    # Metadata
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    created_by: Optional[UUID] = None
    updated_by: Optional[UUID] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def create(
        cls,
        tenant_id: UUID,
        name: str,
        supplier_code: str,
        supplier_type: str = "vendor",
        payment_terms: PaymentTerms = PaymentTerms.NET_30
    ) -> 'Supplier':
        """Factory method to create new supplier"""
        if not name:
            raise BusinessRuleViolation("Supplier name is required")
        if not supplier_code:
            raise BusinessRuleViolation("Supplier code is required")

        supplier = cls(
            tenant_id=tenant_id,
            name=name,
            supplier_code=supplier_code.upper(),
            supplier_type=supplier_type,
            payment_terms=payment_terms
        )

        return supplier

    def set_contact_info(
        self,
        contact_name: Optional[str] = None,
        email: Optional[str] = None,
        phone: Optional[str] = None,
        website: Optional[str] = None
    ):
        """Set primary contact information"""
        if contact_name:
            self.primary_contact_name = contact_name
        if email:
            self.primary_email = email
        if phone:
            self.primary_phone = phone
        if website:
            self.website = website

        self.mark_as_modified()

    def set_addresses(
        self,
        billing: Optional[Address] = None,
        shipping: Optional[Address] = None,
        remittance: Optional[Address] = None
    ):
        """Set supplier addresses"""
        if billing:
            self.billing_address = billing
        if shipping:
            self.shipping_address = shipping
        if remittance:
            self.remittance_address = remittance

        self.mark_as_modified()

    def set_payment_info(
        self,
        terms: Optional[PaymentTerms] = None,
        credit_limit: Optional[Decimal] = None,
        method: Optional[str] = None
    ):
        """Set payment information"""
        if terms:
            self.payment_terms = terms

        if credit_limit is not None:
            if credit_limit < 0:
                raise BusinessRuleViolation("Credit limit cannot be negative")
            self.credit_limit = credit_limit

        if method:
            if method not in ['check', 'eft', 'wire', 'credit_card', 'cash']:
                raise BusinessRuleViolation("Invalid payment method")
            self.payment_method = method

        self.mark_as_modified()

    def set_order_requirements(
        self,
        minimum_amount: Optional[Decimal] = None,
        minimum_quantity: Optional[int] = None,
        lead_time: Optional[int] = None,
        cutoff_time: Optional[str] = None,
        delivery_days: Optional[List[str]] = None
    ):
        """Set order requirements"""
        if minimum_amount is not None:
            if minimum_amount < 0:
                raise BusinessRuleViolation("Minimum order amount cannot be negative")
            self.minimum_order_amount = minimum_amount

        if minimum_quantity is not None:
            if minimum_quantity < 0:
                raise BusinessRuleViolation("Minimum order quantity cannot be negative")
            self.minimum_order_quantity = minimum_quantity

        if lead_time is not None:
            if lead_time < 0:
                raise BusinessRuleViolation("Lead time cannot be negative")
            self.lead_time_days = lead_time

        if cutoff_time:
            self.order_cutoff_time = cutoff_time

        if delivery_days:
            self.delivery_days = delivery_days

        self.mark_as_modified()

    def set_cannabis_license(
        self,
        license_number: str,
        license_type: str,
        expiry_date: date,
        health_canada: Optional[str] = None
    ):
        """Set cannabis license information"""
        self.license_number = license_number
        self.license_type = license_type
        self.license_expiry = expiry_date

        if health_canada:
            self.health_canada_license = health_canada
            self.is_licensed_producer = True

        # Update license status
        if expiry_date < date.today():
            self.license_status = "expired"
        else:
            self.license_status = "active"

        self.mark_as_modified()

    def add_certification(self, certification: str):
        """Add a certification"""
        if certification not in self.certifications:
            self.certifications.append(certification)
            self.mark_as_modified()

    def remove_certification(self, certification: str):
        """Remove a certification"""
        if certification in self.certifications:
            self.certifications.remove(certification)
            self.mark_as_modified()

    def add_product_category(self, category: str):
        """Add a product category"""
        if category not in self.product_categories:
            self.product_categories.append(category)
            self.mark_as_modified()

    def add_brand(self, brand: str):
        """Add a brand carried"""
        if brand not in self.brands_carried:
            self.brands_carried.append(brand)
            self.mark_as_modified()

    def update_performance_metrics(
        self,
        on_time_rate: Optional[Decimal] = None,
        quality_rating: Optional[Decimal] = None
    ):
        """Update performance metrics"""
        if on_time_rate is not None:
            if on_time_rate < 0 or on_time_rate > 100:
                raise BusinessRuleViolation("On-time rate must be between 0 and 100")
            self.on_time_delivery_rate = on_time_rate

        if quality_rating is not None:
            if quality_rating < 0 or quality_rating > 5:
                raise BusinessRuleViolation("Quality rating must be between 0 and 5")
            self.quality_rating = quality_rating

        self.mark_as_modified()

    def record_order(self, order_amount: Decimal):
        """Record a new order"""
        if order_amount < 0:
            raise BusinessRuleViolation("Order amount cannot be negative")

        self.total_orders_placed += 1
        self.total_spend += order_amount
        self.current_balance += order_amount
        self.mark_as_modified()

    def record_delivery(self, on_time: bool = True):
        """Record a delivery"""
        self.total_orders_received += 1

        # Update on-time rate
        if self.total_orders_received > 0:
            if on_time:
                current_on_time = self.total_orders_received - 1
                new_on_time = current_on_time + 1
            else:
                current_on_time = (self.on_time_delivery_rate / 100) * (self.total_orders_received - 1)
                new_on_time = current_on_time

            self.on_time_delivery_rate = (new_on_time / self.total_orders_received) * 100

        self.mark_as_modified()

    def record_payment(self, amount: Decimal):
        """Record a payment"""
        if amount < 0:
            raise BusinessRuleViolation("Payment amount cannot be negative")

        self.current_balance = max(Decimal("0"), self.current_balance - amount)
        self.mark_as_modified()

    def approve(self, approved_by: UUID):
        """Approve the supplier"""
        self.is_approved = True
        self.approved_by = approved_by
        self.approval_date = datetime.utcnow()
        self.status = "active"
        self.mark_as_modified()

    def suspend(self, reason: str):
        """Suspend the supplier"""
        self.status = "suspended"
        self.is_approved = False
        self.metadata['suspension_reason'] = reason
        self.metadata['suspended_at'] = datetime.utcnow().isoformat()
        self.mark_as_modified()

    def reactivate(self):
        """Reactivate the supplier"""
        if self.status == "blacklisted":
            raise BusinessRuleViolation("Cannot reactivate blacklisted supplier")

        self.status = "active"
        self.mark_as_modified()

    def blacklist(self, reason: str):
        """Blacklist the supplier"""
        self.status = "blacklisted"
        self.is_approved = False
        self.is_preferred = False
        self.metadata['blacklist_reason'] = reason
        self.metadata['blacklisted_at'] = datetime.utcnow().isoformat()
        self.mark_as_modified()

    def mark_as_preferred(self):
        """Mark supplier as preferred"""
        if self.status != "active":
            raise BusinessRuleViolation("Only active suppliers can be marked as preferred")

        self.is_preferred = True
        self.mark_as_modified()

    def enable_api_integration(self, endpoint: str, credentials: str):
        """Enable API integration"""
        self.api_enabled = True
        self.api_endpoint = endpoint
        self.api_credentials = credentials  # Should be encrypted
        self.mark_as_modified()

    def enable_edi(self, edi_id: str):
        """Enable EDI integration"""
        self.edi_enabled = True
        self.edi_id = edi_id
        self.mark_as_modified()

    def is_license_valid(self) -> bool:
        """Check if license is valid"""
        if not self.license_number:
            return False

        if not self.license_expiry:
            return False

        return self.license_expiry >= date.today() and self.license_status == "active"

    def is_credit_available(self, amount: Decimal) -> bool:
        """Check if credit is available for an order"""
        if self.credit_limit == 0:
            return True  # No credit limit

        return (self.current_balance + amount) <= self.credit_limit

    def days_until_license_expiry(self) -> Optional[int]:
        """Calculate days until license expires"""
        if not self.license_expiry:
            return None

        delta = self.license_expiry - date.today()
        return delta.days

    def needs_license_renewal(self, days_threshold: int = 60) -> bool:
        """Check if license needs renewal soon"""
        days_left = self.days_until_license_expiry()
        if days_left is None:
            return False

        return 0 < days_left <= days_threshold

    def validate(self) -> List[str]:
        """Validate supplier data"""
        errors = []

        if not self.name:
            errors.append("Supplier name is required")

        if not self.supplier_code:
            errors.append("Supplier code is required")

        if not self.tenant_id:
            errors.append("Tenant ID is required")

        if self.credit_limit < 0:
            errors.append("Credit limit cannot be negative")

        if self.current_balance < 0:
            errors.append("Current balance cannot be negative")

        if self.minimum_order_amount < 0:
            errors.append("Minimum order amount cannot be negative")

        if self.on_time_delivery_rate < 0 or self.on_time_delivery_rate > 100:
            errors.append("On-time delivery rate must be between 0 and 100")

        if self.quality_rating < 0 or self.quality_rating > 5:
            errors.append("Quality rating must be between 0 and 5")

        if self.license_expiry and self.license_expiry < date.today():
            errors.append("License has expired")

        return errors