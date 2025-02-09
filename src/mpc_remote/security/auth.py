"""Authentication layer for Model Context Protocol"""

from typing import Any, Dict, Optional, Protocol, runtime_checkable

from ..core.errors import MCPError, MCPErrorCode
from ..core.protocol import ProtocolHandler


@runtime_checkable
class AuthProvider(Protocol):
    """Protocol for authentication providers"""
    
    async def verify_token(self, token: str) -> bool:
        """Verify if a token is valid"""
        ...
    
    async def check_tool_permission(self, token: str, tool_name: str) -> bool:
        """Check if a token has permission to use a tool"""
        ...

class AuthenticatedProtocolHandler(ProtocolHandler):
    """Protocol handler with authentication support"""
    
    def __init__(self, auth_provider: AuthProvider, **kwargs):
        """Initialize authenticated protocol handler"""
        if not isinstance(auth_provider, AuthProvider):
            raise TypeError(
                "auth_provider must implement AuthProvider protocol"
            )
        super().__init__(**kwargs)
        self.auth_provider = auth_provider
    
    async def execute_tool(self, tool_name: str, params: Dict[str, Any], auth_token: Optional[str] = None) -> Any:
        """Execute a tool with authentication"""
        if not auth_token:
            raise MCPError(
                "Authentication required",
                code=MCPErrorCode.UNAUTHORIZED
            )
        
        # Verify token
        if not await self.auth_provider.verify_token(auth_token):
            raise MCPError(
                "Authentication failed",
                code=MCPErrorCode.UNAUTHORIZED
            )
        
        # Check tool permissions
        if not await self.auth_provider.check_tool_permission(auth_token, tool_name):
            raise MCPError(
                "Permission denied",
                code=MCPErrorCode.RESOURCE_FORBIDDEN
            )
        
        return await super().execute_tool(tool_name, params)