"""LangGraph StateGraph workflow implementation.

This module manages the LangGraph workflow compilation and dynamic routing.
The workflow is compiled here using StateGraph, and routing is completely dynamic
based on the agent registry.

Following LangGraph cookbook patterns:
- State uses TypedDict for LangGraph compatibility
- Nodes return dict updates (not full state objects)
- StateGraph merges updates automatically
- Uses checkpointers for state persistence and conversation history
"""

import os
from typing import Any, Optional

from langchain_core.runnables.graph import CurveStyle
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, StateGraph

from src.agents.registry import (
    get_agent_executor,
    get_available_agent_types,
    get_routing_map,
)
from src.constants import AgentType, END_NODE
from src.models.state import AgentState
from src.models.state_typed import AgentStateTyped
from src.utils.checkpoint import get_checkpointer
from src.utils.logger import logger
from langgraph.graph.state import CompiledStateGraph


def create_workflow(checkpointer: Optional[MemorySaver] = None) -> Any:
    """Create and configure the LangGraph workflow with dynamic routing.

    The workflow is compiled here. All agents are dynamically discovered from
    the agent registry, and routing is built dynamically based on available agents.
    No hardcoded routing logic is used.

    Args:
        checkpointer: Optional MemorySaver instance for state persistence.
                     If None, creates a new one.

    Returns:
        Compiled LangGraph application ready to be invoked.
    """
    logger.info("Creating LangGraph workflow with dynamic agent discovery...")

    # Use singleton checkpointer if not provided
    if checkpointer is None:
        checkpointer = get_checkpointer()

    # Create StateGraph with TypedDict state (LangGraph cookbook pattern)
    workflow = StateGraph[AgentStateTyped, None, AgentStateTyped, AgentStateTyped](AgentStateTyped)

    # Dynamically add all registered agents as nodes
    available_agents = get_available_agent_types()

    def create_node_wrapper(agent_executor_func):
        """Wrapper to convert agent execute signature to LangGraph-compatible format.

        LangGraph nodes expect: state: dict -> dict (partial updates)
        Our agents return: (AgentState, UsageStats) -> tuple
        This wrapper converts between formats following LangGraph cookbook pattern.
        """

        def node_func(state: dict) -> dict:
            # Convert dict state to Pydantic AgentState for agent execution
            # Handle missing fields with defaults
            agent_state = AgentState(
                user_input=state.get("user_input", ""),
                task_list=state.get("task_list"),
                current_agent=state.get("current_agent"),
                messages=state.get("messages", []),
                usage_stats=state.get("usage_stats") or AgentState(user_input="").usage_stats,
                final_result=state.get("final_result"),
                error=state.get("error"),
                conversation_history=state.get("conversation_history", []),
            )
            usage_stats = agent_state.usage_stats

            # Execute agent (returns tuple)
            updated_state, updated_stats = agent_executor_func(agent_state, usage_stats)

            # Convert back to dict with partial updates (LangGraph pattern)
            # Only return fields that changed (LangGraph merges automatically)
            updates: dict[str, Any] = {}

            # Check and include changed fields
            if updated_state.current_agent != state.get("current_agent"):
                updates["current_agent"] = updated_state.current_agent

            # Always include task_list if it exists (it may have been modified in place)
            # Pydantic model comparison might not detect in-place changes to nested objects
            if updated_state.task_list is not None:
                updates["task_list"] = updated_state.task_list

            if updated_state.final_result != state.get("final_result"):
                updates["final_result"] = updated_state.final_result
            if updated_state.error != state.get("error"):
                updates["error"] = updated_state.error

            # Usage stats
            updates["usage_stats"] = updated_stats

            # Messages - use Annotated[operator.add] pattern
            # Return new messages only (LangGraph will append via operator.add)
            current_messages = state.get("messages", [])
            new_messages = [msg for msg in updated_state.messages if msg not in current_messages]
            if new_messages:
                updates["messages"] = new_messages

            # Conversation history - append user input and final result if workflow ends
            if updated_state.final_result and updated_state.current_agent == END_NODE:
                # Add to conversation history when workflow completes
                conversation_entry = {
                    "user_input": updated_state.user_input,
                    "result": updated_state.final_result,
                    "messages": updated_state.messages[-10:],  # Last 10 messages for context
                }
                current_history = state.get("conversation_history", [])
                # Check if this entry already exists (avoid duplicates)
                entry_exists = any(
                    entry.get("user_input") == conversation_entry["user_input"] 
                    and entry.get("result") == conversation_entry["result"]
                    for entry in current_history
                )
                if not entry_exists:
                    # Use operator.add pattern - return list with new entry to append
                    # LangGraph will merge this with existing history using operator.add
                    updates["conversation_history"] = [conversation_entry]

            return updates

        return node_func

    for agent_type in available_agents:
        agent_executor = get_agent_executor(agent_type)
        wrapped_node = create_node_wrapper(agent_executor)
        workflow.add_node(agent_type, wrapped_node)
        logger.info(f"Added node: {agent_type}")

    # Set entry point to supervisor
    workflow.set_entry_point(AgentType.SUPERVISOR.value)

    # Dynamic routing function - routes based on state.current_agent
    def route_after_supervisor(state: dict) -> str:
        """Dynamic routing function based on supervisor decision.

        This function reads the current_agent from state and routes accordingly.
        No hardcoded agent names are used - routing is completely dynamic.
        """
        current_agent = state.get("current_agent")
        if current_agent is None or current_agent == END_NODE:
            return END_NODE

        agent_name = current_agent

        # Validate that the agent exists in our registry
        if agent_name not in available_agents and agent_name != END_NODE:
            logger.error(f"Unknown agent in routing: {agent_name}")
            return END_NODE

        logger.info(f"Routing to: {agent_name}")
        return agent_name

    # Build dynamic routing map
    routing_map = get_routing_map()
    # Convert END_NODE string to LangGraph END constant
    routing_map_with_end = {k: END if k == END_NODE else v for k, v in routing_map.items()}

    # Add conditional edges from supervisor with dynamic routing map
    workflow.add_conditional_edges(
        AgentType.SUPERVISOR.value,
        route_after_supervisor,
        routing_map_with_end,
    )

    # All agents (except supervisor) return to supervisor after execution
    # This is dynamic - any agent in the registry will automatically route back
    for agent_type in available_agents:
        if agent_type != AgentType.SUPERVISOR.value:
            workflow.add_edge(agent_type, AgentType.SUPERVISOR.value)
            logger.debug(f"Added edge: {agent_type} -> supervisor")

    # Compile workflow with checkpointer for state persistence
    # This enables conversation history and state management across invocations
    app: CompiledStateGraph = workflow.compile(checkpointer=checkpointer)
    # Render the graph png file
    try:
        # Create the visualizations directory if it doesn't exist
        os.makedirs("visualizations", exist_ok=True)
        app.get_graph().draw_mermaid_png(
            output_file_path="visualizations/workflow.png",
            padding=30,
            max_retries=2,
            curve_style=CurveStyle.CARDINAL,
        )
        logger.info("Graph visualization saved to visualizations/workflow.png")
    except Exception as e:
        logger.warning(f"Could not render graph visualization: {e}")
    logger.info(
        f"Workflow compiled successfully with {len(available_agents)} agents. "
        f"Routing map: {list(routing_map.keys())}"
    )

    return app
