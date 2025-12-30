## Fixed output guardrails scope validation for conversational responses

### Problem:
- Output guardrails were rejecting valid conversational responses like greetings
- Responses with scope indicators like "How can I help you?" were still failing validation
- Final result was null even when workflow completed successfully

### Root Cause:
The `ScopeValidationGuardrail` was too strict:
- Required explicit scope indicators in ALL responses over 20 words
- Didn't account for conversational/greeting contexts
- Failed to recognize variations of scope phrases

### Changes Made:
- **Enhanced scope indicator detection** with more comprehensive phrase matching
- **Added greeting response exemption** for conversational contexts
- **Improved validation logic** to be more lenient for appropriate response types
- **Better scope indicator coverage** including "how can i help", "i'm here to assist"

### Technical Details:
- Added greeting detection: `["hello", "hi", "hey", "greetings", "how are you", "how can i help"]`
- Modified validation to allow longer responses for greetings without strict scope requirements
- Expanded scope indicators list to catch more variations of helper phrases

### Impact:
- **Conversational responses now pass validation** instead of being rejected
- **Final results are properly returned** for successful workflow completions
- **Better user experience** with natural conversational responses
- **Maintained security** while reducing false positives

### Example:
Before: "Hey there! How can I help you out today?" → ❌ Rejected (scope validation failed)
After: "Hey there! How can I help you out today?" → ✅ Accepted (greeting with helper intent)
