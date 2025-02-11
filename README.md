# MPC Remote

ZeroMQ and WebSocket implementation of the Model Context Protocol.

## Features

- Full [Model Context Protocol](https://github.com/modelcontextprotocol/python-sdk) implementation
- Multiple transport options:
  - ZeroMQ (tcp://, ipc://, inproc://)
  - WebSocket (ws://, wss://)
  - Standard IO (compatible with canonical SDK)
- Built-in security:
  - ZMQ CURVE encryption
  - WebSocket TLS/SSL
- Transparent URL-based transport selection

## Installation

```bash
pip install mpc-remote
```

## Quick Start

```python
from mpc_remote import MCPClient

# Basic usage - transport selected automatically from URL
async with MCPClient.connect("tcp://localhost:5555") as session:
    await session.initialize()
    result = await session.call_tool("my_tool", {"arg": "value"})

# Secure ZMQ connection with CURVE
# Generate server keys first (typically done on server side)
server_keys = MCPClient.generate_client_keys()
server_public = server_keys.public_key

async with MCPClient.connect(
    "tcp://localhost:5555",
    server_key=server_public
) as session:
    await session.initialize()
    result = await session.call_tool("my_tool", {"arg": "value"})

# WebSocket with SSL
import ssl
ssl_context = ssl.create_default_context()
async with MCPClient.connect(
    "wss://example.com/mcp",
    ssl_context=ssl_context
) as session:
    await session.initialize()
    result = await session.call_tool("my_tool", {"arg": "value"})

# Standard IO (compatible with canonical SDK)
async with MCPClient.connect() as session:
    await session.initialize()
    result = await session.call_tool("my_tool", {"arg": "value"})
```

## Supported URL Schemes

- `tcp://` - ZMQ TCP transport
- `ipc://` - ZMQ IPC transport
- `inproc://` - ZMQ in-process transport
- `ws://` - WebSocket transport
- `wss://` - Secure WebSocket transport
- No URL - Standard IO transport (canonical SDK compatible)

## Security Features

### ZMQ CURVE Security

```python
# Generate keys
server_keys = MCPClient.generate_client_keys()
client_keys = MCPClient.generate_client_keys()

# Create secure connection
async with MCPClient.connect(
    "tcp://localhost:5555",
    server_key=server_keys.public_key,
    client_keys=client_keys
) as session:
    await session.initialize()
```

### WebSocket Security

```python
import ssl

# Configure SSL context
ssl_context = ssl.create_default_context()
ssl_context.load_verify_locations("path/to/ca.pem")

# Create secure connection
async with MCPClient.connect(
    "wss://example.com/mcp",
    ssl_context=ssl_context
) as session:
    await session.initialize()
```

## Transport-Specific Options

### ZMQ Options

```python
# Configure ZMQ socket options
async with MCPClient.connect(
    "tcp://localhost:5555",
    LINGER=0,          # ZMQ socket option
    RCVTIMEO=1000,     # Receive timeout
    SNDTIMEO=1000      # Send timeout
) as session:
    await session.initialize()
```

### WebSocket Options

```python
# Configure WebSocket options
async with MCPClient.connect(
    "ws://localhost:8080",
    ping_interval=20,    # Keep-alive ping interval
    ping_timeout=10,     # Ping timeout
    max_size=2**20      # Max message size
) as session:
    await session.initialize()
```

## Protocol Compatibility

This implementation maintains full compatibility with the [canonical MCP SDK](https://github.com/modelcontextprotocol/python-sdk) while adding transport options. The protocol implementation is identical regardless of transport choice:

```python
# All these are protocol-compatible:
async with MCPClient.connect("tcp://localhost:5555") as session:
    await session.initialize()
    result = await session.call_tool("my_tool", {"arg": "value"})

async with MCPClient.connect("ws://localhost:8080") as session:
    await session.initialize()
    result = await session.call_tool("my_tool", {"arg": "value"})

async with MCPClient.connect() as session:  # stdio like canonical SDK
    await session.initialize()
    result = await session.call_tool("my_tool", {"arg": "value"})
```

## Development

```bash
# Install development dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Run integration tests
pytest -m integration
```