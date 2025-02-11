"""Tests for JSON-RPC 2.0 Implementation"""

import json

import pytest

from mpc_remote.core.jsonrpc import JSONRPCError, JSONRPCProtocol, JSONRPCRequest, JSONRPCResponse


class TestJSONRPCProtocol:
    """Test JSON-RPC 2.0 Protocol Implementation"""
    
    def test_create_request(self):
        """Test creating a valid JSON-RPC request"""
        request = JSONRPCProtocol.create_request("test_method", {"param1": "value"})
        
        assert request.jsonrpc == "2.0"
        assert request.method == "test_method"
        assert request.params == {"param1": "value"}
        assert request.id is not None
    
    def test_create_response_with_result(self):
        """Test creating a response with a result"""
        response = JSONRPCProtocol.create_response(result="success", id="test_id")
        
        assert response.jsonrpc == "2.0"
        assert response.result == "success"
        assert response.id == "test_id"
    
    def test_create_response_with_error(self):
        """Test creating a response with an error"""
        error = JSONRPCError(
            code=JSONRPCProtocol.ERROR_INVALID_REQUEST, 
            message="Invalid request"
        )
        response = JSONRPCProtocol.create_response(error=error, id="error_id")
        
        assert response.jsonrpc == "2.0"
        assert response.error.code == JSONRPCProtocol.ERROR_INVALID_REQUEST
        assert response.error.message == "Invalid request"
        assert response.id == "error_id"
    
    def test_parse_message_valid_json_string(self):
        """Test parsing a valid JSON-RPC request from a string"""
        message_str = json.dumps({
            "jsonrpc": "2.0", 
            "method": "test", 
            "id": "123"
        })
        parsed = JSONRPCProtocol.parse_message(message_str, expected_type=JSONRPCRequest)
        
        assert parsed.jsonrpc == "2.0"
        assert parsed.method == "test"
        assert parsed.id == "123"
    
    def test_parse_message_invalid_version(self):
        """Test parsing a message with invalid version"""
        with pytest.raises(ValueError, match="Unsupported JSON-RPC version"):
            JSONRPCProtocol.parse_message({"jsonrpc": "1.0", "method": "test"})
    
    def test_parse_message_invalid_json(self):
        """Test parsing an invalid JSON string"""
        with pytest.raises(ValueError, match="Invalid JSON"):
            JSONRPCProtocol.parse_message("invalid json")
    
    def test_is_request(self):
        """Test identifying a JSON-RPC request"""
        request = {"jsonrpc": "2.0", "method": "test", "id": "123"}
        
        assert JSONRPCProtocol.is_request(request) is True
    
    def test_is_response(self):
        """Test identifying a JSON-RPC response"""
        response = {"jsonrpc": "2.0", "result": "success", "id": "123"}
        
        assert JSONRPCProtocol.is_response(response) is True
