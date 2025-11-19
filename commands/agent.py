# commands/agent.py
import json
import logging
import re
import random
import inspect
from typing import Any, Callable, Dict, List

from rich.console import Console
from rich.panel import Panel

from commands.ai_chat import GeminiClient
from commands.file_organizer import (
    move_file, rename_file,
    handle_generic_document, handle_image, handle_invoice, handle_project_asset,
    handle_screenshot, delete_junk_file)
from commands.gmail_tools import send_gmail_message
from commands.image_tools import analyze_image_content
from commands.system_info_tools import get_system_information, get_process_list
from commands.system_tools import execute_shell_command
from commands.task_runner import run_report_builder_task
from commands.voice_tools import text_to_speech, transcribe_audio
from commands.web_tools import browse_web_page, search_and_browse
from commands.backup_tools import create_project_backup
from commands.weather_tools import get_current_weather
from config import ENABLE_LOGGING, LOG_FILE, TELEGRAM_ADMIN_USER_ID

if ENABLE_LOGGING:
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                        handlers=[logging.FileHandler(LOG_FILE, encoding='utf-8')])
    logger = logging.getLogger(__name__)
else:
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.CRITICAL + 1)
    logger.propagate = False

console = Console()

ACTION_REGISTRY: Dict[str, Callable[..., Any]] = {
    # General Purpose File Tools
    "move_file": move_file,
    "rename_file": rename_file,
    # Specialist File System Tools
    "handle_generic_document": handle_generic_document,
    "handle_image": handle_image,
    "handle_invoice": handle_invoice,
    "handle_project_asset": handle_project_asset,
    "handle_screenshot": handle_screenshot,
    "delete_junk_file": delete_junk_file,
    # Backup Tool
    "create_project_backup": create_project_backup,
    # System & Execution Tools
    "execute_shell_command": execute_shell_command,
    "get_system_information": get_system_information,
    "get_process_list": get_process_list,
    # Web Tools
    "browse_web_page": lambda url: browse_web_page(url)[0],
    "search_and_browse": search_and_browse,
    # Communication Tools
    "send_gmail_message": send_gmail_message,
    # Multimodal Tools
    "analyze_image_content": analyze_image_content,
    "transcribe_audio": transcribe_audio,
    "text_to_speech": text_to_speech,
    # Weather Tools
    "get_current_weather": get_current_weather,
    # Task-specific Tools
    "run_report_builder_task": run_report_builder_task,
}

THINKING_MESSAGES = [
    "Pondering the next move...", "Consulting the archives...", "Formulating a strategy...",
    "Processing new information...", "Connecting the dots...", "Orchestrating tools...",
]


def think(gemini_client: GeminiClient, user_goal: str, user_id: int = None, silent_mode: bool = True) -> str:
    """
    The upgraded core "thinking" loop with a sliding window memory to prevent token limits.
    
    Args:
        gemini_client: The Gemini AI client
        user_goal: The user's request/goal
        user_id: User identifier for authorization checks
        silent_mode: If True, suppresses console output (for web UI). Default True (suppresses output)
    """
    if not silent_mode:
        console.print(Panel(f"[bold]New Goal:[/bold] {user_goal}", border_style="green", title="Agent Activated", expand=False))

    tool_descriptions = "\n".join([
        f"- {name}{inspect.signature(func)}: {func.__doc__.strip().splitlines()[0] if func.__doc__ else 'No description available.'}"
        for name, func in ACTION_REGISTRY.items()
    ])
    
    system_prompt = (
        "You are an expert autonomous agent named JARVIS, running directly on the user's local computer. You have DIRECT and REAL access to the user's system via your tools.\n\n"
        "**REASONING HIERARCHY:**\n"
        "1. **For questions about current events or general knowledge,** ALWAYS use `search_and_browse` first.\n"
        "2. **For local file system or OS tasks,** use the most specific tool available (e.g., `rename_file`, `get_process_list`).\n"
        "3. **Use `execute_shell_command` only as a last resort** for tasks not covered by other tools.\n\n"
        "You operate in a loop. You must follow this format exactly:\n"
        "1. **Thought:** Briefly explain your reasoning and your plan.\n"
        "2. **Tool:** Provide a single JSON object for the tool you need to use, enclosed in ```json ... ```. The JSON MUST have 'tool_name' and 'args' (as an object).\n\n"
        "When the task is fully completed, you MUST respond ONLY with 'Final Answer:' followed by a clear, user-friendly summary."
    )

    permanent_prompt_part = f"SYSTEM_PROMPT: {system_prompt}\n\nAVAILABLE TOOLS:\n{tool_descriptions}\n\nUSER_GOAL: {user_goal}"
    
    turn_history: List[str] = []
    max_history_turns = 3
    max_turns = 10 

    # Only show spinner in CLI mode
    if not silent_mode:
        status = console.status("[bold green]Agent is thinking...[/bold green]", spinner="dots")
        status.start()
    
    try:
        for turn in range(max_turns):
            if not silent_mode:
                status.update(random.choice(THINKING_MESSAGES))
                console.print(f"\n[bold magenta]--- Agent Turn {turn + 1}/{max_turns} ---[/bold magenta]")

            recent_turns = turn_history[-max_history_turns:]
            full_prompt = permanent_prompt_part + "\n\n" + "\n".join(recent_turns)
            
            ai_response_text = gemini_client.generate_text(full_prompt)
            
            if not silent_mode:
                console.print(Panel(ai_response_text, title="Agent's Thought Process", border_style="cyan", expand=False))

            if "Final Answer:" in ai_response_text:
                final_answer = ai_response_text.split("Final Answer:", 1)[1].strip()
                if not silent_mode:
                    console.print(Panel(f"[bold green]Goal Achieved![/bold green]\n{final_answer}", title="Task Completed", border_style="green", expand=False))
                return final_answer

            tool_call_match = re.search(r'```json\n(.*?)\n```', ai_response_text, re.DOTALL)
            
            if not tool_call_match:
                error_feedback = "Error: Invalid response format. You must provide a 'Thought' and then a 'Tool' in a JSON code block. Please try again."
                if not silent_mode:
                    console.print(f"[bold red]{error_feedback}[/bold red]")
                turn_history.append(f"AI_RESPONSE:\n{ai_response_text}\nSYSTEM_FEEDBACK: {error_feedback}")
                continue

            try:
                tool_call = json.loads(tool_call_match.group(1))
                tool_name = tool_call.get("tool_name")
                tool_args = tool_call.get("args", {})
                if not tool_name or not isinstance(tool_args, dict):
                    raise ValueError("Missing 'tool_name' or 'args' is not an object.")
            except (json.JSONDecodeError, ValueError) as e:
                error_feedback = f"Error: The JSON for the tool call was malformed: {e}. Please correct the JSON structure and try again."
                if not silent_mode:
                    console.print(f"[bold red]{error_feedback}[/bold red]")
                turn_history.append(f"AI_RESPONSE:\n{ai_response_text}\nSYSTEM_FEEDBACK: {error_feedback}")
                continue

            if not silent_mode:
                status.update(f"[bold yellow]Executing: {tool_name}...[/bold yellow]")
                console.print(f"[bold yellow]Using Tool:[/bold yellow] {tool_name} with args: {tool_args}")
            
            action_func = ACTION_REGISTRY.get(tool_name)
            tool_output = ""

            if not action_func:
                tool_output = f"Error: Unknown tool '{tool_name}'. Please choose from the available tools."
            elif tool_name == "execute_shell_command" and user_id != TELEGRAM_ADMIN_USER_ID:
                tool_output = "Security Error: You are not authorized to execute shell commands."
            else:
                try:
                    if 'gemini_client' in inspect.signature(action_func).parameters:
                        tool_args['gemini_client'] = gemini_client
                    tool_output = action_func(**tool_args)
                except Exception as e:
                    logger.error(f"Error executing tool {tool_name}: {e}", exc_info=True)
                    tool_output = f"Error during tool execution: {e}"

            tool_output_str = str(tool_output)
            if not silent_mode:
                console.print(Panel(tool_output_str, title=f"Tool Output ({tool_name})", border_style="yellow", expand=False))
            
            current_turn_summary = f"AI_RESPONSE:\n{ai_response_text}\nTOOL_RESULT:\n{tool_output_str}"
            turn_history.append(current_turn_summary)
    finally:
        if not silent_mode:
            status.stop()

    if not silent_mode:
        console.print("[bold red]Agent reached maximum turns without a final answer.[/bold red]")
    return "The agent could not complete the task after multiple steps. Please try rephrasing your goal."