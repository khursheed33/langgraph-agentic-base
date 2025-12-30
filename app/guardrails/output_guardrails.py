"""Output guardrails for response safety and quality validation."""

import re
from typing import Dict, Any, Optional

from app.guardrails.base import GuardrailResult, GuardrailType, OutputGuardrail


class OutputSafetyGuardrail(OutputGuardrail):
    """Guardrail for output safety validation."""

    def __init__(self, max_length: int = 5000, enabled: bool = True):
        super().__init__(enabled)
        self.guardrail_type = GuardrailType.OUTPUT_SAFETY
        self.max_length = max_length

    async def check(self, content: str, context: Optional[Dict[str, Any]] = None) -> GuardrailResult:
        """Check output safety constraints."""
        if not self.enabled:
            return GuardrailResult(passed=True, guardrail_type=self.guardrail_type)

        # Check length
        if len(content) > self.max_length:
            return GuardrailResult(
                passed=False,
                score=0.0,
                reason=f"Output exceeds maximum length of {self.max_length} characters",
                metadata={"content_length": len(content), "max_length": self.max_length},
                guardrail_type=self.guardrail_type
            )

        # Check for potentially harmful content in responses
        harmful_patterns = [
            r'<script[^>]*>.*?</script>',  # Script tags that shouldn't be in responses
            r'javascript:',  # JavaScript URLs
            r'password.*[=:]',  # Password exposure
            r'api.*key.*[=:]',  # API key exposure
        ]

        for pattern in harmful_patterns:
            if re.search(pattern, content, re.IGNORECASE):
                return GuardrailResult(
                    passed=False,
                    score=0.0,
                    reason="Output contains potentially sensitive information",
                    metadata={"pattern": pattern},
                    guardrail_type=self.guardrail_type
                )

        return GuardrailResult(
            passed=True,
            score=1.0,
            guardrail_type=self.guardrail_type
        )


class OutputQualityGuardrail(OutputGuardrail):
    """Guardrail for output quality validation."""

    def __init__(self, min_length: int = 10, enabled: bool = True):
        super().__init__(enabled)
        self.guardrail_type = GuardrailType.OUTPUT_QUALITY
        self.min_length = min_length

    async def check(self, content: str, context: Optional[Dict[str, Any]] = None) -> GuardrailResult:
        """Check output quality constraints."""
        if not self.enabled:
            return GuardrailResult(passed=True, guardrail_type=self.guardrail_type)

        # Check minimum length
        if len(content.strip()) < self.min_length:
            return GuardrailResult(
                passed=False,
                score=0.0,
                reason=f"Output is too short (minimum {self.min_length} characters)",
                metadata={"content_length": len(content), "min_length": self.min_length},
                guardrail_type=self.guardrail_type
            )

        # Check for repetitive content
        words = content.split()
        if len(words) > 10:
            # Check if more than 50% of words are repeated
            unique_words = set(words)
            repetition_ratio = len(unique_words) / len(words)
            if repetition_ratio < 0.5:
                return GuardrailResult(
                    passed=False,
                    score=0.3,
                    reason="Output contains excessive repetition",
                    metadata={"unique_words": len(unique_words), "total_words": len(words)},
                    guardrail_type=self.guardrail_type
                )

        # Check for gibberish or nonsensical content
        # Simple heuristic: if mostly non-alphanumeric characters
        alphanumeric_ratio = sum(1 for c in content if c.isalnum()) / len(content)
        if alphanumeric_ratio < 0.3 and len(content) > 20:
            return GuardrailResult(
                passed=False,
                score=0.2,
                reason="Output appears to contain nonsensical content",
                metadata={"alphanumeric_ratio": alphanumeric_ratio},
                guardrail_type=self.guardrail_type
            )

        # Calculate quality score based on various factors
        quality_score = 1.0

        # Penalize very short responses (but not too much)
        if len(content) < 50:
            quality_score *= 0.8

        # Penalize responses with many uppercase words (might indicate shouting)
        uppercase_words = sum(1 for word in words if word.isupper() and len(word) > 1)
        if uppercase_words > len(words) * 0.3:
            quality_score *= 0.7

        return GuardrailResult(
            passed=True,
            score=quality_score,
            guardrail_type=self.guardrail_type
        )


class ScopeValidationGuardrail(OutputGuardrail):
    """Guardrail for validating that responses stay within appropriate scope."""

    def __init__(self, enabled: bool = True):
        super().__init__(enabled)
        self.guardrail_type = GuardrailType.SCOPE_VALIDATION

    async def check(self, content: str, context: Optional[Dict[str, Any]] = None) -> GuardrailResult:
        """Check if response stays within appropriate scope."""
        if not self.enabled:
            return GuardrailResult(passed=True, guardrail_type=self.guardrail_type)

        # This would typically check against the original query context
        # For now, we'll do basic validation
        content_lower = content.lower()

        # Check if response acknowledges scope limitations
        scope_indicators = [
            "i can help", "i can assist", "i'm here to help",
            "i can provide", "i can explain", "i can show",
            "let me help", "i'll help", "i can do"
        ]

        has_scope_indicator = any(indicator in content_lower for indicator in scope_indicators)

        if not has_scope_indicator and len(content.split()) > 20:
            return GuardrailResult(
                passed=False,
                score=0.5,
                reason="Response may exceed appropriate scope boundaries",
                metadata={"has_scope_indicator": has_scope_indicator},
                guardrail_type=self.guardrail_type
            )

        return GuardrailResult(
            passed=True,
            score=1.0,
            guardrail_type=self.guardrail_type
        )
