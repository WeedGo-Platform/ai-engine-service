"""
MCP (Model Context Protocol) Integration Module
Provides client and server implementations for MCP protocol
"""

from .mcp_client import MCPClient, MCPClientInterface
from .mcp_types import (
    MCPRequest,
    MCPResponse,
    MCPTool,
    MCPServer,
    MCPResource,
    MCPPrompt,
    MCPError,
    MCPCapabilities
)
from .mcp_discovery import MCPDiscovery
from .mcp_transport import MCPTransport, TransportType

__all__ = [
    'MCPClient',
    'MCPClientInterface',
    'MCPRequest',
    'MCPResponse',
    'MCPTool',
    'MCPServer',
    'MCPResource',
    'MCPPrompt',
    'MCPError',
    'MCPCapabilities',
    'MCPDiscovery',
    'MCPTransport',
    'TransportType'
]