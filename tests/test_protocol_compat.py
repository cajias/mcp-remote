"""Test compatibility with original MCP SDK client"""
import pytest
from pydantic import BaseModel
from mpc_remote.protocol.adapter import ProtocolAdapter, InitializeParams, LegacyCapabilities, RootsCapability

async def test_initialize_request_compatibility():
    """Test that we handle the original SDK initialize request correctly"""
    original_request = InitializeParams(
        protocolVersion="1.0",
        capabilities=LegacyCapabilities(
            sampling=None,
            experimental=None,
            roots=RootsCapability(listChanged=True)
        ),
        clientInfo={
            "name": "mcp",
            "version": "0.1.0"
        }
    )
    
    adapter = ProtocolAdapter()
    version, capabilities = adapter.adapt_initialize_request(original_request)
    
    # Check version handling
    assert version == "1.0"
    
    # Critical: Verify roots capability is preserved
    assert capabilities["extensions"]["roots"]["listChanged"] is True
    
    # Check response compatibility
    response = adapter.adapt_initialize_response(version, capabilities)
    
    # Original SDK expects these exact response fields
    assert "protocolVersion" in response
    assert "capabilities" in response
    assert "streaming" in response["capabilities"]
    assert "roots" in response["capabilities"]
    assert response["capabilities"]["roots"]["listChanged"] is True

async def test_tools_compatibility():
    """Test compatibility with original SDK tool calls"""
    adapter = ProtocolAdapter()
    adapter.legacy_mode = True
    
    # Original SDK tools/call format
    original_tool_call = {
        "name": "my_tool",
        "arguments": ["arg1", "arg2"]  # Original uses array arguments
    }
    
    # Adapt request
    adapted = adapter.adapt_request("tools/call", original_tool_call)
    
    # Check format conversion to dict as expected by original SDK
    assert adapted["name"] == "my_tool"
    assert isinstance(adapted["arguments"], dict)
    assert adapted["arguments"]["args"] == ["arg1", "arg2"]
    
    # Test tools/list response
    original_tools_list = {
        "tools": [
            {
                "name": "my_tool",
                "description": "A tool"
            }
        ]
    }
    
    adapted_response = adapter.adapt_response("tools/list", original_tools_list)
    
    # Check required legacy fields are added correctly
    assert "schema" in adapted_response["tools"][0]
    assert adapted_response["tools"][0]["schema"] == {"type": "object", "properties": {}}
    assert "required" in adapted_response["tools"][0]
    assert adapted_response["tools"][0]["required"] == []

async def test_resource_compatibility():
    """Test compatibility with original SDK resource handling"""
    adapter = ProtocolAdapter()
    adapter.legacy_mode = True
    
    # Original SDK resources/list response format
    original_resources = {
        "resources": [
            {
                "uri": "resource:my_resource"
            }
        ]
    }
    
    # Adapt response
    adapted = adapter.adapt_response("resources/list", original_resources)
    
    # Check legacy fields are added correctly
    for resource in adapted["resources"]:
        assert "type" in resource
        assert resource["type"] == "text"  # Default in original SDK
        assert "metadata" in resource
        assert isinstance(resource["metadata"], dict)

async def test_completion_compatibility():
    """Test compatibility with original SDK completion requests"""
    adapter = ProtocolAdapter()
    adapter.legacy_mode = True
    
    # Original SDK format with string argument
    original_completion = {
        "argument": "Hello, how are you?"
    }
    
    # Test string argument preservation
    adapted = adapter.adapt_request("completion/complete", original_completion)
    assert adapted["argument"] == "Hello, how are you?"
    
    # Test dict argument conversion
    dict_completion = {
        "argument": {
            "prompt": "What's the weather?",
            "metadata": {"temperature": 0.7}
        }
    }
    
    adapted = adapter.adapt_request("completion/complete", dict_completion)
    assert adapted["argument"] == "What's the weather?"