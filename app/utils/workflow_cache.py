"""Workflow cache manager for optimized LangGraph workflow initialization.

This module provides a singleton pattern for caching the compiled LangGraph workflow,
ensuring that agents and tools are initialized only once at startup rather than
per user query.
"""

from typing import Optional

from langgraph.graph.state import CompiledStateGraph

from app.utils.logger import logger
from app.workflow.graph import create_workflow

# Singleton compiled workflow instance
_cached_workflow: Optional[CompiledStateGraph] = None


def get_cached_workflow() -> CompiledStateGraph:
    """Get or create singleton compiled workflow instance.

    This ensures the workflow (including all agents and tools) is initialized
    only once at startup, improving performance for subsequent queries.

    Returns:
        Compiled LangGraph application ready to be invoked.
    """
    global _cached_workflow
    if _cached_workflow is None:
        logger.info("Initializing workflow cache - creating compiled workflow...")
        _cached_workflow = create_workflow()
        logger.info("Workflow cache initialized successfully")
    return _cached_workflow


def clear_workflow_cache() -> None:
    """Clear the cached workflow instance.

    This can be useful for testing or when agent configurations change.
    """
    global _cached_workflow
    if _cached_workflow is not None:
        logger.info("Clearing workflow cache")
        _cached_workflow = None


def is_workflow_cached() -> bool:
    """Check if the workflow is currently cached.

    Returns:
        True if workflow is cached, False otherwise.
    """
    return _cached_workflow is not None