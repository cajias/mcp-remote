from __future__ import annotations

import asyncio

from mpc_remote.server.base import MCPServer
from mpc_remote.transport.zmq_transport import ZMQTransport


class MCPServerRunner:
    """
    A simple server runner that integrates the MCPServer and the transport.
    It listens on the given endpoint until killed.
    """

    def __init__(self, server: MCPServer, endpoint: str) -> None:
        self.server = server
        self.endpoint = endpoint
        # Create a ZeroMQ transport that binds (listens) to the endpoint.
        self.transport = ZMQTransport(endpoint=self.endpoint, connection_type="bind")
        self._task: asyncio.Task | None = None

    async def _request_handler(self, request: dict) -> dict:
        """
        Delegates the request to the server's protocol handler.
        Expects the JSON-RPC request to include a "method" and optionally "params" and "id".
        """
        method = request.get("method")
        params = request.get("params", {})
        request_id = request.get("id")
        try:
            # Execute the tool registered under the method name.
            result = await self.server.protocol_handler.execute_tool(method, params)
            return {"jsonrpc": "2.0", "result": result, "id": request_id}
        except Exception as e:
            # Return a JSON-RPC error response in case of failure.
            return {
                "jsonrpc": "2.0",
                "error": {"code": -32000, "message": str(e), "data": {"type": type(e).__name__}},
                "id": request_id,
            }

    async def _run(self) -> None:
        """
        Run the server: handle incoming requests indefinitely.
        """
        print(f"Server listening on {self.endpoint}...")
        await self.transport.handle_request(self._request_handler)

    def start(self) -> asyncio.Task:
        """Starts the server in the background and returns the asyncio.Task that runs it."""
        self._task = asyncio.create_task(self._run())
        return self._task

    async def stop(self) -> None:
        """Stops the server by cancelling the running task."""
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                print("Server stopped.")

    async def __aenter__(self) -> object:
        """Start the server automatically when used in an `async with` block."""
        self.start()
        return self

    async def __aexit__(self, exc_type: object, exc_value: object, traceback: object) -> None:
        """Stop the server when exiting an `async with` block."""
        await self.stop()


# Example usage:
async def _main() -> None:
    # Initialize the MCP server.
    server = MCPServer(name="MyMCPServer")

    @server.tool("ping")
    async def ping() -> str:
        """A simple ping tool that responds with 'pong'."""
        return "pong"

    # Use the server in an `async with` block.
    async with MCPServerRunner(server, "tcp://*:5555"):
        await asyncio.sleep(100)  # Keep the server running.


# Run the server.
if __name__ == "__main__":
    asyncio.run(_main())
