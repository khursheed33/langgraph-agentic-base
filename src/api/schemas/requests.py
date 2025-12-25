"""Request schemas for API endpoints."""

from typing import Optional

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    """Request schema for chat endpoint."""

    message: str = Field(..., description="User message/query")
    thread_id: Optional[str] = Field(
        default=None, description="Optional thread ID for conversation continuity"
    )


class HistoryRequest(BaseModel):
    """Request schema for history endpoint."""

    thread_id: Optional[str] = Field(
        default=None, description="Optional thread ID to filter history"
    )
    limit: Optional[int] = Field(default=50, ge=1, le=1000, description="Maximum number of entries to return")

