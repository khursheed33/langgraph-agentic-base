# Async Workflow Service Fix - Chat API Integration

## Summary
Fixed chat API to properly handle async workflow service calls.

## Issue
The chat API was calling the async `run_workflow()` function synchronously, which would cause runtime errors.

## Fix Applied

### Modified `app/api/v1/chat.py`
**Before:**
```python
# Run workflow
result = run_workflow(request.message, thread_id)
```

**After:**
```python
# Run workflow
result = await run_workflow(request.message, thread_id)
```

## Context
- The workflow service was made async to support guardrail checking operations
- The chat API endpoint was already async (FastAPI requirement)
- The call needed to be updated to use `await` for proper async handling

## Files Modified
- `app/api/v1/chat.py`: Updated workflow service call to be properly awaited

## Verification
- ✅ Chat API now properly awaits async workflow service
- ✅ No linter errors introduced
- ✅ Maintains FastAPI async compatibility
- ✅ Guardrail integration works correctly

## Technical Details
- **Async/Await Pattern**: Properly implemented async function calling
- **FastAPI Compatibility**: Maintains async endpoint behavior
- **Guardrail Integration**: Enables proper async guardrail checking in workflow
