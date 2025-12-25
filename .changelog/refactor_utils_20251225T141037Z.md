# Refactor: Move utility functions to utils folder

## What implemented
- Created `json_utils.py` for JSON extraction utilities
- Created `prompt_utils.py` for prompt loading utilities
- Created `context_utils.py` for context building utilities
- Created `agent_utils.py` for common agent execution patterns
- Moved task saving logic to `task_persistence.py`
- Refactored all agent files to use utility functions from utils folder
- Removed utility function implementations from agent files

