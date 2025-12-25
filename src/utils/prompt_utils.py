"""Utility functions for loading and managing prompts."""

from pathlib import Path

from langchain_core.prompts import ChatPromptTemplate

from src.utils.agent_metadata import get_agent_metadata_loader
from src.utils.logger import logger


def load_prompt_template(agent_name: str) -> ChatPromptTemplate:
    """Load prompt template from markdown file.
    
    Args:
        agent_name: Name of the agent (used to locate prompt file).
        
    Returns:
        ChatPromptTemplate instance with loaded prompt.
    """
    prompt_file = Path(f"src/agents/{agent_name}/prompt.md")
    if not prompt_file.exists():
        logger.warning(f"Prompt file not found: {prompt_file}")
        return ChatPromptTemplate.from_messages(
            [("system", "You are a helpful assistant.")]
        )

    prompt_content = prompt_file.read_text(encoding="utf-8")
    return ChatPromptTemplate.from_messages(
        [("system", prompt_content), ("human", "{input}")]
    )


def load_prompt_template_with_agents(
    agent_name: str, 
    exclude_agents: list[str] | None = None,
    format_type: str = "supervisor"
) -> ChatPromptTemplate:
    """Load prompt template with dynamically injected agent information.
    
    Args:
        agent_name: Name of the agent (used to locate prompt file).
        exclude_agents: List of agent names to exclude from metadata.
        format_type: Type of formatting ("supervisor" or "planner").
        
    Returns:
        ChatPromptTemplate instance with loaded and formatted prompt.
    """
    prompt_file = Path(f"src/agents/{agent_name}/prompt.md")
    if not prompt_file.exists():
        logger.warning(f"Prompt file not found: {prompt_file}")
        return ChatPromptTemplate.from_messages(
            [("system", "You are a helpful assistant.")]
        )

    prompt_content = prompt_file.read_text(encoding="utf-8")
    
    # Load agent metadata and inject into prompt
    loader = get_agent_metadata_loader()
    
    if format_type == "planner":
        available_agents = loader.format_for_planner(exclude=exclude_agents or ["supervisor", "planner"])
        agent_names = loader.get_agent_names_list(exclude=exclude_agents or ["supervisor", "planner"])
    else:  # supervisor
        available_agents = loader.format_for_supervisor(exclude=exclude_agents or ["supervisor"])
        agent_names = loader.get_agent_names_list(exclude=exclude_agents or ["supervisor"])
    
    agent_names_str = ", ".join([f'"{name}"' for name in agent_names])
    
    # Replace placeholders
    prompt_content = prompt_content.replace("{available_agents}", available_agents)
    prompt_content = prompt_content.replace("{agent_names}", agent_names_str)
    
    return ChatPromptTemplate.from_messages(
        [("system", prompt_content), ("human", "{input}")]
    )

