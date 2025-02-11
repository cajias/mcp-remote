from typing import Dict, Any, Optional, AsyncIterator
import asyncio
from dataclasses import dataclass
import logging

from mpc_remote.protocol.types import (
    MCPRequest,
    MCPResponse,
    InitializeRequest,
    InitializeResponse,
    ToolCallRequest,
    ToolCallResponse,
)
from mpc_remote.transport.base import Transport, TransportServer

logger = logging.getLogger(__name__)

@dataclass
class TestTool:
    name: str
    handler: callable

class MCPTestServer:
    def __init__(self):
        self.tools: Dict[str, TestTool] = {}
        self._transport: Optional[TransportServer] = None
    
    def register_tool(self, name: str, handler: callable):
        """Register a synchronous tool handler"""
        self.tools[name] = TestTool(name=name, handler=handler)
    
    async def handle_initialize(self, req: InitializeRequest) -> InitializeResponse:
        """Handle protocol initialization"""
        return InitializeResponse(
            tools=[tool.name for tool in self.tools.values()],
            version="1.0"
        )
    
    async def handle_tool_call(self, req: ToolCallRequest) -> ToolCallResponse:
        """Handle tool execution request"""
        tool = self.tools.get(req.tool)
        if not tool:
            raise ValueError(f"Unknown tool: {req.tool}")
            
        try:
            result = tool.handler(req.arguments)
            return ToolCallResponse(result=result)
        except Exception as e:
            logger.exception("Tool execution failed")
            return ToolCallResponse(error=str(e))
    
    async def handle_request(self, req: MCPRequest) -> MCPResponse:
        """Main request handler"""
        if isinstance(req, InitializeRequest):
            return await self.handle_initialize(req)
        elif isinstance(req, ToolCallRequest):
            return await self.handle_tool_call(req)
        else:
            raise ValueError(f"Unknown request type: {type(req)}")
    
    async def serve(self, transport: TransportServer):
        """Start serving requests on the given transport"""
        self._transport = transport
        
        async with transport:
            async for session in transport.accept():
                asyncio.create_task(self._handle_session(session))
    
    async def _handle_session(self, session: Transport):
        """Handle a single client session"""
        try:
            async with session:
                async for request in session.receive():
                    response = await self.handle_request(request)
                    await session.send(response)
        except Exception:
            logger.exception("Session handling failed")

# Example usage:
if __name__ == "__main__":
    import uvicorn
    from mpc_remote.transport.websocket import WebSocketServer
    
    # Create and configure server
    server = MCPTestServer()
    
    # Register a simple echo tool
    server.register_tool("echo", lambda args: args)
    
    # Create WebSocket transport
    transport = WebSocketServer("localhost", 8765)
    
    # Start server
    uvicorn.run(transport.app, host="localhost", port=8765)