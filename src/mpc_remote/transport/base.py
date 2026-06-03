"""Base transport interface for MCP protocol."""

from abc import ABC, abstractmethod
from typing import Protocol

from ..core.jsonrpc import JSONRPCMessage


class MCPTransport(Protocol):
    """Protocol interface for MCP transports."""
    
    @abstractmethod
    async def initialize(self) -> None:
        """Initialize the transport connection."""
        ...
    
    @abstractmethod
    async def read_message(self) -> JSONRPCMessage:
        """Read next protocol message."""
        ...
    
    @abstractmethod
    async def write_message(self, message: JSONRPCMessage) -> None:
        """Write protocol message."""
        ...
    
    @abstractmethod
    async def close(self) -> None:
        """Close the transport connection."""
        ...
    
    @property
    @abstractmethod
    def is_connected(self) -> bool:
        """Check if transport is connected."""
        ...

class BaseTransport(ABC):
    """Base implementation of MCPTransport protocol."""
    
    def __init__(self) -> None:
        self._connected = False
    
    @property
    def is_connected(self) -> bool:
        return self._connected
    
    async def __aenter__(self):
        await self.initialize()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()