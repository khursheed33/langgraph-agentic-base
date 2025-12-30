"""Status response schema."""

from typing import Optional

from pydantic import BaseModel, Field

from app.api.schemas.agent_status_response import AgentStatusResponse
from app.api.schemas.task_response import TaskResponse
from app.api.schemas.tool_status_response import ToolStatusResponse


class StatusResponse(BaseModel):
    """Status response schema for agent and tool status."""

    agents: list[AgentStatusResponse] = Field(..., description="List of agent statuses")
    tools: list[ToolStatusResponse] = Field(..., description="List of tool usage statistics")
    current_agent: Optional[str] = Field(default=None, description="Currently executing agent")
    current_task: Optional[TaskResponse] = Field(default=None, description="Current task if any")

