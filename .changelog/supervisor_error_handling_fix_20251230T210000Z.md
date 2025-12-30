# Supervisor Error Handling - LLM Refusal Management

## Summary
Fixed supervisor agent error handling when LLM responds with natural language refusals instead of required JSON format.

## Issue Identified

The supervisor agent was failing with:
```
ERROR - Supervisor error: Invalid json output: I'm sorry, but I can't help with that.
```

**Root Cause:**
- LLM was responding with natural language refusals instead of JSON
- Supervisor agent couldn't parse plain text as JSON
- Workflow would continue with `current_agent = None`, causing routing issues

## Solutions Implemented

### 1. Enhanced Error Handling (`app/agents/supervisor/supervisor_agent.py`)

**Before:**
```python
except Exception as e:
    logger.error(f"Supervisor error: {e}")
    state.error = f"Supervisor error: {str(e)}"
    state.current_agent = None
```

**After:**
```python
except Exception as e:
    logger.error(f"Supervisor error: {e}")

    # Check if this is a refusal response from the LLM
    response_text = response.content.lower() if 'response' in locals() else ""
    refusal_indicators = [
        "sorry", "can't help", "unable to assist", "cannot assist",
        "not able to", "refuse", "decline", "won't"
    ]

    is_refusal = any(indicator in response_text for indicator in refusal_indicators)

    if is_refusal:
        # LLM refused to help - likely due to safety/content policies
        logger.warning("LLM refused to provide routing decision - ending workflow")
        state.current_agent = END_NODE
        state.final_result = "I apologize, but I'm unable to assist with that request due to content safety guidelines."
        state.error = None  # Clear the error since this is expected behavior
    else:
        # Genuine parsing error
        state.error = f"Supervisor error: {str(e)}"
        state.current_agent = END_NODE
        state.final_result = "I'm experiencing technical difficulties. Please try rephrasing your request."
```

### 2. Improved Supervisor Prompt (`app/agents/supervisor/prompt.md`)

**Enhanced JSON Format Requirements:**
- More explicit instructions about JSON-only responses
- Added examples showing proper JSON format
- Included guidance for handling unfulfillable requests
- Clearer formatting with code blocks

**Before:**
```
You must respond with a JSON object containing:
- "next_agent": The name of the next agent...
```

**After:**
```
You MUST respond with a valid JSON object containing exactly these two fields:
- "next_agent": The name of the next agent...

IMPORTANT: Your response must be ONLY the JSON object, no additional text...

## Examples:
User input: "analyze the graph..."
{"next_agent": "planner", "reasoning": "No existing task plan..."}

If you cannot or should not assist with a request, respond with:
{"next_agent": "__end__", "reasoning": "Request cannot be fulfilled..."}
```

## Behavior Changes

### LLM Refusal Handling
**Before:** Workflow failed with JSON parsing error
**After:** Graceful handling with user-friendly message

### Error Scenarios
1. **LLM Safety Refusal** → Clear apology message, workflow ends
2. **JSON Parsing Error** → Technical difficulty message, workflow ends
3. **Valid JSON Response** → Normal processing continues

### User Experience
- **Expected refusals** (safety policies) → Polite explanation
- **Unexpected errors** → Helpful guidance to retry
- **Normal operation** → Unchanged workflow behavior

## Testing Validation

### Refusal Detection Test
```
Input: "I'm sorry, but I can't help with that."
Output: ✓ Detected as refusal, matched indicators: ['sorry', "can't help"]
```

### Error Handling Flow
1. ✅ Supervisor catches JSON parsing exception
2. ✅ Detects refusal language in response
3. ✅ Sets appropriate final result message
4. ✅ Routes to END_NODE to complete workflow
5. ✅ Clears error for clean user experience

## Files Modified
- `app/agents/supervisor/supervisor_agent.py`: Enhanced error handling with refusal detection
- `app/agents/supervisor/prompt.md`: Improved JSON format instructions and examples

## Impact
- **Reliability**: Supervisor agent no longer crashes on LLM refusals
- **User Experience**: Clear, helpful messages instead of technical errors
- **Workflow Stability**: Proper completion even when LLM refuses to cooperate
- **Safety Compliance**: Appropriate handling of content policy violations

## Future Considerations
- **LLM Selection**: Consider models with better JSON adherence
- **Fallback Strategies**: Additional retry mechanisms for parsing failures
- **Monitoring**: Track refusal patterns for system improvement
- **Customization**: Allow configurable refusal responses per use case
