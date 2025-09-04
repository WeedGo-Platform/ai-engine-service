"""Base tool interface and implementations for the AI engine"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from dataclasses import dataclass
import json
import logging

logger = logging.getLogger(__name__)

@dataclass
class ToolResult:
    """Result from tool execution"""
    success: bool
    data: Any
    error: Optional[str] = None
    metadata: Optional[Dict] = None

class ITool(ABC):
    """Interface for all tools"""
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Tool name"""
        pass
    
    @property
    @abstractmethod
    def description(self) -> str:
        """Tool description for LLM"""
        pass
    
    @property
    @abstractmethod
    def parameters(self) -> Dict:
        """Parameter schema for the tool"""
        pass
    
    @abstractmethod
    async def execute(self, **kwargs) -> ToolResult:
        """Execute the tool with given parameters"""
        pass
    
    def to_function_schema(self) -> Dict:
        """Convert to OpenAI function calling schema"""
        return {
            "name": self.name,
            "description": self.description,
            "parameters": self.parameters
        }

class SearchTool(ITool):
    """Base search tool for product searches"""
    
    @property
    def name(self) -> str:
        return "search_products"
    
    @property
    def description(self) -> str:
        return "Search for cannabis products in inventory"
    
    @property
    def parameters(self) -> Dict:
        return {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Search query for products"
                },
                "category": {
                    "type": "string",
                    "enum": ["flower", "edibles", "pre-rolls", "concentrates", "all"],
                    "description": "Product category to search in"
                },
                "limit": {
                    "type": "integer",
                    "default": 5,
                    "description": "Maximum number of results"
                }
            },
            "required": ["query"]
        }
    
    async def execute(self, query: str, category: str = "all", limit: int = 5, **kwargs) -> ToolResult:
        """Execute product search"""
        try:
            # This would connect to actual product database
            # For now, return mock data
            mock_products = [
                {"name": "Blue Dream", "category": "flower", "thc": "22%", "price": "$45"},
                {"name": "OG Kush Pre-Roll", "category": "pre-rolls", "thc": "20%", "price": "$15"},
                {"name": "THC Gummies", "category": "edibles", "thc": "10mg", "price": "$20"}
            ]
            
            results = [p for p in mock_products if query.lower() in p["name"].lower()][:limit]
            
            return ToolResult(
                success=True,
                data=results,
                metadata={"query": query, "category": category, "count": len(results)}
            )
        except Exception as e:
            return ToolResult(success=False, data=None, error=str(e))

class CalculatorTool(ITool):
    """Basic calculator tool"""
    
    @property
    def name(self) -> str:
        return "calculator"
    
    @property
    def description(self) -> str:
        return "Perform basic mathematical calculations"
    
    @property
    def parameters(self) -> Dict:
        return {
            "type": "object",
            "properties": {
                "expression": {
                    "type": "string",
                    "description": "Mathematical expression to evaluate"
                }
            },
            "required": ["expression"]
        }
    
    async def execute(self, expression: str, **kwargs) -> ToolResult:
        """Execute calculation"""
        try:
            # Safe evaluation of mathematical expressions
            import ast
            import operator as op
            
            # Supported operators
            operators = {
                ast.Add: op.add, ast.Sub: op.sub, ast.Mult: op.mul,
                ast.Div: op.truediv, ast.Pow: op.pow, ast.USub: op.neg
            }
            
            def eval_expr(expr):
                """Safely evaluate mathematical expression"""
                def _eval(node):
                    if isinstance(node, ast.Constant):  # Python 3.8+
                        return node.value
                    elif isinstance(node, ast.BinOp):
                        return operators[type(node.op)](_eval(node.left), _eval(node.right))
                    elif isinstance(node, ast.UnaryOp):
                        return operators[type(node.op)](_eval(node.operand))
                    else:
                        raise TypeError(f"Unsupported type {type(node)}")
                
                return _eval(ast.parse(expr, mode='eval').body)
            
            result = eval_expr(expression)
            return ToolResult(
                success=True,
                data={"expression": expression, "result": result},
                metadata={"type": "calculation"}
            )
        except Exception as e:
            return ToolResult(success=False, data=None, error=f"Calculation error: {str(e)}")

class ToolManager:
    """Manages available tools for an agent"""
    
    def __init__(self):
        self.tools: Dict[str, ITool] = {}
        self._load_base_tools()
    
    def _load_base_tools(self):
        """Load base tools available to all agents"""
        self.register_tool(SearchTool())
        self.register_tool(CalculatorTool())
    
    def register_tool(self, tool: ITool):
        """Register a tool"""
        self.tools[tool.name] = tool
        logger.info(f"Registered tool: {tool.name}")
    
    def get_tool(self, name: str) -> Optional[ITool]:
        """Get tool by name"""
        return self.tools.get(name)
    
    def list_tools(self) -> List[str]:
        """List available tool names"""
        return list(self.tools.keys())
    
    def get_function_schemas(self) -> List[Dict]:
        """Get all tool schemas for function calling"""
        return [tool.to_function_schema() for tool in self.tools.values()]
    
    async def execute_tool(self, name: str, parameters: Dict) -> ToolResult:
        """Execute a tool by name with parameters"""
        tool = self.get_tool(name)
        if not tool:
            return ToolResult(success=False, data=None, error=f"Tool '{name}' not found")
        
        try:
            return await tool.execute(**parameters)
        except Exception as e:
            logger.error(f"Tool execution error for {name}: {e}")
            return ToolResult(success=False, data=None, error=str(e))