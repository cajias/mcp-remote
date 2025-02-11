"""Test transport security features."""

import asyncio
import pytest
import zmq
import zmq.auth
from zmq.utils.z85 import encode
from zmq.auth.asyncio import AsyncioAuthenticator

from mpc_remote.client import MCPClient
from mpc_remote.transport.zmq import ZMQSecurity, ZMQTransport

async def test_zmq_curve_security():
    """Test ZMQ CURVE security setup."""
    
    # Generate server and client keys
    server_keys = ZMQSecurity.generate()
    client_keys = ZMQSecurity.generate()
    
    # Create secure transport
    transport = ZMQTransport.create_secure_client(
        "tcp://localhost:5555",
        encode(server_keys.public_key),
        client_keys
    )
    
    # Verify CURVE security is configured
    await transport.initialize()
    assert transport.socket.mechanism == zmq.CURVE
    assert transport.socket.curve_serverkey == server_keys.public_key
    assert transport.socket.curve_publickey == client_keys.public_key
    assert transport.socket.curve_secretkey == client_keys.secret_key
    
    await transport.close()

async def test_inproc_transport():
    """Test in-process transport."""
    
    url = "inproc://test"
    
    # Create server and client context
    ctx = zmq.asyncio.Context()
    
    try:
        # Create server socket
        server = ctx.socket(zmq.REP)
        server.bind(url)
        
        # Create client session
        async with await MCPClient.connect(url, context=ctx) as session:
            assert isinstance(session._transport, ZMQTransport)
            assert session._transport.is_connected
            
            # Test communication
            server_task = asyncio.create_task(server.recv_json())
            
            await session.call_tool("test", {"arg": "value"})
            
            # Verify server received message
            msg = await server_task
            assert msg["method"] == "tools/call"
            assert msg["params"]["name"] == "test"
        
    finally:
        server.close()
        ctx.term()

async def test_secure_client_creation():
    """Test secure client creation through MCPClient."""
    
    # Generate server keys
    server_keys = ZMQSecurity.generate()
    server_public = encode(server_keys.public_key)
    
    # Create secure client session
    session = await MCPClient.connect(
        "tcp://localhost:5555",
        server_key=server_public
    )
    
    assert isinstance(session._transport, ZMQTransport)
    assert session._transport.security is not None
    assert session._transport.socket.mechanism == zmq.CURVE
    
    # Test with provided client keys
    client_keys = MCPClient.generate_client_keys()
    session = await MCPClient.connect(
        "tcp://localhost:5555",
        server_key=server_public,
        client_keys=client_keys
    )
    
    assert session._transport.security.public_key == client_keys.public_key
    assert session._transport.security.secret_key == client_keys.secret_key

@pytest.mark.integration
async def test_secure_protocol_flow():
    """Test full protocol flow with secure transport."""
    
    # Set up secure server
    server_keys = ZMQSecurity.generate()
    ctx = zmq.asyncio.Context()
    
    auth = AsyncioAuthenticator(ctx)
    auth.start()
    auth.configure_curve(domain='*', location=zmq.auth.CURVE_ALLOW_ANY)
    
    server = ctx.socket(zmq.REP)
    server.curve_server = True
    server.curve_secretkey = server_keys.secret_key
    server.curve_publickey = server_keys.public_key
    server.bind("tcp://127.0.0.1:5555")
    
    try:
        # Create secure client session
        async with await MCPClient.connect(
            "tcp://127.0.0.1:5555",
            server_key=encode(server_keys.public_key)
        ) as session:
            await session.initialize()
            
            # Test protocol operations
            server_task = asyncio.create_task(server.recv_json())
            await session.call_tool("test", {"arg": "value"})
            
            # Verify secure communication worked
            msg = await server_task
            assert msg["method"] == "tools/call"
            
            # Server responds
            await server.send_json({
                "id": msg.get("id"),
                "result": {"status": "ok"}
            })
    
    finally:
        server.close()
        auth.stop()
        ctx.term()

@pytest.mark.integration
async def test_multi_transport_protocol():
    """Test protocol consistency across different transports."""
    
    test_inputs = [
        ("tcp://localhost:5555", ZMQTransport),
        ("ipc:///tmp/test.sock", ZMQTransport),
        ("inproc://test", ZMQTransport)
    ]
    
    for url, transport_class in test_inputs:
        # Create session with specific transport
        session = await MCPClient.connect(url)
        assert isinstance(session._transport, transport_class)
        
        # Verify protocol capabilities are consistent
        caps = session._transport._client_capabilities
        if caps:
            # Core protocol capabilities should be same across transports
            assert caps.roots.listChanged is True
            # But transport capabilities may differ
            assert caps.transport is not None

async def test_zmq_security_error_handling():
    """Test error handling in ZMQ security setup."""
    
    # Test missing server key
    with pytest.raises(ValueError, match="server public key"):
        transport = ZMQTransport(
            "tcp://localhost:5555",
            security=ZMQSecurity(
                public_key=b"client-public",
                secret_key=b"client-secret"
            )
        )
        await transport.initialize()
    
    # Test missing client keys
    with pytest.raises(ValueError, match="Both public and secret keys required"):
        transport = ZMQTransport(
            "tcp://localhost:5555",
            security=ZMQSecurity(
                server_public_key=b"server-public"
            )
        )
        await transport.initialize()

async def test_transport_options():
    """Test passing transport-specific options."""
    
    # Test ZMQ socket options
    session = await MCPClient.connect(
        "tcp://localhost:5555",
        LINGER=0,
        RCVTIMEO=1000,
        SNDTIMEO=1000
    )
    
    transport = session._transport
    assert isinstance(transport, ZMQTransport)
    assert transport.socket_options.get('LINGER') == 0
    assert transport.socket_options.get('RCVTIMEO') == 1000
    assert transport.socket_options.get('SNDTIMEO') == 1000
    
    # Test inproc with custom context
    ctx = zmq.asyncio.Context()
    try:
        session = await MCPClient.connect(
            "inproc://test",
            context=ctx
        )
        assert isinstance(session._transport, ZMQTransport)
        assert session._transport.context == ctx
    finally:
        ctx.term()