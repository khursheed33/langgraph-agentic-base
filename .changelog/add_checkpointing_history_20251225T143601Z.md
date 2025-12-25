# Add: Checkpointing and conversation history management

## What implemented
- Added MemorySaver checkpointer to workflow for state persistence
- Added conversation_history field to AgentState and AgentStateTyped
- Updated workflow to use thread_id for conversation continuity
- Modified main.py and cli.py to support thread_id and load previous state
- Updated supervisor and planner agents to include conversation history in context
- Interactive mode now maintains conversation history across queries

