import pytest
from mpc_remote.client.session import (
    MCPSession, 
    ClientCapabilities, 
    VersionInfo,
    VersionNegotiation
)
from mpc_remote.version import __version__

@pytest.mark.asyncio
async def test_version_negotiation():
    session = MCPSession()
    
    # Test compatible version
    assert await session.initialize_version(__version__)
    
    # Test incompatible version
    assert not await session.initialize_version("0.0.1")

@pytest.mark.asyncio
async def test_capability_negotiation():
    session = MCPSession()
    
    # Test basic capabilities
    caps = ClientCapabilities(
        version=__version__,
        features=["basic"],
        extensions={}
    )
    assert await session.negotiate_capabilities(caps)
    
    # Test empty capabilities
    empty_caps = ClientCapabilities(
        version=__version__,
        features=[],
        extensions={}
    )
    assert not await session.negotiate_capabilities(empty_caps)

@pytest.mark.asyncio
async def test_session_initialization():
    session = MCPSession()
    
    # Test full initialization sequence
    assert await session.initialize_version(__version__)
    
    caps = ClientCapabilities(
        version=__version__,
        features=["basic", "streaming"],
        extensions={"custom": True}
    )
    assert await session.negotiate_capabilities(caps)
    
    # Verify capability state
    assert session.capabilities is not None
    assert "basic" in session.capabilities.active_features
    assert "streaming" in session.capabilities.active_features
    assert session.capabilities.extensions.get("custom") is True