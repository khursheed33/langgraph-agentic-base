# Circular Import Fix - Guardrail Configuration

## Summary
Fixed circular import issue between `app.config` and `app.guardrails` modules.

## Issue
The application was failing to start with:
```
ImportError: cannot import name 'load_guardrail_config' from partially initialized module 'app.config'
```

## Root Cause
Circular import dependency:
1. `app/config/__init__.py` imported `GuardrailConfig` from `app.guardrails.config`
2. `app/guardrails/__init__.py` imported `load_guardrail_config` from `app.config`
3. This created a circular dependency preventing module initialization

## Fix Applied

### Modified `app/guardrails/__init__.py`
**Before:**
```python
from app.config import load_guardrail_config
# ...
__all__ = [
    "GuardrailResult",
    "GuardrailType",
    "GuardrailConfig",
    "GuardrailManager",
    "load_guardrail_config",  # <-- Circular import
]
```

**After:**
```python
# Removed: from app.config import load_guardrail_config
# ...
__all__ = [
    "GuardrailResult",
    "GuardrailType",
    "GuardrailConfig",
    "GuardrailManager",
    # Removed: "load_guardrail_config",
]
```

## Resolution Strategy
- **Eliminated circular dependency** by removing the import from guardrails to config
- **Configuration loading** now happens at the point of use (workflow service, etc.)
- **Maintains functionality** while fixing the import structure
- **Follows clean architecture** principles with proper separation of concerns

## Files Modified
- `app/guardrails/__init__.py`: Removed circular import dependency

## Verification
- ✅ Application starts without circular import errors
- ✅ Guardrail functionality preserved
- ✅ Configuration loading still works in workflow service
- ✅ No linter errors introduced

## Impact
- **Application startup**: Now works correctly
- **API endpoints**: Can be imported and used
- **Guardrail system**: Fully functional
- **Code maintainability**: Better separation of concerns
