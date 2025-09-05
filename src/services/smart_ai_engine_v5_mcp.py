"""
Smart AI Engine V5 with MCP Integration
Extends the base V5 engine with MCP (Model Context Protocol) capabilities
"""
import asyncio
import logging
import time
from typing import Dict, Any, Optional, List
from pathlib import Path

# Import base V5 engine
from .smart_ai_engine_v5 import SmartAIEngineV5

# Import MCP adapter
from .mcp_adapter import MCPAdapter

logger = logging.getLogger(__name__)

class SmartAIEngineV5MCP(SmartAIEngineV5):
    """
    V5 Engine enhanced with MCP support
    Maintains offline capabilities while adding MCP tools when available
    """
    
    def __init__(self):
        """Initialize MCP-enhanced engine"""
        super().__init__()
        
        self.mcp_adapter: Optional[MCPAdapter] = None
        self.mcp_enabled = False
        self.mcp_tools_registered = False
        
        # Initialize MCP in background
        asyncio.create_task(self._initialize_mcp())
    
    async def _initialize_mcp(self) -> None:
        """Initialize MCP adapter asynchronously"""
        try:
            logger.info("Initializing MCP integration...")
            
            self.mcp_adapter = MCPAdapter(offline_fallback=True)
            self.mcp_enabled = await self.mcp_adapter.initialize()
            
            if self.mcp_enabled:
                logger.info("MCP integration enabled successfully")
                # Register MCP tools with the engine
                await self._register_mcp_tools()
            else:
                logger.info("MCP not available, using offline tools")
                
        except Exception as e:
            logger.error(f"Failed to initialize MCP: {e}")
            self.mcp_enabled = False
    
    async def _register_mcp_tools(self) -> None:
        """Register MCP tools with the V5 engine"""
        if not self.mcp_adapter or not self.tool_manager:
            return
        
        try:
            # Get available MCP tools
            mcp_tools = self.mcp_adapter.get_available_tools()
            
            for tool_name, tool_info in mcp_tools.items():
                # Create wrapper for MCP tool
                mcp_tool_wrapper = self._create_mcp_tool_wrapper(tool_name, tool_info)
                
                # Register with tool manager
                if hasattr(self.tool_manager, 'register_tool'):
                    self.tool_manager.register_tool(tool_name, mcp_tool_wrapper)
                    logger.debug(f"Registered MCP tool: {tool_name}")
            
            self.mcp_tools_registered = True
            logger.info(f"Registered {len(mcp_tools)} MCP tools")
            
        except Exception as e:
            logger.error(f"Failed to register MCP tools: {e}")
    
    def _create_mcp_tool_wrapper(self, tool_name: str, tool_info: Dict[str, Any]):
        """Create a wrapper function for MCP tools"""
        async def mcp_tool_executor(**kwargs) -> Any:
            """Execute MCP tool"""
            if not self.mcp_adapter:
                return {"error": "MCP adapter not initialized"}
            
            result = await self.mcp_adapter.execute_tool(
                tool_name,
                kwargs,
                context={"session_id": getattr(self, 'current_session_id', None)}
            )
            
            return result
        
        # Add metadata to the wrapper
        mcp_tool_executor.__name__ = tool_name
        mcp_tool_executor.__doc__ = tool_info.get("description", "MCP tool")
        mcp_tool_executor.schema = tool_info.get("input_schema", {})
        
        return mcp_tool_executor
    
    async def process_message(
        self,
        message: str,
        context: Optional[Dict[str, Any]] = None,
        session_id: Optional[str] = None,
        use_mcp: bool = True
    ) -> Dict[str, Any]:
        """
        Process message with MCP support
        
        Args:
            message: User message
            context: Message context
            session_id: Session identifier
            use_mcp: Whether to use MCP tools if available
            
        Returns:
            Response dictionary
        """
        # Store session ID for MCP context
        self.current_session_id = session_id
        
        # Check if MCP tools should be used
        if use_mcp and self.mcp_enabled and not self.mcp_tools_registered:
            # Try to register MCP tools if not done yet
            await self._register_mcp_tools()
        
        # Check for MCP-specific commands
        if message.startswith("@mcp"):
            return await self._handle_mcp_command(message, context)
        
        # Process normally through base engine
        # Convert async MCP tools to sync for compatibility
        response = super().process_message(message, context, session_id)
        
        # If response involves tool calls, check if they're MCP tools
        if isinstance(response, dict) and "tools_used" in response:
            tools_used = response.get("tools_used", [])
            mcp_tools = []
            
            for tool in tools_used:
                if self.mcp_adapter and tool in self.mcp_adapter.available_tools:
                    mcp_tools.append(tool)
            
            if mcp_tools:
                response["mcp_tools_used"] = mcp_tools
        
        return response
    
    async def _handle_mcp_command(self, message: str, context: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Handle MCP-specific commands"""
        parts = message.split(maxsplit=2)
        
        if len(parts) < 2:
            return {
                "response": "MCP command format: @mcp <command> [args]",
                "commands": ["status", "list", "connect", "disconnect", "tool"]
            }
        
        command = parts[1].lower()
        args = parts[2] if len(parts) > 2 else ""
        
        if command == "status":
            return await self._get_mcp_status()
        
        elif command == "list":
            if not self.mcp_adapter:
                return {"response": "MCP not initialized"}
            
            tools = self.mcp_adapter.get_available_tools()
            return {
                "response": f"Available MCP tools: {len(tools)}",
                "tools": list(tools.keys()),
                "details": tools
            }
        
        elif command == "connect":
            if not args:
                return {"response": "Usage: @mcp connect <server_name_or_url>"}
            
            success = await self._connect_mcp_server(args)
            return {
                "response": f"Connected to {args}" if success else f"Failed to connect to {args}",
                "success": success
            }
        
        elif command == "disconnect":
            if self.mcp_adapter and self.mcp_adapter.mcp_client:
                await self.mcp_adapter.mcp_client.disconnect()
                return {"response": "Disconnected from MCP servers"}
            return {"response": "No active MCP connections"}
        
        elif command == "tool":
            if not args:
                return {"response": "Usage: @mcp tool <tool_name> <json_args>"}
            
            tool_parts = args.split(maxsplit=1)
            tool_name = tool_parts[0]
            tool_args = {}
            
            if len(tool_parts) > 1:
                try:
                    import json
                    tool_args = json.loads(tool_parts[1])
                except:
                    return {"response": "Invalid JSON arguments"}
            
            if not self.mcp_adapter:
                return {"response": "MCP not initialized"}
            
            result = await self.mcp_adapter.execute_tool(tool_name, tool_args, context)
            return {"response": "Tool executed", "result": result}
        
        else:
            return {
                "response": f"Unknown MCP command: {command}",
                "commands": ["status", "list", "connect", "disconnect", "tool"]
            }
    
    async def _get_mcp_status(self) -> Dict[str, Any]:
        """Get MCP status information"""
        status = {
            "mcp_enabled": self.mcp_enabled,
            "mcp_tools_registered": self.mcp_tools_registered,
            "adapter_initialized": self.mcp_adapter is not None
        }
        
        if self.mcp_adapter:
            status["available_tools"] = len(self.mcp_adapter.available_tools)
            status["offline_fallback"] = self.mcp_adapter.offline_fallback
            
            if self.mcp_adapter.mcp_client:
                status["connected_servers"] = self.mcp_adapter.mcp_client.get_connected_servers()
        
        return {
            "response": "MCP Status",
            "status": status
        }
    
    async def _connect_mcp_server(self, server_spec: str) -> bool:
        """Connect to an MCP server"""
        if not self.mcp_adapter:
            self.mcp_adapter = MCPAdapter(offline_fallback=True)
            await self.mcp_adapter.initialize()
        
        # Check if it's a URL or server name
        if server_spec.startswith("http") or server_spec.startswith("ws"):
            # URL provided
            from core.mcp.mcp_types import TransportType
            
            if server_spec.startswith("ws"):
                transport = TransportType.WEBSOCKET
            else:
                transport = TransportType.HTTP
            
            return await self.mcp_adapter.register_mcp_server(
                name=f"custom_{int(time.time())}",
                url=server_spec,
                transport=transport
            )
        else:
            # Server name provided
            if self.mcp_adapter.mcp_client:
                return await self.mcp_adapter.mcp_client.connect_by_name(server_spec)
        
        return False
    
    async def stream_response(
        self,
        message: str,
        context: Optional[Dict[str, Any]] = None,
        session_id: Optional[str] = None
    ):
        """Stream response with MCP support"""
        # Store session ID
        self.current_session_id = session_id
        
        # Check for MCP command
        if message.startswith("@mcp"):
            result = await self._handle_mcp_command(message, context)
            yield result.get("response", "MCP command processed")
            return
        
        # Stream from base engine
        # Note: This is a simplified version - actual implementation would need
        # to handle async properly
        try:
            response = super().process_message(message, context, session_id)
            
            if isinstance(response, str):
                # Simple string response
                for word in response.split():
                    yield word + " "
                    await asyncio.sleep(0.05)  # Small delay for streaming effect
            elif isinstance(response, dict):
                # Structured response
                text = response.get("response", "")
                for word in text.split():
                    yield word + " "
                    await asyncio.sleep(0.05)
        except Exception as e:
            logger.error(f"Streaming error: {e}")
            yield f"Error: {str(e)}"
    
    def get_tool_schemas(self, format: str = "openai") -> List[Dict[str, Any]]:
        """Get all tool schemas including MCP tools"""
        schemas = []
        
        # Get base tool schemas
        if hasattr(super(), 'get_tool_schemas'):
            schemas.extend(super().get_tool_schemas(format))
        
        # Add MCP tool schemas
        if self.mcp_adapter:
            mcp_schemas = self.mcp_adapter.get_tool_schemas(format)
            schemas.extend(mcp_schemas)
        
        return schemas
    
    async def cleanup(self) -> None:
        """Clean up resources including MCP connections"""
        # Clean up MCP adapter
        if self.mcp_adapter:
            await self.mcp_adapter.cleanup()
            self.mcp_adapter = None
        
        # Clean up base engine
        if hasattr(super(), 'cleanup'):
            super().cleanup()
        
        logger.info("V5 MCP engine cleaned up")

# Factory function to create MCP-enhanced engine
def create_mcp_engine() -> SmartAIEngineV5MCP:
    """Create and return an MCP-enhanced V5 engine instance"""
    return SmartAIEngineV5MCP()

# Async initialization helper
async def initialize_mcp_engine() -> SmartAIEngineV5MCP:
    """Initialize and return a fully configured MCP engine"""
    engine = SmartAIEngineV5MCP()
    
    # Wait for MCP initialization
    max_wait = 10  # seconds
    start_time = time.time()
    
    while not engine.mcp_adapter and (time.time() - start_time) < max_wait:
        await asyncio.sleep(0.5)
    
    if engine.mcp_enabled:
        logger.info("MCP engine initialized with MCP support")
    else:
        logger.info("MCP engine initialized in offline mode")
    
    return engine