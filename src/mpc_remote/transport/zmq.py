"""ZeroMQ transport implementation with security features."""

import json
from typing import Any, Optional

import zmq
import zmq.asyncio
from zmq.utils.z85 import decode

from ..core.jsonrpc import JSONRPCMessage
from .base import BaseTransport


class ZMQSecurity:
    """ZMQ security configuration."""

    def __init__(
        self,
        public_key: Optional[bytes] = None,
        secret_key: Optional[bytes] = None,
        server_public_key: Optional[bytes] = None,
    ) -> None:
        self.public_key = public_key
        self.secret_key = secret_key
        self.server_public_key = server_public_key

    @classmethod
    def generate_certificates(cls) -> tuple[bytes, bytes]:
        """Generate new CURVE key pair."""
        public, secret = zmq.curve_keypair()
        return public, secret

    @classmethod
    def from_keys(cls, public_key: str, secret_key: str, server_public_key: Optional[str] = None) -> "ZMQSecurity":
        """Create from Z85-encoded keys."""
        return cls(
            public_key=decode(public_key),
            secret_key=decode(secret_key),
            server_public_key=decode(server_public_key) if server_public_key else None,
        )

    @classmethod
    def generate(cls) -> "ZMQSecurity":
        """Generate new security configuration."""
        public, secret = cls.generate_certificates()
        return cls(public_key=public, secret_key=secret)


class ZMQTransport(BaseTransport):
    """
    ZeroMQ transport implementation supporting tcp://, ipc://, and inproc:// URLs.
    Includes CURVE security support.
    """

    def __init__(
        self,
        url: str,
        context: Optional[zmq.asyncio.Context] = None,
        socket_type: int = zmq.REQ,
        security: Optional[ZMQSecurity] = None,
        encoding: str = "utf-8",
        **kwargs: Any,
    ) -> None:
        super().__init__()
        self.url = url
        self.context = context or zmq.asyncio.Context.instance()
        self.socket_type = socket_type
        self.socket = None
        self.security = security
        self.encoding = encoding
        self.socket_options = kwargs
        self._authenticator = None

    async def initialize(self) -> None:
        """Initialize ZMQ connection with optional security."""
        if self.is_connected:
            return

        # Create and configure socket
        self.socket = self.context.socket(self.socket_type)

        # Set up CURVE security if configured
        if self.security:
            await self._setup_security()

        # Apply socket options
        for option, value in self.socket_options.items():
            if isinstance(option, str):
                option = getattr(zmq, option)
            self.socket.set(option, value)

        # Connect
        self.socket.connect(self.url)
        self._connected = True

    async def _setup_security(self) -> None:
        """Configure CURVE security for the socket."""
        if not self.security.public_key or not self.security.secret_key:
            raise ValueError("Both public and secret keys required for CURVE security")

        self.socket.curve_publickey = self.security.public_key
        self.socket.curve_secretkey = self.security.secret_key

        if self.security.server_public_key:
            self.socket.curve_serverkey = self.security.server_public_key

        # Enable CURVE security
        self.socket.mechanism = zmq.CURVE

    async def read_message(self) -> JSONRPCMessage:
        """Read JSON-RPC message from ZMQ socket."""
        if not self.is_connected:
            raise RuntimeError("Transport not connected")

        frames = await self.socket.recv_multipart()

        # Handle multi-frame messages
        if len(frames) > 1:
            # Last frame is the message, others might be routing info
            message_data = frames[-1]
        else:
            message_data = frames[0]

        # Parse JSON-RPC message
        try:
            message_dict = json.loads(message_data.decode(self.encoding))
            return JSONRPCMessage.parse_obj(message_dict)
        except Exception as e:
            raise ValueError(f"Invalid message format: {e}") from e

    async def write_message(self, message: JSONRPCMessage) -> None:
        """Write JSON-RPC message to ZMQ socket."""
        if not self.is_connected:
            raise RuntimeError("Transport not connected")

        # Serialize message
        content = json.dumps(message.dict(exclude_none=True))
        content_bytes = content.encode(self.encoding)

        # Send as single frame
        await self.socket.send(content_bytes)

    async def close(self) -> None:
        """Close ZMQ connection and clean up security."""
        if self.socket:
            self.socket.close()
            self.socket = None
        if self._authenticator:
            self._authenticator.stop()
            self._authenticator = None
        self._connected = False

    @classmethod
    def create_secure_client(
        cls, url: str, server_public_key: str, client_keys: Optional[ZMQSecurity] = None, **kwargs: Any
    ) -> "ZMQTransport":
        """
        Create a secure ZMQ transport with CURVE authentication.

        Args:
            url: Server URL (tcp://, ipc://, or inproc://)
            server_public_key: Z85-encoded server public key
            client_keys: Optional client keys, generated if not provided
            **kwargs: Additional socket options

        Returns:
            Configured secure transport
        """
        # Generate client keys if not provided
        if not client_keys:
            client_keys = ZMQSecurity.generate()

        # Add server's public key
        client_keys.server_public_key = decode(server_public_key)

        return cls(url, security=client_keys, **kwargs)
