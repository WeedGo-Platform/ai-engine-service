"""
MCP Discovery Module
Discovers and manages available MCP servers
"""
import json
import os
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
from .mcp_types import MCPServer, TransportType, MCPCapabilities

logger = logging.getLogger(__name__)

class MCPDiscovery:
    """Discovers available MCP servers"""
    
    def __init__(self, config_paths: List[str] = None):
        """Initialize discovery
        
        Args:
            config_paths: Paths to search for MCP configurations
        """
        self.config_paths = config_paths or self._get_default_paths()
        self.servers: Dict[str, MCPServer] = {}
        self._cache_file = Path.home() / ".mcp" / "servers_cache.json"
    
    def _get_default_paths(self) -> List[str]:
        """Get default MCP configuration paths"""
        paths = []
        
        # User home directory
        user_config = Path.home() / ".mcp"
        if user_config.exists():
            paths.append(str(user_config))
        
        # System-wide configuration
        system_configs = [
            "/etc/mcp",
            "/usr/local/etc/mcp"
        ]
        paths.extend([p for p in system_configs if os.path.exists(p)])
        
        # Application directory
        app_config = Path(__file__).parent.parent.parent / "mcp_servers"
        if app_config.exists():
            paths.append(str(app_config))
        
        # Environment variable
        if "MCP_CONFIG_PATH" in os.environ:
            paths.extend(os.environ["MCP_CONFIG_PATH"].split(":"))
        
        return paths
    
    async def discover_servers(self, refresh: bool = False) -> List[MCPServer]:
        """Discover all available MCP servers
        
        Args:
            refresh: Force refresh of server list
            
        Returns:
            List of discovered servers
        """
        if not refresh and self.servers:
            return list(self.servers.values())
        
        self.servers.clear()
        
        # Load from configuration files
        for config_path in self.config_paths:
            await self._scan_directory(config_path)
        
        # Load from cache if exists
        if not self.servers and self._cache_file.exists():
            await self._load_cache()
        
        # Discover from environment
        await self._discover_from_env()
        
        # Save to cache
        await self._save_cache()
        
        logger.info(f"Discovered {len(self.servers)} MCP servers")
        return list(self.servers.values())
    
    async def _scan_directory(self, path: str) -> None:
        """Scan directory for MCP server configurations"""
        path_obj = Path(path)
        if not path_obj.exists():
            return
        
        # Look for JSON configuration files
        for config_file in path_obj.glob("*.json"):
            try:
                with open(config_file, 'r') as f:
                    config = json.load(f)
                    
                if "mcp" in config:
                    server = self._parse_server_config(config["mcp"])
                    if server:
                        self.servers[server.id] = server
                        logger.debug(f"Loaded server {server.name} from {config_file}")
                        
            except Exception as e:
                logger.warning(f"Failed to load config from {config_file}: {e}")
        
        # Look for executable MCP servers
        for exec_file in path_obj.glob("mcp-*"):
            if exec_file.is_file() and os.access(exec_file, os.X_OK):
                server = self._create_stdio_server(exec_file)
                if server:
                    self.servers[server.id] = server
    
    def _parse_server_config(self, config: Dict[str, Any]) -> Optional[MCPServer]:
        """Parse server configuration"""
        try:
            # Determine transport type
            if "command" in config:
                transport = TransportType.STDIO
            elif "websocket" in config or config.get("url", "").startswith("ws"):
                transport = TransportType.WEBSOCKET
            else:
                transport = TransportType.HTTP
            
            # Parse capabilities
            capabilities = MCPCapabilities()
            if "capabilities" in config:
                cap = config["capabilities"]
                capabilities.tools = cap.get("tools", True)
                capabilities.resources = cap.get("resources", True)
                capabilities.prompts = cap.get("prompts", True)
                capabilities.sampling = cap.get("sampling", False)
                capabilities.roots = cap.get("roots", False)
                capabilities.experimental = cap.get("experimental", {})
            
            return MCPServer(
                name=config["name"],
                version=config.get("version", "1.0.0"),
                protocol_version=config.get("protocolVersion", "1.0"),
                capabilities=capabilities,
                transport=transport,
                url=config.get("url"),
                command=config.get("command"),
                args=config.get("args", []),
                env=config.get("env", {}),
                metadata=config.get("metadata", {})
            )
            
        except KeyError as e:
            logger.warning(f"Invalid server config, missing field: {e}")
            return None
    
    def _create_stdio_server(self, exec_path: Path) -> Optional[MCPServer]:
        """Create server config for executable MCP server"""
        try:
            # Extract name from filename (remove mcp- prefix)
            name = exec_path.stem
            if name.startswith("mcp-"):
                name = name[4:]
            
            # Try to get version by running --version
            import subprocess
            try:
                result = subprocess.run(
                    [str(exec_path), "--version"],
                    capture_output=True,
                    text=True,
                    timeout=1
                )
                version = result.stdout.strip() or "1.0.0"
            except:
                version = "1.0.0"
            
            return MCPServer(
                name=name,
                version=version,
                transport=TransportType.STDIO,
                command=str(exec_path),
                metadata={"discovered": "executable"}
            )
            
        except Exception as e:
            logger.warning(f"Failed to create server for {exec_path}: {e}")
            return None
    
    async def _discover_from_env(self) -> None:
        """Discover servers from environment variables"""
        # Check for MCP server environment variables
        for key, value in os.environ.items():
            if key.startswith("MCP_SERVER_"):
                server_name = key[11:].lower()
                
                # Parse connection string
                if value.startswith("http"):
                    server = MCPServer(
                        name=server_name,
                        version="1.0.0",
                        transport=TransportType.HTTP,
                        url=value,
                        metadata={"discovered": "environment"}
                    )
                    self.servers[server.id] = server
                    
                elif value.startswith("ws"):
                    server = MCPServer(
                        name=server_name,
                        version="1.0.0",
                        transport=TransportType.WEBSOCKET,
                        url=value,
                        metadata={"discovered": "environment"}
                    )
                    self.servers[server.id] = server
    
    async def _load_cache(self) -> None:
        """Load servers from cache"""
        try:
            with open(self._cache_file, 'r') as f:
                cache = json.load(f)
                
            for server_data in cache.get("servers", []):
                server = self._parse_server_config(server_data)
                if server:
                    server.metadata["cached"] = True
                    self.servers[server.id] = server
                    
        except Exception as e:
            logger.debug(f"Failed to load cache: {e}")
    
    async def _save_cache(self) -> None:
        """Save servers to cache"""
        try:
            self._cache_file.parent.mkdir(parents=True, exist_ok=True)
            
            cache = {
                "servers": [
                    {
                        "name": server.name,
                        "version": server.version,
                        "protocolVersion": server.protocol_version,
                        "capabilities": {
                            "tools": server.capabilities.tools,
                            "resources": server.capabilities.resources,
                            "prompts": server.capabilities.prompts,
                            "sampling": server.capabilities.sampling,
                            "roots": server.capabilities.roots,
                            "experimental": server.capabilities.experimental
                        },
                        "url": server.url,
                        "command": server.command,
                        "args": server.args,
                        "env": server.env,
                        "metadata": server.metadata
                    }
                    for server in self.servers.values()
                ]
            }
            
            with open(self._cache_file, 'w') as f:
                json.dump(cache, f, indent=2)
                
        except Exception as e:
            logger.debug(f"Failed to save cache: {e}")
    
    def get_server(self, name: str) -> Optional[MCPServer]:
        """Get server by name
        
        Args:
            name: Server name
            
        Returns:
            MCPServer instance or None
        """
        # Try exact match
        for server in self.servers.values():
            if server.name == name:
                return server
        
        # Try ID match
        server_id = f"{name}_1_0_0"
        return self.servers.get(server_id)
    
    def list_capabilities(self) -> Dict[str, List[str]]:
        """List all servers grouped by capability
        
        Returns:
            Dictionary mapping capabilities to server names
        """
        capabilities = {
            "tools": [],
            "resources": [],
            "prompts": [],
            "sampling": [],
            "roots": []
        }
        
        for server in self.servers.values():
            if server.capabilities.tools:
                capabilities["tools"].append(server.name)
            if server.capabilities.resources:
                capabilities["resources"].append(server.name)
            if server.capabilities.prompts:
                capabilities["prompts"].append(server.name)
            if server.capabilities.sampling:
                capabilities["sampling"].append(server.name)
            if server.capabilities.roots:
                capabilities["roots"].append(server.name)
        
        return capabilities
    
    def register_server(self, server: MCPServer) -> None:
        """Manually register an MCP server
        
        Args:
            server: MCPServer instance
        """
        self.servers[server.id] = server
        logger.info(f"Registered server: {server.name}")
    
    def unregister_server(self, name: str) -> bool:
        """Unregister an MCP server
        
        Args:
            name: Server name
            
        Returns:
            True if server was removed
        """
        server = self.get_server(name)
        if server:
            del self.servers[server.id]
            logger.info(f"Unregistered server: {name}")
            return True
        return False