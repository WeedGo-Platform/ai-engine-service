"""
ProductAttributes Value Objects
Following DDD Architecture Document Section 2.3
"""

from dataclasses import dataclass
from decimal import Decimal
from typing import Optional, List, Dict, Any
from enum import Enum

from ....shared.domain_base import ValueObject


class ProductForm(str, Enum):
    """Cannabis product forms"""
    DRIED_FLOWER = "dried_flower"
    PRE_ROLL = "pre_roll"
    MILLED = "milled"
    OIL = "oil"
    CAPSULE = "capsule"
    SPRAY = "spray"
    EDIBLE = "edible"
    BEVERAGE = "beverage"
    TOPICAL = "topical"
    CONCENTRATE = "concentrate"
    VAPE_CARTRIDGE = "vape_cartridge"
    VAPE_DISPOSABLE = "vape_disposable"
    SEEDS = "seeds"
    ACCESSORIES = "accessories"
    OTHER = "other"


class UnitOfMeasure(str, Enum):
    """Units of measure for cannabis products"""
    GRAM = "g"
    MILLIGRAM = "mg"
    MILLILITER = "ml"
    UNIT = "unit"
    PACK = "pack"
    EACH = "each"


@dataclass(frozen=True)
class TerpeneProfile(ValueObject):
    """
    TerpeneProfile Value Object - Cannabis terpene composition
    Immutable value object representing terpene profiles
    """
    primary_terpenes: List[str]
    terpene_percentages: Optional[Dict[str, Decimal]] = None
    aroma_notes: Optional[List[str]] = None
    flavor_notes: Optional[List[str]] = None

    def get_dominant_terpene(self) -> Optional[str]:
        """Get the dominant terpene"""
        if self.primary_terpenes:
            return self.primary_terpenes[0]
        return None

    def has_terpene(self, terpene_name: str) -> bool:
        """Check if profile contains a specific terpene"""
        return terpene_name.lower() in [t.lower() for t in self.primary_terpenes]

    def get_common_effects(self) -> List[str]:
        """Get common effects based on terpene profile"""
        terpene_effects = {
            "limonene": ["uplifting", "stress-relief", "mood-enhancer"],
            "myrcene": ["sedating", "relaxing", "couch-lock"],
            "pinene": ["alertness", "memory-retention", "anti-inflammatory"],
            "linalool": ["calming", "anti-anxiety", "sedative"],
            "caryophyllene": ["anti-inflammatory", "pain-relief", "stress-relief"],
            "humulene": ["appetite-suppressant", "anti-inflammatory"],
            "terpinolene": ["uplifting", "energizing", "creative"],
            "ocimene": ["decongestant", "antiviral", "antifungal"]
        }

        effects = []
        for terpene in self.primary_terpenes:
            terpene_lower = terpene.lower()
            if terpene_lower in terpene_effects:
                effects.extend(terpene_effects[terpene_lower])

        return list(set(effects))  # Remove duplicates

    def to_display_string(self) -> str:
        """Get user-friendly display string"""
        if not self.primary_terpenes:
            return "Unknown terpene profile"
        return f"Dominant: {', '.join(self.primary_terpenes[:3])}"


@dataclass(frozen=True)
class CannabinoidRange(ValueObject):
    """
    CannabinoidRange Value Object - THC/CBD content ranges
    Immutable value object for cannabinoid content
    """
    thc_min: Optional[Decimal]
    thc_max: Optional[Decimal]
    cbd_min: Optional[Decimal]
    cbd_max: Optional[Decimal]
    total_cannabinoids: Optional[Decimal] = None

    def get_thc_range_string(self) -> str:
        """Get THC range as display string"""
        if self.thc_min is None and self.thc_max is None:
            return "N/A"
        if self.thc_min == self.thc_max:
            return f"{self.thc_min}%"
        return f"{self.thc_min or 0}%-{self.thc_max or 0}%"

    def get_cbd_range_string(self) -> str:
        """Get CBD range as display string"""
        if self.cbd_min is None and self.cbd_max is None:
            return "N/A"
        if self.cbd_min == self.cbd_max:
            return f"{self.cbd_min}%"
        return f"{self.cbd_min or 0}%-{self.cbd_max or 0}%"

    def is_high_thc(self) -> bool:
        """Check if this is a high-THC product (>20%)"""
        return self.thc_max is not None and self.thc_max > Decimal("20")

    def is_high_cbd(self) -> bool:
        """Check if this is a high-CBD product (>10%)"""
        return self.cbd_max is not None and self.cbd_max > Decimal("10")

    def is_balanced(self) -> bool:
        """Check if THC:CBD ratio is balanced (between 0.5:1 and 2:1)"""
        if not (self.thc_max and self.cbd_max):
            return False
        if self.cbd_max == 0:
            return False
        ratio = self.thc_max / self.cbd_max
        return Decimal("0.5") <= ratio <= Decimal("2")

    def get_potency_level(self) -> str:
        """Get potency level description"""
        if self.thc_max is None:
            return "Unknown"
        if self.thc_max < Decimal("10"):
            return "Mild"
        elif self.thc_max < Decimal("17"):
            return "Medium"
        elif self.thc_max < Decimal("22"):
            return "Strong"
        else:
            return "Very Strong"

    def get_total_mg(self, quantity_g: Decimal) -> Dict[str, Decimal]:
        """Calculate total mg of cannabinoids for given quantity"""
        result = {}
        if self.thc_max:
            result['thc_mg'] = (self.thc_max / 100) * quantity_g * 1000
        if self.cbd_max:
            result['cbd_mg'] = (self.cbd_max / 100) * quantity_g * 1000
        return result


@dataclass(frozen=True)
class ProductAttributes(ValueObject):
    """
    ProductAttributes Value Object - Complete product characteristics
    Immutable value object aggregating all product attributes
    """
    product_form: ProductForm
    cannabinoid_range: CannabinoidRange
    terpene_profile: Optional[TerpeneProfile] = None
    volume_ml: Optional[Decimal] = None
    pieces: Optional[int] = None
    unit_of_measure: UnitOfMeasure = UnitOfMeasure.GRAM
    allergens: Optional[List[str]] = None
    ingredients: Optional[List[str]] = None

    def is_edible(self) -> bool:
        """Check if product is an edible"""
        return self.product_form in [
            ProductForm.EDIBLE,
            ProductForm.BEVERAGE,
            ProductForm.CAPSULE
        ]

    def is_inhalable(self) -> bool:
        """Check if product is for inhalation"""
        return self.product_form in [
            ProductForm.DRIED_FLOWER,
            ProductForm.PRE_ROLL,
            ProductForm.MILLED,
            ProductForm.VAPE_CARTRIDGE,
            ProductForm.VAPE_DISPOSABLE,
            ProductForm.CONCENTRATE
        ]

    def is_topical(self) -> bool:
        """Check if product is topical"""
        return self.product_form == ProductForm.TOPICAL

    def requires_device(self) -> bool:
        """Check if product requires a device to consume"""
        return self.product_form in [
            ProductForm.VAPE_CARTRIDGE,
            ProductForm.CONCENTRATE
        ]

    def get_onset_time(self) -> str:
        """Get typical onset time for effects"""
        onset_map = {
            ProductForm.DRIED_FLOWER: "5-10 minutes",
            ProductForm.PRE_ROLL: "5-10 minutes",
            ProductForm.MILLED: "5-10 minutes",
            ProductForm.VAPE_CARTRIDGE: "2-5 minutes",
            ProductForm.VAPE_DISPOSABLE: "2-5 minutes",
            ProductForm.CONCENTRATE: "2-5 minutes",
            ProductForm.OIL: "30-120 minutes",
            ProductForm.CAPSULE: "30-120 minutes",
            ProductForm.SPRAY: "15-45 minutes",
            ProductForm.EDIBLE: "30-120 minutes",
            ProductForm.BEVERAGE: "15-60 minutes",
            ProductForm.TOPICAL: "15-30 minutes (localized)",
        }
        return onset_map.get(self.product_form, "Varies")

    def get_duration(self) -> str:
        """Get typical effect duration"""
        duration_map = {
            ProductForm.DRIED_FLOWER: "1-3 hours",
            ProductForm.PRE_ROLL: "1-3 hours",
            ProductForm.MILLED: "1-3 hours",
            ProductForm.VAPE_CARTRIDGE: "1-2 hours",
            ProductForm.VAPE_DISPOSABLE: "1-2 hours",
            ProductForm.CONCENTRATE: "1-3 hours",
            ProductForm.OIL: "4-8 hours",
            ProductForm.CAPSULE: "4-8 hours",
            ProductForm.SPRAY: "2-4 hours",
            ProductForm.EDIBLE: "4-8 hours",
            ProductForm.BEVERAGE: "2-6 hours",
            ProductForm.TOPICAL: "2-4 hours (localized)",
        }
        return duration_map.get(self.product_form, "Varies")

    def has_allergen(self, allergen: str) -> bool:
        """Check if product contains a specific allergen"""
        if not self.allergens:
            return False
        return allergen.lower() in [a.lower() for a in self.allergens]

    def get_serving_size(self) -> str:
        """Get recommended serving size"""
        if self.product_form == ProductForm.EDIBLE and self.pieces:
            return f"1/{self.pieces} package"
        elif self.product_form == ProductForm.BEVERAGE and self.volume_ml:
            return f"{self.volume_ml}ml"
        elif self.product_form == ProductForm.CAPSULE and self.pieces:
            return "1 capsule"
        elif self.product_form in [ProductForm.DRIED_FLOWER, ProductForm.MILLED]:
            return "0.25g (starter dose)"
        elif self.product_form == ProductForm.PRE_ROLL:
            return "1/3 to 1/2 joint"
        return "See package instructions"

    def validate(self) -> List[str]:
        """Validate product attributes"""
        errors = []

        # Edibles must have pieces count
        if self.is_edible() and self.product_form != ProductForm.BEVERAGE:
            if not self.pieces or self.pieces <= 0:
                errors.append("Edible products must specify number of pieces")

        # Beverages must have volume
        if self.product_form == ProductForm.BEVERAGE:
            if not self.volume_ml or self.volume_ml <= 0:
                errors.append("Beverage products must specify volume in ml")

        # Vape products should have volume
        if self.product_form in [ProductForm.VAPE_CARTRIDGE, ProductForm.VAPE_DISPOSABLE]:
            if not self.volume_ml:
                errors.append("Vape products should specify volume in ml")

        return errors