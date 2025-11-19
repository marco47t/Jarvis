#!/usr/bin/env python3
"""
Jarvis CLI - Simplified for Modern (Standalone) Agent
Clean, robust, and independent: Only pull what you actually use.
"""

import os
import sys
import time
import traceback
from colorama import Fore, Style, init
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.markdown import Markdown
from rich.prompt import Prompt

init(autoreset=True)
console = Console()

try:
    from commands.ai_chat import GeminiClient
    from commands import agent
except ImportError as e:
    console.print(f"[red]Import error: {e}")
    sys.exit(1)

BANNER = f"""
{Fore.CYAN}╔═══════════════════════════════════════════════════════════╗
║                                                           ║
║   {Fore.YELLOW} █████╗ ██████╗ ██████╗ ██╗   ██╗██╗ ███████╗{Fore.CYAN}      ║
║   {Fore.YELLOW}██╔══██╗██╔══██╗██╔══██╗██║   ██║██║██╔════╝{Fore.CYAN}      ║
║   {Fore.YELLOW}███████║██████╔╝██████╔╝██║   ██║██║███████╗{Fore.CYAN}      ║
║   {Fore.YELLOW}██╔══██║██╔══██╗██╔══██╗╚██╗ ██╔╝██║╚════██║{Fore.CYAN}      ║
║   {Fore.YELLOW}██║  ██║██║  ██║██║  ██║ ╚████╔╝ ██║███████║{Fore.CYAN}      ║
║   {Fore.YELLOW}╚═╝  ╚═╝╚═╝  ╚═╝╚═╝  ╚═╝  ╚═══╝  ╚═╝╚══════╝{Fore.CYAN}      ║
║                                                           ║
║   {Fore.GREEN}Your Intelligent AI Assistant - CLI Edition{Fore.CYAN}        ║
║                                                           ║
╚═══════════════════════════════════════════════════════════╝{Style.RESET_ALL}
"""

class JarvisCLI:
    def __init__(self):
        self.gemini_client = None
        self.running = True

    def display_banner(self):
        os.system('cls' if os.name == 'nt' else 'clear')
        console.print(BANNER)
        time.sleep(0.1)

    def initialize(self):
        console.print("[bold cyan]Initializing Jarvis AI...[/bold cyan]")
        with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"), console=console, transient=True) as p:
            t1 = p.add_task('[green]Loading core AI...', total=1)
            try:
                self.gemini_client = GeminiClient()
                p.update(t1, advance=1)
                console.print("[green]✓ AI Engine Ready!")
            except Exception as e:
                console.print(f"[red]✗ Failed to initialize GeminiClient: {e}")
                self.running = False
        time.sleep(0.1)

    def chat_with_ai(self, user_input: str) -> str:
        if not self.gemini_client:
            return "[red]AI Engine not available. Check your configuration."
        try:
            with Progress(SpinnerColumn(), TextColumn("Thinking..."), console=console, transient=True) as p:
                p.add_task('thinking', total=None)
                response = agent.think(self.gemini_client, user_input)
            return response
        except Exception as e:
            return f"[red]Error: {e}\n{traceback.format_exc()}"

    def run(self):
        self.display_banner()
        self.initialize()
        if not self.gemini_client:
            console.print("[bold red]AI engine not ready. Exiting.")
            return
        console.print(Panel("[cyan]Type anything (e.g. 'weather', 'news', 'summarize ...', 'exit').[/cyan]", border_style="cyan"))
        while self.running:
            try:
                user_input = Prompt.ask("\n[bold yellow]You[/bold yellow]")
                if user_input.lower().strip() in ['exit', 'quit', 'bye', 'q']:
                    console.print("[green]Thanks for using Jarvis CLI!")
                    break
                if not user_input.strip():
                    continue
                response = self.chat_with_ai(user_input)
                try:
                    console.print(Panel(Markdown(str(response)), title="[bold green]Jarvis[/bold green]", border_style="green", padding=(1, 2)))
                except Exception:
                    console.print(Panel(str(response), title="[bold green]Jarvis[/bold green]", border_style="green", padding=(1, 2)))
            except KeyboardInterrupt:
                console.print("\n[yellow]Interrupted. Type 'exit' or 'quit' to leave.")
                continue
            except Exception as e:
                console.print(f"[red]Fatal error: {e}")
                traceback.print_exc()
                self.running = False
        time.sleep(0.2)

def main():
    try:
        cli = JarvisCLI()
        cli.run()
    except KeyboardInterrupt:
        console.print("\n\n[yellow]Session cancelled by user.[/yellow]")
        sys.exit(0)
    except Exception as e:
        console.print(f"\n[bold red]Fatal error: {e}")
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
