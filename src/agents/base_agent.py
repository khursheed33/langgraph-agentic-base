"""Base agent class."""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

from langchain_core.messages import BaseMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.tools import BaseTool

from src.llm import get_llm
from src.models.state import AgentState, UsageStats
from src.utils.logger import logger


class BaseAgent(ABC):
    """Base class for all agents."""

    def __init__(self, agent_name: str) -> None:
        """Initialize the agent."""
        self.agent_name = agent_name
        self.llm = get_llm()
        self.prompt_template = self._load_prompt()
        self.tools = self._load_tools()

    def _load_prompt(self) -> ChatPromptTemplate:
        """Load prompt from markdown file."""
        prompt_file = Path(f"src/agents/{self.agent_name}/prompt.md")
        if not prompt_file.exists():
            logger.warning(f"Prompt file not found: {prompt_file}")
            return ChatPromptTemplate.from_messages(
                [("system", "You are a helpful assistant.")]
            )

        prompt_content = prompt_file.read_text(encoding="utf-8")
        return ChatPromptTemplate.from_messages(
            [("system", prompt_content), ("human", "{input}")]
        )

    def _load_tools(self) -> list[BaseTool]:
        """Load tools from tools directory."""
        tools: list[BaseTool] = []

        try:
            # Import tools module
            tools_module_name = f"src.agents.{self.agent_name}.tools"
            tools_module = __import__(tools_module_name, fromlist=[""])
            
            # Get all tools from __all__ or search for BaseTool instances
            if hasattr(tools_module, "__all__"):
                for tool_name in tools_module.__all__:
                    tool = getattr(tools_module, tool_name, None)
                    if isinstance(tool, BaseTool):
                        tools.append(tool)
                        logger.info(f"Loaded tool: {tool.name}")
            else:
                # Fallback: search for BaseTool instances
                for attr_name in dir(tools_module):
                    if not attr_name.startswith("_"):
                        attr = getattr(tools_module, attr_name)
                        if isinstance(attr, BaseTool):
                            tools.append(attr)
                            logger.info(f"Loaded tool: {attr.name}")
        except ImportError as e:
            logger.warning(f"Could not import tools for {self.agent_name}: {e}")
        except Exception as e:
            logger.error(f"Failed to load tools for {self.agent_name}: {e}")

        return tools

    def get_status(self) -> dict[str, Any]:
        """Get agent status information."""
        return {
            "agent_name": self.agent_name,
            "tools_count": len(self.tools),
            "tools": [tool.name for tool in self.tools],
        }

    @abstractmethod
    def execute(
        self, state: AgentState, usage_stats: UsageStats
    ) -> tuple[AgentState, UsageStats]:
        """Execute the agent's task."""
        pass

