"""Base classes for tool system"""

from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from abc import ABC, abstractmethod
import logging

logger = logging.getLogger(__name__)

@dataclass
class ToolResult:
    """Result from tool execution"""
    success: bool
    data: Any = None
    error: Optional[str] = None

class ITool(ABC):
    """Base interface for tools"""
    
    @abstractmethod
    def name(self) -> str:
        """Return tool name"""
        pass
    
    @abstractmethod
    async def execute(self, **kwargs) -> ToolResult:
        """Execute the tool"""
        pass

class ToolManager:
    """Manages available tools"""
    
    def __init__(self):
        self.tools: Dict[str, ITool] = {}
        logger.info("ToolManager initialized")
    
    def register(self, tool: ITool):
        """Register a new tool"""
        self.tools[tool.name()] = tool
        logger.info(f"Registered tool: {tool.name()}")
    
    def list_tools(self) -> List[str]:
        """List available tool names"""
        return list(self.tools.keys())
    
    async def execute_tool(self, name: str, **kwargs) -> ToolResult:
        """Execute a tool by name"""
        if name not in self.tools:
            return ToolResult(success=False, error=f"Tool {name} not found")
        
        try:
            return await self.tools[name].execute(**kwargs)
        except Exception as e:
            logger.error(f"Tool {name} execution failed: {e}")
            return ToolResult(success=False, error=str(e))