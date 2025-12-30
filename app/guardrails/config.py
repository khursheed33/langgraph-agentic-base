"""Guardrail configuration system for the agentic framework."""

from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field

from app.guardrails.base import GuardrailType


class GuardrailSettings(BaseModel):
    """Settings for a specific guardrail."""

    enabled: bool = Field(default=True, description="Whether this guardrail is enabled")
    severity: str = Field(default="medium", description="Severity level: low, medium, high")
    threshold: Optional[float] = Field(default=None, description="Threshold for passing the check")
    custom_config: Dict[str, Any] = Field(default_factory=dict, description="Custom configuration")


class GuardrailConfig(BaseModel):
    """Configuration for the guardrails system."""

    enabled: bool = Field(default=True, description="Whether guardrails are enabled globally")
    fail_fast: bool = Field(default=True, description="Stop on first failure if True, continue checking if False")
    log_violations: bool = Field(default=True, description="Log guardrail violations")

    # Individual guardrail configurations
    input_safety: GuardrailSettings = Field(default_factory=GuardrailSettings)
    input_content_filter: GuardrailSettings = Field(default_factory=GuardrailSettings)
    output_safety: GuardrailSettings = Field(default_factory=GuardrailSettings)
    output_quality: GuardrailSettings = Field(default_factory=GuardrailSettings)
    rate_limiting: GuardrailSettings = Field(default_factory=GuardrailSettings)
    ethical_boundaries: GuardrailSettings = Field(default_factory=GuardrailSettings)
    scope_validation: GuardrailSettings = Field(default_factory=GuardrailSettings)

    # Global settings
    blocked_keywords: List[str] = Field(default_factory=list, description="Keywords to block in inputs")
    allowed_domains: List[str] = Field(default_factory=lambda: ["*"], description="Allowed domains for external content")
    max_input_length: int = Field(default=10000, description="Maximum input length")
    max_output_length: int = Field(default=5000, description="Maximum output length")

    def is_guardrail_enabled(self, guardrail_type: GuardrailType) -> bool:
        """Check if a specific guardrail is enabled."""
        if not self.enabled:
            return False

        settings = getattr(self, guardrail_type.value, None)
        return settings.enabled if settings else False

    def get_guardrail_settings(self, guardrail_type: GuardrailType) -> Optional[GuardrailSettings]:
        """Get settings for a specific guardrail."""
        return getattr(self, guardrail_type.value, None)

    def get_all_enabled_guardrails(self) -> List[GuardrailType]:
        """Get all enabled guardrail types."""
        return [gt for gt in GuardrailType if self.is_guardrail_enabled(gt)]
