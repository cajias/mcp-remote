"""ZeroMQ transport implementation for Model Context Protocol"""

from __future__ import annotations

import asyncio
import json
from typing import Any, Callable

import zmq
import zmq.asyncio

from ..core.errors import MCPError


class ZMQTransportError(MCPError):
    """Transport-specific errors"""

    pass


class ZMQTransport:
    """ZeroMQ transport for Model Context Protocol communications"""

    def __init__(
        self, endpoint: str, connection_type: str = "connect", context: zmq.Context | None = None, timeout: float = 5.0
    ) -> None:
        """Initialize ZMQ transport

        Args:
            endpoint: ZMQ endpoint string (e.g., tcp://localhost:5555)
            connection_type: Either 'connect' or 'bind'
            context: Optional ZMQ context to use
            timeout: Request timeout in seconds
        """
        self.context = context or zmq.asyncio.Context()
        conn_type = zmq.REQ if connection_type == "connect" else zmq.REP
        self.socket = self.context.socket(conn_type)

        # Configure socket
        self.socket.setsockopt(zmq.LINGER, 100)  # Reduced linger
        self.socket.setsockopt(zmq.RCVTIMEO, int(timeout * 1000))
        self.socket.setsockopt(zmq.SNDTIMEO, int(timeout * 1000))

        # Special handling for inproc transport
        if endpoint.startswith("inproc://"):
            self.socket.setsockopt(zmq.SNDHWM, 10000)
            self.socket.setsockopt(zmq.RCVHWM, 10000)
            self.socket.setsockopt(zmq.IMMEDIATE, 1)
        else:
            self.socket.setsockopt(zmq.SNDHWM, 1000)
            self.socket.setsockopt(zmq.RCVHWM, 1000)

        # Increase TCP keep-alive for better connection stability
        self.socket.setsockopt(zmq.TCP_KEEPALIVE, 1)
        self.socket.setsockopt(zmq.TCP_KEEPALIVE_IDLE, 60)
        self.socket.setsockopt(zmq.TCP_KEEPALIVE_INTVL, 30)

        if connection_type == "connect":
            self.socket.connect(endpoint)
        elif connection_type == "bind":
            self.socket.bind(endpoint)
        else:
            raise ValueError("Connection type must be 'connect' or 'bind'")

        self.endpoint = endpoint
        self._closed = False
        self._timeout = timeout

    async def recv_json(self) -> dict[str, Any]:
        """Receive and parse JSON data"""
        try:
            data = await self.socket.recv()
            return json.loads(data.decode("utf-8"))
        except zmq.error.Again as err:
            raise ZMQTransportError("Receive operation timed out") from err

    async def send_json(self, data: dict[str, Any]) -> None:
        """Encode and send JSON data"""
        try:
            message = json.dumps(data).encode("utf-8")
            await self.socket.send(message)
        except zmq.error.Again as err:
            raise ZMQTransportError("Send operation timed out") from err

    async def _send_and_receive(self, request: dict[str, Any]) -> dict[str, Any]:
        """Helper method for sending request and receiving response"""
        await self.send_json(request)
        return await self.recv_json()

    async def send_request(self, request: dict[str, Any], timeout: float | None = None) -> dict[str, Any]:
        """Send a JSON-RPC request via ZeroMQ"""
        if self._closed:
            raise ZMQTransportError("Transport is closed")

        timeout = timeout or self._timeout

        try:
            return await asyncio.wait_for(self._send_and_receive(request), timeout=timeout)

        except asyncio.TimeoutError as err:
            raise ZMQTransportError(
                f"Request timed out after {timeout} seconds", details={"endpoint": self.endpoint}
            ) from err

        except zmq.ZMQError as err:
            raise ZMQTransportError(f"ZMQ error: {err!s}", details={"errno": err.errno}) from err

        except json.JSONDecodeError as err:
            raise ZMQTransportError("Invalid JSON response", details={"error": str(err)}) from err

    async def handle_request(self, handler: Callable) -> None:
        """Handle incoming requests (server mode)"""
        if self._closed:
            raise ZMQTransportError("Transport is closed")

        while True:
            try:
                # Receive and process request
                request = await self.recv_json()
                response = await handler(request)
                await self.send_json(response)

            except Exception as err:
                # Send error response
                error_response = {
                    "jsonrpc": "2.0",
                    "error": {"code": -32000, "message": str(err), "data": {"type": type(err).__name__}},
                    "id": request.get("id") if isinstance(request, dict) else None,
                }
                await self.send_json(error_response)

    def close(self) -> None:
        """Close the transport"""
        if not self._closed:
            try:
                if hasattr(self, "socket"):
                    self.socket.close(linger=0)  # Immediate close
            finally:
                self._closed = True

    def __del__(self) -> None:
        """Ensure resources are cleaned up"""
        self.close()
