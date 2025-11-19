#!/usr/bin/env python3
"""
Jarvis CLI - AI-powered Command Line
- Automatic intent detection
- Beautiful banner with properly rendered 'JARVIS'
- User input is interpreted via AI; no menu selection
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
from rich import box

# Initialize
init(autoreset=True)
console = Console()

try:
    from config import CHATS_DIR
    from commands.ai_chat import GeminiClient
    from commands import agent
    from commands.tools.weather_bot import WeatherBot
    from commands.tools.system_monitor import SystemMonitor
    from commands.tools.system_health import SystemHealthMonitor
    from commands.briefing_manager import generate_and_execute_briefing
    from commands.tools import tool_definitions
    from commands.config_manager import get_config_values, load_profile
except ImportError as e:
    console.print(f"[red]Error importing Jarvis modules: {e}[/red]")
    console.print("[yellow]Run this file from your Jarvis project directory.[/yellow]")
    sys.exit(1)


BANNER = f"""{Fore.CYAN}
╔═══════════════════════════════════════════════════════════╗
║                                                           ║
║      █████ █████  ██████  ██    ██ ██ ███████             ║
║      ██    ██  ██ ██      ██    ██ ██ ██    ██            ║
║      ██    ██████ ██      ██    ██ ██ ███████             ║
║      ██    ██     ██      ██    ██ ██ ██   ██             ║
║      ██    ██     ██████  ██████  ██ ███████              ║
║                                                           ║
║         {Fore.GREEN}Your Intelligent AI Assistant - CLI Edition{Fore.CYAN}       ║
║                                                           ║
╚═══════════════════════════════════════════════════════════╝{Style.RESET_ALL}
"""

class JarvisCLI:
    def __init__(self):
        self.gemini_client = None
        self.weather_bot = None
        self.system_monitor = None
        self.health_monitor = None
        self.running = True
        self.errors = []

    def display_banner(self):
        os.system('cls' if os.name == 'nt' else 'clear')
        console.print(BANNER)
        time.sleep(0.2)

    def initialize(self):
        console.print("[bold cyan]\nInitializing Jarvis AI...[/bold cyan]")
        with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"), console=console, transient=True) as p:
            t1 = p.add_task('[green]Loading core AI...', total=1)
            try:
                self.gemini_client = GeminiClient()
                p.update(t1, advance=1)
                console.print("[green]✓ Assistant Ready!")
            except Exception as e:
                self.errors.append("Can't start GeminiClient: " + str(e))
                console.print(f"[red]Gemini AI Engine error: {e}")
        time.sleep(0.2)

    def ai_interpret(self, user_input):
        """Use the AI backend to interpret and fulfill user request."""
        if not self.gemini_client:
            return "[red]AI Engine not available."    
        try:
            with Progress(SpinnerColumn(), TextColumn("AI processing your request..."), console=console, transient=True) as p:
                p.add_task('thinking', total=None)
                response = self.gemini_client.generate_response(user_input)
            return response
        except Exception as e:
            return f"[red]Error executing your request: {str(e)}"

    def run(self):
        self.display_banner()
        self.initialize()
        if self.errors:
            for err in self.errors:
                console.print(f"[yellow]{err}")
            console.print('[red]Critical error: Most AI features unavailable!')
            return

        console.print(Panel("[cyan]Type your instruction (e.g. 'weather', 'morning briefing', or any request). Type 'exit' to quit.[/cyan]", border_style="cyan"))
        while self.running:
            try:
                user_input = Prompt.ask("\n[bold yellow]You[/bold yellow]")
                if user_input.lower().strip() in ['exit', 'quit', 'q']:
                    break
                response = self.ai_interpret(user_input)
                # if markdown valid, render as markdown
                try:
                    console.print(Panel(Markdown(response), title="[bold green]Jarvis[/bold green]", border_style="green"))
                except Exception:
                    console.print(Panel(str(response), title="[bold green]Jarvis[/bold green]", border_style="green"))
            except Exception as e:
                console.print(f"[red]Unexpected Error: {e}")
                traceback.print_exc()
                continue
        console.print("[green]Thank you for using Jarvis CLI!")
        time.sleep(0.5)

if __name__ == "__main__":
    cli = JarvisCLI()
    cli.run()
