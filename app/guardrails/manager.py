"""Guardrail manager for orchestrating multiple guardrails."""

import asyncio
from typing import Dict, Any, List, Optional

from app.guardrails.base import GuardrailResult, GuardrailType, BaseGuardrail
from app.guardrails.config import GuardrailConfig
from app.guardrails.input_guardrails import (
    ContentFilterGuardrail,
    InputSafetyGuardrail,
    EthicalBoundariesGuardrail
)
from app.guardrails.intelligent_guardrails import (
    IntelligentInputGuardrail,
    SystemProtectionGuardrail
)
from app.guardrails.output_guardrails import (
    OutputSafetyGuardrail,
    OutputQualityGuardrail,
    ScopeValidationGuardrail
)


class GuardrailManager:
    """Manager for coordinating multiple guardrails.

    This class orchestrates the execution of various guardrails based on
    the configuration, providing a clean interface for input/output validation.
    """

    def __init__(self, config: GuardrailConfig):
        """Initialize the guardrail manager.

        Args:
            config: Guardrail configuration
        """
        self.config = config
        self.guardrails: Dict[GuardrailType, BaseGuardrail] = {}

        # Initialize guardrails based on configuration
        self._initialize_guardrails()

    def _initialize_guardrails(self) -> None:
        """Initialize all guardrails based on configuration."""
        # Intelligent input guardrails (higher priority)
        if self.config.is_guardrail_enabled(GuardrailType.INPUT_SAFETY):
            settings = self.config.get_guardrail_settings(GuardrailType.INPUT_SAFETY)
            self.guardrails[GuardrailType.INPUT_SAFETY] = IntelligentInputGuardrail(
                enabled=settings.enabled if settings else True
            )

        if self.config.is_guardrail_enabled(GuardrailType.SCOPE_VALIDATION):
            settings = self.config.get_guardrail_settings(GuardrailType.SCOPE_VALIDATION)
            self.guardrails[GuardrailType.SCOPE_VALIDATION] = SystemProtectionGuardrail(
                enabled=settings.enabled if settings else True
            )

        # Basic input guardrails (fallback)
        if self.config.is_guardrail_enabled(GuardrailType.INPUT_CONTENT_FILTER):
            settings = self.config.get_guardrail_settings(GuardrailType.INPUT_CONTENT_FILTER)
            self.guardrails[GuardrailType.INPUT_CONTENT_FILTER] = ContentFilterGuardrail(
                blocked_keywords=self.config.blocked_keywords,
                enabled=settings.enabled if settings else True
            )

        if self.config.is_guardrail_enabled(GuardrailType.ETHICAL_BOUNDARIES):
            settings = self.config.get_guardrail_settings(GuardrailType.ETHICAL_BOUNDARIES)
            self.guardrails[GuardrailType.ETHICAL_BOUNDARIES] = EthicalBoundariesGuardrail(
                enabled=settings.enabled if settings else True
            )

        # Output guardrails
        if self.config.is_guardrail_enabled(GuardrailType.OUTPUT_SAFETY):
            settings = self.config.get_guardrail_settings(GuardrailType.OUTPUT_SAFETY)
            self.guardrails[GuardrailType.OUTPUT_SAFETY] = OutputSafetyGuardrail(
                max_length=self.config.max_output_length,
                enabled=settings.enabled if settings else True
            )

        if self.config.is_guardrail_enabled(GuardrailType.OUTPUT_QUALITY):
            settings = self.config.get_guardrail_settings(GuardrailType.OUTPUT_QUALITY)
            self.guardrails[GuardrailType.OUTPUT_QUALITY] = OutputQualityGuardrail(
                enabled=settings.enabled if settings else True
            )

        if self.config.is_guardrail_enabled(GuardrailType.SCOPE_VALIDATION):
            settings = self.config.get_guardrail_settings(GuardrailType.SCOPE_VALIDATION)
            self.guardrails[GuardrailType.SCOPE_VALIDATION] = ScopeValidationGuardrail(
                enabled=settings.enabled if settings else True
            )

    async def check_input(self, content: str, context: Optional[Dict[str, Any]] = None) -> List[GuardrailResult]:
        """Check input content against all enabled input guardrails.

        Args:
            content: Input content to check
            context: Optional context information

        Returns:
            List of guardrail results
        """
        if not self.config.enabled:
            return []

        results = []
        input_guardrail_types = [
            GuardrailType.INPUT_SAFETY,
            GuardrailType.INPUT_CONTENT_FILTER,
            GuardrailType.ETHICAL_BOUNDARIES
        ]

        for guardrail_type in input_guardrail_types:
            if guardrail_type in self.guardrails:
                guardrail = self.guardrails[guardrail_type]
                if guardrail.is_enabled():
                    result = await guardrail.check(content, context)
                    results.append(result)

                    # Stop on first failure if fail_fast is enabled
                    if not result.passed and self.config.fail_fast:
                        break

        return results

    async def check_output(self, content: str, context: Optional[Dict[str, Any]] = None) -> List[GuardrailResult]:
        """Check output content against all enabled output guardrails.

        Args:
            content: Output content to check
            context: Optional context information

        Returns:
            List of guardrail results
        """
        if not self.config.enabled:
            return []

        results = []
        output_guardrail_types = [
            GuardrailType.OUTPUT_SAFETY,
            GuardrailType.OUTPUT_QUALITY,
            GuardrailType.SCOPE_VALIDATION
        ]

        for guardrail_type in output_guardrail_types:
            if guardrail_type in self.guardrails:
                guardrail = self.guardrails[guardrail_type]
                if guardrail.is_enabled():
                    result = await guardrail.check(content, context)
                    results.append(result)

                    # Stop on first failure if fail_fast is enabled
                    if not result.passed and self.config.fail_fast:
                        break

        return results

    def get_enabled_guardrails(self) -> List[GuardrailType]:
        """Get all enabled guardrail types."""
        return [gt for gt in self.guardrails.keys() if self.guardrails[gt].is_enabled()]

    def enable_guardrail(self, guardrail_type: GuardrailType) -> None:
        """Enable a specific guardrail."""
        if guardrail_type in self.guardrails:
            self.guardrails[guardrail_type].enable()

    def disable_guardrail(self, guardrail_type: GuardrailType) -> None:
        """Disable a specific guardrail."""
        if guardrail_type in self.guardrails:
            self.guardrails[guardrail_type].disable()

    def update_config(self, config: GuardrailConfig) -> None:
        """Update guardrail configuration and reinitialize guardrails."""
        self.config = config
        self._initialize_guardrails()
