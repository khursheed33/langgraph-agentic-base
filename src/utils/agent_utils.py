"""Utility functions for common agent operations."""

from typing import Optional

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate

from src.constants import AgentType, TaskStatus
from src.models.workflow_state import AgentState, Task, TaskList


def find_pending_task(
    task_list: TaskList, 
    agent_type: AgentType
) -> tuple[Optional[Task], int]:
    """Find the next pending task for a specific agent type.
    
    Args:
        task_list: Task list to search.
        agent_type: Type of agent to find task for.
        
    Returns:
        Tuple of (task, index) or (None, -1) if not found.
    """
    for i, task in enumerate(task_list.tasks):
        if task.agent == agent_type and task.status == TaskStatus.PENDING:
            return task, i
    return None, -1


def build_task_description(
    task: Task, 
    user_input: str, 
    previous_results: Optional[list[str]] = None
) -> str:
    """Build task description string for agent execution.
    
    Args:
        task: Task to build description for.
        user_input: Original user input.
        previous_results: Optional list of previous task results.
        
    Returns:
        Formatted task description string.
    """
    task_description = (
        f"Task: {task.description}\n\nUser Request: {user_input}"
    )
    
    if previous_results:
        task_description += f"\n\nPrevious Task Results:\n" + "\n\n".join(previous_results)
    
    return task_description


def build_agent_messages(
    prompt_template: ChatPromptTemplate,
    task_description: str,
    conversation_context: Optional[str] = None
) -> list[SystemMessage | HumanMessage]:
    """Build messages list for agent execution.
    
    Args:
        prompt_template: Prompt template to format.
        task_description: Task description string.
        conversation_context: Optional conversation context to append.
        
    Returns:
        List of messages (SystemMessage and HumanMessage).
    """
    input_text = task_description
    if conversation_context:
        input_text += conversation_context
    
    formatted_prompt = prompt_template.format_messages(input=input_text)
    system_content = (
        formatted_prompt[0].content
        if formatted_prompt
        else "You are a helpful assistant."
    )
    
    return [
        SystemMessage(content=system_content),
        HumanMessage(content=input_text),
    ]


def get_previous_task_results(
    task_list: TaskList,
    include_agents: Optional[list[AgentType]] = None
) -> list[str]:
    """Get results from completed tasks.
    
    Args:
        task_list: Task list to extract results from.
        include_agents: Optional list of agent types to include. If None, includes all.
        
    Returns:
        List of formatted result strings.
    """
    previous_results = []
    for task in task_list.tasks:
        if task.status.value == "completed" and task.result:
            if include_agents is None or task.agent in include_agents:
                previous_results.append(
                    f"Task [{task.agent.value}]: {task.description}\n"
                    f"Result: {task.result}"
                )
    return previous_results


def get_conversation_context(
    messages: list[dict],
    exclude_roles: Optional[list[str]] = None,
    max_messages: int = 5
) -> str:
    """Get conversation context from previous messages.
    
    Args:
        messages: List of message dictionaries.
        exclude_roles: Optional list of roles to exclude.
        max_messages: Maximum number of recent messages to include.
        
    Returns:
        Formatted conversation context string.
    """
    exclude_roles = exclude_roles or []
    recent_messages = [
        msg
        for msg in messages
        if msg.get("role") not in exclude_roles
    ][-max_messages:]
    
    if not recent_messages:
        return ""
    
    conversation_context = "\n\nPrevious conversation:\n"
    conversation_context += "\n".join(
        [
            f"{msg.get('role', 'unknown')}: {msg.get('content', '')}"
            for msg in recent_messages
        ]
    )
    return conversation_context

