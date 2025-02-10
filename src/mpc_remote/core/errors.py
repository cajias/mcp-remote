"""Error types for MPC Remote"""

from enum import IntEnum
from typing import Optional


class MCPErrorCode(IntEnum):
    """Error codes for MPC Remote"""
    PARSE_ERROR = -32700
    INVALID_REQUEST = -32600
    METHOD_NOT_FOUND = -32601
    INVALID_PARAMS = -32602
    INTERNAL_ERROR = -32603
    CONSENT_REQUIRED = 403
    VALIDATION_ERROR = 400
    CONNECTION_ERROR = 503
    AUTHENTICATION_ERROR = 401

class MCPError(Exception):
    """Base exception for MPC Remote errors"""
    def __init__(self, message: str, code: MCPErrorCode = None, details: Optional[dict] = None) -> None:
        super().__init__(message)
        self.code = code or MCPErrorCode.INTERNAL_ERROR
        self.details = details or {}

class ConsentError(MCPError):
    """Error raised when consent is required but not granted"""
    def __init__(self, resource_name: str) -> None:
        super().__init__(
            f"Consent required for '{resource_name}'",
            code=MCPErrorCode.CONSENT_REQUIRED
        )
        self.resource_name = resource_name

class ValidationError(MCPError):
    """Error raised when input validation fails"""
    def __init__(self, message: str, details: Optional[dict] = None) -> None:
        super().__init__(
            message,
            code=MCPErrorCode.VALIDATION_ERROR,
            details=details
        )

class ConnectionError(MCPError):
    """Error raised when connection to server fails"""
    def __init__(self, message: str) -> None:
        super().__init__(
            message,
            code=MCPErrorCode.CONNECTION_ERROR
        )

class AuthenticationError(MCPError):
    """Error raised when authentication fails"""
    def __init__(self, message: str = "Authentication failed") -> None:
        super().__init__(
            message,
            code=MCPErrorCode.AUTHENTICATION_ERROR
        )
