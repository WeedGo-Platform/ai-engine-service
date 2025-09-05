"""
MCP Type Definitions
Defines all data types used in MCP protocol
"""
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional, Union
from enum import Enum
import uuid
from datetime import datetime

class TransportType(Enum):
    """MCP transport protocol types"""
    HTTP = "http"
    WEBSOCKET = "websocket"
    STDIO = "stdio"
    GRPC = "grpc"

class MCPErrorCode(Enum):
    """MCP error codes"""
    PARSE_ERROR = -32700
    INVALID_REQUEST = -32600
    METHOD_NOT_FOUND = -32601
    INVALID_PARAMS = -32602
    INTERNAL_ERROR = -32603
    SERVER_ERROR = -32000
    TIMEOUT = -32001
    CONNECTION_ERROR = -32002
    UNAUTHORIZED = -32003

@dataclass
class MCPCapabilities:
    """Server capabilities"""
    tools: bool = True
    resources: bool = True
    prompts: bool = True
    sampling: bool = False
    roots: bool = False
    experimental: Dict[str, Any] = field(default_factory=dict)

@dataclass
class MCPTool:
    """MCP tool definition"""
    name: str
    description: str
    input_schema: Dict[str, Any]
    output_schema: Optional[Dict[str, Any]] = None
    tags: List[str] = field(default_factory=list)
    examples: List[Dict[str, Any]] = field(default_factory=list)
    
    def to_openai_function(self) -> Dict[str, Any]:
        """Convert to OpenAI function format"""
        return {
            "name": self.name,
            "description": self.description,
            "parameters": self.input_schema
        }
    
    def to_anthropic_tool(self) -> Dict[str, Any]:
        """Convert to Anthropic tool format"""
        return {
            "name": self.name,
            "description": self.description,
            "input_schema": self.input_schema
        }

@dataclass
class MCPResource:
    """MCP resource definition"""
    uri: str
    name: str
    description: Optional[str] = None
    mime_type: str = "text/plain"
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class MCPPrompt:
    """MCP prompt template"""
    name: str
    description: str
    arguments: List[Dict[str, Any]]
    template: str
    tags: List[str] = field(default_factory=list)

@dataclass
class MCPServer:
    """MCP server information"""
    name: str
    version: str
    protocol_version: str = "1.0"
    capabilities: MCPCapabilities = field(default_factory=MCPCapabilities)
    transport: TransportType = TransportType.HTTP
    url: Optional[str] = None
    command: Optional[str] = None
    args: List[str] = field(default_factory=list)
    env: Dict[str, str] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def id(self) -> str:
        """Generate unique server ID"""
        return f"{self.name}_{self.version}".replace(".", "_")

@dataclass
class MCPRequest:
    """MCP request message"""
    jsonrpc: str = "2.0"
    method: str = ""
    params: Optional[Dict[str, Any]] = None
    id: Optional[Union[str, int]] = None
    
    def __post_init__(self):
        if self.id is None:
            self.id = str(uuid.uuid4())
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        result = {
            "jsonrpc": self.jsonrpc,
            "method": self.method,
            "id": self.id
        }
        if self.params is not None:
            result["params"] = self.params
        return result

@dataclass
class MCPResponse:
    """MCP response message"""
    jsonrpc: str = "2.0"
    result: Optional[Any] = None
    error: Optional['MCPError'] = None
    id: Optional[Union[str, int]] = None
    
    def is_success(self) -> bool:
        """Check if response is successful"""
        return self.error is None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        result = {
            "jsonrpc": self.jsonrpc,
            "id": self.id
        }
        if self.error:
            result["error"] = self.error.to_dict()
        else:
            result["result"] = self.result
        return result

@dataclass
class MCPError:
    """MCP error response"""
    code: int
    message: str
    data: Optional[Any] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        result = {
            "code": self.code,
            "message": self.message
        }
        if self.data is not None:
            result["data"] = self.data
        return result
    
    @classmethod
    def from_exception(cls, e: Exception, code: MCPErrorCode = MCPErrorCode.INTERNAL_ERROR) -> 'MCPError':
        """Create error from exception"""
        return cls(
            code=code.value,
            message=str(e),
            data={"type": type(e).__name__}
        )

@dataclass
class MCPNotification:
    """MCP notification (no response expected)"""
    jsonrpc: str = "2.0"
    method: str = ""
    params: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        result = {
            "jsonrpc": self.jsonrpc,
            "method": self.method
        }
        if self.params is not None:
            result["params"] = self.params
        return result

@dataclass
class MCPSession:
    """MCP client session"""
    session_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    server: Optional[MCPServer] = None
    connected: bool = False
    created_at: datetime = field(default_factory=datetime.now)
    last_activity: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)