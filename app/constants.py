"""Constants used throughout the application."""

from enum import Enum
from typing import Final

class AgentType(str, Enum):
    """Available agent types in the system."""
    SUPERVISOR = "supervisor"
    PLANNER = "planner"
    NEO4J = "neo4j"
    FILESYSTEM = "filesystem"
    GENERAL_QA = "general_qa"
    MATHEMATICS = "mathematics"

class WorkflowStatus(str, Enum):
    """Workflow execution status."""
    INITIALIZED = "initialized"
    PLANNING = "planning"
    EXECUTING = "executing"
    COMPLETED = "completed"
    FAILED = "failed"

class TaskStatus(str, Enum):
    """Task execution status."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"

# Agent capabilities descriptions
AGENT_CAPABILITIES: Final[dict[str, str]] = {
    AgentType.NEO4J: "Query and analyze Neo4j graph database. Can retrieve nodes, relationships, and perform graph analysis.",
    AgentType.FILESYSTEM: "Read and write files, create directories, and manage file system operations.",
    AgentType.GENERAL_QA: "Handle general conversational queries, greetings, questions, and provide friendly responses to user inputs.",
    AgentType.MATHEMATICS: "Perform mathematical calculations, solve equations, and provide mathematical problem-solving capabilities.",
}

# Available agents list
AVAILABLE_AGENTS: Final[list[str]] = [
    AgentType.NEO4J,
    AgentType.FILESYSTEM,
    AgentType.GENERAL_QA,
    AgentType.MATHEMATICS,
]

# End node name
END_NODE: Final[str] = "__end__"

# User-facing messages (centralized for reuse)
SUPERVISOR_TECHNICAL_DIFFICULTIES_MSG: Final[str] = "I'm experiencing technical difficulties. Please try rephrasing your request."
SUPERVISOR_SAFETY_STOP_MSG: Final[str] = "I apologize, but I'm unable to assist with that request due to content safety guidelines."
SUPERVISOR_PLANNER_ERROR_MSG: Final[str] = "Workflow ended due to planner errors: {error}"
SUPERVISOR_GREETING_MSG: Final[str] = "Hello! I'm here to help you with various tasks. What would you like assistance with?"
SUPERVISOR_NO_TASKS_MSG: Final[str] = "No tasks required for this request."
