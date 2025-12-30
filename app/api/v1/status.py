"""Status router for getting agent and tool status."""

from typing import Optional

from fastapi import APIRouter, HTTPException

from app.api.schemas.agent_status_response import AgentStatusResponse
from app.api.schemas.error_response import ErrorResponse
from app.api.schemas.status_response import StatusResponse
from app.api.schemas.task_response import TaskResponse
from app.api.schemas.tool_status_response import ToolStatusResponse
from app.api.utils import (
    get_all_agent_status,
    get_all_tool_status,
    get_current_task,
    get_workflow_state,
)
from app.utils.logger import logger

router = APIRouter(prefix="/status", tags=["status"])


@router.get("/", response_model=StatusResponse)
async def get_status(thread_id: Optional[str] = None) -> StatusResponse:
    """Get current status of all agents and tools.
    
    Args:
        thread_id: Optional thread ID to get status for specific conversation.
        
    Returns:
        Status response with agent and tool information.
    """
    try:
        usage_stats = {}
        workflow_state = None
        
        if thread_id:
            workflow_state = get_workflow_state(thread_id)
            if workflow_state:
                # Extract usage stats from state
                state_usage_stats = workflow_state.get("usage_stats")
                if state_usage_stats:
                    if isinstance(state_usage_stats, dict):
                        usage_stats = state_usage_stats
                    else:
                        # If it's a UsageStats object, convert to dict
                        usage_stats = {
                            "agent_usage": getattr(state_usage_stats, "agent_usage", {}),
                            "tool_usage": getattr(state_usage_stats, "tool_usage", {}),
                        }
        
        # Get agent and tool status - filter to only show used ones
        all_agent_statuses = get_all_agent_status(usage_stats)
        used_agent_statuses = [
            agent_status for agent_status in all_agent_statuses
            if agent_status.get("usage_count", 0) > 0
        ]
        
        all_tool_statuses = get_all_tool_status(usage_stats)
        used_tool_statuses = [
            tool_status for tool_status in all_tool_statuses
            if tool_status.get("usage_count", 0) > 0
        ]
        
        # Get current task
        current_task = get_current_task(workflow_state)
        
        response = StatusResponse(
            agents=[
                AgentStatusResponse(**agent_status) for agent_status in used_agent_statuses
            ],
            tools=[ToolStatusResponse(**tool_status) for tool_status in used_tool_statuses],
            current_agent=workflow_state.get("current_agent") if workflow_state else None,
            current_task=TaskResponse(**current_task) if current_task else None,
        )
        
        return response
        
    except Exception as e:
        logger.error(f"Status error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

