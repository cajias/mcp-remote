"""Tool management for MCP server"""

from typing import Dict, Any, Optional, Callable, Type
from dataclasses import dataclass, field
import inspect
import json
import asyncio
from ..core.constants import ToolType
from ..core.errors import MCPError

class ToolManager:
    """
    Manages tools for a Model Context Protocol server
    
    Handles tool registration, validation, and execution
    """
    def __init__(self):
        """Initialize tool manager"""
        self._tools: Dict[str, 'Tool'] = {}
        self._tool_validators: Dict[str, Callable] = {}
    
    def register_tool(
        self,
        name: str,
        implementation: Callable,
        tool_type: ToolType = ToolType.FUNCTION,
        description: Optional[str] = None,
        params_schema: Optional[Dict[str, Any]] = None,
        validator: Optional[Callable] = None
    ):
        """
        Register a new tool
        
        :param name: Unique tool name
        :param implementation: Tool implementation function
        :param tool_type: Type of tool
        :param description: Human-readable description
        :param params_schema: JSON schema for parameter validation
        :param validator: Optional custom validator function
        """
        if name in self._tools:
            raise ValueError(f"Tool '{name}' already exists")
        
        # Automatically generate params schema if not provided
        if params_schema is None:
            params_schema = self._generate_params_schema(implementation)
        
        tool = Tool(
            name=name,
            implementation=implementation,
            type=tool_type,
            description=description,
            params_schema=params_schema
        )
        
        self._tools[name] = tool
        
        if validator:
            self._tool_validators[name] = validator
    
    def _generate_params_schema(self, func: Callable) -> Dict[str, Any]:
        """
        Generate JSON schema from function signature
        
        :param func: Function to inspect
        :return: JSON schema for function parameters
        """
        sig = inspect.signature(func)
        schema = {"type": "object", "properties": {}, "required": []}
        
        for name, param in sig.parameters.items():
            # Determine parameter type
            if param.annotation == inspect.Parameter.empty:
                param_type = "object"  # default
            elif param.annotation == str:
                param_type = "string"
            elif param.annotation in (int, float):
                param_type = "number"
            elif param.annotation == bool:
                param_type = "boolean"
            elif param.annotation == list:
                param_type = "array"
            elif param.annotation == dict:
                param_type = "object"
            else:
                param_type = "object"
            
            # Add to schema
            schema["properties"][name] = {"type": param_type}
            
            # Check if parameter is required
            if param.default == inspect.Parameter.empty:
                schema["required"].append(name)
        
        return schema
    
    def get_tool(self, name: str) -> 'Tool':
        """
        Retrieve a registered tool
        
        :param name: Name of the tool
        :return: Tool object
        :raises KeyError: If tool not found
        """
        return self._tools[name]
    
    def list_tools(self) -> Dict[str, 'Tool']:
        """
        List all registered tools
        
        :return: Dictionary of tools
        """
        return dict(self._tools)
    
    def execute_tool(
        self, 
        name: str, 
        params: Dict[str, Any],
        user_context: Optional[Dict[str, Any]] = None
    ) -> Any:
        """
        Execute a registered tool
        
        :param name: Tool name to execute
        :param params: Tool parameters
        :param user_context: Optional user authentication context
        :return: Tool execution result
        :raises MCPError: If tool execution fails
        """
        if name not in self._tools:
            raise MCPError(f"Tool '{name}' not found")
        
        tool = self._tools[name]
        
        # Validate parameters against schema
        self._validate_params(tool, params)
        
        # Run custom validator if defined
        if name in self._tool_validators:
            validation_result = self._tool_validators[name](
                tool=tool, 
                params=params, 
                user_context=user_context
            )
            if not validation_result:
                raise MCPError(f"Tool '{name}' validation failed")
        
        # Execute tool based on its type
        try:
            if tool.type == ToolType.FUNCTION:
                return tool.implementation(**params)
            elif tool.type == ToolType.GENERATOR:
                return list(tool.implementation(**params))
            elif tool.type == ToolType.STREAMING:
                # For streaming tools, return an iterator
                return tool.implementation(**params)
            elif tool.type == ToolType.RECURSIVE:
                # For recursive tools, support async execution
                if asyncio.iscoroutinefunction(tool.implementation):
                    return asyncio.run(tool.implementation(**params))
                return tool.implementation(**params)
            else:
                raise MCPError(f"Unsupported tool type: {tool.type}")
        except Exception as e:
            raise MCPError(f"Tool execution failed: {str(e)}")
    
    def _validate_params(self, tool: 'Tool', params: Dict[str, Any]):
        """
        Validate parameters against tool's JSON schema
        
        :param tool: Tool object
        :param params: Parameters to validate
        :raises MCPError: If validation fails
        """
        if not tool.params_schema:
            return
        
        try:
            # Basic JSON schema validation
            from jsonschema import validate
            validate(instance=params, schema=tool.params_schema)
        except Exception as e:
            raise MCPError(f"Parameter validation failed: {str(e)}")

@dataclass
class Tool:
    """
    Represents a tool in the Model Context Protocol
    
    Encapsulates tool metadata and implementation details
    """
    name: str
    implementation: Callable
    type: ToolType = ToolType.FUNCTION
    description: Optional[str] = None
    params_schema: Optional[Dict[str, Any]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert tool to dictionary representation
        
        :return: Dictionary with tool details
        """
        return {
            'name': self.name,
            'type': self.type.name,
            'description': self.description,
            'params_schema': self.params_schema,
            'metadata': self.metadata
        }
