"""MCP client with automatic transport selection."""

from __future__ import annotations

import ssl
from typing import Any, ClassVar
from urllib.parse import urlparse

from .protocol.session import MCPSession
from .transport.base import MCPTransport
from .transport.stdio import StdIOTransport
from .transport.websocket import WebSocketTransport
from .transport.zmq import ZMQSecurity, ZMQTransport


class MCPClient:
    """
    Model Context Protocol client with automatic transport selection.
    
    Usage:
        # Basic usage
        async with MCPClient.connect("tcp://localhost:5555") as session:
            await session.initialize()
            result = await session.call_tool("my_tool", {"arg": "value"})
            
        # Secure ZMQ connection
        async with MCPClient.connect(
            "tcp://localhost:5555",
            server_key="ZMQ-server-public-key",
            client_keys=generated_keys
        ) as session:
            await session.initialize()
    """
    
    TRANSPORT_SCHEMES: ClassVar[dict[str, str]] = {
        'tcp': 'zmq',        # ZMQ TCP transport
        'ipc': 'zmq',        # ZMQ IPC transport
        'inproc': 'zmq',     # ZMQ in-process transport
        'ws': 'websocket',   # WebSocket
        'wss': 'websocket',  # WebSocket Secure
        'stdio': 'stdio'     # Standard IO (default)
    }
    
    @classmethod
    async def connect(
        cls,
        url: str | None = None,
        ssl_context: ssl.SSLContext | None = None,
        server_key: str | None = None,
        client_keys: ZMQSecurity | None = None,
        **kwargs: Any
    ) -> MCPSession:
        """
        Create an MCP session with appropriate transport based on URL.
        
        Args:
            url: Connection URL. If None, uses stdio transport.
            ssl_context: Optional SSL context for secure websocket connections.
            server_key: ZMQ CURVE server public key (for secure ZMQ connections).
            client_keys: Optional ZMQ CURVE client keys (generated if needed).
            **kwargs: Additional transport-specific options.
            
        Returns:
            MCPSession configured with appropriate transport.
            
        Raises:
            ValueError: If URL scheme is not supported.
        """
        transport = await cls._create_transport(
            url,
            ssl_context,
            server_key,
            client_keys,
            **kwargs
        )
        return MCPSession(transport)
    
    @classmethod
    async def _create_transport(
        cls,
        url: str | None,
        ssl_context: ssl.SSLContext | None = None,
        server_key: str | None = None,
        client_keys: ZMQSecurity | None = None,
        **kwargs: Any
    ) -> MCPTransport:
        """Create appropriate transport based on URL scheme."""
        if not url:
            return StdIOTransport()
            
        parsed = urlparse(url)
        transport_type = cls.TRANSPORT_SCHEMES.get(parsed.scheme)
        
        if not transport_type:
            raise ValueError(
                f"Unsupported URL scheme: {parsed.scheme}. "
                f"Supported schemes: {', '.join(cls.TRANSPORT_SCHEMES.keys())}"
            )
        
        if transport_type == 'zmq':
            # Handle secure ZMQ connections
            if server_key:
                return ZMQTransport.create_secure_client(
                    url,
                    server_key,
                    client_keys,
                    **kwargs
                )
            return ZMQTransport(url, **kwargs)
            
        elif transport_type == 'websocket':
            return WebSocketTransport(
                url,
                ssl=ssl_context if parsed.scheme == 'wss' else None,
                **kwargs
            )
        else:
            return StdIOTransport()
    
    @classmethod
    def generate_client_keys(cls) -> ZMQSecurity:
        """Generate new ZMQ CURVE key pair for secure connections."""
        return ZMQSecurity.generate()