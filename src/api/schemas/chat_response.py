"""Chat response schema."""

from typing import Any, Optional

from pydantic import BaseModel, Field

from src.api.schemas.status_response import StatusResponse
from src.api.schemas.token_info_response import TokenInfoResponse


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

