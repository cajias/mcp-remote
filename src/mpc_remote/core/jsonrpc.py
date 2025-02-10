"""JSON-RPC 2.0 implementation for Model Context Protocol"""

import uuid
import json
from typing import Any, Dict, Optional, Union

class JSONRPCError(Exception):
    """Base exception for JSON-RPC errors"""
    def __init__(self, code: int, message: str, data: Optional[Any] = None):
        self.code = code
        self.message = message
        self.data = data
        super().__init__(f"JSON-RPC Error {code}: {message}")

class JSONRPCProtocol:
    """
    JSON-RPC 2.0 protocol handler
    
    Manages message creation, parsing, and routing
    """
    # Standard JSON-RPC 2.0 error codes
    ERROR_PARSE = -32700
    ERROR_INVALID_REQUEST = -32600
    ERROR_METHOD_NOT_FOUND = -32601
    ERROR_INVALID_PARAMS = -32602
    ERROR_INTERNAL = -32603

    @classmethod
    def create_request(
        cls, 
        method: str, 
        params: Optional[Union[Dict[str, Any], list]] = None,
        id: Optional[Union[str, int]] = None
    ) -> Dict[str, Any]:
        """
        Create a JSON-RPC 2.0 request
        
        :param method: Method to invoke
        :param params: Method parameters (optional)
        :param id: Request identifier (optional)
        :return: Formatted JSON-RPC request
        """
        request = {
            "jsonrpc": "2.0",
            "method": method
        }
        
        if params is not None:
            request["params"] = params
        
        # Generate ID if not provided
        request["id"] = id or str(uuid.uuid4())
        
        return request
    
    @classmethod
    def create_response(
        cls, 
        result: Optional[Any] = None, 
        error: Optional[JSONRPCError] = None, 
        id: Optional[Union[str, int]] = None
    ) -> Dict[str, Any]:
        """
        Create a JSON-RPC 2.0 response
        
        :param result: Successful result (mutually exclusive with error)
        :param error: Error information
        :param id: Request identifier
        :return: Formatted JSON-RPC response
        """
        response = {"jsonrpc": "2.0"}
        
        if error:
            response["error"] = {
                "code": error.code,
                "message": error.message,
                **({"data": error.data} if error.data else {})
            }
        elif result is not None:
            response["result"] = result
        
        if id is not None:
            response["id"] = id
        
        return response
    
    @classmethod
    def parse_message(cls, message: Union[str, Dict[str, Any]]) -> Dict[str, Any]:
        """
        Parse a JSON-RPC 2.0 message
        
        :param message: JSON-RPC message (string or dict)
        :return: Parsed message
        :raises JSONRPCError: For invalid message formats
        """
        # Ensure dictionary format
        if isinstance(message, str):
            try:
                message = json.loads(message)
            except json.JSONDecodeError:
                raise JSONRPCError(
                    cls.ERROR_PARSE, 
                    "Parse error"
                )
        
        # Validate JSON-RPC version
        if message.get("jsonrpc") != "2.0":
            raise JSONRPCError(
                cls.ERROR_INVALID_REQUEST, 
                "Invalid JSON-RPC version"
            )
        
        return message
    
    @classmethod
    def is_request(cls, message: Dict[str, Any]) -> bool:
        """
        Check if message is a JSON-RPC request
        
        :param message: Parsed message
        :return: True if request, False otherwise
        """
        return "method" in message and "id" in message
    
    @classmethod
    def is_response(cls, message: Dict[str, Any]) -> bool:
        """
        Check if message is a JSON-RPC response
        
        :param message: Parsed message
        :return: True if response, False otherwise
        """
        return ("result" in message or "error" in message) and "id" in message
