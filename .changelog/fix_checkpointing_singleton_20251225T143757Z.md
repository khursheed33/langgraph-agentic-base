# Fix: Checkpointing singleton and conversation history loading

## What implemented
- Changed checkpointer to singleton pattern to persist across workflow invocations
- Added better logging for conversation history loading
- Fixed state initialization to properly preserve conversation_history and messages
- Reset task_list for new queries while preserving conversation context

