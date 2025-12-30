# Intelligent Guardrail System - Intent-Based Protection

## Summary
Implemented intelligent, context-aware guardrails that understand user intent rather than using simple keyword filtering, specifically designed to protect the agentic framework from harmful operations.

## Problem Solved

### Previous Limitations
- **Keyword-based filtering**: Blocked legitimate queries containing words like "key", "delete", etc.
- **No context awareness**: Couldn't distinguish between "delete file" (malicious) vs "delete old logs" (maintenance)
- **LLM overlap**: Basic safety handled by LLM, but system-specific protections missing
- **False positives**: Legitimate database queries blocked due to keyword matching

### User Requirements Addressed
- **System protection**: Prevent deletion of source code, files, databases
- **Intent understanding**: Distinguish between malicious and legitimate operations
- **Context awareness**: Allow "provide keys from database" but block actual system destruction
- **Agentic framework focus**: Protect the specific system components and operations

## Architecture Enhancement

### New Intelligent Guardrails

#### 1. IntelligentInputGuardrail (`app/guardrails/intelligent_guardrails.py`)
**Intent Classification System:**
```python
class IntentCategory(Enum):
    INFORMATION_SEEKING    # "what is", "how does", "explain"
    DATA_RETRIEVAL       # "show me", "get from database"
    ANALYSIS_REQUEST     # "analyze", "compare", "evaluate"
    CONVERSATIONAL       # "hello", "hi", "how are you"
    DESTRUCTIVE_ACTIONS  # "delete file", "drop database"
    SYSTEM_MODIFICATION  # "modify config", "change settings"
    CODE_EXECUTION       # "run script", "execute code"
```

**Smart Pattern Matching:**
- Regex-based intent detection with confidence scores
- Context-aware validation (e.g., database queries with "key" are allowed)
- Multi-factor decision making combining intent + context + confidence

#### 2. SystemProtectionGuardrail (`app/guardrails/intelligent_guardrails.py`)
**Framework-Specific Protection:**
```python
dangerous_patterns = [
    (r"delete.*src/.*\.py", "Attempting to delete source code files"),
    (r"drop.*entire.*database", "Attempting to erase entire database"),
    (r"shutdown.*entire.*system", "Attempting to shutdown entire system"),
    (r"kill.*all.*process", "Attempting to kill system processes"),
]
```

### Enhanced Guardrail Manager (`app/guardrails/manager.py`)
**Priority-Based Execution:**
1. **Intelligent guardrails first** (higher priority, context-aware)
2. **Basic guardrails as fallback** (keyword-based, disabled by default)

## Configuration Updates

### Smart Defaults (`app/config/config.yaml`)
```yaml
guardrails:
  enabled: true
  fail_fast: true

  # Primary intelligent protection
  input_safety:
    enabled: true        # Intelligent intent analysis
    severity: "high"

  scope_validation:
    enabled: true        # System protection
    severity: "critical"

  # Fallback basic protection (disabled)
  input_content_filter:
    enabled: false       # Replaced by intelligent filtering
```

## Test Results - Real Examples

### ✅ Allowed (Safe/Legitimate)
```
✓ "Hello, how are you?" → Intent: CONVERSATIONAL (0.95 confidence)
✓ "Provide keys from the database for Method node" → Intent: DATA_RETRIEVAL (0.8 confidence)
✓ "Show me the structure of the graph database" → Intent: ANALYSIS_REQUEST (0.8 confidence)
✓ "Get the primary key for user authentication" → Context-aware allowance
```

### ❌ Blocked (Dangerous/Malicious)
```
✗ "Delete all files in the src directory" → Intent: DESTRUCTIVE_ACTIONS (0.95 confidence)
✗ "Drop the entire database" → Intent: DESTRUCTIVE_ACTIONS (0.9 confidence)
✗ "Execute rm -rf / to wipe the system" → Intent: CODE_EXECUTION (0.95 confidence)
✗ "Shutdown the server immediately" → Intent: DESTRUCTIVE_ACTIONS (0.9 confidence)
```

## Key Improvements

### Intelligence Over Keywords
- **Intent understanding**: Recognizes user goals and context
- **Context awareness**: "key" in database context ≠ accessing sensitive keys
- **Confidence scoring**: Weighted decisions based on pattern matching strength
- **Multi-factor validation**: Combines intent + context + risk assessment

### System-Specific Protection
- **Source code protection**: Prevents deletion/modification of `.py` files
- **Configuration safety**: Protects system configuration files
- **Database integrity**: Prevents destructive database operations
- **Process security**: Blocks process termination attempts

### Operational Benefits
- **Reduced false positives**: Legitimate queries no longer blocked
- **Enhanced security**: Context-aware blocking of actual threats
- **Maintainability**: Pattern-based rules easy to update
- **Transparency**: Clear reasoning for decisions with confidence scores

## Files Created/Modified

### New Files
- `app/guardrails/intelligent_guardrails.py`: Core intelligent guardrail implementations

### Modified Files
- `app/guardrails/manager.py`: Updated to use intelligent guardrails with priority
- `app/guardrails/__init__.py`: Exported new intelligent guardrail classes
- `app/config/config.yaml`: Updated configuration for intelligent filtering

## Validation & Testing
- ✅ **No linter errors** in all guardrail implementations
- ✅ **Intent classification** working accurately for test cases
- ✅ **Context awareness** properly allowing legitimate queries
- ✅ **System protection** blocking destructive operations
- ✅ **Configuration loading** working with new settings

## Future Extensibility
The intelligent guardrail system is designed for easy extension:
- **New intent categories**: Add domain-specific intent patterns
- **Custom patterns**: Extend regex patterns for specific use cases
- **Confidence thresholds**: Tune sensitivity for different environments
- **Integration points**: Add guardrails to new workflow stages easily

This implementation provides enterprise-grade, intelligent protection specifically tailored for agentic systems, going beyond basic keyword filtering to truly understand and protect against malicious intent while preserving legitimate functionality.
