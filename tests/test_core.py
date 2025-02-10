"""Tests for core protocol components"""

import asyncio
import pytest

from mpc_remote.core.constants import ResourceAccessLevel, ToolType
from mpc_remote.core.errors import MCPError
from mpc_remote.server.base import MCPServer

@pytest.mark.asyncio
async def test_server_initialization():
    """Test basic server initialization"""
    server = MCPServer(name="TestServer")
    capabilities = server.get_capabilities()
    assert capabilities["protocol_version"] == "1.0"
    assert isinstance(capabilities["resources"], dict)
    assert isinstance(capabilities["tools"], dict)

@pytest.mark.asyncio
async def test_resource_decorator():
    """Test resource registration via decorator"""
    server = MCPServer()
    
    @server.resource(
        name="test_resource",
        resource_type="document",
        description="A test resource",
        access_level=ResourceAccessLevel.READ_ONLY
    )
    class TestResource:
        def __init__(self):
            self.data = {}
    
    capabilities = server.get_capabilities()
    assert "test_resource" in capabilities["resources"]
    resource_info = capabilities["resources"]["test_resource"]
    assert resource_info["type"] == "document"
    assert resource_info["access_level"] == "read-only"

@pytest.mark.asyncio
async def test_sync_tool_decorator():
    """Test synchronous tool registration via decorator"""
    server = MCPServer()
    
    @server.tool(name="add")
    def add_numbers(a: int, b: int) -> int:
        return a + b
    
    result = await server.execute_tool("add", {"a": 5, "b": 3})
    assert result == 8

@pytest.mark.asyncio
async def test_async_tool_decorator():
    """Test asynchronous tool registration via decorator"""
    server = MCPServer()
    
    @server.tool(name="async_add")
    async def delayed_add(a: int, b: int) -> int:
        await asyncio.sleep(0.1)
        return a + b
    
    result = await server.execute_tool("async_add", {"a": 5, "b": 3})
    assert result == 8

@pytest.mark.asyncio
async def test_tool_error_handling():
    """Test error handling with decorated tools"""
    server = MCPServer()
    
    @server.tool(name="failing_tool")
    def failing_tool():
        raise ValueError("Expected test error")
    
    with pytest.raises(MCPError) as exc_info:
        await server.execute_tool("failing_tool", {})
    assert "Expected test error" in str(exc_info.value)

@pytest.mark.asyncio
async def test_missing_tool_error():
    """Test error handling for non-existent tools"""
    server = MCPServer()
    
    with pytest.raises(MCPError) as exc_info:
        await server.execute_tool("nonexistent_tool", {})
    assert "not found" in str(exc_info.value)

@pytest.mark.asyncio
async def test_params_schema_inference():
    """Test automatic parameter schema inference"""
    server = MCPServer()
    
    @server.tool(name="typed_tool")
    def typed_tool(x: int, y: float, name: str) -> bool:
        return True
    
    capabilities = server.get_capabilities()
    tool_info = capabilities["tools"]["typed_tool"]
    assert tool_info["params_schema"]["properties"]["x"]["type"] == "integer"
    assert tool_info["params_schema"]["properties"]["y"]["type"] == "number"
    assert tool_info["params_schema"]["properties"]["name"]["type"] == "string"