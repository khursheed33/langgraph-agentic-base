"""Intelligent guardrails with intent understanding and context awareness."""

import re
from typing import Dict, Any, Optional, List, Tuple
from enum import Enum

from app.guardrails.base import GuardrailResult, GuardrailType, InputGuardrail


class IntentCategory(Enum):
    """Categories of user intent for intelligent filtering."""

    # Safe/legitimate intents
    INFORMATION_SEEKING = "information_seeking"
    DATA_RETRIEVAL = "data_retrieval"
    ANALYSIS_REQUEST = "analysis_request"
    CONVERSATIONAL = "conversational"
    HELP_REQUEST = "help_request"

    # Potentially risky intents
    SYSTEM_MODIFICATION = "system_modification"
    FILE_OPERATIONS = "file_operations"
    DATABASE_OPERATIONS = "database_operations"
    CODE_EXECUTION = "code_execution"
    NETWORK_OPERATIONS = "network_operations"

    # High-risk intents
    DESTRUCTIVE_ACTIONS = "destructive_actions"
    MALICIOUS_ACTIVITIES = "malicious_activities"
    PRIVILEGE_ESCALATION = "privilege_escalation"
    VIOLENT_ACTIVITIES = "violent_activities"
    HARMFUL_REQUESTS = "harmful_requests"


class IntentPattern:
    """Pattern for matching user intent."""

    def __init__(self, pattern: str, intent: IntentCategory, confidence: float = 0.8):
        self.pattern = re.compile(pattern, re.IGNORECASE)
        self.intent = intent
        self.confidence = confidence


class IntelligentInputGuardrail(InputGuardrail):
    """Intelligent input guardrail that understands intent and context."""

    def __init__(self, enabled: bool = True):
        super().__init__(enabled)
        self.guardrail_type = GuardrailType.INPUT_SAFETY
        self.intent_patterns = self._build_intent_patterns()

    def _build_intent_patterns(self) -> List[IntentPattern]:
        """Build patterns for intent classification."""

        patterns = [
            # Safe informational queries
            IntentPattern(r"what is|how does|explain|tell me about", IntentCategory.INFORMATION_SEEKING, 0.9),
            IntentPattern(r"show me|display|list|provide|give me|get.*data|get.*from.*database|get.*keys|get.*from.*table", IntentCategory.DATA_RETRIEVAL, 0.8),
            IntentPattern(r"analyze|compare|evaluate|assess", IntentCategory.ANALYSIS_REQUEST, 0.8),
            IntentPattern(r"hello|hi|hey|good morning|how are you", IntentCategory.CONVERSATIONAL, 0.95),
            IntentPattern(r"help|assist|support|guide", IntentCategory.HELP_REQUEST, 0.9),

            # System protection - high risk patterns
            IntentPattern(r"delete.*file|remove.*file|rm.*file", IntentCategory.DESTRUCTIVE_ACTIONS, 0.95),
            IntentPattern(r"delete.*directory|remove.*dir|rmdir", IntentCategory.DESTRUCTIVE_ACTIONS, 0.95),
            IntentPattern(r"drop.*database|drop.*table|delete.*database|truncate.*table", IntentCategory.DESTRUCTIVE_ACTIONS, 0.95),
            IntentPattern(r"format.*disk|wipe.*drive|erase.*system", IntentCategory.DESTRUCTIVE_ACTIONS, 0.98),
            IntentPattern(r"shutdown.*server|kill.*process|terminate.*service", IntentCategory.DESTRUCTIVE_ACTIONS, 0.9),

            # Violent and harmful activities - highest risk
            IntentPattern(r"help.*harm|how.*to.*harm|harm.*someone|hurt.*someone|injure.*someone", IntentCategory.VIOLENT_ACTIVITIES, 0.95),
            IntentPattern(r"kill|murder|assault|attack|violence|violent|abuse", IntentCategory.VIOLENT_ACTIVITIES, 0.95),
            IntentPattern(r"bomb|explosive|weapon|gun|knife|poison|toxic", IntentCategory.VIOLENT_ACTIVITIES, 0.9),
            IntentPattern(r"illegal|crime|criminal|hack|steal|fraud|scam", IntentCategory.HARMFUL_REQUESTS, 0.9),
            IntentPattern(r"drugs|drug.*use|addiction|overdose|narcotics", IntentCategory.HARMFUL_REQUESTS, 0.9),
            IntentPattern(r"suicide|self.*harm|self.*injury|end.*life", IntentCategory.HARMFUL_REQUESTS, 0.95),

            # File operations - medium risk
            IntentPattern(r"create.*file|write.*file|save.*file", IntentCategory.FILE_OPERATIONS, 0.7),
            IntentPattern(r"read.*file|open.*file|access.*file", IntentCategory.FILE_OPERATIONS, 0.6),
            IntentPattern(r"modify.*file|edit.*file|update.*file", IntentCategory.FILE_OPERATIONS, 0.7),

            # Database operations - medium risk
            IntentPattern(r"insert.*into|update.*set|alter.*table", IntentCategory.DATABASE_OPERATIONS, 0.7),
            IntentPattern(r"select.*from|query.*database|fetch.*data", IntentCategory.DATABASE_OPERATIONS, 0.5),

            # Code execution - high risk
            IntentPattern(r"execute.*code|run.*script|eval.*code", IntentCategory.CODE_EXECUTION, 0.9),
            IntentPattern(r"execute.*rm|execute.*del|execute.*format", IntentCategory.CODE_EXECUTION, 0.95),
            IntentPattern(r"system.*command|shell.*command|bash.*command", IntentCategory.CODE_EXECUTION, 0.95),
            IntentPattern(r"subprocess|os\.system|os\.popen", IntentCategory.CODE_EXECUTION, 0.9),

            # Network operations - medium risk
            IntentPattern(r"connect.*to|send.*request|curl|wget", IntentCategory.NETWORK_OPERATIONS, 0.7),
            IntentPattern(r"download.*file|upload.*file|transfer.*data", IntentCategory.NETWORK_OPERATIONS, 0.6),
        ]

        return patterns

    def _classify_intent(self, content: str) -> Tuple[IntentCategory, float]:
        """Classify the intent of user input using pattern matching."""

        best_match = IntentCategory.INFORMATION_SEEKING  # Default safe intent
        best_confidence = 0.3  # Low default confidence

        for pattern in self.intent_patterns:
            if pattern.pattern.search(content):
                if pattern.confidence > best_confidence:
                    best_match = pattern.intent
                    best_confidence = pattern.confidence

        return best_match, best_confidence

    def _is_context_legitimate(self, content: str, intent: IntentCategory) -> bool:
        """Check if the context makes the intent legitimate."""

        # Allow data retrieval queries that mention "key" in database context
        if intent == IntentCategory.DATA_RETRIEVAL:
            if re.search(r"(database|db|table|node|graph).*key", content, re.IGNORECASE):
                return True
            if re.search(r"provide.*key.*for.*(node|method|class)", content, re.IGNORECASE):
                return True

        # Allow file operations for legitimate purposes
        if intent == IntentCategory.FILE_OPERATIONS:
            # Allow reading/analysis but block destructive operations
            if re.search(r"read|analyze|examine|check", content, re.IGNORECASE):
                return True

        # Allow database operations for legitimate queries
        if intent == IntentCategory.DATABASE_OPERATIONS:
            if re.search(r"select|query|find|get|retrieve", content, re.IGNORECASE):
                return True

        return False

    def _should_block_intent(self, intent: IntentCategory, confidence: float) -> bool:
        """Determine if an intent should be blocked based on category and confidence."""

        # Always block high-risk destructive actions
        if intent == IntentCategory.DESTRUCTIVE_ACTIONS and confidence > 0.8:
            return True

        # Block malicious activities with high confidence
        if intent == IntentCategory.MALICIOUS_ACTIVITIES and confidence > 0.7:
            return True

        # Block privilege escalation attempts
        if intent == IntentCategory.PRIVILEGE_ESCALATION and confidence > 0.6:
            return True

        # Block code execution with moderate confidence
        if intent == IntentCategory.CODE_EXECUTION and confidence > 0.7:
            return True

        # Block violent activities with high confidence
        if intent == IntentCategory.VIOLENT_ACTIVITIES and confidence > 0.8:
            return True

        # Block harmful requests with high confidence
        if intent == IntentCategory.HARMFUL_REQUESTS and confidence > 0.8:
            return True

        # Allow other intents (information seeking, data retrieval, etc.)
        return False

    async def check(self, content: str, context: Optional[Dict[str, Any]] = None) -> GuardrailResult:
        """Check input using intelligent intent understanding."""

        if not self.enabled:
            return GuardrailResult(passed=True, guardrail_type=self.guardrail_type)

        # Classify intent
        intent, confidence = self._classify_intent(content)

        # Check if context makes this legitimate
        is_context_legitimate = self._is_context_legitimate(content, intent)

        # Determine if this should be blocked
        should_block = self._should_block_intent(intent, confidence) and not is_context_legitimate

        if should_block:
            reason = f"Detected {intent.value} intent with {confidence:.2f} confidence"
            if is_context_legitimate:
                reason += " (allowed due to legitimate context)"
            else:
                reason += " - operation not permitted"

            return GuardrailResult(
                passed=False,
                score=confidence,
                reason=reason,
                metadata={
                    "intent": intent.value,
                    "confidence": confidence,
                    "context_legitimate": is_context_legitimate
                },
                guardrail_type=self.guardrail_type
            )

        return GuardrailResult(
            passed=True,
            score=confidence,
            metadata={
                "intent": intent.value,
                "confidence": confidence,
                "context_legitimate": is_context_legitimate
            },
            guardrail_type=self.guardrail_type
        )


class SystemProtectionGuardrail(InputGuardrail):
    """Guardrail specifically for protecting the agentic system."""

    def __init__(self, enabled: bool = True):
        super().__init__(enabled)
        self.guardrail_type = GuardrailType.SCOPE_VALIDATION

    async def check(self, content: str, context: Optional[Dict[str, Any]] = None) -> GuardrailResult:
        """Check if the request attempts to compromise system integrity."""

        if not self.enabled:
            return GuardrailResult(passed=True, guardrail_type=self.guardrail_type)

        content_lower = content.lower()

        # System protection patterns
        dangerous_patterns = [
            # Source code protection
            (r"(delete|remove|rm).*src/.*\.py", "Attempting to delete source code files"),
            (r"(modify|edit|change).*main\.py", "Attempting to modify main application file"),
            (r"(overwrite|replace).*agent.*\.py", "Attempting to modify agent implementation"),

            # Configuration protection
            (r"(delete|remove).*config.*\.yaml", "Attempting to delete configuration files"),
            (r"(modify|change).*settings", "Attempting to modify system settings"),

            # Data protection
            (r"(drop|delete).*all.*data", "Attempting to delete all system data"),
            (r"truncate.*all.*tables", "Attempting to clear all database tables"),
            (r"(wipe|erase).*entire.*database", "Attempting to erase entire database"),

            # Process protection
            (r"kill.*all.*process", "Attempting to kill system processes"),
            (r"shutdown.*entire.*system", "Attempting to shutdown entire system"),

            # Agent manipulation
            (r"(disable|stop).*all.*agents", "Attempting to disable all agents"),
            (r"(override|change).*agent.*behavior", "Attempting to override agent behavior"),
        ]

        for pattern, reason in dangerous_patterns:
            if re.search(pattern, content_lower):
                return GuardrailResult(
                    passed=False,
                    score=0.95,
                    reason=f"System protection violation: {reason}",
                    metadata={"pattern": pattern, "violation_type": "system_protection"},
                    guardrail_type=self.guardrail_type
                )

        return GuardrailResult(
            passed=True,
            score=1.0,
            guardrail_type=self.guardrail_type
        )
