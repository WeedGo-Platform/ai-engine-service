"""
MCP Transport Layer
Handles different transport protocols for MCP communication
"""
import asyncio
import aiohttp
import json
import logging
import subprocess
import os
from typing import Dict, Any, Optional, Callable, List
from abc import ABC, abstractmethod
import websockets
from .mcp_types import (
    MCPRequest, MCPResponse, MCPError, MCPErrorCode,
    TransportType, MCPNotification
)

logger = logging.getLogger(__name__)

class MCPTransport(ABC):
    """Abstract base class for MCP transports"""
    
    @abstractmethod
    async def connect(self, **kwargs) -> bool:
        """Establish connection"""
        pass
    
    @abstractmethod
    async def disconnect(self) -> None:
        """Close connection"""
        pass
    
    @abstractmethod
    async def send_request(self, request: MCPRequest) -> MCPResponse:
        """Send request and wait for response"""
        pass
    
    @abstractmethod
    async def send_notification(self, notification: MCPNotification) -> None:
        """Send notification (no response expected)"""
        pass
    
    @abstractmethod
    def is_connected(self) -> bool:
        """Check if transport is connected"""
        pass

class HTTPTransport(MCPTransport):
    """HTTP/HTTPS transport for MCP"""
    
    def __init__(self, base_url: str, timeout: int = 30):
        """Initialize HTTP transport
        
        Args:
            base_url: Base URL for MCP server
            timeout: Request timeout in seconds
        """
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self.session: Optional[aiohttp.ClientSession] = None
        self.headers = {
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
    
    async def connect(self, **kwargs) -> bool:
        """Create HTTP session"""
        try:
            if self.session:
                await self.disconnect()
            
            # Add any auth headers
            if "auth_token" in kwargs:
                self.headers["Authorization"] = f"Bearer {kwargs['auth_token']}"
            
            self.session = aiohttp.ClientSession(
                headers=self.headers,
                timeout=aiohttp.ClientTimeout(total=self.timeout)
            )
            
            # Test connection with initialize request
            test_request = MCPRequest(method="initialize", params={"protocolVersion": "1.0"})
            response = await self.send_request(test_request)
            
            return response.is_success()
            
        except Exception as e:
            logger.error(f"HTTP connection failed: {e}")
            return False
    
    async def disconnect(self) -> None:
        """Close HTTP session"""
        if self.session:
            await self.session.close()
            self.session = None
    
    async def send_request(self, request: MCPRequest) -> MCPResponse:
        """Send HTTP request"""
        if not self.session:
            raise RuntimeError("Not connected")
        
        try:
            url = f"{self.base_url}/mcp"
            async with self.session.post(url, json=request.to_dict()) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    if "error" in data:
                        return MCPResponse(
                            id=data.get("id"),
                            error=MCPError(**data["error"])
                        )
                    return MCPResponse(
                        id=data.get("id"),
                        result=data.get("result")
                    )
                else:
                    return MCPResponse(
                        id=request.id,
                        error=MCPError(
                            code=MCPErrorCode.SERVER_ERROR.value,
                            message=f"HTTP {resp.status}: {await resp.text()}"
                        )
                    )
        except asyncio.TimeoutError:
            return MCPResponse(
                id=request.id,
                error=MCPError(
                    code=MCPErrorCode.TIMEOUT.value,
                    message="Request timeout"
                )
            )
        except Exception as e:
            return MCPResponse(
                id=request.id,
                error=MCPError.from_exception(e)
            )
    
    async def send_notification(self, notification: MCPNotification) -> None:
        """Send notification via HTTP POST"""
        if not self.session:
            raise RuntimeError("Not connected")
        
        try:
            url = f"{self.base_url}/mcp"
            async with self.session.post(url, json=notification.to_dict()) as resp:
                # Notifications don't expect responses
                pass
        except Exception as e:
            logger.error(f"Failed to send notification: {e}")
    
    def is_connected(self) -> bool:
        """Check if session is active"""
        return self.session is not None and not self.session.closed

class WebSocketTransport(MCPTransport):
    """WebSocket transport for MCP"""
    
    def __init__(self, url: str, reconnect: bool = True):
        """Initialize WebSocket transport
        
        Args:
            url: WebSocket URL
            reconnect: Auto-reconnect on disconnect
        """
        self.url = url
        self.reconnect = reconnect
        self.websocket: Optional[websockets.WebSocketClientProtocol] = None
        self.pending_requests: Dict[str, asyncio.Future] = {}
        self.receive_task: Optional[asyncio.Task] = None
        self.notification_handler: Optional[Callable] = None
    
    async def connect(self, **kwargs) -> bool:
        """Connect to WebSocket server"""
        try:
            self.websocket = await websockets.connect(self.url)
            
            # Start receive loop
            self.receive_task = asyncio.create_task(self._receive_loop())
            
            # Send initialize
            init_request = MCPRequest(method="initialize", params={"protocolVersion": "1.0"})
            response = await self.send_request(init_request)
            
            return response.is_success()
            
        except Exception as e:
            logger.error(f"WebSocket connection failed: {e}")
            return False
    
    async def disconnect(self) -> None:
        """Close WebSocket connection"""
        if self.receive_task:
            self.receive_task.cancel()
            try:
                await self.receive_task
            except asyncio.CancelledError:
                pass
        
        if self.websocket:
            await self.websocket.close()
            self.websocket = None
        
        # Cancel pending requests
        for future in self.pending_requests.values():
            if not future.done():
                future.cancel()
        self.pending_requests.clear()
    
    async def _receive_loop(self) -> None:
        """Receive messages from WebSocket"""
        while self.websocket and not self.websocket.closed:
            try:
                message = await self.websocket.recv()
                data = json.loads(message)
                
                # Check if it's a response to a request
                if "id" in data and data["id"] in self.pending_requests:
                    future = self.pending_requests.pop(data["id"])
                    if "error" in data:
                        response = MCPResponse(
                            id=data["id"],
                            error=MCPError(**data["error"])
                        )
                    else:
                        response = MCPResponse(
                            id=data["id"],
                            result=data.get("result")
                        )
                    future.set_result(response)
                
                # Check if it's a notification
                elif "method" in data and "id" not in data:
                    if self.notification_handler:
                        notification = MCPNotification(
                            method=data["method"],
                            params=data.get("params")
                        )
                        await self.notification_handler(notification)
                
            except websockets.ConnectionClosed:
                logger.warning("WebSocket connection closed")
                if self.reconnect:
                    await self._handle_reconnect()
                break
            except Exception as e:
                logger.error(f"Error in receive loop: {e}")
    
    async def _handle_reconnect(self) -> None:
        """Handle reconnection logic"""
        max_retries = 5
        retry_delay = 1
        
        for attempt in range(max_retries):
            logger.info(f"Reconnection attempt {attempt + 1}/{max_retries}")
            await asyncio.sleep(retry_delay)
            
            if await self.connect():
                logger.info("Reconnected successfully")
                return
            
            retry_delay = min(retry_delay * 2, 30)
        
        logger.error("Failed to reconnect after max retries")
    
    async def send_request(self, request: MCPRequest) -> MCPResponse:
        """Send request via WebSocket"""
        if not self.websocket or self.websocket.closed:
            return MCPResponse(
                id=request.id,
                error=MCPError(
                    code=MCPErrorCode.CONNECTION_ERROR.value,
                    message="WebSocket not connected"
                )
            )
        
        try:
            # Create future for response
            future = asyncio.Future()
            self.pending_requests[request.id] = future
            
            # Send request
            await self.websocket.send(json.dumps(request.to_dict()))
            
            # Wait for response
            response = await asyncio.wait_for(future, timeout=30)
            return response
            
        except asyncio.TimeoutError:
            self.pending_requests.pop(request.id, None)
            return MCPResponse(
                id=request.id,
                error=MCPError(
                    code=MCPErrorCode.TIMEOUT.value,
                    message="Request timeout"
                )
            )
        except Exception as e:
            self.pending_requests.pop(request.id, None)
            return MCPResponse(
                id=request.id,
                error=MCPError.from_exception(e)
            )
    
    async def send_notification(self, notification: MCPNotification) -> None:
        """Send notification via WebSocket"""
        if self.websocket and not self.websocket.closed:
            try:
                await self.websocket.send(json.dumps(notification.to_dict()))
            except Exception as e:
                logger.error(f"Failed to send notification: {e}")
    
    def is_connected(self) -> bool:
        """Check if WebSocket is connected"""
        return self.websocket is not None and not self.websocket.closed
    
    def set_notification_handler(self, handler: Callable) -> None:
        """Set handler for incoming notifications"""
        self.notification_handler = handler

class StdioTransport(MCPTransport):
    """Standard I/O transport for local MCP servers"""
    
    def __init__(self, command: str, args: List[str] = None, env: Dict[str, str] = None):
        """Initialize stdio transport
        
        Args:
            command: Command to start MCP server
            args: Command arguments
            env: Environment variables
        """
        self.command = command
        self.args = args or []
        self.env = env or {}
        self.process: Optional[asyncio.subprocess.Process] = None
        self.pending_requests: Dict[str, asyncio.Future] = {}
        self.receive_task: Optional[asyncio.Task] = None
    
    async def connect(self, **kwargs) -> bool:
        """Start MCP server process"""
        try:
            # Merge environment variables
            env = {**os.environ, **self.env}
            
            # Start process
            self.process = await asyncio.create_subprocess_exec(
                self.command,
                *self.args,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env=env
            )
            
            # Start receive loop
            self.receive_task = asyncio.create_task(self._receive_loop())
            
            # Initialize connection
            init_request = MCPRequest(method="initialize", params={"protocolVersion": "1.0"})
            response = await self.send_request(init_request)
            
            return response.is_success()
            
        except Exception as e:
            logger.error(f"Failed to start MCP server: {e}")
            return False
    
    async def disconnect(self) -> None:
        """Stop MCP server process"""
        if self.receive_task:
            self.receive_task.cancel()
            try:
                await self.receive_task
            except asyncio.CancelledError:
                pass
        
        if self.process:
            # Send shutdown notification
            try:
                await self.send_notification(MCPNotification(method="shutdown"))
                await asyncio.sleep(0.5)
            except:
                pass
            
            # Terminate process
            self.process.terminate()
            try:
                await asyncio.wait_for(self.process.wait(), timeout=5)
            except asyncio.TimeoutError:
                self.process.kill()
                await self.process.wait()
            
            self.process = None
        
        # Cancel pending requests
        for future in self.pending_requests.values():
            if not future.done():
                future.cancel()
        self.pending_requests.clear()
    
    async def _receive_loop(self) -> None:
        """Read responses from process stdout"""
        while self.process and self.process.returncode is None:
            try:
                line = await self.process.stdout.readline()
                if not line:
                    break
                
                data = json.loads(line.decode())
                
                # Handle response
                if "id" in data and data["id"] in self.pending_requests:
                    future = self.pending_requests.pop(data["id"])
                    if "error" in data:
                        response = MCPResponse(
                            id=data["id"],
                            error=MCPError(**data["error"])
                        )
                    else:
                        response = MCPResponse(
                            id=data["id"],
                            result=data.get("result")
                        )
                    future.set_result(response)
                
            except Exception as e:
                logger.error(f"Error in stdio receive loop: {e}")
    
    async def send_request(self, request: MCPRequest) -> MCPResponse:
        """Send request via stdin"""
        if not self.process or self.process.returncode is not None:
            return MCPResponse(
                id=request.id,
                error=MCPError(
                    code=MCPErrorCode.CONNECTION_ERROR.value,
                    message="Process not running"
                )
            )
        
        try:
            # Create future for response
            future = asyncio.Future()
            self.pending_requests[request.id] = future
            
            # Send request
            message = json.dumps(request.to_dict()) + "\n"
            self.process.stdin.write(message.encode())
            await self.process.stdin.drain()
            
            # Wait for response
            response = await asyncio.wait_for(future, timeout=30)
            return response
            
        except asyncio.TimeoutError:
            self.pending_requests.pop(request.id, None)
            return MCPResponse(
                id=request.id,
                error=MCPError(
                    code=MCPErrorCode.TIMEOUT.value,
                    message="Request timeout"
                )
            )
        except Exception as e:
            self.pending_requests.pop(request.id, None)
            return MCPResponse(
                id=request.id,
                error=MCPError.from_exception(e)
            )
    
    async def send_notification(self, notification: MCPNotification) -> None:
        """Send notification via stdin"""
        if self.process and self.process.returncode is None:
            try:
                message = json.dumps(notification.to_dict()) + "\n"
                self.process.stdin.write(message.encode())
                await self.process.stdin.drain()
            except Exception as e:
                logger.error(f"Failed to send notification: {e}")
    
    def is_connected(self) -> bool:
        """Check if process is running"""
        return self.process is not None and self.process.returncode is None

def create_transport(transport_type: TransportType, **kwargs) -> MCPTransport:
    """Factory function to create transport instance
    
    Args:
        transport_type: Type of transport
        **kwargs: Transport-specific configuration
        
    Returns:
        MCPTransport instance
    """
    if transport_type == TransportType.HTTP:
        return HTTPTransport(kwargs.get("url", "http://localhost:3000"))
    elif transport_type == TransportType.WEBSOCKET:
        return WebSocketTransport(kwargs.get("url", "ws://localhost:3000"))
    elif transport_type == TransportType.STDIO:
        return StdioTransport(
            command=kwargs.get("command"),
            args=kwargs.get("args", []),
            env=kwargs.get("env", {})
        )
    else:
        raise ValueError(f"Unsupported transport type: {transport_type}")