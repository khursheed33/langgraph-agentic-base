"""Agent registry for dynamic agent discovery and management.

This module provides a registry system that allows dynamic discovery and
routing of agents without hardcoding agent names in the workflow.
"""

from typing import Callable, Type

from app.agents.base_agent import BaseAgent
from app.agents.compiler.compiler_agent import CompilerAgent
from app.agents.filesystem.filesystem_agent import FileSystemAgent
from app.agents.general_qa.general_qa_agent import GeneralQAAgent
from app.agents.mathematics.mathematics_agent import MathematicsAgent
from app.agents.neo4j.neo4j_agent import Neo4jAgent
from app.agents.planner.planner_agent import PlannerAgent
from app.agents.python_code_generator.python_code_generator_agent import PythonCodeGeneratorAgent
from app.agents.supervisor.supervisor_agent import SupervisorAgent
from app.constants import AgentType, AVAILABLE_AGENTS, END_NODE
from app.models.workflow_state import AgentState, UsageStats
from app.utils.logger import logger

# Agent registry mapping agent types to their classes
AGENT_REGISTRY: dict[str, Type[BaseAgent]] = {
    AgentType.SUPERVISOR: SupervisorAgent,
    AgentType.PLANNER: PlannerAgent,
    AgentType.NEO4J: Neo4jAgent,
    AgentType.FILESYSTEM: FileSystemAgent,
    AgentType.GENERAL_QA: GeneralQAAgent,
    AgentType.MATHEMATICS: MathematicsAgent,
    AgentType.COMPILER: CompilerAgent,
    AgentType.PYTHON_CODE_GENERATOR: PythonCodeGeneratorAgent,
}

# Agent instances cache (singleton pattern per agent type)
_agent_instances: dict[str, BaseAgent] = {}


def get_agent(agent_type: str) -> BaseAgent:
    """Get or create an agent instance for the given agent type."""
    if agent_type not in _agent_instances:
        if agent_type not in AGENT_REGISTRY:
            raise ValueError(f"Unknown agent type: {agent_type}")
        
        agent_class = AGENT_REGISTRY[agent_type]
        _agent_instances[agent_type] = agent_class()
        logger.info(f"Created agent instance: {agent_type}")
    
    return _agent_instances[agent_type]


def get_agent_executor(agent_type: str) -> Callable[[AgentState, UsageStats], tuple[AgentState, UsageStats]]:
    """Get the execute function for an agent."""
    agent = get_agent(agent_type)
    return agent.execute


def get_available_agent_types() -> list[str]:
    """Get list of available agent type names."""
    return [agent_type.value for agent_type in AVAILABLE_AGENTS] + [
        AgentType.SUPERVISOR.value,
        AgentType.PLANNER.value,
    ]


def get_routing_map() -> dict[str, str]:
    """Get dynamic routing map for all registered agents.
    
    Returns a dictionary mapping agent names to their node names in the graph.
    This is used for dynamic conditional routing in LangGraph.
    """
    routing_map: dict[str, str] = {}
    
    # Add all available agents to routing map (agent_name -> node_name)
    for agent_type in get_available_agent_types():
        routing_map[agent_type] = agent_type
    
    # Add END_NODE mapping
    routing_map[END_NODE] = END_NODE
    
    logger.info(f"Created routing map with {len(routing_map)} routes: {list(routing_map.keys())}")
    return routing_map


def register_agent(agent_type: str, agent_class: Type[BaseAgent]) -> None:
    """Register a new agent type dynamically."""
    if agent_type in AGENT_REGISTRY:
        logger.warning(f"Agent {agent_type} already registered. Overwriting.")
    
    AGENT_REGISTRY[agent_type] = agent_class
    logger.info(f"Registered new agent: {agent_type}")

