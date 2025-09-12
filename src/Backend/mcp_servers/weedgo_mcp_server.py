#!/usr/bin/env python3
"""
WeedGo MCP Server
Cannabis-specific MCP server with specialized tools
"""
import asyncio
import json
import sys
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
import aiohttp
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.mcp.mcp_types import (
    MCPRequest, MCPResponse, MCPError, MCPErrorCode,
    MCPTool, MCPResource, MCPPrompt
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class WeedGoMCPServer:
    """MCP server with cannabis industry tools"""
    
    def __init__(self):
        """Initialize WeedGo MCP server"""
        self.name = "weedgo"
        self.version = "1.0.0"
        self.tools = self._register_tools()
        self.resources = self._register_resources()
        self.prompts = self._register_prompts()
        
        # Strain database (would be connected to real DB in production)
        self.strain_db = self._load_strain_database()
        
        # Compliance data
        self.compliance_db = self._load_compliance_data()
    
    def _register_tools(self) -> Dict[str, MCPTool]:
        """Register available tools"""
        tools = {}
        
        # Strain lookup tool
        tools["strain_lookup"] = MCPTool(
            name="strain_lookup",
            description="Get detailed information about cannabis strains",
            input_schema={
                "type": "object",
                "properties": {
                    "strain": {"type": "string", "description": "Strain name"},
                    "info_type": {
                        "type": "string",
                        "enum": ["general", "effects", "medical", "terpenes"],
                        "description": "Type of information to retrieve"
                    }
                },
                "required": ["strain"]
            },
            tags=["cannabis", "strains", "information"]
        )
        
        # Dosage calculator
        tools["dosage_calculator"] = MCPTool(
            name="dosage_calculator",
            description="Calculate recommended cannabis dosages",
            input_schema={
                "type": "object",
                "properties": {
                    "weight": {"type": "number", "description": "Body weight in kg"},
                    "tolerance": {
                        "type": "string",
                        "enum": ["none", "low", "moderate", "high"],
                        "description": "Cannabis tolerance level"
                    },
                    "product_type": {
                        "type": "string",
                        "enum": ["flower", "edible", "tincture", "concentrate"],
                        "description": "Type of cannabis product"
                    },
                    "desired_effect": {
                        "type": "string",
                        "enum": ["microdose", "mild", "moderate", "strong"],
                        "description": "Desired effect level"
                    }
                },
                "required": ["weight", "tolerance", "product_type"]
            },
            tags=["cannabis", "dosage", "safety"]
        )
        
        # Compliance checker
        tools["compliance_check"] = MCPTool(
            name="compliance_check",
            description="Check cannabis compliance regulations by state",
            input_schema={
                "type": "object",
                "properties": {
                    "state": {"type": "string", "description": "US state code"},
                    "query": {
                        "type": "string",
                        "enum": ["possession", "cultivation", "sales", "medical", "testing"],
                        "description": "Compliance area to check"
                    },
                    "license_type": {
                        "type": "string",
                        "enum": ["dispensary", "cultivation", "manufacturing", "testing", "distribution"],
                        "description": "License type for business compliance"
                    }
                },
                "required": ["state", "query"]
            },
            tags=["cannabis", "compliance", "regulations"]
        )
        
        # Terpene analyzer
        tools["terpene_analyzer"] = MCPTool(
            name="terpene_analyzer",
            description="Analyze terpene profiles and effects",
            input_schema={
                "type": "object",
                "properties": {
                    "terpenes": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of terpenes to analyze"
                    },
                    "analysis_type": {
                        "type": "string",
                        "enum": ["effects", "synergy", "flavor", "medical"],
                        "description": "Type of analysis"
                    }
                },
                "required": ["terpenes"]
            },
            tags=["cannabis", "terpenes", "chemistry"]
        )
        
        # Lab result interpreter
        tools["lab_result_interpreter"] = MCPTool(
            name="lab_result_interpreter",
            description="Interpret cannabis lab test results",
            input_schema={
                "type": "object",
                "properties": {
                    "thc": {"type": "number", "description": "THC percentage"},
                    "cbd": {"type": "number", "description": "CBD percentage"},
                    "terpenes": {
                        "type": "object",
                        "description": "Terpene percentages",
                        "additionalProperties": {"type": "number"}
                    },
                    "contaminants": {
                        "type": "object",
                        "description": "Contaminant test results",
                        "properties": {
                            "pesticides": {"type": "string", "enum": ["pass", "fail"]},
                            "heavy_metals": {"type": "string", "enum": ["pass", "fail"]},
                            "microbials": {"type": "string", "enum": ["pass", "fail"]}
                        }
                    }
                },
                "required": ["thc", "cbd"]
            },
            tags=["cannabis", "testing", "safety"]
        )
        
        return tools
    
    def _register_resources(self) -> Dict[str, MCPResource]:
        """Register available resources"""
        resources = {}
        
        resources["strain_database"] = MCPResource(
            uri="weedgo://strains/database",
            name="Strain Database",
            description="Complete cannabis strain database",
            mime_type="application/json"
        )
        
        resources["compliance_guide"] = MCPResource(
            uri="weedgo://compliance/guide",
            name="Compliance Guide",
            description="State-by-state compliance guide",
            mime_type="application/json"
        )
        
        resources["terpene_reference"] = MCPResource(
            uri="weedgo://terpenes/reference",
            name="Terpene Reference",
            description="Comprehensive terpene reference guide",
            mime_type="application/json"
        )
        
        return resources
    
    def _register_prompts(self) -> Dict[str, MCPPrompt]:
        """Register available prompts"""
        prompts = {}
        
        prompts["budtender_consultation"] = MCPPrompt(
            name="budtender_consultation",
            description="Generate budtender consultation dialogue",
            arguments=[
                {"name": "customer_needs", "type": "string", "description": "Customer requirements"},
                {"name": "experience_level", "type": "string", "description": "Customer experience"}
            ],
            template="""As a knowledgeable budtender, help a customer with the following needs:
Customer Needs: {{customer_needs}}
Experience Level: {{experience_level}}

Provide personalized strain recommendations and usage guidance.""",
            tags=["cannabis", "consultation", "customer_service"]
        )
        
        prompts["compliance_report"] = MCPPrompt(
            name="compliance_report",
            description="Generate compliance report template",
            arguments=[
                {"name": "state", "type": "string", "description": "State for compliance"},
                {"name": "business_type", "type": "string", "description": "Type of cannabis business"}
            ],
            template="""Generate a compliance report for:
State: {{state}}
Business Type: {{business_type}}

Include all relevant regulations and requirements.""",
            tags=["cannabis", "compliance", "reporting"]
        )
        
        return prompts
    
    def _load_strain_database(self) -> Dict[str, Any]:
        """Load strain database (mock data for example)"""
        return {
            "blue_dream": {
                "name": "Blue Dream",
                "type": "Sativa-dominant hybrid",
                "genetics": {"parent1": "Blueberry", "parent2": "Haze"},
                "cannabinoids": {"thc": 18.5, "cbd": 0.5, "cbg": 0.2},
                "terpenes": {
                    "myrcene": 0.4,
                    "pinene": 0.3,
                    "caryophyllene": 0.2,
                    "limonene": 0.5,
                    "linalool": 0.1
                },
                "effects": ["creative", "euphoric", "happy", "relaxed", "uplifted"],
                "medical": ["anxiety", "depression", "pain", "stress"],
                "negatives": ["dry_mouth", "dry_eyes"],
                "flavors": ["berry", "blueberry", "herbal", "sweet", "vanilla"]
            },
            "og_kush": {
                "name": "OG Kush",
                "type": "Indica-dominant hybrid",
                "genetics": {"parent1": "Chemdawg", "parent2": "Hindu Kush"},
                "cannabinoids": {"thc": 22.0, "cbd": 0.2, "cbn": 0.1},
                "terpenes": {
                    "myrcene": 0.3,
                    "limonene": 0.4,
                    "caryophyllene": 0.3,
                    "linalool": 0.2,
                    "humulene": 0.1
                },
                "effects": ["euphoric", "happy", "hungry", "relaxed", "sleepy"],
                "medical": ["insomnia", "pain", "stress", "lack_of_appetite"],
                "negatives": ["dry_mouth", "dry_eyes", "paranoia"],
                "flavors": ["earthy", "pine", "woody", "lemon", "diesel"]
            }
        }
    
    def _load_compliance_data(self) -> Dict[str, Any]:
        """Load compliance data (mock data for example)"""
        return {
            "CA": {
                "name": "California",
                "adult_use": True,
                "medical": True,
                "possession_limit": {
                    "flower": "28.5g",
                    "concentrate": "8g"
                },
                "cultivation": {
                    "personal": "6 plants",
                    "medical": "6 mature or 12 immature"
                },
                "testing_required": True,
                "track_and_trace": "METRC",
                "licenses": ["dispensary", "cultivation", "manufacturing", "testing", "distribution"],
                "tax_rate": {
                    "excise": "15%",
                    "cultivation": "$9.65/oz flower"
                }
            },
            "CO": {
                "name": "Colorado",
                "adult_use": True,
                "medical": True,
                "possession_limit": {
                    "flower": "28g",
                    "concentrate": "8g"
                },
                "cultivation": {
                    "personal": "6 plants (3 mature)",
                    "medical": "6 plants"
                },
                "testing_required": True,
                "track_and_trace": "METRC",
                "licenses": ["dispensary", "cultivation", "manufacturing", "testing"],
                "tax_rate": {
                    "excise": "15%",
                    "retail": "15%"
                }
            }
        }
    
    async def handle_request(self, request: MCPRequest) -> MCPResponse:
        """Handle incoming MCP request"""
        try:
            method = request.method
            
            if method == "initialize":
                return await self._handle_initialize(request)
            elif method == "tools/list":
                return await self._handle_list_tools(request)
            elif method == "tools/call":
                return await self._handle_tool_call(request)
            elif method == "resources/list":
                return await self._handle_list_resources(request)
            elif method == "resources/read":
                return await self._handle_read_resource(request)
            elif method == "prompts/list":
                return await self._handle_list_prompts(request)
            elif method == "prompts/get":
                return await self._handle_get_prompt(request)
            else:
                return MCPResponse(
                    id=request.id,
                    error=MCPError(
                        code=MCPErrorCode.METHOD_NOT_FOUND.value,
                        message=f"Method not found: {method}"
                    )
                )
                
        except Exception as e:
            logger.error(f"Error handling request: {e}")
            return MCPResponse(
                id=request.id,
                error=MCPError.from_exception(e)
            )
    
    async def _handle_initialize(self, request: MCPRequest) -> MCPResponse:
        """Handle initialization request"""
        return MCPResponse(
            id=request.id,
            result={
                "protocolVersion": "1.0",
                "serverInfo": {
                    "name": self.name,
                    "version": self.version,
                    "description": "WeedGo cannabis industry MCP server"
                },
                "capabilities": {
                    "tools": {"available": True},
                    "resources": {"available": True},
                    "prompts": {"available": True}
                }
            }
        )
    
    async def _handle_list_tools(self, request: MCPRequest) -> MCPResponse:
        """Handle list tools request"""
        tools_list = []
        for tool in self.tools.values():
            tools_list.append({
                "name": tool.name,
                "description": tool.description,
                "inputSchema": tool.input_schema,
                "tags": tool.tags
            })
        
        return MCPResponse(
            id=request.id,
            result={"tools": tools_list}
        )
    
    async def _handle_tool_call(self, request: MCPRequest) -> MCPResponse:
        """Handle tool call request"""
        params = request.params or {}
        tool_name = params.get("name")
        arguments = params.get("arguments", {})
        
        if tool_name not in self.tools:
            return MCPResponse(
                id=request.id,
                error=MCPError(
                    code=MCPErrorCode.INVALID_PARAMS.value,
                    message=f"Tool not found: {tool_name}"
                )
            )
        
        # Execute tool
        result = await self._execute_tool(tool_name, arguments)
        
        return MCPResponse(
            id=request.id,
            result={"content": [{"type": "text", "text": json.dumps(result)}]}
        )
    
    async def _execute_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Any:
        """Execute a tool and return result"""
        
        if tool_name == "strain_lookup":
            strain = arguments.get("strain", "").lower().replace(" ", "_")
            info_type = arguments.get("info_type", "general")
            
            if strain in self.strain_db:
                data = self.strain_db[strain]
                if info_type == "effects":
                    return {
                        "strain": data["name"],
                        "effects": data["effects"],
                        "medical": data["medical"],
                        "negatives": data["negatives"]
                    }
                elif info_type == "terpenes":
                    return {
                        "strain": data["name"],
                        "terpenes": data["terpenes"],
                        "flavors": data["flavors"]
                    }
                else:
                    return data
            else:
                return {"error": f"Strain '{arguments.get('strain')}' not found"}
        
        elif tool_name == "dosage_calculator":
            weight = arguments.get("weight", 70)
            tolerance = arguments.get("tolerance", "none")
            product_type = arguments.get("product_type", "flower")
            desired_effect = arguments.get("desired_effect", "moderate")
            
            # Base doses in mg THC
            base_doses = {
                "none": {"microdose": 1, "mild": 2.5, "moderate": 5, "strong": 10},
                "low": {"microdose": 2.5, "mild": 5, "moderate": 10, "strong": 20},
                "moderate": {"microdose": 5, "mild": 10, "moderate": 20, "strong": 30},
                "high": {"microdose": 10, "mild": 20, "moderate": 30, "strong": 50}
            }
            
            # Product multipliers
            product_multipliers = {
                "flower": 1.0,
                "edible": 0.5,  # Edibles need less due to liver processing
                "tincture": 0.8,
                "concentrate": 0.3  # Concentrates are much stronger
            }
            
            base = base_doses.get(tolerance, base_doses["none"])
            dose = base.get(desired_effect, 5)
            
            # Adjust for weight
            weight_factor = weight / 70
            dose = dose * (0.8 + 0.2 * weight_factor)
            
            # Apply product multiplier
            dose = dose * product_multipliers.get(product_type, 1.0)
            
            return {
                "recommended_dose_mg": round(dose, 1),
                "tolerance": tolerance,
                "product_type": product_type,
                "weight_kg": weight,
                "desired_effect": desired_effect,
                "notes": self._get_dosage_notes(product_type, tolerance)
            }
        
        elif tool_name == "compliance_check":
            state = arguments.get("state", "CA")
            query = arguments.get("query", "possession")
            license_type = arguments.get("license_type")
            
            if state in self.compliance_db:
                data = self.compliance_db[state]
                
                if query == "possession":
                    return {
                        "state": data["name"],
                        "possession_limits": data["possession_limit"],
                        "adult_use_legal": data["adult_use"],
                        "medical_legal": data["medical"]
                    }
                elif query == "cultivation":
                    return {
                        "state": data["name"],
                        "cultivation_limits": data["cultivation"],
                        "license_required": license_type in data.get("licenses", [])
                    }
                elif query == "testing":
                    return {
                        "state": data["name"],
                        "testing_required": data["testing_required"],
                        "track_and_trace": data.get("track_and_trace")
                    }
                else:
                    return data
            else:
                return {"error": f"State '{state}' compliance data not available"}
        
        elif tool_name == "terpene_analyzer":
            terpenes = arguments.get("terpenes", [])
            analysis_type = arguments.get("analysis_type", "effects")
            
            terpene_effects = {
                "myrcene": {
                    "effects": ["sedating", "relaxing", "muscle_relaxant"],
                    "flavor": "earthy, musky, fruity",
                    "medical": ["pain", "insomnia", "inflammation"]
                },
                "limonene": {
                    "effects": ["uplifting", "mood_enhancing", "stress_relief"],
                    "flavor": "citrus, lemon, orange",
                    "medical": ["anxiety", "depression", "acid_reflux"]
                },
                "pinene": {
                    "effects": ["alertness", "memory_retention", "counteracts_thc"],
                    "flavor": "pine, fresh, sharp",
                    "medical": ["asthma", "inflammation", "anxiety"]
                },
                "linalool": {
                    "effects": ["calming", "sedating", "anti_anxiety"],
                    "flavor": "floral, lavender, sweet",
                    "medical": ["anxiety", "depression", "insomnia", "pain"]
                },
                "caryophyllene": {
                    "effects": ["anti_inflammatory", "pain_relief"],
                    "flavor": "spicy, peppery, woody",
                    "medical": ["chronic_pain", "inflammation", "anxiety"]
                }
            }
            
            analysis = {}
            for terpene in terpenes:
                terpene_lower = terpene.lower()
                if terpene_lower in terpene_effects:
                    if analysis_type == "effects":
                        analysis[terpene] = terpene_effects[terpene_lower]["effects"]
                    elif analysis_type == "flavor":
                        analysis[terpene] = terpene_effects[terpene_lower]["flavor"]
                    elif analysis_type == "medical":
                        analysis[terpene] = terpene_effects[terpene_lower]["medical"]
                    else:
                        analysis[terpene] = terpene_effects[terpene_lower]
            
            if analysis_type == "synergy" and len(terpenes) > 1:
                analysis["entourage_effect"] = "Multiple terpenes working together may enhance overall effects"
                analysis["recommendation"] = "This combination may provide balanced effects"
            
            return analysis
        
        elif tool_name == "lab_result_interpreter":
            thc = arguments.get("thc", 0)
            cbd = arguments.get("cbd", 0)
            terpenes = arguments.get("terpenes", {})
            contaminants = arguments.get("contaminants", {})
            
            interpretation = {
                "cannabinoid_profile": self._interpret_cannabinoids(thc, cbd),
                "potency_level": self._determine_potency(thc),
                "recommended_use": self._recommend_use(thc, cbd),
                "terpene_analysis": self._analyze_terpene_profile(terpenes),
                "safety_assessment": self._assess_safety(contaminants)
            }
            
            return interpretation
        
        return {"error": f"Tool '{tool_name}' execution not implemented"}
    
    def _get_dosage_notes(self, product_type: str, tolerance: str) -> str:
        """Get dosage notes based on product and tolerance"""
        notes = {
            "edible": "Wait 2 hours before taking more. Effects last 4-8 hours.",
            "flower": "Effects onset in 5-10 minutes. Start with small amounts.",
            "tincture": "Hold under tongue for 30 seconds. Effects in 15-45 minutes.",
            "concentrate": "Very potent. Use specialized equipment. Start very small."
        }
        
        if tolerance == "none":
            return f"First time user advice: {notes.get(product_type, 'Start low and go slow.')}"
        return notes.get(product_type, "Start low and go slow.")
    
    def _interpret_cannabinoids(self, thc: float, cbd: float) -> str:
        """Interpret cannabinoid profile"""
        ratio = thc / cbd if cbd > 0 else float('inf')
        
        if ratio > 20:
            return "THC-dominant: Psychoactive, euphoric effects expected"
        elif ratio > 5:
            return "THC-forward: Moderate psychoactive effects with some CBD balance"
        elif ratio > 1:
            return "Balanced: Mild psychoactive effects with CBD moderation"
        elif ratio > 0.5:
            return "CBD-forward: Minimal psychoactive effects, therapeutic focus"
        else:
            return "CBD-dominant: Non-psychoactive, therapeutic effects"
    
    def _determine_potency(self, thc: float) -> str:
        """Determine potency level"""
        if thc < 10:
            return "Low potency - Good for beginners"
        elif thc < 15:
            return "Medium potency - Suitable for occasional users"
        elif thc < 20:
            return "High potency - For experienced users"
        elif thc < 25:
            return "Very high potency - For high tolerance users"
        else:
            return "Extreme potency - Use with caution"
    
    def _recommend_use(self, thc: float, cbd: float) -> str:
        """Recommend use based on cannabinoid profile"""
        if thc < 5 and cbd > 10:
            return "Ideal for medical use without intoxication"
        elif thc < 10:
            return "Good for daytime functional use"
        elif thc < 15 and cbd > 5:
            return "Balanced effects suitable for various occasions"
        elif thc > 20:
            return "Best for evening/nighttime use or high tolerance users"
        else:
            return "Versatile profile for various uses"
    
    def _analyze_terpene_profile(self, terpenes: Dict[str, float]) -> str:
        """Analyze terpene profile"""
        if not terpenes:
            return "No terpene data available"
        
        dominant = max(terpenes.items(), key=lambda x: x[1])
        total = sum(terpenes.values())
        
        if total > 3:
            return f"Rich terpene profile ({total:.1f}%), dominant in {dominant[0]}"
        elif total > 1:
            return f"Moderate terpene profile ({total:.1f}%), led by {dominant[0]}"
        else:
            return f"Low terpene profile ({total:.1f}%)"
    
    def _assess_safety(self, contaminants: Dict[str, str]) -> str:
        """Assess safety based on contaminant results"""
        if not contaminants:
            return "No contaminant data available"
        
        failures = [k for k, v in contaminants.items() if v == "fail"]
        
        if failures:
            return f"FAILED: {', '.join(failures)}. Do not consume."
        else:
            return "Passed all contaminant tests. Safe for consumption."
    
    async def _handle_list_resources(self, request: MCPRequest) -> MCPResponse:
        """Handle list resources request"""
        resources_list = []
        for resource in self.resources.values():
            resources_list.append({
                "uri": resource.uri,
                "name": resource.name,
                "description": resource.description,
                "mimeType": resource.mime_type
            })
        
        return MCPResponse(
            id=request.id,
            result={"resources": resources_list}
        )
    
    async def _handle_read_resource(self, request: MCPRequest) -> MCPResponse:
        """Handle read resource request"""
        params = request.params or {}
        uri = params.get("uri")
        
        if uri == "weedgo://strains/database":
            content = json.dumps(self.strain_db, indent=2)
        elif uri == "weedgo://compliance/guide":
            content = json.dumps(self.compliance_db, indent=2)
        elif uri == "weedgo://terpenes/reference":
            content = json.dumps({
                "terpenes": {
                    "myrcene": "Sedating, earthy",
                    "limonene": "Uplifting, citrus",
                    "pinene": "Alert, pine",
                    "linalool": "Calming, floral",
                    "caryophyllene": "Anti-inflammatory, spicy"
                }
            }, indent=2)
        else:
            return MCPResponse(
                id=request.id,
                error=MCPError(
                    code=MCPErrorCode.INVALID_PARAMS.value,
                    message=f"Resource not found: {uri}"
                )
            )
        
        return MCPResponse(
            id=request.id,
            result={
                "contents": [{"uri": uri, "mimeType": "application/json", "text": content}]
            }
        )
    
    async def _handle_list_prompts(self, request: MCPRequest) -> MCPResponse:
        """Handle list prompts request"""
        prompts_list = []
        for prompt in self.prompts.values():
            prompts_list.append({
                "name": prompt.name,
                "description": prompt.description,
                "arguments": prompt.arguments,
                "tags": prompt.tags
            })
        
        return MCPResponse(
            id=request.id,
            result={"prompts": prompts_list}
        )
    
    async def _handle_get_prompt(self, request: MCPRequest) -> MCPResponse:
        """Handle get prompt request"""
        params = request.params or {}
        name = params.get("name")
        arguments = params.get("arguments", {})
        
        if name not in self.prompts:
            return MCPResponse(
                id=request.id,
                error=MCPError(
                    code=MCPErrorCode.INVALID_PARAMS.value,
                    message=f"Prompt not found: {name}"
                )
            )
        
        prompt = self.prompts[name]
        
        # Render template with arguments
        rendered = prompt.template
        for arg_name, arg_value in arguments.items():
            rendered = rendered.replace(f"{{{{{arg_name}}}}}", str(arg_value))
        
        return MCPResponse(
            id=request.id,
            result={
                "messages": [{"role": "user", "content": {"type": "text", "text": rendered}}]
            }
        )
    
    async def run_stdio(self):
        """Run server in stdio mode"""
        logger.info("WeedGo MCP Server starting in stdio mode...")
        
        while True:
            try:
                line = await asyncio.get_event_loop().run_in_executor(None, sys.stdin.readline)
                if not line:
                    break
                
                # Parse request
                request_data = json.loads(line)
                request = MCPRequest(**request_data)
                
                # Handle request
                response = await self.handle_request(request)
                
                # Send response
                print(json.dumps(response.to_dict()))
                sys.stdout.flush()
                
            except Exception as e:
                logger.error(f"Error in stdio loop: {e}")
                error_response = MCPResponse(
                    error=MCPError.from_exception(e)
                )
                print(json.dumps(error_response.to_dict()))
                sys.stdout.flush()

async def main():
    """Main entry point"""
    server = WeedGoMCPServer()
    
    # Check if running in stdio mode or HTTP mode
    if len(sys.argv) > 1 and sys.argv[1] == "--stdio":
        await server.run_stdio()
    else:
        # Could add HTTP server mode here
        logger.info("Starting in stdio mode by default...")
        await server.run_stdio()

if __name__ == "__main__":
    asyncio.run(main())