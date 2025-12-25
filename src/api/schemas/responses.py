"""Response schemas for API endpoints."""

from typing import Any, Optional

from pydantic import BaseModel, Field


class ErrorResponse(BaseModel):
    """Error response schema."""

    error: str = Field(..., description="Error message")
    detail: Optional[str] = Field(default=None, description="Detailed error information")


class TaskResponse(BaseModel):
    """Task response schema."""

    agent: str = Field(..., description="Agent responsible for this task")
    description: str = Field(..., description="Task description")
    status: str = Field(..., description="Task status")
    result: Optional[str] = Field(default=None, description="Task result")
    error: Optional[str] = Field(default=None, description="Task error if any")


class ToolStatusResponse(BaseModel):
    """Tool status response schema."""

    tool_name: str = Field(..., description="Tool name")
    usage_count: int = Field(..., description="Number of times tool was used")


class AgentStatusResponse(BaseModel):
    """Agent status response schema."""

    agent_name: str = Field(..., description="Agent name")
    tools_count: int = Field(..., description="Number of tools available")
    tools: list[str] = Field(..., description="List of tool names")
    usage_count: int = Field(default=0, description="Number of times agent was used")


class StatusResponse(BaseModel):
    """Status response schema for agent and tool status."""

    agents: list[AgentStatusResponse] = Field(..., description="List of agent statuses")
    tools: list[ToolStatusResponse] = Field(..., description="List of tool usage statistics")
    current_agent: Optional[str] = Field(default=None, description="Currently executing agent")
    current_task: Optional[TaskResponse] = Field(default=None, description="Current task if any")


class TokenUsageResponse(BaseModel):
    """Token usage response schema."""

    input_tokens: int = Field(default=0, description="Total input tokens")
    output_tokens: int = Field(default=0, description="Total output tokens")
    total_tokens: int = Field(default=0, description="Total tokens")


class TokenCostResponse(BaseModel):
    """Token cost response schema."""

    input_cost: float = Field(default=0.0, description="Total input cost")
    output_cost: float = Field(default=0.0, description="Total output cost")
    total_cost: float = Field(default=0.0, description="Total cost")


class TokenInfoResponse(BaseModel):
    """Token information response schema."""

    usage: TokenUsageResponse = Field(default_factory=TokenUsageResponse, description="Token usage")
    cost: TokenCostResponse = Field(default_factory=TokenCostResponse, description="Token cost")


class HistoryResponse(BaseModel):
    """History response schema."""

    thread_id: str = Field(..., description="Thread ID")
    conversation_history: list[dict[str, Any]] = Field(
        ..., description="Conversation history entries"
    )
    total_entries: int = Field(..., description="Total number of entries")


class ChatResponse(BaseModel):
    """Chat response schema."""

    thread_id: str = Field(..., description="Thread ID for this conversation")
    user_input: str = Field(..., description="User input")
    final_result: Optional[str] = Field(default=None, description="Final result from workflow")
    messages: list[dict[str, Any]] = Field(..., description="Conversation messages")
    error: Optional[str] = Field(default=None, description="Error message if any")
    status: StatusResponse = Field(..., description="Complete agent and tool status")
    usage_stats: dict[str, Any] = Field(..., description="Usage statistics")
    token_info: TokenInfoResponse = Field(
        default_factory=TokenInfoResponse, description="Token usage and cost information"
    )

