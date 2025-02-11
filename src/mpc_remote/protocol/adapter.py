"""Backward compatibility adapters for MCP protocol"""

from typing import Any, Dict, Optional, Tuple
from pydantic import BaseModel
from ..version import __version__

class RootsCapability(BaseModel):
    """Original MCP roots capability"""
    listChanged: bool = True

class LegacyCapabilities(BaseModel):
    """Original MCP client capabilities structure"""
    sampling: Optional[Dict[str, Any]] = None
    experimental: Optional[Dict[str, Any]] = None
    roots: RootsCapability = RootsCapability()

class InitializeParams(BaseModel):
    """Original MCP initialize request parameters"""
    protocolVersion: str
    capabilities: LegacyCapabilities
    clientInfo: Dict[str, str]

class ProtocolAdapter:
    """Adapts between old and new protocol versions"""
    
    def __init__(self):
        self.legacy_mode = False
        self.auth_enabled = False

    def adapt_initialize_request(
        self, 
        params: InitializeParams
    ) -> Tuple[str, Dict[str, Any]]:
        """
        Adapt initialize request from old format to new
        Returns (version, capabilities)
        """
        self.legacy_mode = True
        
        # Convert capabilities ensuring roots capability is preserved
        new_capabilities = {
            "version": params.protocolVersion,
            "features": ["basic", "streaming"],
            "extensions": {
                "roots": {
                    "listChanged": True  # This is required by original SDK
                }
            }
        }

        # Add legacy capabilities if present
        if params.capabilities:
            if params.capabilities.sampling:
                new_capabilities["extensions"]["sampling"] = params.capabilities.sampling
            if params.capabilities.experimental:
                new_capabilities["extensions"]["experimental"] = params.capabilities.experimental
            
            # Preserve the exact roots capability from original request
            if params.capabilities.roots:
                new_capabilities["extensions"]["roots"]["listChanged"] = params.capabilities.roots.listChanged

        # Add auth capability in compatible way
        if self.auth_enabled:
            new_capabilities["extensions"]["auth"] = {
                "type": "none",  # Don't require auth for legacy clients
                "version": "1.0"
            }

        return params.protocolVersion, new_capabilities

    def adapt_initialize_response(
        self,
        protocol_version: str,
        capabilities: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Adapt initialize response from new format to old
        """
        legacy_response = {
            "protocolVersion": protocol_version,
            "capabilities": {
                "streaming": True,
                "progress": True
            }
        }

        # Must include roots capability in response for original SDK
        legacy_response["capabilities"]["roots"] = {
            "listChanged": True
        }

        # Convert new capabilities to legacy format
        if "extensions" in capabilities:
            if "sampling" in capabilities["extensions"]:
                legacy_response["capabilities"]["sampling"] = capabilities["extensions"]["sampling"]
            if "experimental" in capabilities["extensions"]:
                legacy_response["capabilities"]["experimental"] = capabilities["extensions"]["experimental"]
            if "roots" in capabilities["extensions"]:
                legacy_response["capabilities"]["roots"] = capabilities["extensions"]["roots"]

        return legacy_response

    def adapt_request(self, method: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Adapt request from old format to new
        """
        if not self.legacy_mode:
            return params

        # Handle legacy request formats
        if method == "tools/call":
            return self._adapt_tool_call(params)
        elif method == "completion/complete":
            return self._adapt_completion(params)
        
        return params

    def adapt_response(self, method: str, response: Dict[str, Any]) -> Dict[str, Any]:
        """
        Adapt response from new format to old
        """
        if not self.legacy_mode:
            return response

        # Handle legacy response formats
        if method == "tools/list":
            return self._adapt_tools_list_response(response)
        elif method == "resources/list":
            return self._adapt_resources_list_response(response)
        
        return response

    def _adapt_tool_call(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Adapt tool call request params"""
        # Original SDK expects arguments as dict
        if "arguments" not in params or not isinstance(params["arguments"], dict):
            params = {
                "name": params.get("name", ""),
                "arguments": {
                    "args": params.get("arguments", [])
                }
            }
        
        return params

    def _adapt_completion(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Adapt completion request params"""
        if "argument" not in params:
            return params
            
        # Convert new argument format to old
        arg = params["argument"]
        if isinstance(arg, dict) and "prompt" in arg:
            params["argument"] = arg["prompt"]
            
        return params

    def _adapt_tools_list_response(self, response: Dict[str, Any]) -> Dict[str, Any]:
        """Adapt tools list response"""
        if "tools" not in response:
            return response
            
        # Add legacy fields exactly as original SDK expects
        for tool in response["tools"]:
            if "schema" not in tool:
                tool["schema"] = {"type": "object", "properties": {}}
            if "required" not in tool:
                tool["required"] = []
                
        return response

    def _adapt_resources_list_response(self, response: Dict[str, Any]) -> Dict[str, Any]:
        """Adapt resources list response"""
        if "resources" not in response:
            return response
            
        # Add legacy fields exactly as original SDK expects
        for resource in response["resources"]:
            if "type" not in resource:
                resource["type"] = "text"
            if "metadata" not in resource:
                resource["metadata"] = {}
                
        return response