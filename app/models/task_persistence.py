"""Task persistence models for saving and loading task data."""

from typing import Optional

from pydantic import BaseModel, Field


class PersistedTask(BaseModel):
    """Model for a persisted task in JSON format."""

    agent: str = Field(..., description="Agent responsible for this task")
    description: str = Field(..., description="Description of what needs to be done")
    status: str = Field(..., description="Current status of the task")
    result: Optional[str] = Field(default=None, description="Result of task execution")
    error: Optional[str] = Field(default=None, description="Error message if task failed")


class TaskFileData(BaseModel):
    """Model for the complete task file data structure."""

    user_input: str = Field(..., description="User input that generated these tasks")
    created_at: str = Field(..., description="Timestamp when tasks were created")
    reasoning: str = Field("", description="Reasoning from the planner")
    tasks: list[PersistedTask] = Field(default_factory=list, description="List of tasks")
