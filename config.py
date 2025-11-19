# config.py

import os
import datetime # Import datetime for daily file naming

# --- API Configuration ---
# You'll need to get your API key from Google AI Studio or other AI providers.
# It's recommended to load these from environment variables for security.
# Example: GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
# If not using environment variables, uncomment and set directly (less secure for production).
GEMINI_API_KEY = "AIzaSyAjzSlEqihneKzNcvJosLdDPKkYsA591GI"
# Replace with your actual key or load from environment variable
# If you plan to use other AI models, add their API keys here too.

# --- Telegram Bot Configuration ---
# Get your Telegram Bot Token from BotFather on Telegram.
# It's highly recommended to load this from an environment variable for security.
TELEGRAM_BOT_TOKEN = "7750024213:AAHV66d5DC-TFs8DobM-Bux5Y73QOc2LuT8"
# Set the Telegram User ID of the admin. Only this user can run shell commands.
# You can get your user ID by sending /start to the bot and checking the logs,
# or by using a bot like @userinfobot.
TELEGRAM_ADMIN_USER_ID = 919340565 # <--- IMPORTANT: REPLACE WITH YOUR ACTUAL TELEGRAM USER ID

# --- Weather API Configuration ---
WEATHER_API_KEY = "c43985c6496940808e875805250808"
WEATHER_UPDATE_INTERVAL = 600 # seconds

# --- AI Model Settings ---
# Default AI model to use for text generation and multimodal tasks.
# 'gemini-1.5-pro-latest' is a powerful model for general purpose and multimodal tasks.
DEFAULT_AI_MODEL = "gemini-2.5-flash"
# Specific model for vision tasks. Can be the same as the default model if it's multimodal.
VISION_MODEL_NAME = "gemini-2.5-pro"


# --- Web Scraping Settings ---
# Max length of web page content to send to AI to prevent excessive token usage.
# Content beyond this limit will be truncated.
MAX_WEB_SCRAPE_CONTENT_LENGTH = 4000 # ~1000 words, adjust as needed

# Max number of internal links to follow when 'follow_links' is true in search_and_browse.
# This helps prevent infinite loops and excessive scraping.
MAX_LINKS_TO_FOLLOW = 2 # Follow up to 2 internal links per initial search result

# --- Google Custom Search API Settings ---
# You'll need an API Key and a Search Engine ID (CX) from Google Cloud Console.
# Follow the setup guide to get these.
# It's recommended to load these from environment variables for security.
GOOGLE_CSE_API_KEY = "AIzaSyA6WYkx2zB6NYbn_jcZtVj8l_FaFjWFrw4" # Replace with your actual API Key
GOOGLE_CSE_ENGINE_ID = "c7a537e265a9e4338" # Replace with your actual Search Engine ID (CX)


# AI interaction mode.
# 'chat': For conversational interactions.
# 'code': Optimized for code generation/completion.
# 'shell': Optimized for shell command generation.
DEFAULT_AI_MODE = "chat"

# AI response temperature (creativity).
# Lower values (e.g., 0.2) make responses more focused and deterministic.
# Higher values (e.g., 0.8) make responses more creative and varied.
AI_TEMPERATURE = 0.7

# Max tokens for AI response.
# Limits the length of the AI's output.
# Increased to 4096 to allow for longer, more complex plans.
MAX_RESPONSE_TOKENS = 4096

# --- File Paths ---
# Base directory for data storage (logs, memory, etc.)
DATA_DIR = "data"
LOGS_DIR = os.path.join(DATA_DIR, "logs")
# Changed MEMORY_FILE to MEMORY_DIR for daily memory files
MEMORY_DIR = os.path.join(DATA_DIR, "memory")
PROMPTS_DIR = "prompts"
INSIGHTS_FILE = os.path.join(DATA_DIR, "ai_insights.json") # NEW: Path for extracted insights
TEMP_DIR = "temp" # For temporary files like audio and images
os.makedirs(TEMP_DIR, exist_ok=True)


# Ensure directories exist
os.makedirs(LOGS_DIR, exist_ok=True)
os.makedirs(MEMORY_DIR, exist_ok=True) # Ensure 'data/memory' exists
os.makedirs(os.path.dirname(INSIGHTS_FILE), exist_ok=True) # Ensure 'data' exists for insights file

# Helper function to get the daily memory file path
def get_daily_memory_file_path():
    """Generates the file path for the current day's conversational memory."""
    today_str = datetime.date.today().strftime("%Y-%m-%d")
    return os.path.join(MEMORY_DIR, f"{today_str}.json")


# --- Logging Settings ---
# Enable/disable logging of AI requests/responses and command executions.\
ENABLE_LOGGING = True
LOG_FILE = os.path.join(LOGS_DIR, "assistant_log.txt")

# In config.py, add these new settings, perhaps after the Telegram section

# --- GMail Bot Configuration ---
# A list of sender emails or keywords (case-insensitive) to treat as important.
# Examples: "alerts@mybank.com", "jane.doe@company.com", "Facebook", "GitHub"
GMAIL_IMPORTANT_SENDERS = [
    "important@example.com", 
    "github", 
    "billing@company.com"
] # <--- CUSTOMIZE THIS LIST
GMAIL_CHECK_INTERVAL = 120 # seconds (check every 2 minutes)

# --- UI/UX Settings ---
# Enable/disable rich output styling.
ENABLE_RICH_OUTPUT = True

# --- System & Safety ---
# Confirm shell command execution before running.
# Set to True to always ask for confirmation.
# Set to False to run immediately (use with caution!).
CONFIRM_SHELL_EXECUTION = True

# Whitelist of allowed commands for 'ai shell' if strict security is needed.
# Leave empty [] to allow all suggested commands (with confirmation).
# Example: SHELL_COMMAND_WHITELIST = ["dir", "cd", "copy"]
SHELL_COMMAND_WHITELIST = []

# --- Clipboard Settings ---
# Max length of clipboard text to send to AI to prevent excessive token usage.
MAX_CLIPBOARD_TEXT_LENGTH = 5000 # characters

# --- Add other settings as your project grows ---
# Example: Default folder for 'ai organize'
# DEFAULT_ORGANIZE_FOLDER = os.path.expanduser("~") # User's home directory

# --- Agent Settings ---
# This is a special "tool name" that the agent looks for to identify a final answer.
# If the AI produces plain text and not a tool call, it's treated as the FINAL_ANSWER_TOOL_NAME.
FINAL_ANSWER_TOOL_NAME = "final_answer" # New line