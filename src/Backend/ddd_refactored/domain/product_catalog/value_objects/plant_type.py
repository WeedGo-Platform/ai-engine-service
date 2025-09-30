"""
PlantType Value Object
Following DDD Architecture Document Section 2.3
"""

from dataclasses import dataclass
from enum import Enum
from typing import List

from ....shared.domain_base import ValueObject


class PlantTypeEnum(str, Enum):
    """Cannabis plant types"""
    SATIVA = "sativa"
    INDICA = "indica"
    HYBRID = "hybrid"
    HYBRID_SATIVA_DOMINANT = "hybrid_sativa_dominant"
    HYBRID_INDICA_DOMINANT = "hybrid_indica_dominant"
    CBD_DOMINANT = "cbd_dominant"
    BALANCED = "balanced"  # Balanced THC/CBD
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class PlantType(ValueObject):
    """
    PlantType Value Object - Cannabis plant classification
    Immutable value object representing the genetic classification of cannabis
    """
    type: PlantTypeEnum

    @classmethod
    def from_string(cls, plant_type_str: str) -> 'PlantType':
        """Create PlantType from string representation"""
        normalized = plant_type_str.lower().strip().replace(' ', '_').replace('-', '_')

        # Map common variations
        mappings = {
            'sativa': PlantTypeEnum.SATIVA,
            's': PlantTypeEnum.SATIVA,
            'indica': PlantTypeEnum.INDICA,
            'i': PlantTypeEnum.INDICA,
            'hybrid': PlantTypeEnum.HYBRID,
            'h': PlantTypeEnum.HYBRID,
            'sativa_dominant': PlantTypeEnum.HYBRID_SATIVA_DOMINANT,
            'hybrid_sativa': PlantTypeEnum.HYBRID_SATIVA_DOMINANT,
            'indica_dominant': PlantTypeEnum.HYBRID_INDICA_DOMINANT,
            'hybrid_indica': PlantTypeEnum.HYBRID_INDICA_DOMINANT,
            'cbd': PlantTypeEnum.CBD_DOMINANT,
            'cbd_dominant': PlantTypeEnum.CBD_DOMINANT,
            'balanced': PlantTypeEnum.BALANCED,
            '1:1': PlantTypeEnum.BALANCED,
        }

        plant_type_enum = mappings.get(normalized, PlantTypeEnum.UNKNOWN)
        return cls(type=plant_type_enum)

    def is_sativa_leaning(self) -> bool:
        """Check if plant type leans towards sativa effects"""
        return self.type in [
            PlantTypeEnum.SATIVA,
            PlantTypeEnum.HYBRID_SATIVA_DOMINANT
        ]

    def is_indica_leaning(self) -> bool:
        """Check if plant type leans towards indica effects"""
        return self.type in [
            PlantTypeEnum.INDICA,
            PlantTypeEnum.HYBRID_INDICA_DOMINANT
        ]

    def is_hybrid(self) -> bool:
        """Check if plant type is any form of hybrid"""
        return self.type in [
            PlantTypeEnum.HYBRID,
            PlantTypeEnum.HYBRID_SATIVA_DOMINANT,
            PlantTypeEnum.HYBRID_INDICA_DOMINANT,
            PlantTypeEnum.BALANCED
        ]

    def is_cbd_focused(self) -> bool:
        """Check if plant type is CBD-focused"""
        return self.type in [
            PlantTypeEnum.CBD_DOMINANT,
            PlantTypeEnum.BALANCED
        ]

    def get_typical_effects(self) -> List[str]:
        """Get typical effects associated with this plant type"""
        effects_map = {
            PlantTypeEnum.SATIVA: ["energizing", "uplifting", "creative", "focused"],
            PlantTypeEnum.INDICA: ["relaxing", "sedating", "calming", "body-high"],
            PlantTypeEnum.HYBRID: ["balanced", "versatile", "mood-dependent"],
            PlantTypeEnum.HYBRID_SATIVA_DOMINANT: ["energizing", "uplifting", "mild-relaxation"],
            PlantTypeEnum.HYBRID_INDICA_DOMINANT: ["relaxing", "calming", "mild-energy"],
            PlantTypeEnum.CBD_DOMINANT: ["non-intoxicating", "therapeutic", "clear-headed"],
            PlantTypeEnum.BALANCED: ["mild-high", "therapeutic", "functional"],
            PlantTypeEnum.UNKNOWN: []
        }
        return effects_map.get(self.type, [])

    def get_typical_use_time(self) -> str:
        """Get typical time of day for use"""
        time_map = {
            PlantTypeEnum.SATIVA: "daytime",
            PlantTypeEnum.INDICA: "evening/nighttime",
            PlantTypeEnum.HYBRID: "anytime",
            PlantTypeEnum.HYBRID_SATIVA_DOMINANT: "daytime/afternoon",
            PlantTypeEnum.HYBRID_INDICA_DOMINANT: "evening",
            PlantTypeEnum.CBD_DOMINANT: "anytime",
            PlantTypeEnum.BALANCED: "anytime",
            PlantTypeEnum.UNKNOWN: "varies"
        }
        return time_map.get(self.type, "varies")

    def to_display_string(self) -> str:
        """Get user-friendly display string"""
        display_map = {
            PlantTypeEnum.SATIVA: "Sativa",
            PlantTypeEnum.INDICA: "Indica",
            PlantTypeEnum.HYBRID: "Hybrid",
            PlantTypeEnum.HYBRID_SATIVA_DOMINANT: "Sativa-Dominant Hybrid",
            PlantTypeEnum.HYBRID_INDICA_DOMINANT: "Indica-Dominant Hybrid",
            PlantTypeEnum.CBD_DOMINANT: "CBD Dominant",
            PlantTypeEnum.BALANCED: "Balanced THC/CBD",
            PlantTypeEnum.UNKNOWN: "Unknown"
        }
        return display_map.get(self.type, str(self.type))

    def __str__(self) -> str:
        return self.to_display_string()