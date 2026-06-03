```
   __  __ ____   ____      ____                       _
  |  \/  |  _ \ / ___|    |  _ \ ___ _ __ ___   ___ | |_ ___
  | |\/| | |_) | |   _____| |_) / _ \ '_ ` _ \ / _ \| __/ _ \
  | |  | |  __/| |__|_____|  _ <  __/ | | | | | (_) | ||  __/
  |_|  |_|_|    \____|    |_| \_\___|_| |_| |_|\___/ \__\___|
```

**A multi-transport implementation of the Model Context Protocol — ZeroMQ, WebSocket, and stdio behind one URL.**

<p align="center">
  <a href="LICENSE"><img src="https://img.shields.io/github/license/cajias/mcp-remote" alt="License"></a>
  <img src="https://img.shields.io/github/languages/top/cajias/mcp-remote" alt="Top language">
  <img src="https://img.shields.io/github/last-commit/cajias/mcp-remote" alt="Last commit">
  <img src="https://img.shields.io/badge/python-%E2%89%A53.8-blue" alt="Python >=3.8">
  <img src="https://img.shields.io/badge/transport-ZeroMQ%20%C2%B7%20WebSocket%20%C2%B7%20stdio-orange" alt="Transports">
</p>

`mpc-remote` is a Python implementation of the [Model Context Protocol](https://modelcontextprotocol.io)
that decouples the protocol from the wire. The canonical MCP SDK speaks stdio; this library keeps the
same JSON-RPC protocol layer but lets you run it over **ZeroMQ** (`tcp://`, `ipc://`, `inproc://`),
**WebSocket** (`ws://`, `wss://`), or **stdio** — selected automatically from the connection URL. The
protocol handling is identical regardless of transport, with optional ZMQ CURVE encryption, TLS for
WebSocket, and a pluggable authentication layer (including Amazon Cognito).

## ✨ Features

- **Pluggable transports** — ZeroMQ, WebSocket, and stdio, behind a single URL-driven API.
- **Transport-transparent protocol** — the same `ProtocolHandler` JSON-RPC layer runs over every transport.
- **Built-in security** — ZMQ CURVE keypair encryption and WebSocket TLS/SSL.
- **Authenticated handler** — `AuthenticatedProtocolHandler` wraps the protocol layer with auth and consent checks.
- **Amazon Cognito integration** — token verification, validation, and refresh (see [`COGNITO_README.md`](COGNITO_README.md)).
- **stdio compatibility** — interoperates with the canonical MCP SDK's stdio transport.

## 📦 Installation

Requires Python ≥ 3.8.

```bash
# From a checkout
pip install -e .

# With development extras (pytest, ruff, coverage)
pip install -e ".[dev]"
```

Core runtime dependencies: `pyzmq`, `jsonschema`, `cryptography`, `anyio`, `pydantic`.

## 🚀 Usage

The public package surface exposes the protocol and transport primitives:

```python
from mpc_remote import (
    ProtocolHandler,            # transport-agnostic JSON-RPC protocol layer
    AuthenticatedProtocolHandler,  # protocol layer with auth + consent
    ZMQTransport,               # ZeroMQ transport
)
```

### A secure ZeroMQ transport

```python
from mpc_remote import ZMQTransport

# Bind a server-side ZMQ transport
transport = ZMQTransport()

# CURVE keypairs are generated and managed by the transport's security layer;
# see src/mpc_remote/transport/zmq_transport.py for the full option set.
```

### Authenticating the protocol layer

```python
from mpc_remote import ProtocolHandler, AuthenticatedProtocolHandler

handler = ProtocolHandler()
secured = AuthenticatedProtocolHandler(handler)
```

### Amazon Cognito authentication

```python
from mpc_remote.security.cognito_auth_integration import CognitoAuthIntegration

auth = CognitoAuthIntegration()
tokens = auth.authenticate("username", "password")
claims = auth.validate_token(tokens["access_token"])
refreshed = auth.refresh_tokens(tokens["refresh_token"])
```

Cognito requires `COGNITO_POOL_ID`, `AWS_REGION`, and `COGNITO_CLIENT_ID` to be set, plus AWS
credentials. Full setup is documented in [`COGNITO_README.md`](COGNITO_README.md).

### Supported URL schemes

| Scheme            | Transport            |
| ----------------- | -------------------- |
| `tcp://`          | ZeroMQ (TCP)         |
| `ipc://`          | ZeroMQ (IPC)         |
| `inproc://`       | ZeroMQ (in-process)  |
| `ws://`           | WebSocket            |
| `wss://`          | WebSocket over TLS   |
| *(no URL)*        | stdio (SDK-compatible) |

## 🗂️ Project Structure

```
mcp-remote/
├── src/mpc_remote/
│   ├── __init__.py          # public exports: ProtocolHandler, AuthenticatedProtocolHandler, ZMQTransport
│   ├── core/                # JSON-RPC, protocol handler, errors, constants
│   ├── protocol/            # protocol adapter, session, and type definitions
│   ├── transport/           # zmq, websocket, and stdio transports
│   ├── security/            # auth, consent, and Cognito integration
│   ├── server/              # server runner, tools, resources, decorators
│   ├── client/              # client-side session helpers
│   └── utils/               # logging and validation helpers
├── tests/                   # unit and integration test suite
├── docs/                    # Sphinx documentation sources
├── pyproject.toml           # build config, dependencies, pytest + coverage
├── Makefile                 # test, lint, docs, and release targets
└── COGNITO_README.md        # Amazon Cognito setup guide
```

## 🛠️ Development

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run the test suite (pytest is configured in pyproject.toml)
pytest

# Run only integration tests
pytest -m integration

# Lint
ruff check src tests

# Or via the Makefile
make test
make lint
```

Coverage is enabled by default through `pyproject.toml` (`--cov=mpc_remote`).

## 🤝 Contributing

Contributions are welcome. Please read [`CONTRIBUTING.rst`](CONTRIBUTING.rst) and the
[`CODE_OF_CONDUCT.rst`](CODE_OF_CONDUCT.rst). In short: fork, create a feature branch, add tests,
keep `ruff` and `pytest` green, and open a pull request.

## 📄 License

Released under the [MIT License](LICENSE). Copyright © 2025 Raul Cajias.
