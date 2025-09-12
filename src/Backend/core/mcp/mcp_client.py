"""
MCP Client Implementation
Main client for interacting with MCP servers
"""
import asyncio
import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Callable
from .mcp_types import (
    MCPRequest, MCPResponse, MCPServer, MCPTool,
    MCPResource, MCPPrompt, MCPSession, MCPError,
    MCPErrorCode, TransportType
)
from .mcp_transport import create_transport, MCPTransport
from .mcp_discovery import MCPDiscovery

logger = logging.getLogger(__name__)

class MCPClientInterface(ABC):
    """Abstract interface for MCP clients"""
    
    @abstractmethod
    async def connect(self, server: MCPServer) -> bool:
        """Connect to MCP server"""
        pass
    
    @abstractmethod
    async def disconnect(self) -> None:
        """Disconnect from MCP server"""
        pass
    
    @abstractmethod
    async def execute(self, request: MCPRequest) -> MCPResponse:
        """Execute MCP request"""
        pass
    
    @abstractmethod
    async def list_tools(self) -> List[MCPTool]:
        """List available tools"""
        pass
    
    @abstractmethod
    async def call_tool(self, name: str, arguments: Dict[str, Any]) -> Any:
        """Call a specific tool"""
        pass

class MCPClient(MCPClientInterface):
    """MCP client for communicating with MCP servers"""
    
    def __init__(self, discovery: Optional[MCPDiscovery] = None):
        """Initialize MCP client
        
        Args:
            discovery: MCPDiscovery instance for server discovery
        """
        self.discovery = discovery or MCPDiscovery()
        self.sessions: Dict[str, MCPSession] = {}
        self.transports: Dict[str, MCPTransport] = {}
        self.tools_cache: Dict[str, List[MCPTool]] = {}
        self.resources_cache: Dict[str, List[MCPResource]] = {}
        self.prompts_cache: Dict[str, List[MCPPrompt]] = {}
    
    async def discover_servers(self) -> List[MCPServer]:
        """Discover available MCP servers
        
        Returns:
            List of discovered servers
        """
        return await self.discovery.discover_servers()
    
    async def connect(self, server: MCPServer) -> bool:
        """Connect to MCP server
        
        Args:
            server: MCPServer to connect to
            
        Returns:
            True if connected successfully
        """
        try:
            # Check if already connected
            if server.id in self.sessions and self.sessions[server.id].connected:
                logger.debug(f"Already connected to {server.name}")
                return True
            
            # Create transport
            transport_config = {
                "url": server.url,
                "command": server.command,
                "args": server.args,
                "env": server.env
            }
            
            transport = create_transport(server.transport, **transport_config)
            
            # Connect transport
            if not await transport.connect():
                logger.error(f"Failed to connect transport to {server.name}")
                return False
            
            # Store transport and session
            self.transports[server.id] = transport
            self.sessions[server.id] = MCPSession(
                server=server,
                connected=True
            )
            
            # Load server capabilities
            await self._load_server_info(server.id)
            
            logger.info(f"Connected to MCP server: {server.name}")
            return True
            
        except Exception as e:
            logger.error(f"Connection to {server.name} failed: {e}")
            return False
    
    async def connect_by_name(self, server_name: str) -> bool:
        """Connect to server by name
        
        Args:
            server_name: Name of server to connect
            
        Returns:
            True if connected successfully
        """
        server = self.discovery.get_server(server_name)
        if not server:
            logger.error(f"Server '{server_name}' not found")
            return False
        
        return await self.connect(server)
    
    async def disconnect(self, server_id: Optional[str] = None) -> None:
        """Disconnect from MCP server(s)
        
        Args:
            server_id: Optional server ID. If None, disconnect all.
        """
        if server_id:
            await self._disconnect_server(server_id)
        else:
            # Disconnect all servers
            server_ids = list(self.sessions.keys())
            for sid in server_ids:
                await self._disconnect_server(sid)
    
    async def _disconnect_server(self, server_id: str) -> None:
        """Disconnect specific server"""
        try:
            if server_id in self.transports:
                await self.transports[server_id].disconnect()
                del self.transports[server_id]
            
            if server_id in self.sessions:
                self.sessions[server_id].connected = False
                del self.sessions[server_id]
            
            # Clear caches
            self.tools_cache.pop(server_id, None)
            self.resources_cache.pop(server_id, None)
            self.prompts_cache.pop(server_id, None)
            
            logger.info(f"Disconnected from server: {server_id}")
            
        except Exception as e:
            logger.error(f"Error disconnecting from {server_id}: {e}")
    
    async def execute(self, request: MCPRequest, server_id: Optional[str] = None) -> MCPResponse:
        """Execute MCP request
        
        Args:
            request: MCPRequest to execute
            server_id: Optional server ID. If None, use first connected.
            
        Returns:
            MCPResponse from server
        """
        # Get server ID
        if not server_id:
            connected = [sid for sid, session in self.sessions.items() if session.connected]
            if not connected:
                return MCPResponse(
                    id=request.id,
                    error=MCPError(
                        code=MCPErrorCode.CONNECTION_ERROR.value,
                        message="No connected servers"
                    )
                )
            server_id = connected[0]
        
        # Check if connected
        if server_id not in self.transports:
            return MCPResponse(
                id=request.id,
                error=MCPError(
                    code=MCPErrorCode.CONNECTION_ERROR.value,
                    message=f"Not connected to server {server_id}"
                )
            )
        
        # Send request
        transport = self.transports[server_id]
        response = await transport.send_request(request)
        
        # Update session activity
        if server_id in self.sessions:
            import datetime
            self.sessions[server_id].last_activity = datetime.datetime.now()
        
        return response
    
    async def list_tools(self, server_id: Optional[str] = None) -> List[MCPTool]:
        """List available tools from server(s)
        
        Args:
            server_id: Optional server ID. If None, list from all.
            
        Returns:
            List of available tools
        """
        if server_id:
            return await self._list_server_tools(server_id)
        
        # List from all connected servers
        all_tools = []
        for sid in self.sessions:
            if self.sessions[sid].connected:
                tools = await self._list_server_tools(sid)
                all_tools.extend(tools)
        
        return all_tools
    
    async def _list_server_tools(self, server_id: str) -> List[MCPTool]:
        """List tools from specific server"""
        # Check cache
        if server_id in self.tools_cache:
            return self.tools_cache[server_id]
        
        # Request tools list
        request = MCPRequest(method="tools/list")
        response = await self.execute(request, server_id)
        
        if not response.is_success():
            logger.error(f"Failed to list tools: {response.error}")
            return []
        
        # Parse tools
        tools = []
        for tool_data in response.result.get("tools", []):
            try:
                tool = MCPTool(
                    name=tool_data["name"],
                    description=tool_data.get("description", ""),
                    input_schema=tool_data.get("inputSchema", {}),
                    output_schema=tool_data.get("outputSchema"),
                    tags=tool_data.get("tags", []),
                    examples=tool_data.get("examples", [])
                )
                tools.append(tool)
            except Exception as e:
                logger.warning(f"Failed to parse tool: {e}")
        
        # Cache tools
        self.tools_cache[server_id] = tools
        
        return tools
    
    async def call_tool(
        self,
        name: str,
        arguments: Dict[str, Any],
        server_id: Optional[str] = None
    ) -> Any:
        """Call a specific tool
        
        Args:
            name: Tool name
            arguments: Tool arguments
            server_id: Optional server ID
            
        Returns:
            Tool execution result
        """
        # Find server with the tool
        if not server_id:
            server_id = await self._find_server_with_tool(name)
            if not server_id:
                raise ValueError(f"Tool '{name}' not found in any connected server")
        
        # Create tool call request
        request = MCPRequest(
            method="tools/call",
            params={
                "name": name,
                "arguments": arguments
            }
        )
        
        # Execute request
        response = await self.execute(request, server_id)
        
        if not response.is_success():
            raise RuntimeError(f"Tool call failed: {response.error.message}")
        
        return response.result.get("content", [])
    
    async def _find_server_with_tool(self, tool_name: str) -> Optional[str]:
        """Find server that has specific tool"""
        for server_id in self.sessions:
            if self.sessions[server_id].connected:
                tools = await self._list_server_tools(server_id)
                if any(tool.name == tool_name for tool in tools):
                    return server_id
        return None
    
    async def list_resources(self, server_id: Optional[str] = None) -> List[MCPResource]:
        """List available resources
        
        Args:
            server_id: Optional server ID
            
        Returns:
            List of resources
        """
        if server_id:
            return await self._list_server_resources(server_id)
        
        # List from all servers
        all_resources = []
        for sid in self.sessions:
            if self.sessions[sid].connected:
                resources = await self._list_server_resources(sid)
                all_resources.extend(resources)
        
        return all_resources
    
    async def _list_server_resources(self, server_id: str) -> List[MCPResource]:
        """List resources from specific server"""
        # Check cache
        if server_id in self.resources_cache:
            return self.resources_cache[server_id]
        
        # Request resources list
        request = MCPRequest(method="resources/list")
        response = await self.execute(request, server_id)
        
        if not response.is_success():
            logger.error(f"Failed to list resources: {response.error}")
            return []
        
        # Parse resources
        resources = []
        for res_data in response.result.get("resources", []):
            try:
                resource = MCPResource(
                    uri=res_data["uri"],
                    name=res_data["name"],
                    description=res_data.get("description"),
                    mime_type=res_data.get("mimeType", "text/plain"),
                    metadata=res_data.get("metadata", {})
                )
                resources.append(resource)
            except Exception as e:
                logger.warning(f"Failed to parse resource: {e}")
        
        # Cache resources
        self.resources_cache[server_id] = resources
        
        return resources
    
    async def read_resource(
        self,
        uri: str,
        server_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Read resource content
        
        Args:
            uri: Resource URI
            server_id: Optional server ID
            
        Returns:
            Resource content
        """
        # Find server with resource
        if not server_id:
            server_id = await self._find_server_with_resource(uri)
            if not server_id:
                raise ValueError(f"Resource '{uri}' not found")
        
        # Create read request
        request = MCPRequest(
            method="resources/read",
            params={"uri": uri}
        )
        
        # Execute request
        response = await self.execute(request, server_id)
        
        if not response.is_success():
            raise RuntimeError(f"Resource read failed: {response.error.message}")
        
        return response.result.get("contents", [])
    
    async def _find_server_with_resource(self, uri: str) -> Optional[str]:
        """Find server with specific resource"""
        for server_id in self.sessions:
            if self.sessions[server_id].connected:
                resources = await self._list_server_resources(server_id)
                if any(res.uri == uri for res in resources):
                    return server_id
        return None
    
    async def list_prompts(self, server_id: Optional[str] = None) -> List[MCPPrompt]:
        """List available prompts
        
        Args:
            server_id: Optional server ID
            
        Returns:
            List of prompts
        """
        if server_id:
            return await self._list_server_prompts(server_id)
        
        # List from all servers
        all_prompts = []
        for sid in self.sessions:
            if self.sessions[sid].connected:
                prompts = await self._list_server_prompts(sid)
                all_prompts.extend(prompts)
        
        return all_prompts
    
    async def _list_server_prompts(self, server_id: str) -> List[MCPPrompt]:
        """List prompts from specific server"""
        # Check cache
        if server_id in self.prompts_cache:
            return self.prompts_cache[server_id]
        
        # Request prompts list
        request = MCPRequest(method="prompts/list")
        response = await self.execute(request, server_id)
        
        if not response.is_success():
            logger.error(f"Failed to list prompts: {response.error}")
            return []
        
        # Parse prompts
        prompts = []
        for prompt_data in response.result.get("prompts", []):
            try:
                prompt = MCPPrompt(
                    name=prompt_data["name"],
                    description=prompt_data.get("description", ""),
                    arguments=prompt_data.get("arguments", []),
                    template=prompt_data.get("template", ""),
                    tags=prompt_data.get("tags", [])
                )
                prompts.append(prompt)
            except Exception as e:
                logger.warning(f"Failed to parse prompt: {e}")
        
        # Cache prompts
        self.prompts_cache[server_id] = prompts
        
        return prompts
    
    async def get_prompt(
        self,
        name: str,
        arguments: Dict[str, Any],
        server_id: Optional[str] = None
    ) -> str:
        """Get rendered prompt
        
        Args:
            name: Prompt name
            arguments: Prompt arguments
            server_id: Optional server ID
            
        Returns:
            Rendered prompt text
        """
        # Find server with prompt
        if not server_id:
            server_id = await self._find_server_with_prompt(name)
            if not server_id:
                raise ValueError(f"Prompt '{name}' not found")
        
        # Create prompt request
        request = MCPRequest(
            method="prompts/get",
            params={
                "name": name,
                "arguments": arguments
            }
        )
        
        # Execute request
        response = await self.execute(request, server_id)
        
        if not response.is_success():
            raise RuntimeError(f"Prompt get failed: {response.error.message}")
        
        # Extract prompt text
        messages = response.result.get("messages", [])
        if messages:
            return messages[0].get("content", {}).get("text", "")
        
        return ""
    
    async def _find_server_with_prompt(self, prompt_name: str) -> Optional[str]:
        """Find server with specific prompt"""
        for server_id in self.sessions:
            if self.sessions[server_id].connected:
                prompts = await self._list_server_prompts(server_id)
                if any(prompt.name == prompt_name for prompt in prompts):
                    return server_id
        return None
    
    async def _load_server_info(self, server_id: str) -> None:
        """Load server capabilities and cache info"""
        try:
            # Get server info
            request = MCPRequest(method="initialize", params={"protocolVersion": "1.0"})
            response = await self.execute(request, server_id)
            
            if response.is_success() and server_id in self.sessions:
                server_info = response.result.get("serverInfo", {})
                capabilities = response.result.get("capabilities", {})
                
                # Update server metadata
                session = self.sessions[server_id]
                session.metadata["serverInfo"] = server_info
                session.metadata["capabilities"] = capabilities
                
                # Update server capabilities
                if session.server:
                    session.server.capabilities.tools = capabilities.get("tools", {}) != {}
                    session.server.capabilities.resources = capabilities.get("resources", {}) != {}
                    session.server.capabilities.prompts = capabilities.get("prompts", {}) != {}
                    session.server.capabilities.sampling = capabilities.get("sampling", {}) != {}
                
        except Exception as e:
            logger.warning(f"Failed to load server info: {e}")
    
    def get_connected_servers(self) -> List[str]:
        """Get list of connected server IDs
        
        Returns:
            List of connected server IDs
        """
        return [sid for sid, session in self.sessions.items() if session.connected]
    
    def is_connected(self, server_id: str) -> bool:
        """Check if connected to specific server
        
        Args:
            server_id: Server ID to check
            
        Returns:
            True if connected
        """
        return server_id in self.sessions and self.sessions[server_id].connected
    
    async def cleanup(self) -> None:
        """Clean up all connections"""
        await self.disconnect()