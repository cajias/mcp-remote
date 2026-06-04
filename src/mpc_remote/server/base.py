"""Base server implementation for Model Context Protocol"""

import asyncio
import logging
from typing import Any, Callable, Dict, Optional, Type, TypeVar, get_type_hints

from ..core.constants import ResourceAccessLevel, ToolType
from ..core.errors import ConsentError, MCPError
from ..core.protocol import ProtocolHandler, Resource, Tool

T = TypeVar("T")


class MCPServer:
    """Core server implementation using decorators for registration"""

    def __init__(
        self, name: Optional[str] = None, logger: Optional[logging.Logger] = None, version: str = "1.0"
    ) -> None:
        self.name = name or "GenericMCPServer"
        self.logger = logger or logging.getLogger("mcp.server")
        self.protocol_handler = ProtocolHandler(version=version)
        self._consent_handler: Optional[Callable] = None
        self._auth_handler: Optional[Callable] = None
        self._tools: Dict[str, Tool] = {}
        self._resources: Dict[str, Resource] = {}

    def tool(
        self,
        name: Optional[str] = None,
        description: Optional[str] = None,
        tool_type: ToolType = ToolType.FUNCTION,
        params_schema: Optional[Dict[str, Any]] = None,
        consent_required: bool = False,
    ) -> Callable[[T], T]:
        """
        Register a function as an MCP tool

        @server.tool("add")
        async def add(a: int, b: int) -> int:
            return a + b
        """

        def decorator(func: T) -> T:
            tool_name = name or func.__name__
            tool = Tool(
                name=tool_name,
                implementation=func,
                description=description or func.__doc__,
                type=tool_type,
                params_schema=params_schema or self._infer_params_schema(func),
                consent_required=consent_required,
            )
            self._tools[tool_name] = tool
            self.protocol_handler.register_tool(tool)
            return func

        return decorator

    def resource(
        self,
        name: Optional[str] = None,
        resource_type: Optional[str] = None,
        description: Optional[str] = None,
        access_level: ResourceAccessLevel = ResourceAccessLevel.READ_ONLY,
        consent_required: bool = False,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Callable[[Type[T]], Type[T]]:
        """
        Register a class as an MCP resource

        @server.resource("user_data")
        class UserData:
            def __init__(self):
                self.data = {}
        """

        def decorator(cls: Type[T]) -> Type[T]:
            resource_name = name or cls.__name__
            resource = Resource(
                name=resource_name,
                type=resource_type or cls.__name__.lower(),
                description=description or cls.__doc__,
                access_level=access_level,
                consent_required=consent_required,
                metadata=metadata or {},
            )
            self._resources[resource_name] = resource
            self.protocol_handler.register_resource(resource)
            return cls

        return decorator

    def _infer_params_schema(self, func: Callable) -> Dict[str, Any]:
        """Infer JSON schema from function type hints"""
        hints = get_type_hints(func)
        return {
            "type": "object",
            "properties": {
                name: {"type": self._type_to_json_type(typ)} for name, typ in hints.items() if name != "return"
            },
            "required": [name for name, _ in hints.items() if name != "return"],
        }

    def _type_to_json_type(self, typ: Type) -> str:
        """Convert Python type to JSON schema type"""
        type_map = {int: "integer", float: "number", str: "string", bool: "boolean", list: "array", dict: "object"}
        return type_map.get(typ, "string")

    def set_consent_handler(self, handler: Callable) -> None:
        """Set custom consent handler"""
        self._consent_handler = handler

    def set_auth_handler(self, handler: Callable) -> None:
        """Set custom authentication handler"""
        self._auth_handler = handler

    async def execute_tool(self, name: str, params: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> Any:
        """Execute a registered tool"""
        if self._auth_handler and not await self._auth_handler(context):
            raise MCPError("Authentication failed")

        tool = self._tools.get(name)
        if not tool:
            raise MCPError(f"Tool '{name}' not found")

        if tool.consent_required and self._consent_handler:
            if not await self._consent_handler(name, context):
                raise ConsentError(f"Consent denied for tool '{name}'")

        # Handle both sync and async implementations
        try:
            if asyncio.iscoroutinefunction(tool.implementation):
                return await tool.implementation(**params)
            return tool.implementation(**params)
        except Exception as e:
            raise MCPError(f"Tool execution failed: {e!s}") from e

    def get_capabilities(self) -> Dict[str, Any]:
        """Get server capabilities"""
        return {
            "server_name": self.name,
            "protocol_version": self.protocol_handler._version,
            "resources": {name: resource.to_dict() for name, resource in self._resources.items()},
            "tools": {name: tool.to_dict() for name, tool in self._tools.items()},
        }
