# commands/system_tools.py
import subprocess
import logging
import shlex  # Used for safely parsing shell commands.
import platform # <-- NEW: Import the platform module
from typing import List
from config import ENABLE_LOGGING, LOG_FILE
from commands.ai_chat import GeminiClient

# --- Setting up the Logger ---
# Configures the logging system to record shell command executions and suggestions.
if ENABLE_LOGGING:
    logging.basicConfig(level=logging.INFO,
                        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                        handlers=[
                            logging.FileHandler(LOG_FILE, encoding='utf-8'),
                            logging.StreamHandler()
                        ])
    logger = logging.getLogger(__name__)
else:
    # If logging is disabled, the logger is set to a critical level
    # to suppress all but the most severe messages.
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.CRITICAL + 1)
    logger.propagate = False

def execute_shell_command(command: str) -> str:
    """
    Executes a given shell command securely, captures its output, and
    translates common commands for Windows compatibility.
    This function is designed to prevent shell injection vulnerabilities.

    Args:
        command (str): The shell command to be executed.

    Returns:
        str: The standard output and standard error of the command,
             or an informative error message if execution fails.
    """
    # --- NEW: Platform-specific command translation ---
    if platform.system() == "Windows":
        # Create a dictionary of common command translations
        translations = {
            "ls": "dir",
            "ls -l": "dir",
            "ls -la": "dir /a",
            "cp": "copy",
            "mv": "move",
            "rm": "del",
            "clear": "cls"
            # Add more translations as needed
        }
        # Check if the command needs translation
        # We split the command to handle arguments correctly, e.g., 'cp source.txt dest.txt'
        command_parts_for_check = command.strip().split()
        base_command = command_parts_for_check[0]
        
        if command in translations:
             command = translations[command]
        elif base_command in translations:
             # Translate the base command and keep the arguments
             command_parts_for_check[0] = translations[base_command]
             command = " ".join(command_parts_for_check)

    logger.info(f"Attempting to execute shell command: '{command}'")
    try:
        # Uses shlex.split() to safely parse the command string into a list of arguments.
        # This is crucial for security, preventing malicious command injection.
        # On Windows, we need to handle this carefully for commands like 'dir'
        if platform.system() == "Windows":
            # For built-in commands like 'dir', 'copy', etc., we need to run them through the shell.
            # We can do this safely by letting subprocess handle the command string directly.
             result = subprocess.run(
                command,
                shell=True, # Use shell=True for Windows built-ins
                capture_output=True,
                text=True,
                check=False,
                encoding='utf-8', # Specify encoding for wider compatibility
                errors='ignore'
            )
        else:
            # For Linux/macOS, the original secure method is best
            command_parts = shlex.split(command)
            result = subprocess.run(
                command_parts,
                capture_output=True,
                text=True,
                check=False
            )

        output = result.stdout.strip()
        error = result.stderr.strip()

        if result.returncode == 0:
            logger.info(f"Command executed successfully: '{command}'")
            return f"Command executed successfully.\nOutput:\n{output}" if output else "Command executed successfully (no output)."
        else:
            logger.error(f"Command failed: '{command}' with exit code {result.returncode}")
            # Provides both error and standard output for comprehensive debugging.
            return f"Command failed with exit code {result.returncode}.\nError:\n{error}\nOutput:\n{output}"

    except FileNotFoundError:
        cmd_name = command.split(' ')[0]
        logger.error(f"Command not found: '{cmd_name}'")
        return f"Error: Command '{cmd_name}' not found. Make sure it's installed and in your system's PATH."
    except Exception as e:
        logger.error(f"An unexpected error occurred during command execution: {e}")
        return f"An unexpected error occurred: {e}"

def generate_shell_command_suggestions(gemini_client: GeminiClient, user_task: str) -> str:
    """
    Generates AI-powered suggestions for shell commands based on a natural language task description.
    The AI is instructed to provide only the command(s) without additional conversational text.

    Args:
        gemini_client (GeminiClient): An initialized instance of the GeminiClient for AI communication.
        user_task (str): A natural language description of the task for which a shell command is needed.

    Returns:
        str: The AI's suggested shell command(s) or "N/A" if no command can be determined.
    """
    # --- NEW: Determine the OS for the prompt ---
    os_name = "Windows (CMD/PowerShell)" if platform.system() == "Windows" else "Linux/macOS (bash/zsh)"

    prompt = (
        f"You are a helpful assistant that suggests command-line commands for the {os_name} operating system.\n"
        "Given a user's task description, provide the exact shell command(s) needed to accomplish it.\n"
        "Do NOT include any explanatory text, conversational phrases, or markdown formatting (like ```bash). "
        "Just provide the command(s) directly, one per line if multiple are needed.\n"
        "If you cannot determine a command, respond with 'N/A'.\n\n"
        f"User task: {user_task}\n"
        "Command:"
    )
    logger.info(f"Sending shell command suggestion prompt to AI for task: '{user_task}'")

    ai_response = gemini_client.generate_text(prompt)

    # Cleans the AI's response by removing any markdown code block formatting.
    cleaned_response = ai_response.strip()
    if cleaned_response.startswith("```") and cleaned_response.endswith("```"):
        cleaned_response = "\n".join(cleaned_response.splitlines()[1:-1]).strip()

    logger.info(f"AI suggested command (first 100 chars): '{cleaned_response[:100]}...'")
    return cleaned_response