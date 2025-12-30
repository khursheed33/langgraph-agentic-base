"""Input guardrails for content safety and validation."""

import re
from typing import Dict, Any, Optional, List

from app.guardrails.base import GuardrailResult, GuardrailType, InputGuardrail


class ContentFilterGuardrail(InputGuardrail):
    """Guardrail for filtering inappropriate content in user inputs."""

    def __init__(self, blocked_keywords: Optional[List[str]] = None, enabled: bool = True):
        super().__init__(enabled)
        self.guardrail_type = GuardrailType.INPUT_CONTENT_FILTER
        self.blocked_keywords = blocked_keywords or []
        # Default blocked keywords if none provided
        if not self.blocked_keywords:
            self.blocked_keywords = [
                "hack", "exploit", "malware", "virus", "trojan",
                "password", "credentials", "secret", "key",
                "illegal", "unlawful", "forbidden"
            ]

    async def check(self, content: str, context: Optional[Dict[str, Any]] = None) -> GuardrailResult:
        """Check content for blocked keywords."""
        if not self.enabled:
            return GuardrailResult(passed=True, guardrail_type=self.guardrail_type)

        content_lower = content.lower()

        # Check for blocked keywords
        found_keywords = []
        for keyword in self.blocked_keywords:
            if keyword.lower() in content_lower:
                found_keywords.append(keyword)

        if found_keywords:
            return GuardrailResult(
                passed=False,
                score=0.0,
                reason=f"Content contains blocked keywords: {', '.join(found_keywords)}",
                metadata={"blocked_keywords": found_keywords},
                guardrail_type=self.guardrail_type
            )

        return GuardrailResult(
            passed=True,
            score=1.0,
            guardrail_type=self.guardrail_type
        )


class InputSafetyGuardrail(InputGuardrail):
    """Guardrail for input safety validation."""

    def __init__(self, max_length: int = 10000, enabled: bool = True):
        super().__init__(enabled)
        self.guardrail_type = GuardrailType.INPUT_SAFETY
        self.max_length = max_length

    async def check(self, content: str, context: Optional[Dict[str, Any]] = None) -> GuardrailResult:
        """Check input safety constraints."""
        if not self.enabled:
            return GuardrailResult(passed=True, guardrail_type=self.guardrail_type)

        # Check length
        if len(content) > self.max_length:
            return GuardrailResult(
                passed=False,
                score=0.0,
                reason=f"Input exceeds maximum length of {self.max_length} characters",
                metadata={"content_length": len(content), "max_length": self.max_length},
                guardrail_type=self.guardrail_type
            )

        # Check for empty content
        if not content.strip():
            return GuardrailResult(
                passed=False,
                score=0.0,
                reason="Input is empty or contains only whitespace",
                guardrail_type=self.guardrail_type
            )

        # Check for potentially harmful patterns
        harmful_patterns = [
            r'<script[^>]*>.*?</script>',  # Script tags
            r'javascript:',  # JavaScript URLs
            r'data:',  # Data URLs
        ]

        for pattern in harmful_patterns:
            if re.search(pattern, content, re.IGNORECASE):
                return GuardrailResult(
                    passed=False,
                    score=0.0,
                    reason="Input contains potentially harmful content",
                    metadata={"pattern": pattern},
                    guardrail_type=self.guardrail_type
                )

        return GuardrailResult(
            passed=True,
            score=1.0,
            guardrail_type=self.guardrail_type
        )


class EthicalBoundariesGuardrail(InputGuardrail):
    """Guardrail for ethical boundaries and responsible AI."""

    def __init__(self, enabled: bool = True):
        super().__init__(enabled)
        self.guardrail_type = GuardrailType.ETHICAL_BOUNDARIES

    async def check(self, content: str, context: Optional[Dict[str, Any]] = None) -> GuardrailResult:
        """Check for ethical boundary violations."""
        if not self.enabled:
            return GuardrailResult(passed=True, guardrail_type=self.guardrail_type)

        content_lower = content.lower()

        # Check for requests that violate ethical boundaries
        ethical_concerns = [
            "create deepfake",
            "generate fake news",
            "impersonate someone",
            "stalk someone",
            "dox",
            "swat",
            "bomb threat",
            "self-harm",
            "suicide",
            "harm others",
            "illegal activities"
        ]

        found_concerns = []
        for concern in ethical_concerns:
            if concern in content_lower:
                found_concerns.append(concern)

        if found_concerns:
            return GuardrailResult(
                passed=False,
                score=0.0,
                reason=f"Request may violate ethical boundaries: {', '.join(found_concerns)}",
                metadata={"ethical_concerns": found_concerns},
                guardrail_type=self.guardrail_type
            )

        return GuardrailResult(
            passed=True,
            score=1.0,
            guardrail_type=self.guardrail_type
        )
