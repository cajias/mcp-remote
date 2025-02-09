"""Tests for authentication layer implementation"""


import pytest

from mpc_remote.core.constants import ToolType
from mpc_remote.core.errors import MCPError
from mpc_remote.core.protocol import Tool
from mpc_remote.security.auth import AuthenticatedProtocolHandler, AuthProvider


@pytest.fixture
def test_auth_provider():
    """Provide a test authentication provider"""
    class TestAuthProvider(AuthProvider):
        async def verify_token(self, token: str) -> bool:
            """Verify if a token is valid"""
            valid_tokens = {
                "user_token": {"role": "user"},
                "admin_token": {"role": "admin"}
            }
            return token in valid_tokens

        async def check_tool_permission(self, token: str, tool_name: str) -> bool:
            """Check if a token has permission to use a tool"""
            if token not in ("user_token", "admin_token"):
                return False
            
            if token == "admin_token":
                return True
                
            return tool_name == "basic_tool"
    
    return TestAuthProvider()

@pytest.fixture
async def auth_handler(test_auth_provider):
    """Provide a configured authenticated protocol handler"""
    handler = AuthenticatedProtocolHandler(test_auth_provider)
    
    # Register test tools
    async def basic_tool(value: int) -> int:
        return value * 2

    async def admin_tool(value: int) -> int:
        return value * 10
    
    handler.register_tool(Tool(
        name="basic_tool",
        implementation=basic_tool,
        type=ToolType.FUNCTION
    ))
    
    handler.register_tool(Tool(
        name="admin_tool",
        implementation=admin_tool,
        type=ToolType.FUNCTION
    ))
    
    return handler

@pytest.mark.asyncio
async def test_valid_authentication(auth_handler):
    """Test successful authentication and tool execution"""
    # Execute basic tool with user token
    result = await auth_handler.execute_tool(
        "basic_tool",
        {"value": 21},
        auth_token="user_token"
    )
    assert result == 42

@pytest.mark.asyncio
async def test_invalid_token(auth_handler):
    """Test handling of invalid authentication token"""
    with pytest.raises(MCPError) as exc_info:
        await auth_handler.execute_tool(
            "basic_tool",
            {"value": 21},
            auth_token="invalid_token"
        )
    assert "Authentication failed" in str(exc_info.value)

@pytest.mark.asyncio
async def test_missing_token(auth_handler):
    """Test handling of missing authentication token"""
    with pytest.raises(MCPError) as exc_info:
        await auth_handler.execute_tool(
            "basic_tool",
            {"value": 21}
        )
    assert "Authentication required" in str(exc_info.value)

@pytest.mark.asyncio
async def test_permission_enforcement(auth_handler):
    """Test enforcement of tool permissions"""
    # User can access basic tool
    result = await auth_handler.execute_tool(
        "basic_tool",
        {"value": 21},
        auth_token="user_token"
    )
    assert result == 42
    
    # User cannot access admin tool
    with pytest.raises(MCPError) as exc_info:
        await auth_handler.execute_tool(
            "admin_tool",
            {"value": 21},
            auth_token="user_token"
        )
    assert "Permission denied" in str(exc_info.value)
    
    # Admin can access both tools
    result = await auth_handler.execute_tool(
        "admin_tool",
        {"value": 21},
        auth_token="admin_token"
    )
    assert result == 210

@pytest.mark.asyncio
async def test_auth_provider_interface():
    """Test that custom auth providers must implement required methods"""
    class IncompleteAuthProvider:
        pass
    
    with pytest.raises(TypeError):
        AuthenticatedProtocolHandler(IncompleteAuthProvider())

@pytest.mark.asyncio
async def test_capabilities_with_auth(auth_handler):
    """Test that authentication doesn't affect capability reporting"""
    capabilities = auth_handler.get_capabilities()
    
    # Verify both tools are listed in capabilities
    assert "basic_tool" in capabilities["tools"]
    assert "admin_tool" in capabilities["tools"]
    
    # Verify tool information doesn't include implementation details
    for tool_info in capabilities["tools"].values():
        assert "implementation" not in tool_info