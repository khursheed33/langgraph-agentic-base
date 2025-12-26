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

