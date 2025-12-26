"""Token cost response schema."""

from pydantic import BaseModel, Field


class TokenCostResponse(BaseModel):
    """Token cost response schema."""

    input_cost: float = Field(default=0.0, description="Total input cost")
    output_cost: float = Field(default=0.0, description="Total output cost")
    total_cost: float = Field(default=0.0, description="Total cost")

