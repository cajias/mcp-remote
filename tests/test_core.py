"""Tests for core protocol components"""

import asyncio

import pytest

from mpc_remote.core.constants import ResourceAccessLevel, ToolType
from mpc_remote.core.errors import MCPError
from mpc_remote.core.protocol import ProtocolHandler, Resource, Tool


@pytest.mark.asyncio
async def test_protocol_handler_initialization():
    """Test basic protocol handler initialization and version handling"""
    handler = ProtocolHandler(version="1.0")
    capabilities = handler.get_capabilities()
    assert capabilities["protocol_version"] == "1.0"
    assert isinstance(capabilities["resources"], dict)
    assert isinstance(capabilities["tools"], dict)

@pytest.mark.asyncio
async def test_resource_registration():
    """Test resource registration and capability reporting"""
    handler = ProtocolHandler()
    
    resource = Resource(
        name="test_resource",
        type="document",
        description="A test resource",
        access_level=ResourceAccessLevel.READ_ONLY
    )
    handler.register_resource(resource)
    
    capabilities = handler.get_capabilities()
    assert "test_resource" in capabilities["resources"]
    
    resource_info = capabilities["resources"]["test_resource"]
    assert resource_info["type"] == "document"
    assert resource_info["access_level"] == "read-only"

@pytest.mark.asyncio
async def test_sync_tool_execution():
    """Test execution of synchronous tools"""
    handler = ProtocolHandler()
    
    def add_numbers(a: int, b: int) -> int:
        return a + b
    
    tool = Tool(
        name="add",
        implementation=add_numbers,
        description="Add two numbers",
        type=ToolType.FUNCTION
    )
    handler.register_tool(tool)
    
    result = await handler.execute_tool("add", {"a": 5, "b": 3})
    assert result == 8

@pytest.mark.asyncio
async def test_async_tool_execution():
    """Test execution of asynchronous tools"""
    handler = ProtocolHandler()
    
    async def delayed_add(a: int, b: int) -> int:
        await asyncio.sleep(0.1)  # Simulate async operation
        return a + b
    
    tool = Tool(
        name="async_add",
        implementation=delayed_add,
        description="Add two numbers asynchronously",
        type=ToolType.FUNCTION
    )
    handler.register_tool(tool)
    
    result = await handler.execute_tool("async_add", {"a": 5, "b": 3})
    assert result == 8

@pytest.mark.asyncio
async def test_tool_error_handling():
    """Test proper error handling during tool execution"""
    handler = ProtocolHandler()
    
    def failing_tool():
        raise ValueError("Expected test error")
    
    tool = Tool(
        name="failing_tool",
        implementation=failing_tool,
        type=ToolType.FUNCTION
    )
    handler.register_tool(tool)
    
    with pytest.raises(MCPError) as exc_info:
        await handler.execute_tool("failing_tool", {})
    assert "Expected test error" in str(exc_info.value)

@pytest.mark.asyncio
async def test_missing_tool_error():
    """Test error handling when requesting non-existent tool"""
    handler = ProtocolHandler()
    
    with pytest.raises(MCPError) as exc_info:
        await handler.execute_tool("nonexistent_tool", {})
    assert "not found" in str(exc_info.value)