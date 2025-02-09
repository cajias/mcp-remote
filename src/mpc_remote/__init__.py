"""MPC Remote - ZeroMQ implementation of Model Context Protocol"""

from .core.protocol import ProtocolHandler
from .transport.zmq import ZMQTransport
from .security.auth import AuthenticatedProtocolHandler

__version__ = "0.1.0"