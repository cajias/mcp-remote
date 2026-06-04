"""Constants for Model Context Protocol"""

from enum import Enum, auto


class ResourceAccessLevel(Enum):
    """
    Defines access levels for resources

    These levels determine what operations are allowed on a resource:
    - READ_ONLY: Only allows reading the resource
    - READ_WRITE: Allows both reading and modifying
    - EXECUTE: Allows execution (for executable resources)
    - ADMIN: Full access including configuration
    """

    READ_ONLY = "read-only"
    READ_WRITE = "read-write"
    EXECUTE = "execute"
    ADMIN = "admin"


class ToolType(Enum):
    """
    Defines types of tools in the protocol

    Different tool types support different execution patterns:
    - FUNCTION: Simple request-response
    - GENERATOR: Yields multiple results
    - STREAMING: Continuous data stream
    - RECURSIVE: Can call other tools
    """

    FUNCTION = auto()
    GENERATOR = auto()
    STREAMING = auto()
    RECURSIVE = auto()


# Default timeouts and limits
DEFAULT_REQUEST_TIMEOUT = 30  # seconds
MAX_TOOL_EXECUTION_TIME = 300  # 5 minutes
MAX_PAYLOAD_SIZE = 10 * 1024 * 1024  # 10 MB
