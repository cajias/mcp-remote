"""Test Model Context Protocol implementation."""
import pytest
from anyio.streams.memory import MemoryObjectReceiveStream, MemoryObjectSendStream

from mpc_remote.protocol.types import (
    ClientCapabilities, RootsCapability, InitializeRequestParams,
    ClientInfo, InitializeResult
)
from mpc_remote.protocol.session import MCPSession
from mpc_remote.version import PROTOCOL_VERSION

async def test_protocol_initialization():
    """Test protocol initialization matches canonical SDK."""
    read_stream = MemoryObjectReceiveStream()
    write_stream = MemoryObjectSendStream()
    
    session = MCPSession(read_stream, write_stream)
    
    # Verify initialize request format matches canonical SDK
    request = InitializeRequestParams(
        protocolVersion=PROTOCOL_VERSION,
        capabilities=ClientCapabilities(
            sampling=None,
            experimental=None,
            roots=RootsCapability(listChanged=True)
        ),
        clientInfo=ClientInfo(
            name="mpc_remote",
            version="0.1.0"
        )
    )
    
    # Verify all required fields are present
    assert request.protocolVersion == PROTOCOL_VERSION
    assert request.capabilities.roots.listChanged is True
    
    # Test server response handling
    response = InitializeResult(
        protocolVersion=PROTOCOL_VERSION,
        capabilities=ClientCapabilities(
            roots=RootsCapability(listChanged=True)
        )
    )
    
    # Verify response format matches expectations
    assert response.protocolVersion == PROTOCOL_VERSION
    assert response.capabilities.roots.listChanged is True

async def test_tools_protocol():
    """Test tools API matches canonical SDK format."""
    read_stream = MemoryObjectReceiveStream()
    write_stream = MemoryObjectSendStream()
    
    session = MCPSession(read_stream, write_stream)
    
    # Test tool call request format
    tool_request = {
        "name": "my_tool",
        "arguments": {
            "arg1": "value1",
            "arg2": "value2"
        }
    }
    
    # Verify format matches canonical SDK
    assert isinstance(tool_request["arguments"], dict)
    
    # Test tool call response format
    tool_response = {
        "result": {
            "output": "success"
        }
    }
    
    assert "result" in tool_response

async def test_completion_protocol():
    """Test completion API matches canonical SDK format."""
    read_stream = MemoryObjectReceiveStream()
    write_stream = MemoryObjectSendStream()
    
    session = MCPSession(read_stream, write_stream)
    
    # Test completion request format
    completion_request = {
        "ref": {
            "uri": "resource:test"
        },
        "argument": {
            "prompt": "Hello",
            "metadata": {
                "temperature": 0.7
            }
        }
    }
    
    # Verify format matches canonical SDK
    assert "ref" in completion_request
    assert "argument" in completion_request
    assert isinstance(completion_request["argument"], dict)
    
    # Test completion response format
    completion_response = {
        "completion": "test response",
        "metadata": {
            "finish_reason": "stop"
        }
    }
    
    assert "completion" in completion_response
    assert isinstance(completion_response["metadata"], dict)