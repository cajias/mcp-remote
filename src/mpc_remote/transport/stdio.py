from typing import AsyncGenerator, Union, Optional
import anyio
from anyio import Stream
from .buffer import MessageBuffer, BackpressureManager

class StreamCommunicator:
    """
    Enhanced stream communicator with buffer management and backpressure
    """
    def __init__(
        self,
        stream: Stream,
        max_buffer_size: int = 1024 * 1024,  # 1MB default
        chunk_size: int = 4096  # 4KB chunks
    ):
        self.stream = stream
        self._buffer = MessageBuffer(max_buffer_size)
        self._backpressure = BackpressureManager(max_buffer_size * 0.8)  # 80% threshold
        self._chunk_size = chunk_size
        self._closed = False

    async def read_message(self) -> AsyncGenerator[bytes, None]:
        """
        Read messages using AnyIO stream semantics with backpressure support
        """
        try:
            while not self._closed:
                # Check backpressure before reading
                await self._backpressure.check_backpressure(self._buffer.size)
                
                # Read chunk
                chunk = await self.stream.receive(self._chunk_size)
                if not chunk:
                    break

                # Write to buffer
                if not self._buffer.write(chunk):
                    # Buffer is full, apply backpressure
                    continue

                # Check for message boundaries
                if self._is_message_complete(chunk):
                    self._buffer.mark_message_boundary()
                    
                    # Read complete message
                    while message := self._buffer.read():
                        # Release backpressure if buffer is now below threshold
                        self._backpressure.release_backpressure(self._buffer.size)
                        yield message

        except Exception as e:
            # Log error and close stream
            print(f"Error in read_message: {e}")
            await self.close()
            raise

    async def write_message(self, message: Union[str, bytes]) -> None:
        """
        Write messages with proper encoding and chunking
        """
        try:
            if isinstance(message, str):
                message = message.encode('utf-8')

            # Split message into chunks if needed
            for i in range(0, len(message), self._chunk_size):
                chunk = message[i:i + self._chunk_size]
                
                # Check backpressure before sending
                await self._backpressure.check_backpressure(len(chunk))
                
                # Send chunk
                await self.stream.send(chunk)

        except Exception as e:
            print(f"Error in write_message: {e}")
            await self.close()
            raise

    def _is_message_complete(self, chunk: bytes) -> bool:
        """
        Check if we have a complete message
        Override this method for different message framing protocols
        """
        # Default implementation checks for newline
        return b'\n' in chunk

    async def close(self) -> None:
        """
        Clean up resources
        """
        if not self._closed:
            self._closed = True
            try:
                await self.stream.aclose()
            except Exception as e:
                print(f"Error closing stream: {e}")

class StdioTransport:
    """
    Implementation of stdio-based transport using StreamCommunicator
    """
    def __init__(
        self,
        max_buffer_size: int = 1024 * 1024,
        chunk_size: int = 4096
    ):
        self.stdin_stream: Optional[Stream] = None
        self.stdout_stream: Optional[Stream] = None
        self.communicator: Optional[StreamCommunicator] = None
        self._max_buffer_size = max_buffer_size
        self._chunk_size = chunk_size

    async def initialize(self) -> None:
        """
        Initialize stdio streams with AnyIO
        """
        try:
            # Create memory streams for testing/mocking
            self.stdin_stream = await anyio.streams.create_memory_object_stream(
                max_buffer_size=self._max_buffer_size
            )
            self.stdout_stream = await anyio.streams.create_memory_object_stream(
                max_buffer_size=self._max_buffer_size
            )
            
            # Initialize communicator with configured parameters
            self.communicator = StreamCommunicator(
                self.stdout_stream,
                max_buffer_size=self._max_buffer_size,
                chunk_size=self._chunk_size
            )
        except Exception as e:
            print(f"Error initializing transport: {e}")
            raise

    async def send(self, message: Union[str, bytes]) -> None:
        """
        Send a message through stdout
        """
        if self.communicator:
            await self.communicator.write_message(message)
        else:
            raise RuntimeError("Transport not initialized")

    async def receive(self) -> AsyncGenerator[bytes, None]:
        """
        Receive messages from stdin with backpressure support
        """
        if self.communicator:
            async for message in self.communicator.read_message():
                yield message
        else:
            raise RuntimeError("Transport not initialized")

    async def close(self) -> None:
        """
        Clean up resources
        """
        if self.communicator:
            await self.communicator.close()
            self.communicator = None