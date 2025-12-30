"""Tool status model for API responses."""

from pydantic import BaseModel, Field


class ToolStatus(BaseModel):
    """Tool status model for API responses."""

    tool_name: str = Field(..., description="Name of the tool")
    usage_count: int = Field(default=0, description="Number of times the tool has been used")


class TaskStatusInfo(BaseModel):
    """Task status information model for API responses."""

    agent: str = Field(..., description="Agent responsible for the task")
    description: str = Field(..., description="Description of the task")
    status: str = Field(..., description="Current status of the task")
    result: str | None = Field(default=None, description="Result of the task execution")
    error: str | None = Field(default=None, description="Error message if task failed")
