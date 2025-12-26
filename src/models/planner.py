"""Planner agent output models."""

from pydantic import BaseModel, Field

from src.models.workflow_state import Task


class PlannerOutput(BaseModel):
    """Planner output containing task list."""

    tasks: list[Task] = Field(..., description="List of tasks to execute")
    reasoning: str = Field(..., description="Reasoning for the task plan")

