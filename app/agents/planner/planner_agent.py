"""Planner agent implementation."""

import json

from langchain_core.output_parsers import JsonOutputParser

from app.agents.base_agent import BaseAgent
from app.constants import AgentType
from app.models.workflow_state import AgentState, TaskList, UsageStats
from app.models.planner import PlannerOutput
from app.utils.json_utils import extract_json_from_text
from app.utils.logger import logger
from app.utils.prompt_utils import load_prompt_template_with_agents
from app.utils.task_persistence import save_task_list
from app.utils.token_calculator import track_token_usage


class PlannerAgent(BaseAgent):
    """Planner agent that creates task plans."""

    def __init__(self) -> None:
        """Initialize planner agent."""
        super().__init__("planner")
        self.json_parser = JsonOutputParser(pydantic_object=PlannerOutput)
        # Override prompt template with dynamic agent info
        self.prompt_template = load_prompt_template_with_agents(
            "planner", 
            exclude_agents=["supervisor", "planner"],
            format_type="planner"
        )

    def execute(
        self, state: AgentState, usage_stats: UsageStats
    ) -> tuple[AgentState, UsageStats]:
        """Execute planner to create task list."""
        logger.info("Planner agent executing...")
        usage_stats.increment_agent_usage("planner")

        try:
            # Build context including conversation history
            context_parts = [f"User Input: {state.user_input}"]
            
            # Add conversation history if available
            if state.conversation_history:
                context_parts.append("\n=== Previous Conversation History ===")
                for i, entry in enumerate(state.conversation_history[-3:], 1):  # Last 3 conversations
                    prev_input = entry.get("user_input", "")
                    prev_result = entry.get("result", "")
                    context_parts.append(f"\nPrevious Question {i}: {prev_input}")
                    if prev_result:
                        # Truncate long results
                        result_preview = prev_result[:300] + "..." if len(prev_result) > 300 else prev_result
                        context_parts.append(f"Previous Answer {i}: {result_preview}")
                context_parts.append("\n=== End of Conversation History ===\n")
                context_parts.append("\nNote: Consider the conversation history when planning tasks. "
                                   "The user may be asking a follow-up question or referring to previous context.")
            
            user_input_text = "\n".join(context_parts)
            messages = self.prompt_template.format_messages(input=user_input_text)

            response = self.llm.invoke(messages)
            track_token_usage(response, usage_stats)
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
                            agent_str = str(task_dict["agent"]).lower()
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
            save_task_list(state, reasoning=planner_output.reasoning)

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

