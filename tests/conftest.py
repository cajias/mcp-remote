"""Pytest configuration and shared fixtures"""

import asyncio

import pytest

from mpc_remote.core.protocol import ProtocolHandler
from mpc_remote.security.auth import AuthProvider
from mpc_remote.transport.zmq import ZMQTransport


# Enable asyncio support for pytest
@pytest.fixture
def event_loop():
    """Create an instance of the default event loop for each test case."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

# Common test fixtures that can be shared across test files
@pytest.fixture
async def protocol_handler():
    """Provide a fresh protocol handler for each test."""
    handler = ProtocolHandler()
    return handler

@pytest.fixture
async def transport_pair():
    """Create a connected pair of ZMQ transports (server and client)."""
    # Create transports with a unique port to avoid conflicts
    port = 5555
    server = ZMQTransport(f'tcp://*:{port}', connection_type='bind')
    client = ZMQTransport(f'tcp://localhost:{port}', connection_type='connect')
    
    # Allow time for connection establishment
    await asyncio.sleep(0.1)
    
    yield server, client
    
    # Cleanup
    server.close()
    client.close()

@pytest.fixture
def mock_auth_provider():
    """Provide a mock authentication provider for testing."""
    class MockAuthProvider(AuthProvider):
        def __init__(self):
            self.valid_tokens = {"valid_token", "admin_token"}
            self.admin_tokens = {"admin_token"}
        
        async def verify_token(self, token: str) -> bool:
            return token in self.valid_tokens
        
        async def check_tool_permission(self, token: str, tool_name: str) -> bool:
            if token in self.admin_tokens:
                return True
            return not tool_name.startswith("admin_")
    
    return MockAuthProvider()

# Configure pytest-asyncio
def pytest_configure(config):
    """Configure pytest with asyncio settings."""
    config.addinivalue_line(
        "markers",
        "asyncio: mark test as async"
    )

# Error handling for unclosed event loops
@pytest.fixture(autouse=True)
def check_event_loop():
    """Ensure each test starts with a fresh event loop and cleanup properly."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    yield
    if not loop.is_closed():
        loop.close()