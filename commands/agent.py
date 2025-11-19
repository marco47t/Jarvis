# commands/agent.py
from asyncio import exceptions
import json
import logging
import re
import random
import threading
import time
import traceback
from typing import Dict, List
from google.api_core import exceptions as google_exceptions
from rich.console import Console
from rich.panel import Panel
from rich.markup import escape

# --- Core Imports ---
from commands.ai_chat import GeminiClient
from config import (
    ENABLE_LOGGING, LOG_FILE,
    CONFIDENCE_THRESHOLD_GO, CONFIDENCE_THRESHOLD_ASK
)
import eel

# --- Agent-Specific Imports ---
from commands.memory_manager import MemoryManager
from commands.dynamic_tool_manager import DYNAMIC_TOOL_REGISTRY
from commands.tools import tool_definitions
from commands.tool_executor import execute_tool
from commands.agent_verifier import verify_action
from commands.agent_historian import get_historical_confidence
from commands.transaction_logger import log_tool_execution


class ConfirmationHandler:
    """Handles blocking for user confirmation from the UI."""
    def __init__(self):
        self.event = threading.Event()
        self.result = False

    def wait_for_response(self, timeout=120.0):
        """Blocks until the UI sets a response or timeout occurs."""
        self.event.wait(timeout)
        return self.result

    def set_response(self, confirmed: bool):
        """Called by the main thread to set the result and unblock the agent."""
        self.result = confirmed
        self.event.set()

# --- Logger & Console Setup ---
if ENABLE_LOGGING:
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                        handlers=[logging.FileHandler(LOG_FILE, encoding='utf-8')])
    logger = logging.getLogger(__name__)
else:
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.CRITICAL + 1)
    logger.propagate = False

console = Console()
memory_manager = MemoryManager()

# --- Helper Functions ---
def classify_intent(user_goal: str) -> List[str]:
    """Classifies the user's goal into categories to prune the tool list."""
    goal = user_goal.lower()
    categories = set()
    category_keywords = {
        "File Ops": ['file', 'folder', 'directory', 'move', 'rename', 'delete', 'organize', 'backup', 'copy', 'save'],
        "System Info": ['system', 'os', 'process', 'cpu', 'ram', 'info', 'hardware', 'memory', 'preference'],
        "Web Search": ['search', 'browse', 'web', 'google', 'look up', 'find', 'research', 'what is', 'who is'],
        "Communication": ['email', 'send', 'gmail', 'message', 'contact'],
        "Multimedia Analysis": ['image', 'photo', 'picture', 'audio', 'voice', 'read pdf', 'read docx', 'transcribe', 'analyze image', 'ocr'],
        "Weather": ['weather', 'forecast', 'temperature', 'climate', 'how hot is it'],
        "Task-Specific": ['report', 'summarize', 'build'],
        "Clipboard": ['clipboard', 'copy', 'paste'],
        "System Info & Execution": ['command', 'execute', 'shell', 'terminal', 'run', 'script', 'code', 'tool']
    }
    for category, keywords in category_keywords.items():
        if any(kw in goal for kw in keywords):
            categories.add(category)
    if not categories:
        return list(category_keywords.keys())
    return list(categories)

THINKING_MESSAGES = [
    "Pondering the next move...", "Consulting the archives...", "Formulating a strategy...",
    "Processing new information...", "Connecting the dots...", "Orchestrating tools...",
]


# In file: commands/agent.py

def think(gemini_client: GeminiClient, user_goal: str, user_id: int = None) -> str:
    """
    The core "thinking" loop. It uses a dynamic continuation logic based on confidence
    and self-correction for errors.
    """
    console.print(Panel(f"[bold]New Goal:[/bold] {user_goal}", border_style="green", title="Agent Activated", expand=False))

    # --- Step 1: Build the full context prompt for the agent's reasoning ---
    relevant_memories = memory_manager.retrieve_relevant_memories(user_goal)
    user_preferences = memory_manager.get_all_preferences()
    memory_prompt_part = ""
    if relevant_memories:
        formatted_memories = "\n".join([f"- {mem}" for mem in relevant_memories])
        memory_prompt_part += f"\n\n**RELEVANT PAST TASKS (for context):**\n{formatted_memories}"
    if user_preferences:
        formatted_prefs = "\n".join([f"- {key}: {value}" for key, value in user_preferences.items()])
        memory_prompt_part += f"\n\n**USER PREFERENCES (adhere to these):**\n{formatted_prefs}"

    relevant_categories = classify_intent(user_goal)
    dynamic_tools = DYNAMIC_TOOL_REGISTRY
    session_tools = {**tool_definitions.TOOL_DEFINITIONS, **dynamic_tools}
    pruned_tool_defs = {
        name: definition for name, definition in session_tools.items()
        if definition.get('category') in relevant_categories or definition.get('category') == 'Dynamic'
    }
    pruned_tool_descriptions = []
    for tool_name, tool_data in pruned_tool_defs.items():
        model = tool_data['args_model']
        try:
            schema = model.model_json_schema()
            description = schema.get('description', 'No description available.')
            pruned_tool_descriptions.append(f"- Tool: {tool_name}\n  Description: {description}\n  Arguments Schema: {json.dumps(schema['properties'])}")
        except Exception as e:
            console.print(f"[bold red]Error generating schema for {tool_name}: {e}[/bold red]")
    tool_prompt_string = "\n".join(pruned_tool_descriptions)

    system_prompt = (
        "You are an expert autonomous agent named JARVIS. You operate in a loop, and you must self-assess your confidence before every action.\n"
        "Your primary goal is to use the existing tools. However, if and only if NO existing tool can accomplish the user's task, you have the ability to write and execute a Python script.\n\n"
        "**Reasoning Hierarchy:**\n"
        "1. Always prefer using a specific, existing tool if one is available.\n"
        "2. If no tool can perform the action, consider if you can create a new, simple, reusable tool with `create_new_tool`.\n"
        "3. ONLY as a last resort for one-off tasks, use `execute_generated_python_script` to generate and run a Python script.\n\n"
        "**Dynamic Tool Creation:**\n"
        "If, and only if, there is absolutely no existing tool that can solve a specific sub-problem, you can create a new tool for this session using `create_new_tool`.\n"
        "1. The `python_code` argument must be a single, complete Python function. Include all necessary imports *inside* the function to keep it self-contained.\n"
        "2. The function name in the code MUST match the `tool_name` argument.\n"
        "3. **CRITICAL: You MUST include Python type hints for all function arguments (e.g., `def my_tool(query: str, limit: int = 5):`). This is not optional.**\n"
        "4. Keep the function simple and focused on a single task.\n"
        "5. After creating a tool, you can then call it on a subsequent turn.\n\n"
        "Follow this format exactly:\n"
        "1. **Thought:** Briefly explain your reasoning and your plan for the next step. A plan can involve multiple tool calls.\n"
        "2. **Confidence:** An integer score from 1-10 on how likely you believe the plan is to succeed and contribute to the goal. 1 is a wild guess, 10 is a certainty.\n"
        "3. **Rationale:** A very brief, one-sentence justification for your confidence score.\n"
        "4. **Tool Calls:** A JSON list of one or more tool calls to execute in sequence. Each item MUST have 'tool_name' and 'args'.\n\n"
        "Example of a multi-step plan:\n"
        "```json\n"
        "{\n"
        '  "thought": "The user wants the top tech news headlines emailed to them. I will first search for the news, and then use the send_gmail_message tool to email the results.",\n'
        '  "confidence": 9,\n'
        '  "rationale": "This is a standard workflow combining search and communication tools.",\n'
        '  "tool_calls": [\n'
        '    { "tool_name": "search_and_browse", "args": { "query": "top tech news headlines today" } },\n'
        '    { "tool_name": "send_gmail_message", "args": { "to_address": "user@example.com", "subject": "Tech News Headlines", "body": "Placeholder: The search results will be sent in the next turn after I see them." } }\n'
        '  ]\n'
        "}\n"
        "```\n"
        "When the task is fully completed, you MUST respond ONLY with 'Final Answer:' followed by a clear, user-friendly summary."
    )

    # --- Step 2: The Agent's internal thought process loop ---
    internal_scratchpad = []
    executed_tools = []
    
    turn_count = 0
    max_turns_failsafe = 15
    consecutive_error_count = 0
    max_consecutive_errors = 2

    with console.status("[bold green]Agent is thinking...[/bold green]", spinner="dots") as status:
        while turn_count < max_turns_failsafe:
            turn_count += 1
            status.update(random.choice(THINKING_MESSAGES))
            console.print(f"\n[bold magenta]--- Agent Turn {turn_count}/{max_turns_failsafe} ---[/bold magenta]")

            full_prompt_for_turn = (
                f"{system_prompt}\n\n"
                f"AVAILABLE TOOLS:\n{tool_prompt_string}\n"
                f"{memory_prompt_part}\n\n"
                f"USER_GOAL: {user_goal}\n\n"
                f"INTERNAL SCRATCHPAD (Previous Steps):\n{''.join(internal_scratchpad)}"
            )
            
            try:
                response = gemini_client.model.generate_content(full_prompt_for_turn)
                
                if response.parts:
                    ai_response_text = "".join(part.text for part in response.parts)
                else:
                    finish_reason_name = "UNKNOWN"
                    if response.candidates:
                        finish_reason_name = response.candidates[0].finish_reason.name
                    
                    error_message = f"AI model returned no content. Finish Reason: {finish_reason_name}."
                    console.print(f"[bold red]AI Response Error:[/bold red] {error_message}")
                    
                    feedback = f"SYSTEM_FEEDBACK: Your response was empty. This is a critical error. You MUST provide a JSON object with a thought and a tool call, or a 'Final Answer:'. Do not respond with empty content again."
                    internal_scratchpad.append(f"\nAI_RESPONSE:\n(EMPTY)\n{feedback}")
                    consecutive_error_count += 1
                    if consecutive_error_count >= max_consecutive_errors:
                        console.print("[bold red]Agent failed to recover after multiple attempts. Aborting.[/bold red]")
                        return "The agent got stuck and could not recover. Please try rephrasing your goal."
                    continue

            except google_exceptions.ResourceExhausted as e:
                wait_time = 30 
                match = re.search(r'retry_delay {\s*seconds: (\d+)\s*}', str(e))
                if match:
                    wait_time = int(match.group(1)) + 1

                console.print(f"[bold yellow]API Rate Limit Exceeded.[/bold yellow] The agent will automatically pause for {wait_time} seconds and then retry.")
                eel.update_agent_status(f"Rate limit hit. Pausing for {wait_time}s...")()
                
                time.sleep(wait_time)
                
                turn_count -= 1 
                continue

            except google_exceptions.InternalServerError as e:
                console.print(f"[bold red]API Error:[/bold red] A 500 Internal Server Error occurred. The agent will attempt to recover. Details: {e}")
                feedback = f"SYSTEM_FEEDBACK: The API call failed with a server error. This may have been a temporary issue. Please re-evaluate the plan and try again."
                internal_scratchpad.append(f"\nSYSTEM_ERROR:\n{feedback}")
                consecutive_error_count += 1
                if consecutive_error_count >= max_consecutive_errors:
                    console.print("[bold red]Agent failed to recover after multiple API errors. Aborting.[/bold red]")
                    return "The agent encountered repeated API errors. Please try again later."
                continue

            except Exception as e:
                console.print(f"[bold red]An unexpected error occurred during AI generation:[/bold red] {e}")
                traceback.print_exc()
                return f"Sorry, a critical error occurred while communicating with the AI: {e}"

            if "Final Answer:" in ai_response_text:
                final_answer = ai_response_text.split("Final Answer:", 1)[1].strip()
                console.print(Panel(f"[bold green]Goal Achieved![/bold green]\n{final_answer}", title="Task Completed", border_style="green", expand=False))
                
                try:
                    if executed_tools:
                        summary_prompt = f"Based on the original goal and the final answer, create a one-sentence summary of what was accomplished. Original Goal: {user_goal}. Final Answer: {final_answer}"
                        task_summary = gemini_client.generate_text(summary_prompt).strip()
                        if task_summary and not task_summary.startswith("Error"):
                             memory_manager.add_memory(task_summary, list(set(executed_tools)), final_answer)
                except Exception as e:
                    logger.error(f"Failed to save memory reflection: {e}")
                
                return final_answer

            # --- Step 3: Parse, Verify, and Execute Tool Call ---
            try:
                json_match = re.search(r'```json\n(.*?)\n```', ai_response_text, re.DOTALL)
                if not json_match: raise ValueError("No JSON block found in the response.")
                
                parsed_json = json.loads(json_match.group(1))

                if isinstance(parsed_json, list) and parsed_json:
                    parsed_response = parsed_json[0]
                else:
                    parsed_response = parsed_json
                
                if not isinstance(parsed_response, dict):
                    raise ValueError("The parsed JSON content is not a dictionary.")
                    
                thought = parsed_response.get('thought', 'No thought provided.')
                model_confidence = parsed_response.get('confidence', 5) / 10.0
                confidence_rationale = parsed_response.get('rationale', 'No rationale provided.')
                tool_calls = parsed_response.get('tool_calls', [])

                if not tool_calls:
                    console.print("[yellow]Warning: AI did not propose a tool. Will try again based on its thought.[/yellow]")
                    if "answer is" in thought.lower() or "here is the" in thought.lower():
                        feedback = "SYSTEM_FEEDBACK: Your thought seems to contain the final answer, but you did not use the required 'Final Answer:' prefix. You MUST either use a tool or format your response as 'Final Answer: [your response]'."
                    else:
                        feedback = "SYSTEM_FEEDBACK: Your response was valid, but you did not propose any action. Every turn must result in a tool call. If you believe the task is complete, you must use the 'Final Answer:' format. Otherwise, you must choose a tool to get closer to the goal."
                    internal_scratchpad.append(f"\nAI_RESPONSE:\n{ai_response_text}\n{feedback}")
                    consecutive_error_count += 1
                    if consecutive_error_count >= max_consecutive_errors:
                         console.print("[bold red]Agent failed to propose an action after multiple attempts. Aborting.[/bold red]")
                         return "The agent could not decide on a next step. Please try rephrasing your goal."
                    continue

                consecutive_error_count = 0

            except (json.JSONDecodeError, ValueError) as e:
                error_feedback = f"Error: Invalid response format from AI. Details: {e}"
                console.print(f"[bold red]{error_feedback}[/bold red]")
                
                feedback = f"SYSTEM_FEEDBACK: Your last response could not be parsed. The error was: '{e}'. You MUST follow the specified JSON format exactly, including the '```json' markers. Do not add any text outside the JSON block."
                internal_scratchpad.append(f"\nAI_RESPONSE:\n{ai_response_text}\n{feedback}")
                
                consecutive_error_count += 1
                if consecutive_error_count >= max_consecutive_errors:
                    console.print("[bold red]Agent failed to provide a valid response format after multiple attempts. Aborting.[/bold red]")
                    return "The agent failed to format its response correctly. This may be an internal issue."
                
                continue

            console.print(Panel(f"Thought: {thought}\nConfidence: {model_confidence*10:.1f}/10\nRationale: {confidence_rationale}", title="Agent's Plan", border_style="cyan"))
            eel.update_agent_status(f"Thinking: {thought}")()

            adjusted_confidence = model_confidence 
            console.print(f"[bold]Plan Confidence: [cyan]{adjusted_confidence:.2f}[/cyan][/bold]")
            
            decision = "STOP"
            is_destructive = any(tc.get("tool_name") in ["execute_shell_command", "delete_junk_file", "create_new_tool", "execute_generated_python_script"] for tc in tool_calls)
            
            if is_destructive and adjusted_confidence < CONFIDENCE_THRESHOLD_ASK: decision = "STOP"
            elif is_destructive: decision = "ASK"
            elif adjusted_confidence >= CONFIDENCE_THRESHOLD_GO: decision = "GO"
            elif adjusted_confidence >= CONFIDENCE_THRESHOLD_ASK: decision = "ASK"
            
            user_confirmed = False
            if decision == "ASK":
                console.print("[bold yellow]Decision: ASK.[/bold yellow] Requesting user confirmation for the plan.")
                global confirmation_handler 
                confirmation_handler = ConfirmationHandler()
                details = { "title": "Confirm Action Plan", "plan": tool_calls, "rationale": confidence_rationale }
                eel.prompt_user_for_confirmation(details)
                user_confirmed = confirmation_handler.wait_for_response()
                confirmation_handler = None
                if not user_confirmed:
                    feedback = "User cancelled the action plan. Please propose a new plan."
                    console.print(f"[red]{feedback}[/red]")
                    internal_scratchpad.append(f"\nAI_RESPONSE:\n{ai_response_text}\nSYSTEM_FEEDBACK: {feedback}")
                    continue
            
            if decision == "GO" or user_confirmed:
                console.print("[bold green]Decision: GO.[/bold green] Executing plan.")
                
                all_tool_outputs = []
                plan_failed = False
                for tool_call in tool_calls:
                    tool_name = tool_call.get("tool_name")
                    raw_tool_args = tool_call.get("args", {})
                    
                    console.print(f"\n[bold]Executing Tool: [blue]{tool_name}[/blue][/bold]")
                    eel.update_agent_status(f"Executing: {tool_name}...")()
                    
                    executed_tools.append(tool_name)
                    tool_definition = session_tools.get(tool_name)
                    
                    if not tool_definition:
                        tool_output = {"status": "error", "message": f"Tool '{tool_name}' not found."}
                    else:
                        tool_output = execute_tool(
                            tool_func=tool_definition["function"],
                            args_model=tool_definition["args_model"],
                            raw_args=raw_tool_args
                        )

                    tool_output_str = json.dumps(tool_output, indent=2)
                    sanitized_output_str = escape(tool_output_str)
                    console.print(Panel(sanitized_output_str, title=f"Output from {tool_name}", border_style="yellow"))
                    
                    log_tool_execution(
                        tool_name, raw_tool_args,
                        tool_output.get("status") == "ok",
                        str(tool_output.get("data") or tool_output.get("message")),
                        json.dumps(tool_output) if tool_output.get("status") == "error" else None,
                        {"model_score": model_confidence, "adjusted_score": adjusted_confidence }
                    )
                    
                    all_tool_outputs.append(f"--- Output from {tool_name} ---\n{tool_output_str}")

                    if tool_output.get("status") == "error":
                        console.print(f"[bold red]Plan execution failed at step '{tool_name}'. Stopping plan.[/bold red]")
                        plan_failed = True
                        break 
                
                consolidated_output = "\n".join(all_tool_outputs)
                internal_scratchpad.append(f"\nAI_RESPONSE:\n{ai_response_text}\nTOOL_RESULTS:\n{consolidated_output}")

    console.print(f"[bold red]Agent reached maximum turns failsafe ({max_turns_failsafe}) without a final answer.[/bold red]")
    return "The agent could not complete the task within the allowed number of steps. Please try rephrasing your goal."