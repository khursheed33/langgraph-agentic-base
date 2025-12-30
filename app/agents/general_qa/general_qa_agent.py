"""General QA agent implementation for general conversational responses."""

from app.agents.base_agent import BaseAgent
from app.constants import AgentType, TaskStatus
from app.models.workflow_state import AgentState, UsageStats
from app.utils.agent_utils import (
    build_agent_messages,
    build_task_description,
    find_pending_task,
    get_conversation_context,
)
from app.utils.logger import logger
from app.utils.task_persistence import update_task_file
from app.utils.token_calculator import track_token_usage


class GeneralQAAgent(BaseAgent):
    """General QA agent for handling general conversational queries and responses."""

    def __init__(self) -> None:
        """Initialize general QA agent."""
        super().__init__("general_qa")
        # General QA agent doesn't need tools - it uses LLM for conversational responses

    def execute(
        self, state: AgentState, usage_stats: UsageStats
    ) -> tuple[AgentState, UsageStats]:
        """Execute general QA agent to generate conversational response."""
        logger.info("General QA agent executing...")
        usage_stats.increment_agent_usage("general_qa")

        if not state.task_list:
            logger.warning("No task list available - routing back to supervisor for task planning")
            # For simple conversational queries without a task list, provide a direct response
            # This handles cases where supervisor routes directly to general_qa for simple queries
            user_input_lower = state.user_input.lower()

            # Handle simple greetings and conversational queries
            if any(greeting in user_input_lower for greeting in ["hello", "hi", "hey", "howdy"]):
                state.final_result = "Hello! I'm here to help you with various tasks including file operations, mathematical calculations, database queries, and more. What would you like assistance with?"
            elif "how are you" in user_input_lower or "what's up" in user_input_lower:
                state.final_result = "I'm doing well, thank you! I'm ready to help you with your tasks. What can I assist you with today?"
            else:
                # For other queries without task list, suggest creating a plan
                state.final_result = "I understand you need assistance. For complex requests, I can create a task plan to help organize the work. Could you provide more details about what you'd like to accomplish?"

            state.current_agent = END_NODE  # End workflow since we handled it directly
            state.messages.append({
                "role": "general_qa",
                "content": f"Handled conversational query: {state.final_result}"
            })
            return state, usage_stats

        # Find current task for general QA agent
        current_task, task_index = find_pending_task(state.task_list, AgentType.GENERAL_QA)

        if not current_task:
            logger.warning("No pending General QA task found")
            state.messages.append(
                {"role": "general_qa", "content": "No pending task for General QA agent"}
            )
            return state, usage_stats

        # Mark task as in progress
        current_task.status = TaskStatus.IN_PROGRESS

        try:
            # Build task description
            task_description = build_task_description(current_task, state.user_input)

            # Get conversation context from previous messages
            conversation_context = get_conversation_context(
                state.messages,
                exclude_roles=["general_qa", "supervisor"],
                max_messages=5
            )

            # Execute agent using LangGraph cookbook pattern
            # Build messages using utility function
            messages = build_agent_messages(
                self.prompt_template,
                task_description,
                conversation_context
            )

            # Get LLM response
            llm_response = self.llm.invoke(messages)
            track_token_usage(llm_response, usage_stats)
            result_text = (
                llm_response.content
                if hasattr(llm_response, "content")
                else str(llm_response)
            )

            # Ensure result_text is not empty
            if not result_text or not result_text.strip():
                logger.error("General QA agent result text is empty")
                result_text = "I'm here to help! Could you please rephrase your question?"

            # Mark task as completed
            state.task_list.mark_task_completed(task_index, result_text)

            logger.info(f"General QA task completed: {current_task.description}")

            # Update task file
            update_task_file(state)

            # Add message to state
            state.messages.append(
                {
                    "role": "general_qa",
                    "content": f"Completed task: {current_task.description}\nResult: {result_text}",
                }
            )

        except Exception as e:
            logger.error(f"General QA agent error: {e}")
            import traceback

            logger.error(f"General QA traceback: {traceback.format_exc()}")
            state.task_list.mark_task_failed(task_index, str(e))
            state.error = f"General QA agent error: {str(e)}"

        return state, usage_stats

