"""Tool status response schema."""

from pydantic import BaseModel, Field


class ToolStatusResponse(BaseModel):
    """Tool status response schema."""

    tool_name: str = Field(..., description="Tool name")
    usage_count: int = Field(..., description="Number of times tool was used")

