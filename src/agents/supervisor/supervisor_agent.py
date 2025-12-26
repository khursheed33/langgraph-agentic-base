"""Supervisor agent implementation."""

from langchain_core.output_parsers import JsonOutputParser

from src.agents.base_agent import BaseAgent
from src.constants import AgentType, END_NODE
from src.models.workflow_state import AgentState, UsageStats
from src.models.supervisor import SupervisorDecision
from src.utils.context_utils import build_supervisor_context
from src.utils.logger import logger
from src.utils.prompt_utils import load_prompt_template_with_agents
from src.utils.token_calculator import track_token_usage


class SupervisorAgent(BaseAgent):
    """Supervisor agent that routes tasks to appropriate agents."""

    def __init__(self) -> None:
        """Initialize supervisor agent."""
        super().__init__("supervisor")
        self.json_parser = JsonOutputParser(pydantic_object=SupervisorDecision)
        # Override prompt template with dynamic agent info
        self.prompt_template = load_prompt_template_with_agents(
            "supervisor",
            exclude_agents=["supervisor"],
            format_type="supervisor"
        )

    def execute(
        self, state: AgentState, usage_stats: UsageStats
    ) -> tuple[AgentState, UsageStats]:
        """Execute supervisor routing logic."""
        logger.info("Supervisor agent executing...")
        usage_stats.increment_agent_usage("supervisor")

        # Check if there's an error and planner has been called multiple times
        # Prevent infinite loops by ending workflow if planner keeps failing
        planner_call_count = sum(
            1 for msg in state.messages 
            if msg.get("role") == "planner" or 
            (isinstance(msg, dict) and "planner" in str(msg.get("content", "")).lower())
        )
        
        if state.error and "planner" in state.error.lower() and planner_call_count >= 3:
            logger.error("Planner has failed multiple times. Ending workflow.")
            state.current_agent = END_NODE
            state.final_result = f"Workflow ended due to planner errors: {state.error}"
            return state, usage_stats

        # Prepare context for supervisor
        context = build_supervisor_context(state)

        # Get routing decision from LLM
        try:
            # Format prompt template with context
            formatted_messages = self.prompt_template.format_messages(input=context)
            messages = formatted_messages

            response = self.llm.invoke(messages)
            track_token_usage(response, usage_stats)
            decision_dict = self.json_parser.parse(response.content)

            decision = SupervisorDecision(**decision_dict)
            logger.info(
                f"Supervisor decision: route to {decision.next_agent}. "
                f"Reasoning: {decision.reasoning}"
            )

            # Update state - store as string to handle END_NODE
            state.current_agent = decision.next_agent
            
            # Handle empty task list - end workflow
            if state.task_list and len(state.task_list.tasks) == 0:
                state.current_agent = END_NODE
                state.final_result = "No tasks required for this request."
            
            # Build final result if ending with tasks
            if decision.next_agent == END_NODE and state.task_list and len(state.task_list.tasks) > 0:
                results = []
                for task in state.task_list.tasks:
                    results.append(f"Task [{task.agent.value}]: {task.description}")
                    if task.result:
                        results.append(f"  Result: {task.result}")
                    if task.error:
                        results.append(f"  Error: {task.error}")
                state.final_result = "\n".join(results)

            # Add message to state
            state.messages.append(
                {
                    "role": "supervisor",
                    "content": f"Routing to {decision.next_agent}: {decision.reasoning}",
                }
            )

        except Exception as e:
            logger.error(f"Supervisor error: {e}")
            state.error = f"Supervisor error: {str(e)}"
            state.current_agent = None

        return state, usage_stats

