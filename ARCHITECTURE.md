# Architecture Documentation

## Overview

This project implements a multi-agent system using LangGraph's StateGraph for workflow management. The system follows a supervisor-planner pattern where a supervisor agent routes tasks to specialized agents based on a dynamically created task plan.

## Core Components

### 1. State Management (`src/models/state.py`)

The `AgentState` Pydantic model manages the entire workflow state:
- `user_input`: Original user request
- `task_list`: List of tasks to execute (created by planner)
- `current_agent`: Currently executing agent
- `messages`: Conversation history
- `usage_stats`: Tracking of agent and tool usage
- `final_result`: Final workflow result
- `error`: Error messages if any

### 2. Singleton Patterns

#### Logger (`src/utils/logger.py`)
- Single instance across the application
- Logs to both file (`logs/timestamp_log.log`) and console
- Configurable log level via environment variable

#### LLM Instance (`src/llm/llm_instance.py`)
- Single Groq LLM instance shared by all agents
- Initialized once with API key from environment
- Ensures consistent model usage across agents

### 3. Agent Architecture

All agents inherit from `BaseAgent` which provides:
- Prompt loading from markdown files
- Tool loading from tools directory
- Status reporting capabilities
- Common execution interface

#### Agent Types

1. **Supervisor Agent**: Routes tasks, manages workflow
2. **Planner Agent**: Creates task plans from user intent
3. **Neo4j Agent**: Database operations, query building, and result formatting
4. **FileSystem Agent**: File operations

### 4. Workflow Graph (`src/workflow/graph.py`)

The LangGraph StateGraph implements the workflow:
- Entry point: Supervisor
- Supervisor routes to Planner (if no task list) or task agents
- Task agents return to Supervisor after completion
- Supervisor ends workflow when all tasks complete

## Design Patterns

### Singleton Pattern
- Logger and LLM instances use singleton pattern
- Ensures single instance and shared state

### Factory Pattern
- BaseAgent creates agents with consistent interface
- Tools are loaded dynamically from tools directory

### Strategy Pattern
- Each agent implements its own execution strategy
- Supervisor uses routing strategy based on state

### Observer Pattern
- Usage statistics track agent and tool usage
- State changes are logged for traceability

## Data Flow

1. User input → Main/CLI
2. Main creates workflow and initial state
3. Workflow starts at Supervisor
4. Supervisor routes to Planner (if needed)
5. Planner creates task list
6. Supervisor routes to task agents based on task list
7. Task agents execute and return to Supervisor
8. Supervisor checks completion and routes accordingly
9. When all tasks complete, Supervisor ends workflow
10. Final result returned with usage statistics

## Type Safety

- All functions have type hints
- Pydantic models validate data structures
- Enums used for fixed value sets (AgentType, TaskStatus, etc.)
- Constants module for shared values

## Error Handling

- Try-except blocks in all agent executions
- Errors stored in state.error
- Failed tasks marked with error status
- Comprehensive logging of all errors

## Extensibility

### Adding New Agents

1. Create agent directory: `src/agents/new_agent/`
2. Add `prompt.md` with instructions
3. Create tools in `tools/` directory
4. Implement agent class inheriting from `BaseAgent`
5. Add to workflow graph
6. Update constants with agent type

### Adding New Tools

1. Create tool file in agent's `tools/` directory
2. Inherit from `langchain_core.tools.BaseTool`
3. Export in `tools/__init__.py`
4. Tool automatically loaded by agent

## Best Practices

1. **Type Hints**: All functions have complete type annotations
2. **Error Handling**: Comprehensive try-except blocks
3. **Logging**: All operations logged for traceability
4. **Constants**: Fixed values in constants module
5. **Enums**: Type-safe enumerations for fixed sets
6. **Pydantic**: Data validation and serialization
7. **Singleton**: Shared resources use singleton pattern
8. **Separation of Concerns**: Clear module boundaries

