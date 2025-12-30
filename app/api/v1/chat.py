"""Chat router for handling user messages."""

from fastapi import APIRouter, HTTPException

from app.api.schemas.agent_status_response import AgentStatusResponse
from app.api.schemas.chat_request import ChatRequest
from app.api.schemas.chat_response import ChatResponse
from app.api.schemas.status_response import StatusResponse
from app.api.schemas.task_response import TaskResponse
from app.api.schemas.token_cost_response import TokenCostResponse
from app.api.schemas.token_info_response import TokenInfoResponse
from app.api.schemas.token_usage_response import TokenUsageResponse
from app.api.schemas.tool_status_response import ToolStatusResponse
from app.api.utils import (
    get_all_agent_status,
    get_all_tool_status,
    get_current_task,
    get_workflow_state,
)
from app.services.workflow_service import run_workflow
from app.utils.logger import logger

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("/", response_model=ChatResponse)
async def chat(request: ChatRequest) -> ChatResponse:
    """Handle chat message and return response with agent/tool status.
    
    Args:
        request: Chat request with message and optional thread_id.
        
    Returns:
        Chat response with result and complete status.
    """
    try:
        logger.info(f"Received chat request: {request.message[:100]}...")
        
        # Normalize thread_id - generate UUID if empty, None, or invalid
        thread_id = request.thread_id
        if not thread_id or thread_id.strip() == "" or thread_id.lower() == "string":
            thread_id = None
        
        # Use the workflow service
        
        # Run workflow
        result = await run_workflow(request.message, thread_id)
        # Ensure thread_id is always set from result (should be UUID if new thread)
        thread_id = result.get("thread_id")
        if not thread_id:
            # Fallback: generate UUID if somehow not set
            import uuid
            thread_id = str(uuid.uuid4())
            logger.warning(f"Thread ID was not returned, generated new one: {thread_id}")
        
        # Get current workflow state
        workflow_state = get_workflow_state(thread_id)
        
        # Get agent and tool status - filter to only show used ones
        usage_stats = result.get("usage_stats", {})
        
        # Get token stats
        token_stats = result.get("token_stats", {})
        
        # Get all agent statuses but filter to only used agents
        all_agent_statuses = get_all_agent_status(usage_stats)
        used_agent_statuses = [
            agent_status for agent_status in all_agent_statuses
            if agent_status.get("usage_count", 0) > 0
        ]
        
        # Get all tool statuses but filter to only used tools
        all_tool_statuses = get_all_tool_status(usage_stats)
        used_tool_statuses = [
            tool_status for tool_status in all_tool_statuses
            if tool_status.usage_count > 0
        ]
        
        # Get current task
        current_task = get_current_task(workflow_state)
        
        # Build status response with only used agents and tools
        status = StatusResponse(
            agents=[
                AgentStatusResponse(**agent_status) for agent_status in used_agent_statuses
            ],
            tools=[ToolStatusResponse(**tool_status.model_dump()) for tool_status in used_tool_statuses],
            current_agent=workflow_state.get("current_agent") if workflow_state else None,
            current_task=TaskResponse(**current_task.model_dump()) if current_task else None,
        )
        
        # Build token info response
        token_info = TokenInfoResponse(
            usage=TokenUsageResponse(
                input_tokens=token_stats.get("input_tokens", 0),
                output_tokens=token_stats.get("output_tokens", 0),
                total_tokens=token_stats.get("total_tokens", 0),
            ),
            cost=TokenCostResponse(
                input_cost=token_stats.get("input_cost", 0.0),
                output_cost=token_stats.get("output_cost", 0.0),
                total_cost=token_stats.get("total_cost", 0.0),
            ),
        )
        
        # Build chat response
        response = ChatResponse(
            thread_id=thread_id,
            user_input=result.get("user_input", request.message),
            final_result=result.get("final_result"),
            messages=result.get("messages", []),
            error=result.get("error"),
            status=status,
            usage_stats=usage_stats,
            token_info=token_info,
        )
        
        logger.info(f"Chat request completed for thread: {thread_id}")
        return response
        
    except Exception as e:
        logger.error(f"Chat error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

