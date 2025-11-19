#!/usr/bin/env python3
"""
Jarvis CLI - Interactive Command Line Interface
A colorful, animated CLI for testing Jarvis features
"""

import os
import sys
import time
import json
import traceback
from datetime import datetime
from typing import Optional
from colorama import Fore, Style, init
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.markdown import Markdown
from rich.prompt import Prompt, Confirm
from rich import box

# Initialize colorama for Windows color support
init(autoreset=True)

# Initialize Rich console
console = Console()

# Import Jarvis modules
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
    console.print("[yellow]Make sure you're running this from the Jarvis directory.[/yellow]")
    sys.exit(1)


class JarvisCLI:
    """Main CLI application class for Jarvis"""
    
    def __init__(self):
        self.gemini_client: Optional[GeminiClient] = None
        self.weather_bot: Optional[WeatherBot] = None
        self.system_monitor: Optional[SystemMonitor] = None
        self.health_monitor: Optional[SystemHealthMonitor] = None
        self.running = True
        self.initialization_errors = []
        
    def display_banner(self) -> None:
        """Display an animated ASCII art banner"""
        banner = f"""
{Fore.CYAN}╔════════════════════════════════════════════════════════════════════════╗
║                                                                      ║
║   {Fore.YELLOW}█████╗ ██████╗ ██████╗ ██╗   ██╗██╗ ███████╗{Fore.CYAN}              ║
║   {Fore.YELLOW}██╔══██╗██╔══██╗██╔══██╗██║   ██║██║██╔════╝{Fore.CYAN}              ║
║   {Fore.YELLOW}███████║██████╔╝██████╔╝██║   ██║██║███████╗{Fore.CYAN}              ║
║   {Fore.YELLOW}██╔══██║██╔══██╗██╔══██╗╚██╗ ██╔╝██║╚════██║{Fore.CYAN}              ║
║   {Fore.YELLOW}██║  ██║██║  ██║██║  ██║ ╚████╔╝ ██║███████║{Fore.CYAN}              ║
║   {Fore.YELLOW}╚═╝  ╚═╝╚═╝  ╚═╝╚═╝  ╚═╝  ╚═══╝  ╚═╝╚══════╝{Fore.CYAN}              ║
║                                                                      ║
║         {Fore.GREEN}Your Intelligent AI Assistant - CLI Edition{Fore.CYAN}               ║
║                                                                      ║
╚════════════════════════════════════════════════════════════════════════╝{Style.RESET_ALL}
        """
        console.print(banner)
        time.sleep(0.3)
        
    def initialize_services(self) -> None:
        """Initialize all Jarvis services with progress display"""
        console.print("\n[bold cyan]Initializing Jarvis Services...[/bold cyan]\n")
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
            transient=True
        ) as progress:
            
            # Initialize Gemini Client
            task1 = progress.add_task("[cyan]Starting AI Engine...", total=1)
            try:
                self.gemini_client = GeminiClient()
                progress.update(task1, advance=1)
                console.print("[green]✓[/green] AI Engine: Ready")
            except Exception as e:
                error_msg = f"AI Engine failed to initialize: {str(e)[:80]}..."
                console.print(f"[red]✗[/red] {error_msg}")
                self.initialization_errors.append(error_msg)
                
            # Initialize Weather Bot
            task2 = progress.add_task("[cyan]Connecting to Weather Service...", total=1)
            try:
                self.weather_bot = WeatherBot()
                self.weather_bot.start()
                progress.update(task2, advance=1)
                console.print("[green]✓[/green] Weather Service: Connected")
            except Exception as e:
                console.print(f"[yellow]![/yellow] Weather Service: Optional (skipped)")
                
            # Initialize System Monitor
            task3 = progress.add_task("[cyan]Activating System Monitor...", total=1)
            try:
                if self.gemini_client:
                    self.system_monitor = SystemMonitor(gemini_client=self.gemini_client)
                    progress.update(task3, advance=1)
                    console.print("[green]✓[/green] System Monitor: Active")
                else:
                    console.print("[yellow]![/yellow] System Monitor: Skipped (AI not available)")
            except Exception as e:
                console.print(f"[yellow]![/yellow] System Monitor: Optional (skipped)")
                
            # Initialize Health Monitor
            task4 = progress.add_task("[cyan]Activating Health Monitor...", total=1)
            try:
                if self.gemini_client:
                    self.health_monitor = SystemHealthMonitor(gemini_client=self.gemini_client)
                    progress.update(task4, advance=1)
                    console.print("[green]✓[/green] Health Monitor: Active")
                else:
                    console.print("[yellow]![/yellow] Health Monitor: Skipped (AI not available)")
            except Exception as e:
                console.print(f"[yellow]![/yellow] Health Monitor: Optional (skipped)")
        
        if self.initialization_errors:
            console.print("\n[bold yellow]⚠ Some critical services failed to initialize[/bold yellow]")
            console.print("[yellow]Some features may not be available.[/yellow]")
        else:
            console.print("\n[bold green]✓ All systems initialized![/bold green]")
        
        time.sleep(1)
        
    def chat_with_ai(self, user_input: str) -> str:
        """Send message to AI and get response using agent mode"""
        if not self.gemini_client:
            return "AI Engine not available. Cannot process request."
            
        try:
            # Use the agent.think method which handles the full interaction
            response = agent.think(self.gemini_client, user_input)
            return response
        except Exception as e:
            error_details = traceback.format_exc()
            console.print(f"[dim red]{error_details}[/dim red]")
            return f"Error processing your request: {str(e)}"
        
    def run(self) -> None:
        """Main application loop"""
        # Clear screen
        os.system('cls' if os.name == 'nt' else 'clear')
        
        # Display banner
        self.display_banner()
        
        # Initialize services
        self.initialize_services()
        
        # Check if AI is available
        if not self.gemini_client:
            console.print("\n[bold red]Critical: AI Engine failed to initialize![/bold red]")
            console.print("[yellow]The CLI cannot function without the AI engine.[/yellow]")
            console.print("[yellow]Please check your API key configuration in .env or config.py[/yellow]")
            return
        
        console.print(Panel.fit(
            "[bold cyan]Jarvis CLI Ready[/bold cyan]\n"
            "Type your requests naturally and I'll help you. Type 'exit' or 'quit' to close.",
            border_style="cyan"
        ))
        
        # Main interaction loop
        while self.running:
            try:
                user_input = Prompt.ask("\n[bold yellow]You[/bold yellow]")
                
                if user_input.lower().strip() in ['exit', 'quit', 'q', 'bye']:
                    if Confirm.ask("[yellow]Are you sure you want to exit?[/yellow]"):
                        break
                    continue
                    
                if not user_input.strip():
                    continue
                
                # Display thinking animation
                with Progress(
                    SpinnerColumn(),
                    TextColumn("[cyan]Jarvis is thinking..."),
                    console=console,
                    transient=True
                ) as progress:
                    progress.add_task("thinking", total=None)
                    response = self.chat_with_ai(user_input)
                
                # Display response in a panel
                try:
                    console.print(Panel(
                        Markdown(response),
                        title="[bold green]Jarvis[/bold green]",
                        border_style="green",
                        padding=(1, 2)
                    ))
                except Exception:
                    # Fallback to plain text if markdown fails
                    console.print(Panel(
                        response,
                        title="[bold green]Jarvis[/bold green]",
                        border_style="green",
                        padding=(1, 2)
                    ))
                
            except KeyboardInterrupt:
                console.print("\n[yellow]Interrupted. Type 'exit' to quit.[/yellow]")
                time.sleep(0.5)
            except Exception as e:
                console.print(f"[red]Unexpected error: {str(e)}[/red]")
                traceback.print_exc()
                time.sleep(1)
                
        # Cleanup
        console.print("\n[bold green]Thank you for using Jarvis![/bold green]")
        console.print("[cyan]Shutting down...[/cyan]\n")
        time.sleep(0.5)


def main() -> None:
    """Entry point for the CLI application"""
    try:
        cli = JarvisCLI()
        cli.run()
    except KeyboardInterrupt:
        console.print("\n\n[yellow]Application interrupted by user[/yellow]")
        sys.exit(0)
    except Exception as e:
        console.print(f"\n[bold red]Fatal Error: {str(e)}[/bold red]")
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
