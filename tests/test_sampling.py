"""
Sampling Mechanism Tests

Sampling in the Model Context Protocol is a powerful feature that allows 
server-initiated, recursive AI interactions. Here's what it enables:

1. Iterative Content Generation
   - Start with an initial prompt
   - Allow AI to generate a response
   - Optionally use that response to generate a new, related prompt
   - Repeat for a specified number of iterations

2. Use Cases:
   - Story expansion (each iteration adds to the narrative)
   - Problem-solving with incremental refinement
   - Multi-step reasoning tasks
   - Exploratory AI-driven investigations

Example Workflow:
1. Initial Prompt: "Write a short story about a robot"
2. First Iteration: AI generates a basic story
3. Second Iteration: Use first story as context to expand plot
4. Continues until max iterations or stopping condition

This test suite verifies the sampling mechanism's core functionality.
"""

import pytest
import asyncio
from mpc_remote.core.sampling import SamplingManager, SamplingRequest
from mpc_remote.core.protocol import ProtocolHandler, Tool


@pytest.mark.asyncio
async def test_basic_sampling():
    """
    Verify basic sampling workflow
    - Single iteration
    - Verify result generation
    """
    # Create protocol handler with mock LLM tool
    protocol_handler = ProtocolHandler()
    
    async def mock_llm_sample(prompt: str, context: dict) -> str:
        """Simulate LLM response generation"""
        return f"Response to: {prompt}"
    
    protocol_handler.register_tool(Tool(
        name="llm_sample",
        implementation=mock_llm_sample,
        description="Mock LLM sampling tool"
    ))
    
    # Create sampling manager
    sampling_manager = SamplingManager(protocol_handler)
    
    # Create sampling request
    request = SamplingRequest(
        prompt="Tell me a short story",
        max_iterations=1
    )
    
    # Execute sampling
    result = await sampling_manager.initiate_sampling(request)
    
    # Verify result structure
    assert "sampling_id" in result
    assert "results" in result
    assert len(result["results"]) == 1
    assert result["results"][0].startswith("Response to:")


@pytest.mark.asyncio
async def test_multi_iteration_sampling():
    """
    Verify multi-iteration sampling
    - Multiple iterations
    - Context accumulation
    """
    protocol_handler = ProtocolHandler()
    
    # Track iteration state
    iteration_count = 0
    
    async def mock_llm_sample(prompt: str, context: dict) -> str:
        """Simulate LLM response with iteration tracking"""
        nonlocal iteration_count
        iteration_count += 1
        return f"Iteration {iteration_count} response: {prompt}"
    
    protocol_handler.register_tool(Tool(
        name="llm_sample",
        implementation=mock_llm_sample,
        description="Mock LLM sampling tool"
    ))
    
    sampling_manager = SamplingManager(protocol_handler)
    
    # Create sampling request with multiple iterations
    request = SamplingRequest(
        prompt="Start a story",
        max_iterations=3,
        result_aggregator=lambda results: f"Continue this: {results[-1]}"
    )
    
    # Execute sampling
    result = await sampling_manager.initiate_sampling(request)
    
    # Verify multiple iterations
    assert len(result["results"]) == 3
    assert all("Iteration" in res for res in result["results"])


@pytest.mark.asyncio
async def test_sampling_cancellation():
    """
    Verify sampling can be cancelled
    """
    protocol_handler = ProtocolHandler()
    
    async def mock_llm_sample(prompt: str, context: dict) -> str:
        await asyncio.sleep(0.1)  # Simulate processing time
        return "Sample response"
    
    protocol_handler.register_tool(Tool(
        name="llm_sample",
        implementation=mock_llm_sample,
        description="Mock LLM sampling tool"
    ))
    
    sampling_manager = SamplingManager(protocol_handler)
    
    # Create sampling request
    request = SamplingRequest(
        prompt="Long running task",
        max_iterations=10
    )
    
    # Start sampling
    sampling_task = asyncio.create_task(
        sampling_manager.initiate_sampling(request)
    )
    
    # Immediately cancel
    cancellation_result = sampling_manager.cancel_sampling(request.id)
    
    # Verify cancellation
    assert cancellation_result is True
    
    # Verify sampling status is None after cancellation
    status = sampling_manager.get_sampling_status(request.id)
    assert status is None
