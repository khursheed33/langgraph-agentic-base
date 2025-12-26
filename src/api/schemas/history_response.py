"""History response schema."""

from typing import Any

from pydantic import BaseModel, Field


class HistoryResponse(BaseModel):
    """History response schema."""

    thread_id: str = Field(..., description="Thread ID")
    conversation_history: list[dict[str, Any]] = Field(
        ..., description="Conversation history entries"
    )
    total_entries: int = Field(..., description="Total number of entries")

