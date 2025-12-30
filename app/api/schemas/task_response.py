"""Task response schema."""

from typing import Optional

from pydantic import BaseModel, Field


class TaskResponse(BaseModel):
    """Task response schema."""

    agent: str = Field(..., description="Agent responsible for this task")
    description: str = Field(..., description="Task description")
    status: str = Field(..., description="Task status")
    result: Optional[str] = Field(default=None, description="Task result")
    error: Optional[str] = Field(default=None, description="Task error if any")

