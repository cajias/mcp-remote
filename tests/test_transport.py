import pytest

# These tests target an unimplemented transport-buffering/stream-communicator
# subsystem: `mpc_remote.transport.buffer` (MessageBuffer/BackpressureManager)
# never existed in git history, and `StreamCommunicator`/`StdioTransport` are not
# defined in `transport.stdio` (only `StdIOTransport`). Skip at module level until
# that API is built, rather than fail collection.
pytest.skip(
    "transport.buffer / StreamCommunicator / StdioTransport are not implemented",
    allow_module_level=True,
)

import anyio  # noqa: E402
from mpc_remote.transport.buffer import MessageBuffer, BackpressureManager  # noqa: E402
from mpc_remote.transport.stdio import StreamCommunicator, StdioTransport  # noqa: E402

@pytest.mark.asyncio
async def test_message_buffer():
    buffer = MessageBuffer(max_size=100)
    
    # Test writing within limits
    assert buffer.write(b"Hello")
    assert buffer.size == 5
    
    # Test writing that would exceed limit
    large_data = b"x" * 96
    assert not buffer.write(large_data)
    
    # Test message boundaries
    buffer = MessageBuffer(max_size=100)
    assert buffer.write(b"Hello\nWorld\n")
    buffer.mark_message_boundary()
    
    message = buffer.read()
    assert message == b"Hello\nWorld\n"
    assert buffer.size == 0

@pytest.mark.asyncio
async def test_backpressure_manager():
    manager = BackpressureManager(high_water_mark=100)
    
    # Test no backpressure
    assert not manager.is_backpressured
    await manager.check_backpressure(50)
    assert not manager.is_backpressured
    
    # Test applying backpressure
    await manager.check_backpressure(150)
    assert manager.is_backpressured
    
    # Test releasing backpressure
    manager.release_backpressure(50)
    assert not manager.is_backpressured

@pytest.mark.asyncio
async def test_stream_communicator():
    # Create test streams
    send_stream, receive_stream = await anyio.create_memory_object_stream(100)
    communicator = StreamCommunicator(send_stream, max_buffer_size=1024)
    
    # Test basic message sending
    test_message = b"Hello World\n"
    await communicator.write_message(test_message)
    
    # Test message receiving
    received = None
    async for message in communicator.read_message():
        received = message
        break
    
    assert received == test_message
    
    # Test string message encoding
    await communicator.write_message("String Message\n")
    
    received = None
    async for message in communicator.read_message():
        received = message
        break
    
    assert received == b"String Message\n"

@pytest.mark.asyncio
async def test_stdio_transport():
    transport = StdioTransport(max_buffer_size=1024)
    await transport.initialize()
    
    # Test basic message exchange
    test_message = "Test Message\n"
    await transport.send(test_message)
    
    received = None
    async for message in transport.receive():
        received = message
        break
    
    assert received == test_message.encode()
    
    # Test cleanup
    await transport.close()
    
    # Test error handling
    with pytest.raises(RuntimeError):
        await transport.send("message")  # Should fail after close

@pytest.mark.asyncio
async def test_backpressure_handling():
    # Create a transport with small buffer for testing backpressure
    transport = StdioTransport(max_buffer_size=100, chunk_size=10)
    await transport.initialize()
    
    # Send messages until backpressure kicks in
    large_message = "x" * 200 + "\n"
    
    # This should trigger backpressure
    async def send_messages():
        try:
            await transport.send(large_message)
        except Exception as e:
            print(f"Expected error during send: {e}")
    
    async def receive_messages():
        try:
            async for _ in transport.receive():
                # Simulate slow consumer
                await anyio.sleep(0.1)
        except Exception as e:
            print(f"Expected error during receive: {e}")
    
    # Run both operations concurrently
    async with anyio.create_task_group() as tg:
        tg.start_soon(send_messages)
        tg.start_soon(receive_messages)
    
    await transport.close()