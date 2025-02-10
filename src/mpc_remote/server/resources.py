"""Resource management for MCP server"""

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, Optional

from ..core.constants import ResourceAccessLevel


class ResourceManager:
    """
    Manages resources for a Model Context Protocol server

    Handles resource registration, access control, and metadata management
    """
    def __init__(self)->None:
        """Initialize resource manager"""
        self._resources: Dict[str, Resource] = {}
        self._access_hooks: Dict[str, Callable] = {}

    def register_resource(
        self,
        name: str,
        resource_type: str,
        access_level: ResourceAccessLevel = ResourceAccessLevel.READ_ONLY,
        description: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        access_hook: Optional[Callable] = None
    )->None:
        """
        Register a new resource

        :param name: Unique resource name
        :param resource_type: Type of resource
        :param access_level: Access permissions for the resource
        :param description: Human-readable description
        :param metadata: Additional resource metadata
        :param access_hook: Optional callable to validate access
        """
        if name in self._resources:
            raise ValueError(f"Resource '{name}' already exists")

        resource = Resource(
            name=name,
            type=resource_type,
            access_level=access_level,
            description=description,
            metadata=metadata or {}
        )

        self._resources[name] = resource

        if access_hook:
            self._access_hooks[name] = access_hook

    def get_resource(self, name: str) -> 'Resource':
        """
        Retrieve a registered resource

        :param name: Name of the resource
        :return: Resource object
        :raises KeyError: If resource not found
        """
        return self._resources[name]

    def list_resources(self) -> Dict[str, 'Resource']:
        """
        List all registered resources

        :return: Dictionary of resources
        """
        return dict(self._resources)

    def check_resource_access(
        self,
        name: str,
        access_level: ResourceAccessLevel,
        user_context: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Check if access to a resource is permitted

        :param name: Resource name
        :param access_level: Requested access level
        :param user_context: Optional user authentication context
        :return: Whether access is granted
        """
        if name not in self._resources:
            return False

        resource = self._resources[name]

        # Check resource access level
        if access_level.value > resource.access_level.value:
            return False

        # Check custom access hook if defined
        if name in self._access_hooks:
            return self._access_hooks[name](
                resource=resource,
                access_level=access_level,
                user_context=user_context
            )

        return True

@dataclass
class Resource:
    """
    Represents a resource in the Model Context Protocol

    Encapsulates resource metadata and access control information
    """
    name: str
    type: str
    access_level: ResourceAccessLevel = ResourceAccessLevel.READ_ONLY
    description: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert resource to dictionary representation

        :return: Dictionary with resource details
        """
        return {
            'name': self.name,
            'type': self.type,
            'access_level': self.access_level.value,
            'description': self.description,
            'metadata': self.metadata
        }
