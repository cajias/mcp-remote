from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
from packaging import version

@dataclass
class ProtocolVersionRange:
    min_version: str
    max_version: str
    fallback_versions: List[str]

# Protocol version compatibility matrix
# Maps client protocol versions to compatible server protocol versions
PROTOCOL_COMPATIBILITY = {
    "1.0": ProtocolVersionRange(
        min_version="1.0",
        max_version="1.1",
        fallback_versions=["1.0"]
    ),
    "1.1": ProtocolVersionRange(
        min_version="1.0",
        max_version="1.1",
        fallback_versions=["1.0", "1.1"]
    ),
}

def is_protocol_compatible(client_version: str, server_version: str) -> Tuple[bool, Optional[str]]:
    """
    Check if protocol versions are compatible and return fallback if needed
    Returns (is_compatible, fallback_version)
    """
    try:
        if client_version not in PROTOCOL_COMPATIBILITY:
            return False, None
            
        compat_range = PROTOCOL_COMPATIBILITY[client_version]
        client_ver = version.parse(client_version)
        server_ver = version.parse(server_version)
        min_ver = version.parse(compat_range.min_version)
        max_ver = version.parse(compat_range.max_version)
        
        # Direct compatibility
        if min_ver <= server_ver <= max_ver:
            return True, None
            
        # Check fallbacks
        for fallback in compat_range.fallback_versions:
            if version.parse(fallback) == server_ver:
                return True, fallback
                
        return False, None
    except version.InvalidVersion:
        return False, None

# Required capabilities matrix
# Maps protocol versions to required capabilities
REQUIRED_CAPABILITIES = {
    "1.0": {
        "basic": ["send_message", "receive_message"],
        "streaming": ["stream_data"],
        "async": ["async_operation"]
    },
    "1.1": {
        "basic": ["send_message", "receive_message", "error_handling"],
        "streaming": ["stream_data", "backpressure"],
        "async": ["async_operation", "cancellation"]
    }
}