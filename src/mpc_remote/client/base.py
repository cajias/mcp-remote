"""Base client implementation for Model Context Protocol"""

import asyncio
import json
import logging
import uuid
from typing import Any, Dict, Optional

from ..core.constants import ToolType
from ..core.errors import MCPError
from ..version import PROTOCOL_VERSION, __version__
from .session import ClientCapabilities, MCPSession


class MCPClient:
    """
    Core client implementation for Model Context Protocol

    Provides a flexible interface for interacting with MCP servers
    """

    def __init__(
        self,
        server_endpoint: str,
        transport_class: Optional[type] = None,
        protocol_version: str = PROTOCOL_VERSION,
        logger: Optional[logging.Logger] = None,
    ) -> None:
        """
        Initialize MCP client

        :param server_endpoint: Connection endpoint for the server
        :param transport_class: Custom transport class (optional)
        :param protocol_version: Protocol version to use
        :param logger: Optional custom logger
        """
        # Logging setup
        self.logger = logger or logging.getLogger("mcp.client")

        # Server connection details
        self.server_endpoint = server_endpoint
        self.protocol_version = protocol_version

        # Transport mechanism
        self._transport = None
        if transport_class:
            self._transport = transport_class(server_endpoint)

        # Session and capabilities management
        self._session = MCPSession()
        self._capabilities: Optional[Dict[str, Any]] = None

        # Request tracking
        self._request_timeout = 30  # seconds

    @staticmethod
    def _generate_request_id() -> str:
        """
        Generate a unique request ID

        :return: Unique request identifier
        """
        return str(uuid.uuid4())

    async def _send_request(
        self, method: str, params: Optional[Dict[str, Any]] = None, is_notification: bool = False
    ) -> Any:
        """
        Send a JSON-RPC request to the server

        :param method: Request method
        :param params: Request parameters
        :param is_notification: Whether this is a notification request
        :return: Request response
        """
        # Prepare request payload
        request = {
            "jsonrpc": "2.0",
            "method": method,
        }

        # Add parameters if present
        if params:
            request["params"] = params

        # Add request ID if not a notification
        if not is_notification:
            request["id"] = self._generate_request_id()

        # Send request via transport
        if not self._transport:
            raise MCPError("No transport mechanism configured")

        try:
            response = await asyncio.wait_for(self._transport.send_request(request), timeout=self._request_timeout)

            # Handle JSON-RPC response
            if "error" in response:
                raise MCPError(response["error"].get("message", "Unknown error"), response["error"].get("code"))

            return response.get("result")

        except asyncio.TimeoutError as err:
            raise MCPError("Request timed out") from err
        except Exception as e:
            raise MCPError(f"Request failed: {e!s}") from e

    async def get_capabilities(self, force_refresh: bool = False) -> Dict[str, Any]:
        """
        Retrieve server capabilities

        :param force_refresh: Force fetching capabilities from server
        :return: Server capabilities
        """
        # Return cached capabilities if available and not forced
        if not force_refresh and self._capabilities:
            return self._capabilities

        # Initialize session if needed
        if not await self._session.initialize_version(__version__):
            raise MCPError("Version negotiation failed")

        # Setup client capabilities
        client_caps = ClientCapabilities(version=__version__, features=["basic", "streaming", "async"], extensions={})
        if not await self._session.negotiate_capabilities(client_caps):
            raise MCPError("Capability negotiation failed")

        # Fetch capabilities from server
        self._capabilities = await self._send_request("capabilities")
        return self._capabilities

    async def execute_tool(
        self, tool_name: str, params: Dict[str, Any], tool_type: ToolType = ToolType.FUNCTION
    ) -> Any:
        """
        Execute a tool on the server

        :param tool_name: Name of the tool to execute
        :param params: Tool parameters
        :param tool_type: Type of tool
        :return: Tool execution result
        """
        # Validate tool existence (optional, based on cached capabilities)
        if self._capabilities:
            available_tools = self._capabilities.get("tools", {})
            if tool_name not in available_tools:
                raise MCPError(f"Tool '{tool_name}' not available")

        # Execute tool based on its type
        if tool_type in [ToolType.FUNCTION, ToolType.RECURSIVE]:
            return await self._send_request(tool_name, params)
        elif tool_type == ToolType.GENERATOR:
            # For generators, multiple calls might be needed
            return await self._send_request(tool_name, params)
        elif tool_type == ToolType.STREAMING:
            # Placeholder for streaming tool implementation
            raise NotImplementedError("Streaming tools not yet supported")
        else:
            raise MCPError(f"Unsupported tool type: {tool_type}")

    async def send_notification(self, method: str, params: Optional[Dict[str, Any]] = None) -> None:
        """
        Send a notification to the server

        :param method: Notification method
        :param params: Notification parameters
        """
        await self._send_request(method, params, is_notification=True)


# Example usage
async def example_client_usage() -> None:
    """
    Demonstrate MCP client usage
    """
    # Assume a ZMQ transport is implemented
    from ..transport.zmq_transport import ZMQTransport

    # Create client
    client = MCPClient(server_endpoint="tcp://localhost:5555", transport_class=ZMQTransport)

    # Get server capabilities
    capabilities = await client.get_capabilities()
    print(json.dumps(capabilities, indent=2))

    # Execute a tool
    result = await client.execute_tool("add", {"a": 5, "b": 3})
    print("Tool execution result:", result)


# Main execution
if __name__ == "__main__":
    asyncio.run(example_client_usage())
