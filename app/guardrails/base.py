"""Base guardrail interface and types for the agentic framework."""

from abc import ABC, abstractmethod
from enum import Enum
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field


class GuardrailType(Enum):
    """Types of guardrails available in the system."""

    INPUT_SAFETY = "input_safety"
    INPUT_CONTENT_FILTER = "input_content_filter"
    OUTPUT_SAFETY = "output_safety"
    OUTPUT_QUALITY = "output_quality"
    RATE_LIMITING = "rate_limiting"
    ETHICAL_BOUNDARIES = "ethical_boundaries"
    SCOPE_VALIDATION = "scope_validation"


class GuardrailResult(BaseModel):
    """Result of a guardrail check."""

    passed: bool = Field(..., description="Whether the content passed the guardrail")
    score: Optional[float] = Field(default=None, description="Confidence score (0-1)")
    reason: Optional[str] = Field(default=None, description="Reason for failure if not passed")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    guardrail_type: GuardrailType = Field(..., description="Type of guardrail that was checked")


class BaseGuardrail(ABC):
    """Abstract base class for all guardrails.

    Guardrails are safety and quality controls that can be applied to
    agent inputs and outputs. Each guardrail has a specific scope and
    can be configured independently.
    """

    def __init__(self, guardrail_type: GuardrailType, enabled: bool = True):
        """Initialize the guardrail.

        Args:
            guardrail_type: Type of guardrail
            enabled: Whether this guardrail is enabled
        """
        self.guardrail_type = guardrail_type
        self.enabled = enabled

    @abstractmethod
    async def check(self, content: str, context: Optional[Dict[str, Any]] = None) -> GuardrailResult:
        """Check content against this guardrail.

        Args:
            content: Content to check
            context: Optional context information

        Returns:
            GuardrailResult indicating pass/fail status
        """
        pass

    def is_enabled(self) -> bool:
        """Check if this guardrail is enabled."""
        return self.enabled

    def enable(self) -> None:
        """Enable this guardrail."""
        self.enabled = True

    def disable(self) -> None:
        """Disable this guardrail."""
        self.enabled = False


class InputGuardrail(BaseGuardrail):
    """Base class for input guardrails (applied to user inputs)."""

    def __init__(self, enabled: bool = True):
        super().__init__(GuardrailType.INPUT_SAFETY, enabled)


class OutputGuardrail(BaseGuardrail):
    """Base class for output guardrails (applied to agent responses)."""

    def __init__(self, enabled: bool = True):
        super().__init__(GuardrailType.OUTPUT_SAFETY, enabled)
