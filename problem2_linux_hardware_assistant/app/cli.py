"""
Interactive CLI for Linux Hardware Q&A Assistant.
Provides rich terminal formatting, command inspection, and multi-turn conversation.
"""
import sys
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import json
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.syntax import Syntax
from rich.prompt import Prompt

from .core_agent import HardwareQAAgent
from .memory_context import session_context

console = Console(force_terminal=True, legacy_windows=False)

def run_cli():
    agent = HardwareQAAgent(session_context)
    
    console.print("\n[bold cyan]====================================================================[/bold cyan]")
    console.print("[bold yellow]       LOCAL LINUX HARDWARE Q&A ASSISTANT (CLI INTERFACE)           [/bold yellow]")
    console.print("[bold cyan]====================================================================[/bold cyan]")
    console.print("[dim]Type your question about RAM, CPU, SSD/NVMe, or GPU. Type 'exit' to quit.[/dim]\n")

    while True:
        try:
            query = Prompt.ask("[bold green]User[/bold green]")
            if not query.strip():
                continue
            if query.strip().lower() in ("exit", "quit", "q"):
                console.print("[bold yellow]Exiting Hardware Assistant. Goodbye![/bold yellow]")
                break

            response = agent.process_query(query)

            # Display Tool Execution Trace
            if response["tool_called"]:
                console.print(f"[dim]🔧 Tool Dispatched: [bold cyan]{response['tool_called']}[/bold cyan][/dim]")
                
                # Show Structured JSON payload in collapsible/styled block
                json_str = json.dumps(response["structured_data"], indent=2)
                syntax = Syntax(json_str, "json", theme="monokai", line_numbers=False)
                console.print(Panel(syntax, title="[dim]Normalized Structured JSON Output[/dim]", border_style="blue"))

            # Display Grounded Answer
            console.print(Panel(
                response["answer"],
                title="[bold green]Assistant Answer (Verified System Facts)[/bold green]",
                border_style="green"
            ))
            console.print()

        except KeyboardInterrupt:
            console.print("\n[bold yellow]Session ended.[/bold yellow]")
            break

if __name__ == "__main__":
    run_cli()
