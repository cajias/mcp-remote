"""Standard IO transport implementation matching canonical SDK."""

import json
import sys

from ..core.jsonrpc import JSONRPCMessage
from .base import BaseTransport


class StdIOTransport(BaseTransport):
    """
    Standard IO transport implementation.
    Matches behavior of canonical SDK for compatibility.
    """
    
    def __init__(self) -> None:
        super().__init__()
        self._initialized = False
    
    async def initialize(self) -> None:
        """Initialize stdio transport."""
        if self._initialized:
            return
            
        # Configure stdin/stdout for binary mode if needed
        if hasattr(sys.stdin, 'buffer'):
            sys.stdin = sys.stdin.buffer
        if hasattr(sys.stdout, 'buffer'):
            sys.stdout = sys.stdout.buffer
            
        self._initialized = True
        self._connected = True
    
    async def read_message(self) -> JSONRPCMessage:
        """Read JSON-RPC message from stdin."""
        if not self._initialized:
            raise RuntimeError("Transport not initialized")
            
        # Read content length
        header = await self._read_line()
        if not header.startswith(b"Content-Length: "):
            raise ValueError("Invalid header format")
            
        content_length = int(header.split(b": ")[1])
        
        # Skip empty line
        empty_line = await self._read_line()
        if empty_line != b"":
            raise ValueError("Expected empty line after header")
        
        # Read message content
        content = await self._read_exactly(content_length)
        message_dict = json.loads(content.decode('utf-8'))
        
        return JSONRPCMessage.parse_obj(message_dict)
    
    async def write_message(self, message: JSONRPCMessage) -> None:
        """Write JSON-RPC message to stdout."""
        if not self._initialized:
            raise RuntimeError("Transport not initialized")
            
        # Serialize message
        content = json.dumps(message.dict(exclude_none=True))
        content_bytes = content.encode('utf-8')
        
        # Write header
        header = f"Content-Length: {len(content_bytes)}\r\n\r\n"
        sys.stdout.buffer.write(header.encode('ascii'))
        
        # Write content
        sys.stdout.buffer.write(content_bytes)
        sys.stdout.buffer.flush()
    
    async def close(self) -> None:
        """Close stdio transport."""
        self._connected = False
        self._initialized = False
    
    async def _read_line(self) -> bytes:
        """Read a line from stdin."""
        result = bytearray()
        while True:
            c = sys.stdin.buffer.read(1)
            if c == b'\r':
                c2 = sys.stdin.buffer.read(1)
                if c2 == b'\n':
                    break
                result.extend(c)
                result.extend(c2)
            elif c == b'\n':
                break
            else:
                result.extend(c)
        return bytes(result)
    
    async def _read_exactly(self, n: int) -> bytes:
        """Read exactly n bytes from stdin."""
        result = sys.stdin.buffer.read(n)
        if len(result) != n:
            raise EOFError(f"Expected {n} bytes, got {len(result)}")
        return result