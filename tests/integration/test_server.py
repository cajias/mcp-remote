import pytest
import asyncio
from mpc_remote import MCPClient
from tests.integration.server import MCPTestServer
from mpc_remote.transport.websocket import WebSocketServer

@pytest.fixture
async def server():
    server = MCPTestServer()
    server.register_tool("echo", lambda args: args)
    server.register_tool("add", lambda args: args["a"] + args["b"])
    
    transport = WebSocketServer("localhost", 8765)
    task = asyncio.create_task(server.serve(transport))
    yield server
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass

@pytest.mark.asyncio
async def test_basic_tool_call(server):
    async with MCPClient.connect("ws://localhost:8765") as session:
        await session.initialize()
        result = await session.call_tool("echo", {"test": "value"})
        assert result == {"test": "value"}

@pytest.mark.asyncio
async def test_math_operation(server):
    async with MCPClient.connect("ws://localhost:8765") as session:
        await session.initialize()
        result = await session.call_tool("add", {"a": 5, "b": 3})
        assert result == 8

@pytest.mark.asyncio
async def test_unknown_tool(server):
    async with MCPClient.connect("ws://localhost:8765") as session:
        await session.initialize()
        with pytest.raises(ValueError):
            await session.call_tool("unknown", {})