"""Checkpoint management for LangGraph workflow state persistence."""

from pathlib import Path
from typing import Optional

from langgraph.checkpoint.memory import MemorySaver

from app.utils.logger import logger

# Singleton checkpointer instance
_checkpointer: Optional[MemorySaver] = None


def get_checkpointer() -> MemorySaver:
    """Get or create singleton checkpoint saver for workflow state persistence.
    
    Returns:
        MemorySaver instance for checkpointing workflow state (singleton).
    """
    global _checkpointer
    if _checkpointer is None:
        logger.info("Creating MemorySaver checkpointer for state persistence")
        _checkpointer = MemorySaver()
    return _checkpointer


def create_checkpointer() -> MemorySaver:
    """Create a checkpoint saver for workflow state persistence.
    
    DEPRECATED: Use get_checkpointer() instead for singleton pattern.
    
    Returns:
        MemorySaver instance for checkpointing workflow state.
    """
    return get_checkpointer()

