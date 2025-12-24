"""TypedDict state definition for LangGraph compatibility.

This module provides TypedDict-based state that LangGraph expects,
while maintaining compatibility with our Pydantic models.
"""

from typing import Any, Optional
from typing_extensions import Annotated, TypedDict
import operator

from src.models.state import TaskList, UsageStats


class AgentStateTyped(TypedDict, total=False):
    """TypedDict state for LangGraph StateGraph.
    
    This follows the LangGraph cookbook pattern using TypedDict.
    Messages use Annotated with operator.add for automatic merging.
    """
    
    user_input: str
    task_list: Optional[TaskList]
    current_agent: Optional[str]
    messages: Annotated[list[dict[str, Any]], operator.add]
    usage_stats: UsageStats
    final_result: Optional[str]
    error: Optional[str]

