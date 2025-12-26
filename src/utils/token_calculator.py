"""Utility for calculating token usage and costs from LLM responses."""

from typing import TYPE_CHECKING, Any, Optional

from pydantic import BaseModel, Field

from src.utils.logger import logger
from src.utils.settings import settings

if TYPE_CHECKING:
    from src.models.workflow_state import UsageStats


class TokenUsage(BaseModel):
    """Token usage information."""

    input_tokens: int = Field(default=0, description="Number of input tokens")
    output_tokens: int = Field(default=0, description="Number of output tokens")
    total_tokens: int = Field(default=0, description="Total number of tokens")

    def __add__(self, other: "TokenUsage") -> "TokenUsage":
        """Add two TokenUsage objects together."""
        return TokenUsage(
            input_tokens=self.input_tokens + other.input_tokens,
            output_tokens=self.output_tokens + other.output_tokens,
            total_tokens=self.total_tokens + other.total_tokens,
        )


class TokenCost(BaseModel):
    """Token cost information."""

    input_cost: float = Field(default=0.0, description="Cost for input tokens")
    output_cost: float = Field(default=0.0, description="Cost for output tokens")
    total_cost: float = Field(default=0.0, description="Total cost")

    def __add__(self, other: "TokenCost") -> "TokenCost":
        """Add two TokenCost objects together."""
        return TokenCost(
            input_cost=self.input_cost + other.input_cost,
            output_cost=self.output_cost + other.output_cost,
            total_cost=self.total_cost + other.total_cost,
        )


class TokenInfo(BaseModel):
    """Complete token information including usage and cost."""

    usage: TokenUsage = Field(default_factory=TokenUsage, description="Token usage")
    cost: TokenCost = Field(default_factory=TokenCost, description="Token cost")

    def __add__(self, other: "TokenInfo") -> "TokenInfo":
        """Add two TokenInfo objects together."""
        return TokenInfo(
            usage=self.usage + other.usage,
            cost=self.cost + other.cost,
        )


# Model pricing per 1M tokens (input, output)
# Groq pricing is typically free or very low cost
# These are approximate values - adjust based on actual pricing
MODEL_PRICING: dict[str, tuple[float, float]] = {
    # Groq models (approximate - Groq is typically free tier)
    "llama-3.1-70b-versatile": (0.0, 0.0),  # Free tier
    "llama-3.1-8b-instant": (0.0, 0.0),  # Free tier
    "mixtral-8x7b-32768": (0.0, 0.0),  # Free tier
    # OpenAI models (per 1M tokens)
    "gpt-4": (30.0, 60.0),
    "gpt-4-turbo": (10.0, 30.0),
    "gpt-3.5-turbo": (0.5, 1.5),
    # Anthropic models (per 1M tokens)
    "claude-3-opus": (15.0, 75.0),
    "claude-3-sonnet": (3.0, 15.0),
    "claude-3-haiku": (0.25, 1.25),
}


def get_model_pricing(model_name: str) -> tuple[float, float]:
    """Get pricing for a model (input_cost_per_1M, output_cost_per_1M).
    
    Args:
        model_name: Name of the model.
        
    Returns:
        Tuple of (input_cost_per_1M_tokens, output_cost_per_1M_tokens).
    """
    # Try exact match first
    if model_name in MODEL_PRICING:
        return MODEL_PRICING[model_name]
    
    # Try partial match (e.g., "gpt-4" matches "gpt-4-turbo")
    for key, value in MODEL_PRICING.items():
        if key.lower() in model_name.lower() or model_name.lower() in key.lower():
            return value
    
    # Default to free (Groq models)
    logger.warning(f"Unknown model pricing for {model_name}, defaulting to free")
    return (0.0, 0.0)


def extract_token_usage_from_response(response: Any) -> Optional[TokenUsage]:
    """Extract token usage from LLM response.
    
    Args:
        response: LLM response object (LangChain BaseMessage or similar).
        
    Returns:
        TokenUsage object if found, None otherwise.
    """
    try:
        # LangChain responses typically have response_metadata
        if hasattr(response, "response_metadata"):
            metadata = response.response_metadata
            if metadata and isinstance(metadata, dict):
                token_usage = metadata.get("token_usage") or metadata.get("usage")
                if token_usage:
                    if isinstance(token_usage, dict):
                        input_tokens = token_usage.get("prompt_tokens") or token_usage.get("input_tokens", 0)
                        output_tokens = token_usage.get("completion_tokens") or token_usage.get("output_tokens", 0)
                        total_tokens = token_usage.get("total_tokens", input_tokens + output_tokens)
                        return TokenUsage(
                            input_tokens=input_tokens,
                            output_tokens=output_tokens,
                            total_tokens=total_tokens,
                        )
        
        # Try direct attributes
        if hasattr(response, "usage"):
            usage = response.usage
            if isinstance(usage, dict):
                input_tokens = usage.get("prompt_tokens") or usage.get("input_tokens", 0)
                output_tokens = usage.get("completion_tokens") or usage.get("output_tokens", 0)
                total_tokens = usage.get("total_tokens", input_tokens + output_tokens)
                return TokenUsage(
                    input_tokens=input_tokens,
                    output_tokens=output_tokens,
                    total_tokens=total_tokens,
                )
        
        # Try response_metadata directly on response
        if hasattr(response, "response_metadata"):
            metadata = response.response_metadata
            if isinstance(metadata, dict):
                input_tokens = metadata.get("prompt_tokens") or metadata.get("input_tokens", 0)
                output_tokens = metadata.get("completion_tokens") or metadata.get("output_tokens", 0)
                total_tokens = metadata.get("total_tokens", input_tokens + output_tokens)
                if input_tokens > 0 or output_tokens > 0:
                    return TokenUsage(
                        input_tokens=input_tokens,
                        output_tokens=output_tokens,
                        total_tokens=total_tokens,
                    )
        
    except Exception as e:
        logger.debug(f"Failed to extract token usage from response: {e}")
    
    return None


def calculate_token_cost(token_usage: TokenUsage, model_name: str) -> TokenCost:
    """Calculate cost for token usage.
    
    Args:
        token_usage: TokenUsage object.
        model_name: Name of the model used.
        
    Returns:
        TokenCost object.
    """
    input_cost_per_1M, output_cost_per_1M = get_model_pricing(model_name)
    
    input_cost = (token_usage.input_tokens / 1_000_000) * input_cost_per_1M
    output_cost = (token_usage.output_tokens / 1_000_000) * output_cost_per_1M
    total_cost = input_cost + output_cost
    
    return TokenCost(
        input_cost=input_cost,
        output_cost=output_cost,
        total_cost=total_cost,
    )


def get_token_info_from_response(response: Any, model_name: Optional[str] = None) -> TokenInfo:
    """Get complete token information from LLM response.
    
    Args:
        response: LLM response object.
        model_name: Optional model name. If not provided, uses settings.GROQ_MODEL.
        
    Returns:
        TokenInfo object with usage and cost.
    """
    if model_name is None:
        model_name = settings.GROQ_MODEL
    
    token_usage = extract_token_usage_from_response(response)
    if token_usage is None:
        token_usage = TokenUsage()
    
    token_cost = calculate_token_cost(token_usage, model_name)
    
    return TokenInfo(usage=token_usage, cost=token_cost)


def aggregate_token_info(token_infos: list[TokenInfo]) -> TokenInfo:
    """Aggregate multiple TokenInfo objects into one.
    
    Args:
        token_infos: List of TokenInfo objects.
        
    Returns:
        Aggregated TokenInfo object.
    """
    if not token_infos:
        return TokenInfo()
    
    result = token_infos[0]
    for info in token_infos[1:]:
        result = result + info
    
    return result


def track_token_usage(response: Any, usage_stats: Any, model_name: Optional[str] = None) -> None:
    """Track token usage from LLM response and update usage_stats.
    
    Args:
        response: LLM response object.
        usage_stats: UsageStats object to update.
        model_name: Optional model name. If not provided, uses settings.GROQ_MODEL.
    """
    try:
        token_info = get_token_info_from_response(response, model_name)
        usage_stats.token_stats.add_usage(
            input_tokens=token_info.usage.input_tokens,
            output_tokens=token_info.usage.output_tokens,
            input_cost=token_info.cost.input_cost,
            output_cost=token_info.cost.output_cost,
        )
        logger.debug(
            f"Tracked tokens: input={token_info.usage.input_tokens}, "
            f"output={token_info.usage.output_tokens}, "
            f"cost=${token_info.cost.total_cost:.6f}"
        )
    except Exception as e:
        logger.warning(f"Failed to track token usage: {e}")

