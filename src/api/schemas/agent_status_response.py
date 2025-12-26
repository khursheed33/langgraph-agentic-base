"""Agent status response schema."""

from pydantic import BaseModel, Field


class AgentStatusResponse(BaseModel):
    """Agent status response schema."""

    agent_name: str = Field(..., description="Agent name")
    tools_count: int = Field(..., description="Number of tools available")
    tools: list[str] = Field(..., description="List of tool names")
    usage_count: int = Field(default=0, description="Number of times agent was used")

