"""ZeroMQ transport implementation for Model Context Protocol"""

import asyncio
import json
from typing import Any, Dict, Optional

import zmq
import zmq.asyncio

from ..core.errors import MCPError


class ZMQTransportError(MCPError):
    """Transport-specific errors"""
    pass

class ZMQTransport:
    """ZeroMQ transport for Model Context Protocol communications"""
    
    def __init__(
        self, 
        endpoint: str,
        connection_type: str = 'connect',
        context: Optional[zmq.Context] = None,
        timeout: float = 5.0
    ):
        """Initialize ZMQ transport"""
        self.context = context or zmq.asyncio.Context()
        self.socket = self.context.socket(zmq.REQ if connection_type == 'connect' else zmq.REP)
        
        # Configure socket
        self.socket.setsockopt(zmq.LINGER, 1000)  # 1 second linger
        self.socket.setsockopt(zmq.RCVTIMEO, int(timeout * 1000))
        self.socket.setsockopt(zmq.SNDTIMEO, int(timeout * 1000))
        
        # Special handling for inproc transport
        if endpoint.startswith("inproc://"):
            # Increase HWM for inproc to prevent message loss
            self.socket.setsockopt(zmq.SNDHWM, 10000)
            self.socket.setsockopt(zmq.RCVHWM, 10000)
            # Set immediate mode to prevent buffering
            self.socket.setsockopt(zmq.IMMEDIATE, 1)
        else:
            self.socket.setsockopt(zmq.SNDHWM, 1000)
            self.socket.setsockopt(zmq.RCVHWM, 1000)
        
        if connection_type == 'connect':
            self.socket.connect(endpoint)
        elif connection_type == 'bind':
            self.socket.bind(endpoint)
        else:
            raise ValueError("Connection type must be 'connect' or 'bind'")
        
        self.endpoint = endpoint
        self._closed = False
        self._timeout = timeout
    
    async def recv_json(self) -> Dict[str, Any]:
        """Receive and parse JSON data"""
        try:
            data = await self.socket.recv()
            return json.loads(data.decode('utf-8'))
        except zmq.error.Again:
            raise ZMQTransportError("Receive operation timed out")
    
    async def send_json(self, data: Dict[str, Any]) -> None:
        """Encode and send JSON data"""
        try:
            message = json.dumps(data).encode('utf-8')
            await self.socket.send(message)
        except zmq.error.Again:
            raise ZMQTransportError("Send operation timed out")
    
    async def send_request(
        self, 
        request: Dict[str, Any],
        timeout: Optional[float] = None
    ) -> Dict[str, Any]:
        """Send a JSON-RPC request via ZeroMQ"""
        if self._closed:
            raise ZMQTransportError("Transport is closed")
        
        timeout = timeout or self._timeout
        
        try:
            async with asyncio.timeout(timeout):
                await self.send_json(request)
                response = await self.recv_json()
            
            return response
            
        except asyncio.TimeoutError:
            raise ZMQTransportError(
                f"Request timed out after {timeout} seconds",
                details={"endpoint": self.endpoint}
            )
        except zmq.ZMQError as e:
            raise ZMQTransportError(
                f"ZMQ error: {e!s}",
                details={"errno": e.errno}
            )
        except json.JSONDecodeError as e:
            raise ZMQTransportError(
                "Invalid JSON response",
                details={"error": str(e)}
            )
    
    async def handle_request(self, handler) -> None:
        """Handle incoming requests (server mode)"""
        if self._closed:
            raise ZMQTransportError("Transport is closed")
            
        while True:
            try:
                # Receive and process request
                request = await self.recv_json()
                response = await handler(request)
                await self.send_json(response)
                
            except Exception as e:
                # Send error response
                error_response = {
                    "jsonrpc": "2.0",
                    "error": {
                        "code": -32000,
                        "message": str(e),
                        "data": {"type": type(e).__name__}
                    },
                    "id": request.get("id") if isinstance(request, dict) else None
                }
                await self.send_json(error_response)
    
    def close(self) -> None:
        """Close the transport"""
        if not self._closed:
            if hasattr(self, 'socket'):
                self.socket.close(linger=100)  # 100ms linger
            self._closed = True
    
    def __del__(self):
        """Ensure resources are cleaned up"""
        self.close()