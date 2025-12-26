"""Chat request schema."""

from typing import Optional

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    """Request schema for chat endpoint."""

    message: str = Field(..., description="User message/query")
    thread_id: Optional[str] = Field(
        default=None, description="Optional thread ID for conversation continuity"
    )

