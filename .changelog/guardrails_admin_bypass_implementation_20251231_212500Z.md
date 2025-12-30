# Admin-Based Guardrails Bypass Implementation

## Status: ✓ COMPLETE

The system now checks user role and applies guardrails based on admin status.

## Implementation Details

### 1. User Model (`app/models/user.py`)
- `UserDB` model includes `bypass_guardrails: bool` field (default: False)
- `AuthUser` model includes `bypass_guardrails: bool` field for request context

### 2. User Service (`app/services/user_service.py`)
- Line 111: Automatically sets `bypass_guardrails = role == "admin"`
- When creating a user, if role is "admin", `bypass_guardrails` is set to True
- Regular users have `bypass_guardrails = False`

### 3. Security Layer (`app/api/security.py`)
- `get_current_user()` dependency extracts user from token
- Returns `AuthUser` with `bypass_guardrails` value from database
- Line 65: Retrieves `bypass_guardrails` from user object

### 4. Chat Endpoint (`app/api/v1/chat.py`)
- Line 51: Passes `bypass_guardrails=current_user.bypass_guardrails` to workflow
- Authenticated user data flows through the endpoint

### 5. Workflow Service (`app/services/workflow_service.py`)
- Line 46: Checks `if not bypass_guardrails:` before applying input guardrails
- If admin (bypass_guardrails=True): Guardrails are skipped
- If regular user (bypass_guardrails=False): Full guardrail validation applied
- Logs "Guardrails bypassed by admin user" when applicable

## Flow

1. User authenticates and gets token
2. Token is verified by `get_current_user()`
3. User object with `bypass_guardrails` flag is retrieved from Neo4j
4. Chat request includes authenticated user data
5. Workflow service receives `bypass_guardrails` flag
6. Guardrails applied conditionally:
   - **Admin users**: No guardrails applied
   - **Regular users**: Full guardrails applied

## Testing

Admin users can submit any input without guardrail filtering.
Regular users have all guardrails enforced.
