"""State models for LangGraph."""

from typing import Any, Optional

from pydantic import BaseModel, Field

from src.constants import AgentType, TaskStatus


class Task(BaseModel):
    """Represents a single task in the workflow."""

    agent: AgentType = Field(..., description="Agent responsible for this task")
    description: str = Field(..., description="Description of what needs to be done")
    status: TaskStatus = Field(
        default=TaskStatus.PENDING, description="Current status of the task"
    )
    result: Optional[str] = Field(
        default=None, description="Result of task execution"
    )
    error: Optional[str] = Field(default=None, description="Error message if task failed")


class TaskList(BaseModel):
    """List of tasks to be executed."""

    tasks: list[Task] = Field(default_factory=list, description="List of tasks")
    current_task_index: int = Field(
        default=0, description="Index of currently executing task"
    )

    def get_next_pending_task(self) -> Optional[Task]:
        """Get the next pending task."""
        for task in self.tasks:
            if task.status == TaskStatus.PENDING:
                return task
        return None

    def mark_task_completed(self, task_index: int, result: str) -> None:
        """Mark a task as completed."""
        if 0 <= task_index < len(self.tasks):
            self.tasks[task_index].status = TaskStatus.COMPLETED
            self.tasks[task_index].result = result

    def mark_task_failed(self, task_index: int, error: str) -> None:
        """Mark a task as failed."""
        if 0 <= task_index < len(self.tasks):
            self.tasks[task_index].status = TaskStatus.FAILED
            self.tasks[task_index].error = error

    def all_tasks_completed(self) -> bool:
        """Check if all tasks are completed."""
        return all(
            task.status in [TaskStatus.COMPLETED, TaskStatus.FAILED]
            for task in self.tasks
        )


class UsageStats(BaseModel):
    """Tracks usage statistics for agents and tools."""

    agent_usage: dict[str, int] = Field(
        default_factory=dict, description="Number of times each agent was used"
    )
    tool_usage: dict[str, int] = Field(
        default_factory=dict, description="Number of times each tool was used"
    )

    def increment_agent_usage(self, agent_name: str) -> None:
        """Increment agent usage count."""
        self.agent_usage[agent_name] = self.agent_usage.get(agent_name, 0) + 1

    def increment_tool_usage(self, tool_name: str) -> None:
        """Increment tool usage count."""
        self.tool_usage[tool_name] = self.tool_usage.get(tool_name, 0) + 1


class AgentState(BaseModel):
    """State managed by LangGraph StateGraph."""

    user_input: str = Field(..., description="Original user input")
    task_list: Optional[TaskList] = Field(
        default=None, description="List of tasks to execute"
    )
    current_agent: Optional[str] = Field(
        default=None, description="Currently executing agent name or '__end__' to end workflow"
    )
    messages: list[dict[str, Any]] = Field(
        default_factory=list, description="Conversation messages"
    )
    usage_stats: UsageStats = Field(
        default_factory=UsageStats, description="Usage statistics"
    )
    final_result: Optional[str] = Field(
        default=None, description="Final result of the workflow"
    )
    error: Optional[str] = Field(default=None, description="Error message if any")

