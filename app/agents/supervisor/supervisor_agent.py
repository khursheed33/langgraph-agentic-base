"""Supervisor agent implementation."""

from langchain_core.output_parsers import JsonOutputParser

from app.agents.base_agent import BaseAgent
from app.constants import (
    AgentType,
    END_NODE,
    SUPERVISOR_TECHNICAL_DIFFICULTIES_MSG,
    SUPERVISOR_SAFETY_STOP_MSG,
    SUPERVISOR_PLANNER_ERROR_MSG,
    SUPERVISOR_GREETING_MSG,
    SUPERVISOR_NO_TASKS_MSG,
)
from app.models.workflow_state import AgentState, UsageStats
from app.models.supervisor import SupervisorDecision
from app.utils.context_utils import build_supervisor_context
from app.utils.logger import logger
from app.utils.prompt_utils import load_prompt_template_with_agents
from app.utils.token_calculator import track_token_usage
from app.guardrails.intelligent_guardrails import IntelligentInputGuardrail, IntentCategory
import asyncio

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
        # Intent classifier (guardrail)
        self.intent_guardrail = IntelligentInputGuardrail()

    async def _classify_intent(self, text: str):
        result = await self.intent_guardrail.check(text)
        return result

    def execute(
        self, state: AgentState, usage_stats: UsageStats
    ) -> tuple[AgentState, UsageStats]:
        """Execute supervisor routing logic."""
        logger.info("Supervisor agent executing...")
        usage_stats.increment_agent_usage("supervisor")

        # Check if there's an error and planner has been called multiple times
        planner_call_count = sum(
            1 for msg in state.messages 
            if msg.get("role") == "planner" or 
            (isinstance(msg, dict) and "planner" in str(msg.get("content", "")).lower())
        )
        if state.error and "planner" in state.error.lower() and planner_call_count >= 3:
            logger.error("Planner has failed multiple times. Ending workflow.")
            state.current_agent = END_NODE
            state.final_result = SUPERVISOR_PLANNER_ERROR_MSG.format(error=state.error)
            return state, usage_stats

        # Prepare context for supervisor
        context = build_supervisor_context(state)
        response = None
        try:
            # Format prompt template with context
            formatted_messages = self.prompt_template.format_messages(input=context)
            messages = formatted_messages
            response = self.llm.invoke(messages)
            track_token_usage(response, usage_stats)
            decision = None
            response_content = response.content.strip()
            logger.debug(f"Raw LLM response content: '{response_content}'")
            # Special case: if LLM responds with just "next_agent" (with or without quotes), route to planner
            cleaned_response = response_content.lower().strip().strip('"').strip("'")
            logger.debug(f"Supervisor LLM response: '{response_content}' (cleaned: '{cleaned_response}')")
            if cleaned_response == "next_agent" or response_content.strip() in ['"next_agent"', "'next_agent'"]:
                decision = SupervisorDecision(
                    next_agent="planner",
                    reasoning="LLM response unclear, routing to planner for task planning"
                )
                logger.debug("Using special case handling for 'next_agent' response")
            else:
                # Strategy 1: Try standard JSON parsing
                try:
                    decision_dict = self.json_parser.parse(response_content)
                    logger.debug(f"Supervisor parse output: {decision_dict}")
                    if (
                        isinstance(decision_dict, dict)
                        and decision_dict.get("next_agent")
                        and decision_dict.get("reasoning")
                    ):
                        decision = SupervisorDecision(**decision_dict)
                    else:
                        logger.warning(f"Parsed dict missing required fields: {decision_dict}. Fallback triggered.")
                except Exception as e:
                    logger.warning(f"First JSON parse strategy failed: {type(e).__name__}: {e}")
                    logger.debug(f"Response that failed JSON parsing: '{response_content}'")
                    # Strategy 2: Try manual JSON parsing
                    try:
                        import json
                        if response_content.startswith('{') and response_content.endswith('}'):
                            decision_dict = json.loads(response_content)
                            logger.debug(f"Manual JSON parse output: {decision_dict}")
                            if (
                                isinstance(decision_dict, dict)
                                and decision_dict.get("next_agent")
                                and decision_dict.get("reasoning")
                            ):
                                decision = SupervisorDecision(**decision_dict)
                            else:
                                logger.warning(f"Manual JSON produced incomplete result: {decision_dict}")
                    except Exception as e2:
                        logger.warning(f"Manual JSON parsing failed: {e2}")
                # If JSON parsing failed, try to extract agent name directly
                if decision is None:
                    logger.warning(f"JSON parsing failed for response: {response_content}")
                    available_agents = [
                        AgentType.NEO4J,
                        AgentType.FILESYSTEM,
                        AgentType.GENERAL_QA,
                        AgentType.MATHEMATICS,
                        AgentType.PLANNER,
                    ]
                    for agent in available_agents:
                        if agent.value in response_content.lower():
                            decision = SupervisorDecision(
                                next_agent=agent,
                                reasoning=f"Extracted agent '{agent.value}' from LLM response"
                            )
                            break
                    # If still no decision, check for END_NODE
                    if (decision is None and ("end" in response_content.lower() or END_NODE in response_content)):
                        decision = SupervisorDecision(
                            next_agent=END_NODE,
                            reasoning="LLM indicated workflow should end"
                        )
            # If we still don't have a decision, use classifier as fallback
            if decision is None:
                logger.warning("All parsing strategies failed, using classifier fallback logic")
                user_input = state.user_input
                result = asyncio.run(self._classify_intent(user_input))
                intent = result.metadata.get("intent")
                confidence = result.metadata.get("confidence")

                if not result.passed:
                    decision = SupervisorDecision(
                        next_agent=END_NODE,
                        reasoning=result.reason or SUPERVISOR_SAFETY_STOP_MSG
                    )
                else:
                    # Map intents to agents
                    agent_map = {
                        "information_seeking": AgentType.GENERAL_QA,
                        "conversational": AgentType.GENERAL_QA,
                        "data_retrieval": AgentType.NEO4J,
                        "analysis_request": AgentType.NEO4J,
                        "file_operations": AgentType.FILESYSTEM,
                        "database_operations": AgentType.NEO4J,
                        "mathematics": AgentType.MATHEMATICS,
                        "help_request": AgentType.GENERAL_QA,
                    }
                    mapped_agent = agent_map.get(intent, AgentType.PLANNER)
                    short_reason = result.reason or f"Mapped intent '{intent}'"
                    decision = SupervisorDecision(
                        next_agent=mapped_agent,
                        reasoning=short_reason
                    )
                    # If greeting and very short, end directly
                    if intent == "conversational" and len(user_input.split()) <= 3:
                        decision = SupervisorDecision(
                            next_agent=END_NODE,
                            reasoning="Simple greeting - ending workflow directly"
                        )
                        state.final_result = SUPERVISOR_GREETING_MSG
            logger.info(
                f"Supervisor decision: route to {decision.next_agent}. "
                f"Reasoning: {decision.reasoning}"
            )
            # Update state - store as string to handle END_NODE
            state.current_agent = decision.next_agent
            # Handle empty task list - end workflow
            if state.task_list and len(state.task_list.tasks) == 0:
                state.current_agent = END_NODE
                state.final_result = SUPERVISOR_NO_TASKS_MSG
            # Build final result if ending with tasks
            if decision.next_agent == END_NODE and state.task_list and len(state.task_list.tasks) > 0:
                results = []
                for task in state.task_list.tasks:
                    if task.result:
                        results.append(task.result)
                    elif task.error:
                        results.append(f"Error: {task.error}")
                state.final_result = "\n".join(results) if len(results) > 1 else (results[0] if results else "")
            # Add message to state
            state.messages.append(
                {
                    "role": "supervisor",
                    "content": f"Routing to {decision.next_agent}: {decision.reasoning}",
                }
            )
        except Exception as e:
            logger.error(f"Supervisor error: {type(e).__name__}: {e}")
            logger.error(f"Response content that caused error: '{response_content}'")
            response_text = response.content.lower() if response else ""
            refusal_indicators = [
                "sorry", "can't help", "unable to assist", "cannot assist",
                "not able to", "refuse", "decline", "won't"
            ]
            is_refusal = any(indicator in response_text for indicator in refusal_indicators)
            if is_refusal:
                logger.warning("LLM refused to provide routing decision - ending workflow")
                state.current_agent = END_NODE
                state.final_result = SUPERVISOR_SAFETY_STOP_MSG
                state.error = None  # Clear the error since this is expected behavior
            else:
                logger.error("All parsing failed, ending workflow")
                state.current_agent = END_NODE
                state.final_result = SUPERVISOR_TECHNICAL_DIFFICULTIES_MSG
        return state, usage_stats
