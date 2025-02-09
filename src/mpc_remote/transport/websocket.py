"""WebSocket transport implementation for Model Context Protocol"""

import asyncio
import json
from typing import Any, Dict, Optional

import websockets


class WebSocketTransport:
    """
    WebSocket transport for Model Context Protocol communications
    
    Supports full-duplex WebSocket communication
    """
    def __init__(
        self, 
        endpoint: str, 
        reconnect: bool = True,
        max_reconnect_attempts: int = 3
    ):
        """
        Initialize WebSocket transport
        
        :param endpoint: WebSocket server endpoint
        :param reconnect: Enable automatic reconnection
        :param max_reconnect_attempts: Maximum reconnection attempts
        """
        self.endpoint = endpoint
        self.websocket = None
        self.reconnect = reconnect
        self.max_reconnect_attempts = max_reconnect_attempts
        
        # Request tracking
        self._pending_requests = {}
    
    async def _connect(self):
        """
        Establish WebSocket connection
        
        :return: WebSocket connection
        """
        attempts = 0
        while attempts < self.max_reconnect_attempts:
            try:
                self.websocket = await websockets.connect(self.endpoint)
                return self.websocket
            except Exception as e:
                attempts += 1
                if attempts >= self.max_reconnect_attempts:
                    raise ConnectionError(f"Failed to connect after {attempts} attempts: {e}")
                await asyncio.sleep(2 ** attempts)  # Exponential backoff
    
    async def send_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """
        Send a JSON-RPC request via WebSocket
        
        :param request: JSON-RPC request dictionary
        :return: JSON-RPC response
        """
        # Ensure connection
        if not self.websocket:
            await self._connect()
        
        # Prepare request
        request_json = json.dumps(request)
        
        try:
            # Send request
            await self.websocket.send(request_json)
            
            # Wait for response
            response_json = await self.websocket.recv()
            return json.loads(response_json)
        
        except websockets.ConnectionClosed:
            if self.reconnect:
                # Attempt reconnection
                await self._connect()
                return await self.send_request(request)
            raise
        except Exception as e:
            raise RuntimeError(f"WebSocket request failed: {e}")
    
    async def listen(self, message_handler: Optional[callable] = None):
        """
        Listen for incoming messages
        
        :param message_handler: Optional callback for processing messages
        """
        if not self.websocket:
            await self._connect()
        
        try:
            while True:
                try:
                    message = await self.websocket.recv()
                    parsed_message = json.loads(message)
                    
                    if message_handler:
                        await message_handler(parsed_message)
                except websockets.ConnectionClosed:
                    if self.reconnect:
                        await self._connect()
                    else:
                        break
        except Exception as e:
            print(f"WebSocket listening error: {e}")
    
    async def close(self):
        """
        Close WebSocket connection
        """
        if self.websocket:
            await self.websocket.close()
            self.websocket = None

# Example usage
async def example_websocket_transport():
    """
    Demonstrate WebSocket transport usage
    """
    transport = WebSocketTransport('ws://localhost:8765')
    
    # Example request
    request = {
        "jsonrpc": "2.0",
        "method": "add",
        "params": {"a": 5, "b": 3},
        "id": "example-request"
    }
    
    try:
        # Message handler for async messages
        async def handle_message(message):
            print("Received message:", message)
        
        # Start listening in background
        listen_task = asyncio.create_task(transport.listen(handle_message))
        
        # Send request
        response = await transport.send_request(request)
        print("Response:", response)
        
        # Wait a bit to receive potential async messages
        await asyncio.sleep(1)
    
    except Exception as e:
        print(f"Error: {e}")
    finally:
        await transport.close()

# Main execution
if __name__ == "__main__":
    asyncio.run(example_websocket_transport())
