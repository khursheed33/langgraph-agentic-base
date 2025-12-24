"""Planner agent implementation."""

import json
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.output_parsers import JsonOutputParser

from src.agents.base_agent import BaseAgent
from src.constants import AgentType
from src.models.state import AgentState, Task, TaskList, UsageStats
from src.models.planner import PlannerOutput
from src.utils.logger import get_logger

logger = get_logger()


def extract_json_from_text(text: str) -> str:
    """Extract JSON from text, handling markdown code blocks."""
    # Try to find JSON in markdown code blocks
    json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', text, re.DOTALL)
    if json_match:
        return json_match.group(1)
    
    # Try to find JSON object directly
    json_match = re.search(r'\{.*\}', text, re.DOTALL)
    if json_match:
        return json_match.group(0)
    
    # Return original text if no JSON found
    return text


class PlannerAgent(BaseAgent):
    """Planner agent that creates task plans."""

    def __init__(self) -> None:
        """Initialize planner agent."""
        super().__init__("planner")
        self.json_parser = JsonOutputParser(pydantic_object=PlannerOutput)

    def execute(
        self, state: AgentState, usage_stats: UsageStats
    ) -> tuple[AgentState, UsageStats]:
        """Execute planner to create task list."""
        logger.info("Planner agent executing...")
        usage_stats.increment_agent_usage("planner")

        try:
            # Format prompt template with user input
            user_input_text = f"User Input: {state.user_input}"
            messages = self.prompt_template.format_messages(input=user_input_text)

            response = self.llm.invoke(messages)
            logger.debug(f"Planner LLM response: {response.content[:500]}")  # Log first 500 chars
            
            # Extract JSON from response (handles markdown code blocks)
            json_text = extract_json_from_text(response.content)
            
            try:
                planner_output_dict = self.json_parser.parse(json_text)
            except Exception as parse_error:
                logger.error(f"JSON parsing error: {parse_error}")
                logger.error(f"Response content: {response.content}")
                logger.error(f"Extracted JSON text: {json_text}")
                # Try to parse as raw JSON as fallback
                try:
                    planner_output_dict = json.loads(json_text)
                    logger.info("Successfully parsed JSON using fallback method")
                except json.JSONDecodeError:
                    raise ValueError(f"Failed to parse planner output as JSON: {parse_error}")

            # Convert agent strings to AgentType enums
            if "tasks" in planner_output_dict:
                for task_dict in planner_output_dict["tasks"]:
                    if "agent" in task_dict and isinstance(task_dict["agent"], str):
                        try:
                            task_dict["agent"] = AgentType(task_dict["agent"])
                        except ValueError:
                            # If agent name doesn't match any AgentType, try to find closest match
                            agent_str = task_dict["agent"].lower()
                            for agent_type in AgentType:
                                if agent_type.value == agent_str:
                                    task_dict["agent"] = agent_type
                                    break
                            else:
                                logger.error(f"Unknown agent type: {task_dict['agent']}")
                                raise ValueError(f"Unknown agent type: {task_dict['agent']}. Available agents: {[a.value for a in AgentType]}")

            planner_output = PlannerOutput(**planner_output_dict)

            # Convert to TaskList
            task_list = TaskList(tasks=planner_output.tasks)
            state.task_list = task_list

            logger.info(
                f"Planner created {len(task_list.tasks)} tasks: "
                f"{[t.agent.value + ': ' + t.description for t in task_list.tasks]}"
            )

            # Save tasks to tasks/ folder
            try:
                tasks_dir = Path("tasks")
                tasks_dir.mkdir(exist_ok=True)
                
                # Generate unique task file name with timestamp
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                task_file = tasks_dir / f"task_{timestamp}.json"
                
                # Convert task list to JSON-serializable format
                task_data = {
                    "user_input": state.user_input,
                    "created_at": timestamp,
                    "reasoning": planner_output.reasoning,
                    "tasks": [
                        {
                            "agent": task.agent.value,
                            "description": task.description,
                            "status": task.status.value,
                            "result": task.result,
                            "error": task.error,
                        }
                        for task in task_list.tasks
                    ],
                }
                
                with open(task_file, "w", encoding="utf-8") as f:
                    json.dump(task_data, f, indent=2, ensure_ascii=False)
                
                logger.info(f"Saved task list to {task_file}")
            except Exception as e:
                logger.error(f"Failed to save task list: {e}")

            # Add message to state
            state.messages.append(
                {
                    "role": "planner",
                    "content": f"Created task plan with {len(task_list.tasks)} tasks. "
                    f"Reasoning: {planner_output.reasoning}",
                }
            )

        except Exception as e:
            logger.error(f"Planner error: {e}")
            import traceback
            logger.error(f"Planner traceback: {traceback.format_exc()}")
            state.error = f"Planner error: {str(e)}"
            # Set current_agent to END to prevent infinite loop
            # The supervisor should handle this gracefully
            state.current_agent = None

        return state, usage_stats

