# Chat API ToolStatus Fix - Pydantic Model Access

## Summary
Fixed chat API error where ToolStatus objects were being accessed as dictionaries instead of Pydantic models.

## Issue
The chat API was failing with error:
```
ERROR - Chat error: 'ToolStatus' object has no attribute 'get'
```

## Root Cause
After refactoring to use Pydantic models, `get_all_tool_status()` returns `list[ToolStatus]` (models), but the chat API was trying to call `.get("usage_count", 0)` on these models, treating them like dictionaries.

## Fixes Applied

### 1. Fixed Tool Status Filtering (app/api/v1/chat.py)
```python
# Before (incorrect - calling .get() on Pydantic model)
if tool_status.get("usage_count", 0) > 0

# After (correct - accessing model attribute)
if tool_status.usage_count > 0
```

### 2. Fixed ToolStatusResponse Creation (app/api/v1/chat.py)
```python
# Before (deprecated Pydantic V1 method)
ToolStatusResponse(**tool_status.dict())

# After (Pydantic V2 method)
ToolStatusResponse(**tool_status.model_dump())
```

## Files Modified
- `app/api/v1/chat.py`: Fixed ToolStatus model access and response creation

## Validation
- ✅ No linter errors
- ✅ ToolStatus model filtering works correctly
- ✅ ToolStatusResponse creation uses modern Pydantic V2 API
- ✅ Chat API should now return proper JSON without errors

## Expected Result
Chat API responses should now include proper tool status information without throwing "'ToolStatus' object has no attribute 'get'" errors.
