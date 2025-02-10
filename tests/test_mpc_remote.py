"""Tests for mpc_remote package."""

import pytest
from mpc_remote import __version__

from mpc_remote.core.protocol import ProtocolHandler
from mpc_remote.transport.zmq_transport import ZMQTransport


def test_version():
    """Test version is a string."""
    assert isinstance(__version__, str)
    assert len(__version__) > 0


@pytest.mark.asyncio
async def test_transport_creation():
    """Test transport basic initialization."""
    transport = ZMQTransport("tcp://localhost:5555", connection_type="connect")
    assert transport.endpoint == "tcp://localhost:5555"
    assert not transport._closed
    transport.close()
    assert transport._closed


@pytest.mark.asyncio
async def test_handler_initialization():
    """Test protocol handler initialization."""
    handler = ProtocolHandler()
    capabilities = handler.get_capabilities()
    assert isinstance(capabilities, dict)
    assert "protocol_version" in capabilities
    assert "tools" in capabilities
    assert isinstance(capabilities["tools"], dict)  # Tools are returned as a dict
    assert "resources" in capabilities
    assert isinstance(capabilities["resources"], dict)