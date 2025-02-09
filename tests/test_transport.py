"""Tests for ZeroMQ transport implementation"""

import asyncio

import pytest
import zmq.asyncio

from mpc_remote.transport.zmq import ZMQTransport


@pytest.mark.asyncio
async def test_client_server_communication():
    """Test basic client-server communication"""
    server = ZMQTransport("tcp://*:5555", connection_type="bind")
    client = ZMQTransport("tcp://localhost:5555", connection_type="connect")
    
    try:
        ready = asyncio.Event()
        handled = asyncio.Event()
        
        async def handle_server():
            ready.set()
            try:
                request = await server.recv_json()
                assert request["method"] == "test_method"
                assert request["params"]["value"] == 42
                await server.send_json({
                    "jsonrpc": "2.0",
                    "result": "success",
                    "id": request.get("id")
                })
            finally:
                handled.set()
        
        server_task = asyncio.create_task(handle_server())
        await ready.wait()
        
        response = await client.send_request({
            "jsonrpc": "2.0",
            "method": "test_method",
            "params": {"value": 42},
            "id": "test-1"
        })
        
        await handled.wait()
        assert response["result"] == "success"
        await server_task
        
    finally:
        server.close()
        client.close()

@pytest.mark.asyncio
async def test_inproc_communication():
    """Test communication within the same process"""
    # Use shared context for inproc communication
    context = zmq.asyncio.Context()
    
    try:
        endpoint = "inproc://test"
        server = ZMQTransport(endpoint, connection_type="bind", context=context)
        client = ZMQTransport(endpoint, connection_type="connect", context=context)
        
        ready = asyncio.Event()
        handled = asyncio.Event()
        
        async def handle_server():
            ready.set()
            try:
                request = await server.recv_json()
                await server.send_json({
                    "jsonrpc": "2.0",
                    "result": request["params"]["value"] * 2,
                    "id": request.get("id")
                })
            finally:
                handled.set()
        
        server_task = asyncio.create_task(handle_server())
        await ready.wait()
        
        response = await client.send_request({
            "jsonrpc": "2.0",
            "method": "double",
            "params": {"value": 21},
            "id": "test-2"
        })
        
        await handled.wait()
        assert response["result"] == 42
        await server_task
        
    finally:
        server.close()
        client.close()
        context.term()

@pytest.mark.asyncio
async def test_error_handling():
    """Test error handling"""
    server = ZMQTransport("tcp://*:5556", connection_type="bind")
    client = ZMQTransport("tcp://localhost:5556", connection_type="connect")
    
    try:
        ready = asyncio.Event()
        handled = asyncio.Event()
        
        async def handle_server():
            ready.set()
            try:
                await server.recv_json()
                await server.send_json({
                    "jsonrpc": "2.0",
                    "error": {
                        "code": -32000,
                        "message": "Test error"
                    },
                    "id": "test-3"
                })
            finally:
                handled.set()
        
        server_task = asyncio.create_task(handle_server())
        await ready.wait()
        
        response = await client.send_request({
            "jsonrpc": "2.0",
            "method": "failing_method",
            "params": {},
            "id": "test-3"
        })
        
        await handled.wait()
        assert "error" in response
        assert response["error"]["code"] == -32000
        assert response["error"]["message"] == "Test error"
        
        await server_task
        
    finally:
        server.close()
        client.close()

@pytest.mark.asyncio
async def test_multiple_clients():
    """Test multiple clients"""
    server = ZMQTransport("tcp://*:5557", connection_type="bind")
    clients = [
        ZMQTransport("tcp://localhost:5557", connection_type="connect")
        for _ in range(3)
    ]
    
    try:
        request_count = 0
        ready = asyncio.Event()
        handled = asyncio.Event()
        
        async def handle_server():
            nonlocal request_count
            ready.set()
            try:
                for _ in range(len(clients)):
                    await server.recv_json()
                    request_count += 1
                    await server.send_json({
                        "jsonrpc": "2.0",
                        "result": f"response-{request_count}",
                        "id": "test-4"
                    })
            finally:
                handled.set()
        
        server_task = asyncio.create_task(handle_server())
        await ready.wait()
        
        responses = await asyncio.gather(*(
            client.send_request({
                "jsonrpc": "2.0",
                "method": "test",
                "params": {},
                "id": "test-4"
            })
            for client in clients
        ))
        
        await handled.wait()
        assert len(responses) == len(clients)
        assert request_count == len(clients)
        await server_task
        
    finally:
        server.close()
        for client in clients:
            client.close()