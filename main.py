"""Main entry point for the application."""

import sys
from typing import Optional

from src.models.state import AgentState
from src.models.state_typed import AgentStateTyped
from src.utils.logger import logger
from src.utils.settings import settings
from src.workflow import create_workflow


def run_workflow(user_input: str) -> dict:
    """Run the workflow with user input."""
    logger.info(f"Starting workflow with input: {user_input}")

    # Create workflow
    app = create_workflow()

    # Initialize state as dict (LangGraph expects dict/TypedDict)
    initial_state: AgentStateTyped = {
        "user_input": user_input,
        "task_list": None,
        "current_agent": None,
        "messages": [],
        "usage_stats": AgentState(user_input=user_input).usage_stats,
        "final_result": None,
        "error": None,
    }

    try:
        # Run workflow (LangGraph cookbook pattern)
        config = {"recursion_limit": settings.MAX_ITERATIONS}
        final_state_dict = app.invoke(initial_state, config=config)

        # Convert back to Pydantic for easier access
        final_state = AgentState(**final_state_dict)

        # Build result
        result = {
            "user_input": final_state.user_input,
            "final_result": final_state.final_result,
            "usage_stats": {
                "agent_usage": final_state.usage_stats.agent_usage,
                "tool_usage": final_state.usage_stats.tool_usage,
            },
            "messages": final_state.messages,
            "error": final_state.error,
        }

        logger.info("Workflow completed successfully")
        return result

    except Exception as e:
        logger.error(f"Workflow error: {e}")
        return {
            "user_input": user_input,
            "final_result": None,
            "error": str(e),
            "usage_stats": {},
            "messages": [],
        }


def main() -> None:
    """Main function."""
    if len(sys.argv) < 2:
        print("Usage: python main.py '<user_input>'")
        sys.exit(1)

    user_input = sys.argv[1]
    result = run_workflow(user_input)

    print("\n" + "=" * 80)
    print("WORKFLOW RESULT")
    print("=" * 80)
    print(f"\nUser Input: {result['user_input']}")
    
    if result.get("error"):
        print(f"\nError: {result['error']}")
    
    if result.get("final_result"):
        print(f"\nFinal Result:\n{result['final_result']}")
    
    print("\nUsage Statistics:")
    print(f"  Agent Usage: {result['usage_stats'].get('agent_usage', {})}")
    print(f"  Tool Usage: {result['usage_stats'].get('tool_usage', {})}")
    print("=" * 80)


if __name__ == "__main__":
    main()

