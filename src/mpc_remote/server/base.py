"""Base server implementation for Model Context Protocol"""

from typing import Dict, Any, Optional, Callable
import logging
from .resources import ResourceManager
from .tools import ToolManager
from ..core.protocol import ProtocolHandler
from ..core.errors import MCPError, ConsentError
from ..core.constants import ResourceAccessLevel

class MCPServer:
    """
    Core server implementation for Model Context Protocol
    
    Integrates resource and tool management with core protocol handling
    """
    def __init__(
        self, 
        name: Optional[str] = None,
        logger: Optional[logging.Logger] = None
    ):
        """
        Initialize MCP server
        
        :param name: Optional server name
        :param logger: Optional custom logger
        """
        # Logging setup
        self.logger = logger or logging.getLogger('mcp.server')
        
        # Server identification
        self.name = name or "GenericMCPServer"
        
        # Core protocol handler
        self.protocol_handler = ProtocolHandler()
        
        # Resource and tool management
        self.resources = ResourceManager()
        self.tools = ToolManager()
        
        # User consent and authentication callbacks
        self._consent_handler: Optional[Callable] = None
        self._authentication_handler: Optional[Callable] = None
    
    def set_consent_handler(self, handler: Callable):
        """
        Set a custom consent handler
        
        :param handler: Callable to handle user consent
        """
        self._consent_handler = handler
    
    def set_authentication_handler(self, handler: Callable):
        """
        Set a custom authentication handler
        
        :param handler: Callable to handle user authentication
        """
        self._authentication_handler = handler
    
    def _check_user_consent(
        self, 
        resource_or_tool_name: str, 
        is_tool: bool = False
    ) -> bool:
        """
        Check user consent for a resource or tool
        
        :param resource_or_tool_name: Name of resource or tool
        :param is_tool: Whether checking a tool or a resource
        :return: Whether consent is granted
        :raises ConsentError: If consent is not obtained
        """
        if not self._consent_handler:
            return True
        
        try:
            consent_granted = self._consent_handler(
                resource_or_tool_name=resource_or_tool_name,
                is_tool=is_tool
            )
            
            if not consent_granted:
                raise ConsentError(resource_or_tool_name)
            
            return True
        except Exception as e:
            self.logger.error(f"Consent check failed: {e}")
            raise
    
    def _authenticate_user(self, user_context: Optional[Dict[str, Any]] = None) -> bool:
        """
        Authenticate user based on provided context
        
        :param user_context: User authentication context
        :return: Whether authentication is successful
        """
        if not self._authentication_handler:
            return True
        
        try:
            return self._authentication_handler(user_context)
        except Exception as e:
            self.logger.error(f"Authentication failed: {e}")
            return False
    
    def register_resource(
        self, 
        name: str, 
        resource_type: str,
        access_level: ResourceAccessLevel = ResourceAccessLevel.READ_ONLY,
        description: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Register a new resource
        
        :param name: Unique resource name
        :param resource_type: Type of resource
        :param access_level: Access permissions for the resource
        :param description: Human-readable description
        :param metadata: Additional resource metadata
        """
        self.resources.register_resource(
            name=name,
            resource_type=resource_type,
            access_level=access_level,
            description=description,
            metadata=metadata
        )
        
        # Also register with protocol handler
        from ..core.protocol import Resource
        protocol_resource = Resource(
            name=name,
            type=resource_type,
            access_level=access_level,
            description=description,
            metadata=metadata or {}
        )
        self.protocol_handler.register_resource(protocol_resource)
    
    def register_tool(
        self,
        name: str,
        implementation: Callable,
        tool_type: ToolType = ToolType.FUNCTION,
        description: Optional[str] = None,
        params_schema: Optional[Dict[str, Any]] = None
    ):
        """
        Register a new tool
        
        :param name: Unique tool name
        :param implementation: Tool implementation function
        :param tool_type: Type of tool
        :param description: Human-readable description
        :param params_schema: JSON schema for parameter validation
        """
        self.tools.register_tool(
            name=name,
            implementation=implementation,
            tool_type=tool_type,
            description=description,
            params_schema=params_schema
        )
        
        # Also register with protocol handler
        from ..core.protocol import Tool
        protocol_tool = Tool(
            name=name,
            implementation=implementation,
            type=tool_type,
            description=description,
            params_schema=params_schema
        )
        self.protocol_handler.register_tool(protocol_tool)
    
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
        :raises MCPError: If execution fails
        """
        # Authenticate user
        if not self._authenticate_user(user_context):
            raise MCPError("Authentication failed")
        
        # Check consent
        self._check_user_consent(name, is_tool=True)
        
        # Execute tool
        return self.tools.execute_tool(name, params, user_context)
    
    def get_capabilities(self) -> Dict[str, Any]:
        """
        Retrieve server capabilities
        
        :return: Comprehensive server capabilities
        """
        return {
            "server_name": self.name,
            "protocol_version": self.protocol_handler._version,
            "resources": {
                name: resource.to_dict() 
                for name, resource in self.resources.list_resources().items()
            },
            "tools": {
                name: tool.to_dict() 
                for name, tool in self.tools.list_tools().items()
            }
        }
    
    def handle_request(
        self, 
        method: str, 
        params: Dict[str, Any],
        user_context: Optional[Dict[str, Any]] = None
    ) -> Any:
        """
        Handle a generic protocol request
        
        :param method: Request method
        :param params: Request parameters
        :param user_context: Optional user authentication context
        :return: Request execution result
        """
        # Special method handling
        if method == 'capabilities':
            return self.get_capabilities()
        
        # Tool execution
        return self.execute_tool(method, params, user_context)

# Example usage demonstrating server setup
def example_server_setup():
    """
    Example of setting up an MCP server with resources and tools
    """
    # Create server
    server = MCPServer(name="ExampleMCPServer")
    
    # Example resource
    server.register_resource(
        name="system_info",
        resource_type="metadata",
        description="Basic system information",
        access_level=ResourceAccessLevel.READ_ONLY
    )
    
    # Example tool: simple calculator
    def add(a: float, b: float) -> float:
        return a + b
    
    server.register_tool(
        name="add",
        implementation=add,
        description="Simple addition operation",
        tool_type=ToolType.FUNCTION
    )
    
    # Optional: Set custom consent handler
    def consent_handler(resource_or_tool_name: str, is_tool: bool) -> bool:
        # Example implementation
        print(f"Consent requested for: {resource_or_tool_name}")
        return True
    
    server.set_consent_handler(consent_handler)
    
    return server

# Main execution
if __name__ == "__main__":
    # Create and demonstrate server capabilities
    server = example_server_setup()
    print(json.dumps(server.get_capabilities(), indent=2))
