# Schema Separation and Naming Improvements

- Renamed state.py to workflow_state.py for clearer naming (workflow state, not generic state)
- Renamed AgentState class to WorkflowState (kept AgentState as alias for backward compatibility)
- Split request schemas into separate files: chat_request.py, history_request.py
- Split response schemas into separate files: chat_response.py, history_response.py, status_response.py, error_response.py, agent_status_response.py, tool_status_response.py, task_response.py, token_usage_response.py, token_cost_response.py, token_info_response.py
- Updated all imports across codebase to use new file locations
- Deleted old requests.py and responses.py files

