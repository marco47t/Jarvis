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
from typing import Optional, Dict, Any
from colorama import Fore, Back, Style, init
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
{Fore.CYAN}╔═══════════════════════════════════════════════════════════╗
║                                                           ║
║     {Fore.YELLOW}     ██╗ █████╗ ██████╗ ██╗   ██╗██╗███████╗    {Fore.CYAN}   ║
║     {Fore.YELLOW}     ██║██╔══██╗██╔══██╗██║   ██║██║██╔════╝    {Fore.CYAN}   ║
║     {Fore.YELLOW}     ██║███████║██████╔╝██║   ██║██║███████╗    {Fore.CYAN}   ║
║     {Fore.YELLOW}██   ██║██╔══██║██╔══██╗╚██╗ ██╔╝██║╚════██║    {Fore.CYAN}   ║
║     {Fore.YELLOW}╚█████╔╝██║  ██║██║  ██║ ╚████╔╝ ██║███████║    {Fore.CYAN}   ║
║     {Fore.YELLOW} ╚════╝ ╚═╝  ╚═╝╚═╝  ╚═╝  ╚═══╝  ╚═╝╚══════╝    {Fore.CYAN}   ║
║                                                           ║
║         {Fore.GREEN}Your Intelligent AI Assistant - CLI Edition{Fore.CYAN}       ║
║                                                           ║
╚═══════════════════════════════════════════════════════════╝{Style.RESET_ALL}
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
                error_msg = f"AI Engine: Failed ({str(e)[:50]}...)"
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
        
    def display_menu(self) -> None:
        """Display the main menu with rich formatting"""
        table = Table(
            title="\n[bold cyan]Jarvis Command Center[/bold cyan]", 
            box=box.ROUNDED,
            show_header=True,
            header_style="bold magenta"
        )
        
        table.add_column("#", style="cyan", width=6, justify="center")
        table.add_column("Feature", style="green", no_wrap=True)
        table.add_column("Description", style="white")
        
        table.add_row("1", "💬 Chat with AI", "Have a conversation with Jarvis")
        table.add_row("2", "🎯 Agent Mode", "Let Jarvis complete tasks autonomously")
        table.add_row("3", "🌤️  Weather Info", "Get current weather data")
        table.add_row("4", "📊 System Status", "View system monitoring information")
        table.add_row("5", "🌅 Morning Briefing", "Generate morning briefing")
        table.add_row("6", "💾 Chat History", "View saved chat sessions")
        table.add_row("7", "🔧 Settings", "View current configuration")
        table.add_row("8", "📋 Profile Info", "View user profile")
        table.add_row("9", "🛠️  Test Tools", "Test individual tools")
        table.add_row("0", "🚪 Exit", "Close Jarvis CLI")
        
        console.print(table)
        
    def chat_mode(self) -> None:
        """Interactive chat mode"""
        if not self.gemini_client:
            console.print("[red]AI Engine not available. Cannot enter chat mode.[/red]")
            Prompt.ask("\nPress Enter to continue")
            return
            
        console.print(Panel.fit(
            "[bold cyan]Chat Mode Activated[/bold cyan]\n"
            "Type your messages and press Enter. Type 'back' to return to menu.",
            border_style="cyan"
        ))
        
        while True:
            try:
                user_input = Prompt.ask("\n[bold green]You[/bold green]")
                
                if user_input.lower() in ['back', 'exit', 'quit']:
                    break
                    
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
                    response = self.gemini_client.generate_response(user_input)
                
                # Display response in a panel
                console.print(Panel(
                    Markdown(response),
                    title="[bold yellow]Jarvis[/bold yellow]",
                    border_style="yellow",
                    padding=(1, 2)
                ))
                
            except KeyboardInterrupt:
                console.print("\n[yellow]Chat interrupted[/yellow]")
                break
            except Exception as e:
                console.print(f"[red]Error: {str(e)}[/red]")
                console.print("[yellow]Try again or type 'back' to return to menu.[/yellow]")
                
    def agent_mode(self) -> None:
        """Agent mode for task completion"""
        if not self.gemini_client:
            console.print("[red]AI Engine not available. Cannot enter agent mode.[/red]")
            Prompt.ask("\nPress Enter to continue")
            return
            
        console.print(Panel.fit(
            "[bold cyan]Agent Mode Activated[/bold cyan]\n"
            "Describe what you want Jarvis to do. Type 'back' to return.",
            border_style="cyan"
        ))
        
        while True:
            try:
                goal = Prompt.ask("\n[bold green]Task[/bold green]")
                
                if goal.lower() in ['back', 'exit', 'quit']:
                    break
                    
                if not goal.strip():
                    continue
                
                # Execute agent task with progress
                console.print("\n[cyan]Executing task...[/cyan]")
                
                with Progress(
                    SpinnerColumn(),
                    TextColumn("[cyan]{task.description}"),
                    console=console,
                    transient=True
                ) as progress:
                    progress.add_task("Agent working...", total=None)
                    result = agent.think(self.gemini_client, goal)
                
                # Display result
                console.print(Panel(
                    Markdown(result),
                    title="[bold yellow]Task Result[/bold yellow]",
                    border_style="green",
                    padding=(1, 2)
                ))
                
            except KeyboardInterrupt:
                console.print("\n[yellow]Task interrupted[/yellow]")
                break
            except Exception as e:
                console.print(f"[red]Error: {str(e)}[/red]")
                console.print("[yellow]Try again or type 'back' to return to menu.[/yellow]")
                
    def show_weather(self) -> None:
        """Display weather information"""
        if not self.weather_bot:
            console.print("[red]Weather service not available[/red]")
            Prompt.ask("\nPress Enter to continue")
            return
            
        console.print("\n[cyan]Fetching weather data...[/cyan]")
        
        try:
            weather_data = self.weather_bot.get_latest_weather_data()
            
            if weather_data and weather_data.get('status') == 'success':
                data = weather_data.get('data', {})
                
                table = Table(
                    title="[bold cyan]Current Weather[/bold cyan]", 
                    box=box.DOUBLE_EDGE,
                    show_header=True,
                    header_style="bold cyan"
                )
                table.add_column("Parameter", style="cyan")
                table.add_column("Value", style="yellow")
                
                table.add_row("Location", str(data.get('location', 'N/A')))
                table.add_row("Temperature", f"{data.get('temperature', 'N/A')}°C")
                table.add_row("Condition", str(data.get('condition', 'N/A')))
                table.add_row("Humidity", f"{data.get('humidity', 'N/A')}%")
                table.add_row("Wind Speed", f"{data.get('wind_speed', 'N/A')} km/h")
                
                console.print(table)
            else:
                error_msg = weather_data.get('message', 'Unknown error') if weather_data else 'No data available'
                console.print(f"[red]Failed to fetch weather: {error_msg}[/red]")
        except Exception as e:
            console.print(f"[red]Error fetching weather: {str(e)}[/red]")
            
        Prompt.ask("\nPress Enter to continue")
        
    def show_system_status(self) -> None:
        """Display system monitoring status"""
        console.print("\n[bold cyan]System Status[/bold cyan]\n")
        
        status_displayed = False
        
        if self.system_monitor:
            try:
                actions = self.system_monitor.get_actions()
                if actions:
                    table = Table(title="Suggested Actions", box=box.ROUNDED)
                    table.add_column("ID", style="cyan", width=10)
                    table.add_column("Message", style="white")
                    
                    for action in actions:
                        table.add_row(str(action.get('id', 'N/A')), str(action.get('text', 'N/A')))
                        
                    console.print(table)
                    status_displayed = True
                else:
                    console.print("[green]✓ No system issues detected[/green]")
                    status_displayed = True
            except Exception as e:
                console.print(f"[yellow]Could not fetch system actions: {str(e)}[/yellow]")
        else:
            console.print("[yellow]System monitor not available[/yellow]")
            
        if self.health_monitor:
            try:
                alerts = self.health_monitor.get_alerts()
                if alerts:
                    table = Table(title="Health Alerts", box=box.ROUNDED)
                    table.add_column("ID", style="cyan", width=10)
                    table.add_column("Alert", style="red")
                    
                    for alert in alerts:
                        table.add_row(str(alert.get('id', 'N/A')), str(alert.get('text', 'N/A')))
                        
                    console.print(table)
                    status_displayed = True
                else:
                    console.print("[green]✓ System health is good[/green]")
                    status_displayed = True
            except Exception as e:
                console.print(f"[yellow]Could not fetch health alerts: {str(e)}[/yellow]")
        else:
            console.print("[yellow]Health monitor not available[/yellow]")
            
        if not status_displayed:
            console.print("[yellow]No status information available[/yellow]")
            
        Prompt.ask("\nPress Enter to continue")
        
    def morning_briefing(self) -> None:
        """Generate and display morning briefing"""
        if not self.gemini_client:
            console.print("[red]AI Engine not available. Cannot generate briefing.[/red]")
            Prompt.ask("\nPress Enter to continue")
            return
            
        console.print("\n[bold cyan]Generating Morning Briefing...[/bold cyan]\n")
        
        try:
            with Progress(
                SpinnerColumn(),
                TextColumn("[cyan]{task.description}"),
                console=console,
                transient=True
            ) as progress:
                progress.add_task("Creating briefing...", total=None)
                script, briefing_points, action_plan = generate_and_execute_briefing(
                    self.gemini_client, 
                    self.weather_bot
                )
            
            # Display briefing points
            console.print(Panel(
                Markdown(script),
                title="[bold yellow]Your Morning Briefing[/bold yellow]",
                border_style="yellow",
                padding=(1, 2)
            ))
            
            # Display action plan if any
            if action_plan:
                console.print("\n[bold green]Suggested Actions:[/bold green]")
                for i, action in enumerate(action_plan, 1):
                    tool_name = action.get('tool_name', 'Unknown')
                    console.print(f"  {i}. {tool_name}")
            else:
                console.print("\n[dim]No automated actions suggested.[/dim]")
                    
        except Exception as e:
            console.print(f"[red]Error generating briefing: {str(e)}[/red]")
            traceback.print_exc()
            
        Prompt.ask("\nPress Enter to continue")
        
    def show_chat_history(self) -> None:
        """Display saved chat sessions"""
        console.print("\n[bold cyan]Chat History[/bold cyan]\n")
        
        if not os.path.exists(CHATS_DIR):
            console.print("[yellow]No chat history found[/yellow]")
            Prompt.ask("\nPress Enter to continue")
            return
            
        try:
            files = [os.path.join(CHATS_DIR, f) for f in os.listdir(CHATS_DIR) if f.endswith(".json")]
        except Exception as e:
            console.print(f"[red]Error reading chat directory: {str(e)}[/red]")
            Prompt.ask("\nPress Enter to continue")
            return
        
        if not files:
            console.print("[yellow]No chat sessions saved[/yellow]")
            Prompt.ask("\nPress Enter to continue")
            return
            
        files.sort(key=os.path.getmtime, reverse=True)
        
        table = Table(box=box.ROUNDED, title="Recent Chat Sessions")
        table.add_column("#", style="cyan", width=6, justify="center")
        table.add_column("Title", style="green")
        table.add_column("Date", style="yellow")
        
        for i, file_path in enumerate(files[:10], 1):  # Show last 10
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    title = data.get('title', 'Untitled')
                    timestamp = data.get('timestamp', 'Unknown')
                    table.add_row(str(i), title, timestamp)
            except Exception:
                continue
                
        console.print(table)
        Prompt.ask("\nPress Enter to continue")
        
    def show_settings(self) -> None:
        """Display current settings"""
        console.print("\n[bold cyan]Current Settings[/bold cyan]\n")
        
        keys = [
            'DEFAULT_AI_MODEL', 'VISION_MODEL_NAME', 'AI_TEMPERATURE',
            'MAX_RESPONSE_TOKENS', 'WEATHER_UPDATE_INTERVAL'
        ]
        
        try:
            settings = get_config_values(keys)
            
            table = Table(box=box.ROUNDED, title="Configuration")
            table.add_column("Setting", style="cyan")
            table.add_column("Value", style="yellow")
            
            for key, value in settings.items():
                table.add_row(key, str(value))
                
            console.print(table)
        except Exception as e:
            console.print(f"[red]Error loading settings: {str(e)}[/red]")
            
        Prompt.ask("\nPress Enter to continue")
        
    def show_profile(self) -> None:
        """Display user profile information"""
        console.print("\n[bold cyan]User Profile[/bold cyan]\n")
        
        try:
            profile = load_profile()
            
            if not profile:
                console.print("[yellow]No profile configured[/yellow]")
                Prompt.ask("\nPress Enter to continue")
                return
                
            table = Table(box=box.ROUNDED, title="Profile Information")
            table.add_column("Field", style="cyan")
            table.add_column("Value", style="yellow")
            
            for key, value in profile.items():
                display_key = key.replace('_', ' ').title()
                table.add_row(display_key, str(value))
                
            console.print(table)
        except Exception as e:
            console.print(f"[red]Error loading profile: {str(e)}[/red]")
            
        Prompt.ask("\nPress Enter to continue")
        
    def test_tools(self) -> None:
        """Test individual tools"""
        console.print("\n[bold cyan]Tool Testing[/bold cyan]\n")
        
        try:
            # List available tools
            tools = list(tool_definitions.TOOL_DEFINITIONS.keys())
            
            if not tools:
                console.print("[yellow]No tools available[/yellow]")
                Prompt.ask("\nPress Enter to continue")
                return
            
            table = Table(title="Available Tools", box=box.ROUNDED)
            table.add_column("#", style="cyan", width=6, justify="center")
            table.add_column("Tool Name", style="green")
            
            for i, tool_name in enumerate(tools, 1):
                table.add_row(str(i), tool_name)
                
            console.print(table)
            
            choice = Prompt.ask("\nEnter tool number to test (or 'back' to return)")
            
            if choice.lower() == 'back':
                return
                
            try:
                tool_idx = int(choice) - 1
                if 0 <= tool_idx < len(tools):
                    tool_name = tools[tool_idx]
                    console.print(f"\n[cyan]Testing {tool_name}...[/cyan]")
                    console.print("[yellow]Note: This is a basic test. Some tools may require arguments.[/yellow]")
                    
                    # Check if tool exists
                    tool_def = tool_definitions.TOOL_DEFINITIONS.get(tool_name)
                    if tool_def:
                        console.print(f"[green]✓ Tool '{tool_name}' is available[/green]")
                        console.print(f"[dim]Description: {tool_def.get('description', 'No description')}[/dim]")
                    else:
                        console.print(f"[red]✗ Tool '{tool_name}' not found[/red]")
                else:
                    console.print("[red]Invalid tool number[/red]")
            except ValueError:
                console.print("[red]Invalid input. Please enter a number.[/red]")
                
        except Exception as e:
            console.print(f"[red]Error loading tools: {str(e)}[/red]")
            
        Prompt.ask("\nPress Enter to continue")
        
    def cleanup(self) -> None:
        """Cleanup resources before exit"""
        try:
            if self.weather_bot:
                # Stop weather bot if it has a stop method
                if hasattr(self.weather_bot, 'stop'):
                    self.weather_bot.stop()
        except Exception:
            pass
        
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
            console.print("[yellow]Many features will not be available.[/yellow]")
            if not Confirm.ask("\nDo you want to continue anyway?"):
                return
        
        # Main menu loop
        while self.running:
            try:
                # Clear screen
                os.system('cls' if os.name == 'nt' else 'clear')
                
                # Display banner
                self.display_banner()
                
                # Display menu
                self.display_menu()
                
                # Get user choice
                choice = Prompt.ask("\n[bold cyan]Enter your choice[/bold cyan]")
                
                # Handle menu selection
                if choice == '1':
                    self.chat_mode()
                elif choice == '2':
                    self.agent_mode()
                elif choice == '3':
                    self.show_weather()
                elif choice == '4':
                    self.show_system_status()
                elif choice == '5':
                    self.morning_briefing()
                elif choice == '6':
                    self.show_chat_history()
                elif choice == '7':
                    self.show_settings()
                elif choice == '8':
                    self.show_profile()
                elif choice == '9':
                    self.test_tools()
                elif choice == '0':
                    if Confirm.ask("\n[yellow]Are you sure you want to exit?[/yellow]"):
                        self.running = False
                else:
                    console.print("[red]Invalid choice. Please try again.[/red]")
                    time.sleep(1.5)
                    
            except KeyboardInterrupt:
                console.print("\n[yellow]Interrupted. Press 0 to exit.[/yellow]")
                time.sleep(1)
            except Exception as e:
                console.print(f"[red]Unexpected error: {str(e)}[/red]")
                time.sleep(2)
                
        # Cleanup
        self.cleanup()
        console.print("\n[bold green]Thank you for using Jarvis![/bold green]")
        console.print("[cyan]Shutting down...[/cyan]\n")
        time.sleep(1)


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
