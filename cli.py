"""CLI tool using Rich for interactive console."""

import sys
from typing import Optional

from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.prompt import Prompt
from rich.table import Table
from rich.text import Text
from rich.syntax import Syntax

from app.models.workflow_state import AgentState
from app.models.state_typed import AgentStateTyped
from app.utils.agent_metadata import get_agent_metadata_loader
from app.utils.logger import logger
from app.utils.settings import settings
from app.utils.workflow_cache import get_cached_workflow

console = Console()


def display_welcome() -> None:
    """Display welcome message with dynamically loaded agents."""
    # Load agent metadata dynamically
    loader = get_agent_metadata_loader()
    
    # Build agent list
    agent_lines = [
        "• Supervisor Agent - Routes tasks intelligently",
        "• Planner Agent - Creates execution plans",
    ]
    
    # Add other agents dynamically (exclude supervisor and planner)
    other_agents = loader.get_available_agents(exclude=["supervisor", "planner"])
    
    # Format agent names nicely (capitalize and add spaces)
    def format_agent_name(name: str) -> str:
        """Format agent name for display (e.g., 'general_qa' -> 'General QA', 'neo4j' -> 'Neo4j')."""
        # Handle special cases
        special_cases = {
            "qa": "QA",
            "neo4j": "Neo4j",
        }
        
        # Split by underscore and format each word
        words = name.split("_")
        formatted_words = []
        for word in words:
            if word.lower() in special_cases:
                formatted_words.append(special_cases[word.lower()])
            else:
                formatted_words.append(word.capitalize())
        
        return " ".join(formatted_words)
    
    # Sort agents alphabetically for consistent display
    for agent_name in sorted(other_agents.keys()):
        agent_meta = other_agents[agent_name]
        formatted_name = format_agent_name(agent_meta.name)
        agent_lines.append(f"• {formatted_name} Agent - {agent_meta.description}")
    
    welcome_text = """
    [bold cyan]LangGraph Agentic Base[/bold cyan]
    
    A LangGraph-based multi-agent system with:
    """ + "\n    ".join(agent_lines)
    
    console.print(Panel(welcome_text, title="Welcome", border_style="cyan"))


def display_result(result: dict) -> None:
    """Display workflow result using Rich formatting."""
    console.print()  # Empty line for spacing
    
    # Header panel
    header_panel = Panel(
        "[bold cyan]WORKFLOW RESULT[/bold cyan]",
        border_style="cyan",
        padding=(1, 2),
    )
    console.print(header_panel)

    # User input
    console.print(f"\n[bold yellow]📝 User Input:[/bold yellow] [white]{result['user_input']}[/white]")

    # Error if any
    if result.get("error"):
        error_panel = Panel(
            f"[bold red]❌ Error:[/bold red]\n{result['error']}",
            border_style="red",
            title="Error",
            padding=(1, 2),
        )
        console.print(f"\n{error_panel}")

    # Final result - enhanced formatting
    if result.get("final_result"):
        console.print("\n[bold green]✨ Result:[/bold green]")
        
        # Check if result contains markdown-like content
        result_text = result["final_result"]
        
        # Try to detect if it's markdown or plain text
        if any(marker in result_text for marker in ["#", "##", "```", "*", "-", "|"]):
            # Render as markdown
            result_panel = Panel(
                Markdown(result_text),
                border_style="green",
                title="[bold green]Result[/bold green]",
                padding=(1, 2),
                expand=False,
            )
        else:
            # Render as formatted text
            result_panel = Panel(
                result_text,
                border_style="green",
                title="[bold green]Result[/bold green]",
                padding=(1, 2),
                expand=False,
            )
        
        console.print(result_panel)

    # Usage statistics
    usage_stats = result.get("usage_stats", {})
    agent_usage = usage_stats.get("agent_usage", {})
    tool_usage = usage_stats.get("tool_usage", {})

    if agent_usage or tool_usage:
        console.print("\n[bold magenta]📊 Usage Statistics:[/bold magenta]")

        # Agent usage table
        if agent_usage:
            agent_table = Table(
                title="[bold cyan]Agent Usage[/bold cyan]",
                show_header=True,
                header_style="bold cyan",
                border_style="cyan",
                row_styles=["", "dim"],
            )
            agent_table.add_column("Agent", style="cyan", no_wrap=True)
            agent_table.add_column("Count", justify="right", style="green")
            for agent, count in agent_usage.items():
                agent_table.add_row(agent, str(count))
            console.print(agent_table)

        # Tool usage table
        if tool_usage:
            tool_table = Table(
                title="[bold cyan]Tool Usage[/bold cyan]",
                show_header=True,
                header_style="bold cyan",
                border_style="cyan",
                row_styles=["", "dim"],
            )
            tool_table.add_column("Tool", style="cyan", no_wrap=True)
            tool_table.add_column("Count", justify="right", style="green")
            for tool, count in tool_usage.items():
                tool_table.add_row(tool, str(count))
            console.print(tool_table)

    # Messages - optional, can be collapsed
    messages = result.get("messages", [])
    if messages:
        console.print("\n[bold blue]💬 Execution Messages:[/bold blue]")
        messages_panel_content = []
        for msg in messages:
            role = msg.get("role", "unknown")
            content = msg.get("content", "")
            # Truncate long messages
            display_content = content[:300] + "..." if len(content) > 300 else content
            messages_panel_content.append(f"[bold cyan]{role}[/bold cyan]: {display_content}")
        
        messages_panel = Panel(
            "\n".join(messages_panel_content),
            border_style="blue",
            title="[bold blue]Messages[/bold blue]",
            padding=(1, 2),
            expand=False,
        )
        console.print(messages_panel)

    # Footer
    console.print("\n" + "[dim]" + "─" * 80 + "[/dim]")


def run_workflow(user_input: str, thread_id: Optional[str] = None) -> dict:
    """Run the workflow with user input and optional thread_id for conversation history.

    Args:
        user_input: User's input/query.
        thread_id: Optional thread ID for conversation continuity. If None, creates new thread.

    Returns:
        Dictionary with workflow result and metadata.
    """
    import uuid

    logger.info(f"Starting workflow with input: {user_input}")

    # Generate thread_id if not provided (for new conversation)
    if thread_id is None:
        thread_id = str(uuid.uuid4())
        logger.info(f"Created new conversation thread: {thread_id}")
    else:
        logger.info(f"Continuing conversation thread: {thread_id}")

    # Get cached workflow (initialized once at startup)
    app = get_cached_workflow()

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
        
        with console.status("[bold green]Executing workflow...", spinner="dots"):
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
            "messages": [],
        }


def interactive_mode() -> None:
    """Run in interactive mode with conversation history support."""
    import uuid

    display_welcome()

    # Initialize workflow cache at startup (agents and tools loaded once)
    console.print("[dim]Initializing workflow cache...[/dim]")
    get_cached_workflow()
    console.print("[dim]Workflow cache initialized successfully![/dim]\n")

    # Create a thread_id for this interactive session
    thread_id = str(uuid.uuid4())
    console.print(f"[dim]Conversation thread ID: {thread_id}[/dim]\n")

    while True:
        console.print("\n")
        user_input = Prompt.ask("[bold cyan]Enter your request[/bold cyan] (or 'quit' to exit)")

        if user_input.lower() in ["quit", "exit", "q"]:
            console.print("[bold yellow]Goodbye![/bold yellow]")
            break

        if not user_input.strip():
            console.print("[bold red]Please enter a valid request.[/bold red]")
            continue

        # Use the same thread_id for conversation continuity
        result = run_workflow(user_input, thread_id=thread_id)
        display_result(result)


def main() -> None:
    """Main CLI function."""
    if len(sys.argv) > 1:
        # Single command mode - initialize workflow cache first
        console.print("[dim]Initializing workflow cache...[/dim]")
        get_cached_workflow()
        console.print("[dim]Workflow cache initialized successfully![/dim]\n")

        user_input = " ".join(sys.argv[1:])
        result = run_workflow(user_input)
        display_result(result)
    else:
        # Interactive mode
        interactive_mode()


if __name__ == "__main__":
    main()

