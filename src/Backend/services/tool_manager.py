"""
Tool Management Service
Implements IToolManager interface following SOLID principles
Handles tool registration, execution, and enrollment
"""

import json
import re
import logging
from typing import Dict, List, Any, Optional, Callable
from pathlib import Path
import sys
import importlib
import inspect

# Import interfaces
sys.path.append(str(Path(__file__).parent.parent))
from core.interfaces import IToolManager, IDatabaseSearchTool, IDatabaseConnectionManager

logger = logging.getLogger(__name__)


class ToolManager(IToolManager):
    """
    Tool Manager implementation
    Single Responsibility: Tool lifecycle and execution management
    """
    
    def __init__(self, agent_pool=None):
        """Initialize the Tool Manager

        Args:
            agent_pool: Optional reference to agent pool for LLM-based features
        """
        self.tools = {}
        self.tool_instances = {}
        self.agent_tools = {}  # Maps agent_id to enrolled tools
        self.tool_configs = {}
        self.connection_manager = None
        self.agent_pool = agent_pool  # Store agent pool reference

        # Register built-in tools
        self._register_builtin_tools()

        logger.info(f"ToolManager initialized with {len(self.tools)} built-in tools")
    
    def _register_builtin_tools(self):
        """Register built-in tools"""
        # Register database search tool
        self.register_tool(
            "database_search",
            self._create_database_search_tool,
            {
                "description": "Search database for products and information",
                "category": "database",
                "requires_connection": True
            }
        )

        # Register smart product search tool (primary product search)
        self.register_tool(
            "smart_product_search",
            self._create_smart_product_search_tool,
            {
                "description": "Search products using API with context awareness",
                "category": "search",
                "requires_context": True
            }
        )

        # Register product search tool (wrapper)
        self.register_tool(
            "search_products",
            self._search_products_wrapper,
            {
                "description": "Search for products by various criteria",
                "category": "search"
            }
        )

        # Register category search tool
        self.register_tool(
            "search_by_category",
            self._search_by_category_wrapper,
            {
                "description": "Search products by category",
                "category": "search"
            }
        )

        # Register effects search tool
        self.register_tool(
            "search_by_effects",
            self._search_by_effects_wrapper,
            {
                "description": "Search products by desired effects",
                "category": "search"
            }
        )
    
    def register_tool(self, tool_name: str, tool_function: Callable, 
                     config: Optional[Dict] = None) -> bool:
        """
        Register a new tool
        
        Args:
            tool_name: Name of the tool
            tool_function: Callable that implements the tool
            config: Optional tool configuration
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if tool_name in self.tools:
                logger.warning(f"Tool '{tool_name}' already registered, overwriting")
            
            self.tools[tool_name] = tool_function
            
            if config:
                self.tool_configs[tool_name] = config
            
            logger.info(f"Registered tool: {tool_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to register tool '{tool_name}': {e}")
            return False
    
    async def execute_tool(self, tool_name: str, **kwargs) -> Dict[str, Any]:
        """
        Execute a tool with given parameters

        Args:
            tool_name: Name of the tool to execute
            **kwargs: Tool parameters

        Returns:
            Tool execution result
        """
        if tool_name not in self.tools:
            return {
                "success": False,
                "error": f"Tool '{tool_name}' not found",
                "available_tools": list(self.tools.keys())
            }

        try:
            tool_function = self.tools[tool_name]

            # Check if this is a tool that needs initialization
            if tool_name == "database_search" and tool_name not in self.tool_instances:
                instance = self._create_database_search_tool()
                if instance:
                    self.tool_instances[tool_name] = instance

            if tool_name == "smart_product_search" and tool_name not in self.tool_instances:
                instance = self._create_smart_product_search_tool()
                if instance:
                    self.tool_instances[tool_name] = instance

            # Execute the tool
            if tool_name in self.tool_instances:
                # Use the tool instance
                result = await self._execute_tool_instance(tool_name, **kwargs)
            else:
                # Direct function call
                result = tool_function(**kwargs)

            return {
                "success": True,
                "tool": tool_name,
                "result": result
            }

        except Exception as e:
            logger.error(f"Tool execution failed for '{tool_name}': {e}")
            return {
                "success": False,
                "tool": tool_name,
                "error": str(e)
            }
    
    def list_tools(self) -> List[str]:
        """
        List available tools
        
        Returns:
            List of tool names
        """
        return list(self.tools.keys())
    
    def extract_tool_calls(self, response: str) -> List[Dict]:
        """
        Extract tool calls from a response
        
        Args:
            response: LLM response text
            
        Returns:
            List of extracted tool calls
        """
        tool_calls = []
        
        # Pattern 1: Function call syntax - tool_name(param1=value1, param2=value2)
        pattern1 = r'(\w+)\((.*?)\)'
        matches = re.finditer(pattern1, response)
        
        for match in matches:
            tool_name = match.group(1)
            params_str = match.group(2)
            
            if tool_name in self.tools:
                # Parse parameters
                params = self._parse_tool_params(params_str)
                tool_calls.append({
                    "tool": tool_name,
                    "parameters": params
                })
        
        # Pattern 2: JSON format - {"tool": "tool_name", "parameters": {...}}
        json_pattern = r'\{[^{}]*"tool"[^{}]*\}'
        json_matches = re.finditer(json_pattern, response)
        
        for match in json_matches:
            try:
                tool_call = json.loads(match.group())
                if "tool" in tool_call and tool_call["tool"] in self.tools:
                    tool_calls.append(tool_call)
            except:
                pass
        
        # Pattern 3: Natural language - "search for products with THC > 20"
        if "search" in response.lower():
            # Extract search intent
            search_call = self._extract_search_intent(response)
            if search_call:
                tool_calls.append(search_call)
        
        return tool_calls
    
    def _parse_tool_params(self, params_str: str) -> Dict[str, Any]:
        """
        Parse tool parameters from string
        
        Args:
            params_str: Parameter string
            
        Returns:
            Parsed parameters dictionary
        """
        params = {}
        
        if not params_str:
            return params
        
        # Split by comma (but not within quotes)
        param_parts = re.split(r',(?=(?:[^"]*"[^"]*")*[^"]*$)', params_str)
        
        for part in param_parts:
            if '=' in part:
                key, value = part.split('=', 1)
                key = key.strip()
                value = value.strip()
                
                # Remove quotes if present
                if value.startswith('"') and value.endswith('"'):
                    value = value[1:-1]
                elif value.startswith("'") and value.endswith("'"):
                    value = value[1:-1]
                
                # Try to parse as number
                try:
                    if '.' in value:
                        value = float(value)
                    else:
                        value = int(value)
                except:
                    pass
                
                params[key] = value
        
        return params
    
    def _extract_search_intent(self, text: str) -> Optional[Dict]:
        """
        Extract search intent from natural language
        
        Args:
            text: Natural language text
            
        Returns:
            Tool call dictionary or None
        """
        text_lower = text.lower()
        
        # Category search
        categories = ["flower", "edibles", "concentrates", "vapes", "accessories"]
        for category in categories:
            if category in text_lower:
                return {
                    "tool": "search_by_category",
                    "parameters": {"category": category}
                }
        
        # Effects search
        effects = ["relaxing", "energizing", "creative", "focused", "happy", "sleepy"]
        found_effects = [e for e in effects if e in text_lower]
        if found_effects:
            return {
                "tool": "search_by_effects",
                "parameters": {"effects": found_effects}
            }
        
        # THC/CBD content search
        thc_match = re.search(r'thc\s*[><=]+\s*(\d+)', text_lower)
        cbd_match = re.search(r'cbd\s*[><=]+\s*(\d+)', text_lower)
        
        if thc_match or cbd_match:
            filters = {}
            if thc_match:
                filters["thc_content"] = {"gte": int(thc_match.group(1))}
            if cbd_match:
                filters["cbd_content"] = {"gte": int(cbd_match.group(1))}
            
            return {
                "tool": "search_products",
                "parameters": {"filters": filters}
            }
        
        return None
    
    def enroll_agent_tools(self, agent_id: str, tool_names: List[str]) -> bool:
        """
        Enroll tools for a specific agent
        
        Args:
            agent_id: Agent identifier
            tool_names: List of tool names to enroll
            
        Returns:
            True if successful
        """
        try:
            valid_tools = []
            
            for tool_name in tool_names:
                if tool_name in self.tools:
                    valid_tools.append(tool_name)
                else:
                    logger.warning(f"Tool '{tool_name}' not found for agent '{agent_id}'")
            
            self.agent_tools[agent_id] = valid_tools
            logger.info(f"Enrolled {len(valid_tools)} tools for agent '{agent_id}': {valid_tools}")
            
            # Initialize database tools if enrolled
            if "database_search" in valid_tools:
                self._initialize_database_tool()
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to enroll tools for agent '{agent_id}': {e}")
            return False
    
    def get_agent_tools(self, agent_id: str) -> List[str]:
        """
        Get enrolled tools for an agent
        
        Args:
            agent_id: Agent identifier
            
        Returns:
            List of enrolled tool names
        """
        return self.agent_tools.get(agent_id, [])
    
    def _create_database_search_tool(self) -> Optional[IDatabaseSearchTool]:
        """
        Create database search tool instance

        Returns:
            Database search tool instance or None
        """
        try:
            from services.tools.database_search_tool import DatabaseSearchTool
            from services.database_connection_manager import DatabaseConnectionManager

            if not self.connection_manager:
                self.connection_manager = DatabaseConnectionManager()

            tool = DatabaseSearchTool(self.connection_manager)

            # Auto-connect with default config
            import os
            config = {
                'host': os.getenv('DB_HOST', 'localhost'),
                'port': int(os.getenv('DB_PORT', 5432)),
                'database': os.getenv('DB_NAME', 'weedgo'),
                'user': os.getenv('DB_USER', 'postgres'),
                'password': os.getenv('DB_PASSWORD', 'postgres')
            }

            if tool.connect(config):
                logger.info("Database search tool connected")
                return tool
            else:
                logger.warning("Database search tool failed to connect")
                return None

        except Exception as e:
            logger.error(f"Failed to create database search tool: {e}")
            return None

    def _create_smart_product_search_tool(self):
        """
        Create smart product search tool instance

        Returns:
            Smart product search tool instance or None
        """
        try:
            from services.tools.smart_product_search_tool import SmartProductSearchTool
            import os

            base_url = os.getenv('API_BASE_URL', 'http://localhost:5024')
            tool = SmartProductSearchTool(base_url=base_url, agent_pool=self.agent_pool)

            logger.info(f"Smart product search tool created with base_url: {base_url}, agent_pool: {self.agent_pool is not None}")
            return tool

        except Exception as e:
            logger.error(f"Failed to create smart product search tool: {e}")
            return None
    
    def _initialize_database_tool(self):
        """Initialize database tool if not already done"""
        if "database_search" not in self.tool_instances:
            instance = self._create_database_search_tool()
            if instance:
                self.tool_instances["database_search"] = instance
    
    async def _execute_tool_instance(self, tool_name: str, **kwargs) -> Any:
        """
        Execute a tool instance method

        Args:
            tool_name: Tool name
            **kwargs: Method parameters

        Returns:
            Method result
        """
        instance = self.tool_instances.get(tool_name)
        if not instance:
            raise ValueError(f"Tool instance '{tool_name}' not found")

        # Determine which method to call based on parameters
        if tool_name == "database_search":
            if "filters" in kwargs:
                return instance.search_products(kwargs["filters"])
            elif "category" in kwargs:
                return instance.search_by_category(
                    kwargs["category"],
                    kwargs.get("limit", 10)
                )
            elif "effects" in kwargs:
                return instance.search_by_effects(
                    kwargs["effects"],
                    kwargs.get("limit", 10)
                )
            elif "product_id" in kwargs:
                return instance.get_product_details(kwargs["product_id"])
            elif "query_params" in kwargs:
                return instance.search(kwargs["query_params"])
            else:
                # Generic search
                return instance.search(kwargs)

        elif tool_name == "smart_product_search":
            # Call the smart product search tool with context
            return await instance.search(
                query=kwargs.get("query", ""),
                store_id=kwargs.get("store_id"),
                limit=kwargs.get("limit", 5),
                category=kwargs.get("category"),
                min_thc=kwargs.get("min_thc"),
                max_thc=kwargs.get("max_thc"),
                min_cbd=kwargs.get("min_cbd"),
                max_cbd=kwargs.get("max_cbd"),
                strain_type=kwargs.get("strain_type"),
                session_id=kwargs.get("session_id"),
                user_id=kwargs.get("user_id")
            )

        raise ValueError(f"Unknown tool execution pattern for '{tool_name}'")
    
    # Wrapper functions for database search
    def _search_products_wrapper(self, **kwargs):
        """Wrapper for product search"""
        return self.execute_tool("database_search", filters=kwargs)
    
    def _search_by_category_wrapper(self, category: str, limit: int = 10):
        """Wrapper for category search"""
        return self.execute_tool("database_search", category=category, limit=limit)
    
    def _search_by_effects_wrapper(self, effects: List[str], limit: int = 10):
        """Wrapper for effects search"""
        return self.execute_tool("database_search", effects=effects, limit=limit)
    
    def get_tool_info(self, tool_name: str) -> Dict[str, Any]:
        """
        Get information about a specific tool
        
        Args:
            tool_name: Tool name
            
        Returns:
            Tool information dictionary
        """
        if tool_name not in self.tools:
            return {"error": f"Tool '{tool_name}' not found"}
        
        info = {
            "name": tool_name,
            "available": True,
            "config": self.tool_configs.get(tool_name, {})
        }
        
        # Add function signature if available
        tool_func = self.tools[tool_name]
        if callable(tool_func):
            try:
                sig = inspect.signature(tool_func)
                info["parameters"] = str(sig)
            except:
                pass
        
        return info
    
    def cleanup(self):
        """Cleanup resources"""
        # Close database connections
        for tool_name, instance in self.tool_instances.items():
            if hasattr(instance, 'disconnect'):
                try:
                    instance.disconnect()
                except:
                    pass
        
        if self.connection_manager:
            try:
                self.connection_manager.close_all_connections()
            except:
                pass
        
        logger.info("ToolManager cleanup completed")