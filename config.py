import os
import datetime
from dotenv import load_dotenv

# Load environment variables from .env file (NEW)
load_dotenv()

# --- API Configuration ---
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# --- Telegram Bot Configuration ---
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_ADMIN_USER_ID = int(os.getenv("TELEGRAM_ADMIN_USER_ID", "0"))

# --- Weather API Configuration ---
WEATHER_API_KEY = os.getenv("WEATHER_API_KEY")
WEATHER_UPDATE_INTERVAL = int(os.getenv("WEATHER_UPDATE_INTERVAL", "600"))

# --- AI Model Settings ---
DEFAULT_AI_MODEL = os.getenv("DEFAULT_AI_MODEL", "gemini-2.5-flash")
VISION_MODEL_NAME = os.getenv("VISION_MODEL_NAME", "gemini-2.5-pro")

# --- Web Scraping Settings ---
MAX_WEB_SCRAPE_CONTENT_LENGTH = int(os.getenv("MAX_WEB_SCRAPE_CONTENT_LENGTH", "4000"))
MAX_LINKS_TO_FOLLOW = int(os.getenv("MAX_LINKS_TO_FOLLOW", "2"))

# --- Google Custom Search API Settings ---
GOOGLE_CSE_API_KEY = os.getenv("GOOGLE_CSE_API_KEY")
GOOGLE_CSE_ENGINE_ID = os.getenv("GOOGLE_CSE_ENGINE_ID")

# AI interaction mode
DEFAULT_AI_MODE = os.getenv("DEFAULT_AI_MODE", "chat")

# AI response temperature
AI_TEMPERATURE = float(os.getenv("AI_TEMPERATURE", "0.7"))

# Max tokens for AI response
MAX_RESPONSE_TOKENS = int(os.getenv("MAX_RESPONSE_TOKENS", "4096"))

# --- File Paths ---
DATA_DIR = os.getenv("DATA_DIR", "data")
LOGS_DIR = os.path.join(DATA_DIR, "logs")
MEMORY_DIR = os.path.join(DATA_DIR, "memory")
PROMPTS_DIR = os.getenv("PROMPTS_DIR", "prompts")
INSIGHTS_FILE = os.path.join(DATA_DIR, "ai_insights.json")
TEMP_DIR = os.getenv("TEMP_DIR", "temp")
os.makedirs(LOGS_DIR, exist_ok=True)
os.makedirs(MEMORY_DIR, exist_ok=True)
os.makedirs(TEMP_DIR, exist_ok=True)
os.makedirs(os.path.dirname(INSIGHTS_FILE), exist_ok=True)

def get_daily_memory_file_path():
    today_str = datetime.date.today().strftime("%Y-%m-%d")
    return os.path.join(MEMORY_DIR, f"{today_str}.json")

# --- Logging Settings ---
ENABLE_LOGGING = os.getenv("ENABLE_LOGGING", "True").lower() == "true"
LOG_FILE = os.path.join(LOGS_DIR, "assistant_log.txt")

GMAIL_IMPORTANT_SENDERS = os.getenv("GMAIL_IMPORTANT_SENDERS", "important@example.com,github,billing@company.com").split(',')
GMAIL_CHECK_INTERVAL = int(os.getenv("GMAIL_CHECK_INTERVAL", "120"))

ENABLE_RICH_OUTPUT = os.getenv("ENABLE_RICH_OUTPUT", "True").lower() == "true"
CONFIRM_SHELL_EXECUTION = os.getenv("CONFIRM_SHELL_EXECUTION", "True").lower() == "true"
SHELL_COMMAND_WHITELIST = os.getenv("SHELL_COMMAND_WHITELIST", "").split(',') if os.getenv("SHELL_COMMAND_WHITELIST") else []
MAX_CLIPBOARD_TEXT_LENGTH = int(os.getenv("MAX_CLIPBOARD_TEXT_LENGTH", "5000"))

# Agent Settings
FINAL_ANSWER_TOOL_NAME = os.getenv("FINAL_ANSWER_TOOL_NAME", "final_answer")
CONFIDENCE_THRESHOLD_GO = float(os.getenv("CONFIDENCE_THRESHOLD_GO", "0.75"))
CONFIDENCE_THRESHOLD_ASK = float(os.getenv("CONFIDENCE_THRESHOLD_ASK", "0.40"))
HISTORY_RECORDS_TO_CONSIDER = int(os.getenv("HISTORY_RECORDS_TO_CONSIDER", "50"))

# --- Optimizer Settings (optional/legacy) ---
OPTIMIZER_WORKSPACE_DIR = os.getenv("OPTIMIZER_WORKSPACE_DIR", os.path.join(os.path.abspath(os.path.dirname(__file__)), "optimizer_workspace"))
OPTIMIZER_SOURCE_DIR = os.getenv("OPTIMIZER_SOURCE_DIR", os.path.abspath(os.path.dirname(__file__)))
OPTIMIZER_DEFAULT_MODE = os.getenv("OPTIMIZER_DEFAULT_MODE", "report-only")
OPTIMIZER_IGNORE_PATTERNS = os.getenv("OPTIMIZER_IGNORE_PATTERNS", ".git,optimizer_workspace,data/memory,__pycache__",).split(',')
