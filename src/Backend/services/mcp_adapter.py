"""
MCP Adapter for V5 AI Engine
Integrates MCP tools with the V5 agent system
"""
import asyncio
import logging
from typing import Dict, Any, List, Optional, Callable
from pathlib import Path
import json

from core.mcp import MCPClient, MCPDiscovery, MCPServer, MCPTool
from core.mcp.mcp_types import TransportType, MCPCapabilities

logger = logging.getLogger(__name__)

class MCPAdapter:
    """Adapts MCP tools for use by V5 agents"""
    
    def __init__(self, offline_fallback: bool = True):
        """Initialize MCP adapter
        
        Args:
            offline_fallback: Use offline tools when MCP is unavailable
        """
        self.offline_fallback = offline_fallback
        self.mcp_client: Optional[MCPClient] = None
        self.mcp_enabled = False
        self.available_tools: Dict[str, MCPTool] = {}
        self.tool_mapping: Dict[str, str] = {}  # Maps tool names to server IDs
        self.offline_tools: Dict[str, Callable] = {}
        
        # Initialize offline tools registry
        self._register_offline_tools()
    
    async def initialize(self) -> bool:
        """Initialize MCP adapter"""
        try:
            logger.info("Initializing MCP adapter...")
            
            # Try to initialize MCP client
            try:
                self.mcp_client = MCPClient()
                servers = await self.mcp_client.discover_servers()
                
                if servers:
                    logger.info(f"Discovered {len(servers)} MCP servers")
                    
                    # Try to connect to available servers
                    for server in servers:
                        if await self.mcp_client.connect(server):
                            logger.info(f"Connected to MCP server: {server.name}")
                            
                            # Load tools from server
                            tools = await self.mcp_client.list_tools(server.id)
                            for tool in tools:
                                self.available_tools[tool.name] = tool
                                self.tool_mapping[tool.name] = server.id
                    
                    self.mcp_enabled = len(self.available_tools) > 0
                    
                    if self.mcp_enabled:
                        logger.info(f"MCP enabled with {len(self.available_tools)} tools")
                else:
                    logger.info("No MCP servers found, using offline mode")
                    
            except Exception as e:
                logger.warning(f"MCP initialization failed: {e}, using offline mode")
                self.mcp_enabled = False
            
            # Always succeed if offline fallback is enabled
            if not self.mcp_enabled and self.offline_fallback:
                logger.info("Using offline tools as fallback")
                return True
            
            return self.mcp_enabled
            
        except Exception as e:
            logger.error(f"Adapter initialization failed: {e}")
            return False
    
    def _register_offline_tools(self) -> None:
        """Register offline tool implementations"""
        # These provide fallback functionality when MCP is unavailable
        
        self.offline_tools["calculate"] = self._offline_calculate
        self.offline_tools["search_products"] = self._offline_search_products
        self.offline_tools["strain_lookup"] = self._offline_strain_lookup
        self.offline_tools["dosage_calculator"] = self._offline_dosage_calculator
        self.offline_tools["compliance_check"] = self._offline_compliance_check
    
    async def execute_tool(
        self,
        tool_name: str,
        arguments: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Execute a tool (MCP or offline)
        
        Args:
            tool_name: Name of tool to execute
            arguments: Tool arguments
            context: Optional execution context
            
        Returns:
            Tool execution result
        """
        try:
            # Try MCP first if enabled
            if self.mcp_enabled and tool_name in self.available_tools:
                logger.debug(f"Executing MCP tool: {tool_name}")
                server_id = self.tool_mapping.get(tool_name)
                
                try:
                    result = await self.mcp_client.call_tool(
                        tool_name,
                        arguments,
                        server_id
                    )
                    
                    return {
                        "success": True,
                        "result": result,
                        "source": "mcp",
                        "tool": tool_name
                    }
                    
                except Exception as e:
                    logger.warning(f"MCP tool execution failed: {e}")
                    
                    # Fall through to offline if enabled
                    if not self.offline_fallback:
                        return {
                            "success": False,
                            "error": str(e),
                            "source": "mcp",
                            "tool": tool_name
                        }
            
            # Use offline fallback
            if tool_name in self.offline_tools:
                logger.debug(f"Executing offline tool: {tool_name}")
                result = await self.offline_tools[tool_name](arguments, context)
                
                return {
                    "success": True,
                    "result": result,
                    "source": "offline",
                    "tool": tool_name
                }
            
            # Tool not found
            return {
                "success": False,
                "error": f"Tool '{tool_name}' not found",
                "available_tools": list(self.get_available_tools().keys())
            }
            
        except Exception as e:
            logger.error(f"Tool execution error: {e}")
            return {
                "success": False,
                "error": str(e),
                "tool": tool_name
            }
    
    def get_available_tools(self) -> Dict[str, Dict[str, Any]]:
        """Get all available tools (MCP and offline)
        
        Returns:
            Dictionary of tool definitions
        """
        tools = {}
        
        # Add MCP tools
        for name, tool in self.available_tools.items():
            tools[name] = {
                "name": name,
                "description": tool.description,
                "input_schema": tool.input_schema,
                "source": "mcp"
            }
        
        # Add offline tools
        for name in self.offline_tools:
            if name not in tools:  # Don't override MCP tools
                tools[name] = {
                    "name": name,
                    "description": self._get_offline_tool_description(name),
                    "input_schema": self._get_offline_tool_schema(name),
                    "source": "offline"
                }
        
        return tools
    
    def get_tool_schemas(self, format: str = "openai") -> List[Dict[str, Any]]:
        """Get tool schemas in specified format
        
        Args:
            format: Schema format ("openai" or "anthropic")
            
        Returns:
            List of tool schemas
        """
        schemas = []
        
        for tool_info in self.get_available_tools().values():
            if format == "openai":
                schema = {
                    "type": "function",
                    "function": {
                        "name": tool_info["name"],
                        "description": tool_info["description"],
                        "parameters": tool_info["input_schema"]
                    }
                }
            else:  # anthropic format
                schema = {
                    "name": tool_info["name"],
                    "description": tool_info["description"],
                    "input_schema": tool_info["input_schema"]
                }
            
            schemas.append(schema)
        
        return schemas
    
    # Offline tool implementations
    
    async def _offline_calculate(
        self,
        arguments: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> Any:
        """Offline calculator tool"""
        expression = arguments.get("expression", "")
        
        try:
            # Simple safe evaluation
            import ast
            import operator
            
            ops = {
                ast.Add: operator.add,
                ast.Sub: operator.sub,
                ast.Mult: operator.mul,
                ast.Div: operator.truediv,
                ast.Pow: operator.pow,
                ast.USub: operator.neg
            }
            
            def eval_expr(node):
                if isinstance(node, ast.Num):
                    return node.n
                elif isinstance(node, ast.BinOp):
                    return ops[type(node.op)](
                        eval_expr(node.left),
                        eval_expr(node.right)
                    )
                elif isinstance(node, ast.UnaryOp):
                    return ops[type(node.op)](eval_expr(node.operand))
                else:
                    raise ValueError(f"Unsupported expression: {node}")
            
            tree = ast.parse(expression, mode='eval')
            result = eval_expr(tree.body)
            
            return {
                "expression": expression,
                "result": result
            }
            
        except Exception as e:
            return {
                "expression": expression,
                "error": str(e)
            }
    
    async def _offline_search_products(
        self,
        arguments: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> Any:
        """Offline product search (mock data)"""
        query = arguments.get("query", "")
        category = arguments.get("category")
        
        # Mock product data
        mock_products = [
            {
                "id": "1",
                "name": "Blue Dream",
                "category": "flower",
                "type": "sativa",
                "thc": 18.5,
                "cbd": 0.5,
                "price": 45.00,
                "available": True
            },
            {
                "id": "2",
                "name": "OG Kush",
                "category": "flower",
                "type": "indica",
                "thc": 22.0,
                "cbd": 0.2,
                "price": 50.00,
                "available": True
            },
            {
                "id": "3",
                "name": "CBD Tincture",
                "category": "tincture",
                "type": "cbd",
                "thc": 0.0,
                "cbd": 30.0,
                "price": 65.00,
                "available": True
            }
        ]
        
        # Filter by category if provided
        results = mock_products
        if category:
            results = [p for p in results if p["category"] == category]
        
        # Simple query matching
        if query:
            query_lower = query.lower()
            results = [
                p for p in results
                if query_lower in p["name"].lower() or
                   query_lower in p.get("type", "").lower()
            ]
        
        return {
            "query": query,
            "category": category,
            "results": results,
            "count": len(results)
        }
    
    async def _offline_strain_lookup(
        self,
        arguments: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> Any:
        """Offline strain information lookup"""
        strain_name = arguments.get("strain", "").lower()
        
        # Mock strain database
        strains = {
            "blue dream": {
                "name": "Blue Dream",
                "type": "Sativa-dominant hybrid",
                "genetics": "Blueberry x Haze",
                "thc_range": "17-24%",
                "cbd_range": "0.1-0.2%",
                "effects": ["Creative", "Euphoric", "Uplifted"],
                "medical": ["Depression", "Pain", "Stress"],
                "flavors": ["Berry", "Blueberry", "Sweet"],
                "description": "A popular daytime strain known for gentle cerebral invigoration"
            },
            "og kush": {
                "name": "OG Kush",
                "type": "Indica-dominant hybrid",
                "genetics": "Chemdawg x Hindu Kush",
                "thc_range": "20-25%",
                "cbd_range": "0.0-0.3%",
                "effects": ["Euphoric", "Happy", "Relaxed"],
                "medical": ["Stress", "Pain", "Insomnia"],
                "flavors": ["Earthy", "Pine", "Woody"],
                "description": "A legendary strain with complex terpene profile"
            }
        }
        
        if strain_name in strains:
            return strains[strain_name]
        else:
            return {
                "error": f"Strain '{arguments.get('strain')}' not found",
                "suggestion": "Try 'Blue Dream' or 'OG Kush'"
            }
    
    async def _offline_dosage_calculator(
        self,
        arguments: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> Any:
        """Offline dosage calculator"""
        weight = arguments.get("weight", 70)  # kg
        experience = arguments.get("experience", "beginner")
        product_type = arguments.get("product_type", "flower")
        
        # Basic dosage recommendations (mg THC)
        base_doses = {
            "beginner": {"edible": 2.5, "flower": 5, "tincture": 5},
            "intermediate": {"edible": 5, "flower": 10, "tincture": 10},
            "experienced": {"edible": 10, "flower": 20, "tincture": 20}
        }
        
        # Get base dose
        base = base_doses.get(experience, base_doses["beginner"])
        dose = base.get(product_type, 5)
        
        # Adjust for weight (simple linear adjustment)
        weight_factor = weight / 70  # Normalize to 70kg
        adjusted_dose = dose * (0.7 + 0.3 * weight_factor)
        
        return {
            "recommended_dose_mg": round(adjusted_dose, 1),
            "experience_level": experience,
            "product_type": product_type,
            "weight_kg": weight,
            "notes": "Start low and go slow. Wait 2 hours before redosing edibles."
        }
    
    async def _offline_compliance_check(
        self,
        arguments: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> Any:
        """Offline compliance checker"""
        state = arguments.get("state", "CA")
        check_type = arguments.get("type", "general")
        
        # Mock compliance data
        compliance_data = {
            "CA": {
                "legal_age": 21,
                "medical_age": 18,
                "possession_limit": "28.5g flower",
                "home_grow": "6 plants",
                "public_consumption": False,
                "dispensary_hours": "6am-10pm"
            },
            "CO": {
                "legal_age": 21,
                "medical_age": 18,
                "possession_limit": "28g flower",
                "home_grow": "6 plants (3 mature)",
                "public_consumption": False,
                "dispensary_hours": "8am-12am"
            }
        }
        
        if state in compliance_data:
            return {
                "state": state,
                "compliance": compliance_data[state],
                "status": "compliant"
            }
        else:
            return {
                "state": state,
                "error": "State compliance data not available",
                "status": "unknown"
            }
    
    def _get_offline_tool_description(self, tool_name: str) -> str:
        """Get description for offline tool"""
        descriptions = {
            "calculate": "Perform mathematical calculations",
            "search_products": "Search cannabis products catalog",
            "strain_lookup": "Get detailed strain information",
            "dosage_calculator": "Calculate recommended dosages",
            "compliance_check": "Check state compliance regulations"
        }
        return descriptions.get(tool_name, "Tool description not available")
    
    def _get_offline_tool_schema(self, tool_name: str) -> Dict[str, Any]:
        """Get input schema for offline tool"""
        schemas = {
            "calculate": {
                "type": "object",
                "properties": {
                    "expression": {"type": "string", "description": "Mathematical expression"}
                },
                "required": ["expression"]
            },
            "search_products": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search query"},
                    "category": {"type": "string", "enum": ["flower", "edible", "tincture", "topical"]}
                }
            },
            "strain_lookup": {
                "type": "object",
                "properties": {
                    "strain": {"type": "string", "description": "Strain name"}
                },
                "required": ["strain"]
            },
            "dosage_calculator": {
                "type": "object",
                "properties": {
                    "weight": {"type": "number", "description": "Body weight in kg"},
                    "experience": {"type": "string", "enum": ["beginner", "intermediate", "experienced"]},
                    "product_type": {"type": "string", "enum": ["flower", "edible", "tincture"]}
                },
                "required": ["weight", "experience", "product_type"]
            },
            "compliance_check": {
                "type": "object",
                "properties": {
                    "state": {"type": "string", "description": "US state code"},
                    "type": {"type": "string", "enum": ["general", "medical", "recreational"]}
                },
                "required": ["state"]
            }
        }
        return schemas.get(tool_name, {"type": "object", "properties": {}})
    
    async def register_mcp_server(
        self,
        name: str,
        url: Optional[str] = None,
        command: Optional[str] = None,
        transport: TransportType = TransportType.HTTP
    ) -> bool:
        """Manually register an MCP server
        
        Args:
            name: Server name
            url: Server URL (for HTTP/WebSocket)
            command: Server command (for stdio)
            transport: Transport type
            
        Returns:
            True if registration successful
        """
        try:
            if not self.mcp_client:
                self.mcp_client = MCPClient()
            
            # Create server configuration
            server = MCPServer(
                name=name,
                version="1.0.0",
                transport=transport,
                url=url,
                command=command
            )
            
            # Register and connect
            self.mcp_client.discovery.register_server(server)
            
            if await self.mcp_client.connect(server):
                # Load tools
                tools = await self.mcp_client.list_tools(server.id)
                for tool in tools:
                    self.available_tools[tool.name] = tool
                    self.tool_mapping[tool.name] = server.id
                
                self.mcp_enabled = True
                logger.info(f"Registered and connected to MCP server: {name}")
                return True
            
        except Exception as e:
            logger.error(f"Failed to register MCP server: {e}")
        
        return False
    
    async def cleanup(self) -> None:
        """Clean up resources"""
        if self.mcp_client:
            await self.mcp_client.cleanup()
            self.mcp_client = None
        
        self.available_tools.clear()
        self.tool_mapping.clear()
        self.mcp_enabled = False