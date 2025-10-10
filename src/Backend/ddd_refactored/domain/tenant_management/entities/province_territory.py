"""
Province/Territory Entity
Following DDD Architecture Document Section 2.1
"""

from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from typing import Optional, Dict, Any
from uuid import UUID, uuid4
from enum import Enum

from ....shared.domain_base import Entity


class ProvinceType(str, Enum):
    """Canadian jurisdiction types"""
    PROVINCE = "province"
    TERRITORY = "territory"


@dataclass
class ProvinceTerritory(Entity):
    """
    Province or Territory entity
    As defined in DDD_ARCHITECTURE_REFACTORING.md Section 2.1
    """
    code: str = ""  # e.g., "ON", "BC", "QC"
    name: str = ""
    type: ProvinceType = ProvinceType.PROVINCE
    tax_rate: Decimal = Decimal("13.00")
    min_age: int = 19
    regulatory_body: Optional[str] = None
    license_prefix: Optional[str] = None
    delivery_allowed: bool = True
    pickup_allowed: bool = True
    settings: Dict[str, Any] = field(default_factory=dict)

    def is_valid_for_cannabis_sales(self) -> bool:
        """Check if province/territory allows cannabis sales"""
        return self.regulatory_body is not None

    def get_total_tax_rate(self) -> Decimal:
        """Get total tax rate including federal and provincial"""
        # In Canada, cannabis has additional excise duties
        # This is simplified - actual implementation would be more complex
        return self.tax_rate

    def validate_license_format(self, license_number: str) -> bool:
        """Validate license number format for this province"""
        if not self.license_prefix:
            return True  # No specific format required
        return license_number.startswith(self.license_prefix)

    def update_tax_rate(self, new_rate: Decimal):
        """Update the tax rate"""
        if new_rate < 0 or new_rate > 100:
            raise ValueError("Tax rate must be between 0 and 100")
        self.tax_rate = new_rate
        self.mark_as_modified()