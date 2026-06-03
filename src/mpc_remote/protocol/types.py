"""
Model Context Protocol types, mirroring the canonical SDK.
"""
from typing import Any, Dict, Optional, Union

from pydantic import AnyUrl, BaseModel


class RootsCapability(BaseModel):
    """Capability for receiving roots/list_changed notifications"""
    listChanged: bool = True

class ClientCapabilities(BaseModel):
    """Client capabilities definition"""
    sampling: Optional[Dict[str, Any]] = None
    experimental: Optional[Dict[str, Any]] = None
    roots: RootsCapability = RootsCapability()

class ClientInfo(BaseModel):
    """Client implementation information"""
    name: str
    version: str

class TransportCapability(BaseModel):
    """Transport-specific capabilities"""
    zmq: bool = False
    websocket: bool = False
    stdio: bool = True  # Default like canonical SDK

class ExtendedCapabilities(ClientCapabilities):
    """Extended capabilities that preserve core protocol compatibility"""
    transport: Optional[TransportCapability] = None

# Request/Response Types
class InitializeRequestParams(BaseModel):
    """Initialize request parameters"""
    protocolVersion: str
    capabilities: ClientCapabilities
    clientInfo: ClientInfo

class InitializeRequest(BaseModel):
    """Initialize request"""
    method: str = "initialize"
    params: InitializeRequestParams

class InitializeResult(BaseModel):
    """Initialize response"""
    protocolVersion: str
    capabilities: ClientCapabilities

class EmptyParams(BaseModel):
    """Empty parameters for requests that don't need them"""
    pass

class EmptyResult(BaseModel):
    """Empty result for responses that don't need them"""
    pass

class ProgressNotificationParams(BaseModel):
    """Progress notification parameters"""
    progressToken: Union[str, int]
    progress: float
    total: Optional[float] = None

class ProgressNotification(BaseModel):
    """Progress notification"""
    method: str = "notifications/progress"
    params: ProgressNotificationParams

class ResourceReference(BaseModel):
    """Reference to a resource"""
    uri: AnyUrl

class PromptReference(BaseModel):
    """Reference to a prompt"""
    name: str
    arguments: Optional[Dict[str, str]] = None

class CompletionArgument(BaseModel):
    """Completion request argument"""
    prompt: str
    metadata: Optional[Dict[str, Any]] = None

class CompleteRequestParams(BaseModel):
    """Completion request parameters"""
    ref: Union[ResourceReference, PromptReference]
    argument: CompletionArgument

class CompleteRequest(BaseModel):
    """Completion request"""
    method: str = "completion/complete"
    params: CompleteRequestParams

class CompleteResult(BaseModel):
    """Completion response"""
    completion: str
    metadata: Optional[Dict[str, Any]] = None

class CallToolRequestParams(BaseModel):
    """Tool call request parameters"""
    name: str
    arguments: Dict[str, Any]

class CallToolRequest(BaseModel):
    """Tool call request"""
    method: str = "tools/call"
    params: CallToolRequestParams

class CallToolResult(BaseModel):
    """Tool call response"""
    result: Any

# Combine all possible request/response types
class ClientRequest(BaseModel):
    """Union of all possible client requests"""
    initialize: Optional[InitializeRequest] = None
    complete: Optional[CompleteRequest] = None
    call_tool: Optional[CallToolRequest] = None
    # Add other request types as needed

class ServerRequest(BaseModel):
    """Union of all possible server requests"""
    pass  # Add server-specific requests if needed

class ClientResult(BaseModel):
    """Union of all possible client results"""
    initialize: Optional[InitializeResult] = None
    complete: Optional[CompleteResult] = None
    call_tool: Optional[CallToolResult] = None
    empty: Optional[EmptyResult] = None