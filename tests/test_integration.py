"""Integration tests for MPC Remote"""

import asyncio

import pytest

from mpc_remote.core.constants import ToolType
from mpc_remote.core.protocol import Tool
from mpc_remote.security.auth import AuthenticatedProtocolHandler


@pytest.mark.asyncio
async def test_complete_workflow(transport_pair, mock_auth_provider):
    """Test a complete workflow including authentication, resource access, and tool execution"""
    server, client = transport_pair
    handler = AuthenticatedProtocolHandler(mock_auth_provider)
    
    # Register test tool
    async def process_data(value: int) -> str:
        return "high" if value > 30 else "normal"
    
    handler.register_tool(Tool(
        name="analyze_value",
        implementation=process_data,
        type=ToolType.FUNCTION
    ))
    
    # Set up server handler
    async def handle_server():
        request = await server.socket.recv_json()
        result = await handler.execute_tool(
            request["params"]["tool_name"],
            request["params"]["tool_params"],
            auth_token=request["auth"]
        )
        await server.socket.send_json({"result": result})
    
    server_task = asyncio.create_task(handle_server())
    
    try:
        # Execute tool
        response = await client.send_request({
            "method": "execute_tool",
            "params": {
                "tool_name": "analyze_value",
                "tool_params": {"value": 35}
            },
            "auth": "valid_token"
        })
        
        assert response["result"] == "high"
        
    finally:
        await server_task

@pytest.mark.asyncio
async def test_error_propagation(transport_pair, mock_auth_provider):
    """Test that errors are properly propagated from server to client"""
    server, client = transport_pair
    handler = AuthenticatedProtocolHandler(mock_auth_provider)
    
    # Register failing tool
    def failing_tool():
        raise ValueError("Expected test error")
    
    handler.register_tool(Tool(
        name="failing_tool",
        implementation=failing_tool,
        type=ToolType.FUNCTION
    ))
    
    # Set up server handler
    async def handle_server():
        request = await server.socket.recv_json()
        try:
            result = await handler.execute_tool(
                request["params"]["tool_name"],
                request["params"]["tool_params"],
                auth_token=request["auth"]
            )
            await server.socket.send_json({"result": result})
        except Exception as e:
            await server.socket.send_json({
                "error": {
                    "code": -32000,
                    "message": str(e)
                }
            })
    
    server_task = asyncio.create_task(handle_server())
    
    try:
        # Execute failing tool
        response = await client.send_request({
            "method": "execute_tool",
            "params": {
                "tool_name": "failing_tool",
                "tool_params": {}
            },
            "auth": "valid_token"
        })
        
        assert "error" in response
        assert response["error"]["code"] == -32000
        assert "Expected test error" in response["error"]["message"]
        
    finally:
        await server_task