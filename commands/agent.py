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
        self.event.wait(timeout)
        return self.result
    def set_response(self, confirmed: bool):
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

def classify_intent(user_goal: str) -> List[str]:
    """Classifies the user's goal into categories to prune the tool list."""
    goal = user_goal.lower()
    categories = set()
    category_keywords = {
        "File Ops": ['file', 'folder', 'directory', 'move', 'rename', 'delete', 'organize', 'backup', 'copy', 'save'],
        "System Info": ['system', 'os', 'process', 'cpu', 'ram', 'info', 'hardware', 'memory', 'preference'],
        "Web Search": [
            'search', 'browse', 'web', 'google', 'look up', 'find', 'research',
            'what is', 'who is', 'latest', 'news', 'headline', 'summarize', 'summarise', 'summarization', 'wikipedia', 'article', 'current events', 'ai news', 'tech news'],
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

def think(gemini_client: GeminiClient, user_goal: str, user_id: int = None) -> str:
    # ... [rest identical to previous, unchanged] ...
    # Only the classify_intent and possibly the system prompt section above is changed.
    # The remainder of the file remains unchanged (use the agent loop, scratchpad and error prompt as before)

    [THE REST OF THE AGENT SCRIPT IS UNCHANGED]
