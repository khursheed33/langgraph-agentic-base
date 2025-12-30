"""Main entry point for the application."""

import sys
from typing import Dict, Any

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import api_router
from app.config import load_api_config
from app.services.workflow_service import run_workflow
from app.utils.logger import logger


def create_app() -> FastAPI:
    """Create and configure FastAPI application.

    Returns:
        Configured FastAPI application instance.
    """
    # Load API configuration
    api_config = load_api_config()

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
    # Load API configuration
    api_config = load_api_config()

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

