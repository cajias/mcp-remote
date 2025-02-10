"""Core protocol implementation for Model Context Protocol"""

import asyncio
from dataclasses import asdict, dataclass, field
from typing import Any, Callable, Dict, Optional

from .constants import ResourceAccessLevel, ToolType
from .errors import MCPError


@dataclass
class Resource:
    """
    Represents a resource in the Model Context Protocol

    Resources are entities that can be accessed and manipulated through the protocol.
    Each resource has a defined access level and can optionally require consent
    for operations.
    """
    name: str
    type: str
    description: Optional[str] = None
    access_level: ResourceAccessLevel = ResourceAccessLevel.READ_ONLY
    version: Optional[str] = None
    consent_required: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert resource to dictionary representation"""
        resource_dict = asdict(self)
        resource_dict['access_level'] = self.access_level.value
        return resource_dict

@dataclass
class Tool:
    """
    Represents a tool in the Model Context Protocol

    Tools are executable components that can process data or perform operations.
    Each tool defines how it should be executed and what parameters it accepts.
    The implementation can be either synchronous or asynchronous.
    """
    name: str
    implementation: Callable
    description: Optional[str] = None
    type: ToolType = ToolType.FUNCTION
    params_schema: Optional[Dict[str, Any]] = None
    consent_required: bool = False
    version: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert tool to dictionary representation, excluding the implementation"""
        return {
            'name': self.name,
            'description': self.description,
            'type': self.type.name,
            'params_schema': self.params_schema,
            'consent_required': self.consent_required,
            'version': self.version
        }

class ProtocolHandler:
    """
    Core handler for Model Context Protocol communications

    This class manages protocol-level interactions by:
    - Maintaining registries of available resources and tools
    - Handling tool execution with proper error management
    - Providing capability discovery
    - Ensuring version compatibility
    """
    def __init__(self, version: str = "1.0") -> None:
        """
        Initialize protocol handler

        Args:
            version: Protocol version to use, defaults to "1.0"
        """
        self._version = version
        self._resources: Dict[str, Resource] = {}
        self._tools: Dict[str, Tool] = {}

    def register_resource(self, resource: Resource) -> None:
        """
        Register a resource in the protocol

        Args:
            resource: Resource to register
        """
        self._resources[resource.name] = resource

    def register_tool(self, tool: Tool) -> None:
        """
        Register a tool in the protocol

        Args:
            tool: Tool to register
        """
        self._tools[tool.name] = tool

    def get_capabilities(self) -> Dict[str, Any]:
        """
        Retrieve current protocol capabilities

        Returns:
            Dictionary containing:
            - protocol_version: Current protocol version
            - resources: Dictionary of registered resources
            - tools: Dictionary of available tools
        """
        return {
            "protocol_version": self._version,
            "resources": {
                name: resource.to_dict()
                for name, resource in self._resources.items()
            },
            "tools": {
                name: tool.to_dict()
                for name, tool in self._tools.items()
            }
        }

    async def execute_tool(self, tool_name: str, params: Dict[str, Any]) -> Any:
        """
        Execute a registered tool

        This method handles both synchronous and asynchronous tool implementations,
        automatically detecting the appropriate execution mode.

        Args:
            tool_name: Name of the tool to execute
            params: Parameters to pass to the tool

        Returns:
            Tool execution result

        Raises:
            MCPError: If tool is not found or execution fails
        """
        if tool_name not in self._tools:
            raise MCPError(f"Tool '{tool_name}' not found")

        tool = self._tools[tool_name]

        try:
            # Handle both async and sync implementations
            if asyncio.iscoroutinefunction(tool.implementation):
                return await tool.implementation(**params)
            return tool.implementation(**params)

        except Exception as e:
            raise MCPError(
                f"Tool execution failed: {e!s}",
                details={"tool": tool_name, "params": params}
            ) from e
