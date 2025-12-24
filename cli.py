"""CLI tool using Rich for interactive console."""

import os
import sys
from typing import Optional

from dotenv import load_dotenv
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.prompt import Prompt
from rich.table import Table
from rich.text import Text
from rich.syntax import Syntax

from src.models.state import AgentState
from src.models.state_typed import AgentStateTyped
from src.utils.logger import get_logger
from src.workflow import create_workflow

# Load environment variables
load_dotenv()

logger = get_logger()
console = Console()


def display_welcome() -> None:
    """Display welcome message."""
    welcome_text = """
    [bold cyan]LangGraph Agentic Base[/bold cyan]
    
    A LangGraph-based multi-agent system with:
    • Supervisor Agent - Routes tasks intelligently
    • Planner Agent - Creates execution plans
    • Neo4j Agent - Database operations and query building
    • File System Agent - File operations
    • Query Agent - Handles greetings and general questions
    """
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


def run_workflow(user_input: str) -> dict:
    """Run the workflow with user input."""
    logger.info(f"Starting workflow with input: {user_input}")

    # Create workflow
    app = create_workflow()

    # Initialize state as dict (LangGraph expects dict/TypedDict)
    initial_state: AgentStateTyped = {
        "user_input": user_input,
        "task_list": None,
        "current_agent": None,
        "messages": [],
        "usage_stats": AgentState(user_input=user_input).usage_stats,
        "final_result": None,
        "error": None,
    }

    try:
        # Run workflow (LangGraph cookbook pattern)
        config = {"recursion_limit": int(os.getenv("MAX_ITERATIONS", "50"))}
        
        with console.status("[bold green]Executing workflow...", spinner="dots"):
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
        }

        logger.info("Workflow completed successfully")
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
    """Run in interactive mode."""
    display_welcome()

    while True:
        console.print("\n")
        user_input = Prompt.ask("[bold cyan]Enter your request[/bold cyan] (or 'quit' to exit)")

        if user_input.lower() in ["quit", "exit", "q"]:
            console.print("[bold yellow]Goodbye![/bold yellow]")
            break

        if not user_input.strip():
            console.print("[bold red]Please enter a valid request.[/bold red]")
            continue

        result = run_workflow(user_input)
        display_result(result)


def main() -> None:
    """Main CLI function."""
    if len(sys.argv) > 1:
        # Single command mode
        user_input = " ".join(sys.argv[1:])
        result = run_workflow(user_input)
        display_result(result)
    else:
        # Interactive mode
        interactive_mode()


if __name__ == "__main__":
    main()

