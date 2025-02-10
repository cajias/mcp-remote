"""Tests for JSON-RPC 2.0 Implementation"""

import pytest
import json
from mpc_remote.core.jsonrpc import JSONRPCProtocol, JSONRPCError


class TestJSONRPCProtocol:
    """Test JSON-RPC 2.0 Protocol Implementation"""
    
    def test_create_request(self):
        """Test creating a valid JSON-RPC request"""
        rpc = JSONRPCProtocol()
        request = rpc.create_request("test_method", {"param1": "value"})
        
        assert request["jsonrpc"] == "2.0"
        assert request["method"] == "test_method"
        assert request["params"] == {"param1": "value"}
        assert "id" in request
    
    def test_create_response_with_result(self):
        """Test creating a response with a result"""
        rpc = JSONRPCProtocol()
        response = rpc.create_response(result="success", id="test_id")
        
        assert response["jsonrpc"] == "2.0"
        assert response["result"] == "success"
        assert response["id"] == "test_id"
    
    def test_create_response_with_error(self):
        """Test creating a response with an error"""
        rpc = JSONRPCProtocol()
        error = JSONRPCError(
            code=rpc.ERROR_INVALID_REQUEST, 
            message="Invalid request"
        )
        response = rpc.create_response(error=error, id="error_id")
        
        assert response["jsonrpc"] == "2.0"
        assert response["error"]["code"] == rpc.ERROR_INVALID_REQUEST
        assert response["error"]["message"] == "Invalid request"
        assert response["id"] == "error_id"
    
    def test_parse_message_valid_json_string(self):
        """Test parsing a valid JSON-RPC message from a string"""
        rpc = JSONRPCProtocol()
        message_str = json.dumps({
            "jsonrpc": "2.0", 
            "method": "test", 
            "id": "123"
        })
        parsed = rpc.parse_message(message_str)
        
        assert parsed["jsonrpc"] == "2.0"
        assert parsed["method"] == "test"
        assert parsed["id"] == "123"
    
    def test_parse_message_invalid_version(self):
        """Test parsing a message with invalid version"""
        rpc = JSONRPCProtocol()
        with pytest.raises(JSONRPCError) as excinfo:
            rpc.parse_message({"jsonrpc": "1.0", "method": "test"})
        
        assert excinfo.value.code == rpc.ERROR_INVALID_REQUEST
    
    def test_parse_message_invalid_json(self):
        """Test parsing an invalid JSON string"""
        rpc = JSONRPCProtocol()
        with pytest.raises(JSONRPCError) as excinfo:
            rpc.parse_message("invalid json")
        
        assert excinfo.value.code == rpc.ERROR_PARSE
    
    def test_is_request(self):
        """Test identifying a JSON-RPC request"""
        rpc = JSONRPCProtocol()
        request = {"jsonrpc": "2.0", "method": "test", "id": "123"}
        
        assert rpc.is_request(request) is True
    
    def test_is_response(self):
        """Test identifying a JSON-RPC response"""
        rpc = JSONRPCProtocol()
        response = {"jsonrpc": "2.0", "result": "success", "id": "123"}
        
        assert rpc.is_response(response) is True
