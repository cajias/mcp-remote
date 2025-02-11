"""Test MCP client with URL-based transport selection."""

import pytest
import ssl
from mpc_remote.client import MCPClient
from mpc_remote.transport.stdio import StdIOTransport
from mpc_remote.transport.zmq import ZMQTransport
from mpc_remote.transport.websocket import WebSocketTransport

async def test_url_based_transport_selection():
    """Test that appropriate transport is selected based on URL."""
    
    # Test stdio (default)
    session = await MCPClient.connect()
    assert isinstance(session._transport, StdIOTransport)
    
    # Test ZMQ TCP
    session = await MCPClient.connect("tcp://localhost:5555")
    assert isinstance(session._transport, ZMQTransport)
    
    # Test ZMQ IPC
    session = await MCPClient.connect("ipc:///tmp/test.sock")
    assert isinstance(session._transport, ZMQTransport)
    
    # Test WebSocket
    session = await MCPClient.connect("ws://localhost:8080")
    assert isinstance(session._transport, WebSocketTransport)
    
    # Test WebSocket Secure
    session = await MCPClient.connect("wss://example.com/mcp")
    assert isinstance(session._transport, WebSocketTransport)
    
    # Test invalid scheme
    with pytest.raises(ValueError, match="Unsupported URL scheme"):
        await MCPClient.connect("invalid://localhost")

async def test_transport_options():
    """Test passing transport-specific options."""
    
    # Test ZMQ options
    session = await MCPClient.connect(
        "tcp://localhost:5555",
        LINGER=0,
        RCVTIMEO=1000
    )
    assert isinstance(session._transport, ZMQTransport)
    assert session._transport.socket_options.get('LINGER') == 0
    assert session._transport.socket_options.get('RCVTIMEO') == 1000

    # Test WebSocket options with SSL
    ssl_context = ssl.create_default_context()
    session = await MCPClient.connect(
        "wss://example.com/mcp",
        ssl_context=ssl_context,
        ping_interval=20,
        ping_timeout=10
    )
    assert isinstance(session._transport, WebSocketTransport)
    assert session._transport.ssl == ssl_context
    assert session._transport.ws_options.get('ping_interval') == 20
    assert session._transport.ws_options.get('ping_timeout') == 10

async def test_transport_lifecycle():
    """Test transport initialization and cleanup."""
    
    async with await MCPClient.connect("tcp://localhost:5555") as session:
        # Check transport is initialized
        assert session._transport.is_connected
        
        # Test protocol operations are proxied to transport
        await session.initialize()
        
    # Check transport is cleaned up
    assert not session._transport.is_connected

@pytest.mark.integration
async def test_full_protocol_flow():
    """Test full protocol flow over different transports."""
    
    # Test over ZMQ
    async with await MCPClient.connect("tcp://localhost:5555") as session:
        await session.initialize()
        
        # Call a tool
        result = await session.call_tool("echo", {"message": "test"})
        assert result == {"message": "test"}
        
        # Test completion
        completion = await session.complete(
            "test-prompt",
            {"prompt": "Hello"}
        )
        assert completion.completion
        
    # Test over WebSocket
    async with await MCPClient.connect("ws://localhost:8080") as session:
        await session.initialize()
        
        # Same protocol operations should work identically
        result = await session.call_tool("echo", {"message": "test"})
        assert result == {"message": "test"}
        
    # Test over stdio (canonical SDK compatibility)
    async with await MCPClient.connect() as session:
        await session.initialize()
        
        # Protocol should work the same way as canonical SDK
        result = await session.call_tool("echo", {"message": "test"})
        assert result == {"message": "test"}