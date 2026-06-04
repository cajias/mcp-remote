"""Pytest configuration and shared fixtures"""

import asyncio
import sys

import pytest

# On Windows, pyzmq's asyncio support requires a selector-based event loop. The
# default ProactorEventLoop pulls in an optional `tornado` dependency, which
# raises ModuleNotFoundError at teardown of the zmq integration tests. Forcing
# the selector policy on Windows avoids that path (matches Linux/macOS behavior).
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

from mpc_remote.core.protocol import ProtocolHandler
from mpc_remote.security.auth import AuthProvider
from mpc_remote.transport.zmq_transport import ZMQTransport


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

    # Wait longer for connection establishment
    await asyncio.sleep(1.0)

    yield server, client

    # Cleanup
    server.close()
    client.close()

@pytest.fixture
def mock_auth_provider():
    """Provide a mock authentication provider for testing."""
    class MockAuthProvider(AuthProvider):
        def __init__(self) -> None:
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
