"""Utility functions for API endpoints."""

from typing import Any, Optional

from app.agents.registry import get_agent, get_available_agent_types
from app.models.tool_status import ToolStatus, TaskStatusInfo
from app.models.workflow_state import AgentState, TaskList
from app.utils.checkpoint import get_checkpointer
# from app.workflow import create_workflow
from app.services.workflow_service import _WORKFLOW_APP


def get_all_agent_status(usage_stats: Optional[dict[str, Any]] = None) -> list[dict[str, Any]]:
    """Get status for all available agents.
    
    Args:
        usage_stats: Optional usage statistics dict with agent_usage counts.
        
    Returns:
        List of agent status dictionaries.
    """
    agent_statuses = []
    usage_stats = usage_stats or {}
    agent_usage = usage_stats.get("agent_usage", {})
    
    for agent_type in get_available_agent_types():
        try:
            agent = get_agent(agent_type)
            status = agent.get_status()
            status["usage_count"] = agent_usage.get(agent_type, 0)
            agent_statuses.append(status)
        except Exception:
            # Skip agents that fail to load
            continue
    
    return agent_statuses


def get_all_tool_status(usage_stats: Optional[dict[str, Any]] = None) -> list[ToolStatus]:
    """Get status for all tools across all agents.

    Args:
        usage_stats: Optional usage statistics dict with tool_usage counts.

    Returns:
        List of tool status models.
    """
    tool_statuses = {}
    usage_stats = usage_stats or {}
    tool_usage = usage_stats.get("tool_usage", {})

    # Collect all tools from all agents
    for agent_type in get_available_agent_types():
        try:
            agent = get_agent(agent_type)
            for tool in agent.tools:
                tool_name = tool.name
                if tool_name not in tool_statuses:
                    tool_statuses[tool_name] = ToolStatus(
                        tool_name=tool_name,
                        usage_count=tool_usage.get(tool_name, 0),
                    )
        except Exception:
            continue

    return list(tool_statuses.values())


def get_workflow_state(thread_id: str) -> Optional[dict[str, Any]]:
    """Get current workflow state for a thread.
    
    Args:
        thread_id: Thread ID to get state for.
        
    Returns:
        Current state dictionary or None if not found.
    """
    try:
        app = _WORKFLOW_APP
        config = {
            "recursion_limit": 50,
            "configurable": {"thread_id": thread_id},
        }
        checkpoint_state = app.get_state(config)
        if checkpoint_state and checkpoint_state.values:
            return checkpoint_state.values
    except Exception:
        pass
    return None


def get_current_task(state: Optional[dict[str, Any]]) -> Optional[dict[str, Any]]:
    """Get current task from state.
    
    Args:
        state: State dictionary.
        
    Returns:
        Current task dictionary or None.
    """
    if not state:
        return None
    
    task_list = state.get("task_list")
    if not task_list:
        return None
    
    # Handle both dict and TaskList object
    if isinstance(task_list, dict):
        tasks = task_list.get("tasks", [])
        current_index = task_list.get("current_task_index", 0)
    else:
        # It's a TaskList object
        tasks = task_list.tasks if hasattr(task_list, "tasks") else []
        current_index = task_list.current_task_index if hasattr(task_list, "current_task_index") else 0
    
    if 0 <= current_index < len(tasks):
        task = tasks[current_index]
        
        # Handle both dict and Task object
        if isinstance(task, dict):
            agent = task.get("agent")
            description = task.get("description")
            status = task.get("status")
        else:
            # It's a Task object
            agent = getattr(task, "agent", None)
            if agent and hasattr(agent, "value"):
                agent = agent.value
            description = getattr(task, "description", None)
            status = getattr(task, "status", None)
            if status and hasattr(status, "value"):
                status = status.value
        
        # Only return if required fields are present
        if agent and description and status:
            return TaskStatusInfo(
                agent=str(agent),
                description=str(description),
                status=str(status),
                result=getattr(task, "result", None) if not isinstance(task, dict) else task.get("result"),
                error=getattr(task, "error", None) if not isinstance(task, dict) else task.get("error"),
            )
    
    return None

