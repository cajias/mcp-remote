"""Model Context Protocol Version Management"""

__version__ = "0.1.0"  # This matches our pyproject.toml
PROTOCOL_VERSION = "2024-11-05"
SUPPORTED_VERSIONS = [PROTOCOL_VERSION]

def get_current_version() -> str:
    """Return the current protocol version."""
    return PROTOCOL_VERSION

def is_version_supported(version: str) -> bool:
    """
    Check if a given version is supported.
    
    :param version: Version string to check
    :return: Boolean indicating version support
    """
    return version in SUPPORTED_VERSIONS