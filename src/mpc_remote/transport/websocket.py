"""WebSocket transport implementation."""

import json
import ssl
from typing import Any, Optional

import websockets

from ..core.jsonrpc import JSONRPCMessage
from .base import BaseTransport


class WebSocketTransport(BaseTransport):
    """
    WebSocket transport implementation supporting ws:// and wss:// URLs.
    """
    
    def __init__(
        self,
        url: str,
        ssl: Optional[ssl.SSLContext] = None,
        **kwargs: Any
    ) -> None:
        super().__init__()
        self.url = url
        self.ssl = ssl
        self.ws = None
        self.ws_options = kwargs
    
    async def initialize(self) -> None:
        """Initialize WebSocket connection."""
        if self.is_connected:
            return
            
        # Connect with SSL if needed
        self.ws = await websockets.connect(
            self.url,
            ssl=self.ssl,
            **self.ws_options
        )
        self._connected = True
    
    async def read_message(self) -> JSONRPCMessage:
        """Read JSON-RPC message from WebSocket."""
        if not self.is_connected:
            raise RuntimeError("Transport not connected")
            
        try:
            raw_message = await self.ws.recv()
            message_dict = json.loads(raw_message)
            return JSONRPCMessage.parse_obj(message_dict)
        except Exception as e:
            raise ValueError(f"Invalid message format: {e}") from e
    
    async def write_message(self, message: JSONRPCMessage) -> None:
        """Write JSON-RPC message to WebSocket."""
        if not self.is_connected:
            raise RuntimeError("Transport not connected")
            
        content = json.dumps(message.dict(exclude_none=True))
        await self.ws.send(content)
    
    async def close(self) -> None:
        """Close WebSocket connection."""
        if self.ws:
            await self.ws.close()
            self.ws = None
        self._connected = False