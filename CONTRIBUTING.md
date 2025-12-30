# Contributing Guidelines

Thank you for your interest in contributing to LangGraph Agentic Base! This document outlines the coding standards and project structure that should be followed when contributing to this project.

## Project Structure

The project follows a strict folder structure. **Do not add new top-level directories**. All code should fit within the existing structure:

```
langgraph-agentic-base/
├── src/
│   ├── agents/           # Agent implementations
│   │   ├── {agent_name}/ # Each agent in its own directory
│   │   │   ├── prompt.md # Agent prompt instructions
│   │   │   ├── {agent_name}.py # Agent implementation
│   │   │   └── tools/    # Agent-specific tools
│   │   ├── base_agent.py # Base agent class
│   │   └── registry.py   # Agent registry
│   ├── models/           # Pydantic models and state definitions
│   ├── llm/              # LLM instance management
│   ├── workflow/         # LangGraph workflow definitions
│   ├── utils/            # Utility functions (logger, settings, etc.)
│   └── constants.py      # Constants and enums
├── docs/                 # Documentation files
├── logs/                 # Log files (gitignored)
├── tasks/                # Task persistence files (gitignored)
├── .changelog/           # Changelog entries (timestamped)
├── main.py               # Main entry point
├── cli.py                # CLI interface
└── pyproject.toml        # Project configuration
```

### Important Structure Rules

1. **No new top-level directories**: All code must fit within existing directories
2. **Agent structure**: Each agent must have its own directory under `src/agents/` with:
   - `prompt.md`: Agent instructions
   - `{agent_name}.py`: Agent implementation
   - `tools/`: Agent-specific tools directory
3. **Routers**: If adding API endpoints, place routers in `app/api/v1/` by feature
4. **Schemas**: Pydantic schemas go in `app/schemas/`
5. **Changelog**: Always create changelog entries in `.changelog/` folder with timestamp titles (e.g., `auth_updates_2025-12-23T214200Z.md`)

## Coding Standards

### 1. Type Hints

- **All functions must have complete type annotations**
- Use `typing` module for complex types
- Return types are mandatory
- Use `Optional[T]` for nullable values

```python
from typing import Optional, Dict, List

def process_data(data: Dict[str, str]) -> Optional[List[str]]:
    """Process data and return results."""
    pass
```

### 2. Async/Await

- **Use async/await for all endpoints and I/O operations**
- All API endpoints must be async
- Database operations should be async

```python
async def fetch_data(url: str) -> Dict[str, Any]:
    """Fetch data asynchronously."""
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            return await response.json()
```

### 3. Imports

- **All imports must start with `app.subfolder.file`**
- Use absolute imports, not relative imports
- Group imports: standard library, third-party, local

```python
import os
from typing import Optional

from pydantic import BaseModel
from langchain_core.tools import BaseTool

from app.utils.logger import logger
from app.models.state import AgentState
```

### 4. Error Handling

- Use try-except blocks for all operations that can fail
- Log errors using the logger
- Provide meaningful error messages
- Store errors in state.error when applicable

```python
try:
    result = perform_operation()
    logger.info("Operation completed successfully")
except ValueError as e:
    logger.error(f"Invalid input: {e}")
    raise
except Exception as e:
    logger.error(f"Unexpected error: {e}")
    raise
```

### 5. Logging

- Use the singleton logger from `app.utils.logger`
- Log all important operations
- Use appropriate log levels (DEBUG, INFO, WARNING, ERROR)
- Include context in log messages

```python
from app.utils.logger import logger

logger.info(f"Processing task: {task_id}")
logger.error(f"Failed to process task {task_id}: {error}")
```

### 6. Configuration Management

- **Use SettingsManager for all configuration access**
- Never use `os.getenv()` directly
- All settings properties are in UPPER_CASE
- Configuration is loaded from `.env` file via dynaconf

```python
from app.utils.settings import settings

api_key = settings.GROQ_API_KEY
model = settings.GROQ_MODEL
```

### 7. Pydantic Models

- Use Pydantic for all data validation
- Define schemas in `src/schemas/` for API endpoints (if adding API features)
- Use Field for descriptions and validation
- All models should have docstrings

```python
from pydantic import BaseModel, Field

class TaskInput(BaseModel):
    """Input model for task creation."""
    
    name: str = Field(..., description="Task name")
    description: Optional[str] = Field(None, description="Task description")
```

### 8. Singleton Pattern

- Use singleton pattern for shared resources (Logger, LLM, SettingsManager)
- Implement using `__new__` method
- Ensure thread-safe initialization

```python
class Singleton:
    _instance: Optional["Singleton"] = None
    
    def __new__(cls) -> "Singleton":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
```

### 9. Constants and Enums

- Use Enums for fixed value sets
- Define constants in `src/constants.py`
- Use descriptive names

```python
from enum import Enum

class AgentType(str, Enum):
    SUPERVISOR = "supervisor"
    PLANNER = "planner"
    NEO4J = "neo4j"
```

### 10. Documentation

- All modules, classes, and functions must have docstrings
- Use Google-style docstrings
- Document parameters, return values, and exceptions

```python
def process_task(task_id: str, priority: int) -> Dict[str, Any]:
    """Process a task with given priority.
    
    Args:
        task_id: Unique identifier for the task
        priority: Priority level (1-10)
        
    Returns:
        Dictionary containing task result and metadata
        
    Raises:
        ValueError: If task_id is invalid
        RuntimeError: If task processing fails
    """
    pass
```

## Changelog Guidelines

- Always create changelog entries in `.changelog/` folder
- Use timestamp format: `{feature_name}_{YYYY-MM-DDTHHMMSSZ}.md`
- Keep entries very short: only "what implemented", no extra commentary

Example:
```markdown
# Auth Updates

- Implemented user authentication
- Added JWT token support
- Created login endpoint
```

## Development Workflow

1. **Create a branch**: `git checkout -b feature/your-feature-name`
2. **Follow coding standards**: Ensure all code follows the guidelines above
3. **Write tests**: Add tests for new functionality
4. **Update documentation**: Update relevant docs if needed
5. **Create changelog**: Add changelog entry in `.changelog/`
6. **Submit PR**: Create pull request with clear description

## Testing

- Write tests for all new functionality
- Use pytest for testing
- Tests should be in `tests/` directory (if added)
- Ensure tests pass before submitting PR

## Code Review

- All code must be reviewed before merging
- Address review comments promptly
- Ensure CI/CD checks pass
- Maintain code quality standards

## Questions?

If you have questions about contributing, please:
- Check existing code for examples
- Review the ARCHITECTURE.md file
- Open an issue for clarification

Thank you for contributing!

