"""Main entry point for the application."""

import sys
import uuid
from pathlib import Path
from typing import Optional

import uvicorn
import yaml
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.router import api_router
from src.models.state import AgentState
from src.models.state_typed import AgentStateTyped
from src.utils.logger import logger
from src.utils.settings import settings
from src.workflow import create_workflow


def run_workflow(user_input: str, thread_id: Optional[str] = None) -> dict:
    """Run the workflow with user input and optional thread_id for conversation history.
    
    Args:
        user_input: User's input/query.
        thread_id: Optional thread ID for conversation continuity. If None, creates new thread.
        
    Returns:
        Dictionary with workflow result and metadata.
    """
    logger.info(f"Starting workflow with input: {user_input}")
    
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

    # Create workflow with checkpointer
    app = create_workflow()

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

        # Build result
        result = {
            "user_input": final_state.user_input,
            "final_result": final_state.final_result,
            "usage_stats": {
                "agent_usage": final_state.usage_stats.agent_usage,
                "tool_usage": final_state.usage_stats.tool_usage,
            },
            "token_stats": {
                "input_tokens": final_state.usage_stats.token_stats.input_tokens,
                "output_tokens": final_state.usage_stats.token_stats.output_tokens,
                "total_tokens": final_state.usage_stats.token_stats.total_tokens,
                "input_cost": final_state.usage_stats.token_stats.input_cost,
                "output_cost": final_state.usage_stats.token_stats.output_cost,
                "total_cost": final_state.usage_stats.token_stats.total_cost,
            },
            "messages": final_state.messages,
            "error": final_state.error,
            "thread_id": thread_id,
            "conversation_history": final_state.conversation_history,
        }

        logger.info(f"Workflow completed successfully for thread: {thread_id}")
        return result

    except Exception as e:
        logger.error(f"Workflow error: {e}")
        return {
            "user_input": user_input,
            "final_result": None,
            "error": str(e),
            "usage_stats": {},
            "token_stats": {
                "input_tokens": 0,
                "output_tokens": 0,
                "total_tokens": 0,
                "input_cost": 0.0,
                "output_cost": 0.0,
                "total_cost": 0.0,
            },
            "messages": [],
            "thread_id": thread_id,
            "conversation_history": [],
        }


def create_app() -> FastAPI:
    """Create and configure FastAPI application.
    
    Returns:
        Configured FastAPI application instance.
    """
    # Load API config from config.yaml
    config_path = Path(__file__).parent / "src" / "config" / "config.yaml"
    api_config = {
        "host": "0.0.0.0",
        "port": 8000,
        "title": "LangGraph Agentic Base API",
        "version": "0.1.0",
        "description": "Multi-agent system API with supervisor and task planner",
        "enable_cors": True,
        "cors_origins": ["*"],
        "prefix": "/api/v1",
    }
    
    if config_path.exists():
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                config_data = yaml.safe_load(f) or {}
                api_config_from_file = config_data.get("api", {})
                api_config.update(api_config_from_file)
        except Exception as e:
            logger.warning(f"Failed to load API config from {config_path}: {e}")
    
    # Create FastAPI app
    app = FastAPI(
        title=api_config["title"],
        version=api_config["version"],
        description=api_config["description"],
    )
    
    # Configure CORS
    if api_config.get("enable_cors", True):
        origins = api_config.get("cors_origins", ["*"])
        app.add_middleware(
            CORSMiddleware,
            allow_origins=origins,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
    
    # Include API router
    prefix = api_config.get("prefix", "/api/v1")
    app.include_router(api_router, prefix=prefix)
    
    @app.get("/")
    async def root():
        """Root endpoint."""
        return {
            "message": "LangGraph Agentic Base API",
            "version": api_config["version"],
            "docs": "/docs",
            "api_prefix": prefix,
        }
    
    @app.get("/health")
    async def health():
        """Health check endpoint."""
        return {"status": "healthy"}
    
    return app


def run_api() -> None:
    """Run the FastAPI server."""
    # Load API config
    config_path = Path(__file__).parent / "src" / "config" / "config.yaml"
    api_config = {
        "host": "0.0.0.0",
        "port": 8000,
    }
    
    if config_path.exists():
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                config_data = yaml.safe_load(f) or {}
                api_config_from_file = config_data.get("api", {})
                api_config.update(api_config_from_file)
        except Exception as e:
            logger.warning(f"Failed to load API config: {e}")
    
    app = create_app()
    
    logger.info(f"Starting API server on {api_config['host']}:{api_config['port']}")
    logger.info(f"API documentation available at http://{api_config['host']}:{api_config['port']}/docs")
    
    uvicorn.run(
        app,
        host=api_config["host"],
        port=api_config["port"],
        log_level="info",
    )


def main() -> None:
    """Main function supporting both CLI and API modes."""
    if len(sys.argv) < 2:
        print("Usage:")
        print("  CLI mode: python main.py '<user_input>'")
        print("  API mode: python main.py api")
        sys.exit(1)
    
    mode = sys.argv[1].lower()
    
    if mode == "api":
        # Run API server
        run_api()
    else:
        # CLI mode - run workflow
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

