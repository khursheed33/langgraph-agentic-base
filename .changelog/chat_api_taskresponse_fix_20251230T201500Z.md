# Chat API TaskResponse Fix - Pydantic Model Conversion

## Summary
Fixed chat API error where TaskStatusInfo model was being unpacked directly instead of converting to dictionary first.

## Issue
The chat API was failing with error:
```
ERROR - Chat error: app.api.schemas.task_response.TaskResponse() argument after ** must be a mapping, not TaskStatusInfo
```

## Root Cause
After refactoring, `get_current_task()` returns a `TaskStatusInfo` Pydantic model, but the chat API was trying to unpack it directly with `TaskResponse(**current_task)`. The `**` operator expects a dictionary/mapping, not a Pydantic model.

## Fix Applied

### Fixed TaskResponse Creation (app/api/v1/chat.py)
```python
# Before (incorrect - unpacking Pydantic model directly)
current_task=TaskResponse(**current_task) if current_task else None,

# After (correct - convert model to dict first)
current_task=TaskResponse(**current_task.model_dump()) if current_task else None,
```

## Files Modified
- `app/api/v1/chat.py`: Fixed TaskResponse creation to use `.model_dump()` on TaskStatusInfo

## Validation
- ✅ No linter errors
- ✅ TaskStatusInfo to TaskResponse conversion works correctly
- ✅ Proper use of Pydantic V2 `.model_dump()` method
- ✅ Chat API should now handle current task information without errors

## Expected Result
Chat API responses should now properly include current task information in the status object without throwing unpacking errors.
