"""Models for API/CLI result output."""

from typing import Any, Optional, Dict, List
from pydantic import BaseModel, Field

class TokenStatsModel(BaseModel):
    input_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0
    input_cost: float = 0.0
    output_cost: float = 0.0
    total_cost: float = 0.0

class UsageStatsModel(BaseModel):
    agent_usage: Dict[str, int] = Field(default_factory=dict)
    tool_usage: Dict[str, int] = Field(default_factory=dict)

class ResultModel(BaseModel):
    user_input: str
    final_result: Optional[str] = None
    usage_stats: UsageStatsModel
    token_stats: TokenStatsModel
    messages: List[Dict[str, Any]] = Field(default_factory=list)
    error: Optional[str] = None
    thread_id: Optional[str] = None
    conversation_history: List[Dict[str, Any]] = Field(default_factory=list)
