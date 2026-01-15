"""Main CLI application using Rich for beautiful terminal output"""
import json
import yaml
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from rich.syntax import Syntax
from rich.table import Table
from rich import print as rprint

from core.controller import Controller
from engine.ollama_inference import OllamaInferenceEngine


class AITASCLI:
    """Main CLI application"""

    def __init__(self, config_path: str = "config.yaml", use_llm: bool = True):
        self.console = Console()
        try:
            self.config = self._load_config(config_path)
        except:
            self.config = {}
        self.controller = None
        self.running = False
        self.use_llm = use_llm

    def _load_config(self, config_path: str) -> dict:
        """Load configuration from YAML"""
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)

    def initialize(self):
        """Initialize the controller with Ollama or rule-based parser"""
        self.console.print("\n[bold cyan]🤖 AITAS - AI Terminal Assistant[/bold cyan]\n")

        if self.use_llm:
            # Try to use Ollama
            self.console.print("[dim]Initializing Ollama LLM...[/dim]")

            try:
                # Get model name from config or use default
                model_name = self.config.get("model", {}).get("ollama_model", "llama3.2:1b")

                # Create Ollama engine
                engine = OllamaInferenceEngine(model_name=model_name)

                # Test connection
                if engine.test_connection():
                    self.console.print(f"[bold green]✓ Connected to Ollama ({model_name})[/bold green]\n")
                    self.controller = Controller(inference_engine=engine, config=self.config, use_llm=True)
                else:
                    self.console.print("[yellow]⚠ Ollama not available, falling back to rule-based parser[/yellow]\n")
                    self.controller = Controller(config=self.config, use_llm=False)

            except Exception as e:
                self.console.print(f"[yellow]⚠ Could not connect to Ollama: {str(e)}[/yellow]")
                self.console.print("[yellow]Falling back to rule-based parser[/yellow]\n")
                self.controller = Controller(config=self.config, use_llm=False)
        else:
            # Use rule-based parser
            self.console.print("[dim]Using rule-based parser - instant responses![/dim]")
            self.controller = Controller(config=self.config, use_llm=False)
            self.console.print("[bold green]✓ Ready![/bold green]\n")

    def display_result(self, result: dict):
        """Display execution result in a nice format"""
        if result.get("success"):
            # Show command
            if result.get("command"):
                json_str = json.dumps(result["command"], indent=2)
                syntax = Syntax(json_str, "json", theme="monokai", line_numbers=False)
                self.console.print(Panel(syntax, title="[bold green]Command[/bold green]", border_style="green"))

            # Show execution result
            exec_result = result.get("result", {})
            message = exec_result.get("message", "Success")

            self.console.print(f"\n[bold green]✓ {message}[/bold green]")

            # Show additional info
            if "content" in exec_result:
                content = exec_result["content"]
                if len(content) > 500:
                    content = content[:500] + "..."
                self.console.print(f"\n[dim]{content}[/dim]")

            if "items" in exec_result:
                table = Table(title="Directory Contents")
                table.add_column("Name", style="cyan")
                table.add_column("Type", style="magenta")

                for item in exec_result["items"][:20]:
                    table.add_row(item["name"], item["type"])

                self.console.print("\n")
                self.console.print(table)

            # Show shell command output
            if "output" in exec_result and exec_result["output"]:
                self.console.print(f"\n[cyan]Output:[/cyan]")
                self.console.print(f"[dim]{exec_result['output']}[/dim]")

            if "error" in exec_result and exec_result["error"]:
                self.console.print(f"\n[yellow]Stderr:[/yellow]")
                self.console.print(f"[dim]{exec_result['error']}[/dim]")

        else:
            # Show error
            # Check if error is in top level or in result dict
            error_msg = result.get("error")
            if not error_msg and result.get("result"):
                error_msg = result["result"].get("error") or result["result"].get("message")
            if not error_msg:
                error_msg = "Unknown error"

            reason = result.get("reason", "")

            self.console.print(Panel(
                f"[bold red]Error:[/bold red] {error_msg}\n{reason}",
                border_style="red"
            ))

            if result.get("command"):
                json_str = json.dumps(result["command"], indent=2)
                syntax = Syntax(json_str, "json", theme="monokai", line_numbers=False)
                self.console.print(Panel(syntax, title="[dim]Attempted Command[/dim]", border_style="dim"))

    def run(self):
        """Main CLI loop"""
        self.running = True

        self.console.print("[bold]Commands:[/bold]")
        self.console.print("  [cyan]exit[/cyan] or [cyan]quit[/cyan] - Exit AITAS")
        self.console.print("  [cyan]help[/cyan] - Show help\n")

        while self.running:
            try:
                # Get user input
                user_input = Prompt.ask("\n[bold yellow]AITAS[/bold yellow]")

                # Handle special commands
                if user_input.lower() in ["exit", "quit"]:
                    self.console.print("\n[bold cyan]Goodbye! 👋[/bold cyan]\n")
                    break

                if user_input.lower() == "help":
                    self._show_help()
                    continue

                if not user_input.strip():
                    continue

                # Process input - no spinner, let commands run interactively by default
                result = self.controller.process_input(user_input)

                # Display result
                self.display_result(result)

            except KeyboardInterrupt:
                self.console.print("\n\n[bold cyan]Goodbye! 👋[/bold cyan]\n")
                break
            except Exception as e:
                self.console.print(f"\n[bold red]Error:[/bold red] {str(e)}\n")

    def _show_help(self):
        """Show help information"""
        help_text = """
[bold cyan]AITAS Help[/bold cyan]

[bold]Supported Commands:[/bold]
  • Create directory: "Make a folder called ProjectX"
  • Write file: "Create a README.md in ProjectX"
  • Read file: "Read the config.yaml file"
  • List directory: "Show files in current directory"

[bold]Examples:[/bold]
  [dim]> Make a folder called MyProject[/dim]
  [dim]> Write a hello.txt file with Hello World[/dim]
  [dim]> Read requirements.txt[/dim]
  [dim]> List all files here[/dim]
        """
        self.console.print(Panel(help_text, border_style="cyan"))
