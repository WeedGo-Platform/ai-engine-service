"""Dispensary-specific tool implementations"""

from typing import Dict, List, Optional
from services.tools.base import ITool, ToolResult, SearchTool
import logging

logger = logging.getLogger(__name__)

class DispensarySearchTool(SearchTool):
    """Enhanced search tool for dispensary with strain-specific features"""
    
    @property
    def description(self) -> str:
        return "Search cannabis products with strain details, THC/CBD levels, and effects"
    
    @property
    def parameters(self) -> Dict:
        return {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Product search query"
                },
                "strain_type": {
                    "type": "string",
                    "enum": ["sativa", "indica", "hybrid", "any"],
                    "description": "Cannabis strain type"
                },
                "thc_min": {
                    "type": "number",
                    "description": "Minimum THC percentage"
                },
                "thc_max": {
                    "type": "number",
                    "description": "Maximum THC percentage"
                },
                "effects": {
                    "type": "array",
                    "items": {
                        "type": "string",
                        "enum": ["relaxing", "energizing", "creative", "focus", "sleep", "pain-relief"]
                    },
                    "description": "Desired effects"
                },
                "category": {
                    "type": "string",
                    "enum": ["flower", "edibles", "pre-rolls", "concentrates", "vapes", "tinctures", "topicals"],
                    "description": "Product category"
                },
                "limit": {
                    "type": "integer",
                    "default": 5,
                    "description": "Maximum number of results"
                }
            },
            "required": ["query"]
        }
    
    async def execute(self, query: str, strain_type: str = "any", 
                     thc_min: float = None, thc_max: float = None,
                     effects: List[str] = None, category: str = "all", 
                     limit: int = 5, **kwargs) -> ToolResult:
        """Execute enhanced product search"""
        try:
            # Enhanced mock data with strain information
            products = [
                {
                    "name": "Blue Dream",
                    "category": "flower",
                    "strain_type": "sativa",
                    "thc": 22,
                    "cbd": 0.5,
                    "price": "$45/eighth",
                    "effects": ["creative", "energizing", "focus"],
                    "description": "Sweet berry aroma, cerebral high"
                },
                {
                    "name": "Northern Lights",
                    "category": "flower", 
                    "strain_type": "indica",
                    "thc": 19,
                    "cbd": 0.2,
                    "price": "$40/eighth",
                    "effects": ["relaxing", "sleep", "pain-relief"],
                    "description": "Pine aroma, full body relaxation"
                },
                {
                    "name": "Gelato Pre-Roll",
                    "category": "pre-rolls",
                    "strain_type": "hybrid",
                    "thc": 20,
                    "cbd": 0.3,
                    "price": "$15",
                    "effects": ["relaxing", "creative"],
                    "description": "Sweet citrus, balanced effects"
                },
                {
                    "name": "CBD Gummies",
                    "category": "edibles",
                    "strain_type": "any",
                    "thc": 0,
                    "cbd": 25,
                    "price": "$30/pack",
                    "effects": ["pain-relief", "relaxing"],
                    "description": "25mg CBD per gummy, no THC"
                }
            ]
            
            # Filter based on criteria
            results = []
            for product in products:
                # Check query match
                if query.lower() not in product["name"].lower() and query != "*":
                    continue
                
                # Check strain type
                if strain_type != "any" and product["strain_type"] != strain_type:
                    continue
                
                # Check THC range
                if thc_min and product["thc"] < thc_min:
                    continue
                if thc_max and product["thc"] > thc_max:
                    continue
                
                # Check effects
                if effects:
                    if not any(eff in product["effects"] for eff in effects):
                        continue
                
                # Check category
                if category != "all" and product["category"] != category:
                    continue
                
                results.append(product)
                
                if len(results) >= limit:
                    break
            
            return ToolResult(
                success=True,
                data=results,
                metadata={
                    "query": query,
                    "filters": {
                        "strain_type": strain_type,
                        "thc_range": f"{thc_min or 0}-{thc_max or 100}%",
                        "effects": effects,
                        "category": category
                    },
                    "count": len(results)
                }
            )
        except Exception as e:
            return ToolResult(success=False, data=None, error=str(e))

class DosageCalculatorTool(ITool):
    """Calculate recommended dosage for edibles"""
    
    @property
    def name(self) -> str:
        return "dosage_calculator"
    
    @property
    def description(self) -> str:
        return "Calculate recommended cannabis edible dosage based on experience level"
    
    @property
    def parameters(self) -> Dict:
        return {
            "type": "object",
            "properties": {
                "experience_level": {
                    "type": "string",
                    "enum": ["beginner", "occasional", "regular", "experienced"],
                    "description": "User's cannabis experience level"
                },
                "product_thc_mg": {
                    "type": "number",
                    "description": "THC content per serving in mg"
                },
                "tolerance": {
                    "type": "string",
                    "enum": ["low", "medium", "high"],
                    "default": "medium",
                    "description": "User's THC tolerance"
                }
            },
            "required": ["experience_level", "product_thc_mg"]
        }
    
    async def execute(self, experience_level: str, product_thc_mg: float,
                     tolerance: str = "medium", **kwargs) -> ToolResult:
        """Calculate recommended dosage"""
        try:
            # Dosage recommendations (in mg THC)
            recommendations = {
                "beginner": {"low": 2.5, "medium": 5, "high": 7.5},
                "occasional": {"low": 5, "medium": 10, "high": 15},
                "regular": {"low": 10, "medium": 15, "high": 20},
                "experienced": {"low": 15, "medium": 25, "high": 35}
            }
            
            recommended_mg = recommendations[experience_level][tolerance]
            servings = recommended_mg / product_thc_mg if product_thc_mg > 0 else 0
            
            advice = {
                "beginner": "Start low and go slow. Wait at least 2 hours before taking more.",
                "occasional": "You have some experience. Still wait 90 minutes between doses.",
                "regular": "You know your tolerance. Wait 60 minutes to assess effects.",
                "experienced": "You're experienced but always consume responsibly."
            }
            
            return ToolResult(
                success=True,
                data={
                    "recommended_dose_mg": recommended_mg,
                    "product_servings": round(servings, 1),
                    "advice": advice[experience_level],
                    "warning": "Effects can take 30-120 minutes. Never drive under the influence."
                },
                metadata={
                    "experience": experience_level,
                    "tolerance": tolerance,
                    "product_thc": product_thc_mg
                }
            )
        except Exception as e:
            return ToolResult(success=False, data=None, error=str(e))

class StrainComparisonTool(ITool):
    """Compare different cannabis strains"""
    
    @property
    def name(self) -> str:
        return "compare_strains"
    
    @property
    def description(self) -> str:
        return "Compare characteristics of different cannabis strains"
    
    @property
    def parameters(self) -> Dict:
        return {
            "type": "object",
            "properties": {
                "strains": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of strain names to compare",
                    "minItems": 2,
                    "maxItems": 4
                }
            },
            "required": ["strains"]
        }
    
    async def execute(self, strains: List[str], **kwargs) -> ToolResult:
        """Compare strains"""
        try:
            # Strain database (mock)
            strain_db = {
                "blue dream": {
                    "type": "Sativa-dominant Hybrid",
                    "thc": "17-24%",
                    "cbd": "0.1-2%",
                    "effects": "Creative, Energetic, Uplifting",
                    "flavors": "Berry, Sweet, Vanilla",
                    "helps_with": "Depression, Pain, Nausea"
                },
                "og kush": {
                    "type": "Indica-dominant Hybrid",
                    "thc": "20-26%",
                    "cbd": "0-0.3%",
                    "effects": "Relaxed, Happy, Euphoric",
                    "flavors": "Earthy, Pine, Woody",
                    "helps_with": "Stress, Pain, Insomnia"
                },
                "northern lights": {
                    "type": "Indica",
                    "thc": "16-21%",
                    "cbd": "0.1%",
                    "effects": "Relaxed, Sleepy, Happy",
                    "flavors": "Pine, Earthy, Sweet",
                    "helps_with": "Insomnia, Pain, Stress"
                },
                "sour diesel": {
                    "type": "Sativa",
                    "thc": "20-25%",
                    "cbd": "0.2-2%",
                    "effects": "Energetic, Creative, Focused",
                    "flavors": "Diesel, Pungent, Citrus",
                    "helps_with": "Depression, Fatigue, Stress"
                }
            }
            
            comparison = {}
            for strain in strains:
                strain_lower = strain.lower()
                if strain_lower in strain_db:
                    comparison[strain] = strain_db[strain_lower]
                else:
                    comparison[strain] = {"error": "Strain not found in database"}
            
            return ToolResult(
                success=True,
                data=comparison,
                metadata={"strains_compared": len(strains)}
            )
        except Exception as e:
            return ToolResult(success=False, data=None, error=str(e))