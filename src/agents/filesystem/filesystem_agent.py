"""File system agent implementation."""

from langchain_core.messages import ToolMessage

from src.agents.base_agent import BaseAgent
from src.constants import AgentType, TaskStatus
from src.models.state import AgentState, UsageStats
from src.utils.agent_utils import (
    build_agent_messages,
    build_task_description,
    find_pending_task,
    get_previous_task_results,
)
from src.utils.logger import logger
from src.utils.task_persistence import update_task_file
from src.utils.token_calculator import track_token_usage


class FileSystemAgent(BaseAgent):
    """File system agent."""

    def __init__(self) -> None:
        """Initialize file system agent."""
        super().__init__("filesystem")
        # Bind tools to LLM (LangGraph cookbook pattern)
        self.tools_by_name = {tool.name: tool for tool in self.tools}
        self.llm_with_tools = self.llm.bind_tools(self.tools) if self.tools else self.llm

    def execute(
        self, state: AgentState, usage_stats: UsageStats
    ) -> tuple[AgentState, UsageStats]:
        """Execute file system agent task."""
        logger.info("File system agent executing...")
        usage_stats.increment_agent_usage("filesystem")

        if not state.task_list:
            logger.error("No task list available")
            state.error = "No task list available"
            return state, usage_stats

        # Find current task for filesystem agent
        current_task, task_index = find_pending_task(state.task_list, AgentType.FILESYSTEM)

        if not current_task:
            logger.warning("No pending FileSystem task found")
            state.messages.append(
                {"role": "filesystem", "content": "No pending task for FileSystem agent"}
            )
            return state, usage_stats

        # Mark task as in progress
        current_task.status = TaskStatus.IN_PROGRESS

        try:
            # Get previous agent results from completed tasks
            previous_results = get_previous_task_results(
                state.task_list, 
                include_agents=[AgentType.NEO4J]
            )
            
            # Build task description
            task_description = build_task_description(
                current_task,
                state.user_input,
                previous_results if previous_results else None
            )
            
            # Log task description for debugging
            logger.debug(f"FileSystem agent task description length: {len(task_description)}")
            logger.debug(f"FileSystem agent task description preview: {task_description[:500]}...")

            # Execute agent using LangGraph cookbook pattern
            # Step 1: Call LLM with tools bound
            # Build messages using utility function
            messages = build_agent_messages(self.prompt_template, task_description)

            # Get LLM response (may include tool calls)
            llm_response = self.llm_with_tools.invoke(messages)
            track_token_usage(llm_response, usage_stats)
            result_text = ""
            tool_calls_executed = False
            
            # Step 2: Execute tools if LLM made tool calls (LangGraph cookbook pattern)
            if hasattr(llm_response, "tool_calls") and llm_response.tool_calls:
                tool_messages = []
                for tool_call in llm_response.tool_calls:
                    tool_name = tool_call.get("name", "")
                    tool_args = tool_call.get("args", {})
                    
                    if tool_name in self.tools_by_name:
                        tool = self.tools_by_name[tool_name]
                        try:
                            # Execute tool
                            observation = tool.invoke(tool_args)
                            tool_messages.append(
                                ToolMessage(
                                    content=str(observation),
                                    tool_call_id=tool_call.get("id", ""),
                                )
                            )
                            usage_stats.increment_tool_usage(tool_name)
                            tool_calls_executed = True
                        except Exception as e:
                            logger.error(f"Tool {tool_name} error: {e}")
                            tool_messages.append(
                                ToolMessage(
                                    content=f"Error: {str(e)}",
                                    tool_call_id=tool_call.get("id", ""),
                                )
                            )
                
                # If tools were called, get final LLM response
                if tool_calls_executed:
                    final_messages = messages + [llm_response] + tool_messages
                    final_response = self.llm_with_tools.invoke(final_messages)
                    track_token_usage(final_response, usage_stats)
                    result_text = final_response.content if hasattr(final_response, "content") else str(final_response)
                    # Log tool execution results
                    logger.info(f"FileSystem agent executed {len(tool_messages)} tool(s)")
                    for tool_msg in tool_messages:
                        logger.debug(f"Tool result: {str(tool_msg.content)[:200]}...")
                else:
                    result_text = llm_response.content if hasattr(llm_response, "content") else str(llm_response)
                    logger.warning("FileSystem agent did not execute any tools - LLM may not have called write_file")
            else:
                # No tool calls, use LLM response directly
                result_text = llm_response.content if hasattr(llm_response, "content") else str(llm_response)
                logger.warning("FileSystem agent LLM did not make tool calls - may need to call write_file tool")

            # Ensure result_text is not empty
            if not result_text or not result_text.strip():
                logger.error("FileSystem agent result text is empty")
                result_text = "Error: FileSystem agent did not complete the task"

            # Log result text length for debugging
            logger.debug(f"FileSystem agent result text length: {len(result_text)} characters")

            # Mark task as completed
            state.task_list.mark_task_completed(task_index, result_text)

            logger.info(f"FileSystem task completed: {current_task.description}")

            # Update task file
            update_task_file(state)

            # Add message to state
            state.messages.append(
                {
                    "role": "filesystem",
                    "content": f"Completed task: {current_task.description}\nResult: {result_text}",
                }
            )

        except Exception as e:
            logger.error(f"FileSystem agent error: {e}")
            state.task_list.mark_task_failed(task_index, str(e))
            state.error = f"FileSystem agent error: {str(e)}"

        return state, usage_stats

