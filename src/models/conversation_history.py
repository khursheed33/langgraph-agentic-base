"""Conversation history models for storing conversation entries."""

from typing import Any

from pydantic import BaseModel, Field


class ConversationEntry(BaseModel):
    """Model for a single conversation history entry."""

    user_input: str = Field(..., description="User input for this conversation turn")
    result: str = Field(..., description="Final result of the conversation turn")
    messages: list[dict[str, Any]] = Field(..., description="Messages exchanged during this turn")
