"""Backward compatible session handling"""

from typing import Any, Dict, Optional

from anyio import Event
from anyio.streams.memory import MemoryObjectReceiveStream, MemoryObjectSendStream

from ..client.session import ClientCapabilities, MCPSession
from .adapter import ProtocolAdapter


class LegacySession(MCPSession):
    """Session handler with backward compatibility"""

    def __init__(
        self,
        read_stream: MemoryObjectReceiveStream,
        write_stream: MemoryObjectSendStream,
        auth_enabled: bool = False
    ) -> None:
        super().__init__()
        self._read_stream = read_stream
        self._write_stream = write_stream
        self._adapter = ProtocolAdapter()
        self._adapter.auth_enabled = auth_enabled
        self._initialized = Event()

    async def handle_initialize_request(
        self,
        method: str,
        params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Handle initialize request with backward compatibility
        """
        try:
            # Adapt legacy initialize request
            version, capabilities = self._adapter.adapt_initialize_request(params)

            # Negotiate version using new mechanism
            if not await self.initialize_version(version):
                raise RuntimeError(
                    f"Version negotiation failed for version {version}"
                )

            # Set up capabilities
            client_caps = ClientCapabilities(
                version=version,
                features=capabilities["features"],
                extensions=capabilities.get("extensions", {})
            )

            if not await self.negotiate_capabilities(client_caps):
                raise RuntimeError("Capability negotiation failed")

            # Create legacy-compatible response
            response = self._adapter.adapt_initialize_response(
                self.negotiated_protocol_version or version,
                capabilities
            )

            self._initialized.set()
            return response

        except Exception as e:
            self._initialized.set()
            raise RuntimeError(f"Initialization failed: {e}")

    async def handle_request(
        self,
        method: str,
        params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Handle request with backward compatibility
        """
        # Wait for initialization
        await self._initialized.wait()

        # Adapt request/response if needed
        adapted_params = self._adapter.adapt_request(method, params)
        response = await self._handle_request(method, adapted_params)
        return self._adapter.adapt_response(method, response)

    async def _handle_request(
        self,
        method: str,
        params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Internal request handler - override in subclasses
        """
        raise NotImplementedError()

    async def send_notification(
        self,
        method: str,
        params: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Send notification with backward compatibility
        """
        if self._adapter.legacy_mode:
            # Adapt notification format if needed
            if method == "notifications/progress":
                params = self._adapt_progress_notification(params)

        await self._send_notification(method, params or {})

    def _adapt_progress_notification(
        self,
        params: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Adapt progress notification for legacy clients
        """
        if not params:
            return {}

        # Convert new progress format to old
        return {
            "progressToken": params.get("token"),
            "progress": params.get("value", 0),
            "total": params.get("total")
        }
