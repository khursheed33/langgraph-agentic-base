"""Token information response schema."""

from pydantic import BaseModel, Field

from app.api.schemas.token_cost_response import TokenCostResponse
from app.api.schemas.token_usage_response import TokenUsageResponse


class TokenInfoResponse(BaseModel):
    """Token information response schema."""

    usage: TokenUsageResponse = Field(default_factory=TokenUsageResponse, description="Token usage")
    cost: TokenCostResponse = Field(default_factory=TokenCostResponse, description="Token cost")

