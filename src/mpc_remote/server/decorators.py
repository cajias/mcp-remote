"""Decorator-based server implementation for Model Context Protocol"""

import functools
from typing import Any, Callable, Dict, Optional, Protocol, Type, TypeVar

from typing_extensions import ParamSpec

from ..core.constants import ResourceAccessLevel, ToolType
from ..core.protocol import Resource, Tool

P = ParamSpec('P')
R = TypeVar('R')
T = TypeVar('T')

class BaseTool(Protocol[P, R]):
    """Protocol for tool implementations"""
    def __call__(self, *args: P.args, **kwargs: P.kwargs) -> R: ...

class BaseResource(Protocol):
    """Protocol for resource implementations"""
    pass

def tool(
    name: Optional[str] = None,
    description: Optional[str] = None,
    tool_type: ToolType = ToolType.FUNCTION,
    params_schema: Optional[Dict[str, Any]] = None,
    consent_required: bool = False
) -> Callable[[Callable[P, R]], Callable[P, R]]:
    """
    Decorator to register a function as an MCP tool
    
    @server.tool("add")
    async def add(a: int, b: int) -> int:
        return a + b
    """
    def decorator(func: Callable[P, R]) -> Callable[P, R]:
        @functools.wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            return func(*args, **kwargs)
        
        # Store MCP metadata on the function
        wrapper._mcp_tool = Tool(
            name=name or func.__name__,
            implementation=func,
            description=description or func.__doc__,
            type=tool_type,
            params_schema=params_schema,
            consent_required=consent_required
        )
        return wrapper
    return decorator

def resource(
    name: Optional[str] = None,
    resource_type: Optional[str] = None,
    description: Optional[str] = None,
    access_level: ResourceAccessLevel = ResourceAccessLevel.READ_ONLY,
    consent_required: bool = False,
    metadata: Optional[Dict[str, Any]] = None
) -> Callable[[Type[T]], Type[T]]:
    """
    Decorator to register a class as an MCP resource
    
    @server.resource("user_data")
    class UserData:
        def __init__(self):
            self.data = {}
    """
    def decorator(cls: Type[T]) -> Type[T]:
        # Store MCP metadata on the class
        cls._mcp_resource = Resource(
            name=name or cls.__name__,
            type=resource_type or cls.__name__.lower(),
            description=description or cls.__doc__,
            access_level=access_level,
            consent_required=consent_required,
            metadata=metadata or {}
        )
        return cls
    return decorator
