"""Supervisor agent output models."""

from typing import Literal

from pydantic import BaseModel, Field

from app.constants import AgentType, END_NODE


class SupervisorDecision(BaseModel):
    """Supervisor decision output."""

    next_agent: AgentType | Literal[END_NODE] = Field(
        ..., description="Next agent to route to, or END to finish workflow"
    )
    reasoning: str = Field(..., description="Reasoning for the routing decision")

