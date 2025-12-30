"""Utility functions for building context strings."""

from app.constants import AgentType
from app.models.workflow_state import AgentState


def build_supervisor_context(state: AgentState) -> str:
    """Build context string for supervisor decision.
    
    Args:
        state: Current agent state.
        
    Returns:
        Formatted context string for supervisor.
    """
    context_parts = [
        f"User Input: {state.user_input}",
    ]

    # Add conversation history if available
    if state.conversation_history:
        context_parts.append("\n=== Previous Conversation History ===")
        for i, entry in enumerate(state.conversation_history[-3:], 1):  # Last 3 conversations
            prev_input = entry.get("user_input", "")
            prev_result = entry.get("result", "")
            context_parts.append(
                f"\nPrevious Question {i}: {prev_input}"
            )
            if prev_result:
                # Truncate long results
                result_preview = prev_result[:200] + "..." if len(prev_result) > 200 else prev_result
                context_parts.append(f"Previous Answer {i}: {result_preview}")
        context_parts.append("\n=== End of Conversation History ===\n")

    if state.task_list:
        if len(state.task_list.tasks) == 0:
            context_parts.append("\nTask list is empty (no tasks needed).")
        else:
            context_parts.append("\nCurrent Task List:")
            for i, task in enumerate(state.task_list.tasks):
                status_icon = "✓" if task.status.value == "completed" else "○"
                context_parts.append(
                    f"  {i+1}. {status_icon} [{task.agent.value}] {task.description} "
                    f"(Status: {task.status.value})"
                )

            if state.task_list.all_tasks_completed():
                context_parts.append("\nAll tasks are completed.")
            else:
                next_task = state.task_list.get_next_pending_task()
                if next_task:
                    context_parts.append(
                        f"\nNext pending task: [{next_task.agent.value}] {next_task.description}"
                    )
    else:
        context_parts.append("\nNo task list exists. Need to create one.")

    return "\n".join(context_parts)

