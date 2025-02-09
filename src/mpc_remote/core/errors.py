"""Error handling for Model Context Protocol"""

from enum import IntEnum
from typing import Any, Dict, Optional


class MCPErrorCode(IntEnum):
    """
    Error codes for Model Context Protocol
    
    These codes follow JSON-RPC 2.0 conventions with additional
    MCP-specific codes in a separate range.
    """
    # Standard JSON-RPC error codes
    PARSE_ERROR = -32700
    INVALID_REQUEST = -32600
    METHOD_NOT_FOUND = -32601
    INVALID_PARAMS = -32602
    INTERNAL_ERROR = -32603
    
    # MCP-specific error codes
    UNAUTHORIZED = -40001
    CONSENT_REQUIRED = -40002
    RESOURCE_FORBIDDEN = -40003
    SAMPLING_NOT_ALLOWED = -40004
    PROTOCOL_VERSION_MISMATCH = -40005

class MCPError(Exception):
    """
    Base exception for Model Context Protocol errors
    
    This class provides structured error information including:
    - Error code
    - Human-readable message
    - Optional additional details
    """
    
    def __init__(
        self, 
        message: str, 
        code: MCPErrorCode = MCPErrorCode.INTERNAL_ERROR,
        details: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize an MCP error
        
        Args:
            message: Human-readable error message
            code: Error code from MCPErrorCode
            details: Additional error context
        """
        super().__init__(message)
        self.code = code
        self.details = details or {}
    
    def to_json_rpc_error(self) -> Dict[str, Any]:
        """
        Convert error to JSON-RPC 2.0 error format
        
        Returns:
            JSON-RPC error dictionary
        """
        error_response = {
            "code": self.code,
            "message": str(self),
        }
        
        if self.details:
            error_response["data"] = self.details
        
        return error_response

class ProtocolVersionError(MCPError):
    """
    Error raised when protocol version is incompatible
    
    This error provides specific information about version
    mismatches between client and server.
    """
    
    def __init__(self, current_version: str, requested_version: str):
        """
        Initialize version mismatch error
        
        Args:
            current_version: Current supported protocol version
            requested_version: Version requested by client
        """
        super().__init__(
            f"Protocol version mismatch. Current: {current_version}, Requested: {requested_version}",
            code=MCPErrorCode.PROTOCOL_VERSION_MISMATCH,
            details={
                "current_version": current_version,
                "requested_version": requested_version
            }
        )