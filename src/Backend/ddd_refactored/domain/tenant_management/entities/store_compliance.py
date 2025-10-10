"""
StoreCompliance Entity
Following DDD Architecture Document Section 2.1
"""

from dataclasses import dataclass, field
from datetime import datetime, date, timedelta
from typing import Optional, List, Dict, Any
from uuid import UUID, uuid4
from enum import Enum

from ....shared.domain_base import Entity, BusinessRuleViolation, DomainEvent


class ComplianceStatus(str, Enum):
    """Compliance status"""
    COMPLIANT = "compliant"
    WARNING = "warning"
    NON_COMPLIANT = "non_compliant"
    UNDER_REVIEW = "under_review"


class DocumentType(str, Enum):
    """Compliance document types"""
    RETAIL_LICENSE = "retail_license"
    BUSINESS_LICENSE = "business_license"
    CANNABIS_LICENSE = "cannabis_license"
    FIRE_SAFETY_CERTIFICATE = "fire_safety_certificate"
    HEALTH_PERMIT = "health_permit"
    INSURANCE_POLICY = "insurance_policy"
    TAX_REGISTRATION = "tax_registration"
    OTHER = "other"


class InspectionType(str, Enum):
    """Types of compliance inspections"""
    ROUTINE = "routine"
    RANDOM = "random"
    COMPLAINT_BASED = "complaint_based"
    FOLLOW_UP = "follow_up"
    INITIAL = "initial"


# Domain Events
class ComplianceCheckFailed(DomainEvent):
    def __init__(self, compliance_id: UUID, store_id: UUID, issues: List[str]):
        super().__init__(compliance_id)
        self.store_id = store_id
        self.issues = issues

    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()
        data.update({
            'store_id': str(self.store_id),
            'issues': self.issues
        })
        return data


class DocumentExpiring(DomainEvent):
    def __init__(self, compliance_id: UUID, document_type: str, expiry_date: date):
        super().__init__(compliance_id)
        self.document_type = document_type
        self.expiry_date = expiry_date

    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()
        data.update({
            'document_type': self.document_type,
            'expiry_date': self.expiry_date.isoformat()
        })
        return data


@dataclass
class ComplianceDocument:
    """Value object for compliance documents"""
    id: UUID = field(default_factory=uuid4)
    type: DocumentType = DocumentType.OTHER
    name: str = ""
    number: Optional[str] = None
    issuer: Optional[str] = None
    issue_date: Optional[date] = None
    expiry_date: Optional[date] = None
    file_url: Optional[str] = None
    verified: bool = False
    verified_by: Optional[UUID] = None
    verified_at: Optional[datetime] = None
    notes: Optional[str] = None

    def is_valid(self) -> bool:
        """Check if document is valid"""
        if not self.verified:
            return False
        if self.expiry_date:
            return self.expiry_date > date.today()
        return True

    def is_expiring_soon(self, days: int = 30) -> bool:
        """Check if document is expiring soon"""
        if not self.expiry_date:
            return False
        days_until_expiry = (self.expiry_date - date.today()).days
        return 0 < days_until_expiry <= days


@dataclass
class ComplianceInspection:
    """Value object for compliance inspections"""
    id: UUID = field(default_factory=uuid4)
    type: InspectionType = InspectionType.ROUTINE
    inspector_name: Optional[str] = None
    inspector_id: Optional[str] = None
    inspection_date: datetime = field(default_factory=datetime.utcnow)
    passed: bool = True
    score: Optional[int] = None  # 0-100
    findings: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    follow_up_required: bool = False
    follow_up_date: Optional[date] = None
    report_url: Optional[str] = None


@dataclass
class StoreCompliance(Entity):
    """
    StoreCompliance Entity - Manages store regulatory compliance
    As defined in DDD_ARCHITECTURE_REFACTORING.md Section 2.1
    """
    store_id: UUID = field(default_factory=uuid4)
    status: ComplianceStatus = ComplianceStatus.COMPLIANT

    # License Information
    retail_license_number: Optional[str] = None
    retail_license_expiry: Optional[date] = None
    cannabis_license_number: Optional[str] = None
    cannabis_license_expiry: Optional[date] = None
    business_license_number: Optional[str] = None
    business_license_expiry: Optional[date] = None

    # Documents
    documents: List[ComplianceDocument] = field(default_factory=list)

    # Inspections
    inspections: List[ComplianceInspection] = field(default_factory=list)
    last_inspection_date: Optional[datetime] = None
    next_inspection_date: Optional[date] = None

    # Compliance Scores
    overall_compliance_score: int = 100  # 0-100
    health_safety_score: int = 100
    regulatory_score: int = 100
    operational_score: int = 100

    # Issues & Actions
    open_issues: List[Dict[str, Any]] = field(default_factory=list)
    compliance_actions: List[Dict[str, Any]] = field(default_factory=list)
    violations: List[Dict[str, Any]] = field(default_factory=list)

    # Age Verification
    age_verification_enabled: bool = True
    age_verification_method: str = "id_scan"  # id_scan, manual, both
    failed_age_checks: int = 0
    successful_age_checks: int = 0

    # Product Compliance
    max_thc_percentage: float = 30.0  # Provincial limit
    max_purchase_amount_g: float = 30.0  # Daily limit in grams
    restricted_hours: Dict[str, Any] = field(default_factory=dict)

    # Training Requirements
    staff_training_requirements: List[str] = field(default_factory=list)
    staff_certifications_required: List[str] = field(default_factory=list)

    # Reporting
    last_report_submitted: Optional[date] = None
    next_report_due: Optional[date] = None
    reports_submitted: int = 0

    # Metadata
    notes: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def create(
        cls,
        store_id: UUID,
        retail_license_number: Optional[str] = None,
        cannabis_license_number: Optional[str] = None
    ) -> 'StoreCompliance':
        """Factory method to create store compliance record"""
        compliance = cls(
            store_id=store_id,
            retail_license_number=retail_license_number,
            cannabis_license_number=cannabis_license_number
        )

        # Set default training requirements
        compliance.staff_training_requirements = [
            'Cannabis Product Knowledge',
            'Age Verification',
            'Responsible Sales',
            'Security Procedures',
            'Health & Safety'
        ]

        # Set default certifications
        compliance.staff_certifications_required = [
            'Smart Serve',
            'CannSell'
        ]

        # Set default restricted hours (example: no sales 10pm-9am)
        compliance.restricted_hours = {
            'no_sales_start': '22:00',
            'no_sales_end': '09:00'
        }

        return compliance

    def add_document(
        self,
        doc_type: DocumentType,
        name: str,
        number: Optional[str] = None,
        expiry_date: Optional[date] = None,
        file_url: Optional[str] = None
    ) -> ComplianceDocument:
        """Add a compliance document"""
        document = ComplianceDocument(
            type=doc_type,
            name=name,
            number=number,
            issue_date=date.today(),
            expiry_date=expiry_date,
            file_url=file_url
        )

        self.documents.append(document)
        self.mark_as_modified()

        # Check if expiring soon
        if document.is_expiring_soon():
            self.add_domain_event(DocumentExpiring(
                compliance_id=self.id,
                document_type=doc_type.value,
                expiry_date=expiry_date
            ))

        return document

    def verify_document(self, document_id: UUID, verified_by: UUID) -> bool:
        """Verify a compliance document"""
        for doc in self.documents:
            if doc.id == document_id:
                doc.verified = True
                doc.verified_by = verified_by
                doc.verified_at = datetime.utcnow()
                self.mark_as_modified()
                self._update_compliance_status()
                return True
        return False

    def record_inspection(
        self,
        inspection_type: InspectionType,
        passed: bool,
        score: Optional[int] = None,
        findings: Optional[List[str]] = None,
        follow_up_required: bool = False
    ) -> ComplianceInspection:
        """Record a compliance inspection"""
        inspection = ComplianceInspection(
            type=inspection_type,
            inspection_date=datetime.utcnow(),
            passed=passed,
            score=score,
            findings=findings or [],
            follow_up_required=follow_up_required
        )

        if follow_up_required:
            inspection.follow_up_date = date.today() + timedelta(days=30)

        self.inspections.append(inspection)
        self.last_inspection_date = inspection.inspection_date

        # Update next inspection date
        if inspection_type == InspectionType.ROUTINE:
            self.next_inspection_date = date.today() + timedelta(days=180)  # 6 months

        # Update compliance scores
        if score is not None:
            self.overall_compliance_score = score

        self._update_compliance_status()
        self.mark_as_modified()

        # Raise event if inspection failed
        if not passed:
            self.add_domain_event(ComplianceCheckFailed(
                compliance_id=self.id,
                store_id=self.store_id,
                issues=findings or []
            ))

        return inspection

    def add_issue(
        self,
        category: str,
        description: str,
        severity: str = "low",  # low, medium, high, critical
        due_date: Optional[date] = None
    ):
        """Add a compliance issue"""
        issue = {
            'id': str(uuid4()),
            'category': category,
            'description': description,
            'severity': severity,
            'created_at': datetime.utcnow().isoformat(),
            'due_date': due_date.isoformat() if due_date else None,
            'status': 'open'
        }

        self.open_issues.append(issue)
        self._update_compliance_status()
        self.mark_as_modified()

    def resolve_issue(self, issue_id: str, resolution: str):
        """Resolve a compliance issue"""
        for issue in self.open_issues:
            if issue['id'] == issue_id:
                issue['status'] = 'resolved'
                issue['resolution'] = resolution
                issue['resolved_at'] = datetime.utcnow().isoformat()
                self._update_compliance_status()
                self.mark_as_modified()
                return True
        return False

    def add_violation(
        self,
        violation_type: str,
        description: str,
        fine_amount: Optional[float] = None,
        corrective_action: Optional[str] = None
    ):
        """Add a compliance violation"""
        violation = {
            'id': str(uuid4()),
            'type': violation_type,
            'description': description,
            'date': datetime.utcnow().isoformat(),
            'fine_amount': fine_amount,
            'corrective_action': corrective_action,
            'status': 'active'
        }

        self.violations.append(violation)
        self.status = ComplianceStatus.NON_COMPLIANT
        self.mark_as_modified()

    def record_age_verification(self, successful: bool):
        """Record an age verification attempt"""
        if successful:
            self.successful_age_checks += 1
        else:
            self.failed_age_checks += 1

        # Check if too many failures
        failure_rate = self.failed_age_checks / (self.successful_age_checks + self.failed_age_checks)
        if failure_rate > 0.05:  # More than 5% failure rate
            self.add_issue(
                category="Age Verification",
                description=f"High age verification failure rate: {failure_rate:.1%}",
                severity="high"
            )

        self.mark_as_modified()

    def check_document_expiry(self) -> List[ComplianceDocument]:
        """Check for expiring documents"""
        expiring = []
        for doc in self.documents:
            if doc.is_expiring_soon(days=60):
                expiring.append(doc)

                # Raise event for expiring document
                self.add_domain_event(DocumentExpiring(
                    compliance_id=self.id,
                    document_type=doc.type.value,
                    expiry_date=doc.expiry_date
                ))

        return expiring

    def check_license_expiry(self) -> List[str]:
        """Check for expiring licenses"""
        warnings = []
        today = date.today()

        if self.retail_license_expiry:
            days_until = (self.retail_license_expiry - today).days
            if 0 < days_until <= 60:
                warnings.append(f"Retail license expiring in {days_until} days")

        if self.cannabis_license_expiry:
            days_until = (self.cannabis_license_expiry - today).days
            if 0 < days_until <= 60:
                warnings.append(f"Cannabis license expiring in {days_until} days")

        if self.business_license_expiry:
            days_until = (self.business_license_expiry - today).days
            if 0 < days_until <= 60:
                warnings.append(f"Business license expiring in {days_until} days")

        return warnings

    def update_license(
        self,
        license_type: str,
        number: str,
        expiry_date: date
    ):
        """Update license information"""
        if license_type == "retail":
            self.retail_license_number = number
            self.retail_license_expiry = expiry_date
        elif license_type == "cannabis":
            self.cannabis_license_number = number
            self.cannabis_license_expiry = expiry_date
        elif license_type == "business":
            self.business_license_number = number
            self.business_license_expiry = expiry_date
        else:
            raise BusinessRuleViolation(f"Unknown license type: {license_type}")

        self._update_compliance_status()
        self.mark_as_modified()

    def submit_report(self, report_type: str, report_url: Optional[str] = None):
        """Submit a compliance report"""
        self.last_report_submitted = date.today()
        self.reports_submitted += 1

        # Calculate next report due date (monthly)
        self.next_report_due = date.today() + timedelta(days=30)

        if report_url:
            self.metadata[f'last_{report_type}_report_url'] = report_url

        self.mark_as_modified()

    def _update_compliance_status(self):
        """Update overall compliance status"""
        # Check for critical issues
        critical_issues = [i for i in self.open_issues if i.get('severity') == 'critical']
        if critical_issues:
            self.status = ComplianceStatus.NON_COMPLIANT
            return

        # Check for expired documents
        expired_docs = [d for d in self.documents if d.expiry_date and d.expiry_date < date.today()]
        if expired_docs:
            self.status = ComplianceStatus.NON_COMPLIANT
            return

        # Check for active violations
        active_violations = [v for v in self.violations if v.get('status') == 'active']
        if active_violations:
            self.status = ComplianceStatus.NON_COMPLIANT
            return

        # Check for high severity issues
        high_issues = [i for i in self.open_issues if i.get('severity') == 'high']
        if high_issues:
            self.status = ComplianceStatus.WARNING
            return

        # Check compliance scores
        if any([
            self.overall_compliance_score < 70,
            self.health_safety_score < 70,
            self.regulatory_score < 70,
            self.operational_score < 70
        ]):
            self.status = ComplianceStatus.WARNING
            return

        # Otherwise compliant
        self.status = ComplianceStatus.COMPLIANT

    def is_compliant(self) -> bool:
        """Check if store is compliant"""
        return self.status == ComplianceStatus.COMPLIANT

    def get_compliance_score(self) -> int:
        """Get overall compliance score"""
        scores = [
            self.overall_compliance_score,
            self.health_safety_score,
            self.regulatory_score,
            self.operational_score
        ]
        return sum(scores) // len(scores)

    def validate(self) -> List[str]:
        """Validate compliance data"""
        errors = []

        if not self.store_id:
            errors.append("Store ID is required")

        if self.overall_compliance_score < 0 or self.overall_compliance_score > 100:
            errors.append("Compliance score must be between 0 and 100")

        if self.max_thc_percentage < 0 or self.max_thc_percentage > 100:
            errors.append("THC percentage must be between 0 and 100")

        if self.max_purchase_amount_g < 0:
            errors.append("Purchase amount cannot be negative")

        return errors