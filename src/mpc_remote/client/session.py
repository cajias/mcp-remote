from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from ..version import __version__
from .version_matrix import PROTOCOL_COMPATIBILITY, REQUIRED_CAPABILITIES, is_protocol_compatible


class VersionInfo(BaseModel):
    version: str
    protocol_version: str
    extensions: Optional[Dict[str, Any]] = None
    fallback_protocol_versions: List[str] = Field(default_factory=list)

class VersionNegotiation(BaseModel):
    client_version: str
    supported_versions: Dict[str, VersionInfo]
    negotiated_protocol_version: Optional[str] = None

class ClientCapabilities(BaseModel):
    version: str
    features: List[str]
    extensions: Optional[Dict[str, Any]] = None
    required_features: List[str] = Field(default_factory=list)

class CapabilitySet(BaseModel):
    supported_features: List[str]
    active_features: List[str]
    required_features: List[str]
    extensions: Dict[str, Any] = {}
    protocol_version: str

    @classmethod
    def from_client_caps(cls, client_caps: ClientCapabilities, protocol_version: str) -> "CapabilitySet":
        # Get required capabilities for protocol version
        required_caps = REQUIRED_CAPABILITIES.get(protocol_version, {})
        all_required = []
        for feature_type in required_caps.values():
            all_required.extend(feature_type)

        # Determine active features based on requirements and support
        active = [f for f in client_caps.features if f in SUPPORTED_FEATURES]
        
        return cls(
            supported_features=client_caps.features,
            active_features=active,
            required_features=all_required,
            extensions=client_caps.extensions or {},
            protocol_version=protocol_version
        )

    def is_compatible(self) -> bool:
        # Check if all required features are active
        return all(req in self.active_features for req in self.required_features)

    def get_missing_requirements(self) -> List[str]:
        """Get list of required features that are not active"""
        return [req for req in self.required_features if req not in self.active_features]

SUPPORTED_FEATURES = [
    "basic",
    "streaming",
    "async",
    "error_handling",
    "backpressure",
    "cancellation"
]

class MCPSession:
    def __init__(self) -> None:
        self.capabilities: Optional[CapabilitySet] = None
        self.version_info = VersionInfo(
            version=__version__,
            protocol_version="1.1",  # Updated to latest protocol version
            extensions={},
            fallback_protocol_versions=["1.0"]
        )
        self.negotiated_protocol_version: Optional[str] = None

    async def initialize_version(self, client_version: str) -> bool:
        """
        Handle version negotiation with client
        Returns True if versions are compatible
        """
        version_map = await self._get_supported_versions()
        return await self._negotiate_version(client_version, version_map)

    async def _get_supported_versions(self) -> Dict[str, VersionInfo]:
        # Include all supported protocol versions
        versions = {}
        for protocol_ver in PROTOCOL_COMPATIBILITY.keys():
            version_info = self.version_info.copy()
            version_info.protocol_version = protocol_ver
            versions[f"{__version__}-{protocol_ver}"] = version_info
        return versions

    async def _negotiate_version(self, client_version: str, 
                               supported_versions: Dict[str, VersionInfo]) -> bool:
        try:
            # Extract protocol version from client version
            client_protocol_version = client_version.split("-")[-1]
            server_protocol_version = self.version_info.protocol_version

            # Check protocol compatibility
            is_compatible, fallback = is_protocol_compatible(
                client_protocol_version,
                server_protocol_version
            )

            if not is_compatible:
                return False

            # Store negotiated protocol version
            self.negotiated_protocol_version = fallback or server_protocol_version

            version_model = VersionNegotiation(
                client_version=client_version,
                supported_versions=supported_versions,
                negotiated_protocol_version=self.negotiated_protocol_version
            )
            return await self._verify_version_compatibility(version_model)
        except Exception as e:
            print(f"Version negotiation failed: {e}")
            return False

    async def _verify_version_compatibility(self, version_model: VersionNegotiation) -> bool:
        if not version_model.negotiated_protocol_version:
            return False
        return version_model.client_version in version_model.supported_versions

    async def negotiate_capabilities(self, client_caps: ClientCapabilities) -> bool:
        """
        Align capabilities between MCP Remote and client
        """
        if not self.negotiated_protocol_version:
            return False

        self.capabilities = await self._validate_capabilities(client_caps)
        return self.capabilities.is_compatible()

    async def _validate_capabilities(self, 
                                   client_caps: ClientCapabilities) -> CapabilitySet:
        if not self.negotiated_protocol_version:
            raise ValueError("Protocol version not negotiated")
            
        return CapabilitySet.from_client_caps(
            client_caps,
            self.negotiated_protocol_version
        )

    def get_active_features(self) -> List[str]:
        """Get list of currently active features"""
        return self.capabilities.active_features if self.capabilities else []

    def get_missing_requirements(self) -> List[str]:
        """Get list of required features that are not active"""
        return (
            self.capabilities.get_missing_requirements()
            if self.capabilities else []
        )