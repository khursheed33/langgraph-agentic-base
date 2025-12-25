"""Utility functions for persisting tasks to disk."""

import json
from datetime import datetime
from pathlib import Path
from typing import Optional

from src.models.state import AgentState, TaskList
from src.utils.logger import logger


def find_latest_task_file() -> Optional[Path]:
    """Find the most recent task file in the tasks/ directory."""
    tasks_dir = Path("tasks")
    if not tasks_dir.exists():
        return None
    
    task_files = list(tasks_dir.glob("task_*.json"))
    if not task_files:
        return None
    
    # Sort by modification time, most recent first
    task_files.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    return task_files[0]


def update_task_file(state: AgentState) -> None:
    """Update the most recent task file with current task list state."""
    try:
        task_file = find_latest_task_file()
        if not task_file:
            logger.debug("No task file found to update")
            return
        
        if not state.task_list:
            logger.debug("No task list to save")
            return
        
        # Read existing task file
        with open(task_file, "r", encoding="utf-8") as f:
            task_data = json.load(f)
        
        # Update tasks with current state
        task_data["tasks"] = [
            {
                "agent": task.agent.value,
                "description": task.description,
                "status": task.status.value,
                "result": task.result,
                "error": task.error,
            }
            for task in state.task_list.tasks
        ]
        
        # Write back
        with open(task_file, "w", encoding="utf-8") as f:
            json.dump(task_data, f, indent=2, ensure_ascii=False)
        
        logger.debug(f"Updated task file: {task_file}")
    except Exception as e:
        logger.error(f"Failed to update task file: {e}")


def save_task_list(state: AgentState, reasoning: Optional[str] = None) -> None:
    """Save task list to tasks/ folder with timestamp.
    
    Args:
        state: Agent state containing task list and user input.
        reasoning: Optional reasoning string from planner.
    """
    try:
        if not state.task_list:
            logger.warning("No task list to save")
            return
        
        tasks_dir = Path("tasks")
        tasks_dir.mkdir(exist_ok=True)
        
        # Generate unique task file name with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        task_file = tasks_dir / f"task_{timestamp}.json"
        
        # Convert task list to JSON-serializable format
        task_data = {
            "user_input": state.user_input,
            "created_at": timestamp,
            "reasoning": reasoning or "",
            "tasks": [
                {
                    "agent": task.agent.value,
                    "description": task.description,
                    "status": task.status.value,
                    "result": task.result,
                    "error": task.error,
                }
                for task in state.task_list.tasks
            ],
        }
        
        with open(task_file, "w", encoding="utf-8") as f:
            json.dump(task_data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Saved task list to {task_file}")
    except Exception as e:
        logger.error(f"Failed to save task list: {e}")

