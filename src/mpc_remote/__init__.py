"""MPC Remote - ZeroMQ implementation of Model Context Protocol"""

from .core.protocol import ProtocolHandler
from .security.auth import AuthenticatedProtocolHandler
from .transport.zmq import ZMQTransport

__version__ = "0.1.0"