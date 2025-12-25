"""Query agent implementation for general conversational responses."""

from langchain_core.messages import HumanMessage, SystemMessage
from typing import Any

from src.agents.base_agent import BaseAgent
from src.constants import AgentType, TaskStatus
from src.models.state import AgentState, UsageStats
from src.utils.logger import logger
from src.utils.task_persistence import update_task_file


class QueryAgent(BaseAgent):
    """Query agent for handling general conversational queries and responses."""

    def __init__(self) -> None:
        """Initialize query agent."""
        super().__init__("query")
        # Query agent doesn't need tools - it uses LLM for conversational responses

    def execute(
        self, state: AgentState, usage_stats: UsageStats
    ) -> tuple[AgentState, UsageStats]:
        """Execute query agent to generate conversational response."""
        logger.info("Query agent executing...")
        usage_stats.increment_agent_usage("query")

        if not state.task_list:
            logger.error("No task list available")
            state.error = "No task list available"
            return state, usage_stats

        # Find current task for query agent
        current_task = None
        task_index = -1
        for i, task in enumerate(state.task_list.tasks):
            if task.agent == AgentType.QUERY and task.status == TaskStatus.PENDING:
                current_task = task
                task_index = i
                break

        if not current_task:
            logger.warning("No pending Query task found")
            state.messages.append(
                {"role": "query", "content": "No pending task for Query agent"}
            )
            return state, usage_stats

        # Mark task as in progress
        current_task.status = TaskStatus.IN_PROGRESS

        try:
            # Prepare input for agent
            task_description = (
                f"Task: {current_task.description}\n\nUser Request: {state.user_input}"
            )

            # Get conversation context from previous messages
            conversation_context = ""
            if state.messages:
                recent_messages = [
                    msg
                    for msg in state.messages
                    if msg.get("role") not in ["query", "supervisor"]
                ][-5:]  # Last 5 messages for context
                if recent_messages:
                    conversation_context = "\n\nPrevious conversation:\n"
                    conversation_context += "\n".join(
                        [
                            f"{msg.get('role', 'unknown')}: {msg.get('content', '')}"
                            for msg in recent_messages
                        ]
                    )

            # Execute agent using LangGraph cookbook pattern
            # Format prompt template to get system message
            formatted_prompt = self.prompt_template.format_messages(
                input=task_description + conversation_context
            )
            system_content = (
                formatted_prompt[0].content
                if formatted_prompt
                else "You are a helpful assistant."
            )
            messages = [
                SystemMessage(content=system_content),
                HumanMessage(content=task_description + conversation_context),
            ]

            # Get LLM response
            llm_response = self.llm.invoke(messages)
            result_text = (
                llm_response.content
                if hasattr(llm_response, "content")
                else str(llm_response)
            )

            # Ensure result_text is not empty
            if not result_text or not result_text.strip():
                logger.error("Query agent result text is empty")
                result_text = "I'm here to help! Could you please rephrase your question?"

            # Mark task as completed
            state.task_list.mark_task_completed(task_index, result_text)

            logger.info(f"Query task completed: {current_task.description}")

            # Update task file
            update_task_file(state)

            # Add message to state
            state.messages.append(
                {
                    "role": "query",
                    "content": f"Completed task: {current_task.description}\nResult: {result_text}",
                }
            )

        except Exception as e:
            logger.error(f"Query agent error: {e}")
            import traceback

            logger.error(f"Query traceback: {traceback.format_exc()}")
            state.task_list.mark_task_failed(task_index, str(e))
            state.error = f"Query agent error: {str(e)}"

        return state, usage_stats

