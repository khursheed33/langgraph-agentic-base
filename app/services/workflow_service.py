"""Workflow service for executing LangGraph workflows."""

import uuid
from typing import Optional, Dict, Any

from app.config import load_guardrail_config
from app.guardrails.config import GuardrailConfig
from app.guardrails.manager import GuardrailManager
from app.models.result_model import ResultModel, UsageStatsModel, TokenStatsModel
from app.models.state_typed import AgentStateTyped
from app.models.workflow_state import AgentState
from app.utils.logger import logger
from app.utils.settings import settings
from app.workflow import create_workflow
from app.utils.checkpoint import get_checkpointer


# Global singleton workflow app (initialized at import)
_WORKFLOW_APP = create_workflow(get_checkpointer())

async def run_workflow(
    user_input: str,
    thread_id: Optional[str] = None,
    guardrail_config: Optional[GuardrailConfig] = None,
    bypass_guardrails: bool = False,
) -> dict:
    """Run the workflow with user input and optional thread_id for conversation history.

    Args:
        user_input: User's input/query.
        thread_id: Optional thread ID for conversation continuity. If None, creates new thread.
        guardrail_config: Optional guardrail configuration. If None, uses default config.
        bypass_guardrails: If True, skip guardrail checks (admin only).

    Returns:
        Dictionary with workflow result and metadata.
    """
    logger.info(f"Starting workflow with input: {user_input} (bypass_guardrails={bypass_guardrails})")

    # Initialize guardrails
    if guardrail_config is None:
        guardrail_config = load_guardrail_config()  # Load from config file
    guardrail_manager = GuardrailManager(guardrail_config)

    # Check input guardrails unless bypassed by admin user
    if not bypass_guardrails:
        input_results = await guardrail_manager.check_input(user_input)
        failed_guardrails = [result for result in input_results if not result.passed]

        if failed_guardrails:
            # Return early with guardrail failure
            failed_result = failed_guardrails[0]  # Use first failure
            logger.warning(f"Input guardrail failed: {failed_result.reason}")
            return ResultModel(
                user_input=user_input,
                final_result=None,
                error=f"Input validation failed: {failed_result.reason}",
                usage_stats=UsageStatsModel(),
                token_stats=TokenStatsModel(),
                messages=[],
                thread_id=thread_id or str(uuid.uuid4()),
                conversation_history=[],
            ).dict()
    else:
        logger.info("Guardrails bypassed by admin user")

    # Normalize thread_id - treat empty string or 'string' as None
    if thread_id and isinstance(thread_id, str):
        thread_id = thread_id.strip()
        if thread_id == "" or thread_id.lower() == "string":
            thread_id = None

    # Generate thread_id if not provided (for new conversation)
    if thread_id is None:
        thread_id = str(uuid.uuid4())
        logger.info(f"Created new conversation thread: {thread_id}")
    else:
        logger.info(f"Continuing conversation thread: {thread_id}")

    # Use singleton workflow app (already created at import)
    app = _WORKFLOW_APP

    # Prepare config with thread_id for checkpointing
    config = {
        "recursion_limit": settings.MAX_ITERATIONS,
        "configurable": {"thread_id": thread_id},
    }

    try:
        # Try to get existing state from checkpoint
        # This loads previous conversation history if thread_id exists
        existing_state = None
        try:
            # Get the latest checkpoint state
            checkpoint_state = app.get_state(config)
            if checkpoint_state and checkpoint_state.values:
                existing_state = checkpoint_state.values
                logger.info(f"Loaded existing state for thread: {thread_id}")
                logger.debug(f"Existing conversation_history length: {len(existing_state.get('conversation_history', []))}")
                logger.debug(f"Existing messages length: {len(existing_state.get('messages', []))}")
        except Exception as e:
            logger.debug(f"No existing checkpoint found for thread {thread_id}: {e}")

        # Initialize state - merge with existing state if available
        if existing_state:
            # Preserve conversation history and messages from previous state
            existing_history = existing_state.get("conversation_history", [])
            existing_messages = existing_state.get("messages", [])

            logger.info(f"Preserving {len(existing_history)} conversation entries and {len(existing_messages)} messages")

            # Update user_input but preserve conversation history
            initial_state: AgentStateTyped = {
                "user_input": user_input,
                "task_list": None,  # Reset task_list for new query
                "current_agent": None,  # Reset to start new workflow
                "messages": existing_messages,  # Preserve all previous messages
                "usage_stats": existing_state.get("usage_stats") or AgentState(user_input=user_input).usage_stats,
                "final_result": None,  # Reset final result
                "error": None,  # Reset error
                "conversation_history": existing_history,  # Preserve conversation history
            }
        else:
            # New conversation - initialize fresh state
            initial_state: AgentStateTyped = {
                "user_input": user_input,
                "task_list": None,
                "current_agent": None,
                "messages": [],
                "usage_stats": AgentState(user_input=user_input).usage_stats,
                "final_result": None,
                "error": None,
                "conversation_history": [],
            }

        # Run workflow with thread_id for checkpointing (LangGraph cookbook pattern)
        final_state_dict = app.invoke(initial_state, config=config)

        # Convert back to Pydantic for easier access
        final_state = AgentState(**final_state_dict)

        # Check output guardrails if there's a final result
        if final_state.final_result:
            output_results = await guardrail_manager.check_output(final_state.final_result)
            failed_guardrails = [result for result in output_results if not result.passed]

            if failed_guardrails:
                # Output failed guardrails - return error
                failed_result = failed_guardrails[0]  # Use first failure
                logger.warning(f"Output guardrail failed: {failed_result.reason}")
                return ResultModel(
                    user_input=final_state.user_input,
                    final_result=None,
                    error=f"Output validation failed: {failed_result.reason}",
                    usage_stats=UsageStatsModel(),
                    token_stats=TokenStatsModel(),
                    messages=final_state.messages,
                    thread_id=thread_id,
                    conversation_history=final_state.conversation_history,
                ).dict()

        # Build result using ResultModel
        result = ResultModel(
            user_input=final_state.user_input,
            final_result=final_state.final_result,
            usage_stats=UsageStatsModel(
                agent_usage=final_state.usage_stats.agent_usage,
                tool_usage=final_state.usage_stats.tool_usage,
            ),
            token_stats=TokenStatsModel(
                input_tokens=final_state.usage_stats.token_stats.input_tokens,
                output_tokens=final_state.usage_stats.token_stats.output_tokens,
                total_tokens=final_state.usage_stats.token_stats.total_tokens,
                input_cost=final_state.usage_stats.token_stats.input_cost,
                output_cost=final_state.usage_stats.token_stats.output_cost,
                total_cost=final_state.usage_stats.token_stats.total_cost,
            ),
            messages=final_state.messages,
            error=final_state.error,
            thread_id=thread_id,
            conversation_history=final_state.conversation_history,
        )

        logger.info(f"Workflow completed successfully for thread: {thread_id}")
        return result.dict()

    except Exception as e:
        logger.error(f"Workflow error: {e}")
        return ResultModel(
            user_input=user_input,
            final_result=None,
            error=str(e),
            usage_stats=UsageStatsModel(),
            token_stats=TokenStatsModel(),
            messages=[],
            thread_id=thread_id,
            conversation_history=[],
        ).dict()
