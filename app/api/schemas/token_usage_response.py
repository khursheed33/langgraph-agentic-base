"""Token usage response schema."""

from pydantic import BaseModel, Field


class TokenUsageResponse(BaseModel):
    """Token usage response schema."""

    input_tokens: int = Field(default=0, description="Total input tokens")
    output_tokens: int = Field(default=0, description="Total output tokens")
    total_tokens: int = Field(default=0, description="Total tokens")

