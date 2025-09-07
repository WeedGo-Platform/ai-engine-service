"""Dispensary-specific tools for cannabis operations"""

from typing import Dict, Any, List
from .base import ITool, ToolResult
import logging

logger = logging.getLogger(__name__)

class DispensarySearchTool(ITool):
    """Tool for searching cannabis products"""
    
    def name(self) -> str:
        return "dispensary_search"
    
    async def execute(self, query: str = None, **kwargs) -> ToolResult:
        """Search for cannabis products"""
        # Mock data for testing
        products = [
            {"name": "Blue Dream", "type": "Sativa", "thc": 18.5, "price": 35},
            {"name": "OG Kush", "type": "Indica", "thc": 22.0, "price": 40},
            {"name": "Gorilla Glue", "type": "Hybrid", "thc": 25.0, "price": 45}
        ]
        
        if query:
            # Simple filter
            products = [p for p in products if query.lower() in p["name"].lower()]
        
        return ToolResult(success=True, data=products)

class DosageCalculatorTool(ITool):
    """Tool for calculating THC/CBD dosage"""
    
    def name(self) -> str:
        return "dosage_calculator"
    
    async def execute(self, weight_kg: float = 70, tolerance: str = "low", **kwargs) -> ToolResult:
        """Calculate recommended dosage"""
        base_dose = {
            "low": 2.5,
            "medium": 5.0,
            "high": 10.0
        }
        
        recommended = base_dose.get(tolerance, 2.5)
        
        return ToolResult(
            success=True, 
            data={
                "recommended_mg": recommended,
                "notes": f"Start with {recommended}mg THC for {tolerance} tolerance"
            }
        )

class StrainComparisonTool(ITool):
    """Tool for comparing cannabis strains"""
    
    def name(self) -> str:
        return "strain_comparison"
    
    async def execute(self, strain1: str, strain2: str, **kwargs) -> ToolResult:
        """Compare two strains"""
        # Mock comparison
        return ToolResult(
            success=True,
            data={
                "comparison": f"Comparing {strain1} vs {strain2}",
                "recommendation": "Both are excellent choices"
            }
        )