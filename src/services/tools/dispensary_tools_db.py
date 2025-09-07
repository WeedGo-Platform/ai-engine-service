"""Database-backed dispensary tools"""

from .base import ITool, ToolResult

class DispensarySearchToolDB(ITool):
    """Database-backed product search"""
    
    def name(self) -> str:
        return "dispensary_search_db"
    
    async def execute(self, **kwargs) -> ToolResult:
        # Placeholder for database implementation
        return ToolResult(success=True, data=[])

class DispensaryStatsToolDB(ITool):
    """Database-backed statistics"""
    
    def name(self) -> str:
        return "dispensary_stats_db"
    
    async def execute(self, **kwargs) -> ToolResult:
        # Placeholder for database implementation
        return ToolResult(success=True, data={})