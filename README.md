# MPC Remote: High-Performance Model Context Protocol

A ZeroMQ-based implementation of the Model Context Protocol optimized for performance, security, and deployment flexibility.

## Key Features

- **Decorator-Based API**: Simple and intuitive tool/resource registration
- **Type Inference**: Automatic parameter schema generation from type hints
- **Enhanced Security**: Built-in authentication and access control
- **High Performance**: Native ZMQ messaging with configurable patterns
- **Robust Error Handling**: Comprehensive error management and recovery
- **Protocol Extensions**: Authentication and versioning improvements

## Architecture

### Data Flow
```mermaid
flowchart TD
    %% External Entity: Client Side
    A[Client Application]

    %% Transport Layer (abstracted as a single component)
    B[Transport Layer<br/> inproc/ipc/tcp/wss/ ]

    %% Server Side Components
    subgraph SERVER [Server Side]
      C[MCPServer]
      D[Protocol Handler]
      E[Tool/Resource Manager]
      F[Authentication Provider]
      G[Consent Manager]
      H[Logging & Validation]
    end

    %% Data Flow
    A -->|JSON-RPC Request| B
    B -->|Forward Request| C
    C -->|Pass Request| D
    D -->|Log & Validate Request| H
    D -->|Verify Token / Credentials| F
    F -->|Auth Response| D
    D -->|Check Consent if required| G
    G -->|Consent Response| D
    D -->|Dispatch to Tool/Resource| E
    E -->|Tool/Resource Execution Result| D
    D -->|Construct JSON-RPC Response| C
    C -->|Send Response| B
    B -->|JSON-RPC Response| A
```

### ERD
```mermaid
erDiagram
    %% Core protocol entities
    PROTOCOL_HANDLER {
      string version
    }
    TOOL {
      string name
      string type
      string description
      object params_schema
    }
    RESOURCE {
      string name
      string type
      string description
      string access_level
    }

    %% Server and Client entities
    MCP_SERVER {
      string name
      string version
    }
    MCP_CLIENT {
      string server_endpoint
      string protocol_version
    }

    %% Transport entities
    TRANSPORT {
      string endpoint
    }
    ZMQ_TRANSPORT {
      string connection_type
    }
    WEBSOCKET_TRANSPORT {
      string reconnect
      int max_reconnect_attempts
    }

    %% Security & Consent entities
    AUTHENTICATED_PROTOCOL_HANDLER {
    }
    AUTH_PROVIDER {
    }
    CONSENT_MANAGER {
    }
    CONSENT_RECORD {
      string id
      string resource_name
      string status
    }

    %% Auxiliary entities
    MCP_LOGGER {
      string name
      string level
    }
    VALIDATOR {
    }

    %% Relationships
    PROTOCOL_HANDLER ||--o{ TOOL : registers
    PROTOCOL_HANDLER ||--o{ RESOURCE : registers
    MCP_SERVER ||--|| PROTOCOL_HANDLER : uses
    MCP_SERVER ||--o{ TOOL : manages
    MCP_SERVER ||--o{ RESOURCE : manages
    MCP_CLIENT ||--|| TRANSPORT : "communicates over"

    %% Instead of inheritance arrows (which are not supported in erDiagram),
    %% we use one-to-one relationships to indicate "is a type of"
    TRANSPORT ||--|| ZMQ_TRANSPORT : "is a type of"
    TRANSPORT ||--|| WEBSOCKET_TRANSPORT : "is a type of"

    AUTHENTICATED_PROTOCOL_HANDLER ||--|| AUTH_PROVIDER : requires
    CONSENT_MANAGER ||--o{ CONSENT_RECORD : manages
```
### Component Diagram

```mermaid
flowchart TD
    %% Overall MPC Remote System
    subgraph MPC_Remote
      %% Core components (protocol and related services)
      subgraph Core
        PH[ProtocolHandler]
        JR[JSONRPCProtocol]
        ERR[Error Handling]
        CONST[Constants]
      end

      %% Server components (exposes functionality via registered tools and resources)
      subgraph Server
        MS[MCPServer]
        TM[Tool Manager]
        RM[Resource Manager]
        SD[Server Decorators]
      end

      %% Client component (initiates requests)
      subgraph Client
        MC[MCPClient]
      end

      %% Transport components (communication mechanisms)
      subgraph Transport
        ZT[ZMQTransport]
        WT[WebSocketTransport]
      end

      %% Security components (authentication and consent)
      subgraph Security
        AP[AuthProvider / Authentication]
        CM[ConsentManager]
      end

      %% Utilities (supporting logging and validation)
      subgraph Utils
        LU[Logging Utilities]
        VU[Validation Utilities]
      end
    end

    %% Relationships between components
    %% Server uses core services to process requests.
    MS --> PH
    PH --> JR
    PH --> ERR
    PH --> CONST
    MS --> TM
    MS --> RM
    MS --> SD

    %% Client communicates over a transport layer.
    MC --> ZT
    MC --> WT

    %% Server integrates security services.
    MS --> AP
    MS --> CM

    %% Server employs utilities for logging and input validation.
    MS --> LU
    MS --> VU
```
## Quick Start

### Installation
```bash
pip install mpc-remote

# Development install
pip install -e ".[dev]"
```

### Basic Usage

```python
from mpc_remote import MCPServer

# Create server
server = MCPServer()

# Register tools with decorators
@server.tool("add")
async def add(a: int, b: int) -> int:
    return a + b

# Register resources with decorators
@server.resource("user_data")
class UserData:
    def __init__(self):
        self.data = {}

    async def get(self, user_id: str) -> dict:
        return self.data.get(user_id, {})

# Configure security (optional)
@server.tool("analyze", consent_required=True)
async def analyze_data(data: dict) -> dict:
    return await process_data(data)

# Client usage
client = MCPClient("tcp://localhost:5555")
result = await client.execute_tool("add", {"a": 5, "b": 3})
```

## Advanced Features

### Type Hints and Schema Generation
```python
@server.tool("process")
async def process_data(
    input_data: List[float],
    threshold: float = 0.5,
    mode: str = "default"
) -> Dict[str, Any]:
    """
    Process input data with given parameters.
    Schema is automatically generated from type hints.
    """
    return {"result": await analyze(input_data, threshold, mode)}
```

### Consent and Authentication

#### Cognito Integration
```python
# Somewhere in your application setup code:
from mpc_remote.server.base import MCPServer
from mpc_remote.security.authentication import AuthenticationManager
from mpc_remote.security.cognito_auth_integration import cognito_auth_handler

auth_manager = AuthenticationManager()
auth_manager.add_custom_auth_method("cognito", cognito_auth_handler)

# Create your server instance.
server = MCPServer(name="MyMCPServer")

# Set the authentication handler on the server.
# The handler receives a context dictionary (for example, extracted from the request)
# and should return True (or the user context) if authentication succeeds.
server.set_auth_handler(
    lambda context: auth_manager.authenticate(
        username="example_user",
        token="eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9...",  # Cognito JWT token
        method="cognito"
    )
)
```

#### Consent
```python
# Add consent handler
server.set_consent_handler(async def(tool_name, context):
    return await check_user_consent(context["user_id"], tool_name))

# Add authentication
server.set_auth_handler(async def(context):
    return await verify_token(context.get("token")))
```

### Resource Access Control
```python
@server.resource(
    "sensitive_data",
    access_level=ResourceAccessLevel.READ_WRITE,
    consent_required=True
)
class SensitiveData:
    """Access-controlled resource example"""
```

## Development

### Running Tests
```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run tests
pytest tests/

# With coverage
pytest --cov=mpc_remote tests/
```

### Common Issues

1. **Connection Timeouts**
   - Check network connectivity
   - Verify correct endpoints
   - Check firewall settings

2. **Authentication Failures**
   - Verify token validity
   - Check permission configuration
   - Ensure auth provider is properly configured

3. **Performance Issues**
   - Adjust HWM for message queuing
   - Configure appropriate timeouts
   - Consider deployment pattern changes

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## License

MIT License - see [LICENSE](LICENSE) for details.
